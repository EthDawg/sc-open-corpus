"""Merge harvester parts into catalog/sources.json and check every original.

  python3 tools/catalog.py          merge + check, print problems and a summary, write catalog/STATS.md
  python3 tools/catalog.py --strict exit 1 on any error

Checks: required keys, unique ids, file exists, sha256 and bytes match, kind matches the bytes (magic), HTML has real
text, PDFs give text, licence/redistributable agree, genre and sc_jobs from the allowed lists, nothing on the local deny list.
"""
import json, os, sys, glob, hashlib, subprocess, re, collections, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import denylist as DENY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS = ['id', 'org', 'title', 'kind', 'genre', 'audience', 'url', 'fetched_at', 'published', 'file', 'sha256', 'bytes',
        'pages', 'licence', 'redistributable', 'why', 'sc_jobs']
GENRES = set('handbook playbook value-framework competitive demo-script product-doc security-whitepaper trust-faq '
             'questionnaire-response questionnaire-blank rfx rfx-qa proposal deck release-note deprecation roadmap pricing '
             'case-study investor training system-card policy-legal talk'.split())
JOBS = set('absorb respond present demo discover compete price relearn'.split())
OPEN = {'CC-BY-SA-4.0', 'CC-BY-4.0', 'MIT', 'Apache-2.0', 'OGL-UK-3.0', 'US-PD', 'CC0-1.0', 'CC-BY-3.0', 'CC-BY-SA-3.0'}
MAGIC = {'pdf': [b'%PDF'], 'pptx': [b'PK'], 'xlsx': [b'PK'], 'docx': [b'PK'], 'repo': [b'\x1f\x8b'], 'xls': [b'\xd0\xcf'],
         'doc': [b'\xd0\xcf'], 'ppt': [b'\xd0\xcf']}


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def text_len(p, kind):
    try:
        if kind == 'pdf':
            return len(subprocess.run(['pdftotext', '-l', '5', p, '-'], capture_output=True, timeout=60).stdout.strip())
        if kind == 'html':
            t = open(p, 'rb').read().decode('utf-8', 'replace')
            t = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', t)
            return len(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t)).strip())
        if kind in ('md', 'csv', 'json', 'txt'):
            return len(open(p, 'rb').read().strip())
    except Exception:
        return 0
    return None


def load_parts():
    recs, failed = [], []
    for f in sorted(glob.glob(os.path.join(ROOT, 'catalog/parts/*.jsonl'))):
        track = os.path.basename(f).split('.')[0]
        bucket = failed if f.endswith('.failed.jsonl') else recs
        for i, line in enumerate(open(f, encoding='utf-8')):
            line = line.strip()
            if not line: continue
            try: r = json.loads(line)
            except json.JSONDecodeError as e:
                print(f'ERROR {os.path.basename(f)}:{i+1} bad JSON: {e}'); continue
            r['track'] = track; bucket.append(r)
    return recs, failed


def check(recs, deep=True):
    probs, seen = [], {}
    for r in recs:
        rid = r.get('id', '?')
        for k in KEYS:
            if k not in r: probs.append(('error', rid, f'missing key {k}'))
        if rid in seen: probs.append(('error', rid, 'duplicate id'))
        seen[rid] = r
        if r.get('genre') not in GENRES: probs.append(('warn', rid, f"genre {r.get('genre')!r} not in list"))
        bad = set(r.get('sc_jobs') or []) - JOBS
        if bad: probs.append(('warn', rid, f'sc_jobs not in list: {sorted(bad)}'))
        if r.get('redistributable') and r.get('licence') not in OPEN:
            probs.append(('error', rid, f"redistributable but licence {r.get('licence')!r} is not open"))
        blob = ' '.join(str(r.get(k, '')) for k in ('title', 'url', 'file')) if not r.get('public_hold') else ''
        if DENY.hit(blob): probs.append(('error', rid, 'material on the local deny list is excluded from this repository'))
        p = os.path.join(ROOT, r.get('file') or '')
        if not r.get('file') or not os.path.isfile(p):
            probs.append(('error', rid, f"file missing: {r.get('file')}")); continue
        if not deep: continue
        size = os.path.getsize(p)
        if r.get('bytes') != size: probs.append(('warn', rid, f"bytes {r.get('bytes')} != {size} (fixed)")); r['bytes'] = size
        h = sha(p)
        if r.get('sha256') != h: probs.append(('warn', rid, 'sha256 did not match the file (fixed)')); r['sha256'] = h
        head = open(p, 'rb').read(8)
        mg = MAGIC.get(r.get('kind'))
        if mg and not any(head.startswith(m) for m in mg): probs.append(('error', rid, f"bytes are not a {r.get('kind')}"))
        tl = text_len(p, r.get('kind'))
        if tl is not None and tl < 400 and r.get('stress') != 'scanned' and not r.get('short'): probs.append(('error', rid, f'only {tl} characters of text (empty shell?)'))
    return probs


def main():
    strict = '--strict' in sys.argv
    recs, failed = load_parts()
    ov = json.load(open(os.path.join(ROOT, 'catalog/overrides.json'))) if os.path.exists(os.path.join(ROOT, 'catalog/overrides.json')) else {}
    for r in recs:
        r.update({k: v for k, v in ov.get(r.get('id'), {}).items()})
        if r.get('public_hold'): r['redistributable'] = False
    probs = check(recs)
    recs.sort(key=lambda r: (r.get('org', ''), r.get('id', '')))
    out = {'as_of': max([r.get('fetched_at') or '' for r in recs] or ['']), 'built': datetime.date.today().isoformat(),
           'count': len(recs), 'sources': recs, 'failed': failed}
    json.dump(out, open(os.path.join(ROOT, 'catalog/sources.json'), 'w'), indent=1, ensure_ascii=False)
    by = lambda k: collections.Counter(str(r.get(k)) for r in recs)
    mb = sum(r.get('bytes') or 0 for r in recs) / 1e6
    lines = [f"# Catalog: {len(recs)} originals, {mb:.0f} MB, as of {out['as_of']}", '',
             f"Redistributable: {sum(1 for r in recs if r.get('redistributable'))} · private only: "
             f"{sum(1 for r in recs if not r.get('redistributable'))} · failed fetches recorded: {len(failed)}", '']
    for k in ('org', 'genre', 'kind', 'licence', 'audience'):
        lines += [f'## By {k}', ''] + [f'- {a}: {n}' for a, n in by(k).most_common()] + ['']
    jobs = collections.Counter(j for r in recs for j in r.get('sc_jobs') or [])
    lines += ['## By SC job', ''] + [f'- {a}: {n}' for a, n in jobs.most_common()] + ['']
    open(os.path.join(ROOT, 'catalog/STATS.md'), 'w').write('\n'.join(lines))
    errs = [p for p in probs if p[0] == 'error']
    for lvl, rid, msg in probs: print(f'{lvl.upper():5} {rid:24} {msg}')
    print(f"{len(recs)} originals, {mb:.0f} MB, {len(errs)} errors, {len(probs) - len(errs)} warnings, {len(failed)} failed fetches")
    if strict and errs: sys.exit(1)


if __name__ == '__main__':
    main()
