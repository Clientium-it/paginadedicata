# nice() and SHORT copied from c18_batch.py, importable without running a batch
import re
LOW = set('di e ed per del della dello dei degli delle il la le lo gli a al alla ai alle da dal dalla in con su tra fra and the of for'.split())
SHORT = {'bertolotti-soc-per-az-impianti-per-l-industria-siderurgica-e-mineraria': 'Bertolotti',   # register names too long for the cover
         'i-c-m-a-san-giorgio-industria-costruzioni-macchine-e-affini': 'I.C.M.A. San Giorgio',
         'si': 'SISAS',
         'emerson-automation-fluid-control-pneumatics-italy': 'Emerson Automation'}   # register name 'SI', the messages say SISAS
def nice(name):
    """display casing for names from the business register: only mechanical fixes, never new words"""
    n = re.sub(r"[- ]+societa' per azioni$", '', name.strip(), flags=re.I)
    n = re.sub(r"\s+Soc\. Coop\..*$", '', n)
    n = re.sub(r"([aeiou])'(?=\s|$)", lambda m: {'a': 'à', 'e': 'è', 'i': 'ì', 'o': 'ò', 'u': 'ù'}[m.group(1)], n)
    out = []
    for i, w in enumerate(n.split()):
        if i and w.lower() in LOW: w = w.lower()
        elif i and w.isupper() and w.lower() in ('vie', 'and', 'the'): w = w.capitalize() if w.lower() == 'vie' else w.lower()
        if w[:1].isupper(): w = re.sub(r"(?<=[-'])([a-zà-ù])", lambda m: m.group(1).upper(), w)   # mc-link stays as the brand writes it
        if i and re.match(r"(L|D|Dell|Nell|All|Sull|Dall)'", w): w = w[0].lower() + w[1:]
        out.append(w)
    return ' '.join(out)
