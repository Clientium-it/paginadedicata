#!/usr/bin/env python3
"""track.py (every 4 h): deck_events -> deck_sessions, Calendly invitees -> bookings (match, stop, tag, write back).
Usage: python3 track.py [--sample events.jsonl]  (sample mode aggregates a file and prints sessions, no DB, no APIs)
"""
import json, os, sys, time, urllib.request, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import *
INTERNAL_COUNTRIES = set(B.get('internal_countries') or []); INTERNAL_TZ = set(B.get('internal_tz') or [])
DC = ('amazon', 'google', 'microsoft', 'digitalocean', 'hetzner', 'ovh', 'linode', 'akamai', 'cloudflare', 'oracle', 'alibaba', 'facebook', 'meta', 'linkedin', 'twitter', 'apple', 'datacamp', 'm247', 'leaseweb', 'choopa', 'vultr')
PRIV = os.path.join(ROOT, '_private'); os.makedirs(PRIV, exist_ok=True); GEO = os.path.join(PRIV, 'geo.json')

def aggregate(events):
    """pure. events: dicts {sid, slug, ev, t(ms), data{max,total,w,tz,phone,...}, ip, ua, country, city, org, tz}. returns sid -> deck_sessions row"""
    S = {}
    for e in sorted(events, key=lambda e: e['t']):
        d = e.get('data') or {}
        s = S.setdefault(e['sid'], {'slug': e['slug'], 'sid': e['sid'], 'first': e['t'], 'last': e['t'], 'max_slide': 1, 'total_slides': d.get('total'), 'pings': 0, 'videos': 0, 'book_clicks': 0,
                                     'width': d.get('w'), 'tz': d.get('tz') or e.get('tz'), 'ua': (e.get('ua') or '')[:300], 'ip': e.get('ip'), 'country': e.get('country'), 'city': e.get('city'), 'org': e.get('org') or '', 'phone': bool(d.get('phone'))})
        s['last'] = max(s['last'], e['t'])
        if e['ev'] in ('slide', 'book', 'leave') and d.get('max'): s['max_slide'] = max(s['max_slide'], int(d['max']))
        if e['ev'] == 'ping': s['pings'] += 1
        if e['ev'] == 'book': s['book_clicks'] += 1
        if e['ev'] == 'video': s['videos'] += 1
        if e['ev'] == 'open': s['width'] = d.get('w', s['width']); s['tz'] = d.get('tz') or s['tz']; s['total_slides'] = d.get('total') or s['total_slides']; s['phone'] = bool(d.get('phone'))
    for s in S.values():
        s['secs'] = int((s['last'] - s['first']) / 1000)
        s['bot'] = (s['pings'] > s['secs'] // 30 + 1) or (s['width'] == 0) or ('HeadlessChrome' in s['ua']) or any(x in s['org'].lower() for x in DC)
        s['internal'] = (s['country'] in INTERNAL_COUNTRIES) or (s['tz'] in INTERNAL_TZ)
        s['counted'] = not (s['bot'] or s['internal'])
    return S

def geo(ip):
    g = json.load(open(GEO)) if os.path.exists(GEO) else {}
    if ip in g: return g[ip]
    tok = os.environ.get('IPINFO_TOKEN'); r = {}
    if tok and ip:
        try:
            with urllib.request.urlopen(f'https://ipinfo.io/{ip}?token={tok}', timeout=10) as x: d = json.load(x); r = {'country': d.get('country'), 'city': d.get('city'), 'org': d.get('org', ''), 'tz': d.get('timezone')}
        except Exception as e: say('ipinfo', ip, e)
    g[ip] = r; json.dump(g, open(GEO, 'w')); return r

COLS = ('slug', 'sid', 'client', 'first_at', 'last_at', 'secs', 'pings', 'max_slide', 'total_slides', 'videos', 'book_clicks', 'width', 'tz', 'ua', 'ip', 'country', 'city', 'org', 'phone', 'bot', 'internal', 'counted')
def sessions(conn):
    cur = conn.cursor(); cur.execute("select value from job_state where key = 'events_id'"); r = cur.fetchone(); last = int(r[0]) if r and r[0] else 0
    cur.execute('select id, sid from deck_events where id > %s order by id', (last,)); rows = cur.fetchall()
    if not rows: say('no new events'); return
    sids = list({r[1] for r in rows})
    cur.execute('select slug, sid, ev, t, ip, ua, data from deck_events where sid = any(%s) order by id', (sids,))
    ev = []
    for slug, sid, e, t, ip, ua, data in cur.fetchall():
        g = geo(ip); ev.append({'slug': slug, 'sid': sid, 'ev': e, 't': t, 'ip': ip, 'ua': ua, 'data': data or {}, **g})
    for s in aggregate(ev).values():
        s['client'] = CLIENT; s['first_at'] = dt.datetime.utcfromtimestamp(s['first'] / 1000); s['last_at'] = dt.datetime.utcfromtimestamp(s['last'] / 1000)
        upd = ', '.join(f'{c} = excluded.{c}' for c in COLS if c not in ('slug', 'sid'))
        cur.execute(f"insert into deck_sessions ({', '.join(COLS)}) values ({', '.join(['%s'] * len(COLS))}) on conflict (slug, sid) do update set {upd}", [s[c] for c in COLS])
    cur.execute("insert into job_state (key, value, updated_at) values ('events_id', %s, now()) on conflict (key) do update set value = excluded.value, updated_at = now()", (str(rows[-1][0]),))
    say('sessions updated:', len(sids), 'new events:', len(rows))

def calendly(path):
    req = urllib.request.Request('https://api.calendly.com' + path, headers={'Authorization': 'Bearer ' + os.environ['CALENDLY_PAT']})
    with urllib.request.urlopen(req, timeout=30) as r: return json.load(r)

def bookings(conn):
    if not os.environ.get('CALENDLY_PAT'): say('no CALENDLY_PAT, bookings skipped'); return
    user = os.environ.get('CALENDLY_USER_URI') or calendly('/users/me')['resource']['uri']
    since = (dt.datetime.utcnow() - dt.timedelta(days=B.get('booking_lookback_days', 14))).strftime('%Y-%m-%dT%H:%M:%SZ')
    cur = conn.cursor(); leads = json.load(open(os.path.join(PRIV, 'leads.json'))) if os.path.exists(os.path.join(PRIV, 'leads.json')) else {}
    by_slug = {v.get('slug'): (u, v) for u, v in leads.items() if v.get('slug')}
    by_email = {v.get('email', '').lower(): (u, v) for u, v in leads.items() if v.get('email')}
    by_domain = {v.get('website', '').replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].lower(): (u, v) for u, v in leads.items() if v.get('website')}
    internal = set(e.lower() for e in B.get('internal_emails') or [])
    n = 0
    for ev in calendly(f'/scheduled_events?user={user}&count=100&sort=start_time:desc&min_start_time={since}')['collection']:
        for inv in calendly('/scheduled_events/' + ev['uri'].rsplit('/', 1)[1] + '/invitees')['collection']:
            em = inv['email'].lower()
            if em in internal: continue
            cur.execute('select 1 from bookings where invitee_uri = %s', (inv['uri'],))
            if cur.fetchone():
                if inv['status'] == 'canceled': cur.execute("update bookings set status = 'canceled' where invitee_uri = %s", (inv['uri'],))
                continue
            tr = inv.get('tracking') or {}; slug = (tr.get('utm_content') or '').strip(); dom = em.split('@')[1]; url = L = None; by = 'none'; check = True
            if slug and slug in by_slug: url, L = by_slug[slug]; by = 'deck_tag'; check = False
            elif em in by_email: url, L = by_email[em]; by = 'email'; check = False
            elif dom in by_domain and not FREEMAIL(dom): url, L = by_domain[dom]; by = 'domain'; check = False
            else:
                nm = inv.get('name', '').lower().strip()
                hit = [(u, v) for u, v in leads.items() if v.get('name', '').lower().strip() == nm and nm]
                if len(hit) == 1: url, L = hit[0]; by = 'name'; check = True
            cur.execute('''insert into bookings (client, invitee_uri, booked_at, start_at, status, booker_name, booker_email, deck_slug, deck_sid, booked_by, matched_by, needs_check, tz)
                           values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) on conflict (invitee_uri) do nothing''',
                        (CLIENT, inv['uri'], inv.get('created_at'), ev['start_time'], inv['status'], inv.get('name'), em, (L or {}).get('slug'), tr.get('utm_content'), url, by, check, inv.get('timezone')))
            n += 1; say('booking', em, by, (L or {}).get('slug'), 'CHECK' if check else '')
            if url and not check and L.get('campaign'):
                try: hr('/campaign/StopLeadInCampaign', {'campaignId': L['campaign'], 'leadUrl': url}); cur.execute('update bookings set stopped = true where invitee_uri = %s', (inv['uri'],))
                except Exception as e: say('stop failed', e)
                try: hr('/lead/AddTags', {'leadProfileUrl': url, 'tags': ['Meeting booked'], 'createTagIfNotExisting': True}); cur.execute('update bookings set tagged = true where invitee_uri = %s', (inv['uri'],))
                except Exception as e: say('tag failed', e)
                try: cur.execute(f"update leads set {CLIENT}_status = 'meeting booked' where lower(linkedin_url) = %s", (url,)); cur.execute('update bookings set db_written = true where invitee_uri = %s', (inv['uri'],))
                except Exception as e: say('lead db write failed', e)
            elif check: alert(f'booking {em} ({inv.get("name")}) matched by {by}, needs a manual check')
    say('new bookings:', n)

import re
_FREE = re.compile(r'gmail|yahoo|hotmail|outlook|icloud|proton|gmx|web\.de|aol|live\.com|me\.com|mail\.com', re.I)
def FREEMAIL(d): return bool(_FREE.search(d))

def main():
    a = sys.argv[1:]
    if '--sample' in a:
        ev = [json.loads(l) for l in open(a[a.index('--sample') + 1]) if l.strip()]
        for s in aggregate(ev).values(): print(json.dumps(s, default=str))
        return
    conn = db()
    if not conn: say('DATABASE_URL missing'); sys.exit(1)
    sessions(conn); bookings(conn)
    open(os.path.join(PRIV, 'ok_track'), 'w').write(now())

if __name__ == '__main__': main()
