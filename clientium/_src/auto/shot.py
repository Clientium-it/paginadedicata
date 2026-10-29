#!/usr/bin/env python3
"""shot.py: homepage screenshot + logo of a lead site, headless, never a visible window.
Usage: python3 shot.py <slug> <url>   -> assets/shots/<slug>.jpg (1200 px wide, 16:10), assets/leadlogos/<slug>.<ext>, prints JSON
Also exposes crawl(url, max_pages) for facts.py: homepage text + up to 4 buyer pages read in the same browser.
"""
import asyncio, json, os, re, sys, io, urllib.parse
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
ARGS = ['--disable-blink-features=AutomationControlled', '--no-sandbox']
STEALTH = "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});Object.defineProperty(navigator,'languages',{get:()=>['en-US','en']});"
CHALLENGE = re.compile(r'checking your browser|just a moment|verify(ing)? you are human|attention required|ddos protection|you have been blocked|'
                       r'access denied|enable javascript and cookies|are you a robot|captcha|unusual traffic|checking the site connection', re.I)
CONSENT = ['#onetrust-accept-btn-handler', '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll', '#CybotCookiebotDialogBodyButtonAccept',
           r"text=/^\s*(accept|accept all|accept all cookies|accept cookies|allow all|allow all cookies|i agree|got it|ok)\s*$/i",
           r"text=/^\s*(alle akzeptieren|akzeptieren|alles akzeptieren|zustimmen|einverstanden|aceptar|aceptar todo|aceptar todas|accepter|tout accepter|j'accepte|accetta|accetta tutto|accetto|alles accepteren|accepteren|akkoord)\s*$/i"]
KILL = """(()=>{const bl=((document.body&&document.body.innerText)||'').length;
const POP=/cookie|consent|gdpr|privacy|newsletter|subscribe/i;
const page=el=>el===document.documentElement||el===document.body||el.tagName==='MAIN'||!!el.querySelector('main,h1')||(bl>0&&(el.innerText||'').length>0.5*bl);
for(const el of document.querySelectorAll('body *')){try{if(!el.isConnected)continue;const s=getComputedStyle(el);
 if((s.position==='fixed'||s.position==='sticky')&&el.getBoundingClientRect().height>150&&!el.closest('nav,header')&&el.tagName!=='NAV'&&el.tagName!=='HEADER'&&!page(el)){
  const t=(el.innerText||'').trim();const dimmer=t.length<3&&!el.querySelector('img,video,canvas,picture,svg,iframe');
  if(dimmer||POP.test(t)||el.getAttribute('role')==='dialog'||el.getAttribute('aria-modal')==='true')el.remove();}}catch(e){}}
for(const el of document.querySelectorAll('body [id*=cookie i],body [class*=cookie i],body [id*=consent i],body [class*=consent i],body [class*=popup i],body [class*=modal i]')){try{if(el.isConnected&&el.getBoundingClientRect().height>60&&!page(el))el.remove();}catch(e){}}
if(document.body)document.body.style.overflow='auto';window.scrollTo(0,0);return 1;})()"""
INFO = """()=>{const o={imgs:[],svgs:[]};
for(const i of document.querySelectorAll('header img, nav img, a[href="/"] img, [class*=logo i] img, [class*=brand i] img')){if(i.naturalWidth>40)o.imgs.push({src:i.currentSrc||i.src,w:i.naturalWidth,h:i.naturalHeight,alt:i.alt||''})}
for(const s of document.querySelectorAll('header svg, nav svg, a[href="/"] svg, [class*=logo i] svg')){const r=s.getBoundingClientRect();if(r.width>40)o.svgs.push({w:r.width,h:r.height,html:s.outerHTML.slice(0,60000)})}
const og=document.querySelector('meta[property="og:image"]');o.og=og?og.content:'';o.title=document.title;return o}"""
TEXT = """()=>{const c=document.body.cloneNode(true);c.querySelectorAll('script,style,noscript,svg,nav,[aria-hidden=true]').forEach(e=>e.remove());return c.innerText}"""
LINKS = """()=>[...document.querySelectorAll('a[href]')].map(a=>[a.href,(a.innerText||'').trim().slice(0,60)])"""
BUYER = re.compile(r'about|story|pricing|price|plans|shipping|delivery|faq|help|reviews|testimonials|customers|clients|case|results|rewards|loyalty|subscribe|subscription|guarantee|why|chi-siamo|azienda|prezzi|servizi|casi|clienti|risultati|domande|referenze|settori|garanzia|soluzion|prodott|realizzazion|referenz|lavori', re.I)
SKIP = re.compile(r'login|signin|account|cart|checkout|privacy|terms|legal|cookie|careers|jobs|press|blog|news|#|mailto:|tel:|\.(pdf|jpg|png)$', re.I)

async def ev(pg, js, default):
    try: return await pg.evaluate(js)
    except Exception: return default

async def load(pg, u):
    """True when the page is loaded and not behind a bot wall."""
    try: await pg.goto(u, wait_until='networkidle', timeout=45000)
    except Exception:
        try: await pg.goto(u, wait_until='domcontentloaded', timeout=45000)
        except Exception as e: print('FAILED', u, str(e)[:120], file=sys.stderr); return False
    await pg.wait_for_timeout(2500)
    for n in range(9):
        title, text = await ev(pg, "()=>[document.title||'', ((document.body&&document.body.innerText)||'').slice(0,1600)]", ['', ''])
        if len(text) >= 1500 or not CHALLENGE.search(title + ' ' + text): return True
        await pg.wait_for_timeout(2500)
    return False

async def consent(pg):
    for sel in CONSENT:
        try:
            el = pg.locator(sel).first
            if await el.count() and await el.is_visible(): await el.click(timeout=1500); await pg.wait_for_timeout(600); return
        except Exception: pass

async def session(url, slug=None, max_pages=5, want_shot=True):
    out = {'home_url': url, 'pages': [], 'shot': '', 'logo': '', 'blocked': False}
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=ARGS, executable_path=os.environ.get("CHROMIUM_EXE") or None)
        ctx = await b.new_context(viewport={'width': 1280, 'height': 800}, device_scale_factor=2, user_agent=UA, ignore_https_errors=True, locale='en-US')
        await ctx.add_init_script(STEALTH)
        pg = await ctx.new_page()
        ok = await load(pg, url)
        if not ok:
            alt = url.replace('://www.', '://') if '://www.' in url else url.replace('://', '://www.')
            ok = await load(pg, alt)
        if not ok:
            out['blocked'] = True; await b.close(); return out
        await consent(pg)
        info = await ev(pg, INFO, {'imgs': [], 'svgs': [], 'og': ''})
        text = await ev(pg, TEXT, '')
        out['pages'].append({'url': pg.url, 'text': re.sub(r'\n{3,}', '\n\n', text or '')[:7000]})
        links = await ev(pg, LINKS, [])
        if want_shot and slug:
            await ev(pg, KILL, 0); await pg.wait_for_timeout(400)
            raw = await pg.screenshot(type='jpeg', quality=82, clip={'x': 0, 'y': 0, 'width': 1280, 'height': 800})
            try:
                from PIL import Image
                im = Image.open(io.BytesIO(raw)).convert('RGB')
                px = im.resize((40, 25)).getdata(); flat = len(set(px)) < 12
                if not flat:
                    im = im.resize((1200, 750)); d = os.path.join(ROOT, 'assets', 'shots'); os.makedirs(d, exist_ok=True)
                    im.save(os.path.join(d, slug + '.jpg'), quality=82); out['shot'] = slug + '.jpg'
            except ImportError:
                d = os.path.join(ROOT, 'assets', 'shots'); os.makedirs(d, exist_ok=True); open(os.path.join(d, slug + '.jpg'), 'wb').write(raw); out['shot'] = slug + '.jpg'
            out['logo'] = await save_logo(ctx, info, slug, url)
        # buyer pages
        host = urllib.parse.urlparse(pg.url).netloc.replace('www.', '')
        seen, picks = {pg.url.rstrip('/')}, []
        for href, label in links:
            h = href.split('#')[0].rstrip('/')
            if not h or h in seen or host not in urllib.parse.urlparse(h).netloc or SKIP.search(h): continue
            if BUYER.search(h) or BUYER.search(label): seen.add(h); picks.append(h)
            if len(picks) >= max_pages - 1: break
        for h in picks:
            if await load(pg, h):
                t = await ev(pg, TEXT, '')
                if t and len(t) > 400: out['pages'].append({'url': h, 'text': re.sub(r'\n{3,}', '\n\n', t)[:7000]})
        await b.close()
    return out

async def save_logo(ctx, info, slug, base):
    """largest inline svg, else widest header img with 'logo' in src or alt (>=120 px), else og:image if wide and small. Returns file name or ''."""
    d = os.path.join(ROOT, 'assets', 'leadlogos'); os.makedirs(d, exist_ok=True)
    svgs = sorted(info.get('svgs') or [], key=lambda s: -s['w'] * s['h'])
    svgs = [x for x in svgs if '<use' not in x['html'] and re.search(r'<(path|rect|circle|polygon|ellipse|text)\b', x['html'])]   # sprite references and empty shells do not render standalone
    if svgs and svgs[0]['w'] >= 80:
        open(os.path.join(d, slug + '.svg'), 'w', encoding='utf-8').write(svgs[0]['html']); return slug + '.svg'
    imgs = [i for i in (info.get('imgs') or []) if i['w'] >= 120 and re.search(r'logo', (i['src'] + ' ' + i['alt']), re.I)]
    imgs.sort(key=lambda i: -i['w'])
    cands = [i['src'] for i in imgs] + ([info['og']] if info.get('og') else [])
    for src in cands[:3]:
        try:
            r = await ctx.request.get(urllib.parse.urljoin(base, src), timeout=15000)
            if r.status != 200: continue
            body = await r.body(); ct = r.headers.get('content-type', '')
            ext = 'svg' if 'svg' in ct or src.lower().endswith('.svg') else 'png' if 'png' in ct else 'jpg' if 'jp' in ct else 'webp' if 'webp' in ct else ''
            if not ext or len(body) < 300: continue
            if ext != 'svg':
                try:
                    from PIL import Image
                    im = Image.open(io.BytesIO(body)).convert('RGBA'); w, h = im.size
                    if w < 120 or (src == info.get('og') and (h > w or w > 1200)): continue
                    px = [p for p in im.getdata() if p[3] > 20]
                    if px and sum(1 for p in px if p[0] > 235 and p[1] > 235 and p[2] > 235) / len(px) > 0.85: continue   # white logo, falls back to text
                    bbox = im.getbbox(); im = im.crop(bbox) if bbox else im
                    im.save(os.path.join(d, slug + '.png')); return slug + '.png'
                except ImportError: pass
            open(os.path.join(d, slug + '.' + ext), 'wb').write(body); return slug + '.' + ext
        except Exception: continue
    return ''

if __name__ == '__main__':
    slug, url = sys.argv[1], sys.argv[2]
    r = asyncio.run(session(url, slug, max_pages=1))
    print(json.dumps({k: v for k, v in r.items() if k != 'pages'}))
