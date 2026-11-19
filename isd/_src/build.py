#!/usr/bin/env python3
"""Client lead pages: one spec JSON -> <out>/<slug>/index.html + <out>/assets/.
Usage: python3 build.py specs/*.json --out <folder outside the repo>
Everything client-specific lives in config.json next to this file (copy, banned words, calendar, required proof text).
Refuses to write inside ~/paginadedicata. Every lead page needs a verified company fact (cover_note + evidence),
hard rule 18/11: leads without one are reported to the OM, never published generic. Only a spec with no_fact_ok (the example page) is exempt."""
import html, json, os, re, shutil, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ASSETS = os.path.join(HERE, '..', 'assets')
CFG = json.load(open(os.path.join(HERE, 'config.json'), encoding='utf-8'))
_T = sys.argv[sys.argv.index('--tpl') + 1] if '--tpl' in sys.argv else 'template.html'
V2 = _T != 'template.html'
TPL = open(os.path.join(HERE, _T), encoding='utf-8').read()
CTA_LI = open(os.path.join(HERE, 'cta_linkedin_v2.html' if V2 else 'cta_linkedin.html'), encoding='utf-8').read()
BAD = re.compile(r'[—–:!;]| - ')
BANNED = re.compile(CFG['banned'], re.I)
E = lambda s: html.escape(s, quote=False)
A = lambda s: html.escape(s, quote=True)
def slugify(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
def clarity_attr(sp):
    words = {w.lower() for w in re.split(r'\W+', sp.get('first') or (sp.get('full_name') or '').split(' ')[0]) if len(w) >= 3}
    return ' data-no-slug' if words & set(sp['slug'].split('-')) else ''
def visible(page):
    t = re.sub(r'<script.*?</script>|<style.*?</style>|<head>.*?</head>', ' ', page, flags=re.S)
    return html.unescape(re.sub(r'<[^>]+>', ' ', t))
def render(sp):
    c, full, slug = sp['company'].strip(), (sp.get('full_name') or '').strip(), sp['slug']
    note, idea = (sp.get('cover_note') or '').strip(), (sp.get('idea') or '').strip()
    if (note or idea) and not sp.get('evidence'): raise ValueError(f'{slug}: claim about the lead with no evidence')
    if not note and not sp.get('no_fact_ok'): raise ValueError(f'{slug}: no verified company fact (hard rule 18/11), report to the OM instead of publishing generic')
    if full and slugify(full) == slug: raise ValueError(f'{slug}: the slug is the person name')
    cal_url = CFG.get('cal_url') or ''
    for bad in CFG.get('cal_forbidden', []):
        if bad in cal_url: raise ValueError('forbidden calendar')
    cal = (f'<iframe id="calf" title="{A(CFG["cal_title"])}" data-src="{A(cal_url + ("&" if "?" in cal_url else "?") + "utm_source=deck&utm_medium=linkedin&utm_campaign=" + slug)}"></iframe>') if cal_url else CTA_LI
    lead_css = 'html:not(.phone) h1{font-size:44px}' if len(c) > 30 else 'html:not(.phone) h1{font-size:48px}' if len(c) > 20 else ''
    src = re.sub(r'^https?://(www\.)?', '', (sp.get('evidence') or [{'url': ''}])[0]['url']).split('/')[0]
    if V2 and ('{{SHOT}}' in TPL) and not sp.get('shot'): raise ValueError(f'{slug}: v2 needs a screenshot of the prospect site')
    plogo = f'<span class="plogo"><img src="{A(sp["logo"])}" alt="{A(c)}"></span>' if sp.get('logo') else f'<span class="pname">{E(c)}</span>'
    h1v2 = CFG.get('h1_v2', '{c}').split('{c}')
    case = CFG['cases'][sp.get('case') or CFG['default_case']]
    vals = {'COMPANY': E(c), 'COMPANY_ATTR': A(c), 'PREP': E(f'{full} di {c}' if full else c), 'PREP_ATTR': A(f'{full} di {c}' if full else c),
            'OG_PATH': f'og/{slug}.jpg', 'LEAD_CSS': lead_css, 'LEAD_MARK': f'<span class="nm">{E(c)}</span>',
            'H1': E(CFG['h1'].format(c=c)), 'SUB': E(f"{note} {CFG['tail']}" if note else CFG['gen_sub'].format(c=c)),
            'IDEA': E(idea or CFG['gen_idea']), 'CLARITY_ATTR': clarity_attr(sp), 'CAL_BLOCK': cal,
            'TALK_NOTE': CFG['talk_cal'] if cal_url else '', 'CASE_TAG': E(case['tag']), 'CASE_BIG': E(case['big']),
            'CASE_SMALL': E(case['small']), 'CASE_TEXT': E(case['text']),
            'PROSPECT_LOGO': plogo, 'FULLNAME': E(full or c), 'SENDER': E(CFG.get('sender', '')), 'NOTE': E(note), 'GEN_SUB': E(CFG.get('gen_sub_v2', CFG['gen_sub']).format(c=c)),
            'SRC': E(src), 'SHOT': A(sp.get('shot', ''))}
    if V2: vals['H1'] = E(h1v2[0]) + '<em>' + E(c) + '</em>' + E(h1v2[1] if len(h1v2) > 1 else '')
    page = re.sub(r'\{\{(\w+)\}\}', lambda m: vals[m.group(1)], TPL)
    v = visible(page)
    m = BAD.search(v)
    if m: raise ValueError(f'{slug}: copy rule broken in {m.group(0)!r} near {v[max(0, m.start() - 40):m.start() + 10]!r}')
    vv = v.replace(c, '')
    for ok in CFG.get('banned_ok', []): vv = vv.replace(ok, '')
    m = BANNED.search(vv)
    if m: raise ValueError(f'{slug}: banned phrase {m.group(0)!r}')
    for req in CFG.get('required', []):
        if req not in v: raise ValueError(f'{slug}: required text missing {req!r}')
    return page
def main():
    args = sys.argv[1:]
    if '--tpl' in args: j = args.index('--tpl'); args = args[:j] + args[j + 2:]
    i = args.index('--out'); out = os.path.abspath(os.path.expanduser(args[i + 1])); specs = args[:i] + args[i + 2:]
    if os.path.realpath(out).startswith(os.path.realpath(os.path.expanduser('~/paginadedicata'))): sys.exit('out is inside the published repo: refused')
    os.makedirs(f'{out}/assets', exist_ok=True)
    for f in CFG['shared'] + CFG.get('shared_v2', []) * V2: shutil.copy(os.path.join(ASSETS, f), f'{out}/assets/{f}')
    done, bad = [], 0
    for p in specs:
        sp = json.load(open(p, encoding='utf-8'))
        try: page = render(sp)
        except ValueError as e: print('REFUSED', e); bad += 1; continue
        os.makedirs(f"{out}/{sp['slug']}", exist_ok=True)
        ld = os.path.join(ASSETS, 'leads', sp['slug'].removesuffix('-v2'))
        if os.path.isdir(ld): shutil.copytree(ld, f"{out}/assets/leads/{os.path.basename(ld)}", dirs_exist_ok=True)
        open(f"{out}/{sp['slug']}/index.html", 'w', encoding='utf-8').write(page); done.append(sp['slug'])
    print(len(done), 'pages in', out, '|', bad, 'refused'); sys.exit(1 if bad else 0)
if __name__ == '__main__': main()
