"""Read the unlabeled 'do not have and do not want' / "don't know" segments of page 24 (Figure 18) from the
PDF's vector drawing commands: segment rectangle width / full bar width, rounded. A segment with no rectangle
(width 0) becomes null. Printed a/b/c values are typed in from the native text. Writes p24-est.json (read by b6.py).
Replaces an earlier pixel-measurement version that was wrong in 10 of 19 rows."""
import json, collections, pymupdf
from pathlib import Path
S = Path(__file__).resolve().parent
PDF = '/Users/dc/geha/crawl_dir/raw/research/ey-limra-workforce-benefits-study-final-2025.pdf'
page = pymupdf.open(PDF)[23]
box = pymupdf.Rect(9.2, 13.9, 601.8, 653.5)
colours = {'#004F4F': 0, '#109090': 1, '#FF810A': 2, '#42C9C2': 3, '#93F0E6': 4}
rows = collections.defaultdict(dict)
for d in page.get_drawings():
    if not box.intersects(d['rect']) or not d.get('fill'):
        continue
    c = '#%02X%02X%02X' % tuple(round(v*255) for v in d['fill'])
    if c not in colours or d['rect'].y0 < 150:      # skip the legend swatches
        continue
    for it in d['items']:
        r = it[1] if it[0] == 're' else it[1].rect if it[0] == 'qu' else None
        if r is not None:
            rows[round(r.y0, 1)][colours[c]] = (r.x0, r.x1)
printed = [(48,7,35),(57,8,24),(63,9,23),(65,9,20),(66,9,21),(74,7,16),(76,8,13),(84,5,9),(86,7,4),(54,12,23),(68,6,20),(79,5,13),(89,5,4),(32,6,52),(42,7,41),(51,8,31),(58,8,28),(55,7,26),(78,6,12)]
assert len(rows) == len(printed), len(rows)
res = []
for y, pr in zip(sorted(rows), printed):
    segs = rows[y]; x0 = min(s[0] for s in segs.values()); W = max(s[1] for s in segs.values()) - x0
    pct = [(segs[k][1] - segs[k][0]) * 100 / W if k in segs else 0 for k in range(5)]
    d, e = (round(pct[3]) or None), (round(pct[4]) or None)
    res.append([*pr, d, e])
json.dump(res, open(S / 'p24-est.json', 'w'))
