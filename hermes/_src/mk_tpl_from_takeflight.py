"""Derive the Hermes and Genitori.it templates from the Take Flight one (same slide engine, phone layout and checks)."""
import os, re
P = os.path.expanduser('~/paginadedicata'); T = open(f'{P}/takeflight/_src/template.html', encoding='utf-8').read()
head_end = T.index('<section data-i="1"'); tail_start = T.index('</div></div>\n<nav class="pnav"')
css_a = T[:head_end]; js = T[tail_start:]
CLOSE_CSS = ('.talk.nocal .l{flex:1;align-items:center;justify-content:center;text-align:center;border-right:0;padding:48px 64px;gap:26px;background:radial-gradient(90% 70% at 50% 0%,var(--glow),transparent 70%),var(--card)}'
 '.talk.nocal .chip img{height:56px}.talk.nocal .chip{padding:12px 20px}'
 '.talk.nocal h2{font-size:58px;line-height:1.08}.talk.nocal .why{font-size:26px;line-height:1.4;max-width:780px}.talk.nocal .alt{font-size:20px;max-width:640px;color:var(--slate)}'
 '.talk.nocal h2::after{content:"";display:block;width:72px;height:4px;border-radius:2px;background:var(--red);margin:22px auto 0}'
 'html.phone .talk.nocal .l{flex:1 1 auto;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;border-bottom:0;padding:28px 22px;gap:18px}'
 'html.phone .talk.nocal .chip{display:flex}html.phone .talk.nocal .chip img{height:38px}'
 'html.phone .talk.nocal h2{font-size:30px}html.phone .talk.nocal h2::after{margin-top:16px;width:56px}html.phone .talk.nocal .why{font-size:18px;line-height:1.4}html.phone .talk.nocal .alt{font-size:15px;line-height:1.4}\n')
def make(name, brand, logo, logo_alt, root, font_link, font, og_desc, cover_r, cover_css, slides, talk_why):
    h = css_a.replace('{{COMPANY}} e Take Flight', '{{COMPANY}} e ' + brand).replace('{{COMPANY_ATTR}} e Take Flight', '{{COMPANY_ATTR}} e ' + brand)
    h = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{og_desc}">', h)
    h = h.replace('/takeflight/assets/', f'/{name}/assets/')
    h = re.sub(r':root\{[^}]*\}', ':root{' + root + '}', h, 1)
    h = re.sub(r'<link href="https://fonts.googleapis.com/css2[^>]*>', font_link, h)
    h = h.replace('font-family:Montserrat,system-ui,sans-serif', f'font-family:{font},system-ui,sans-serif')
    h = re.sub(r'\.cover \.r\{flex:\.9;[^}]*\}', '.cover .r{flex:.9;border-left:5px solid var(--red);min-width:0}', h)
    h = h.replace('.talk .rp{flex:1;background:#fff url(../assets/report.svg) center/contain no-repeat}', '')
    h = h.replace('.cover .r,.talk .rp{background-size:contain;background-origin:content-box;padding:28px 24px}html.phone .cover .r{flex-basis:34%;padding:10px 12px}html.phone .talk .rp{padding:12px}',
                  'html.phone .cover .r{flex:0 0 26%;border-left:0;border-top:4px solid var(--red)}')
    h = h.replace('{{LEAD_CSS}}</style>', cover_css + CLOSE_CSS + '{{LEAD_CSS}}</style>')
    cover = f'''<section data-i="1" aria-label="Preparata per {{{{COMPANY_ATTR}}}}" class="on"><div class="s cover">
  <div class="l">
    <div class="pair"><span class="chip"><img src="../assets/{logo}" alt="{logo_alt}"></span><span class="x">×</span>{{{{LEAD_MARK}}}}</div>
    <div class="m">
      <div class="eyebrow">Preparata per {{{{PREP}}}}</div>
      <h1>{{{{H1}}}}</h1>
      <p class="sub">{{{{SUB}}}}</p>
    </div>
  </div>
  {cover_r}
</div></section>
'''
    talk = f'''
<section data-i="5" aria-label="Parliamone"><div class="s talk{{{{TALK_CLASS}}}}">
  <div class="l">
    <span class="chip"><img src="../assets/{logo}" alt="{logo_alt}"></span>
    <h2>Parliamo di {{{{COMPANY}}}}</h2>
    <p class="why">{talk_why}</p>
    <a class="btn" href="{{{{CAL_URL}}}}" target="_blank" rel="noopener">Prenoti una call</a>
    <p class="alt">Può rispondere al messaggio che ha ricevuto su LinkedIn.</p>
  </div>
  {{{{TALK_RIGHT}}}}
</div></section>

'''
    open(f'{P}/{name}/_src/template.html', 'w', encoding='utf-8').write(h + cover + slides + talk + js)

make('hermes', 'Hermes Management Consulting', 'hermes-logo.png', 'Hermes Management Consulting',
 '--red:#0b4fd6;--slate:#0a2259;--ink:#1c2433;--mute:#5f6b7a;--line:#dde3ec;--card:#f3f6fb;--bg:#fff;--glow:rgba(11,79,214,.08)',
 '<link href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&display=swap" rel="stylesheet">', "'Inter Tight'",
 'Una pagina preparata per {{PREP_ATTR}} su come liberare liquidità senza occupare il fido.',
 '<div class="r hv" aria-hidden="true"><div class="big">50+</div><div class="cap">istituti bancari e partner finanziari confrontati per voi</div><div class="tl"><span>Analisi<b>2 o 3 giorni</b></span><span>Chiusura<b>7/10 giorni lavorativi</b></span><span>Compenso<b>solo a successo</b></span></div></div>',
 '.hv{background:radial-gradient(120% 90% at 85% 0%,#1d5be0 0%,#0a2259 60%);color:#fff;display:flex;flex-direction:column;justify-content:center;padding:56px 56px 84px;gap:14px}'
 '.hv .big{font-size:150px;font-weight:700;line-height:.9;letter-spacing:-.03em}.hv .cap{font-size:24px;line-height:1.3;max-width:420px;color:#dfe8ff}'
 '.hv .tl{display:grid;gap:10px;margin-top:26px}.hv .tl span{display:flex;justify-content:space-between;gap:14px;border-top:1px solid rgba(255,255,255,.22);padding-top:10px;font-size:17px;color:#c8d6f5}.hv .tl b{color:#fff;font-weight:600}'
 'html.phone .hv{padding:12px 18px;gap:2px;flex-direction:row;flex-wrap:wrap;align-items:center;column-gap:14px}html.phone .hv .big{font-size:58px}html.phone .hv .cap{font-size:13.5px;max-width:200px}html.phone .hv .tl{display:none}'
 '@media (max-height:700px){html.phone .hv .big{font-size:42px}html.phone .hv .cap{font-size:12px}}',
 '''<section data-i="2" aria-label="Cosa facciamo"><div class="s">
  <div class="eyebrow">Cosa facciamo</div>
  <h2>Liquidità per {{COMPANY}}, dalla banca giusta</h2>
  <div class="mk">
    <div><b>Anticipo fatture</b><span>Incassate subito quello che avete già fatturato, senza aspettare i tempi del cliente</span></div>
    <div><b>Linee di credito</b><span>Per il circolante, gli investimenti e i picchi di spesa come le scadenze fiscali</span></div>
    <div><b>Oltre 50 istituti</b><span>Banche, gruppi finanziari e fondi, non solo i prodotti della sua banca</span></div>
    <div><b>Senza occupare il fido</b><span>La liquidità arriva senza toccare le linee che avete già</span></div>
    <div><b>La pratica la seguiamo noi</b><span>Documenti e istruttoria li gestiamo noi, lei arriva solo alla firma</span></div>
    <div><b>Solo a successo</b><span>Il compenso arriva solo quando i fondi sono sul conto</span></div>
  </div>
  <p class="idea">{{IDEA}}</p>
</div></section>

<section data-i="3" aria-label="Come funziona"><div class="s">
  <div class="eyebrow">Come funziona</div>
  <h2>Dalla prima call alla firma</h2>
  <div class="wk">
    <div><i>1</i><b>L'esigenza</b><span>Una prima call per capire quanta liquidità serve, per cosa e in che tempi.</span></div>
    <div><i>2</i><b>L'analisi</b><span>In 2 o 3 giorni studiamo la pratica e confrontiamo le offerte di oltre 50 istituti.</span></div>
    <div><i>3</i><b>La firma</b><span>Di solito chiudiamo tra i 7 e i 10 giorni lavorativi, e lei firma con l'istituto scelto.</span></div>
  </div>
  <p class="band">Fatturare non vuol dire incassare. Chi incassa a 90 giorni e paga i fornitori a 30, in mezzo ci mette i propri soldi. Noi aiutiamo a liberarli <b>senza occupare il fido</b>.</p>
</div></section>

<section data-i="4" aria-label="Perché Hermes"><div class="s">
  <div class="eyebrow">Perché Hermes</div>
  <h2>Consulenti del credito indipendenti</h2>
  <div class="lg pf">
    <div><b>Oltre 50</b><span>istituti bancari e partner finanziari</span></div>
    <div><b>2 o 3 giorni</b><span>per analizzare la pratica</span></div>
    <div><b>Da 7 a 10</b><span>giorni lavorativi per chiudere</span></div>
    <div><b>Solo a successo</b><span>paga quando i fondi sono sul conto</span></div>
  </div>
  <p class="lgn">Non vendiamo prodotti nostri. Confrontiamo per lei le offerte del mercato e portiamo la pratica fino alla firma.</p>
</div></section>
''',
 'Una breve call per capire quanta liquidità potreste liberare, e da quali istituti.')

make('genitori', 'Genitori.it', 'genitori-logo.svg', 'Genitori.it, il progetto formativo del Moige',
 '--red:#ae1022;--slate:#14133b;--ink:#1f1d33;--mute:#62607a;--line:#e3e1ea;--card:#f5f4f8;--bg:#fff;--glow:rgba(174,16,34,.07)',
 '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap" rel="stylesheet">', 'Montserrat',
 'Una pagina preparata per {{PREP_ATTR}} su come un percorso sulla genitorialità può entrare nel piano formativo.',
 '<div class="r gv" aria-hidden="true"><img src="../assets/genitori-o.svg" alt=""><div class="bd"><span>Ente accreditato dal Ministero dell\'Istruzione e del Merito</span><span>Parental coaching certificato ICF</span><span>Oltre trent\'anni con le famiglie</span></div></div>',
 '.gv{background:radial-gradient(110% 80% at 80% 0%,#f8eef0 0%,#fff 62%);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:34px;padding:48px 48px 84px}'
 '.gv img{width:230px;height:auto}.gv .bd{display:grid;gap:10px;width:100%;max-width:420px}.gv .bd span{background:#fff;border:1px solid var(--line);border-left:4px solid var(--red);border-radius:0 8px 8px 0;padding:12px 16px;font-size:17px;font-weight:600;color:var(--slate);line-height:1.3}'
 'html.phone .gv{flex-direction:row;gap:14px;padding:10px 16px}html.phone .gv img{width:70px;flex:none}html.phone .gv .bd{gap:5px}html.phone .gv .bd span{font-size:11.5px;padding:5px 9px}'
 '@media (max-height:700px){html.phone .gv img{width:52px}html.phone .gv .bd span{font-size:10.5px;padding:3px 7px}}',
 '''<section data-i="2" aria-label="Cosa portiamo"><div class="s">
  <div class="eyebrow">Cosa portiamo</div>
  <h2>Un percorso formativo per i genitori di {{COMPANY}}</h2>
  <div class="mk">
    <div><b>Genitorialità consapevole</b><span>Incontri su come si cresce un figlio oggi, dall'infanzia all'adolescenza</span></div>
    <div><b>Parental coaching</b><span>Coaching individuale con professionisti certificati ICF</span></div>
    <div><b>Figli adolescenti</b><span>Un percorso per i genitori di figli dai 12 ai 18 anni</span></div>
    <div><b>Nel piano formativo</b><span>Si rendiconta come la formazione sulle soft skill</span></div>
    <div><b>Partecipazione misurata</b><span>I dati di partecipazione arrivano alla direzione risorse umane</span></div>
    <div><b>Ente accreditato</b><span>Il Moige è accreditato dal Ministero dell'Istruzione e del Merito</span></div>
  </div>
  <p class="idea">{{IDEA}}</p>
</div></section>

<section data-i="3" aria-label="Come funziona"><div class="s">
  <div class="eyebrow">Come funziona</div>
  <h2>Formazione, come le altre soft skill</h2>
  <div class="wk">
    <div><i>1</i><b>Il vostro piano</b><span>Con la direzione risorse umane vediamo dove il percorso entra nella formazione 2027.</span></div>
    <div><i>2</i><b>Il percorso</b><span>Incontri di genitorialità consapevole e parental coaching certificato ICF per chi in azienda è genitore.</span></div>
    <div><i>3</i><b>I risultati</b><span>La partecipazione è misurata e riportata alla direzione risorse umane.</span></div>
  </div>
  <p class="band">Un figlio che non dorme, un adolescente in difficoltà, e il giorno dopo il lavoro ne risente. Nel piano formativo ci sono leadership e lavoro in squadra, ma <b>quello che le persone si portano da casa resta fuori</b>.</p>
</div></section>

<section data-i="4" aria-label="Perché Genitori.it"><div class="s">
  <div class="eyebrow">Perché Genitori.it</div>
  <h2>Il progetto formativo del Moige</h2>
  <div class="lg pf">
    <div><b>Accreditato</b><span>dal Ministero dell'Istruzione e del Merito</span></div>
    <div><b>ICF</b><span>parental coaching certificato</span></div>
    <div><b>Oltre 30 anni</b><span>di lavoro del Moige con le famiglie</span></div>
    <div><b>Soft skill</b><span>si rendiconta come la formazione sulle soft skill</span></div>
  </div>
  <p class="lgn">Genitori.it è il progetto formativo del Moige, Movimento Italiano Genitori, con percorsi pensati per le aziende.</p>
</div></section>
''',
 'Una breve call per vedere come un percorso sulla genitorialità può entrare nel vostro piano formativo 2027.')
print('ok')
