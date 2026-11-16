"""Rebuild raw/ from the catalog: for the public cut, which ships only openly licensed files.

  python3 tools/fetch.py [--org atlassian]

Fetches every original that is missing on disk with plain curl from its recorded URL. Repos and Google exports are
fetched the same way they were harvested (see the record's `why`). A file whose bytes differ from the recorded sha256
is kept and reported: the page has changed since the corpus date, which is exactly what tools/refresh.py tracks.
"""
import json, os, sys, subprocess, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    org = sys.argv[sys.argv.index('--org') + 1] if '--org' in sys.argv else None
    cat = json.load(open(os.path.join(ROOT, 'catalog', 'sources.json')))['sources']
    got = drift = fail = skip = 0
    for r in cat:
        if org and r['org'] != org: continue
        p = os.path.join(ROOT, r['file'])
        if os.path.exists(p): skip += 1; continue
        if r['kind'] == 'repo': print('REPO (re-run its harvest step):', r['id'], r['url']); fail += 1; continue
        os.makedirs(os.path.dirname(p), exist_ok=True)
        c = subprocess.run(['curl', '-sSL', '--max-time', '120', '-o', p, '-w', '%{http_code}', r['url']], capture_output=True, text=True)
        if c.stdout.strip() != '200': print('FAIL', r['id'], c.stdout.strip(), r['url']); fail += 1; os.path.exists(p) and os.remove(p); continue
        got += 1
        if hashlib.sha256(open(p, 'rb').read()).hexdigest() != r['sha256']: drift += 1; print('CHANGED since corpus date:', r['id'])
    print(f'{got} fetched ({drift} changed since the corpus date), {skip} already here, {fail} failed')


if __name__ == '__main__':
    main()
