#!/usr/bin/env python3
"""Thrive Core M2 pages: one spec JSON -> <out>/<slug>/index.html + <out>/assets/.
Usage: python3 build.py specs/*.json --out <folder outside the repo>
Spec: slug, company, first (optional), fact, idea, evidence [{claim,url,quote}], revenue_m (F, M EUR, optional).
Benefit estimate = Gabriele Romoli formula (~/linkedin-campaigns/thrivecore-li/FORMULA_BENEFICIO_THRIVECORE.md).
No revenue_m -> the estimate slide shows no number."""
import html, json, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ASSETS = os.path.join(HERE, '..', 'assets')
TPL = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
BAD = re.compile(r'[—–:!;]| - ')
SHARED = ('logo-thrivecore.svg', 'og.jpg')
E = lambda s: html.escape(s, quote=False); A = lambda s: html.escape(s, quote=True)
fin = lambda s: s if s.endswith(('.', '?')) else s + '.'
eu = lambda x: f"{int(round(x)):,}".replace(',', '.')
k = lambda x: eu(round(x / 1000) * 1000)
pc = lambda x, d=1: f"{x:.{d}f}".replace('.', ',') + '%'
def art(x):
    p = pc(x); ip = int(x)
    return ('allo ' if ip == 0 else "all'" if ip in (1, 11) or p.startswith('8') else 'al ') + p
num = lambda x: (f"{x:g}").replace('.', ',')
def benefit(F):
    P = F * 1e6; G = round(13.75 + 0.75 * F); C = round(0.25 + F / 4)
    lo = dict(gare=G*88*35*.25, acq=P*.699*.005, tempo=P*.065*.75*.01, capi=C*220*(32/60)*15)
    hi = dict(gare=G*88*35*.50, acq=P*.699*.015, tempo=P*.065*.75*.03, capi=C*220*(32/60)*30)
    lo['tot'] = sum(lo.values()); hi['tot'] = sum(hi.values())
    assert abs(lo['tot'] - (770*G + .0039825*P + 1760*C)) < 1 and abs(hi['tot'] - (1540*G + .0119475*P + 3520*C)) < 1
    return P, G, C, lo, hi
def est_html(c, F):
    if not F:
        return f'''<div class="eyebrow">Il beneficio per {E(c)}</div>
  <h2>Quanto vale per voi, calcolato sui vostri numeri</h2>
  <div class="nonum"><p>Per stimare il beneficio annuo partiamo dal fatturato dell'ultimo bilancio e guardiamo quattro voci, una per una.</p>
  <ul><li>Le ore dell'ufficio tecnico sulle gare</li><li>Gli acquisti di commessa</li><li>Il tempo che oggi va nel ribattere i dati</li><li>Il lavoro dei capicantiere</li></ul>
  <p>Se le interessa, la stima con i numeri di {E(c)} gliela preparo prima della call.</p></div>'''
    P, G, C, lo, hi = benefit(F)
    rows = [('Gare', f'{G} gare studiate in un anno, 88 ore ciascuna a 35 € l\'ora, con il 25% di tempo risparmiato (prudente) o il 50% (atteso)', 'gare'),
            ('Acquisti', 'il 69,9% della produzione in acquisti, con un risparmio dello 0,5% (prudente) o dell\'1,5% (atteso)', 'acq'),
            ('Tempo', 'il 6,5% della produzione per il 75%, con un recupero dell\'1% (prudente) o del 3% (atteso)', 'tempo'),
            ('Capicantiere', f'{C} capicantiere, 220 giorni l\'anno, 32 minuti al giorno a 15 € (prudente) o 30 € (atteso) l\'ora', 'capi')]
    tr = ''.join(f'<tr><td><b>{a}</b><small>{E(b)}</small></td><td class="n"><span class="ca">circa </span>{k(lo[x])} €</td><td class="n"><span class="ca">circa </span>{k(hi[x])} €</td></tr>' for a, b, x in rows)
    return f'''<div class="eyebrow">Il beneficio per {E(c)} <span class="tag">Stima</span></div>
  <h2>Circa {k(lo['tot'])} € l'anno nella stima prudente, circa {k(hi['tot'])} € in quella attesa</h2>
  <div class="est">
    <div class="tot">
      <div class="tb"><i>Stima prudente</i><b>circa {k(lo['tot'])} €</b><span>l'anno, pari {art(lo['tot']/P*100)} della produzione</span></div>
      <div class="tb a"><i>Stima attesa</i><b>circa {k(hi['tot'])} €</b><span>l'anno, pari {art(hi['tot']/P*100)} della produzione</span></div>
    </div>
    <div><table class="tbl"><tr><th>Come si calcola</th><th class="n">Prudente</th><th class="n">Attesa</th></tr>{tr}
    <tr class="sum"><td>Totale annuo</td><td class="n"><span class="ca">circa </span>{k(lo['tot'])} €</td><td class="n"><span class="ca">circa </span>{k(hi['tot'])} €</td></tr></table>
    <p class="how">È una stima, non un preventivo. Parte da una produzione di circa {num(round(F,1))} milioni di euro (fatturato dell'ultimo bilancio) e usa parametri medi del settore, che in call verifichiamo con i vostri numeri reali.</p></div>
  </div>'''
def render(sp):
    c, first, slug = sp['company'].strip(), (sp.get('first') or '').strip(), sp['slug']
    fact, idea = (sp.get('fact') or '').strip(), (sp.get('idea') or '').strip()
    if not (fact and idea and sp.get('evidence')): raise ValueError(f'{slug}: needs fact, idea and evidence')
    for t in (c, first, fact, idea):
        if BAD.search(t): raise ValueError(f'{slug}: copy rule broken in {t!r}')
    prep = f'{first} di {c}' if first else c
    est = est_html(c, sp.get('revenue_m'))
    body = re.sub(r'<[^>]+>', ' ', est)
    if BAD.search(html.unescape(body)): raise ValueError(f'{slug}: copy rule broken in estimate')
    vals = {'COMPANY': E(c), 'COMPANY_ATTR': A(c), 'PREP': E(prep), 'PREP_ATTR': A(prep), 'FACT': E(fin(fact)), 'IDEA': E(fin(idea)), 'EST': est,
            'LEAD_CSS': 'h1{font-size:40px}' if len(c) > 30 else '', 'CLARITY_ATTR': ''}
    return re.sub(r'\{\{(\w+)\}\}', lambda m: vals[m.group(1)], TPL)
def main():
    args = sys.argv[1:]; i = args.index('--out'); out = os.path.abspath(os.path.expanduser(args[i + 1])); specs = args[:i] + args[i + 2:]
    if os.path.realpath(out).startswith(os.path.realpath(os.path.expanduser('~/paginadedicata'))): sys.exit('out is inside the published repo: refused')
    os.makedirs(f'{out}/assets', exist_ok=True)
    for f in SHARED:
        if os.path.exists(os.path.join(ASSETS, f)): shutil.copy(os.path.join(ASSETS, f), f'{out}/assets/{f}')
    done, bad = [], 0
    for p in specs:
        sp = json.load(open(p, encoding='utf-8'))
        try: page = render(sp)
        except ValueError as e: print('REFUSED', e); bad += 1; continue
        os.makedirs(f"{out}/{sp['slug']}", exist_ok=True)
        open(f"{out}/{sp['slug']}/index.html", 'w', encoding='utf-8').write(page); done.append(sp['slug'])
    json.dump({'built': done}, open(f'{out}/result.json', 'w'))
    print(len(done), 'pages in', out, '|', bad, 'refused'); sys.exit(1 if bad else 0)
if __name__ == '__main__': main()
