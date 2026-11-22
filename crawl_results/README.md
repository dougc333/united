# United crawl results

Generated from the existing crawl and PDF inventory. No PDFs were modified.

## Files in this directory

- `summary.json`: aggregate crawl and local-corpus statistics.
- `pdf_classification.csv`: one row per currently existing PDF, classified by text/table/image characteristics.
- `candidate_shortlist.md`: recommended documents for the next extraction and RAG benchmark.

## Original crawl artifacts

- Crawl download manifest: `/Users/dc/united/manifest.json` and `/Users/dc/united/manifest.csv`
- Page audit and structural inventory: `/Users/dc/united/pdf_inventory.json`
- Page-count audit: `/Users/dc/united/crawl/pdf_pages.txt`
- Page-count errors: `/Users/dc/united/crawl/pdf_pages_errors.txt`
- Docling profile records: `/Users/dc/united/crawl/profile_data/profiles.jsonl`
- Docling profile summary: `/Users/dc/united/crawl/profile_data/summary.json`

## Important status

- The crawl manifest reports 9169 crawled web pages, 7118 PDF URL records, and 916 crawl errors.
- The current local `/Users/dc/united/pdfs` corpus contains 4429 PDF files represented by the structural inventory.
- The Docling profiler has completed only one PDF, so the broad corpus classification is based on the earlier structural inventory rather than full Docling conversion.
- Image and table counts are candidate-selection heuristics and require visual or model-based verification before being treated as labels.
