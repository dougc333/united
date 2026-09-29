"""Incrementally profile PDFs with Docling and save per-file JSONL statistics.

Examples:
    python profile_pdfs.py --pdf /Users/dc/united/pdfs/example.pdf
    python profile_pdfs.py --limit 10
    python profile_pdfs.py                 # resume the entire PDF tree

The JSONL index is append-only. The newest record for a path wins; unchanged
successful files are skipped on subsequent runs unless --force is supplied.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import tempfile
import time
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(__file__).resolve().parent / "profile_data"
COUNT_FIELDS = (
    "num_pages",
    "num_tables",
    "num_pictures",
    "num_texts",
    "num_section_headers",
    "num_list_items",
    "num_code_items",
    "num_formulas",
    "num_pictures_for_ocr",
)
SKIP_DIRS = {".venv", "venv", ".git", "__pycache__", "node_modules", "crawl"}


def find_pdfs(root: Path):
    for directory, subdirs, filenames in os.walk(root, followlinks=False):
        subdirs[:] = sorted(name for name in subdirs if name not in SKIP_DIRS)
        for name in sorted(filenames):
            if name.lower().endswith(".pdf"):
                yield (Path(directory) / name).resolve()


def load_records(index: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    if not index.exists():
        return records
    with index.open(encoding="utf-8") as source:
        for line in source:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue  # An interrupted append must not invalidate previous rows.
            if isinstance(record, dict) and isinstance(record.get("relative_path"), str):
                records[record["relative_path"]] = record
    return records


def summarize(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    all_records = list(records.values())
    successful = [r for r in all_records if r.get("status") in {"success", "partial_success"}]
    totals = {key: sum(int(r.get("stats", {}).get(key, 0)) for r in successful) for key in COUNT_FIELDS}
    page_counts = [int(r.get("stats", {}).get("num_pages", 0)) for r in successful]
    table_counts = [int(r.get("stats", {}).get("num_tables", 0)) for r in successful]
    return {
        "profiled_files": len(successful),
        "failed_files": sum(r.get("status") == "failure" for r in all_records),
        "partial_files": sum(r.get("status") == "partial_success" for r in all_records),
        "status_counts": dict(Counter(r.get("status", "unknown") for r in all_records)),
        "totals": totals,
        "pages": {
            "min": min(page_counts, default=0),
            "median": statistics.median(page_counts) if page_counts else 0,
            "mean": statistics.mean(page_counts) if page_counts else 0,
            "max": max(page_counts, default=0),
        },
        "tables": {
            "min": min(table_counts, default=0),
            "median": statistics.median(table_counts) if table_counts else 0,
            "mean": statistics.mean(table_counts) if table_counts else 0,
            "max": max(table_counts, default=0),
        },
        "ocr_note": "num_pictures_for_ocr counts detected pictures covering >=5% of a page; it does not verify OCR need or accuracy.",
    }


def save_summary(path: Path, summary: dict[str, Any]) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, suffix=".json.tmp", delete=False
        ) as output:
            temporary_path = Path(output.name)
            json.dump(summary, output, indent=2, ensure_ascii=False)
            output.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def profile_pdf(path: Path, converter: Any) -> dict[str, Any]:
    """Convert a PDF once and profile the resulting DoclingDocument."""
    from docling_core.transforms.profiler import DocumentProfiler

    start = time.monotonic()
    result = converter.convert(path, raises_on_error=False)
    status = getattr(result.status, "value", str(result.status)).lower()
    if status not in {"success", "partial_success"} or result.document is None:
        raise RuntimeError(f"Docling conversion status: {status}")
    stats = DocumentProfiler.profile_document(result.document)
    return {
        "status": status,
        "stats": stats.model_dump(mode="json"),
        "conversion_seconds": round(time.monotonic() - start, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--pdf", type=Path, help="Profile only one PDF under --root")
    parser.add_argument("--limit", type=int, help="Stop after this many newly processed PDFs")
    parser.add_argument("--force", action="store_true", help="Reprocess unchanged files")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    data_dir = args.data_dir.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"root is not a directory: {root}")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    if args.pdf:
        pdf = args.pdf.expanduser().resolve()
        if not pdf.is_file() or pdf.suffix.lower() != ".pdf" or not pdf.is_relative_to(root):
            parser.error("--pdf must be an existing PDF beneath --root")
        pdfs = [pdf]
    else:
        pdfs = find_pdfs(root)

    data_dir.mkdir(parents=True, exist_ok=True)
    index = data_dir / "profiles.jsonl"
    records = load_records(index)
    converter = None  # Avoid loading heavy models if every file can be skipped.
    processed = 0
    for path in pdfs:
        rel = path.relative_to(root).as_posix()
        file_stat = path.stat()
        existing = records.get(rel)
        if (
            not args.force
            and existing is not None
            and existing.get("status") in {"success", "partial_success"}
            and existing.get("size_bytes") == file_stat.st_size
            and existing.get("mtime_ns") == file_stat.st_mtime_ns
        ):
            continue
        if converter is None:
            from docling.document_converter import DocumentConverter

            converter = DocumentConverter()
        record: dict[str, Any] = {
            "relative_path": rel,
            "path": str(path),
            "size_bytes": file_stat.st_size,
            "mtime_ns": file_stat.st_mtime_ns,
        }
        try:
            record.update(profile_pdf(path, converter))
        except Exception as exc:
            record.update(status="failure", error=f"{type(exc).__name__}: {exc}")
        with index.open("a", encoding="utf-8") as output:
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
        records[rel] = record
        processed += 1
        stats = record.get("stats", {})
        print(
            f"[{processed}] {record['status']}: {rel} "
            f"({stats.get('num_pages', '?')} pages, {stats.get('num_tables', '?')} tables)",
            flush=True,
        )
        save_summary(data_dir / "summary.json", summarize(records))
        if args.limit is not None and processed >= args.limit:
            break

    summary = summarize(records)
    save_summary(data_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    print(f"Per-file records: {index}")
    return 0 if summary["failed_files"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
