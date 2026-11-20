#!/usr/bin/env python3
"""Dynamics People v2 pages (Vimec style, LinkedIn reply CTA, no calendar).
Usage: python3 build_v2.py specs_v2.json --out <folder outside the repo>
Spec: {slug, company, full_name, fact, imm, angle, close, logo (path or ''), evidence:{source_url, quote}}.
Refuses to write inside ~/paginadedicata."""
import html,json,os,re,shutil,sys
HERE=os.path.dirname(os.path.abspath(__file__))
TPL=open(os.path.join(HERE,'template_v2.html'),encoding='utf-8').read()
BAD=re.compile(r'[—–:!;]| - |factorial|leader|eccellenz|piattaforma',re.I)
E=lambda s:html.escape(s,quote=False);A=lambda s:html.escape(s,quote=True)
def render(sp,logo_rel):
    c=sp['company'].strip();full=sp['full_name'].strip()
    if not sp.get('evidence',{}).get('quote') or not sp['evidence'].get('source_url'): raise ValueError('no evidence')
    for k in ('fact','imm','angle','close'):
        if BAD.search(sp[k]) or re.search(r'\bDynamics\b',sp[k]): raise ValueError(f'copy rule {k}: {sp[k]!r}')
    if logo_rel:
        chip=f'<span class="plogo"><img src="{logo_rel}" alt="{A(c)}"></span>';big=f'<img src="{logo_rel}" alt="{A(c)}">'
    else:
        chip=f'<span class="pname">{E(c)}</span>';big=f'<span class="pname">{E(c)}</span>'
    v={'COMPANY':E(c),'COMPANY_ATTR':A(c),'FULL':E(full),'PREP_ATTR':A(f'{full} di {c}'),'CHIP':chip,'BIG':big,
       'FACT':E(sp['fact']),'IMM':E(sp['imm']),'ANGLE':E(sp['angle']),'CLOSE':E(sp['close'])}
    return re.sub(r'\{\{(\w+)\}\}',lambda m:v[m.group(1)],TPL)
def main():
    a=sys.argv[1:];i=a.index('--out');out=os.path.abspath(os.path.expanduser(a[i+1]))
    if os.path.realpath(out).startswith(os.path.realpath(os.path.expanduser('~/paginadedicata'))): sys.exit('out is inside the published repo: refused')
    specs=json.load(open(a[0]));done=bad=0
    for sp in specs:
        lr=''
        if sp.get('logo'):
            ext=sp['logo'].rsplit('.',1)[1];d=f"{out}/assets/leads/{sp['slug']}";os.makedirs(d,exist_ok=True)
            shutil.copy(sp['logo'],f'{d}/logo.{ext}');lr=f"../assets/leads/{sp['slug']}/logo.{ext}"
        try: page=render(sp,lr)
        except ValueError as e: print('REFUSED',sp['slug'],e);bad+=1;continue
        os.makedirs(f"{out}/{sp['slug']}",exist_ok=True);open(f"{out}/{sp['slug']}/index.html",'w',encoding='utf-8').write(page);done+=1
    print(done,'pages |',bad,'refused')
if __name__=='__main__':main()
