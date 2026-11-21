import json, sys, pymupdf
from pathlib import Path
import tempfile
S = Path(__file__).resolve().parent          # scripts/ (holds p24-est.json)
ROOT = S.parent
SPECS = ROOT / 'specs'
TMP = Path(tempfile.mkdtemp(prefix='figspec-src-'))   # single-page PDFs used for verification
sys.path.insert(0, '/Users/dc/geha')
from crawl_dir.src.pipeline.figure_specs import verify_figure, native_box_evidence
PDF = '/Users/dc/geha/crawl_dir/raw/research/ey-limra-workforce-benefits-study-final-2025.pdf'
BB = json.load(open('/Users/dc/geha/bounding_box/annotations/research/ey-limra-workforce-benefits-study-final-2025/figure-bounding-boxes.json'))['pages']
DOC = 'ey-limra-workforce-benefits-study-final-2025'
def box(pg, i):
    p = pymupdf.open(PDF)[pg-1].rect; b = BB[str(pg)][i-1]
    return [round(b['x1']*p.width/1000, 2), round(b['y1']*p.height/1000, 2), round(b['x2']*p.width/1000, 2), round(b['y2']*p.height/1000, 2)]
def fig(pg, i, label, title, chart, question="", **extra):
    f = {"id": BB[str(pg)][i-1]['id'], "label": label, "title": title, "question": question, "box_pt": box(pg, i), "chart": chart}
    f.update(extra); return f
def save(pg, figures, groups=None):
    spec = {"schema_version": 1, "document_id": DOC, "page": pg, "author": "claude-blind-test", "figures": figures}
    if groups: spec["groups"] = groups
    (SPECS/f'page-{pg:03d}.json').write_text(json.dumps(spec, indent=2, ensure_ascii=False))
    one = pymupdf.open(); one.insert_pdf(pymupdf.open(PDF), from_page=pg-1, to_page=pg-1); one.save(TMP/f'src-{pg:03d}.pdf')
    for f in figures:
        ev = native_box_evidence(TMP/f'src-{pg:03d}.pdf', f['box_pt'])
        e, w = verify_figure(f, ev)
        print(f'p{pg} {f["label"]}: errors={len(e)} warnings={len(w)}')
        for x in e: print('   ', x['category'], x['html_evidence'][:60] if 'html_evidence' in x else '', '|', x['correction'][:200])
        for x in w: print('    warn', x[:150])
