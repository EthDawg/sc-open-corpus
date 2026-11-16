"""Blind learn: run Green Room's own Learn job (knowledge.run_learn, exactly what the app's Learn button runs) on one
workspace in this corpus's data root, headless, and record time, cost and the result.

  GREENROOM_HOME=~/Developer/sc-open-corpus/greenroom-home GREENROOM_NO_OPEN=1 \
    <green-room>/.venv/bin/python tools/learn.py <org> [--model opus]

The workspace must have no write/ test folders (build_workspaces.py --no-write): the key must not be readable.
Writes runs/<date>-<org>-learn/{run.json, progress.log}.
"""
import os, sys, json, time, datetime, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from greenroom_path import APP
assert os.environ.get('GREENROOM_HOME', '').startswith(ROOT), 'GREENROOM_HOME must be this corpus (greenroom-home)'
os.environ.setdefault('GREENROOM_NO_OPEN', '1')
sys.path.insert(0, APP)
from greenroom import workspace as W, knowledge as K  # noqa: E402

org = sys.argv[1]; model = sys.argv[sys.argv.index('--model') + 1] if '--model' in sys.argv else None
name = {o['slug']: o['name'] for o in json.load(open(os.path.join(ROOT, 'catalog', 'orgs.json')))['orgs']}[org]
w = W.get(W.slugify(name))
assert not glob.glob(os.path.join(w.root, 'engagements', '*', 'write', '*', 'key.md')), 'A written key is in the workspace: rebuild with --no-write first'
tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else ''
run = os.path.join(ROOT, 'runs', f"{datetime.date.today().isoformat()}-{org}-learn{('-' + tag) if tag else ''}"); os.makedirs(run, exist_ok=True)
log = open(os.path.join(run, 'progress.log'), 'a')
def progress(t):
    line = f"{time.strftime('%H:%M:%S')} {t}"; print(line, flush=True); log.write(line + '\n'); log.flush()
job = {'id': f'corpus-{org}-{int(time.time())}', 'kind': 'learn', 'params': {'model': model} if model else {}}
t0 = time.time()
try:
    r = K.run_learn(job, w, progress); err = None
except Exception as e:
    import traceback; r = {}; err = traceback.format_exc()
out = {'org': org, 'workspace': w.root, 'model': model or 'default', 'seconds': round(time.time() - t0), 'cost_usd': r.get('cost_usd'),
       'result_md': r.get('result_md'), 'detail': r.get('detail'), 'error': err, 'finished': datetime.datetime.now().isoformat(timespec='seconds')}
json.dump(out, open(os.path.join(run, 'run.json'), 'w'), indent=1, default=str)
print(json.dumps({k: v for k, v in out.items() if k != 'detail'}, indent=1, default=str)[:3000])
