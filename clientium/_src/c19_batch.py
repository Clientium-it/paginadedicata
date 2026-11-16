"""c19_batch.py <batch.json> --out <folder outside the repo>: Clientium C19 generic pages (level 2, no claim about the lead).
batch rows: slug, company, first_name (+ anything else, ignored). Writes <out>/<slug>/index.html and <out>/specs/<slug>.json.
Never writes into the repo: copy index.html + spec in after the checks. A slug that already has a page or spec is skipped and listed."""
import json, os, re, sys
args = sys.argv[1:]; i = args.index('--out'); OUT = os.path.abspath(os.path.expanduser(args[i + 1])); src = args[0]
if os.path.realpath(OUT).startswith(os.path.realpath(os.path.expanduser('~/paginadedicata'))): sys.exit('out is inside the published repo: refused')
sys.argv = ['build.py']; HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); os.chdir(HERE)
import build
from c18_batch_nice import nice
BAD = re.compile(r'[—–:!]| - ')
LEGAL = r"s\.?\s?r\.?\s?l\.?(\s?s\.?)?|s\.?\s?p\.?\s?a\.?|s\.?\s?a\.?\s?s\.?|s\.?\s?n\.?\s?c\.?"
LONG = r"societ[aà]'?\s+(per\s+azioni|a\s+responsabilit[aà]'?\s+limitata|cooperativa(\s+agricola)?|agricola|benefit|di\s+\w+)|soc\.?\s?coop\.?|unipersonale|in\s+liquidazione"
WORDS = {'new', 'eco', 'art', 'bio', 'sud', 'web', 'lab', 'tec', 'oro', 'blu', 'sun', 'one', 'top', 'via'}
PART = {'di', 'e', 'ed', 'del', 'dei', 'la', 'le', 'il', 'lo', 'gli', 'per', 'con', 'da', 'in', 'al'}
def clean(n):
    n = re.sub(r'\s+', ' ', n.strip().strip('"'))
    n = re.sub(r'(?i)\.(?=unipersonale)|-(?=s\.?\s?[pr]\.?\s?[al]\.?)', ' ', n).rstrip('.') + ('.' if n.rstrip().endswith('..') else '')
    n = re.sub(r"(?i)\s+societ[aà]'?$", '', n)
    n = re.sub(rf"^({LONG})\s+", '', n, flags=re.I)                                   # 'SOCIETA' PER AZIONI CURTI' -> 'CURTI'
    n = re.split(rf"[\s,]+(?:{LEGAL})(?=[\s,\-]|$)|[\s,]+(?:{LONG})(?=[\s,\-]|$)", n, maxsplit=1, flags=re.I)[0]   # brand before the legal form
    parts = re.split(r'\s+-\s*|\s*-\s+', n)
    n = (parts[0] if len(re.sub(r'\W', '', parts[0])) > 2 else '-'.join(parts[:2])).strip(' ,.-')   # 'BRAND - long description' keeps the brand; 'E - PHARMA' -> 'E-PHARMA'
    if re.search(r'(?:\b[A-Za-z]\.)+[A-Za-z]$', n): n += '.'                           # C.M.L -> C.M.L., B. e C -> B. e C.
    elif re.search(r'\b[A-Z]\. e [A-Z]$', n): n += '.'                           # C.M.L -> C.M.L.
    if n.isupper() and len(n) > 4:                                                      # TRENTON -> Trenton; 3-letter words stay acronyms (FCE, LPM)
        n = ' '.join(w if (len(re.sub(r'\W', '', w)) <= 3 and w.lower() not in PART | WORDS) or re.fullmatch(r'(?:[A-Z]\.)+[A-Z]?\.?', w) else w.title() for w in n.split())
    n = re.sub(r'\bF\.Lli\b', 'F.lli', n)
    return nice(n)
os.makedirs(f'{OUT}/specs', exist_ok=True); ok, skip, bad = [], [], []
import unicodedata
def slugify(x):
    x = unicodedata.normalize('NFKD', x or '').encode('ascii', 'ignore').decode(); return re.sub(r'[^a-z0-9]+', '-', x.lower()).strip('-')
taken = lambda x: os.path.exists(os.path.join(HERE, '..', x)) or os.path.exists(os.path.join(HERE, 'specs', x + '.json'))
mine, rows = set(), []
for r in json.load(open(src, encoding='utf-8')):
    company = r.get('company') or r.get('companyName') or ''; first = (r.get('first_name') or r.get('firstName') or '').strip()
    first = first.title() if first.isupper() or first.islower() else first
    name = clean(company); s = r.get('slug')
    if s and r.get('reuse'):   # recontact with a valid page from an earlier campaign on the same company: keep that page and its URL
        mine.add(s); rows.append({'profileUrl': r.get('profileUrl') or r.get('linkedin', ''), 'firstName': first, 'lastName': r.get('lastName') or r.get('last_name', ''), 'companyName_raw': company, 'company': name, 'slug': s, 'page_url': f'https://paginadedicata.com/clientium/{s}/', 'bucket': r.get('bucket', ''), 'reused': True}); continue
    if s and taken(s): skip.append(s); continue
    if not s:   # one page per lead: a slug already used by another page (any campaign) or by this batch gets -2, -3...
        b = slugify(name) or 'azienda'; s, k = b, 2
        while taken(s) or s in mine: s, k = f'{b}-{k}', k + 1
    mine.add(s); rows.append({'profileUrl': r.get('profileUrl') or r.get('linkedin', ''), 'firstName': first, 'lastName': r.get('lastName') or r.get('last_name', ''), 'companyName_raw': company, 'company': name, 'slug': s, 'page_url': f'https://paginadedicata.com/clientium/{s}/', 'bucket': r.get('bucket', '')})
    if True:
        if not name or BAD.search(name) or BAD.search(first) or not first: bad.append((s, name, first)); continue
        sp = {'slug': s, 'company': name, 'first_name': first, 'domain': '', 'register': 'lei', 'sectors': [],
              'cases_first': 'EffePi Engineering', 'cases_allow': ['Planetica', 'EffePi Engineering', 'Neven', 'Publy Team', 'Cube Proemotion'],
              'campaign': 'C19', 'level': 2, 'base_note': f"Una pagina su come lavoriamo e su cosa potremmo fare per {name}."}
        page = build.shared_css(build.render(sp))
        os.makedirs(f'{OUT}/{s}', exist_ok=True); open(f'{OUT}/{s}/index.html', 'w', encoding='utf-8', newline='\n').write(page)
        json.dump(sp, open(f'{OUT}/specs/{s}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1); ok.append(s)
json.dump(rows, open(f'{OUT}/map.json', 'w'), ensure_ascii=False, indent=1)
json.dump({'built': ok, 'skipped': skip, 'bad': bad}, open(f'{OUT}/result.json', 'w'), ensure_ascii=False, indent=1)
print('built', len(ok), 'skipped (page exists)', len(skip), 'bad', len(bad))
