"""mkspecs.py <batch.json> <workdir> [seat]: AssessFirst batch -> <workdir>/specs/<slug>.json.
Fact version only where the open job ad was verified (titolo_annuncio + link_annuncio): cover says the company is hiring that role, evidence = the ad."""
import json, os, re, sys
d = json.load(open(sys.argv[1], encoding='utf-8')); W = sys.argv[2]; seat = sys.argv[3] if len(sys.argv) > 3 else ''
os.makedirs(f'{W}/specs', exist_ok=True)
CH = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), 'af_lp_cliente_changes.json')
EXCL = {}
if os.path.exists(CH):
    for x in json.load(open(CH, encoding='utf-8')): EXCL.setdefault(x['slug'], []).append(x['old'])
nm = lambda s: ' '.join(w.capitalize() if w.isupper() or w.islower() else w for w in (s or '').strip().split())
IDEA = 'Per un ruolo come questo, prima del colloquio vedete quanto il modo di lavorare di ogni candidato si adatta a ciò che serve.'
n = fact = 0
for r in d:
    if seat and r['seat'] != seat: continue
    f, l, c = nm(r['first_name']), nm(r['last_name']), r['company'].strip()
    real = len(f) > 2 and len(l) > 2 and f.lower() != l.lower() and f.lower() not in c.lower().split()
    sp = {'slug': r['slug'], 'company': c, 'first': f, 'full_name': f'{f} {l}' if real else '', 'cliente_citato': r.get('cliente_citato') or '', 'clienti_esclusi': EXCL.get(r['slug'], [])}
    role = (r.get('ruolo_annuncio') or '').strip().rstrip('.')
    if role and r.get('link_annuncio') and r.get('titolo_annuncio'):
        sp.update(cover_note=f'{c} sta cercando {role}.', idea=IDEA,
                  evidence=[{'claim': f'{c} ha un annuncio aperto per {role}', 'url': r['link_annuncio'], 'quote': r['titolo_annuncio']}])
        fact += 1
    json.dump(sp, open(f"{W}/specs/{r['slug']}.json", 'w', encoding='utf-8'), ensure_ascii=False); n += 1
print(n, 'specs,', fact, 'with the job ad')
