"""og_check.py <out> (serve <out> as /tecsaving/ on 127.0.0.1:8766 first) [slugs...]: per page, OG image 1200x630 from the cover, plus overflow and JS error checks on 360x640 phone and 1440x900 desktop."""
import asyncio, json, os, re, sys
from playwright.async_api import async_playwright
EXE='/Users/stevenkoja5/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell'
OUT=sys.argv[1]; B='http://127.0.0.1:8766/tecsaving/'
slugs=sys.argv[2:] or sorted(d for d in os.listdir(OUT) if os.path.exists(f'{OUT}/{d}/index.html'))
OV="Math.max(0,...[...document.querySelectorAll('.slides>section .s')].map(s=>s.scrollHeight-s.clientHeight))"
WIDE="Math.max(0,...[...document.querySelectorAll('.slides>section .s')].map(s=>s.scrollWidth-s.clientWidth))"
async def page(b, slug, vp, mobile, og=False):
    kw=dict(viewport=vp, timezone_id='Europe/Rome')
    if mobile: kw.update(device_scale_factor=2,is_mobile=True,has_touch=True)
    c=await b.new_context(**kw); pg=await c.new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)[:80]))
    await pg.route(re.compile(r'clarity\.ms'),lambda r:r.fulfill(status=204,body=''))
    await pg.goto(B+slug+'/',wait_until='networkidle'); await pg.evaluate('document.fonts.ready')
    r={'ov':await pg.evaluate(OV),'wide':await pg.evaluate(WIDE),'errs':errs}
    if og:
        os.makedirs(f'{OUT}/assets/og',exist_ok=True)
        await pg.add_style_tag(content='body>*:not(.stage),.pnav{display:none!important}.slides,.stage{scrollbar-width:none!important}.slides::-webkit-scrollbar{display:none}')
        await pg.wait_for_timeout(150)
        await pg.screenshot(path=f'{OUT}/assets/og/{slug}.jpg',type='jpeg',quality=82)
    await c.close(); return r
async def m():
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True,executable_path=EXE); res={}
        sem=asyncio.Semaphore(4)
        async def one(s):
            async with sem:
                res[s]={'og':await page(b,s,{'width':1200,'height':630},False,True),
                        'phone':await page(b,s,{'width':360,'height':640},True),
                        'desk':await page(b,s,{'width':1440,'height':900},False)}
        await asyncio.gather(*(one(s) for s in slugs))
        await b.close()
    json.dump(res,open(OUT+'/../og_check.json','w'),indent=0)
    bad={s:v for s,v in res.items() if any(x['ov']>2 or x['wide']>2 or x['errs'] for x in v.values())}
    print(len(res),'pages,',len(bad),'with issues'); [print(s,v) for s,v in list(bad.items())[:30]]
asyncio.run(m())
