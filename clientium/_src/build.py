#!/usr/bin/env python3
"""build.py: spec JSON + brand.json + template.html -> <slug>/index.html
Usage:  python3 build.py specs/<slug>.json [more specs]      (run from _src)
Spec fields (written by auto/deck.py, or by hand):
  slug, company, first_name, domain            required
  shot        file name in assets/shots/ (optional; missing or absent file = no picture layout, nothing else)
  logo        file name in assets/leadlogos/ (optional; absent = company name as text)
  market      {count, label, chips, sectors} from runs/<slug>/market.json, points: exactly 2 [headline, text] pairs (slide 2)
  email       {from, to, subject, body} the first message we would send for them (slide 3)
  cover_sub   one sentence under the cover headline (optional, from the model or a default)
  offer_tail  one sentence specific to the lead under the offer body (optional)
"""
import json, os, re, sys, html, urllib.parse
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
B = json.load(open(os.path.join(HERE, 'brand.json'), encoding='utf-8'))
E = html.escape
REQUIRED = ('slug', 'company', 'first_name', 'domain', 'market')

def steps_html():
    return ''.join(f'<div class="step"><i>0{i+1}</i><div><b>{E(h)}</b><p>{E(t)}</p></div></div>' for i, (h, t) in enumerate(B['steps']))

GEO = json.load(open(os.path.join(HERE, 'geo', 'italy_regions.json'), encoding='utf-8'))

def map_html(mk):
    """Italy as inline SVG, the market regions lit. Regions come from market.json, so the picture is as true as the data."""
    on = set(mk.get('regions') or [])
    if not on: return ''
    unknown = on - set(GEO['regions']); assert not unknown, f'unknown region {unknown}'
    paths = ''.join(f'<path class="{"on" if n in on else ""}" d="{d}"><title>{E(n)}</title></path>' for n, d in GEO['regions'].items())
    n = len(on); where = 'in ' + (f'{n} regioni' if n > 1 else next(iter(on)))
    return (f'<figure class="map"><svg viewBox="{GEO["viewBox"]}" role="img" aria-label="{E(mk["count"])} decisori {E(where)}">{paths}</svg>'
            f'<figcaption class="tag"><b>{E(mk["count"])}</b>decisori {E(where)}</figcaption><span class="credit">Confini ISTAT via openpolis, CC BY 4.0</span></figure>')

def pick_cases(sectors, n=3):
    """the n cases closest to the lead's sectors (tag overlap), ties keep the brand.json order"""
    want = {x.lower() for x in (sectors or [])}
    ranked = sorted(enumerate(B['cases']), key=lambda ic: (-len(want & {t.lower() for t in ic[1].get('sectors', [])}), ic[0]))
    return [c for _, c in ranked[:n]]

def cases_html(sectors=None):
    out = []
    for c in pick_cases(sectors):
        out.append(f'<a class="crow" href="{E(c["url"])}" target="_blank" rel="noopener"><span class="kpi">{E(c["kpi"])}</span>'
                   f'<div><b>{E(c["name"])}</b><p>{E(c["label"][:1].upper() + c["label"][1:])}.<span class="tx"> {E(first_sentence(c["text"]))}</span></p></div></a>')
    return ''.join(out)

def logo_mask(name):
    """the lead logo as a one-colour mask (alpha = ink), trimmed, so the page paints it in its own text colour.
    Transparent logos keep their shape; opaque ones (white or dark box) are keyed on contrast with the corners."""
    src = os.path.join(ROOT, 'assets', 'leadlogos', name)
    im = Image.open(src).convert('RGBA'); w, h = im.size
    L = im.convert('L'); A = im.getchannel('A')
    if A.getextrema()[0] < 250:                        # has transparency: the shape is the alpha
        m = A
    else:
        corners = [L.getpixel(xy) for xy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
        bg = sum(corners) / 4
        m = L.point(lambda v: max(0, min(255, int((abs(v - bg) - 28) * 255 / 120))))   # below 28 = paper noise, gone; 148+ = full ink
    box = m.getbbox()
    if not box: return None
    m = m.crop(box); ar = m.size[0] / m.size[1]
    d = os.path.join(ROOT, 'assets', 'leadlogos', 'mask'); os.makedirs(d, exist_ok=True)
    base = os.path.splitext(name)[0]
    try:                                               # vector when potrace is installed: sharp at any zoom, like the map
        import potrace
        big = m.resize((m.size[0] * 4, m.size[1] * 4), Image.LANCZOS)
        def trace(cut):                                # potrace fills the dark pixels: ink goes dark
            bm = potrace.Bitmap(big.point(lambda v: 0 if v > cut else 255))
            segs = []
            for c in bm.trace(turdsize=8, alphamax=1.0, opticurve=True, opttolerance=0.2):
                s = c.start_point; segs.append(f'M{s.x:.1f} {s.y:.1f}')
                for sg in c.segments:
                    segs.append(f'L{sg.c.x:.1f} {sg.c.y:.1f}L{sg.end_point.x:.1f} {sg.end_point.y:.1f}' if sg.is_corner else
                                f'C{sg.c1.x:.1f} {sg.c1.y:.1f} {sg.c2.x:.1f} {sg.c2.y:.1f} {sg.end_point.x:.1f} {sg.end_point.y:.1f}')
                segs.append('Z')
            return ''.join(segs)
        # two tones keep the logo readable in one colour: the strong ink (lettering) full, the lighter ink (coloured marks) at half
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {big.size[0]} {big.size[1]}">'
               f'<path fill="#000" fill-opacity=".45" fill-rule="evenodd" d="{trace(60)}"/><path fill="#000" fill-rule="evenodd" d="{trace(200)}"/></svg>')
        fn = base + '.svg'; open(os.path.join(d, fn), 'w').write(svg)
    except ImportError:
        out = Image.new('RGBA', m.size, (0, 0, 0, 0)); out.putalpha(m)
        fn = base + '.png'; out.save(os.path.join(d, fn))
    return fn, ar

def first_sentence(s):
    return re.split(r'(?<=\.)\s', s, 1)[0]

def logos_html(prefix):
    return ''.join(f'<img src="{prefix}{E(l)}" alt="">' if l.startswith('assets/') else f'<span class="tl">{E(l)}</span>' for l in B['trusted_logos'])

def render(sp, prefix='../', fallback=False):
    """prefix = path from the deck folder to the repo root ('../' for <slug>/index.html, '/' for 404.html)."""
    for k in REQUIRED:
        assert sp.get(k) not in (None, '', []), f'{sp.get("slug")}: missing {k}'
    mk = sp['market']
    pk = json.load(open(os.path.join(HERE, 'sectors', mk['sector'] + '.json'), encoding='utf-8'))   # sector pack: written once, checked by hand, 0 tokens per lead
    shot = sp.get('shot') if sp.get('shot') and os.path.exists(os.path.join(ROOT, 'assets', 'shots', sp['shot'])) else ''
    logo = sp.get('logo') if sp.get('logo') and os.path.exists(os.path.join(ROOT, 'assets', 'leadlogos', sp['logo'])) else ''
    lm = logo_mask(logo) if logo and B.get('lead_logo') else None   # default: the lead's name in the brand font, always sharp, no logo hunting per lead
    mark = (f'<span class="ll" role="img" aria-label="{E(sp["company"])}" style="--m:url({prefix}assets/leadlogos/mask/{E(lm[0])});--ar:{lm[1]:.3f}"></span>'
            if lm else f'<span class="co">{E(sp["company"])}</span>')
    co = sp['company']
    slots = {
        'THEME': B.get('theme', 'dark'), 'ACCENT': B['accent'], 'INK': B['ink'], 'PAPER': B['paper'], 'FONT': B['font'], 'FONT_Q': urllib.parse.quote(B['font']),
        'BRAND': E(B['brand']), 'BRAND_DOMAIN': E(B['brand_domain']), 'CASES_DOMAIN': E(B['cases_domain']),
        'COMPANY': E(co), 'FIRST': E(sp['first_name']), 'PREPARED': E(f"{sp['first_name']} · {co}") if not fallback else E(f'the {co} team'),
        'DOMAIN': E(sp['domain']), 'CO_MARK': mark,
        'COVER_VISUAL': map_html(sp['market']), 'COVER_CLASS': '' if sp['market'].get('regions') else ' noshot',   # map of the market or text only, never a placeholder
        'COVER_LINE': E(B['cover_line'].replace('{company}', co)), 'COVER_SUB': E(sp.get('cover_sub') or B.get('cover_sub', '')),
        'OFFER_HEAD': E(B['offer_head']), 'OFFER_BODY': E(B['offer_body']), 'OFFER_TAIL': E(sp.get('offer_tail', '')), 'STEPS': steps_html(),
        'MKT_COUNT': E(mk['count']), 'MKT_LABEL': E(mk['label']), 'MKT_CHIPS': ''.join(f'<span>{E(c)}</span>' for c in mk['chips']),
        'MKT_LINE': E(sp.get('market_line', '')),
        'SEGMENTS': ''.join(f'<div class="seg"><i>0{i+1}</i><div><b>{E(h)}</b><p>{E(x)}</p></div></div>' for i, (h, x) in enumerate(pk['segments'])),
        'INS_HEAD': E(pk['insights_head']), 'INS_SUB': E(pk['insights_sub']), 'INS_SOURCE': E(pk['insights_source']),
        'INSIGHTS': ''.join(f'<div class="irow"><span class="kpi">{E(c["kpi"])}</span><div><b>{E(c["label"])}</b><p>{E(first_sentence(c["text"]))}</p></div></div>' for c in pk['insights']),
        'OG_IMAGE': f"https://{B['cases_domain']}/assets/og/{E(sp['slug'])}.png" if os.path.exists(os.path.join(ROOT, 'assets', 'og', sp['slug'] + '.png')) else f"https://{B['cases_domain']}/assets/og.png",
        'PROOF_HEAD': E(B['proof_head']), 'CASES': cases_html(pk.get('sectors')), 'LOGOS': logos_html(prefix),
        'TALK_HEAD': E(B['talk_head']), 'TALK_TEXT': E(B['talk_text']), 'BOOKING_URL': E(B['booking_url']), 'BOOKING_HOST': E(B['booking_host']),
        'SENDER_NAME': E(B['sender_name']), 'SENDER_TITLE': E(B['sender_title']), 'TEAM_PHOTO': prefix + E(B['team_photo']),
        'TRACK_URL': E(B['track_url']), 'SLUG': E(sp['slug']),
    }
    out = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
    for k, v in slots.items():
        out = out.replace('{{' + k + '}}', v)
    assert '{{' not in out, 'unfilled slot: ' + out[out.index('{{'):out.index('{{') + 30]
    return out

if __name__ == '__main__':
    for path in sys.argv[1:]:
        sp = json.load(open(path, encoding='utf-8'))
        out = render(sp)
        d = os.path.join(ROOT, sp['slug']); os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n').write(out)
        print('costruita', sp['slug'], '->', f"https://{B['cases_domain']}/{sp['slug']}/")
