"""slim_pages.py page.html...: in place, swap the inline Italy map for the shared assets/maps/<key>.svg and the <style> block for assets/css/<key>.css.
Nothing else on the page changes (the pages are NOT rebuilt: specs have moved on since they were published)."""
import html, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build
MAP = re.compile(r'<figure class="map"><svg viewBox="[^"]*" role="img" aria-label="([^"]*)">([\s\S]*?)</svg>')
CSS = [('.map svg{height:560px', '.map svg,.map img{height:560px'),
       ('html.phone .map svg{height:min(28vh', 'html.phone .map svg,html.phone .map img{height:min(28vh'),
       ('html.phone .map svg{height:min(30vh', 'html.phone .map svg,html.phone .map img{height:min(30vh')]
done = 0
for p in sys.argv[1:]:
    s = open(p, encoding='utf-8').read(); o = s
    m = MAP.search(s)
    if m:
        on = {html.unescape(t) for t in re.findall(r'<path class="on"[^>]*><title>([^<]*)</title>', m.group(2))}
        assert on and on <= set(build.GEO['regions']), (p, on)
        s = s[:m.start()] + f'<figure class="map"><img src="../assets/maps/{build.map_file(on)}.svg" alt="{m.group(1)}">' + s[m.end():]
        for a, b in CSS:
            if a in s and b not in s: s = s.replace(a, b)
    s = build.shared_css(s)
    if s != o: open(p, 'w', encoding='utf-8', newline='\n').write(s); done += 1
print(done, 'pages slimmed of', len(sys.argv) - 1)
