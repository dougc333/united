# Most complex PDFs in the United corpus

This ranking uses the existing structural inventory for the 4,429 currently present PDFs. Complexity is multi-dimensional: document scale, repeated tables, multilingual content, OCR/text-layer failure, figure density, and parser risk. Image and table counts are heuristics, not ground-truth labels.

## Hardest overall

| Rank | PDF | Why it is difficult | Inventory signals |
|---:|---|---|---|
| 1 | `IN-PathWays-Provider-Directory-Central.pdf` | Extreme length plus almost one detected table per page; repeated provider records make segmentation, deduplication, retrieval, and row preservation difficult. | 4,592 pages; 4,382 tables; English/Spanish |
| 2 | `NE-Medicaid-Heritage-Health-Provider-Directory.pdf` | Massive table-heavy directory with multiple language sections and near-duplicate provider entries. | 3,700 pages; 3,099 tables; 8 images; Chinese/English/Korean/Spanish |
| 3 | `TX-STAR-Kids-Provider-Directory-Houston.pdf` | Very long, table-heavy, multilingual, and already marked high-risk because some pages have little or no detected language/text. | 2,392 pages; 803 tables; high risk |
| 4 | `OH-Provider-Directory-West-EN.pdf` | Very long mixed-language directory with heterogeneous page structure and some uncertain pages. | 4,195 pages; 114 tables; high risk |
| 5 | `TX-CHIP-Provider-Directory-Houston.pdf` | Longest file in the corpus. Extraction may be straightforward, but indexing, chunking, deduplication, and high-recall retrieval across 4,972 pages are demanding. | 4,972 pages; English/Korean/Spanish |
| 6 | `EICA00NI0271896.pdf` | Multi-thousand-page legal/notices document with multilingual sections and incomplete text coverage. | 3,114 pages; 99.9% text coverage; high risk |
| 7 | `Guia-sencilla-sobre-medicare.pdf` | Long image/outline-based Spanish guide with no extractable text in the current audit; requires OCR or vision. | 64 pages; 0% text coverage; high risk |
| 8 | `Live Heart Smart - Session 1` | Image-dominant designed document with visible text but no extracted text, photographs, colored shapes, and complex reading order. | 15 pages; 509 image objects; 0% text coverage |
| 9 | `pharmacy-pdl-surest-4t-trad-jan-2027.pdf` | Combines narrative policy, tier tables, medication lists, and heavily fragmented graphical objects. | 60 pages; 16 tables; 2,008 image objects; four detected languages |
| 10 | `allstatesums-hwc2022.pdf` | Repeated structured tables across every page; useful for testing table continuity and retrieval among near-identical state templates. | 104 pages; 104 tables |
| 11 | `2024_white_paper.pdf` | Short but visually dense; charts, icons, captions, and facts encoded graphically make it a strong figure-understanding test. | 8 pages; 312 image objects; no detected tables |
| 12 | `PA_Chip_Application_ES.pdf` | Form-like multilingual layout containing checkboxes, labels, tables, and images. | 20 pages; 7 tables; 11 images |

## Best benchmark set

Processing only the largest files first would mostly test provider-directory scale. A more diagnostic benchmark should include:

1. `IN-PathWays-Provider-Directory-Central.pdf` - extreme tables and scale.
2. `TX-STAR-Kids-Provider-Directory-Houston.pdf` - high-risk multilingual directory.
3. `Guia-sencilla-sobre-medicare.pdf` - long OCR/vision challenge.
4. `Live%20Heart%20Smart-Session%201-Know%20Your%20Numbers.pdf` - designed image-dominant document.
5. `pharmacy-pdl-surest-4t-trad-jan-2027.pdf` - tables plus graphical fragmentation.
6. `2024_white_paper.pdf` - figure/chart understanding.
7. `PA_Chip_Application_ES.pdf` - multilingual form processing.
8. `allstatesums-hwc2022.pdf` - repeated-table extraction.

## Existing extraction failures

Twelve PDFs are marked `error` in the structural inventory. Treat these as a separate parser-robustness set rather than ranking them as semantically complex. They include two Dietary Guidelines copies, the KFF 2025 Employer Health Benefits Survey, several provider directories, brochures, and a bilingual bookmark.

## Interpretation warning

- An embedded-image count can represent photographs and charts, but it can also count masks, vector fragments, or page-decoration pieces.
- A table estimate may identify aligned provider listings as tables even when the PDF does not contain a native table object.
- Only one PDF has completed the newer Docling profiler. This ranking should therefore be used to select the next Docling batch, not as final extraction ground truth.
