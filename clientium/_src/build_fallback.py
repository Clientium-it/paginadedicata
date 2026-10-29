#!/usr/bin/env python3
"""build_fallback.py: writes ../404.html, the generic deck GitHub Pages serves for every slug without a folder.
It reads _private/leads.json ({profile_url: {slug, company, ...}}, written by auto/poll.py, gitignored) and embeds
slug -> company name (company names only, the repo is public) so a lead who clicks early sees his company on the cover.
Run after every new lead list upload:  python3 build_fallback.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); import build
B = build.B
m = {}
lp = os.path.join(ROOT, '_private', 'leads.json')
if os.path.exists(lp):
    for v in json.load(open(lp, encoding='utf-8')).values():
        if v.get('slug') and v.get('company'): m.setdefault(v['slug'], v['company'].strip())
sp = {'slug': '404', 'company': '__CO__', 'first_name': 'you', 'domain': '__CO__',
      'saw_lines': ['Buyers decide in the first seconds whether a brand is worth their attention.',
                    'So the proof a brand already has should be the first thing they see, not the last.',
                    'We looked at how __CO__ shows up online and put together how we would approach it, the full page is on its way.'],
      'points': [['Your proof, up front', 'Every review, number and press mention you already have becomes the opening of every creative, so the first impression does the convincing.'],
                 ['One offer, everywhere', 'The offer your site makes is the one your ads and emails make, the same words, the same numbers, so a buyer never meets a different story.'],
                 ['Objections answered early', 'Shipping, returns and sizing answered before the click, taken straight from the questions your support team hears most.'],
                 ['Weekly releases', 'New creatives every week built on what won last week, cut what lost, every number in one shared sheet you can open any time.']]}
t = build.render(sp, prefix='/', fallback=True)
t = t.replace('<figure class="shot"><img src="" alt=""><figcaption></figcaption></figure>', '')
js = ('<script>(()=>{const M=' + json.dumps(m, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + ';'
      'const e=s=>s.replace(/&/g,"&amp;").replace(/</g,"&lt;");const r=M[location.pathname.split("/").filter(Boolean)[0]]||"your brand";'
      'document.body.innerHTML=document.body.innerHTML.split("__CO__").join(e(r));document.title=r+" × ' + B['brand'].replace('"', '') + '";'
      'document.querySelectorAll("section[aria-label]").forEach(s=>s.setAttribute("aria-label",s.getAttribute("aria-label").split("__CO__").join(r)));})();</script>\n')
t = t.replace('<title>__CO__', '<title>your brand', 1).replace('</body>', js + '</body>', 1)
open(os.path.join(ROOT, '404.html'), 'w', encoding='utf-8', newline='\n').write(t)
print('404.html written with', len(m), 'company names')
