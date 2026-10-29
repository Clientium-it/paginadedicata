#!/usr/bin/env python3
"""facts.py: lead website -> fact sheet (runs/<slug>/facts.txt) + facts.json, screenshot and logo on the way.
Usage: python3 facts.py <slug> "<First Last>" "<Company>" <url>
No model involved. Everything the model may say must be a line here; every number it writes is checked against this file.
The point selection (CHECKS) is where you encode YOUR offer: a condition on the facts and a fixed score, top 4 win.
"""
import asyncio, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import shot
RUNS = os.path.join(HERE, 'runs')
PROOF = re.compile(r'(?<![\d+]\s)(?<![\d+])(\d[\d.,]*\s?(?:k|mila|milioni|M)?\+?)\s*(clienti|aziende|imprese|appuntamenti|anni|progetti|dipendenti|persone|sedi|paesi|risposte|contatti|decisori|opportunità|meeting|recensioni|partner|settori)', re.I)
MONEY = re.compile(r'€\s?\d[\d.,]*\s?(?:k|mila|M|milioni)?|\d[\d.,]*\s?(?:€|euro)', re.I)
OFFER = re.compile(r'((?:analisi|consulenza|sessione|demo|prova|mappatura|audit|preventivo)\s+(?:gratuit[ao]|gratis|senza impegno)[^.\n]{0,50}|garanzia[^.\n]{0,60}|paghi solo[^.\n]{0,60}|soddisfatti o rimborsati[^.\n]{0,30})', re.I)
CTA = re.compile(r'\b(prenota[^.\n]{0,40}|richiedi[^.\n]{0,40}|contattaci|parla con[^.\n]{0,30}|fissa[^.\n]{0,30})', re.I)
QUOTE = re.compile(r'[«“"]([^»”"\n]{40,220})[»”"]')
FAQ = re.compile(r'^([A-ZÈÉ][^\n?]{12,140}\?)\s*$', re.M)
SECTORS = re.compile(r'\b(manifatturiero|industria|metalmeccanic\w*|edilizia|logistica|alimentare|food|moda|fashion|farmaceutic\w*|sanità|software|saas|ict|consulenza|formazione|energia|automotive|retail|finanza|assicura\w*|marketing|ingegneria|chimic\w*|arredamento|turismo|eventi)\b', re.I)
SOCIAL = re.compile(r'(instagram|tiktok|youtube|facebook|linkedin|x\.com|twitter)\.com', re.I)
NAMED_CASE = re.compile(r'(?:casi studio|caso studio|case study)\s*/\s*([A-Z][\w&.\' ]{2,40})')

def lines(pages):
    text = '\n'.join(p['text'] for p in pages)
    f = {}
    f['proof'] = list(dict.fromkeys(' '.join(m.group(0).split()) for m in PROOF.finditer(text)))[:10]
    f['money'] = list(dict.fromkeys(' '.join(m.group(0).split()) for m in MONEY.finditer(text)))[:8]
    f['offers'] = list(dict.fromkeys(' '.join(m.group(1).split()) for m in OFFER.finditer(text)))[:6]
    f['ctas'] = list(dict.fromkeys(' '.join(m.group(1).split()).lower() for m in CTA.finditer(text)))[:6]
    f['quotes'] = [q.strip() for q in QUOTE.findall(text)][:3]
    f['faq'] = list(dict.fromkeys(FAQ.findall(text)))[:8]
    f['sectors'] = sorted({m.group(1).lower() for m in SECTORS.finditer(text)})[:12]
    f['social'] = sorted({m.group(1).lower().replace('x.com', 'x') for m in SOCIAL.finditer(text + ' '.join(p['url'] for p in pages))})
    f['cases_page'] = any(re.search(r'casi|case|clienti|referenze|risultati', p['url'], re.I) for p in pages)
    home = pages[0]['text'] if pages else ''
    f['home_has_proof'] = bool(PROOF.search(home[:1500]))
    f['home_has_offer'] = bool(OFFER.search(home[:1500]))
    f['ctas_on_home'] = len(CTA.findall(home))
    f['pages'] = [p['url'] for p in pages]
    return f

# ---- L'OFFERTA DI CLIENTIUM VIVE QUI: (nome, condizione(fatti) -> bool, punteggio, direzione). I primi 4 per punteggio diventano POINTS TO WRITE.
CHECKS = [
    ('Prove forti ferme sul sito', lambda f: len(f['proof']) + len(f['money']) >= 3, 90,
     'i numeri che il sito già mostra devono aprire il primo messaggio a un decisore che non vi conosce, non aspettare che visiti il sito'),
    ('Casi con nome usabili come aggancio per settore', lambda f: f['cases_page'] and len(f['sectors']) >= 3, 85,
     'ogni settore servito riceve il caso del suo settore come prima riga, stesso problema, stesso risultato'),
    ('Il sito converte solo chi vi cerca già', lambda f: f['ctas_on_home'] >= 1, 80,
     'il sito chiede di prenotare a chi arriva da solo; un sistema outbound porta in agenda i decisori che oggi non vi cercano'),
    ('Offerta forte da portare fuori dal sito', lambda f: bool(f['offers']), 75,
     "l'offerta del sito va scritta uguale nella prima email e nel primo messaggio LinkedIn"),
    ('Domande del buyer già pronte', lambda f: len(f['faq']) >= 3, 65,
     'le domande della pagina FAQ diventano le risposte nei follow up, una per messaggio'),
    ('Molti settori, un messaggio', lambda f: len(f['sectors']) >= 5, 60,
     'un segmento per campagna, con copy e prova del settore, invece di un messaggio unico per tutti'),
    ('Un segmento per campagna', lambda f: True, 8,
     'un segmento per campagna, con il linguaggio e la prova di quel settore, e il volume spostato dove arrivano le risposte'),
    ('Follow up che portano qualcosa', lambda f: True, 6,
     'ogni follow up porta un elemento nuovo, un caso, una domanda frequente, un dato, invece di ripetere la richiesta'),
    ('Verità di categoria', lambda f: True, 10,
     'i decisori B2B rispondono a chi mostra un risultato su un caso simile al loro e chiede poco tempo'),
]

def points(f):
    hits = [(n, s, d) for n, c, s, d in CHECKS if c(f)]
    hits.sort(key=lambda x: -x[1])
    return hits[:2]

def sheet(lead, company, url, f, pts, blocked):
    L = [f'LEAD: {lead}, {company}, {url}']
    if blocked:
        L.append('SITE: COULD NOT BE LOADED'); L.append('POINTS TO WRITE:'); L += [f'{i+1}. {n}. Direction: {d}' for i, (n, s, d) in enumerate(pts)]; return '\n'.join(L)
    L.append('SITE PROOF: ' + ('; '.join(f['proof']) or 'none found'))
    L.append('SITE MONEY FIGURES: ' + ('; '.join(f['money']) or 'none found'))
    L.append('SITE OFFERS: ' + ('; '.join(f['offers']) or 'none found'))
    L.append('SITE CALLS TO ACTION: ' + ('; '.join(f['ctas']) or 'none found'))
    L.append('SITE QUOTES: ' + ('; '.join('"' + q + '"' for q in f['quotes']) or 'none found'))
    L.append('SITE FAQ: ' + ('; '.join(f['faq']) or 'none found'))
    L.append('SECTORS NAMED: ' + (', '.join(f['sectors']) or 'none found'))
    L.append('SOCIAL: ' + (', '.join(f['social']) or 'none linked'))
    done = [x for x, ok in (('pagina casi studio', f['cases_page']), ('prove in homepage', f['home_has_proof']), ('offerta in homepage', f['home_has_offer']), ('prenotazione dal sito', f['ctas_on_home'] > 0)) if ok]
    L.append('ALREADY DONE: ' + ('; '.join(done) or 'nothing of note'))
    L.append(f'SITE: LOADED ({len(f["pages"])} pages)')
    L.append('POINTS TO WRITE:')
    L += [f'{i+1}. {n}. Direction: {d}' for i, (n, s, d) in enumerate(pts)]
    L.append('HOMEPAGE TEXT (first 2500 chars):')
    return '\n'.join(L)

def run(slug, lead, company, url):
    d = os.path.join(RUNS, slug); os.makedirs(d, exist_ok=True)
    if not url.startswith('http'): url = 'https://' + url
    r = asyncio.run(shot.session(url, slug, max_pages=5))
    f = lines(r['pages']) if not r['blocked'] else {}
    pts = points(f) if f else [c[:1] + c[2:] for c in CHECKS[-1:]]
    txt = sheet(lead, company, url, f, pts, r['blocked'])
    if not r['blocked']: txt += '\n' + r['pages'][0]['text'][:2500]
    open(os.path.join(d, 'facts.txt'), 'w', encoding='utf-8').write(txt)
    meta = {'slug': slug, 'lead': lead, 'company': company, 'url': url, 'shot': r['shot'], 'logo': r['logo'], 'blocked': r['blocked'], 'pages': [p['url'] for p in r['pages']], 'points': pts}
    json.dump(meta, open(os.path.join(d, 'facts.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    return meta, txt

if __name__ == '__main__':
    meta, txt = run(*sys.argv[1:5]); print(txt[:1500]); print(json.dumps({k: v for k, v in meta.items() if k != 'points'}))
