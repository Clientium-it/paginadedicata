"""shared helpers: env, db, HeyReach, alerts"""
import json, os, sys, time, urllib.request, urllib.error
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); ROOT = os.path.dirname(SRC)
B = json.load(open(os.path.join(SRC, 'brand.json'), encoding='utf-8'))
CLIENT = B['client']
HR = 'https://api.heyreach.io/api/public'

def load_env():
    for p in (os.path.join(ROOT, '.env'), os.path.expanduser('~/.env')):
        if os.path.exists(p):
            for ln in open(p, encoding='utf-8'):
                ln = ln.split('#')[0].strip()
                if '=' in ln: k, v = ln.split('=', 1); os.environ.setdefault(k.strip(), v.strip())
load_env()

def now(): return time.strftime('%Y-%m-%d %H:%M:%S')
def say(*a): print(now(), *a, flush=True)

def alert(text):
    say('ALERT', text)
    u = os.environ.get('ALERT_WEBHOOK')
    if u:
        try: urllib.request.urlopen(urllib.request.Request(u, json.dumps({'text': f'[{CLIENT}] {text}'}).encode(), {'Content-Type': 'application/json'}), timeout=15)
        except Exception as e: say('alert failed', e)

def db():
    """psycopg2 connection or None (then poll.py keeps its JSON state only)."""
    url = os.environ.get('DATABASE_URL')
    if not url: return None
    import psycopg2; c = psycopg2.connect(url); c.autocommit = True; return c

def hr(path, body=None, method='POST', key=None):
    key = key or os.environ['HEYREACH_API_KEY']
    for i in range(4):
        req = urllib.request.Request(HR + path, json.dumps(body or {}).encode() if method != 'GET' else None,
                                     {'X-API-KEY': key, 'Content-Type': 'application/json', 'Accept': 'application/json'}, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                t = r.read().decode(); return json.loads(t) if t.strip() else {}
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < 3: time.sleep(20 * (i + 1)); continue
            raise RuntimeError(f'HeyReach {e.code} on {path}: {e.read().decode()[:200]}')
    raise RuntimeError('HeyReach retries exhausted')

def hr_pages(path, body, limit=100):
    off = 0
    while True:
        d = hr(path, dict(body, offset=off, limit=limit)); items = d.get('items') or []
        for it in items: yield it
        if len(items) < limit: return
        off += limit

def norm_url(u):
    import urllib.parse
    u = urllib.parse.unquote((u or '').strip()).lower().rstrip('/')
    u = u.replace('http://', 'https://').replace('https://linkedin.com', 'https://www.linkedin.com')
    return u.split('?')[0]

def slugify(s, n=40):
    import re, unicodedata
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return s[:n].rstrip('-')
