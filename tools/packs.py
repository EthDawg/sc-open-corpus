"""Turn finished runs into packs: one finished company per file, ready to open in Green Room, plus packs/index.json.

  <green-room>/.venv/bin/python tools/packs.py <run folder> [<run folder> ...]

A pack is the run's workspace as a .greenroom file (a zip of the workspace folder), without machine state and logs.
Before a pack is written every text file in it is checked for this machine's home path and user name, and for any
term on the local deny list; a hit stops the build. The index records each pack's bytes, sha256 and what is in it,
so an app can list packs, download one, check it and import it with no paid job.
"""
import os, sys, json, glob, zipfile, hashlib, datetime, getpass, io, re
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import denylist as DENY
J = lambda *p: os.path.join(ROOT, *p)
BASE = 'https://raw.githubusercontent.com/EthDawg/sc-open-corpus/main/packs/'
SKIP_DIRS = {'state', '.git', '__pycache__', 'inbox', 'cache', '.work'}
SKIP_FILES = {'.DS_Store', 'graph.json'}
ME = [getpass.getuser(), os.path.expanduser('~')]


def text_of(name, b):
    if b[:2] == b'PK':
        try:
            z = zipfile.ZipFile(io.BytesIO(b)); return '\n'.join(text_of(n, z.read(n)) for n in z.namelist())
        except zipfile.BadZipFile: pass
    return b.decode('utf-8', 'replace')


def build(run):
    rj = json.load(open(os.path.join(run, 'run.json'))); org = rj['org']
    ws = [w for w in sorted(glob.glob(os.path.join(run, 'home', 'workspaces', '*'))) if os.path.basename(w) != 'tidewell'][0]   # the sample is copied into every new home
    man = yaml.safe_load(open(os.path.join(ws, 'workspace.yaml'))); name = man.get('name') or org
    top = os.path.basename(ws); buf = io.BytesIO(); hits = []; ts = DENY.terms()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for d, dirs, files in os.walk(ws):
            dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
            for f in sorted(files):
                if f in SKIP_FILES or f.endswith(('.lock', '.log', '.raw')): continue
                p = os.path.join(d, f); rel = os.path.join(top, os.path.relpath(p, ws)); b = open(p, 'rb').read()
                t = text_of(f, b)
                if any(m and m in t for m in ME) or re.search(r'/private/tmp/claude|/var/folders/', t): hits.append(('path or user name', rel))   # this machine's paths; a document's own example paths are fine
                if ts and DENY.hit(t, ts): hits.append(('deny list', rel))
                z.writestr(zipfile.ZipInfo(rel, date_time=(2026, 11, 17, 0, 0, 0)), b)
    if hits: sys.exit(f'{org}: refusing to pack, private text found in: ' + '; '.join(f'{k}: {r}' for k, r in hits[:12]))
    os.makedirs(J('packs'), exist_ok=True); out = J('packs', f'{org}.greenroom'); b = buf.getvalue(); open(out, 'wb').write(b)
    idx = json.load(open(os.path.join(ws, 'sources', 'index.json'))) if os.path.exists(os.path.join(ws, 'sources', 'index.json')) else []
    claims = (yaml.safe_load(open(os.path.join(ws, 'knowledge', 'claims.yaml'))) or {}).get('claims', []) if os.path.exists(os.path.join(ws, 'knowledge', 'claims.yaml')) else []
    ans = glob.glob(os.path.join(ws, 'engagements', '*', 'respond', '*', 'answers.md'))
    nq = sum(open(a).read().count('\n## ') for a in ans)
    return {'slug': org, 'name': name, 'file': f'{org}.greenroom', 'url': BASE + f'{org}.greenroom', 'bytes': len(b),
            'sha256': hashlib.sha256(b).hexdigest(), 'shape': man.get('shape') or 3,      # 3: Green Room's workspace shape on 17 Nov 2026
            'summary': f"{len(idx)} sources filed, a {nq}-question buyer questionnaire answered, {len(claims)} facts saved with the sentence each rests on.",
            'licence': 'Originals under their own open licences; everything written for the corpus is CC BY 4.0.',      # shown on screen in Green Room: plain words, no file names
            'made_with': f"Green Room's own jobs with the thin skills in thin/skills, model {rj.get('model')}, {round((rj.get('seconds') or 0) / 60)} min, ${rj.get('cost_usd')} at API list prices.",
            'run': os.path.basename(run)}


if __name__ == '__main__':
    packs = [build(r.rstrip('/')) for r in sys.argv[1:]]
    ip = J('packs', 'index.json'); old = json.load(open(ip))['packs'] if os.path.exists(ip) else []
    keep = [p for p in old if p['slug'] not in {x['slug'] for x in packs}]
    json.dump({'format': 1, 'as_of': datetime.date.today().isoformat(), 'packs': sorted(keep + packs, key=lambda p: p['slug'])}, open(ip, 'w'), indent=1)
    for p in packs: print(p['slug'], p['bytes'], 'bytes', p['sha256'][:12], '|', p['summary'])
