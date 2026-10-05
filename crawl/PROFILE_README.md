# Docling PDF profiler

The profiler recursively finds PDFs beneath `/Users/dc/united` (excluding
virtual environments, Git, caches, and the crawl output), converts each PDF to
a DoclingDocument, and records structural counts. It writes an append-only
`profile_data/profiles.jsonl` file and a cumulative `profile_data/summary.json`.
Reruns skip successful unchanged files; `--force` reprocesses them. Failures
are recorded and can be retried by rerunning the command.

Docling is currently installed in `/Users/dc/geha/.venv`, not
`/Users/dc/united/.venv`. To test one PDF:

```bash
/Users/dc/geha/.venv/bin/python /Users/dc/united/crawl/profile_pdfs.py \
  --pdf /Users/dc/united/pdfs/downloads.aap.org/AAP/PDF/CoE_one_pager_with_disclaimer.pdf
```

To process ten more PDFs, or resume the full collection:

```bash
/Users/dc/geha/.venv/bin/python /Users/dc/united/crawl/profile_pdfs.py --limit 10
/Users/dc/geha/.venv/bin/python /Users/dc/united/crawl/profile_pdfs.py
```

Start the viewer using the United environment (it does not need Docling):

```bash
/Users/dc/united/.venv/bin/python -m streamlit run /Users/dc/united/crawl/profile_app.py
```

The counts reflect Docling's detected content, not independently verified PDF
ground truth. In particular, `num_pictures_for_ocr` counts detected pictures
whose bounding boxes cover at least 5% of a page; it is not an OCR necessity
or correctness test. Inspect the source PDF preview when a count looks wrong.
