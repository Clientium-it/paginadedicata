# usage on VPS: python3 vps_verify2.py IN.json OUT.json  (jobs: [{slug, urls, q:[...]}])
import asyncio,json,re,sys,unicodedata,html
from playwright.async_api import async_playwright
IN,OUT=sys.argv[1],sys.argv[2]; J=json.load(open(IN))
def fixmoj(s):
  try: return s.encode('latin1').decode('utf8')
  except Exception: return s
def n(s): s=unicodedata.normalize('NFKC',fixmoj(s)).replace('’',"'").replace('‘',"'").replace('“','"').replace('”','"').lower(); return re.sub(r'[\s ]+',' ',s).strip()
def sq(s): return n(s).replace(' ','')
def items(q): return [x.strip() for x in re.split(r',|\|',q) if x.strip()]
async def one(br,j,sem,res):
  async with sem:
    ctx=await br.new_context(ignore_https_errors=True,user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36',locale='it-IT')
    out={q:None for q in j['q']}
    for u in j['urls']:
      if all(out.values()): break
      try:
        p=await ctx.new_page();r=await p.goto(u,timeout=25000,wait_until='domcontentloaded');await p.wait_for_timeout(2200)
        if r and r.status<400:
          t=await p.evaluate('document.body.innerText');h=html.unescape(re.sub(r'<[^>]+>',' ',await p.content()))
          N=n(t)+' '+n(h);S=N.replace(' ','')
          for q in out:
            if out[q]: continue
            if n(q) in N: out[q]=['exact',p.url]
            elif sq(q) in S: out[q]=['space',p.url]
            else:
              it=items(q)
              if len(it)>=3 and all(len(x.split())<=6 for x in it) and all(sq(x) in S for x in it): out[q]=['items',p.url]
        await p.close()
      except Exception: pass
    res[j['slug']]=out;await ctx.close()
    if len(res)%50==0: json.dump(res,open(OUT,'w'),ensure_ascii=False)
async def main():
  res={}
  async with async_playwright() as pw:
    br=await pw.chromium.launch();sem=asyncio.Semaphore(12)
    await asyncio.gather(*[one(br,j,sem,res) for j in J])
  json.dump(res,open(OUT,'w'),ensure_ascii=False,indent=1)
asyncio.run(main())
