#!/usr/bin/env python3
"""deck.py: one lead -> facts -> ONE model call -> validate -> spec -> built deck. Never a second call.
Usage: python3 deck.py <slug> "<First Last>" "<Company>" <url> [--no-facts]   (--no-facts reuses runs/<slug>/facts.txt)
Model: ANTHROPIC_API_KEY set -> API; else the logged-in Claude Code CLI (`claude -p`). DECK_MODEL defaults to claude-haiku-5-5.
Exit 0 = built, 2 = validation failed (logged in runs/<slug>/result.json, not retried), 1 = crash (poll.py counts attempts).
"""
import json, os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.dirname(HERE); ROOT = os.path.dirname(SRC)
sys.path.insert(0, HERE); sys.path.insert(0, SRC)
MODEL = os.environ.get('DECK_MODEL', 'claude-haiku-5-5')
NUM = re.compile(r'\d[\d,.]*\d|\d')

def load_env():
    for p in (os.path.join(ROOT, '.env'), os.path.expanduser('~/.env')):
        if os.path.exists(p):
            for ln in open(p, encoding='utf-8'):
                ln = ln.split('#')[0].strip()
                if '=' in ln: k, v = ln.split('=', 1); os.environ.setdefault(k.strip(), v.strip())

def call(system, facts):
    """returns (text, tokens_in, tokens_out)"""
    if os.environ.get('ANTHROPIC_API_KEY'):
        import anthropic
        r = anthropic.Anthropic().messages.create(model=MODEL, max_tokens=400, temperature=0, system=system, messages=[{'role': 'user', 'content': facts}])
        return r.content[0].text, r.usage.input_tokens, r.usage.output_tokens
    cmd = ['claude', '-p', '--model', MODEL, '--tools', '', '--disable-slash-commands', '--setting-sources', '', '--system-prompt', system, '--output-format', 'json']
    r = subprocess.run(cmd, input=facts, capture_output=True, text=True, timeout=240)
    if r.returncode != 0: raise RuntimeError('claude cli: ' + r.stderr[-300:])
    j = json.loads(r.stdout); u = j.get('usage') or {}
    return j.get('result', ''), (u.get('input_tokens', 0) + u.get('cache_read_input_tokens', 0) + u.get('cache_creation_input_tokens', 0)), u.get('output_tokens', 0)

def clean(s):
    s = s.replace('—', ',').replace('–', ',').replace(' - ', ', ').replace('**', '')
    s = re.sub(r'<[^>]+>', '', s); s = re.sub(r'\s+,', ',', s); return ' '.join(s.split())

KEEP = ('LEAD:', 'SITE PROOF:', 'SITE MONEY FIGURES:', 'SITE OFFERS:', 'SECTORS NAMED:')

def compact(facts, slug):
    """what the model sees: a few labelled lines, the market, 800 chars of homepage. About 1k tokens instead of 15k."""
    lines = [l for l in facts.split('\n') if l.startswith(KEEP)]
    home = facts.split('HOMEPAGE TEXT (first 2500 chars):', 1)[-1] if 'HOMEPAGE TEXT' in facts else ''
    p = os.path.join(HERE, 'runs', slug, 'market.json'); m = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None
    if m: lines.append('MARKET (our data): ' + m['count'] + ' ' + m['label'])
    lines.append('HOMEPAGE: ' + ' '.join(home.split())[:800])
    return m, '\n'.join(lines)

def validate(text, facts):
    """valid JSON, three strings, every number in the facts. Dashes and tags are fixed by script (never a second call)."""
    t = text.strip()
    if t.startswith('```'): t = re.sub(r'^```\w*\s*|\s*```$', '', t)
    m = re.search(r'\{.*\}', t, re.S); t = m.group(0) if m else t
    sp = json.loads(t)
    for k in ('cover_sub', 'market_line', 'offer_tail'):
        assert isinstance(sp.get(k), str) and sp[k].strip(), f'missing {k}'
        sp[k] = clean(sp[k])
    allowed = set(NUM.findall(facts)); warn = []
    for k in ('cover_sub', 'market_line', 'offer_tail'):
        for n in NUM.findall(sp[k]):
            assert n in allowed, f'number not in facts: {n}'
    if not 18 <= len(sp['market_line'].split()) <= 32: warn.append('market_line length')
    return sp, warn

def main():
    load_env()
    a = [x for x in sys.argv[1:] if not x.startswith('--')]; slug, lead, company, url = a[:4]
    d = os.path.join(HERE, 'runs', slug); os.makedirs(d, exist_ok=True); t0 = time.time()
    res = {'slug': slug, 'company': company, 'model': MODEL, 'model_calls': 0, 'status': 'crash'}
    try:
        if '--no-facts' in sys.argv and os.path.exists(os.path.join(d, 'facts.txt')):
            facts = open(os.path.join(d, 'facts.txt'), encoding='utf-8').read(); meta = json.load(open(os.path.join(d, 'facts.json'), encoding='utf-8'))
        else:
            import facts as F; meta, facts = F.run(slug, lead, company, url)
        market, facts = compact(facts, slug)
        open(os.path.join(d, 'facts_model.txt'), 'w', encoding='utf-8').write(facts)
        system = open(os.path.join(HERE, 'PROMPT.md'), encoding='utf-8').read()
        res['model_calls'] = 1
        text, ti, to = call(system, facts); res.update(tokens_in=ti, tokens_out=to)
        open(os.path.join(d, 'raw.txt'), 'w', encoding='utf-8').write(text)
        try:
            sp, warn = validate(text, facts)
        except Exception as e:
            res.update(status='failed', error='validation: ' + str(e)[:200], seconds=int(time.time() - t0))
            json.dump(res, open(os.path.join(d, 'result.json'), 'w'), indent=1); print(json.dumps(res)); sys.exit(2)
        first = lead.split()[0] if lead.split() else 'you'
        spec = {'slug': slug, 'company': company, 'first_name': first, 'domain': re.sub(r'^https?://(www\.)?', '', url).split('/')[0],
                'shot': meta.get('shot') or '', 'logo': meta.get('logo') or '',
                'market': market or {}, 'market_line': sp['market_line'],
                'cover_sub': sp['cover_sub'], 'offer_tail': sp['offer_tail']}
        json.dump(spec, open(os.path.join(SRC, 'specs', slug + '.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        import build
        out = build.render(spec); dd = os.path.join(ROOT, slug); os.makedirs(dd, exist_ok=True)
        open(os.path.join(dd, 'index.html'), 'w', encoding='utf-8', newline='\n').write(out)
        res.update(status='built', warnings=warn, seconds=int(time.time() - t0), shot=bool(spec['shot']), logo=bool(spec['logo']))
        json.dump(res, open(os.path.join(d, 'result.json'), 'w'), indent=1); print(json.dumps(res))
    except SystemExit: raise
    except Exception as e:
        res.update(error=str(e)[-300:], seconds=int(time.time() - t0)); json.dump(res, open(os.path.join(d, 'result.json'), 'w'), indent=1); print(json.dumps(res)); sys.exit(1)

if __name__ == '__main__': main()
