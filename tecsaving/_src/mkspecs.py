"""mkspecs.py <batch.json> <workdir>: batch file (slug, company, first, last, cover_note, idea, evidence) -> <workdir>/specs/<slug>.json. Only mechanical fixes: missing accent on può, name casing."""
import json,re,sys,os
m=json.load(open(sys.argv[1])); S=sys.argv[2]; os.makedirs(f'{S}/specs',exist_ok=True)
over=json.load(open(f'{S}/idea_override.json')) if os.path.exists(f'{S}/idea_override.json') else {}
def nm(s):
    s=(s or '').strip()
    return ' '.join(w.capitalize() if w.isupper() or w.islower() else w for w in s.split())
fixed=0
NONAME={'itib'}
for r in m:
    idea=re.sub(r"\b[Pp]uo'?(?=\s)", 'può', r['idea'].strip())
    fixed+=idea!=r['idea'].strip()
    if r['slug'] in over: idea=over[r['slug']]
    f,l=nm(r['first']),nm(r['last'])
    # company pages and initial-only surnames: the page names only the company
    real=len(f)>2 and len(l)>2 and f.lower()!=l.lower() and f.lower() not in r['company'].lower().replace('.',' ').split() and r['slug'] not in NONAME
    sp={'slug':r['slug'],'company':r['company'],'first':f,'full_name':(f+' '+l) if real else '','cover_note':r['cover_note'],'idea':idea,'evidence':r['evidence']}
    json.dump(sp,open(f"{S}/specs/{r['slug']}.json",'w'),ensure_ascii=False)
print(len(m),'specs,',fixed,'accent fixes,',len(over),'overrides')
