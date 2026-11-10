"""report_svg.py: writes assets/report.svg, the sample report chart redrawn as vector from the values in takeflight.it home_takeflight-1.jpg (same 12 axes and percentages, no illustration)."""
import math, os, sys
AX = [('MOTIVAZIONE TOTALE',64,1),('M. Estrinseca',67,0),('M. Intrinseca',55,0),('AUTOCONSAPEVOLEZZA',52,1),('Autostima',73,0),('Capacità di adattamento',53,0),
      ('APERTURA MENTALE',56,1),('Presenza di stereotipi',39,0),('Curiosità',52,0),('ENERGIA',55,1),('Stile di vita',57,0),('Risorse personali',51,0)]
W,H,CX,CY,R = 960,540,480,272,188
def pt(i,r): a=math.radians(i*30); return CX+r*math.sin(a), CY-r*math.cos(a)
def poly(r): return ' '.join('%.1f,%.1f'%pt(i,r) for i in range(12))
o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Helvetica Neue,Helvetica,Arial,sans-serif">','<rect width="100%" height="100%" fill="#fff"/>']
for k in range(1,6): o.append(f'<polygon points="{poly(R*k/5)}" fill="{"#f6f9fc" if k%2 else "#fff"}" stroke="#dfe5ec" stroke-width="1.2"/>')
for i in range(12): x,y=pt(i,R); o.append(f'<line x1="{CX}" y1="{CY}" x2="{x:.1f}" y2="{y:.1f}" stroke="#dfe5ec" stroke-width="1.2"/>')
P=[pt(i,R*v/100) for i,(_,v,_) in enumerate(AX)]
o.append('<polygon points="%s" fill="rgba(28,174,230,.10)" stroke="#1caee6" stroke-width="5" stroke-linejoin="round"/>'%' '.join('%.1f,%.1f'%p for p in P))
for (x,y) in P: o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#1caee6" stroke="#fff" stroke-width="2.5"/>')
for i,((lab,v,cap),(x,y)) in enumerate(zip(AX,P)):
    a=math.radians(i*30); s,c=math.sin(a),-math.cos(a)
    vx,vy=x+s*30,y+c*30+7
    o.append(f'<text x="{vx:.1f}" y="{vy:.1f}" text-anchor="middle" font-size="22" font-weight="700" fill="#24323f" stroke="#fff" stroke-width="5" paint-order="stroke">{v}%</text>')
    lx,ly=pt(i,R+22); anc='middle' if abs(s)<.2 else ('start' if s>0 else 'end'); ly+= 6+ (c*8 if abs(s)<.2 else 0)
    o.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anc}" font-size="{20 if cap else 21}" font-weight="{700 if cap else 500}" letter-spacing="{.6 if cap else 0}" fill="#3c4a57">{lab}</text>')
o.append('</svg>')
# rough viewBox; run fit_viewbox() below (Playwright getBBox) for the exact one
xs,ys=[],[]
for i,(lab,v,cap) in enumerate(AX):
    a=math.radians(i*30); s=math.sin(a); lx,ly=pt(i,R+22); w=len(lab)*(20 if cap else 21)*(0.62 if cap else 0.55)
    x0,x1=(lx-w/2,lx+w/2) if abs(s)<.2 else ((lx,lx+w) if s>0 else (lx-w,lx)); xs+=[x0,x1]; ys+=[ly-24,ly+12]
m=10; vb=f'{min(xs)-m:.0f} {min(ys)-m:.0f} {max(xs)-min(xs)+2*m:.0f} {max(ys)-min(ys)+2*m:.0f}'
o[0]=o[0].replace(f'viewBox="0 0 {W} {H}"',f'viewBox="{vb}"'); o[1]='<rect x="-2000" y="-2000" width="5000" height="5000" fill="#fff"/>'
out=sys.argv[1] if len(sys.argv)>1 else os.path.join(os.path.dirname(__file__),'..','assets','report.svg')
open(out,'w',encoding='utf-8').write('\n'.join(o)); print('wrote',out)

def fit_viewbox(path, margin=14):
    import asyncio, re
    from playwright.async_api import async_playwright
    EXE='/Users/stevenkoja5/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell'
    async def m():
        async with async_playwright() as p:
            b=await p.chromium.launch(executable_path=EXE); pg=await b.new_page(); await pg.goto('file://'+os.path.abspath(path))
            r=await pg.evaluate("(()=>{let a=1e9,c=1e9,e=-1e9,f=-1e9;for(const n of document.querySelectorAll('text,polygon')){const q=n.getBBox();a=Math.min(a,q.x);c=Math.min(c,q.y);e=Math.max(e,q.x+q.width);f=Math.max(f,q.y+q.height)}return [a,c,e,f]})()")
            await b.close(); return r
    a,c,e,f=asyncio.run(m()); t=open(path).read()
    open(path,'w').write(re.sub(r'viewBox="[^"]*"',f'viewBox="{a-margin:.0f} {c-margin:.0f} {e-a+2*margin:.0f} {f-c+2*margin:.0f}"',t,1))
if __name__=='__main__':
    try: fit_viewbox(out)
    except ImportError: print('playwright missing: viewBox left rough')
