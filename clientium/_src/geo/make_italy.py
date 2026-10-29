#!/usr/bin/env python3
"""make_italy.py: one time. openpolis limits_IT_regions.geojson (ISTAT, CC BY 4.0) -> italy_regions.json {region: svg path}, viewBox 0 0 1000 1160.
Usage: python3 make_italy.py <regions.geojson>"""
import json, math, os, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
K = math.cos(math.radians(42)); LON0, LON1, LAT0, LAT1 = 6.6, 18.6, 35.4, 47.15
W = 1000; S = W / ((LON1 - LON0) * K); H = round((LAT1 - LAT0) * S)
def xy(lon, lat): return ((lon - LON0) * K * S, (LAT1 - lat) * S)
def ring(pts, tol=0.35):
    out = []
    for lon, lat in pts:
        p = xy(lon, lat)
        if not out or abs(p[0] - out[-1][0]) + abs(p[1] - out[-1][1]) > tol: out.append(p)
    return out if len(out) > 3 else []
SHORT = {'Trentino-Alto Adige/Südtirol': 'Trentino-Alto Adige', "Valle d'Aosta/Vallée d'Aoste": "Valle d'Aosta", 'Friuli-Venezia Giulia': 'Friuli Venezia Giulia'}
res = {}
for f in d['features']:
    name = SHORT.get(f['properties']['reg_name'], f['properties']['reg_name']); g = f['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    parts = []
    for poly in polys:
        r = ring(poly[0])
        if r: parts.append('M' + 'L'.join(f"{x:.1f},{y:.1f}" for x, y in r) + 'Z')
    res[name] = ''.join(parts)
json.dump({'viewBox': f'0 0 {W} {H}', 'source': 'openpolis geojson-italy, ISTAT, CC BY 4.0', 'regions': res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'italy_regions.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('regions', len(res), 'bytes', os.path.getsize(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'italy_regions.json')), 'H', H)
