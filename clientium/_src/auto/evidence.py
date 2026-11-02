#!/usr/bin/env python3
"""evidence.py: every claim about the lead on the page must come from the lead's own site.
Usage: python3 auto/evidence.py specs/<slug>.json [...]   (run from _src)
Fetches each evidence url, checks the quote is on that page (whitespace, apostrophes, case normalised).
Exit 1 if any quote is missing: that claim does not go on the page. Few fetches per lead; at batch volume run it on the VPS.
"""
import html, json, re, subprocess, sys
def norm(s):
    s = html.unescape(s).replace('’', "'").replace('‘', "'").replace(' ', ' ')
    return re.sub(r'\s+', ' ', s).strip().lower()
def page(url, cache={}):
    if url not in cache:
        r = subprocess.run(['curl', '-sL', '--max-time', '40', '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Chrome/124 Safari/537.36', '-H', 'Accept-Language: it-IT,it;q=0.9', url], capture_output=True)
        t = r.stdout.decode('utf-8', 'ignore')
        t = re.sub(r'(?s)<(script|style)\b.*?</\1>', ' ', t); t = re.sub(r'<[^>]+>', ' ', t)
        cache[url] = norm(t)
    return cache[url]
bad = 0
for p in sys.argv[1:]:
    sp = json.load(open(p, encoding='utf-8'))
    ev = sp.get('evidence') or []
    if (sp.get('cover_note') or sp.get('market_note')) and not ev:
        print('NO EVIDENCE', sp['slug']); bad += 1
    for e in ev:
        ok = norm(e['quote']) in page(e['url'])
        bad += not ok
        print('OK ' if ok else 'MISSING', sp['slug'], '|', e['claim'], '|', e['url'])
sys.exit(1 if bad else 0)
