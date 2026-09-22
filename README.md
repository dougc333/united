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
