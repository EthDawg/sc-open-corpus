"""Make the shareable repository: everything VISION.md allows in public, nothing else.

  python3 tools/public_cut.py [out_dir]        default ~/Developer/sc-open-corpus-public

Copies: the docs, tools, portal source and catalog metadata; openly licensed originals (raw/); fixtures and keys
whose every quoted source is openly licensed; runs only for openly licensed orgs. Never copies the data root,
deliveries, text cache, private originals or anything that names a term on the local deny list
(tools/denylist.py). Ends with a full scan of the output and refuses (exit 1) on any hit.
"""
import os, sys, json, shutil, glob, re, tarfile, zipfile, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import denylist as DENY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else '~/Developer/sc-open-corpus-public'))
J = lambda *p: os.path.join(ROOT, *p)
TS = DENY.terms()
if not TS: sys.exit('No deny list on this machine (~/.config/sc-open-corpus/denylist.txt): refusing to make a public cut.')
if os.path.exists(OUT) and not os.path.exists(os.path.join(OUT, '.sc-open-corpus-public')):
    sys.exit(f'{OUT} exists and is not a previous public cut: refusing to overwrite it.')
keep_git = os.path.join(OUT, '.git')
for x in (os.listdir(OUT) if os.path.exists(OUT) else []):
    if x != '.git': p = os.path.join(OUT, x); shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
os.makedirs(OUT, exist_ok=True); open(os.path.join(OUT, '.sc-open-corpus-public'), 'w').write('made by tools/public_cut.py\n')

cat = json.load(open(J('catalog', 'sources.json')))
src = {r['id']: r for r in cat['sources']}
clean_txt = lambda rid: not DENY.file_hit(J('text', rid + '.txt'), TS)
open_ok = lambda rid: bool(src.get(rid, {}).get('redistributable')) and clean_txt(rid)

def cp(rel):
    s = J(rel); d = os.path.join(OUT, rel); os.makedirs(os.path.dirname(d), exist_ok=True)
    shutil.copytree(s, d) if os.path.isdir(s) else shutil.copy2(s, d)

# 1. docs, code, portal source
for f in ['README.md', 'VISION.md', 'AGENTS.md', 'CLAUDE.md', 'LICENSE', 'LICENSE-CONTENT.md', 'docs/SOURCES.md', 'docs/notes-for-agents.md', 'DESIGN.md', 'PROTOCOL.md', 'HARVEST.md', 'library/AUTHORING.md', 'library/QUESTIONNAIRE.md', 'catalog/orgs.json']:
    if os.path.exists(J(f)): cp(f)
for f in glob.glob(J('tools', '*.py')): cp(os.path.relpath(f, ROOT))
cp('portals/src'); cp('portals/build.py'); cp('portals/serve.sh')
open(os.path.join(OUT, '.gitignore'), 'w').write(open(J('.gitignore')).read())

# 2. catalog: metadata for every original that names nothing denied (URL + hash is how private files are shared)
recs = [r for r in cat['sources'] if not DENY.hit(json.dumps(r), TS) and clean_txt(r['id'])]
failed = [f for f in cat.get('failed', []) if not DENY.hit(json.dumps(f), TS)]
os.makedirs(os.path.join(OUT, 'catalog'), exist_ok=True)
json.dump({**{k: v for k, v in cat.items() if k not in ('sources', 'failed')}, 'count': len(recs), 'sources': recs, 'failed': failed},
          open(os.path.join(OUT, 'catalog', 'sources.json'), 'w'), indent=1, ensure_ascii=False)
for r in recs:                                  # 3. openly licensed originals, byte for byte
    if open_ok(r['id']): cp(r['file'])

# 4. fixtures and keys: keep an entry only if every source it quotes is open and nothing in it is denied
def sources_in(o):
    if isinstance(o, dict):
        for k in ('source', 'raw', 'old_source', 'file_raw'):
            if isinstance(o.get(k), str) and o.get(k): yield o[k].split('#')[0]
        for v in o.values(): yield from sources_in(v)
    elif isinstance(o, list):
        for v in o: yield from sources_in(v)
def keep(o): return not DENY.hit(json.dumps(o), TS) and all(open_ok(s) for s in sources_in(o) if s in src)
kept = {}
for p in sorted(glob.glob(J('keys', '**', '*.json'), recursive=True) + glob.glob(J('library', '*', 'authored', '*.json')) + glob.glob(J('library', '*', 'split.json'))):
    d = json.load(open(p)); rel = os.path.relpath(p, ROOT)
    if isinstance(d, list): out = [x for x in d if keep(x)]
    elif isinstance(d, dict) and isinstance(d.get('entries'), list): out = {**d, 'entries': [x for x in d['entries'] if keep(x)]}
    elif isinstance(d, dict) and isinstance(d.get('items'), list): out = {**d, 'items': [x for x in d['items'] if keep(x)]}
    elif isinstance(d, dict) and isinstance(d.get('rows'), list): out = {**d, 'rows': [x for x in d['rows'] if keep(x)]} if keep({k: v for k, v in d.items() if k != 'rows'}) else None
    elif isinstance(d, dict) and isinstance(d.get('opportunities'), list):
        out = {**d, 'opportunities': [{**o, 'qa': [q for q in o.get('qa', []) if keep(q)], 'documents': [x for x in o['documents'] if open_ok(x['raw'])]}
                                      for o in d['opportunities'] if not DENY.hit(json.dumps({k: o.get(k) for k in ('title', 'summary', 'buyer')}), TS)
                                      and all(open_ok(x['raw']) for x in o['documents'])]}
    elif isinstance(d, dict) and isinstance(d.get('sections'), list):
        # a written questionnaire: keep each question whose sources are all open (or that names none: a question for a person)
        secs = [{**sec, 'questions': [q for q in sec['questions'] if keep(q)]} for sec in d['sections']]
        secs = [sec for sec in secs if sec['questions']]
        out = {**d, 'sections': secs} if sum(len(x['questions']) for x in secs) >= 8 and keep({k: v for k, v in d.items() if k != 'sections'}) else None
    else: out = d if keep(d) else None
    n = len(out) if isinstance(out, list) else len(next((v for k, v in (out or {}).items() if isinstance(v, list)), []) or [])
    if out and n:
        dst = os.path.join(OUT, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
        json.dump(out, open(dst, 'w'), indent=1, ensure_ascii=False); kept[rel] = n

# 4b. the thin skills, and packs: finished workspaces made only from the open deliveries a public cut can build itself
if os.path.isdir(J('thin')): cp('thin')
if os.path.isdir(J('packs')): cp('packs')

# 5. runs on openly licensed orgs only (a run's workspace paraphrases its inputs)
open_orgs = {o for o in {r['org'] for r in cat['sources']} if all(r['redistributable'] for r in cat['sources'] if r['org'] == o)}
for d in glob.glob(J('runs', '*')):
    org = next((o for o in open_orgs if f'-{o}-' in os.path.basename(d)), None)
    if org and os.path.isdir(d): cp(os.path.relpath(d, ROOT))
if os.path.exists(J('runs', 'RESULTS.md')): cp('runs/RESULTS.md')

# 6. scan everything, including inside archives and office files; refuse on any hit
def scan_bytes(name, b):
    if name.endswith('.pdf'):
        t = subprocess.run(['pdftotext', '-', '-'], input=b, capture_output=True).stdout.decode('utf-8', 'replace'); return DENY.hit(t, TS)
    if name.endswith(('.pptx', '.docx', '.xlsx', '.zip')) or b[:2] == b'PK':
        try:
            import io; z = zipfile.ZipFile(io.BytesIO(b)); return any(scan_bytes(n, z.read(n)) for n in z.namelist())
        except zipfile.BadZipFile: pass
    if b[:2] == b'\x1f\x8b':
        import io
        try:
            with tarfile.open(fileobj=io.BytesIO(b)) as tf:
                return any(scan_bytes(m.name, tf.extractfile(m).read()) for m in tf.getmembers() if m.isfile())
        except tarfile.TarError: pass
    return DENY.hit(b.decode('utf-8', 'replace'), TS)
hits = []
for d, dirs, fs in os.walk(OUT):
    dirs[:] = [x for x in dirs if x != '.git']
    for f in fs:
        p = os.path.join(d, f)
        if f.endswith(('.png', '.jpg')): continue
        if p.endswith('tools/denylist.py'): continue
        if scan_bytes(f, open(p, 'rb').read()): hits.append(os.path.relpath(p, OUT))
if hits: print('REFUSED: deny-listed terms in', hits[:20]); sys.exit(1)
mb = sum(os.path.getsize(os.path.join(d, f)) for d, ds, fs in os.walk(OUT) for f in fs if '.git' not in d) / 1e6
print(f"public cut: {OUT} · {len(recs)} catalog records · {sum(1 for r in recs if open_ok(r['id']))} open originals · "
      f"{len(kept)} fixture/key files · {mb:.0f} MB · scan clean")
for k, v in kept.items(): print(f'  {k}: {v}')
