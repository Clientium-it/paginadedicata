#!/usr/bin/env python3
"""Cappa Engineering / INGEGNOS pages: one spec JSON -> <out>/<slug>/index.html + <out>/assets/.
Usage: python3 build.py specs/*.json --out <folder outside the repo>
Refuses to write inside ~/paginadedicata. Generic pages only for now (names, no claim about the lead)."""
import html, json, os, re, shutil, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ASSETS = os.path.join(HERE, '..', 'assets')
TPL = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
BAD = re.compile(r'[—–:!]| - ')
# COVER: slot for the frame from Francesco's videos (swap the file name when it arrives; the old asset stays)
COVER = 'cappa-automazione.jpg'   # from ingegnos.it (dettaglio-automazione.jpg, 3984px, resized to 2400)
CLOSE_IMG = 'cappa-stazione-sollevamento.jpg'   # ingegnos.it sollevatorestampo.jpg, real photo of a station built in their workshop
CASE_IMG = 'cappa-isola-imballi.jpg'   # ingegnos.it isolaimballi.png (cappaengineering.it: isola di produzione imballi)
SHARED = ('ingegnos-cappa-logo.jpg', COVER, CLOSE_IMG, CASE_IMG)
TAIL = 'Qui trova come lavoriamo con i costruttori di macchine, dal progetto alla costruzione.'
GEN_SUB = 'In queste pagine trova come INGEGNOS può affiancare {c} come ufficio tecnico esterno, dal progetto e dal fascicolo tecnico fino alla costruzione.'
GEN_IDEA = 'Progetto, fascicolo tecnico e costruzione con un unico interlocutore, così il vostro ufficio tecnico resta sulle commesse.'
E = lambda s: html.escape(s, quote=False)
A = lambda s: html.escape(s, quote=True)
def slugify(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
def clarity_attr(sp):
    # no person's name in the Clarity tags: skip the slug tag when the slug holds the lead's first name
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
            'OG_PATH': f'og/{slug}.jpg', 'LEAD_CSS': '', 'LEAD_MARK': f'<span class="nm">{E(c)}</span>',
            'H1': E(f'Dal progetto alla macchina collaudata, per {c}'),
            'SUB': E(f'{note} {TAIL}' if note else GEN_SUB.format(c=c)), 'IDEA': E(idea or GEN_IDEA), 'CLARITY_ATTR': clarity_attr(sp), 'COVER': COVER, 'CLOSE_IMG': CLOSE_IMG, 'CASE_IMG': CASE_IMG}
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
