"""Streamlit viewer for the incremental Docling PDF profiler.

Run: streamlit run /Users/dc/united/crawl/profile_app.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pymupdf
import streamlit as st

from profile_pdfs import COUNT_FIELDS, DATA_DIR, load_records, summarize


st.set_page_config(page_title="United PDF profiler", layout="wide")
st.title("United PDF profiler")
st.caption("Docling-derived structure statistics. Only processed PDFs appear here; this is not an OCR-quality or extraction-accuracy score.")

data_dir = Path(st.sidebar.text_input("Profile data directory", str(DATA_DIR))).expanduser()
index = data_dir / "profiles.jsonl"
if st.sidebar.button("Refresh results"):
    st.rerun()

if not index.exists():
    st.info(f"No profiles yet: {index}. Run profile_pdfs.py --limit 1 first.")
    st.stop()

records = load_records(index)
summary = summarize(records)
if not records:
    st.info("The profile index is empty.")
    st.stop()

st.subheader("Cumulative statistics")
columns = st.columns(6)
for col, (label, value) in zip(
    columns,
    (
        ("Profiled PDFs", summary["profiled_files"]),
        ("Failed PDFs", summary["failed_files"]),
        ("Pages", summary["totals"]["num_pages"]),
        ("Tables", summary["totals"]["num_tables"]),
        ("Pictures", summary["totals"]["num_pictures"]),
        ("Text items", summary["totals"]["num_texts"]),
    ),
):
    col.metric(label, value)

st.caption(
    f"Pages per PDF: min {summary['pages']['min']} · median {summary['pages']['median']:g} · "
    f"mean {summary['pages']['mean']:.1f} · max {summary['pages']['max']}. "
    f"{summary['partial_files']} partial conversions."
)
st.warning(summary["ocr_note"])

successful = [
    record for record in records.values()
    if record.get("status") in {"success", "partial_success"}
]
if successful:
    chart_data = pd.DataFrame(
        {
            "PDF": [r["relative_path"] for r in successful],
            "Pages": [r["stats"]["num_pages"] for r in successful],
            "Tables": [r["stats"]["num_tables"] for r in successful],
        }
    ).set_index("PDF")
    left, right = st.columns(2)
    with left:
        st.write("Pages by document")
        st.bar_chart(chart_data["Pages"])
    with right:
        st.write("Tables by document")
        st.bar_chart(chart_data["Tables"])

st.subheader("Single PDF")
search = st.text_input("Filter by filename or path")
matches = sorted(path for path in records if search.lower() in path.lower())
if not matches:
    st.info("No matching profiled PDFs.")
    st.stop()
selected = st.selectbox("Profiled PDF", matches)
record = records[selected]
st.write(f"**Full path:** `{record['path']}`")
st.write(f"**Status:** {record['status']}")
if record.get("error"):
    st.error(record["error"])
else:
    stats = record["stats"]
    selected_columns = st.columns(5)
    for col, field in zip(
        selected_columns,
        ("num_pages", "num_tables", "num_pictures", "num_texts", "num_pictures_for_ocr"),
    ):
        col.metric(field.removeprefix("num_").replace("_", " ").title(), stats.get(field, 0))
    st.dataframe(
        pd.DataFrame(
            [{"Measure": field.removeprefix("num_").replace("_", " ").title(), "Count": stats.get(field, 0)} for field in COUNT_FIELDS]
        ),
        hide_index=True,
        width="stretch",
    )
    st.caption(f"Conversion time: {record.get('conversion_seconds', 0):.1f} s")
    with st.expander("Complete Docling profiler record"):
        st.json(stats)

pdf_path = Path(record["path"])
if pdf_path.is_file():
    with st.expander("View source PDF page"):
        try:
            with pymupdf.open(pdf_path) as document:
                page_number = st.number_input(
                    "Page", min_value=1, max_value=max(1, document.page_count), value=1
                )
                page = document.load_page(page_number - 1)
                pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1.3, 1.3), alpha=False)
                st.image(pixmap.tobytes("png"), caption=f"Source PDF page {page_number}")
        except Exception as exc:
            st.error(f"Could not render source PDF: {exc}")

st.subheader("All profiled files")
rows = [
    {
        "PDF": path,
        "Status": rec.get("status", "unknown"),
        "Pages": rec.get("stats", {}).get("num_pages"),
        "Tables": rec.get("stats", {}).get("num_tables"),
        "Pictures": rec.get("stats", {}).get("num_pictures"),
        "Text items": rec.get("stats", {}).get("num_texts"),
    }
    for path, rec in sorted(records.items())
]
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
st.download_button(
    "Download cumulative summary",
    json.dumps(summary, indent=2),
    file_name="docling_profile_summary.json",
    mime="application/json",
)
