"""Generate source-checked page evals and grade retrieval without an LLM judge."""

from __future__ import annotations

import base64
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path

import pymupdf

from src.pdf_chunking import clean_extra_whitespace


def pdf_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def eval_path(pdf_root: Path, pdf_path: Path) -> Path:
    relative = pdf_path.relative_to(pdf_root)
    return pdf_root.parent / "evals" / relative.parent / f"{relative.stem}_eval.jsonl"


def error_path(eval_file: Path) -> Path:
    return eval_file.with_name(f"{eval_file.stem}_errors.json")


def load_page_errors(path: Path, expected_digest: str) -> dict[int, str]:
    """Read generation failures for one PDF version, if any were recorded."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("pdf_sha256") != expected_digest:
            return {}
        return {int(page): str(message) for page, message in payload.get("errors", {}).items()}
    except (OSError, ValueError, TypeError, AttributeError):
        return {}


def update_page_error(path: Path, pdf_sha256: str, page_num: int, message: str | None) -> None:
    """Atomically record or clear a page-level generation error."""
    errors = load_page_errors(path, pdf_sha256)
    if message:
        errors[int(page_num)] = " ".join(message.split())[:1200]
    else:
        errors.pop(int(page_num), None)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.stem}.", suffix=".tmp", delete=False) as stream:
            temporary_name = stream.name
            json.dump({"pdf_sha256": pdf_sha256,
                       "errors": {str(page): text for page, text in errors.items()}}, stream,
                      ensure_ascii=False, indent=2)
        os.replace(temporary_name, path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def result_path(path: Path, policy_label: str) -> Path:
    slug = hashlib.sha256(policy_label.encode()).hexdigest()[:12]
    return path.with_name(f"{path.stem.removesuffix('_eval')}_{slug}_results.jsonl")


def render_page_png(pdf_path: Path, page_number: int, scale: float = 1.5) -> bytes:
    with pymupdf.open(pdf_path) as pdf:
        return pdf[page_number - 1].get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False).tobytes("png")


def generate_page_evals(client, model: str, png: bytes, page_text: str, page_number: int) -> list[dict]:
    """Use a page image for layout context, then require exact extracted-text evidence."""
    if not page_text:
        return []
    data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    schema = {
        "type": "object",
        "properties": {
            "evals": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "answer": {"type": "string"},
                        "evidence_quote": {"type": "string"},
                    },
                    "required": ["query", "answer", "evidence_quote"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["evals"],
        "additionalProperties": False,
    }
    response = client.responses.create(
        model=model,
        store=False,
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": (
                    "Create exactly three distinct, answerable retrieval questions for this PDF page. "
                    "Use the image for layout and tables, but every evidence_quote MUST be a contiguous "
                    "verbatim substring of EXTRACTED TEXT below (same words and order). "
                    "Each answer must be short, copied verbatim from its evidence_quote, "
                    "and contain only the answer, not an explanation. "
                    "Choose meaningful facts from different parts of the page. Do not invent facts. "
                    f"Page {page_number}. EXTRACTED TEXT:\n{page_text}"
                )},
                {"type": "input_image", "image_url": data_url, "detail": "high"},
            ],
        }],
        text={"format": {"type": "json_schema", "name": "page_retrieval_evals", "strict": True, "schema": schema}},
    )
    data = json.loads(response.output_text)
    items = data.get("evals", [])
    if len(items) != 3:
        raise ValueError(f"Page {page_number}: model returned {len(items)} evals, expected 3")
    normalized = clean_extra_whitespace(page_text)
    clean_items = []
    for item in items:
        query = item["query"].strip()
        answer = item["answer"].strip()
        quote = clean_extra_whitespace(item["evidence_quote"])
        if not query or not answer or not quote or quote not in normalized or answer.casefold() not in quote.casefold():
            raise ValueError(f"Page {page_number}: an eval has missing or non-verbatim evidence")
        clean_items.append({"query": query, "answer": answer, "evidence_quote": quote,
                            "page_num": page_number})
    if len({item["query"].casefold() for item in clean_items}) != 3:
        raise ValueError(f"Page {page_number}: duplicate questions")
    return clean_items


def load_evals(path: Path, expected_digest: str | None = None) -> list[dict]:
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if expected_digest and any(row.get("pdf_sha256") != expected_digest for row in rows):
        raise ValueError("Saved evals refer to a different PDF version")
    return rows


def append_evals(path: Path, rows: list[dict]) -> None:
    """Atomically add/replace a complete page so interrupted runs can resume."""
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    incoming_pages = {int(row["page_num"]) for row in rows if "page_num" in row}
    previous = load_evals(path)
    kept = [row for row in previous if int(row.get("page_num", -1)) not in incoming_pages]
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.stem}.", suffix=".tmp", delete=False) as stream:
            temporary_name = stream.name
            for row in kept + rows:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
        os.replace(temporary_name, path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def page_spans(pages: list[tuple[int, str]]) -> dict[int, tuple[int, int]]:
    """Offsets in the same joined/normalized text used by split_pdf."""
    spans = {}
    offset = 0
    for number, text in pages:
        if not text:
            continue
        if offset:
            offset += 1  # separator space
        spans[number] = (offset, offset + len(text))
        offset += len(text)
    return spans


def evidence_offsets(row: dict, pages: list[tuple[int, str]]) -> list[tuple[int, int]]:
    page_num = int(row["page_num"])
    page_text = dict(pages).get(page_num, "")
    page_start = page_spans(pages).get(page_num, (0, 0))[0]
    quote = row["evidence_quote"]
    offsets = []
    start = 0
    while True:
        found = page_text.find(quote, start)
        if found < 0:
            break
        offsets.append((page_start + found, page_start + found + len(quote)))
        start = found + 1
    return offsets


def relevant_chunk_ids(row: dict, pages: list[tuple[int, str]], chunks: list) -> set[int]:
    targets = evidence_offsets(row, pages)
    relevant = set()
    for index, chunk in enumerate(chunks):
        start = chunk.metadata.get("start_index", -1)
        if start < 0:
            continue
        end = start + len(chunk.page_content)
        if any(start <= left and right <= end for left, right in targets):
            relevant.add(index)
    return relevant


def grade_ranked(ranked_ids: list[int], relevant_ids: set[int], k: int = 3) -> dict:
    top = ranked_ids[:k]
    hits = [1 if chunk_id in relevant_ids else 0 for chunk_id in top]
    first = next((rank for rank, hit in enumerate(hits, 1) if hit), None)
    dcg = sum(hit / math.log2(rank + 1) for rank, hit in enumerate(hits, 1))
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(len(relevant_ids), k) + 1))
    return {
        "recall_at_1": int(any(hits[:1])),
        "recall_at_2": int(any(hits[:2])),
        "recall_at_3": int(any(hits[:3])),
        "mrr_at_3": 1 / first if first else 0.0,
        "ndcg_at_3": dcg / ideal if ideal else 0.0,
        "first_relevant_rank": first,
        "evidence_covered": bool(relevant_ids),
    }


def rank_queries(evals: list[dict], chunks: list, model) -> list[list[int]]:
    """Full-corpus cosine ranking; never leak the answer or page into the query."""
    import numpy as np

    if not chunks:
        return [[] for _ in evals]
    documents = model.encode([chunk.page_content for chunk in chunks], normalize_embeddings=True,
                             convert_to_numpy=True, show_progress_bar=False)
    queries = model.encode([row["query"] for row in evals], normalize_embeddings=True,
                           convert_to_numpy=True, show_progress_bar=False)
    similarities = np.asarray(queries) @ np.asarray(documents).T
    return [np.argsort(-scores, kind="stable").tolist() for scores in similarities]
