import asyncio,json,os,sys,re
from playwright.async_api import async_playwright
OUT='/tmp/cl/isd_logos';os.makedirs(OUT,exist_ok=True)
rows=[l.split() for l in open('/tmp/cl/isd_logo_in.txt') if l.strip()]
JS=r"""()=>{
const cand=[...document.querySelectorAll('header img, header svg, [class*=header] img, [class*=header] svg, a[href="/"] img, a[href="./"] img, img, svg')];
const ok=e=>{const r=e.getBoundingClientRect();return r.width>=40&&r.height>=12&&r.top<300&&r.width<700};
const sc=e=>{const s=((e.getAttribute('src')||'')+' '+(e.getAttribute('alt')||'')+' '+(e.getAttribute('class')||'')+' '+(e.id||'')+' '+((e.parentElement&&e.parentElement.className&&e.parentElement.className.baseVal===undefined)?e.parentElement.className:'')+' '+(e.closest('a')?.getAttribute('href')||'')).toLowerCase();let v=0;if(s.includes('logo'))v+=5;if(e.closest('header,[class*=header],nav'))v+=2;const h=e.closest('a')?.getAttribute('href')||'';if(h=='/'||/^https?:\/\/[^/]+\/?(it|en)?\/?$/.test(h))v+=3;return v};
let best=null,bv=0;for(const e of cand){if(!ok(e))continue;const v=sc(e);if(v>bv){bv=v;best=e}}
if(!best||bv<5)return null;const r=best.getBoundingClientRect();
return {tag:best.tagName.toLowerCase(),src:best.currentSrc||best.getAttribute('src')||'',svg:best.tagName.toLowerCase()=='svg'?best.outerHTML:'',w:r.width,h:r.height,score:bv}}"""
async def one(br,slug,url,name,sem,res):
  async with sem:
    try:
      ctx=await br.new_context(ignore_https_errors=True,user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36',viewport={'width':1440,'height':900},locale='it-IT')
      p=await ctx.new_page();await p.goto(url,timeout=30000,wait_until='domcontentloaded');await p.wait_for_timeout(2500)
      r=await p.evaluate(JS)
      if r:
        if r['svg']: open(f'{OUT}/{slug}.svg','w').write(r['svg']);r['file']=f'{slug}.svg'
        elif r['src'] and not r['src'].startswith('data:'):
          resp=await ctx.request.get(r['src'],timeout=20000)
          ct=resp.headers.get('content-type','');ext='svg' if 'svg' in ct or r['src'].split('?')[0].endswith('.svg') else ('png' if 'png' in ct else 'webp' if 'webp' in ct else 'jpg' if 'jpe' in ct else 'png')
          if resp.ok: open(f'{OUT}/{slug}.{ext}','wb').write(await resp.body());r['file']=f'{slug}.{ext}'
        r.pop('svg',None)
      res[slug]=r or {}
      await ctx.close()
    except Exception as e: res[slug]={'err':str(e)[:120]}
async def main():
  res={}
  async with async_playwright() as pw:
    br=await pw.chromium.launch();sem=asyncio.Semaphore(8)
    await asyncio.gather(*[one(br,s,u,n,sem,res) for s,u,n in rows])
  json.dump(res,open('/tmp/cl/isd_logos.json','w'),indent=1)
  print(len(res),sum(1 for v in res.values() if v.get('file')))
asyncio.run(main())
