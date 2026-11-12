#!/usr/bin/env python3
"""Dotzero pages: one spec JSON -> <out>/<slug>/index.html + <out>/assets/.
Usage: python3 build.py specs/*.json --out <folder outside the repo>
Refuses to write inside ~/paginadedicata: this script prepares pages, it never publishes them.
Spec fields: slug, company, full_name, cover_note + idea + evidence [{claim,url,quote}].
With no cover_note the page is the generic version: names only, no claim about the lead."""
import html, json, os, re, shutil, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ASSETS = os.path.join(HERE, '..', 'assets')
TPL = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
BAD = re.compile(r'[—–:!]| - ')
SHARED = ('logo-dotzero-white.svg', 'studio.webp', 'Hansom-Regular.ttf', 'Hansom-Bold.ttf', 'Hansom-Italic.ttf', 'Hansom-Bold-Italic.ttf')
TAIL = 'Qui trova cosa possiamo realizzare per la vostra comunicazione e come lavoriamo.'
GEN_SUB = 'In queste pagine trova cosa possiamo realizzare per la comunicazione di {c} e come lavoriamo.'
GEN_IDEA = 'Ci dica quale progetto avete in programma, e guardiamo insieme cosa potremmo realizzare.'
fin = lambda s: s if s.endswith(('.', '?')) else s + '.'   # cover = fact + idea (why it matters), never the bare fact
E = lambda s: html.escape(s, quote=False)
A = lambda s: html.escape(s, quote=True)
def slugify(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
def render(sp):
    c, full, slug = sp['company'].strip(), (sp.get('full_name') or '').strip(), sp['slug']
    note, idea = (sp.get('cover_note') or '').strip(), (sp.get('idea') or '').strip()
    if (note or idea) and not sp.get('evidence'): raise ValueError(f'{slug}: claim about the lead with no evidence')
    if full and slugify(full) == slug: raise ValueError(f'{slug}: the slug is the person name')
    for t in (c, full, note, idea):
        if BAD.search(t): raise ValueError(f'{slug}: copy rule broken in {t!r}')
    vals = {'COMPANY': E(c), 'COMPANY_ATTR': A(c), 'PREP': E(f'{full} di {c}' if full else c), 'PREP_ATTR': A(f'{full} di {c}' if full else c),
            'OG_PATH': f'og/{slug}.jpg', 'LEAD_CSS': '', 'LEAD_MARK': f'<span class="nm">{E(c)}</span>',
            'H1': E(f'I video di {c}, dalle riprese al montato finale'),
            'SUB': E(f'{note} {fin(idea)}' if note else GEN_SUB.format(c=c)), 'IDEA': E(GEN_IDEA)}
    return re.sub(r'\{\{(\w+)\}\}', lambda m: vals[m.group(1)], TPL)
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
    print(len(done), 'pages in', out, '|', bad, 'refused'); sys.exit(1 if bad else 0)
if __name__ == '__main__': main()
