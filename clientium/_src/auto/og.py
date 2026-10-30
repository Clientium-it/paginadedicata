#!/usr/bin/env python3
"""og.py: the link preview image per lead (1200x630), what LinkedIn shows in the chat before anyone clicks.
Usage: python3 og.py specs/<slug>.json      (run from _src)   -> assets/og/<slug>.png
Brand colours and font from brand.json, lead logo or name, "Preparata per", the market number. Headless, no model.
"""
import asyncio, base64, html, json, os, sys
from playwright.async_api import async_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); ROOT = os.path.dirname(SRC)
B = json.load(open(os.path.join(SRC, 'brand.json'), encoding='utf-8'))
E = html.escape

def data_uri(path):
    ext = os.path.splitext(path)[1].lstrip('.').replace('jpg', 'jpeg').replace('svg', 'svg+xml')
    return f'data:image/{ext};base64,' + base64.b64encode(open(path, 'rb').read()).decode()

def page(sp):
    base = os.path.join(ROOT, 'assets', 'leadlogos', 'mask', os.path.splitext(sp.get('logo') or '_')[0])   # written by build.py
    mask = base + '.svg' if os.path.exists(base + '.svg') else base + '.png'
    mark = (f'<i class="ll" style="-webkit-mask:url({data_uri(mask)}) left center/contain no-repeat"></i>'
            if sp.get('logo') and os.path.exists(mask) else f'<b>{E(sp["company"])}</b>')
    mk = sp.get('market') or {}
    big = f'<div class="big">{E(mk["count"])}</div><div class="lb">{E(mk["label"])}</div>' if mk.get('count') else ''
    return f'''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family={B['font'].replace(' ', '+')}:wght@500;700;800&display=swap" rel="stylesheet">
<style>*{{margin:0;box-sizing:border-box}}body{{width:1200px;height:630px;background:{B['ink']};color:{B['paper']};font-family:"{B['font']}",sans-serif;padding:64px 72px;display:flex;flex-direction:column}}
.pair{{display:flex;align-items:center;gap:22px;font-size:40px;font-weight:800;letter-spacing:-.02em}}.x{{color:{B['accent']};font-weight:500}}
.pair .ll{{display:block;height:66px;width:300px;background:{B['paper']}}}
.prep{{margin-top:40px;font-size:22px;letter-spacing:.14em;text-transform:uppercase;color:{B['accent']};font-weight:700}}
.big{{margin-top:auto;font-size:120px;font-weight:800;letter-spacing:-.04em;line-height:.9;color:{B['accent']}}}
.lb{{margin-top:14px;font-size:30px;font-weight:700;max-width:30ch;line-height:1.2}}</style></head>
<body><div class="pair"><span>{E(B['brand'])}</span><span class="x">×</span>{mark}</div>
<div class="prep">Preparata per {E(sp['first_name'])} · {E(sp['company'])}</div>{big}</body></html>'''

async def main(paths):
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, executable_path=os.environ.get('CHROMIUM_EXE') or None)
        pg = await b.new_page(viewport={'width': 1200, 'height': 630})
        for path in paths:
            sp = json.load(open(path, encoding='utf-8'))
            await pg.set_content(page(sp), wait_until='networkidle'); await pg.wait_for_timeout(300)
            out = os.path.join(ROOT, 'assets', 'og'); os.makedirs(out, exist_ok=True)
            await pg.screenshot(path=os.path.join(out, sp['slug'] + '.png'))
            print('og', sp['slug'])
        await b.close()

if __name__ == '__main__':
    asyncio.run(main(sys.argv[1:]))
