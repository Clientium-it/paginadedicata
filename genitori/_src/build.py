#!/usr/bin/env python3
"""Genitori.it pages: one spec JSON -> <out>/<slug>/index.html + <out>/assets/.
Usage: python3 build.py specs/*.json --out <folder outside the repo>
Refuses to write inside ~/paginadedicata: this script prepares pages, it never publishes them.
Spec fields: slug, company, full_name, cover_note + idea + evidence [{claim,url,quote}].
With no cover_note the page is the generic version: names only, no claim about the lead."""
import html, json, os, re, shutil, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ASSETS = os.path.join(HERE, '..', 'assets')
TPL = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
BAD = re.compile(r'[—–:!]| - ')
SHARED = ('genitori-logo.svg', 'genitori-o.svg', 'alfredo-spalletta.jpg')
OG_SHARED = 'og.jpg'   # one preview image for every page of this client (site space)
CAL_ID = ''
PHOTO = 'alfredo-spalletta.jpg'   # Alfredo Spalletta photo in assets when we have one: until then his initials   # shared booking calendar (GHL widget id): set it and rebuild, the last slide then shows it next to the text
TAIL = 'Qui trova come Genitori.it può entrare nel vostro piano formativo.'
GEN_SUB = 'In queste pagine trova come Genitori.it, il progetto formativo del Moige, può entrare nel piano formativo di {c}.'
H1 = 'La genitorialità nel piano formativo di {c}'
GEN_IDEA = 'Ci racconti come è fatto il vostro piano formativo, e vediamo insieme dove può entrare un percorso sulla genitorialità.'
E = lambda s: html.escape(s, quote=False)
A = lambda s: html.escape(s, quote=True)
def slugify(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
def clarity_attr(sp):
    words = {w.lower() for w in re.split(r'\W+', sp.get('first') or (sp.get('full_name') or '').split(' ')[0]) if len(w) >= 3}
    return ' data-no-slug' if words & set(sp['slug'].split('-')) else ''
def render(sp):
    c, full, slug = sp['company'].strip(), (sp.get('full_name') or '').strip(), sp['slug']
    note, idea = (sp.get('cover_note') or '').strip(), (sp.get('idea') or '').strip()
    if (note or idea) and not sp.get('evidence'): raise ValueError(f'{slug}: claim about the lead with no evidence')
    if full and slugify(full) == slug: raise ValueError(f'{slug}: the slug is the person name')
    for t in (c, full, note, idea):
        if BAD.search(t): raise ValueError(f'{slug}: copy rule broken in {t!r}')
    vals = {'COMPANY': E(c), 'COMPANY_ATTR': A(c), 'PREP': E(f'{full} di {c}' if full else c), 'PREP_ATTR': A(f'{full} di {c}' if full else c),
            'OG_PATH': OG_SHARED, 'LEAD_CSS': '', 'LEAD_MARK': f'<span class="nm">{E(c)}</span>',
            'H1': E(H1.format(c=c)),
            'SUB': E(f'{note} {TAIL}' if note else GEN_SUB.format(c=c)), 'IDEA': E(idea or GEN_IDEA), 'CLARITY_ATTR': clarity_attr(sp),
            'CAL_URL': f'https://api.leadconnectorhq.com/widget/booking/{CAL_ID}' if CAL_ID else '', 'BTN_DISPLAY': 'block' if CAL_ID else 'none',
            'TALK_RIGHT': '<iframe id="calf" title="Calendario Genitori.it"></iframe>' if CAL_ID else '', 'TALK_CLASS': '' if CAL_ID else ' nocal',
            'PIC': f'<img class="pic" src="../assets/{PHOTO}" alt="Alfredo Spalletta">' if PHOTO else '<div class="pic ini" aria-hidden="true">AS</div>'}
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
