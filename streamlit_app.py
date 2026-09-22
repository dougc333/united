"""Browse recursively downloaded PDFs and compare recursive chunking policies."""

from __future__ import annotations

import math
import os
import json
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st
from transformers import AutoTokenizer

from src.eval_pipeline import (
    append_evals,
    error_path,
    eval_path,
    generate_page_evals,
    grade_ranked,
    load_evals,
    load_page_errors,
    pdf_digest,
    rank_queries,
    relevant_chunk_ids,
    render_page_png,
    result_path,
    page_spans,
    update_page_error,
)
from src.pdf_chunking import (
    EMBEDDING_MODEL_NAME,
    POLICIES,
    count_tokens,
    extract_pages,
    find_pdfs,
    split_pdf,
)


ROOT = Path(__file__).resolve().parent
PDF_ROOT = ROOT / "pdfs"

st.set_page_config(page_title="United PDF chunking explorer", layout="wide")
st.title("United PDF chunking explorer")
st.caption(
    "Select any PDF in pdfs/ to compare the test.py character baseline with the chunks "
    "produced by a selected RecursiveCharacterTextSplitter policy. Token counts use "
    f"{EMBEDDING_MODEL_NAME}."
)


@st.cache_data(ttl=60, show_spinner=False)
def pdf_inventory(root: str) -> list[tuple[str, float]]:
    base = Path(root)
    return [
        (str(path.relative_to(base)), round(path.stat().st_size / (1024 * 1024), 2))
        for path in find_pdfs(base)
    ]


@st.cache_data(show_spinner=False)
def cached_pages(path: str, mtime_ns: int, size: int) -> list[tuple[int, str]]:
    # The metadata arguments invalidate this cache if the PDF changes.
    return extract_pages(Path(path))


@st.cache_resource(show_spinner="Loading the embedding tokenizer...")
def tokenizer_for(model_name: str):
    try:
        return AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    except OSError:
        return AutoTokenizer.from_pretrained(model_name)


@st.cache_resource(show_spinner="Loading BGE embedding model...")
def embedding_model_for(model_name: str):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


@st.cache_data(show_spinner=False)
def cached_policy_chunks(
    path: str, mtime_ns: int, size: int, source: str, policy_label: str
):
    """Keep full-PDF chunk IDs stable while stepping through pages."""
    selected_policy = next(item for item in POLICIES if item.label == policy_label)
    pages = cached_pages(path, mtime_ns, size)
    return split_pdf(pages, source, selected_policy, tokenizer_for(EMBEDDING_MODEL_NAME))


def step_review_page(delta: int, total_pages: int) -> None:
    st.session_state["review_page"] = min(
        total_pages, max(1, st.session_state["review_page"] + delta)
    )


@st.cache_data(show_spinner=False)
def cached_page_image(path: str, mtime_ns: int, page_num: int) -> bytes:
    return render_page_png(Path(path), page_num)


@st.cache_data(show_spinner=False)
def cached_pdf_digest(path: str, mtime_ns: int, size: int) -> str:
    return pdf_digest(Path(path))


@st.cache_data(show_spinner=False)
def saved_eval_status(
    eval_file: str,
    eval_mtime_ns: int,
    eval_size: int,
    pdf_sha256: str,
) -> tuple[list[dict], str | None]:
    """Read source-matched evals; file metadata invalidates the cache."""
    try:
        rows = load_evals(Path(eval_file), pdf_sha256)
        required = {"query", "answer", "evidence_quote", "page_num"}
        if any(not required.issubset(row) for row in rows):
            return [], "Saved evals have missing fields."
        return rows, None
    except (OSError, ValueError, TypeError) as exc:
        return [], str(exc)


def length_histogram(
    lengths: list[int], title: str, xlabel: str, *, limit: int | None = None
):
    fig, ax = plt.subplots(figsize=(7, 4), dpi=110)
    if lengths:
        bins = min(30, max(5, math.ceil(math.sqrt(len(lengths)))))
        ax.hist(lengths, bins=bins, color="#2875ad", edgecolor="white")
    else:
        ax.text(0.5, 0.5, "No extractable text", ha="center", va="center", transform=ax.transAxes)
    if limit is not None:
        ax.axvline(limit, color="#c92c38", linestyle="--", linewidth=1.5, label=f"model limit: {limit}")
        ax.legend(loc="upper right")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Count")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig


def show_inventory(items: list[tuple[str, float]]) -> None:
    st.subheader(f"All PDFs ({len(items):,})")
    st.dataframe(
        [{"PDF filename / relative path": name, "Size (MiB)": size} for name, size in items],
        width="stretch",
        hide_index=True,
        height=420,
    )


if not PDF_ROOT.is_dir():
    st.error(f"PDF directory not found: {PDF_ROOT}")
    st.stop()

if st.button("Refresh PDF list"):
    pdf_inventory.clear()

inventory = pdf_inventory(str(PDF_ROOT))
if not inventory:
    st.warning(f"No PDFs found under {PDF_ROOT}")
    st.stop()

names = [name for name, _ in inventory]
with st.sidebar:
    st.header("Analysis")
    selected_name = st.selectbox("PDF (search by filename or path)", names)
    policy = st.selectbox("Chunking scheme", POLICIES, format_func=lambda item: item.label)
    analyze = st.button("Analyze selected PDF", type="primary")
    st.caption("Only the selected PDF is opened; the full inventory appears below the plots.")

if analyze:
    st.session_state["analysis_selection"] = (selected_name, policy.label)
if st.session_state.get("analysis_selection") != (selected_name, policy.label):
    st.info("Choose a PDF and chunking scheme, then click **Analyze selected PDF**.")
    show_inventory(inventory)
    st.stop()

selected_path = (PDF_ROOT / selected_name).resolve()
if not selected_path.is_relative_to(PDF_ROOT.resolve()) or not selected_path.is_file():
    st.error("Invalid PDF selection")
    st.stop()

try:
    tokenizer = tokenizer_for(EMBEDDING_MODEL_NAME)
    info = selected_path.stat()
    with st.spinner("Extracting PDF pages and splitting text..."):
        pages = cached_pages(str(selected_path), info.st_mtime_ns, info.st_size)
        baseline_chunks = cached_policy_chunks(
            str(selected_path), info.st_mtime_ns, info.st_size, selected_name, POLICIES[-1].label
        )
        chunks = (
            baseline_chunks if policy == POLICIES[-1] else cached_policy_chunks(
                str(selected_path), info.st_mtime_ns, info.st_size, selected_name, policy.label
            )
        )
        baseline_lengths = [count_tokens(doc.page_content, tokenizer) for doc in baseline_chunks]
        chunk_lengths = [count_tokens(doc.page_content, tokenizer) for doc in chunks]
except Exception as exc:
    st.error(f"Could not analyze {selected_name}: {type(exc).__name__}: {exc}")
    st.stop()

model_limit = tokenizer.model_max_length
if not isinstance(model_limit, int) or model_limit > 1_000_000:
    model_limit = None

st.subheader("Page retrieval evals")
st.caption(
    "Generate sends each selected page image and its extracted text to OpenAI. "
    "Three short-answer questions per text-bearing page are saved with a verbatim evidence quote. "
    "Pages without extractable text need OCR and are skipped. Retrieval is ranked over every chunk in this PDF."
)
saved_path = eval_path(PDF_ROOT, selected_path)
pdf_sha256 = cached_pdf_digest(str(selected_path), info.st_mtime_ns, info.st_size)
generation_error_path = error_path(saved_path)
page_errors = load_page_errors(generation_error_path, pdf_sha256)
if saved_path.is_file():
    eval_info = saved_path.stat()
    disk_evals, saved_error = saved_eval_status(
        str(saved_path), eval_info.st_mtime_ns, eval_info.st_size,
        pdf_sha256,
    )
else:
    disk_evals, saved_error = [], None
saved_count = len(disk_evals)
saved_pages = len({int(row["page_num"]) for row in disk_evals})
if "eval_notice" in st.session_state:
    notice, warnings = st.session_state.pop("eval_notice")
    st.success(notice)
    for warning in warnings:
        st.warning(warning)
controls = st.columns([1, 1, 1, 1])
with controls[0]:
    first_page = st.number_input("From page", min_value=1, max_value=len(pages), value=1, step=1)
with controls[1]:
    last_page = st.number_input("Through page", min_value=1, max_value=len(pages), value=len(pages), step=1)
with controls[2]:
    create_clicked = st.button("Generate evals", width="stretch")
with controls[3]:
    load_clicked = st.button(
        "Load evals", type="primary" if saved_count else "secondary",
        disabled=not saved_count, width="stretch",
        help=f"{saved_count} saved evals for this PDF" if saved_count else f"No usable evals at {saved_path}",
    )
    if saved_count:
        st.caption(f"Ready: {saved_count} evals across {saved_pages} pages")
    elif saved_error:
        st.caption(f"Saved evals unavailable: {saved_error}")
    else:
        st.caption("No saved evals for this PDF")

state_key = (str(selected_path), info.st_mtime_ns, info.st_size)
if st.session_state.get("eval_state_key") != state_key:
    st.session_state["eval_state_key"] = state_key
    st.session_state.pop("loaded_evals", None)
    st.session_state.pop("eval_results", None)
if st.session_state.get("scored_policy") != policy.label:
    st.session_state["scored_policy"] = policy.label
    st.session_state.pop("eval_results", None)

if create_clicked:
    if first_page > last_page:
        st.error("The first page must be at or before the last page.")
    elif not os.getenv("OPENAI_API_KEY"):
        st.error("Set OPENAI_API_KEY before generating evals. Loading saved evals does not require a key.")
    else:
        from openai import OpenAI

        digest = pdf_sha256
        generation_done = False
        try:
            existing = load_evals(saved_path, digest)
            page_counts = {}
            for row in existing:
                page_counts[int(row["page_num"])] = page_counts.get(int(row["page_num"]), 0) + 1
            completed = {number for number, count in page_counts.items() if count == 3}
            todo = [(number, text) for number, text in pages
                    if first_page <= number <= last_page and text and number not in completed]
            skipped = sum(1 for number, text in pages if first_page <= number <= last_page and not text)
            client = OpenAI()
            progress = st.progress(0, text="Generating page evals...") if todo else None
            failures = []
            for index, (number, text) in enumerate(todo, 1):
                try:
                    image = cached_page_image(str(selected_path), info.st_mtime_ns, number)
                    rows = generate_page_evals(client, "gpt-4.1-mini", image, text, number)
                    for row in rows:
                        row["pdf_sha256"] = digest
                        row["pdf_relative_path"] = selected_name
                    append_evals(saved_path, rows)
                    update_page_error(generation_error_path, digest, number, None)
                except Exception as exc:
                    message = f"{type(exc).__name__}: {exc}"
                    failures.append(f"Page {number}: {message}")
                    update_page_error(generation_error_path, digest, number, message)
                progress.progress(index / len(todo), text=f"Processed {index}/{len(todo)} pages")
            if not todo:
                st.info("No new text-bearing pages in this range; loading the saved evals.")
            st.session_state["loaded_evals"] = load_evals(saved_path, digest)
            st.session_state.pop("eval_results", None)
            generation_done = True
        except Exception as exc:
            st.error(f"Generation stopped: {type(exc).__name__}: {exc}")
        if generation_done:
            warnings = []
            if failures:
                warnings.append(f"{len(failures)} pages failed; rerun to retry them. " + " | ".join(failures[:3]))
            if skipped:
                warnings.append(f"Skipped {skipped} image-only/empty pages without extractable text.")
            st.session_state["eval_notice"] = (
                f"Saved {len(st.session_state['loaded_evals'])} evals to {saved_path}", warnings
            )
            st.rerun()

if load_clicked:
    try:
        st.session_state["loaded_evals"] = load_evals(saved_path, pdf_sha256)
        st.session_state.pop("eval_results", None)
        if not st.session_state["loaded_evals"]:
            st.warning(f"No saved evals found at {saved_path}")
    except Exception as exc:
        st.error(f"Could not load evals: {type(exc).__name__}: {exc}")

eval_rows = st.session_state.get("loaded_evals", [])
if eval_rows and "eval_results" not in st.session_state:
    try:
        with st.spinner("Embedding chunks and queries; ranking the full PDF..."):
            rankings = rank_queries(eval_rows, chunks, embedding_model_for(EMBEDDING_MODEL_NAME))
            results = []
            for row, ranked in zip(eval_rows, rankings):
                relevant = relevant_chunk_ids(row, pages, chunks)
                grade = grade_ranked(ranked, relevant)
                results.append({**row, **grade, "top_chunk_ids": ranked[:3],
                                "relevant_chunk_ids": sorted(relevant),
                                "chunk_policy": policy.label,
                                "embedding_model": EMBEDDING_MODEL_NAME})
            st.session_state["eval_results"] = results
            output_path = result_path(saved_path, policy.label)
            output_path.write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in results),
                encoding="utf-8",
            )
    except Exception as exc:
        st.error(f"Could not score retrieval: {type(exc).__name__}: {exc}")

results = st.session_state.get("eval_results", [])
if results:
    st.caption(f"Eval file: `{saved_path}` · Scored results: `{result_path(saved_path, policy.label)}`")
    score_columns = st.columns(5)
    for column, (label, field) in zip(score_columns, [
        ("Recall@1", "recall_at_1"), ("Recall@2", "recall_at_2"),
        ("Recall@3", "recall_at_3"), ("MRR@3", "mrr_at_3"),
        ("nDCG@3", "ndcg_at_3"),
    ]):
        column.metric(label, f"{sum(row[field] for row in results) / len(results):.3f}")
    st.caption(
        f"{len(results)} evals scored. A hit requires the full evidence quote in a retrieved chunk. "
        "Recall@k is the fraction of questions with at least one evidence-containing chunk in top k; "
        "MRR and nDCG are truncated at 3. These are retrieval scores, not answer accuracy."
    )

review_source = (str(selected_path), info.st_mtime_ns, info.st_size)
if st.session_state.get("review_source") != review_source:
    st.session_state["review_source"] = review_source
    st.session_state["review_page"] = 1

nav = st.columns([1, 2, 1])
with nav[0]:
    st.button(
        "← Previous", disabled=st.session_state["review_page"] <= 1,
        on_click=step_review_page, args=(-1, len(pages)), width="stretch",
    )
with nav[1]:
    st.number_input("Review PDF page", min_value=1, max_value=len(pages),
                    step=1, key="review_page")
with nav[2]:
    st.button(
        "Next →", disabled=st.session_state["review_page"] >= len(pages),
        on_click=step_review_page, args=(1, len(pages)), width="stretch",
    )
page_num = int(st.session_state["review_page"])
viewer, inspection = st.columns([1, 1], gap="large")
with viewer:
    st.image(cached_page_image(str(selected_path), info.st_mtime_ns, page_num),
             caption=f"Source PDF · page {page_num}", width="stretch")
with inspection:
    source_evals = results if results else disk_evals if disk_evals else eval_rows
    page_evals = [row for row in source_evals if int(row["page_num"]) == page_num]
    scored_evals = [row for row in page_evals if "recall_at_3" in row]
    st.markdown(f"#### Page {page_num}: {len(page_evals)} evals")
    if scored_evals:
        st.metric("Correct evidence in top 3", f"{sum(row['recall_at_3'] for row in scored_evals)}/{len(scored_evals)}")
    if not page_evals:
        page_text = dict(pages).get(page_num, "")
        if page_num in page_errors:
            st.error(f"Eval generation failed on page {page_num}: {page_errors[page_num]}")
            st.caption("Click Generate evals to retry missing pages; completed pages are skipped.")
        elif not page_text:
            st.error("No evals: this page has no extractable text. OCR is required before generation.")
        else:
            st.error(
                f"No evals saved for page {page_num}, although {len(page_text):,} characters "
                "were extracted. The previous version did not retain failure details, so its "
                "exact error is unavailable. Click Generate evals to retry missing pages."
            )
    for index, row in enumerate(page_evals, 1):
        scored = "recall_at_3" in row
        hit = bool(row.get("recall_at_3"))
        with st.container(border=True):
            indicator = "✅" if hit else "❌" if scored else "○"
            st.markdown(f"**{indicator} Eval {index}: {row['query']}**")
            st.write(f"Answer: {row['answer']}")
            st.caption(f"PDF evidence: “{row['evidence_quote']}”")
            if not scored:
                st.info("Saved eval. Click Load evals to compute retrieval scores.")
            elif hit:
                st.success(f"Correct evidence retrieved at rank {row['first_relevant_rank']}.")
            else:
                st.error("Correct evidence not retrieved in the top 3.")
            if scored and not row["evidence_covered"]:
                st.error("No chunk contains the entire evidence span (chunk-boundary miss).")
            elif scored:
                st.caption(
                    f"Recall@1/2/3: {row['recall_at_1']}/{row['recall_at_2']}/{row['recall_at_3']} "
                    f"· MRR@3 {row['mrr_at_3']:.2f} · nDCG@3 {row['ndcg_at_3']:.2f}"
                )
            for rank, chunk_id in enumerate(row.get("top_chunk_ids", []), 1):
                correct = chunk_id in row["relevant_chunk_ids"]
                with st.expander(f"{'✅ MATCH' if correct else '○ no match'} · rank {rank} · chunk {chunk_id}"):
                    if correct:
                        st.success("Contains the complete PDF evidence quote")
                    st.write(chunks[chunk_id].page_content)
    st.markdown("#### Chunks by strategy")
    st.caption("These are all chunks overlapping this page. A check marks a chunk containing a saved eval's complete evidence quote; only the selected sidebar strategy has retrieval scores above.")
    page_span = page_spans(pages).get(page_num)
    for strategy in POLICIES:
        strategy_chunks = (
            chunks if strategy == policy else baseline_chunks if strategy == POLICIES[-1]
            else cached_policy_chunks(
                str(selected_path), info.st_mtime_ns, info.st_size,
                selected_name, strategy.label,
            )
        )
        if page_span:
            left_offset, right_offset = page_span
            page_chunk_ids = [i for i, chunk in enumerate(strategy_chunks)
                              if 0 <= chunk.metadata.get("start_index", -1) < right_offset
                              and chunk.metadata["start_index"] + len(chunk.page_content) > left_offset]
        else:
            page_chunk_ids = []
        evidence_for_chunk = {}
        for eval_index, row in enumerate(page_evals, 1):
            for chunk_id in relevant_chunk_ids(row, pages, strategy_chunks):
                evidence_for_chunk.setdefault(chunk_id, []).append(eval_index)
        with st.expander(
            f"{strategy.label}{' · selected' if strategy == policy else ''} "
            f"· {len(page_chunk_ids)} page chunks", expanded=strategy == policy,
        ):
            if not page_chunk_ids:
                st.caption("No extractable text chunks overlap this page.")
            for chunk_id in page_chunk_ids:
                chunk = strategy_chunks[chunk_id]
                matches = evidence_for_chunk.get(chunk_id, [])
                if matches:
                    st.success(f"Chunk {chunk_id} · contains evidence for eval {', '.join(map(str, matches))}")
                else:
                    st.markdown(f"**Chunk {chunk_id}**")
                st.caption(f"{count_tokens(chunk.page_content, tokenizer)} tokens")
                st.write(chunk.page_content)

metrics = st.columns(4)
metrics[0].metric("PDF pages", len(pages))
metrics[1].metric("Baseline segments", len(baseline_chunks))
metrics[2].metric("Chunks", len(chunks))
metrics[3].metric("Chunks over model limit", sum(n > model_limit for n in chunk_lengths) if model_limit else "unknown")

left, right = st.columns(2)
with left:
    page_figure = length_histogram(
        baseline_lengths, "Before: 2,500-character baseline", "Tokens per baseline segment", limit=model_limit
    )
    st.pyplot(page_figure)
    plt.close(page_figure)
with right:
    chunk_figure = length_histogram(
        chunk_lengths, "After: chunk lengths", "Tokens per chunk", limit=model_limit
    )
    st.pyplot(chunk_figure)
    plt.close(chunk_figure)

st.caption(f"Selected PDF: **{selected_name}** · Policy: **{policy.label}**")
st.caption(
    "The first plot matches test.py's 2,500-character recursive baseline; both plots "
    "count tokens with the same tokenizer. PyMuPDF extracts embedded text, not OCR. "
    "The model-limit line counts tokenizer special tokens, so a 512-token policy may produce "
    "slightly over-limit inputs. The character policy is measured in tokens only after splitting."
)

show_inventory(inventory)
