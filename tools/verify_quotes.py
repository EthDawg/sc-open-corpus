"""Every quote in the answer keys and authored fixtures must appear verbatim (whitespace and quote-mark normalised)
in the cached text of the source it names. Prints each miss; exit 1 if any.

  python3 tools/verify_quotes.py [org ...]
"""
import json, os, sys, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_cache = {}


def norm(s):
    s = s.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    s = s.replace('–', '-').replace('—', '-').replace(' ', ' ').replace('­', '').replace('\u200b', '').replace('\ufeff', '')
    s = re.sub(r'-\s*\n\s*', '-', s)
    return re.sub(r'\s+', ' ', s).strip().lower()


def text(sid):
    if sid not in _cache:
        p = os.path.join(ROOT, 'text', sid + '.txt')
        _cache[sid] = norm(open(p, encoding='utf-8', errors='replace').read()) if os.path.exists(p) else None
    return _cache[sid]


def quotes(obj, where=''):
    """Yield (where, source, quote) from any nested structure with {source|evidence, quote}."""
    if isinstance(obj, dict):
        if obj.get('quote') and isinstance(obj.get('quote'), str) and (obj.get('source') or obj.get('raw')):
            yield where, str(obj.get('source') or obj.get('raw')).split('#')[0], obj['quote']
        for k, v in obj.items(): yield from quotes(v, f"{where}/{obj.get('id', k)}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj): yield from quotes(v, f'{where}[{i}]')


def check_file(p):
    bad = ok = 0
    for where, sid, q in quotes(json.load(open(p))):
        t = text(sid)
        if t is None: print(f'MISS-SRC {os.path.relpath(p, ROOT)} {where}: no text for {sid}'); bad += 1; continue
        if norm(q) in t: ok += 1
        else: print(f'NOT-FOUND {os.path.relpath(p, ROOT)} {where} [{sid}]: {q[:110]!r}'); bad += 1
    return ok, bad


def main():
    orgs = sys.argv[1:] or ['*']
    tot_ok = tot_bad = 0
    for o in orgs:
        for p in sorted(glob.glob(os.path.join(ROOT, f'keys/{o}/**/*.json'), recursive=True) + glob.glob(os.path.join(ROOT, f'library/{o}/authored/*.json'))):
            ok, bad = check_file(p); tot_ok += ok; tot_bad += bad
    print(f'{tot_ok} quotes verified, {tot_bad} not found')
    sys.exit(1 if tot_bad else 0)


if __name__ == '__main__':
    main()
