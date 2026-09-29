"""Recursive PDF inventory scanner. Writes JSON consumed by Streamlit."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pymupdf


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+[\w'-]*\b", text))


def detect_language(text: str) -> str:
    if not text.strip():
        return "none"
    if re.search(r"[\uac00-\ud7af]", text):
        return "korean"
    if re.search(r"[\u4e00-\u9fff]", text):
        return "chinese"
    lower = text.lower()
    spanish = len(re.findall(r"\b(el|la|los|las|de|para|que|por|una|con|del|política|fecha)\b", lower))
    english = len(re.findall(r"\b(the|and|of|for|with|date|policy|table|coverage)\b", lower))
    if spanish > english and spanish >= 2:
        return "spanish"
    return "english" if re.search(r"[A-Za-z]", text) else "other"


def estimate_tables(page: pymupdf.Page, text: str) -> int:
    """Return a fast text-layout table estimate.

    Exact graphical table detection is intentionally omitted from the batch
    scan: on some large PDFs it can render pages and take minutes per page.
    """
    if not text.strip():
        return 0
    pipe_lines = [line for line in text.splitlines() if line.count("|") >= 2]
    if len(pipe_lines) >= 2:
        return 1
    aligned_lines = [line for line in text.splitlines() if len(re.split(r"\s{2,}", line.strip())) >= 3]
    if len(aligned_lines) >= 3:
        return 1
    return 0


def scan_pdf(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pages: list[dict[str, Any]] = []
    totals = {"characters": 0, "words": 0, "images": 0, "blocks": 0, "tables": 0}
    languages: list[str] = []
    with pymupdf.open(path) as doc:
        for page_number, page in enumerate(doc, 1):
            text = page.get_text("text") or ""
            chars = len(text.strip())
            words = word_count(text)
            images = len(page.get_images(full=True))
            blocks = len(page.get_text("blocks"))
            tables = estimate_tables(page, text)
            language = detect_language(text)
            pages.append({"page": page_number, "has_text": bool(chars), "characters": chars,
                          "words": words, "images": images, "text_blocks": blocks,
                          "tables_estimate": tables, "language": language})
            totals["characters"] += chars
            totals["words"] += words
            totals["images"] += images
            totals["blocks"] += blocks
            totals["tables"] += tables
            languages.append(language)
        page_count = len(doc)
    text_pages = sum(int(p["has_text"]) for p in pages)
    language_counts = {lang: languages.count(lang) for lang in sorted(set(languages))}
    summary = {"file_name": path.name, "path": str(path), "pages": page_count,
               "pages_with_text": text_pages, "pages_without_text": page_count - text_pages,
               "text_present": "yes" if totals["characters"] else "no",
               "text_on_all_pages": "yes" if page_count and text_pages == page_count else "no",
               "text_coverage_pct": round(text_pages / page_count * 100, 1) if page_count else 0,
               "total_characters": totals["characters"], "total_words": totals["words"],
               "tables_estimate": totals["tables"], "images": totals["images"],
               "text_blocks": totals["blocks"], "languages": ", ".join(language_counts) or "none",
               "language_pages": language_counts,
               "docling_risk": "high" if text_pages < page_count else ("medium" if totals["characters"] < 1000 else "low")}
    return summary, pages


def error_summary(path: Path, exc: Exception) -> dict[str, Any]:
    return {"file_name": path.name, "path": str(path), "pages": 0,
            "pages_with_text": 0, "pages_without_text": 0, "text_present": "no",
            "text_on_all_pages": "no", "text_coverage_pct": 0, "total_characters": 0,
            "total_words": 0, "tables_estimate": 0, "images": 0, "text_blocks": 0,
            "languages": "error", "language_pages": {}, "docling_risk": "error",
            "error": f"{type(exc).__name__}: {exc}"}


def scan_one(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if path.stat().st_size > 25 * 1024 * 1024:
        return ({"file_name": path.name, "path": str(path), "pages": 0,
                 "pages_with_text": 0, "pages_without_text": 0,
                 "text_present": "unknown", "text_on_all_pages": "unknown",
                 "text_coverage_pct": 0, "total_characters": 0, "total_words": 0,
                 "tables_estimate": 0, "images": 0, "text_blocks": 0,
                 "languages": "skipped_large", "language_pages": {},
                 "docling_risk": "error", "error": "Skipped file larger than 25 MB"}, [])
    return scan_pdf(path)


def scan_directory(input_dir: Path, output_json: Path, workers: int | None = None,
                   checkpoint_every: int = 200, resume: Path | None = None) -> None:
    pdfs = sorted((p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"))
    path_manifest = output_json.with_name("pdf_paths.json")
    path_manifest.write_text(
        json.dumps({"input_dir": str(input_dir), "pdf_count": len(pdfs),
                    "paths": [str(path) for path in pdfs]}, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"discovered {len(pdfs)} PDFs; wrote path manifest to {path_manifest}", flush=True)
    summaries: list[dict[str, Any] | None] = [None] * len(pdfs)
    page_details: dict[str, list[dict[str, Any]]] = {}
    completed_paths: set[str] = set()
    checkpoint_path = resume or output_json.with_suffix(".checkpoint.json")
    if resume and resume.exists():
        checkpoint = json.loads(resume.read_text(encoding="utf-8"))
        prior = {item.get("path"): item for item in checkpoint.get("summaries", []) if item}
        for index, path in enumerate(pdfs):
            if str(path) in prior:
                summaries[index] = prior[str(path)]
                completed_paths.add(str(path))
        page_details.update(checkpoint.get("page_details", {}))
        print(f"resuming {len(completed_paths)} completed PDFs from {resume}", flush=True)
    worker_count = workers or min(16, (os.cpu_count() or 4) * 2)
    with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="pdf-scan") as pool:
        futures = {pool.submit(scan_one, path): (index, path) for index, path in enumerate(pdfs)
                   if str(path) not in completed_paths}
        new_completed = 0
        for future in as_completed(futures):
            index, path = futures[future]
            try:
                summary, pages = future.result()
            except Exception as exc:
                summary, pages = error_summary(path, exc), []
            summaries[index] = summary
            if pages:
                page_details[str(path)] = pages
            new_completed += 1
            total_completed = len(completed_paths) + new_completed
            if new_completed % 25 == 0 or total_completed == len(pdfs):
                print(f"scanned {total_completed}/{len(pdfs)} PDFs with {worker_count} workers", flush=True)
            if checkpoint_every and new_completed % checkpoint_every == 0:
                checkpoint_path.write_text(json.dumps({"input_dir": str(input_dir),
                    "pdf_count": len(pdfs), "summaries": summaries,
                    "page_details": page_details, "workers": worker_count},
                    ensure_ascii=False), encoding="utf-8")
                print(f"checkpoint: {checkpoint_path}", flush=True)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(),
                                       "input_dir": str(input_dir), "pdf_count": len(pdfs),
                                       "summaries": summaries, "page_details": page_details,
                                       "workers": worker_count,
                                       "path_manifest": str(path_manifest)},
                                      ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(summaries)} PDF records to {output_json}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("/Users/dc/united"))
    parser.add_argument("--output-json", type=Path, default=Path("/Users/dc/united/pdf_inventory.json"))
    parser.add_argument("--workers", type=int, default=None,
                        help="Concurrent PDF workers (default: up to 16)")
    parser.add_argument("--checkpoint-every", type=int, default=200)
    parser.add_argument("--resume", type=Path, default=None,
                        help="Resume from a checkpoint JSON file")
    args = parser.parse_args()
    scan_directory(args.input_dir, args.output_json, args.workers,
                   args.checkpoint_every, args.resume)
