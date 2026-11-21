import pymupdf,json,sys
pdf=pymupdf.open('/Users/dc/geha/crawl_dir/raw/research/ey-limra-workforce-benefits-study-final-2025.pdf')
d=json.load(open('/Users/dc/geha/bounding_box/annotations/research/ey-limra-workforce-benefits-study-final-2025/figure-bounding-boxes.json'))['pages']
for a in sys.argv[1:]:
    pg,i=a[1:3],int(a[4])
    pg=int(pg);b=d[str(pg)][i-1];p=pdf[pg-1];r=p.rect
    clip=pymupdf.Rect(b['x1']*r.width/1000,b['y1']*r.height/1000,b['x2']*r.width/1000,b['y2']*r.height/1000)
    t=' | '.join(l.strip() for l in p.get_text('text',clip=clip).splitlines() if l.strip())
    print('==',a,t,'\n')
