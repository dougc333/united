import json, sys
sys.path.insert(0, '/Users/dc/geha')
from crawl_dir.src.pipeline.figure_specs import verify_figure, native_box_evidence, render_figure
import pymupdf, subprocess
S = sys.argv[1]
pdf = pymupdf.open('/Users/dc/geha/crawl_dir/raw/research/ey-limra-workforce-benefits-study-final-2025.pdf')
page = pdf[3]; box = [1.57, 367.82, 348.94, 721.65]
one = pymupdf.open(); one.insert_pdf(pdf, from_page=3, to_page=3); one.save(f'{S}/page-004.pdf')
cats = [("Small (10–99 employees)", [3, 40, 57], "+7% change from 2023"),
        ("Midsize (100–999 employees)", [1, 35, 64], "+6% change from 2023"),
        ("Large (1,000 or more employees)", [3, 30, 67], "+5% change from 2023")]
fig = {"id": "page-004-region-bcb07a18", "label": "Figure 1",
       "title": "Companies plan to offer more benefits in five years.",
       "question": "In five years, do you think your company will be offering fewer, the same or more benefits than it does now?",
       "box_pt": box,
       "chart": {"type": "vbar", "mode": "stacked_100", "category_heading": "Company size",
                 "series": [{"name": "Fewer benefits", "color": "#C4C4CD"},
                            {"name": "About the same", "color": "#747480"},
                            {"name": "More benefits", "color": "#FFE600"}],
                 "categories": [{"label": l, "values": v} for l, v, _ in cats],
                 "annotations": [{"type": "callout", "category": l, "text": t, "meaning": "More benefits"} for l, _, t in cats]}}
spec = {"schema_version": 1, "document_id": "ey-limra-workforce-benefits-study-final-2025", "page": 4,
        "author": "claude-test-from-crop", "figures": [fig]}
json.dump(spec, open(f'{S}/page-004.test.json', 'w'), indent=2, ensure_ascii=False)
ev = native_box_evidence(__import__('pathlib').Path(f'{S}/page-004.pdf'), box)
errs, warns = verify_figure(fig, ev)
print('errors', errs); print('warnings', warns)
open(f'{S}/fig1.html', 'w').write(render_figure(fig))
