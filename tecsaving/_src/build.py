#!/usr/bin/env python3
"""Tecsaving pages: one spec JSON -> <out>/<slug>/index.html + <out>/assets/.
Usage: python3 build.py specs/*.json --out <folder outside the repo>
Refuses to write inside ~/paginadedicata: this script prepares pages, it never publishes them.
Spec fields: slug, company, full_name, cover_note + idea + evidence [{claim,url,quote}].
With no cover_note the page is the generic version: names only, no claim about the lead."""
import html, json, os, re, shutil, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ASSETS = os.path.join(HERE, '..', 'assets')
TPL = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
BAD = re.compile(r'[—–:!]| - ')
# COVER: slot for the frame from Francesco's videos (swap the file name when it arrives; the old asset stays)
COVER = 'tecsaving-cover-unita-parete.jpg'   # frame A from Francesco's video v1/v2 (13/11)
# SLIDE4_LINE: the extra sentence on slide 4 (proposal, pending Steven's OK)
SLIDE4_LINE = "D'estate il caldo nei capannoni fa calare la produttività e mette in crisi anche i macchinari."
# CLOSE_IMG: photo behind the names on the last slide (a second frame from the videos, or the same one)
CLOSE_IMG = 'tecsaving-unita-magazzino.jpg'   # frame B from the same videos
SHARED = ('Logo-Tecsaving-ClimaIndustriale.jpg', COVER, CLOSE_IMG)
TAIL = 'Qui trova come climatizziamo i capannoni e come lavoriamo.'
GEN_SUB = 'In queste pagine trova come potremmo climatizzare i reparti di {c} e come lavoriamo.'
GEN_IDEA = 'Con un sopralluogo gratuito in sede vediamo insieme cosa si può fare nei vostri reparti.'
E = lambda s: html.escape(s, quote=False)
A = lambda s: html.escape(s, quote=True)
def slugify(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
def clarity_attr(sp):
    # no person's name in the Clarity tags: skip the slug tag when the slug holds the lead's first name
    words = {w.lower() for w in re.split(r'\W+', sp.get('first') or (sp.get('full_name') or '').split(' ')[0]) if len(w) >= 3}
    return ' data-no-slug' if words & set(sp['slug'].split('-')) else ''
W, S = "d'inverno", "d'estate"
def summer_first(s):
    # Francesco 12/11: summer cooling comes first wherever summer and winter appear together
    s = re.sub(rf"(\w+) {W} e (\w+) {S}", rf"\2 {S} e \1 {W}", s)
    s = re.sub(rf"{W} (con il \w+|\w+) e {S} (con il \w+|\w+)", rf"{S} \2 e {W} \1", s)
    s = re.sub(rf"{W} (per \w+) e {S} (per \w+)", rf"{S} \2 e {W} \1", s)
    for x, y in (("calore d'inverno e aria più fresca d'estate", "aria più fresca d'estate e calore d'inverno"),
                 ("caldo d'inverno e più fresco d'estate", "più fresco d'estate e caldo d'inverno"),
                 ("con il caldo d'inverno e il fresco d'estate", "con il fresco d'estate e il caldo d'inverno"),
                 (f"sia {W} sia {S}", f"sia {S} sia {W}")):
        s = s.replace(x, y)
    s = s.replace(f"{W} e {S}", f"{S} e {W}").replace(f"sia {W} che {S}", f"sia {S} che {W}").replace(f"{W} come {S}", f"{S} come {W}")
    return s
def render(sp):
    c, full, slug = sp['company'].strip(), (sp.get('full_name') or '').strip(), sp['slug']
    note, idea = summer_first((sp.get('cover_note') or '').strip()), summer_first((sp.get('idea') or '').strip())
    if (note or idea) and not sp.get('evidence'): raise ValueError(f'{slug}: claim about the lead with no evidence')
    if full and slugify(full) == slug: raise ValueError(f'{slug}: the slug is the person name')
    for t in (c, full, note, idea):
        if BAD.search(t): raise ValueError(f'{slug}: copy rule broken in {t!r}')
    vals = {'COMPANY': E(c), 'COMPANY_ATTR': A(c), 'PREP': E(f'{full} di {c}' if full else c), 'PREP_ATTR': A(f'{full} di {c}' if full else c),
            'OG_PATH': f'og/{slug}.jpg', 'LEAD_CSS': '', 'LEAD_MARK': f'<span class="nm">{E(c)}</span>',
            'H1': E(f'Il clima giusto nei reparti di {c}'),
            'SUB': E(f'{note} {TAIL}' if note else GEN_SUB.format(c=c)), 'IDEA': E(idea or GEN_IDEA), 'CLARITY_ATTR': clarity_attr(sp), 'COVER': COVER, 'CLOSE_IMG': CLOSE_IMG, 'SLIDE4_LINE': E(SLIDE4_LINE)}
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
