# Recommended PDFs for the next processing benchmark

These candidates cover materially different extraction problems. Counts come from the existing inventory and were visually spot-checked where noted.

## 1. Dense text / policy baseline

- `/Users/dc/united/pdfs/www.uhc.com/content/dam/uhcdotcom/en/shop-marketplace/sample-medical-policy/Sample-Medical-Policy-MD-UHCIC-Choice-Plus-2026.pdf`
- 150 pages, no detected embedded images or tables, full text coverage.
- Tests headings, bullets, policy clauses, watermarks, chunking, citations, and retrieval without multimodal complexity.
- Visual spot-check: page 10.

## 2. Tables plus narrative text

- `/Users/dc/united/pdfs/www.uhc.com/content/dam/uhcdotcom/en/Pharmacy/PDFs/pharmacy-pdl-surest-3t-adv-jan-2027.pdf`
- 64 pages, 18 estimated tables, 3 detected images, full text coverage.
- Tests tier tables, medication lists, row integrity, repeated headers, and table-aware chunking.
- Visual spot-check: pages 1 and 5; page 5 contains a three-column drug-tier table.

## 3. Figures/charts without detected tables

- `/Users/dc/united/pdfs/healthactioncouncil.org/media/1hcai1ig/2024_white_paper.pdf`
- 8 pages, 312 detected image objects, no estimated tables, full text coverage.
- Tests charts, infographics, captions, reading order, and extraction of facts encoded visually.
- Visual spot-check: page 2 contains icons and a mortality bar chart.

## 4. OCR / image-dominant challenge

- `/Users/dc/united/pdfs/www.uhc.com/communityplan/assets/plandocuments/misc/Live%20Heart%20Smart-Session%201-Know%20Your%20Numbers.pdf`
- 15 pages, 509 detected images, 0% text coverage in the current audit.
- Tests OCR, text rendered as outlines/raster content, image understanding, and graceful fallback.
- Visual spot-check: page 1 visibly contains title text and photography despite zero extracted text.

## 5. Large repeated-table benchmark

- `/Users/dc/united/pdfs/assets.americashealthrankings.org/app/uploads/allstatesums-hwc2022.pdf`
- 104 pages and 104 estimated tables, full text coverage.
- Tests repeated page templates, table segmentation, state-level filtering, and retrieval across near-duplicate structures.

## 6. Multilingual form/table benchmark

- `/Users/dc/united/pdfs/www.uhc.com/communityplan/assets/plandocuments/benefits/PA_Chip_Application_ES.pdf`
- 20 pages, 7 estimated tables, 11 images, full text coverage.
- Tests Spanish content, forms, checkboxes, labels, and mixed table/form layout.

## 7. Long handbook with mixed structure

- `/Users/dc/united/pdfs/www.uhc.com/communityplan/assets/plandocuments/handbook/en/NE_Heritage_Health_Member_Handbook_EN.pdf`
- 132 pages, 7 estimated tables, 4 images, full text coverage.
- Tests long-document hierarchy, benefit rules, cross-references, tables, and retrieval over a member handbook.

## Suggested benchmark order

1. Dense policy baseline.
2. Drug list with tables.
3. Figure/chart white paper.
4. OCR/image-dominant guide.
5. Multilingual form.
6. Long handbook.
7. Repeated-table stress test.
