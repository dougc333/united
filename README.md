# United PDF chunking explorer

The Streamlit app recursively lists every PDF under `pdfs/`. It opens only the
selected PDF, extracts and combines page text with PyMuPDF, and plots token
lengths for the 2,500-character recursive baseline from `src/test.py` beside
chunk-token lengths under a selectable recursive splitting policy. The full PDF
inventory appears below the plots. The tokenizer is `BAAI/bge-small-en-v1.5`,
matching `src/test.py`.

From `/Users/dc/united`:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-streamlit.txt
.venv/bin/python -m streamlit run streamlit_app.py
```

The first run may download the tokenizer. Open the local URL printed by
Streamlit, choose a PDF and chunking scheme in the sidebar, then click
**Analyze selected PDF**. The
character baseline and 512-token scheme mirror `src/test.py`; the smaller
token-aware schemes allow comparison. Analysis is cached per PDF version.

## Streamlit apps in this repo

There are four Streamlit apps. Run each from `/Users/dc/united`; Streamlit
serves on http://localhost:8501 (the next free port if one is already running).
Three are viewers for results produced by a separate script, so run that script
first if its output file is missing.

| App | What it does | Reads |
|---|---|---|
| `streamlit_app.py` | PDF chunking explorer (this README). Compares token lengths of the 2,500-character baseline with a selectable recursive chunking policy for one PDF, and generates or loads page-level retrieval evals. | PDFs under `pdfs/` |
| `pdf_inventory_dashboard.py` | PDF extraction inventory. Charts pages, images, estimated tables and page languages across all scanned PDFs; lists PDFs with image-only pages (no extractable text, so they need OCR) and a Docling risk rating; shows per-page details for one PDF; exports the table as CSV. It doesn't scan anything itself. | `pdf_inventory.json` from `pdf_inventory_scan.py` |
| `crawl/profile_app.py` | Docling PDF profiler viewer. Cumulative structure statistics (pages, tables, pictures and so on) from Docling, a per-PDF breakdown with the full profiler record, and a preview of any source page. The counts are Docling's detections, not verified ground truth. | `crawl/profile_data/profiles.jsonl` from `crawl/profile_pdfs.py` |
| `lead_ai_rag_demo/streamlit_app.py` | Healthcare-policy RAG demo on synthetic data. Pick or type a question and run the LangGraph workflow (hybrid retrieval, query rewriting, answer verification, escalation), then see the answer, citations and the graph's execution trace. | Its own synthetic corpus |

**Chunking explorer:**

```bash
.venv/bin/python -m streamlit run streamlit_app.py
```

**PDF inventory dashboard.** Scan first if `pdf_inventory.json` is missing or
the PDFs changed (add `--resume pdf_inventory.checkpoint.json` to continue an
interrupted scan), then start the app:

```bash
.venv/bin/python pdf_inventory_scan.py --input-dir /Users/dc/united --output-json pdf_inventory.json
.venv/bin/python -m streamlit run pdf_inventory_dashboard.py
```

**Docling profiler viewer.** Profiling needs Docling, which is installed in
`/Users/dc/geha/.venv`; the viewer itself runs in this repo's `.venv`. See
[`crawl/PROFILE_README.md`](crawl/PROFILE_README.md) for details:

```bash
/Users/dc/geha/.venv/bin/python crawl/profile_pdfs.py --limit 10
.venv/bin/python -m streamlit run crawl/profile_app.py
```

**Healthcare RAG demo.** It has its own environment; see
[`lead_ai_rag_demo/README.md`](lead_ai_rag_demo/README.md). The Streamlit page
calls the LangGraph workflow in-process, so the FastAPI server in that README
is only needed for the API:

```bash
cd lead_ai_rag_demo
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m streamlit run streamlit_app.py
```

## Page-level retrieval evals

After analyzing a PDF, choose a page range (defaults to the whole PDF) and click
**Generate evals**. Set `OPENAI_API_KEY` in your shell first. The app sends one
rendered page image and its PyMuPDF text to OpenAI `gpt-4.1-mini` per page, asks
for three questions, short answers, and exact evidence quotes, then rejects
quotes not present in the extracted text. It appends valid records to
`evals/<PDF relative path>/<filename>_eval.jsonl`, so an interrupted run can be
resumed without regenerating completed pages. Do not use this on sensitive PDFs
unless sending their page content to OpenAI is approved. For example:

```bash
cd /Users/dc/united
export OPENAI_API_KEY='your-api-key'
.venv/bin/python -m streamlit run streamlit_app.py
```

Click **Load evals** to reuse the JSONL without an OpenAI call. Either button
then embeds the selected PDF's chunks and eval queries locally with
`BAAI/bge-small-en-v1.5`, ranks all chunks by cosine similarity, and writes
per-question scores to a policy-specific `*_results.jsonl` beside the evals.
The page viewer above the histograms shows the PDF image, each question and
evidence quote, top-three retrieved chunks (green check for a hit), and every
chunk overlapping that page. Recall@1/2/3, MRR@3, and nDCG@3 require an entire
verbatim evidence quote in a retrieved chunk. These measure retrieval, not
generated-answer correctness. If a quote is cut across chunks, the eval scores
zero and is flagged as a boundary miss. Pages with no extractable text need
OCR and are skipped. The first scoring run may download the BGE model.

Token-length histograms alone do not prove that chunk boundaries preserve
meaning. Loading existing evals does not require an OpenAI key or GPU.

To reproduce a 100-PDF, size-stratified length audit and save CSV, JSON, and
flagged-PDF plots:

```bash
cd /Users/dc/united
.venv/bin/python audit_chunk_lengths.py --count 100 --output chunk_length_report
```

The audit compares the 2,500-character baseline with 512-token recursive
chunks using the BGE tokenizer. It caps processing at 30 seconds per PDF by
default; a timeout is reported as a processing issue, not a chunking failure.
The length flags are screening signals and do not establish retrieval quality
or whether a sentence/table was split incorrectly.
# united
