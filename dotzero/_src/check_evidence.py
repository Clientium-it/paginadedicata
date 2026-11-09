#!/usr/bin/env python3
"""Fetch each evidence URL and check that the quote is on the page. Exit 1 on any miss."""
import html, json, re, subprocess, sys
UA = 'Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/126 Safari/537.36'
def text(u):
    r = subprocess.run(['curl', '-sL', '--max-time', '30', '-A', UA, u], capture_output=True).stdout.decode('utf8', 'ignore')
    r = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', r, flags=re.S); r = html.unescape(re.sub(r'<[^>]+>', ' ', r))
    return re.sub(r'\s+', ' ', r).casefold()
bad = 0; cache = {}
for p in sys.argv[1:]:
    for e in json.load(open(p, encoding='utf-8'))['evidence']:
        t = cache.setdefault(e['url'], text(e['url'])); ok = re.sub(r'\s+', ' ', e['quote']).casefold() in t
        print('OK ' if ok else 'MISS', p.split('/')[-1], '|', e['quote'][:70]); bad += not ok
sys.exit(1 if bad else 0)
