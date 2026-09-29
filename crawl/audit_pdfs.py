"""Recursively validate PDFs and inventory their page counts.

Usage:
    python audit_pdfs.py
    python audit_pdfs.py --root /Users/dc/united --output /Users/dc/united/crawl/pdf_pages.txt
    python audit_pdfs.py --deep  # Also parse text on every page (much slower).
    python audit_pdfs.py --html --pdf /Users/dc/united/pdfs/example.pdf
    python audit_pdfs.py --html  # Export all PDFs (potentially large and slow).

The main report is tab-separated: full path, then page count. PDFs that cannot
be parsed or have zero pages are written to a separate error report.
HTML export preserves PDF page positioning; it does not perform OCR or recover
semantic table structure.
"""

from __future__ import annotations

import argparse
import html
import os
import sys
import tempfile
from pathlib import Path

import pymupdf


def audit_pdf(path: Path, *, deep: bool = False) -> tuple[int | None, str | None]:
    """Return (page count, error), loading every page to check the page tree."""
    try:
        with pymupdf.open(path) as document:
            if not document.is_pdf:
                return None, "not a PDF"
            if document.needs_pass:
                return None, "password-protected PDF"
            page_count = document.page_count
            if page_count < 1:
                return None, "PDF has no pages"
            for page_number in range(page_count):
                page = document.load_page(page_number)
                if deep:
                    page.get_text("text")
            return page_count, None
    except Exception as exc:  # Keep scanning after a malformed PDF.
        return None, f"{type(exc).__name__}: {exc}"


def find_pdfs(root: Path):
    """Yield PDFs in stable order, without following directory symlinks."""
    excluded_dirs = {".venv", "venv", ".git", "__pycache__", "node_modules"}
    for directory, subdirs, filenames in os.walk(root, followlinks=False):
        subdirs[:] = sorted(name for name in subdirs if name not in excluded_dirs)
        for filename in sorted(filenames):
            if filename.lower().endswith(".pdf"):
                yield Path(directory, filename).resolve()


def export_html(pdf_path: Path, html_path: Path) -> None:
    """Write one standalone, positioned HTML document for a PDF, atomically."""
    html_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with pymupdf.open(pdf_path) as document:
            if document.needs_pass:
                raise ValueError("password-protected PDF")
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", suffix=".html.tmp",
                dir=html_path.parent, delete=False
            ) as output:
                temporary_path = Path(output.name)
                output.write("<!doctype html>\n<html lang=\"en\">\n<head>\n")
                output.write('<meta charset="utf-8">\n')
                output.write(f"<title>{html.escape(pdf_path.name)}</title>\n")
                output.write(
                    "<style>\n"
                    "body { margin: 0; padding: 24px; background: #eee; }\n"
                    "section { margin: 0 auto 24px; width: fit-content; }\n"
                    "section > div { position: relative; overflow: hidden; "
                    "background: white; box-shadow: 0 2px 8px #bbb; }\n"
                    "section p { position: absolute; margin: 0; white-space: pre; }\n"
                    "</style>\n"
                )
                output.write("</head>\n<body>\n")
                for page_number in range(document.page_count):
                    output.write(
                        f'<section aria-label="Page {page_number + 1}">\n'
                    )
                    page_html = document.load_page(page_number).get_text("html")
                    output.write(
                        page_html.replace('id="page0"', f'id="page{page_number + 1}"', 1)
                    )
                    output.write("\n</section>\n")
                output.write("</body>\n</html>\n")
        os.replace(temporary_path, html_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/Users/dc/united"))
    parser.add_argument(
        "--output", type=Path, default=Path("/Users/dc/united/crawl/pdf_pages.txt")
    )
    parser.add_argument("--deep", action="store_true", help="Also parse every page's text")
    parser.add_argument("--html", action="store_true", help="Export positioned HTML for each PDF")
    parser.add_argument(
        "--html-dir", type=Path, default=Path("/Users/dc/united/crawl/html"),
        help="HTML output root; mirrors PDF paths beneath --root"
    )
    parser.add_argument("--pdf", type=Path, help="Process just this PDF beneath --root")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    output = args.output.expanduser().resolve()
    errors = output.with_name(output.stem + "_errors.txt")
    html_dir = args.html_dir.expanduser().resolve()

    if not root.is_dir():
        parser.error(f"root is not a directory: {root}")
    if args.pdf is not None:
        selected_pdf = args.pdf.expanduser().resolve()
        if not selected_pdf.is_file() or selected_pdf.suffix.lower() != ".pdf":
            parser.error(f"not a PDF file: {selected_pdf}")
        if not selected_pdf.is_relative_to(root):
            parser.error(f"--pdf must be beneath --root: {selected_pdf}")
        pdfs = [selected_pdf]
    else:
        pdfs = find_pdfs(root)

    output.parent.mkdir(parents=True, exist_ok=True)
    valid_count = 0
    invalid_count = 0
    html_count = 0
    with output.open("w", encoding="utf-8") as report, errors.open(
        "w", encoding="utf-8"
    ) as error_report:
        report.write("full_path\tpage_count\n")
        error_report.write("full_path\terror\n")
        for path in pdfs:
            page_count, error = audit_pdf(path, deep=args.deep)
            if error is None and args.html:
                relative_path = path.relative_to(root)
                html_path = html_dir / relative_path.parent / (relative_path.name + ".html")
                try:
                    export_html(path, html_path)
                    html_count += 1
                except Exception as exc:
                    error = f"HTML export failed: {type(exc).__name__}: {exc}"
            if error is None:
                report.write(f"{path}\t{page_count}\n")
                valid_count += 1
            else:
                error_report.write(f"{path}\t{error}\n")
                invalid_count += 1
            if (valid_count + invalid_count) % 100 == 0:
                print(f"Checked {valid_count + invalid_count} PDFs...", file=sys.stderr)

    print(f"Valid PDFs: {valid_count}; invalid PDFs: {invalid_count}")
    if args.html:
        print(f"HTML files exported: {html_count} to {html_dir}")
    print(f"Report: {output}")
    print(f"Errors: {errors}")
    return 0 if invalid_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
