import re,unicodedata
CON={'e','di','del','della','delle','dei','&','de',"d'",'of','von','van'}
def subj(f,az=''):
  t=re.sub(r'^ho visto che\s+','',f.strip()).split();out=[]
  if t and t[0][0].islower() and az and slug(az).startswith(slug(t[0])) and len(t[0])>=3: return t[0]
  for i,w in enumerate(t):
    if w[0].isupper() or w[0].isdigit(): out.append(w)
    elif w in CON and i+1<len(t) and t[i+1][0].isupper() and out: out.append(w)
    else: break
  return ' '.join(out).rstrip(',')
LEG=r'\b(s\.?\s?p\.?\s?a\.?|s\.?r\.?l\.?|soc\.? unipersonale|sarl|snc|s\.a\.s\.?|societa\'? cooperativa|soc\.? coop\.?)\b\.?'
def clean(a):
  a=re.split(r'\s[-|]\s|\s\(',a)[0]; a=re.sub(LEG,'',a,flags=re.I); a=re.sub(r'\s+',' ',a).strip(' .,-')
  if a.isupper() and len(a)>4: a=' '.join(w if len(w)<=3 else w.capitalize() for w in a.split())
  return a
def slug(s): s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower().replace('&','-'); return re.sub(r'[^a-z0-9]+','-',s).strip('-')
def fname(fn):
  fn=(fn or '').strip(); return ' '.join(w.capitalize() for w in fn.split()) if (fn.isupper() or fn.islower()) else fn
def urls_for(u,dom=None):
  from urllib.parse import urlparse
  n=urlparse(u);root=f'{n.scheme}://{n.netloc}';alt=u.replace('://www.','://') if '://www.' in u else u.replace('://','://www.',1)
  L=[u,alt,root+'/',root+'/chi-siamo',root+'/contatti',root+'/azienda',root+'/en/contacts']
  if dom: L+= [f'https://www.{dom}/']
  return list(dict.fromkeys(L))
def quotes(q): return list(dict.fromkeys(x.strip() for x in q.split('||') if x.strip()))
