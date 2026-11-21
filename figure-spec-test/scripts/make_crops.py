"""Render each reviewed bounding box (pages 5-26) from the PDF as a PNG crop (110 dpi)."""
import json, pymupdf
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
PDF = '/Users/dc/geha/crawl_dir/raw/research/ey-limra-workforce-benefits-study-final-2025.pdf'
BB = '/Users/dc/geha/bounding_box/annotations/research/ey-limra-workforce-benefits-study-final-2025/figure-bounding-boxes.json'
pdf = pymupdf.open(PDF)
(ROOT / 'crops').mkdir(exist_ok=True)
for pg, boxes in json.load(open(BB))['pages'].items():
    pg = int(pg)
    if pg < 5:
        continue
    page = pdf[pg - 1]; r = page.rect
    for i, b in enumerate(boxes, 1):
        clip = pymupdf.Rect(b['x1']*r.width/1000, b['y1']*r.height/1000, b['x2']*r.width/1000, b['y2']*r.height/1000)
        page.get_pixmap(clip=clip, dpi=110).save(ROOT / 'crops' / f'p{pg:02d}-{i}.png')
