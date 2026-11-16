"""Run Green Room's free evals on each corpus workspace, headless, and write the results beside the workspace packs.

  GREENROOM_HOME=~/Developer/sc-open-corpus/greenroom-home GREENROOM_NO_OPEN=1 \
    <green-room>/.venv/bin/python tools/evals.py [org ...]

Free evals only (cost 'free'); paid ones (blind learn, the written test) run through tools/learn.py and tools/test.py.
Writes runs/evals-<date>.json and prints one line per workspace and eval.
"""
import os, sys, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from greenroom_path import APP
assert os.environ.get('GREENROOM_HOME', '').startswith(ROOT)
os.environ.setdefault('GREENROOM_NO_OPEN', '1')
sys.path.insert(0, APP)
from greenroom import workspace as W  # noqa: E402
from greenroom.evals import all_evals  # noqa: E402

orgs = {o['slug']: o['name'] for o in json.load(open(os.path.join(ROOT, 'catalog', 'orgs.json')))['orgs']}
want = sys.argv[1:] or list(orgs)
out = {}
for org in want:
    slug = W.slugify(orgs[org])
    if slug not in W.all_workspaces(): continue
    w = W.activate(slug); res = {}
    for e in all_evals():
        if e.get('cost') != 'free' or e['id'] in ('knowledge-lifecycle',): continue
        try:
            r = e['run'](w, lambda t: None); res[e['id']] = {'score': r.get('score'), 'of': r.get('of'), 'summary': r.get('summary')}
        except Exception as x:
            res[e['id']] = {'error': f'{type(x).__name__}: {x}'[:300]}
        print(f"{org:10} {e['id']:24} {res[e['id']].get('score', '-')}/{res[e['id']].get('of', '-')}  {res[e['id']].get('summary') or res[e['id']].get('error', '')}"[:220])
    out[org] = res
p = os.path.join(ROOT, 'runs', f'evals-{datetime.date.today().isoformat()}.json'); os.makedirs(os.path.dirname(p), exist_ok=True)
old = json.load(open(p)) if os.path.exists(p) else {}
old.update(out); json.dump(old, open(p, 'w'), indent=1)
