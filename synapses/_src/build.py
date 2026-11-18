#!/usr/bin/env python3
"""Synapses pages: one spec JSON -> <out>/<slug>/index.html + <out>/assets/.
Usage: python3 build.py specs/*.json --out <folder outside the repo>
Refuses to write inside ~/paginadedicata. Generic pages unless the spec carries a verified claim (cover_note/idea need evidence).
Facts on the page come from synapses.it (home, chi-siamo) and Paolo's brief on Drive; checked 18/11/2026.
Never "agenti a provvigione", "a basso costo", "senza costi fissi"; the five-month case appears once, as proof."""
import html, json, os, re, shutil, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ASSETS = os.path.join(HERE, '..', 'assets')
TPL = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
BAD = re.compile(r'[—–:!;]| - ')
BANNED = re.compile(r'provvigion|basso costo|costi fissi|SIMEST|fondo perduto', re.I)
SHARED = ('synapses-logo.png', 'paolo-bizzotto.jpg', 'synapses-favicon.svg')
# Paolo's booking calendar: ask Paolo for the link. Empty = placeholder box on the last slide.
CAL_URL = 'https://api.leadconnectorhq.com/widget/booking/r2ZA2wDorFXVQFxHHL0o'   # 'Synapses - LinkedIn' (Teams). Only this one, never the other Synapses calendar.
TAIL = 'Qui trova come costruiamo il presidio commerciale nel DACH, zona per zona.'
GEN_SUB = "In queste pagine trova come Synapses costruisce per i produttori italiani come {c} l'organizzazione commerciale in Germania, Austria e Svizzera, con una regia che la tiene sui numeri."
GEN_IDEA = "Raramente il problema è il prodotto. Quasi sempre manca l'organizzazione intorno a chi vende."
CAL_PH = ('<div class="calph"><div class="bx"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
          '<rect x="3" y="4.5" width="18" height="16" rx="2"/><path d="M3 9.5h18M8 2.5v4M16 2.5v4"/></svg>'
          '<b>Il calendario di Paolo Bizzotto</b><span>Qui sceglie il giorno e l\'orario per una breve call Teams.</span></div></div>')
E = lambda s: html.escape(s, quote=False)
A = lambda s: html.escape(s, quote=True)
def slugify(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
def clarity_attr(sp):
    words = {w.lower() for w in re.split(r'\W+', sp.get('first') or (sp.get('full_name') or '').split(' ')[0]) if len(w) >= 3}
    return ' data-no-slug' if words & set(sp['slug'].split('-')) else ''
def visible(page):
    t = re.sub(r'<script.*?</script>|<style.*?</style>|<head>.*?</head>', ' ', page, flags=re.S)
    return html.unescape(re.sub(r'<[^>]+>', ' ', t))
def render(sp):
    c, full, slug = sp['company'].strip(), (sp.get('full_name') or '').strip(), sp['slug']
    note, idea = (sp.get('cover_note') or '').strip(), (sp.get('idea') or '').strip()
    if (note or idea) and not sp.get('evidence'): raise ValueError(f'{slug}: claim about the lead with no evidence')
    if full and slugify(full) == slug: raise ValueError(f'{slug}: the slug is the person name')
    cal = f'<iframe id="calf" title="Calendario di Paolo Bizzotto" data-src="{A(CAL_URL + "?utm_source=deck&utm_medium=linkedin&utm_campaign=" + slug)}"></iframe>' if CAL_URL else CAL_PH
    lead_css = 'html:not(.phone) h1{font-size:44px}' if len(c) > 30 else 'html:not(.phone) h1{font-size:48px}' if len(c) > 20 else ''
    vals = {'COMPANY': E(c), 'COMPANY_ATTR': A(c), 'PREP': E(f'{full} di {c}' if full else c), 'PREP_ATTR': A(f'{full} di {c}' if full else c),
            'OG_PATH': f'og/{slug}.jpg', 'LEAD_CSS': lead_css, 'LEAD_MARK': f'<span class="nm">{E(c)}</span>',
            'H1': E(f'Il presidio commerciale nel DACH, zona per zona, per {c}'),
            'SUB': E(f'{note} {TAIL}' if note else GEN_SUB.format(c=c)), 'IDEA': E(idea or GEN_IDEA), 'CLARITY_ATTR': clarity_attr(sp), 'CAL_BLOCK': cal}
    page = re.sub(r'\{\{(\w+)\}\}', lambda m: vals[m.group(1)], TPL)
    v = visible(page)
    if BAD.search(v.replace('Dipl.-Ing.', '')): raise ValueError(f'{slug}: copy rule broken in {BAD.search(v).group(0)!r} near {v[max(0, BAD.search(v).start() - 40):BAD.search(v).start() + 10]!r}')
    if BANNED.search(v): raise ValueError(f'{slug}: banned phrase {BANNED.search(v).group(0)!r}')
    if len(re.findall(r'cinque mesi', v)) != 1: raise ValueError(f'{slug}: the five-month case must appear exactly once')
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
    print(len(done), 'pages in', out, '|', bad, 'refused'); sys.exit(1 if bad else 0)
if __name__ == '__main__': main()
