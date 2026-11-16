"""Refresh the corpus from the live web: the next real delivery.

  python3 tools/refresh.py [--org gitlab] [--dry-run]

For every original with a URL (repos and Google exports excepted; re-run their harvest steps by hand), fetch it again
with plain curl. Unchanged bytes: nothing. Changed bytes: keep the old file, save the new one as
raw/<org>/<id>-r<YYYYMMDD>.<ext>, append a new record (id <id>-r<YYYYMMDD>, `replaces: <id>`) to
catalog/parts/refresh-<date>.jsonl, and list it in refresh/<date>/changed.json. Refused or gone: refresh/<date>/failed.json.
HTML is compared on its extracted text, so a changed nonce or timestamp doesn't count as a change.
Then: python3 tools/catalog.py && python3 tools/extract.py, author the changes keys for the new delivery (library/AUTHORING.md §5)
and add the new ids to library/<org>/split.json as the next delivery.
"""
import json, os, sys, subprocess, hashlib, datetime, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract import html_text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda *p: os.path.join(ROOT, *p)


def main():
    args = sys.argv[1:]; org = args[args.index('--org') + 1] if '--org' in args else None; dry = '--dry-run' in args
    today = datetime.date.today(); tag = today.strftime('%Y%m%d')
    cat = json.load(open(J('catalog', 'sources.json')))['sources']
    latest = {}
    for r in cat: latest[r.get('replaces') or r['id']] = r      # newest record per original lineage (sorted by id)
    out = J('refresh', today.isoformat()); os.makedirs(out, exist_ok=True)
    changed, failed, same = [], [], 0
    for base, r in sorted(latest.items()):
        if org and r['org'] != org: continue
        if r['kind'] == 'repo' or '/export/' in r['url'] or not r['url'].startswith('http'): continue
        tmp = os.path.join(out, 'tmp'); os.makedirs(tmp, exist_ok=True); f = os.path.join(tmp, 'f')
        p = subprocess.run(['curl', '-sSL', '--max-time', '120', '-o', f, '-w', '%{http_code}', r['url']], capture_output=True, text=True)
        code = p.stdout.strip()
        if code != '200' or not os.path.exists(f):
            failed.append({'id': r['id'], 'url': r['url'], 'http': code, 'error': p.stderr[-200:]}); continue
        new = open(f, 'rb').read(); old = open(J(r['file']), 'rb').read()
        same_bytes = hashlib.sha256(new).hexdigest() == r['sha256']
        if not same_bytes and r['kind'] == 'html':
            same_bytes = html_text(new) == html_text(old)
        if same_bytes: same += 1; continue
        ext = os.path.splitext(r['file'])[1]; nid = f"{base}-r{tag}"; nf = f"raw/{r['org']}/{nid}{ext}"
        rec = dict(r, id=nid, file=nf, fetched_at=today.isoformat(), sha256=hashlib.sha256(new).hexdigest(), bytes=len(new), replaces=base)
        changed.append({'id': nid, 'replaces': base, 'title': r['title'], 'url': r['url']})
        if not dry:
            open(J(nf), 'wb').write(new)
            with open(J('catalog', 'parts', f'refresh-{today.isoformat()}.jsonl'), 'a') as fh: fh.write(json.dumps(rec) + '\n')
    json.dump(changed, open(os.path.join(out, 'changed.json'), 'w'), indent=1)
    json.dump(failed, open(os.path.join(out, 'failed.json'), 'w'), indent=1)
    print(f'{same} unchanged, {len(changed)} changed, {len(failed)} failed -> {out}')


if __name__ == '__main__':
    main()
