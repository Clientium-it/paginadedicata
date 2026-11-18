#!/usr/bin/env python3
"""Best-case Scenario pages: one spec JSON -> <out>/<slug>/index.html + <out>/assets/.
Usage: python3 build.py specs/*.json --out <folder outside the repo>
Refuses to write inside ~/paginadedicata. Generic pages unless the spec carries a verified claim (cover_note/idea need evidence).
Facts come from bestcasescenario.it (home, come-lavoriamo, checked 18/11/2026 from VPS5) and 03-clients/bestcase/context.md.
Packaging case (400 dipendenti, sei settimane): client-approved copy in HeyReach Best Case C2 v2 (723447), field messaggio2_BestCaseLinkedInC2_BestCase, confirmed by the OM 18/11.
Never state which systems the lead uses, no free audit or Diagnosi, no body rental or low-cost development, no client names."""
import html, json, os, re, shutil, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ASSETS = os.path.join(HERE, '..', 'assets')
TPL = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
BAD = re.compile(r'[—–:!;]| - ')
BANNED = re.compile(r'gratuit|gratis(?! *$)|Diagnosi|audit|assessment|body rental|low.cost|basso costo|economic|Qapl|Brandart|Boxeur|UniCredit|Sport e Salute|WBA|15 minuti|30 minuti', re.I)
SHARED = ('bcs-logo.png', 'bcs-favicon.ico')
# Booking calendar from the Calendar Manager (via the OM). Empty = LinkedIn reply CTA on the last slide.
CAL_URL = ''
CTA_LI = open(os.path.join(HERE, 'cta_linkedin.html'), encoding='utf-8').read()
TAIL = 'Qui trova come colleghiamo i sistemi che ci sono già e togliamo i passaggi fatti a mano.'
GEN_SUB = "In queste pagine trova come Best-case Scenario ottimizza i processi collegando i sistemi che un'azienda ha già, toglie i passaggi fatti a mano come copia e incolla e fogli Excel, senza rifare l'ERP."
GEN_IDEA = "La domanda giusta non è quale sistema cambiare, ma dove i sistemi costringono ancora a usare Excel."
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
    cal = f'<iframe id="calf" title="Calendario Best-case Scenario" data-src="{A(CAL_URL + ("&" if "?" in CAL_URL else "?") + "utm_source=deck&utm_medium=linkedin&utm_campaign=" + slug)}"></iframe>' if CAL_URL else CTA_LI
    lead_css = 'html:not(.phone) h1{font-size:44px}' if len(c) > 30 else 'html:not(.phone) h1{font-size:48px}' if len(c) > 20 else ''
    vals = {'COMPANY': E(c), 'COMPANY_ATTR': A(c), 'PREP': E(f'{full} di {c}' if full else c), 'PREP_ATTR': A(f'{full} di {c}' if full else c),
            'OG_PATH': f'og/{slug}.jpg', 'LEAD_CSS': lead_css, 'LEAD_MARK': f'<span class="nm">{E(c)}</span>',
            'H1': E(f'Processi più snelli per {c}, collegando i sistemi che ci sono già'),
            'SUB': E(f'{note} {TAIL}' if note else GEN_SUB), 'IDEA': E(idea or GEN_IDEA), 'CLARITY_ATTR': clarity_attr(sp), 'CAL_BLOCK': cal}
    page = re.sub(r'\{\{(\w+)\}\}', lambda m: vals[m.group(1)], TPL)
    v = visible(page)
    m = BAD.search(v)
    if m: raise ValueError(f'{slug}: copy rule broken in {m.group(0)!r} near {v[max(0, m.start() - 40):m.start() + 10]!r}')
    m = BANNED.search(v.replace('ogni bug corretto gratis', ''))
    if m: raise ValueError(f'{slug}: banned phrase {m.group(0)!r}')
    if len(re.findall(r'400 dipendenti', v)) != 2: raise ValueError(f'{slug}: the packaging case must appear as written')
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
