#!/usr/bin/env python3
"""ISD batch pages: verify on VPS -> logos -> specs -> build -> montage.
Usage: run_batch.py REQUEST.json WORKDIR   (then pub.sh WORKDIR "msg")
Request rows: azienda, page|slug, fatto, source_url, fatto_quote, [domain], [full_name|nome+cognome], [sedi_quote, sedi_url]
One page per company: if a company has more contacts, pass full_name empty -> page shows the company name.
"""
import json, os, re, sys, subprocess, shutil, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plan_lib import subj, clean, slug as mkslug, quotes, urls_for, fname
from urllib.parse import urlparse
VPS = 'root@167.233.71.213'
R = os.path.expanduser('~/paginadedicata/isd')
HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.expanduser('~/deck-kit-review/.venv/bin/python')
BAD = re.compile(r'[—–:!;]| - ')

def sh(c): return subprocess.run(c, shell=True, check=False, capture_output=True, text=True)

def main():
    req, W = sys.argv[1], os.path.abspath(sys.argv[2]); os.makedirs(W, exist_ok=True)
    rows = json.load(open(req)); report = {'ok': [], 'refused': []}
    jobs, logo_in, specs = [], '', {}
    used = set()
    for x in rows:
        name = subj(x['fatto'], x['azienda']) or clean(x['azienda'])
        x['_name'] = name
        base = mkslug(name); slug = base; i = 2
        while slug in used or (os.path.exists(f'{R}/_src/specs/{slug}.json') and json.load(open(f'{R}/_src/specs/{slug}.json')).get('company','').lower() != name.lower()):
            slug = f'{base}-{i}'; i += 1
        used.add(slug); x['_slug'] = slug
        if os.path.exists(f'{R}/{slug}/index.html'):
            report['refused'].append([slug, 'already live, not rebuilt']); continue
        if os.path.exists(f'{R}/_src/specs/{slug}.json'):
            old = json.load(open(f'{R}/_src/specs/{slug}.json'))
            if old.get('company', '').lower() != x['_name'].lower():
                report['refused'].append([slug, f"slug taken by {old.get('company')}"]); continue
        dom = x.get('domain') or urlparse(x['source_url']).netloc
        dom = re.sub(r'^www\.', '', dom)
        qs = quotes(x['fatto_quote'] + (' || ' + x['sedi_quote'] if x.get('sedi_quote') else ''))
        urls = ([x['sedi_url']] if x.get('sedi_url') else []) + urls_for(x['source_url'], dom)
        jobs.append({'slug': slug, 'urls': list(dict.fromkeys(urls)), 'q': qs})
        logo_in += f'{slug} https://www.{dom} x\n'; specs[slug] = (x, qs)
    json.dump(jobs, open(f'{W}/vq_in.json', 'w'), ensure_ascii=False)
    open(f'{W}/logo_in.txt', 'w').write(logo_in)
    tag = os.path.basename(W)
    rd = f'/tmp/cl/isdbatch_{tag}'
    sh(f'ssh {VPS} "rm -rf {rd}; mkdir -p {rd}/isd_logos"')
    for a, b in [(f'{W}/vq_in.json', 'vq_in.json'), (f'{W}/logo_in.txt', 'logo_in.txt'), (f'{HERE}/vps_verify2.py', 'v.py'), (f'{HERE}/vps_logo.py', 'l.py')]:
        sh(f'scp -q {a} {VPS}:{rd}/{b}')
    # patch hardcoded paths in the VPS copies
    sh(f"ssh {VPS} \"cd {rd} && sed -i 's#/tmp/cl/isd_logos.json#{rd}/logos.json#; s#/tmp/cl/isd_logos#{rd}/isd_logos#; s#/tmp/cl/isd_logo_in.txt#{rd}/logo_in.txt#' l.py && timeout 3000 python3 v.py vq_in.json vq_out.json; timeout 900 python3 l.py\"")
    os.makedirs(f'{W}/logos', exist_ok=True)
    sh(f'scp -q {VPS}:{rd}/vq_out.json {W}/; scp -q {VPS}:{rd}/logos.json {W}/; scp -q "{VPS}:{rd}/isd_logos/*" {W}/logos/')
    vq = json.load(open(f'{W}/vq_out.json')); lg = json.load(open(f'{W}/logos.json')) if os.path.exists(f'{W}/logos.json') else {}
    built = []
    for slug, (x, qs) in specs.items():
        found = vq.get(slug, {})
        miss = [q for q in qs if not found.get(q)]
        if miss: report['refused'].append([slug, 'quote not found verbatim: ' + miss[0][:90]]); continue
        note = re.sub(r'^ho visto che\s+', '', x['fatto'].strip()); note = note[0].upper() + note[1:]
        if not note.endswith('.'): note += '.'
        if BAD.search(note): report['refused'].append([slug, 'copy regex: ' + note]); continue
        if not re.search(r'\d|\b(due|tre|quattro|cinque|sei|sette|otto|nove|dieci|undici|dodici|venti|trenta|cento)\b', note, re.I):
            report['refused'].append([slug, 'no number of sites/branches in fatto: ' + note]); continue
        full = (x.get('full_name') if 'full_name' in x else f"{x.get('nome','')} {x.get('cognome','')}").strip() if (x.get('full_name') or x.get('nome')) else ''
        full = ' '.join(w.capitalize() for w in full.split()) if full and full.isupper() else (full or '')
        sp = {'slug': slug, 'company': x['_name'], 'full_name': full, 'first': full.split(' ')[0] if full else '',
              'cover_note': note, 'evidence': [{'claim': note, 'url': found[q][1].rstrip('?'), 'quote': q} for q in qs],
              'checked': f'VPS playwright verbatim check ({os.path.basename(req)})', 'case': 'B'}
        lf = (lg.get(slug) or {}).get('file')
        if lf and os.path.exists(f'{W}/logos/{lf}'):
            ext = lf.rsplit('.', 1)[1]; d = f'{R}/assets/leads/{slug}'; os.makedirs(d, exist_ok=True)
            dst = f'{d}/logo.{ext}'; shutil.copy(f'{W}/logos/{lf}', dst); fix_logo(dst); sp['logo'] = f'../assets/leads/{slug}/logo.{ext}'
        json.dump(sp, open(f'{R}/_src/specs/{slug}.json', 'w'), ensure_ascii=False, indent=1)
        built.append(slug); report['ok'].append({'azienda': x['azienda'], 'company': x['_name'], 'slug': slug, 'page_url': f'https://paginadedicata.com/isd/{slug}/', 'logo': sp.get('logo', 'NOLOGO'), 'verify': sorted(set(found[q][0] for q in qs))})
    out = f'{W}/out'; shutil.rmtree(out, ignore_errors=True)
    if built:
        r = sh(f'cd {R}/_src && python3 build.py --tpl template_v2.html ' + ' '.join(f'specs/{s}.json' for s in built) + f' --out {out}')
        print(r.stdout[-300:], r.stderr[-500:])
    json.dump(report, open(f'{W}/report.json', 'w'), ensure_ascii=False, indent=1)
    print(f"built {len(built)} refused {len(report['refused'])}")
    for s in report['refused']: print('  REFUSED', *s)

def fix_logo(p):
    if p.endswith('.svg'):
        s = open(p, encoding='utf-8', errors='ignore').read()
        m = re.search(r'<svg[^>]*>', s); tag = m.group(0) if m else ''
        if tag and 'width=' not in tag:
            vb = re.search(r'viewBox="([\d.\s-]+)"', tag)
            if vb:
                _, _, w, h = [float(v) for v in vb.group(1).split()]
                nw = 200; nh = round(h * nw / w, 1); s = s.replace(tag, tag[:-1] + f' width="{nw}" height="{nh}">', 1)
        fills = re.findall(r'fill[:=]\s*"?\s*(#fff(?:fff)?|white)\b', s, re.I)
        others = [f for f in re.findall(r'fill[:=]\s*"?\s*(#[0-9a-f]{3,6}|[a-z]+)', s, re.I) if f.lower() not in ('none', '#fff', '#ffffff', 'white', 'currentcolor')]
        if fills and not others: s = re.sub(r'(#fff(?:fff)?|white)\b', '#1a1a1a', s, flags=re.I)
        open(p, 'w').write(s)
    else:
        sh(f'{PY} -c "from PIL import Image\nim=Image.open(\'{p}\').convert(\'RGBA\');px=[q for q in im.getdata() if q[3]>100]\nw=sum(1 for q in px if min(q[:3])>235);t=sum(1 for q in im.getdata() if q[3]<50)/(im.size[0]*im.size[1])\nif px and w/len(px)>0.85 and t>0.1: im.putdata([(26,26,26,a) for r,g,b,a in im.getdata()]);im.save(\'{p}\')"')

if __name__ == '__main__': main()
