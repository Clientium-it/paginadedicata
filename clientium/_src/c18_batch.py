"""c18_batch.py <batch.json> <slugs_out.json>: Clientium C18 pages from an Enrichment batch (slug, company, first_name, domain, case).
No market, idea or evidence in C18: the page has cover, offer, cases and the calendar slide.
A slug that already has a page is skipped and listed: published slugs never change."""
import json, os, sys
sys.argv, args = ['build.py'], sys.argv[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import build
HERE = os.path.dirname(os.path.abspath(__file__))
import re
LOW = set('di e ed per del della dello dei degli delle il la le lo gli a al alla ai alle da dal dalla in con su tra fra and the of for'.split())
SHORT = {'bertolotti-soc-per-az-impianti-per-l-industria-siderurgica-e-mineraria': 'Bertolotti',   # register names too long for the cover
         'i-c-m-a-san-giorgio-industria-costruzioni-macchine-e-affini': 'I.C.M.A. San Giorgio',
         'si': 'SISAS',
         'emerson-automation-fluid-control-pneumatics-italy': 'Emerson Automation'}   # register name 'SI', the messages say SISAS
def nice(name):
    """display casing for names from the business register: only mechanical fixes, never new words"""
    n = re.sub(r"[- ]+societa' per azioni$", '', name.strip(), flags=re.I)
    n = re.sub(r"\s+Soc\. Coop\..*$", '', n)
    n = re.sub(r"([aeiou])'(?=\s|$)", lambda m: {'a': 'à', 'e': 'è', 'i': 'ì', 'o': 'ò', 'u': 'ù'}[m.group(1)], n)
    out = []
    for i, w in enumerate(n.split()):
        if i and w.lower() in LOW: w = w.lower()
        elif i and w.isupper() and w.lower() in ('vie', 'and', 'the'): w = w.capitalize() if w.lower() == 'vie' else w.lower()
        if w[:1].isupper(): w = re.sub(r"(?<=[-'])([a-zà-ù])", lambda m: m.group(1).upper(), w)   # mc-link stays as the brand writes it
        if i and re.match(r"(L|D|Dell|Nell|All|Sull|Dall)'", w): w = w[0].lower() + w[1:]
        out.append(w)
    return ' '.join(out)
d = json.load(open(args[0], encoding='utf-8')); ok, skip = [], []
REBUILD = '--rebuild' in args   # rebuild pages this script made before (same slugs), never other campaigns' pages
for r in d:
    sf = os.path.join(HERE, 'specs', r['slug'] + '.json')
    mine = os.path.exists(sf) and json.load(open(sf, encoding='utf-8')).get('campaign') == 'C18'
    if os.path.exists(os.path.join(HERE, '..', r['slug'], 'index.html')) and not (REBUILD and mine): skip.append(r['slug']); continue
    name = SHORT.get(r['slug']) or SHORT.get(re.sub(r'-\d+$', '', r['slug'])) or nice(r['company'])
    sp = {'slug': r['slug'], 'company': name, 'first_name': r['first_name'], 'domain': r['domain'], 'register': 'lei', 'sectors': [],
          'cases_first': r['case'], 'cases_allow': ['Planetica', 'EffePi Engineering', 'Neven', 'Publy Team', 'Cube Proemotion'],
          'campaign': 'C18', 'level': 2, 'base_note': f"Una pagina su come lavoriamo e su cosa potremmo fare per {name}."}
    json.dump(sp, open(os.path.join(HERE, 'specs', r['slug'] + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    page = build.shared_css(build.render(sp))
    os.makedirs(os.path.join(HERE, '..', r['slug']), exist_ok=True)
    open(os.path.join(HERE, '..', r['slug'], 'index.html'), 'w', encoding='utf-8', newline='\n').write(page); ok.append(r['slug'])
json.dump(ok, open(args[1], 'w')); print('built', len(ok), 'skipped (page already exists)', skip)
