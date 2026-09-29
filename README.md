# UHG

There are 4400 pdf files. Too large for a git commit. Only src

#Preprossing PDFs. 
Goal: ocr the non text containing PDFs. Create RAG app based on pdfs and a conversation agent using the member handbook. 


##step 1: build a exploratory UI which crawls the files and reads which ones need OCR. 
Use threads, precrawl and boot up with past crawl info. This data isn't going to change. No use in recrawling. 
```
cd /Users/dc/united
.venv/bin/python -m streamlit run streamlit_app.py
```

##Step 2: 
divide the pdfs into single pages and use LLM to convert to html. Tell the LLM to take a screenshot using playwright and Chromium and compare the 2 for errors. This is a single call iterative loop. 

## Streamlit apps in this repo

There are four Streamlit apps. Run each from `/Users/dc/united`; Streamlit
serves on http://localhost:8501 (the next free port if one is already running).
Three are viewers for results produced by a separate script, so run that script
first if its output file is missing.

| App | What it does | Reads |
|---|---|---|
| `streamlit_app.py` | PDF chunking explorer (step 1 above). Compares token lengths of the 2,500-character baseline with a selectable recursive chunking policy for one PDF, and generates or loads page-level retrieval evals. | PDFs under `pdfs/` |
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
