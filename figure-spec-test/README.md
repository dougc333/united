# Figure-spec generation test (EY/LIMRA workforce benefits study, pages 4-26)

Can a figure spec (`page-NNN.json`) be generated from a reviewed bounding box alone, and does it match the
specs already committed in the geha repo? Specs here were written by Claude from the inputs below, **without
opening the committed specs first** (page 4 was done earlier, after the committed spec had been seen).

Nothing in the geha repo was changed. This folder is a standalone copy.

## Inputs

| Input | Path | Used for |
|---|---|---|
| Source PDF | `/Users/dc/geha/crawl_dir/raw/research/ey-limra-workforce-benefits-study-final-2025.pdf` | page text and crops |
| Reviewed boxes | `/Users/dc/geha/bounding_box/annotations/research/ey-limra-workforce-benefits-study-final-2025/figure-bounding-boxes.json` | where each figure is (0-1000 grid, converted to PDF points) |
| Crop of each box | `crops/pNN-K.png` (110 dpi, made by `scripts/make_crops.py`) | Claude reads bars, colours, callouts, layout |
| Native PDF text inside each box | `scripts/ntext.py pNN-K` (PyMuPDF) | exact labels and percentages |
| Spec schema and renderers | `crawl_dir/src/pipeline/figure_specs.py` (`render_figure`, `verify_figure`) | which fields and chart types exist |
| Pixel colours | sampled from the crop (all `#FFE600`, `#747480`, `#C4C4CD`, ... values) | series colours |

Not used: the committed `figure-specs/*.json`, the reconstruction prompts, and any crawl-run output.

## How the specs were generated

1. `scripts/make_crops.py` renders each box as a PNG.
2. For each figure Claude looked at the crop, printed the native text (`scripts/ntext.py`) and typed the
   chart data into a small Python script (`scripts/b1.py` ... `b6.py`, shared helpers in `scripts/lib.py`).
   The numbers and labels in those scripts are hand-transcribed by Claude, not extracted by code.
3. `lib.save()` writes `specs/page-NNN.json` and runs `verify_figure` (the pipeline's own checker) against the
   native PDF words inside the figure's box. Every spec here passes with 0 errors.
4. Page 24 (Figure 18) has 38 unlabeled bar segments. `scripts/measure_p24.py` reads them from the PDF's vector
   drawing commands (segment rectangle width / full bar width, rounded; absent segments become null) and writes
   `scripts/p24-est.json`, which `b6.py` reads. An earlier version measured pixels in the crop and was wrong in
   10 of 19 rows, so it was replaced. Page 4 is vector too; see "Vector vs raster" below.
5. Page 4 comes from the separate `scripts/gen_page004.py` (crop `crops/p04-1.png`).

Re-run everything (regenerates `specs/` and `crops/`; output was byte-identical when re-run after the move):

```bash
cd /Users/dc/united/figure-spec-test/scripts
python3 make_crops.py && python3 measure_p24.py
for b in b1 b2 b3 b4 b5 b6; do python3 $b.py; done
python3 compare.py        # rewrites ../diff-report.txt
```

Requires `pymupdf` and `Pillow`, and runs from a checkout where `/Users/dc/geha` exists.

## Deviations from the bbox file

- Pages 14 (Figure 9), 18 and 19: box extended downward because the drawn box cut off labels and the PDF text
  check needs the words inside the box.
- Pages 21 and 25: one drawn box covers two figures, so each is split into two figures with their own `box_pt`
  (page 21 uses a shared group for the "Figures 13 and 14" header).
- Page 11 (wheel) and page 18 (category labels): labels are raster in the PDF, so these figures use
  `value_evidence: raster_visual_read`.
- Pages 10 and 26: text-layer glitches (`Millennial` + `s`, `Al-enabled`) recorded as
  `acknowledged_text_differences`.

## Comparison with the committed specs

Full diff: `diff-report.txt` (compared by content, not bytes).

- All printed chart values agree (about 386 compared). The apparent mismatches in the raw script output are my
  matching of figures (pages 5, 21) or the order of pie slices (page 23).
- Differences: colour hex codes off by a few units (pages 5, 8, 9, 19); `kind` and `category_heading` wording;
  my extra `heading`/`description` fields (pages 7, 16, 20); step numbers `01` vs `1` and `AI-enabled` vs
  `Al-enabled` (page 26); one label typo of mine on page 10 ("Telemedicine benefit").
- Page 24: printed segments and the vector-derived small segments all match the committed spec; only the three
  series colour codes differ by one unit.
- Coverage the current boxes cannot reproduce: page 13's "Figure 7" title sits above the current box, and the
  committed page 25 has a third figure (broker quotes, y 25-140) that the current bbox file has no region for.
  `figure-bounding-boxes.json` was last updated Oct 22, after the committed specs (Oct 10).
- Page 22: only `category_heading` wording differs, once figures are paired by position (the bbox file lists
  Figure 16 before Figure 15).
- Page 3 is not here: it comes from `generate_figure_specs.py` (numbered findings table), not from Claude.

## Vector vs raster

Some charts are vector drawings in the PDF (PyMuPDF `get_drawings()`), not images. On page 4 each series is one
filled path with 3 rectangles; rectangle height / total bar height reproduces 3/40/57, 1/35/64 and 3/30/67
exactly. Page 24 works the same way. Page 18's chart is raster (its text is not in the text layer), so it needs a
visual read. Check `get_images()` against the figure box to tell them apart. Generating values from the vector
geometry would be exact where available; this test did not use it except on page 24.
