"""simplify_map.py <in.json> <out.json> <tol>: Douglas-Peucker on every ring of the Italy regions, 1 decimal."""
import json,re,sys
def dp(P,tol):
    if len(P)<3: return P
    (x1,y1),(x2,y2)=P[0],P[-1]; dx,dy=x2-x1,y2-y1; L=(dx*dx+dy*dy)**.5
    i,m=0,-1
    for k in range(1,len(P)-1):
        x,y=P[k]; dd=abs(dy*x-dx*y+x2*y1-y2*x1)/L if L>1e-9 else ((x-x1)**2+(y-y1)**2)**.5
        if dd>m: i,m=k,dd
    return dp(P[:i+1],tol)[:-1]+dp(P[i:],tol) if m>tol else [P[0],P[-1]]
def ring(pts,tol):
    # closed ring: split at the point farthest from the start, simplify both halves
    x0,y0=pts[0]; far=max(range(len(pts)),key=lambda k:(pts[k][0]-x0)**2+(pts[k][1]-y0)**2)
    if far==0: return pts
    a=dp(pts[:far+1],tol); b=dp(pts[far:]+[pts[0]],tol)
    return a[:-1]+b[:-1]
def simp(d,tol):
    out=[]
    for sub in re.findall(r'M[^M]*',d):
        pts=[tuple(map(float,p)) for p in re.findall(r'(-?[\d.]+)[ ,](-?[\d.]+)',sub)]
        q=ring(pts,tol) if len(pts)>3 else pts
        if len(q)<3: continue
        out.append('M'+'L'.join(f'{round(x,1):g},{round(y,1):g}' for x,y in q)+'Z')
    return ''.join(out)
g=json.load(open(sys.argv[1])); tol=float(sys.argv[3])
s={'viewBox':g['viewBox'],'source':g['source'],'regions':{k:simp(v,tol) for k,v in g['regions'].items()}}
json.dump(s,open(sys.argv[2],'w'),ensure_ascii=False); print(sum(len(v) for v in s['regions'].values()),'bytes of path data')
