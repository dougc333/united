"""Compare specs/ with the committed figure-specs and write ../diff-report.txt (content differences by figure)."""
import json, glob, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
E = '/Users/dc/geha/bounding_box/annotations/research/ey-limra-workforce-benefits-study-final-2025/figure-specs/'
def num(v): return (v['value'], bool(v.get('printed', True))) if isinstance(v, dict) else (v, True)
def cmp(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict) and not ({'value'} >= set(a) - {'printed'} and 'value' in a):
        for k in sorted(set(a) | set(b)):
            if k not in a: out.append(f'{path}.{k}: only in existing = {str(b[k])[:90]}')
            elif k not in b: out.append(f'{path}.{k}: only in mine = {str(a[k])[:90]}')
            else: cmp(a[k], b[k], f'{path}.{k}', out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b): out.append(f'{path}: length mine {len(a)} vs existing {len(b)}')
        for i, (x, y) in enumerate(zip(a, b)): cmp(x, y, f'{path}[{i}]', out)
    else:
        scalar = lambda z: isinstance(z, (int, float, dict)) and z is not None
        if (num(a) != num(b)) if (scalar(a) and scalar(b)) else a != b:
            out.append(f'{path}: mine={str(a)[:80]!r} existing={str(b)[:80]!r}')
def key(f): return (f.get('label') or '', f['title'])
lines = []
for f in sorted(glob.glob(str(ROOT / 'specs' / 'page-*.json'))):
    pg = os.path.basename(f); mine = json.load(open(f)); ex = json.load(open(E + pg))
    mf, ef = mine['figures'], ex['figures']
    if pg == 'page-022.json': mf = sorted(mf, key=lambda x: x['box_pt'][1]); ef = sorted(ef, key=lambda x: x['box_pt'][1])
    if pg == 'page-021.json': pass
    out = []
    cmp(mf, ef, 'figures', out)
    if 'groups' in ex or 'groups' in mine: cmp(mine.get('groups', {}), ex.get('groups', {}), 'groups', out)
    core = [o for o in out if not (o.split(':')[0].endswith('.id') or '.box_pt' in o.split(':')[0])]
    lines.append(f'--- {pg}: {len(core)} content differences ({len(out)-len(core)} id/box-only)')
    lines += ['    ' + o for o in core[:14]]
    if len(core) > 14: lines.append(f'    ... {len(core)-14} more')
(ROOT / 'diff-report.txt').write_text('\n'.join(lines) + '\n')
print('\n'.join(l for l in lines if l.startswith('---')))
