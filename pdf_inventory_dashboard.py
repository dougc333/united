"""Streamlit viewer for the recursive PDF inventory JSON."""
from pathlib import Path
import json

import pandas as pd
import streamlit as st

DEFAULT_JSON = Path("/Users/dc/united/pdf_inventory.json")
st.set_page_config(page_title="PDF inventory", layout="wide")
st.title("PDF extraction inventory")
st.caption("Loaded from a precomputed recursive PDF scan; rescan separately when files change.")

with st.sidebar:
    json_path = Path(st.text_input("Inventory JSON", str(DEFAULT_JSON))).expanduser()
    if st.button("Reload JSON"):
        st.cache_data.clear()
        st.rerun()

@st.cache_data
def load_inventory(path: str):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return pd.DataFrame(payload.get("summaries", [])), payload.get("page_details", {}), payload

if not json_path.exists():
    st.error(f"Inventory not found: {json_path}")
    st.info("Run pdf_inventory_scan.py first.")
    st.stop()

summary, page_details, payload = load_inventory(str(json_path))
st.caption(f"Generated: {payload.get('generated_at', 'unknown')} | Input: {payload.get('input_dir', 'unknown')}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("PDF files", len(summary))
c2.metric("Pages", int(summary["pages"].sum()))
c3.metric("Image-only PDFs", int((summary["pages_without_text"] > 0).sum()))
c4.metric("Estimated tables", int(summary["tables_estimate"].sum()))

st.subheader("Distributions")
left, right = st.columns(2)
with left:
    st.write("Tables per PDF")
    st.bar_chart(summary["tables_estimate"].value_counts().sort_index().rename("PDF count"))
    st.write("Pages per PDF")
    st.bar_chart(summary["pages"].value_counts().sort_index().rename("PDF count"))
with right:
    st.write("Images per PDF")
    st.bar_chart(summary["images"].value_counts().sort_index().rename("PDF count"))
    language_counts = {}
    for value in summary["language_pages"].tolist():
        for language, count in (value or {}).items():
            language_counts[language] = language_counts.get(language, 0) + count
    st.write("Detected language by page")
    st.bar_chart(pd.Series(language_counts, name="Page count").sort_values(ascending=False))

st.subheader("PDFs with image-only pages")
image_only = summary[summary["pages_without_text"] > 0]
st.dataframe(image_only[["file_name", "path", "pages", "pages_without_text", "total_characters", "images", "tables_estimate", "languages", "docling_risk"]], use_container_width=True, hide_index=True)

st.subheader("All PDF results")
st.dataframe(summary.drop(columns=["language_pages"], errors="ignore"), use_container_width=True, hide_index=True)
st.download_button("Download inventory CSV", summary.to_csv(index=False).encode(), "pdf_inventory.csv", "text/csv")

if not summary.empty:
    selected = st.selectbox("Inspect pages", summary["file_name"].tolist())
    selected_path = summary.loc[summary["file_name"] == selected, "path"].iloc[0]
    st.dataframe(pd.DataFrame(page_details.get(selected_path, [])), use_container_width=True, hide_index=True)
