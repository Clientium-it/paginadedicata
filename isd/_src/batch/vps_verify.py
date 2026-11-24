import asyncio,json,re,unicodedata
from playwright.async_api import async_playwright
J=json.load(open('/tmp/cl/isdb_vq_in.json'))
def n(s): s=unicodedata.normalize('NFKC',s).replace('’',"'").lower(); return re.sub(r'\s+',' ',s).strip()
async def one(br,j,sem,res):
  async with sem:
    ctx=await br.new_context(ignore_https_errors=True,user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36',locale='it-IT')
    out={q:[] for q in j['q'] if q}
    for u in j['urls']:
      if all(out.values()) : break
      try:
        p=await ctx.new_page();rr=await p.goto(u,timeout=25000,wait_until='domcontentloaded');await p.wait_for_timeout(2000)
        if rr and rr.status<400:
          t=n(await p.evaluate('document.body.innerText'))+' '+n(await p.content())
          for q in out:
            if not out[q] and n(q) in t: out[q]=[p.url]
        await p.close()
      except Exception as e: pass
    res[j['slug']]=out;await ctx.close()
async def main():
  res={}
  async with async_playwright() as pw:
    br=await pw.chromium.launch();sem=asyncio.Semaphore(6)
    await asyncio.gather(*[one(br,j,sem,res) for j in J])
  json.dump(res,open('/tmp/cl/isdb_vq_out.json','w'),ensure_ascii=False,indent=1)
asyncio.run(main())
