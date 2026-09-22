"""Sample United PDFs and flag text/chunk length outliers.

Run from /Users/dc/united with the dependencies in requirements-streamlit.txt.
This is a length screen, not an answer-quality or boundary-integrity evaluation.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import signal
from pathlib import Path
from statistics import median

import matplotlib.pyplot as plt
from transformers import AutoTokenizer

from src.pdf_chunking import (
    EMBEDDING_MODEL_NAME,
    POLICIES,
    count_tokens,
    extract_pages,
    find_pdfs,
    split_pdf,
)


PDF_ROOT = Path(__file__).resolve().parent / "pdfs"


def sample_by_size(paths: list[Path], n: int, seed: int) -> list[Path]:
    """Take equal-size random samples from ten file-size strata."""
    ranked = sorted(paths, key=lambda path: (path.stat().st_size, str(path)))
    rng = random.Random(seed)
    chosen: list[Path] = []
    for band in range(10):
        group = ranked[band * len(ranked) // 10 : (band + 1) * len(ranked) // 10]
        count = n // 10 + (band < n % 10)
        chosen.extend(rng.sample(group, min(count, len(group))))
    if n >= 10:
        chosen[0] = ranked[0]
        chosen[-1] = ranked[-1]
    return chosen


def percentile(values: list[int], p: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * p)]


def audit(path: Path, tokenizer) -> tuple[dict, list[int], list[int]]:
    pages = extract_pages(path)
    baseline = split_pdf(pages, str(path.relative_to(PDF_ROOT)), POLICIES[-1], tokenizer)
    chunks = split_pdf(pages, str(path.relative_to(PDF_ROOT)), POLICIES[4], tokenizer)
    baseline_lengths = [count_tokens(doc.page_content, tokenizer) for doc in baseline]
    chunk_lengths = [count_tokens(doc.page_content, tokenizer) for doc in chunks]
    page_lengths = [count_tokens(text, tokenizer) for _, text in pages]
    nonempty_pages = [n for n in page_lengths if n]
    flags: list[str] = []
    if not nonempty_pages:
        flags.append("no_extracted_text")
    elif len(nonempty_pages) < len(pages):
        flags.append("empty_pages")
    if sum(nonempty_pages) < 128:
        flags.append("very_short_document")
    if baseline_lengths and max(baseline_lengths) > 512:
        flags.append("baseline_over_embedding_limit")
    if chunk_lengths and max(chunk_lengths) > 512:
        flags.append("chunks_over_embedding_limit")
    if chunk_lengths and sum(n < 32 for n in chunk_lengths) / len(chunk_lengths) >= 0.2:
        flags.append("many_tiny_chunks")
    if len(chunk_lengths) >= 10 and percentile(chunk_lengths, .1) < 64:
        flags.append("short_chunk_tail")
    row = {
        "pdf": str(path.relative_to(PDF_ROOT)),
        "bytes": path.stat().st_size,
        "pages": len(pages),
        "empty_pages": len(pages) - len(nonempty_pages),
        "extracted_tokens": sum(nonempty_pages),
        "baseline_segments": len(baseline_lengths),
        "baseline_median": median(baseline_lengths) if baseline_lengths else 0,
        "baseline_p90": percentile(baseline_lengths, .9),
        "baseline_max": max(baseline_lengths, default=0),
        "chunks": len(chunk_lengths),
        "chunk_median": median(chunk_lengths) if chunk_lengths else 0,
        "chunk_p10": percentile(chunk_lengths, .1),
        "chunk_p90": percentile(chunk_lengths, .9),
        "chunk_min": min(chunk_lengths, default=0),
        "chunk_max": max(chunk_lengths, default=0),
        "chunks_lt_32": sum(n < 32 for n in chunk_lengths),
        "chunks_gt_512": sum(n > 512 for n in chunk_lengths),
        "flags": ";".join(flags),
    }
    return row, baseline_lengths, chunk_lengths


def plot_case(row: dict, before: list[int], after: list[int], target: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), dpi=130)
    for axis, lengths, title in (
        (axes[0], before, "2,500-character baseline"),
        (axes[1], after, "512-token recursive chunks"),
    ):
        if len(lengths) == 1:
            axis.bar(lengths, [1], width=14, color="#2875ad")
            axis.set_xlim(0, max(560, lengths[0] + 30))
        elif lengths:
            axis.hist(lengths, bins=min(25, max(3, math.ceil(math.sqrt(len(lengths))))),
                      color="#2875ad", edgecolor="white")
        else:
            axis.text(.5, .5, "No extracted text", ha="center", va="center", transform=axis.transAxes)
        axis.axvline(512, color="#c92c38", linestyle="--", label="Embedding limit: 512")
        axis.set(title=title, xlabel="BGE tokenizer tokens", ylabel="Count")
        axis.legend(fontsize=8)
        axis.grid(axis="y", alpha=.2)
    fig.suptitle(Path(row["pdf"]).name, fontsize=10, weight="bold")
    fig.text(.5, .01, f'Pages: {row["pages"]}  |  Extracted tokens: {row["extracted_tokens"]}  |  Flags: {row["flags"] or "none"}',
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, .92))
    fig.savefig(target)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=20260921)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds-per-pdf", type=int, default=30)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    paths = sample_by_size(find_pdfs(PDF_ROOT), args.count, args.seed)
    try:
        tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME, local_files_only=True)
    except OSError:
        tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)
    rows: list[dict] = []
    series: dict[str, tuple[list[int], list[int]]] = {}
    def timed_out(_signum, _frame):
        raise TimeoutError(f"Exceeded {args.seconds_per_pdf} seconds")

    signal.signal(signal.SIGALRM, timed_out)
    for index, path in enumerate(paths, 1):
        try:
            signal.setitimer(signal.ITIMER_REAL, args.seconds_per_pdf)
            row, before, after = audit(path, tokenizer)
            rows.append(row)
            series[row["pdf"]] = (before, after)
        except Exception as exc:
            rows.append({"pdf": str(path.relative_to(PDF_ROOT)), "flags": "processing_error", "error": f"{type(exc).__name__}: {exc}"})
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
        if index % 10 == 0:
            print(f"Processed {index}/{len(paths)} PDFs", flush=True)
    with (args.output / "results.csv").open("w", newline="") as handle:
        fields = sorted({key for row in rows for key in row})
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "results.json").write_text(json.dumps({"sample_seed": args.seed, "sample_method": "ten file-size strata; smallest/largest forced", "model": EMBEDDING_MODEL_NAME, "results": rows}, indent=2))
    candidates = [row for row in rows if row["pdf"] in series and row["flags"]]
    candidates.sort(key=lambda row: (
        "no_extracted_text" in row["flags"],
        row.get("chunks_gt_512", 0),
        row.get("baseline_max", 0),
        row.get("chunks_lt_32", 0),
    ), reverse=True)
    for index, row in enumerate(candidates[:12], 1):
        before, after = series[row["pdf"]]
        plot_case(row, before, after, args.output / f"case_{index:02d}.png")
    print(f"Results: {args.output}")
    print(f"Flagged: {len(candidates)}/{len(paths)}")
    for row in candidates[:12]:
        print(row["flags"], row["pdf"])


if __name__ == "__main__":
    main()
