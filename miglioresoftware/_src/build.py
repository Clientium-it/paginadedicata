#!/usr/bin/env python3
"""Migliore Software M2 pages (paginadedicata.com/miglioresoftware/<slug>/): one spec JSON -> <out>/<slug>/index.html + <out>/assets/.
Usage: python3 build.py specs/*.json --out <folder outside the repo>
Spec: slug, company, first (optional), fact, idea, evidence [{claim,url,quote}].
Every page's visible text is checked: no dashes/colons/!/; and none of the banned claims."""
import html, json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ASSETS = os.path.join(HERE, '..', 'assets')
TPL = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
BRAND = 'Migliore Software'
CAL = 'https://api.leadconnectorhq.com/widget/booking/qptu3dFMjAFbAdFhx98R'
BAD = re.compile(r'[—–:!;]| - ')
BANNED = re.compile(r'30\s*%|€|\beuro\b|prezz|costo|audit|settiman|\bgiorni\b|unique|clientium|sidac|magazzin|risorse umane|\bHR\b|su misura|gestional|garanti', re.I)
SHARED = ('ms-logo-white.webp', 'ms-logo-dark.webp', 'ms-matteo-hero.webp', 'ms-matteo-office.webp', 'ms-favicon.png', 'og.jpg')
E = lambda s: html.escape(s, quote=False); A = lambda s: html.escape(s, quote=True)
fin = lambda s: s if s.endswith(('.', '?')) else s + '.'
def visible(page):
    t = re.sub(r'(?s)<(script|style|head)[^>]*>.*?</\1>', ' ', page)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', t)))
def render(sp):
    c, first, slug = sp['company'].strip(), (sp.get('first') or '').strip(), sp['slug']
    fact, idea = (sp.get('fact') or '').strip(), (sp.get('idea') or '').strip()
    if not (fact and idea and sp.get('evidence')): raise ValueError(f'{slug}: needs fact, idea and evidence')
    prep = f'{first} di {c}' if first else c
    vals = {'BRAND': E(BRAND), 'CAL': CAL, 'COMPANY': E(c), 'COMPANY_ATTR': A(c), 'PREP': E(prep), 'PREP_ATTR': A(prep), 'FACT': E(fin(fact)), 'IDEA': E(fin(idea)),
            'LEAD_CSS': 'html:not(.phone) h1{font-size:42px}' if len(c) > 24 else '', 'CLARITY_ATTR': ''}
    page = re.sub(r'\{\{(\w+)\}\}', lambda m: vals[m.group(1)], TPL)
    txt = visible(page)
    if m := BAD.search(txt): raise ValueError(f'{slug}: copy rule broken near {txt[max(0,m.start()-40):m.end()+20]!r}')
    if m := BANNED.search(txt): raise ValueError(f'{slug}: banned claim {m.group(0)!r} near {txt[max(0,m.start()-40):m.end()+20]!r}')
    return page
def main():
    args = sys.argv[1:]; i = args.index('--out'); out = os.path.abspath(os.path.expanduser(args[i + 1])); specs = args[:i] + args[i + 2:]
    if os.path.realpath(out).startswith(os.path.realpath(os.path.expanduser('~/paginadedicata'))): sys.exit('out is inside the published repo: refused')
    os.makedirs(f'{out}/assets', exist_ok=True)
    for f in SHARED: shutil.copy(os.path.join(ASSETS, f), f'{out}/assets/{f}')
    done, bad = [], 0
    for p in specs:
        sp = json.load(open(p, encoding='utf-8'))
        try: page = render(sp)
        except ValueError as e: print('REFUSED', e); bad += 1; continue
        os.makedirs(f"{out}/{sp['slug']}", exist_ok=True)
        open(f"{out}/{sp['slug']}/index.html", 'w', encoding='utf-8').write(page); done.append(sp['slug'])
    json.dump({'built': done}, open(f'{out}/result.json', 'w'))
    print(len(done), 'pages in', out, '|', bad, 'refused'); sys.exit(1 if bad else 0)
if __name__ == '__main__': main()
