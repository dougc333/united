# AWS page-by-page PDF OCR and HTML visual-review pipeline

This is a **bounded CLI proof of concept** for an existing PDF in S3. It does
not deploy infrastructure or run automatically on uploads. For each page it:

1. Saves `source_page_X.pdf` and a raster `source.png` to S3.
2. Calls Textract `AnalyzeDocument` for lines, tables, forms and layout.
3. Calls a vision-capable Bedrock Converse model to draft standalone HTML.
4. Screenshots the HTML with Playwright Chromium, saves an image comparison,
   and asks the vision model to identify visible discrepancies.
5. Checks that the HTML retained OCR words, revises up to `--max-revisions`,
   and records every attempt in S3. An unresolved page is marked `review`.

`auto_pass` is **not a proof of pixel-identical or medically correct content**:
the OCR and visual model can both miss errors. A qualified human must review
the side-by-side images and source PDFs before using extracted policy content.

## Install and run

Python 3.11+ and AWS credentials/region configured by the standard AWS SDK
credential chain are required. Use a Bedrock Converse model in your Region
that supports **image input**. Install Playwright's Chromium once:

```bash
cd /Users/dc/united/aws
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
export BEDROCK_MODEL_ID='your-enabled-vision-model-or-inference-profile-id'
.venv/bin/python pipeline.py s3://YOUR_BUCKET/input/document.pdf \
  --output-bucket YOUR_BUCKET --output-prefix reviewed/document --max-pages 2
```

Remove `--max-pages 2` for the whole PDF. Re-running to the same prefix
overwrites prior objects: use a distinct prefix per run for auditability.
The CLI exits `0` if every page auto-passes and `2` if any page needs review
or errors. Check `s3://YOUR_BUCKET/reviewed/document/manifest.json` and each
`page_XXXX/report.json` or `error.json`. No claim is adjudicated here.

## Security and operations

- Grant only `s3:GetObject` for the input key, `s3:PutObject` for the output
  prefix, `textract:AnalyzeDocument`, and `bedrock:InvokeModel` for the chosen
  model/profile. Keep input and output buckets private and encrypted, with
  appropriate retention and access logging. This code does not create IAM,
  buckets, KMS keys, or VPC endpoints.
- Do **not** send PHI or restricted claims documents to a service/model without
  your organization's approved data handling, contracts, region, and controls.
- PDF content and OCR text are treated as untrusted data; generated HTML is
  rendered with JavaScript disabled and external network requests blocked.
- Textract synchronous PNG requests are subject to AWS size/page limits. For
  high-resolution or oversized pages, lower `page_assets(scale=...)` or move
  to an asynchronous Textract workflow. Do not assume any Bedrock vision model
  accepts an arbitrarily large image or prompt.
- AWS calls have cost and service quotas. Start with `--max-pages 2`, review
  outputs, then scale with Step Functions Map/ECS workers, retries, and a
  separate human approval gate. The CLI is intentionally serial and does not
  automatically trigger on S3 events.

## Local tests

```bash
.venv/bin/python -m unittest -v test_pipeline.py
```

The tests do not invoke AWS or require model access. An end-to-end test needs
AWS credentials, an S3 input PDF, Textract access, a vision-capable Bedrock
model, and installed Playwright Chromium.
