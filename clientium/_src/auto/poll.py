#!/usr/bin/env python3
"""poll.py (every 6 h): HeyReach connected leads -> one deck per company -> push -> live check -> link into the custom field -> guard.
Usage: python3 poll.py [--dry] [--slug <slug> [--force]]
Config in brand.json:  "campaigns": [ids]  "field": "presentation"  "per_run": 20  "budget_min": 25  "link_message_hours": 24
State: _private/leads.json (profile_url -> lead facts, slug), _private/poll_state.json. decks table in the DB when DATABASE_URL is set.
"""
import json, os, re, subprocess, sys, time, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import *
CAMPAIGNS = B.get('campaigns') or []; FIELD = B.get('field', 'presentation'); PER_RUN = B.get('per_run', 20); BUDGET = B.get('budget_min', 25) * 60
LINK_H = B.get('link_message_hours', 24); MAX_ATTEMPTS = 3
PRIV = os.path.join(ROOT, '_private'); os.makedirs(PRIV, exist_ok=True)
LEADS = os.path.join(PRIV, 'leads.json'); STATE = os.path.join(PRIV, 'poll_state.json')
SITE = f"https://{B['cases_domain']}/"
FREE = re.compile(r'gmail|yahoo|hotmail|outlook|icloud|proton|gmx|web\.de|aol|live\.com|me\.com|mail\.com', re.I)

def git(*a, check=True):
    r = subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode: raise RuntimeError('git %s: %s' % (' '.join(a), r.stderr[-300:]))
    return r.stdout

def connected():
    """profile_url -> {name, company, email, website, campaign, sender, status, connected}"""
    out = {}
    for cid in CAMPAIGNS:
        for it in hr_pages('/campaign/GetLeadsFromCampaign', {'campaignId': cid}):
            p = it.get('linkedInUserProfile') or it.get('lead') or {}
            url = norm_url(p.get('profileUrl') or it.get('profileUrl'))
            if not url: continue
            st = (it.get('connectionStatus') or it.get('status') or '').upper()
            conn = any(k in st for k in ('CONNECTED', 'ACCEPTED', 'FIRST_DEGREE', '1ST')) or it.get('isConnected') is True
            cf = {f.get('name'): f.get('value') for f in (p.get('customUserFields') or it.get('customUserFields') or [])}
            out[url] = {'name': ' '.join(x for x in (p.get('firstName'), p.get('lastName')) if x), 'company': p.get('companyName') or '',
                        'email': p.get('emailAddress') or '', 'website': cf.get('website') or cf.get('companyWebsite') or '', 'field': cf.get(FIELD) or '',
                        'campaign': cid, 'sender': it.get('linkedInAccountId') or it.get('senderName') or '', 'status': st, 'connected': conn}
    return out

def website_for(url, info, conn):
    """lead DB (SOP 1) -> HeyReach field -> work email domain -> ''"""
    if conn:
        try:
            cur = conn.cursor(); cur.execute('select domain, website from leads where lower(linkedin_url) = %s limit 1', (url,)); r = cur.fetchone()
            if r and (r[0] or r[1]): return r[1] or 'https://' + r[0]
        except Exception as e: say('db lookup', e)
    if info.get('website'): return info['website']
    em = info.get('email') or ''
    if '@' in em and not FREE.search(em): return 'https://' + em.split('@')[1]
    return ''

def set_field(url, cid, value):
    body = {'leadMemberIdOrUrl': url, 'customFields': [{'name': FIELD, 'value': value}]}
    hr(f'/campaign/UpdateLeadCustomFields/campaigns/{cid}/leads/custom-fields', body, 'PATCH')
    lid = (B.get('lists') or {}).get(str(cid))
    if lid:
        try: hr(f'/list/UpdateLeadCustomFields/lists/{lid}/leads/custom-fields', body, 'PATCH')
        except Exception as e: say('list field update failed (campaign set):', e)

def live(slug):
    try:
        with urllib.request.urlopen(urllib.request.Request(SITE + slug + '/', headers={'User-Agent': 'Mozilla/5.0'}), timeout=20) as r:
            return r.status if B['brand'] in r.read().decode('utf-8', 'ignore') else 0
    except urllib.error.HTTPError as e: return e.code
    except Exception: return 0

def db_deck(conn, slug, url, **kw):
    if not conn: return
    try:
        cur = conn.cursor()
        cur.execute('insert into decks (client, slug, url, profile_url) values (%s,%s,%s,%s) on conflict (client, slug) do nothing', (CLIENT, slug, SITE + slug + '/', url))
        if kw:
            sets = ', '.join(f'{k} = %s' for k in kw); cur.execute(f'update decks set {sets} where client = %s and slug = %s', (*kw.values(), CLIENT, slug))
    except Exception as e: say('db decks', e)

def main():
    a = sys.argv[1:]; dry = '--dry' in a; one = a[a.index('--slug') + 1] if '--slug' in a else None; force = '--force' in a
    if not CAMPAIGNS: say('brand.json has no "campaigns", nothing to poll'); return
    conn = db()
    leads = json.load(open(LEADS, encoding='utf-8')) if os.path.exists(LEADS) else {}
    st = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {'slugs': {}, 'conn': {}}
    git('pull', '--rebase', '--autostash', '-q')
    hrl = connected(); say('leads in campaigns:', len(hrl), 'connected:', sum(1 for v in hrl.values() if v['connected']))
    todo = {}
    for url, info in hrl.items():
        L = leads.setdefault(url, {}); L.update({k: info[k] for k in ('name', 'company', 'email', 'campaign', 'sender') if info.get(k)})
        L.setdefault('website', website_for(url, info, conn)); L.setdefault('slug', slugify(L.get('company')) or slugify(L.get('name')))
        if not info['connected']: continue
        c = st['conn'].setdefault(url, {'first_ts': time.time(), 'first_seen': now()})
        c.update(status=info['status'], field=info['field'], slug=L['slug'], campaign=info['campaign'])
        if L['slug']: todo.setdefault(L['slug'], (url, L))
    json.dump(leads, open(LEADS, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    pending = [s for s in todo if st['slugs'].get(s, {}).get('status') in (None, 'retry') and not os.path.exists(os.path.join(ROOT, s, 'index.html'))]
    if one: pending = [one] if (one in todo or force) else []
    say('connected companies:', len(todo), 'to build:', len(pending), pending[:20])
    if dry:
        for s in pending: print(s, todo.get(s, ('', {}))[1].get('company'), todo.get(s, ('', {}))[1].get('website'))
        return
    built = 0; t0 = time.time()
    for s in pending[:PER_RUN]:
        if time.time() - t0 > BUDGET: say('budget reached'); break
        url, L = todo.get(s) or next(((u, l) for u, l in leads.items() if l.get('slug') == s), ('', {}))
        rec = st['slugs'].setdefault(s, {'attempts': 0}); rec['attempts'] += 1
        db_deck(conn, s, url, status='queued', attempts=rec['attempts'])
        r = subprocess.run([sys.executable, os.path.join(HERE, 'deck.py'), s, L.get('name') or 'there', L.get('company') or s, L.get('website') or ''], capture_output=True, text=True, cwd=HERE)
        res = {}
        try: res = json.loads(r.stdout.strip().splitlines()[-1])
        except Exception: pass
        if r.returncode == 0:
            rec.update(status='built', error=''); built += 1
            db_deck(conn, s, url, status='built', model_calls=1, tokens_in=res.get('tokens_in'), tokens_out=res.get('tokens_out'), build_seconds=res.get('seconds'), built_at=now(), error='')
            say('built', s, res.get('tokens_in'), 'tokens', res.get('warnings'))
        elif r.returncode == 2:
            rec.update(status='failed', error=res.get('error', 'validation')); db_deck(conn, s, url, status='failed', model_calls=1, tokens_in=res.get('tokens_in'), error=rec['error'])
            alert(f'deck /{s}/ failed validation, not retried: {rec["error"]}')
        else:
            err = (res.get('error') or r.stderr[-200:]).strip(); rec.update(status='retry' if rec['attempts'] < MAX_ATTEMPTS else 'failed', error=err)
            db_deck(conn, s, url, status=rec['status'], error=err)
            if rec['status'] == 'failed': alert(f'deck /{s}/ crashed {MAX_ATTEMPTS} times: {err}')
        json.dump(st, open(STATE, 'w', encoding='utf-8'), indent=1)
    if built:
        subprocess.run([sys.executable, os.path.join(SRC, 'build_fallback.py')], cwd=SRC)
        git('add', '-A'); git('commit', '-q', '-m', f'{built} decks {now()}', check=False)
        r = subprocess.run(['git', 'push', '-q'], cwd=ROOT, capture_output=True, text=True)
        if r.returncode: alert('git push failed, decks committed locally, next run retries: ' + r.stderr[-200:])
        else: time.sleep(90)
    # live check + field + guard
    issues = []
    for url, c in st['conn'].items():
        s = c['slug']
        if not s or not os.path.exists(os.path.join(ROOT, s, 'index.html')): continue
        code = c.get('live')
        if code != 200: code = c['live'] = live(s)
        if code == 200:
            st['slugs'].setdefault(s, {})['status'] = 'live'; db_deck(conn, s, url, status='live', live_at=now())
            want = SITE + s + '/'
            if c.get('field') != want:
                try: set_field(url, c['campaign'], want); c['field'] = want; db_deck(conn, s, url, status='link_set', link_set_at=now()); say('link set', url, want)
                except Exception as e: issues.append(f'field not set for {url}: {e}')
    for url, c in st['conn'].items():
        due_in = LINK_H * 3600 - (time.time() - c['first_ts'])
        if not c.get('field') and due_in < 2 * 3600: issues.append(f'{c.get("slug")} ({url}) gets the link message in {max(0, int(due_in / 60))} min and has NO link')
    json.dump(st, open(STATE, 'w', encoding='utf-8'), indent=1)
    if issues: alert('\n'.join(issues[:10]))
    say(f'summary: connected {len(st["conn"])}, built {built}, pending {max(0, len(pending) - built)}, issues {len(issues)}')
    open(os.path.join(PRIV, 'ok_poll'), 'w').write(now())

if __name__ == '__main__': main()
