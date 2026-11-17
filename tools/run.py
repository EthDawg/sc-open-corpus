"""One run of the AI step, by PROTOCOL.md: a fresh Green Room home, delivery d1 in the inbox, intake, then respond on the
org's questionnaire(s). Later deliveries load with a fresh agent and nothing but the workspace.

  <green-room>/.venv/bin/python tools/run.py <org> [--arm greenroom|thin|bare] [--model opus] [--deliveries d1,d2]
      [--skip-respond] [--run <existing run folder, to add a delivery>]

Writes runs/<date>-<org>-<arm>-<model>/ : home/ (GREENROOM_HOME), log-*.jsonl, run.json (time, cost, results per step).
The keys/ folder is passed to Green Room as forbidden: any read of it is reported as a leak and voids the run.
"""
import os, sys, json, time, shutil, datetime, glob, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from greenroom_path import APP
J = lambda *p: os.path.join(ROOT, *p)
args = sys.argv[1:]
opt = lambda k, d=None: args[args.index(k) + 1] if k in args else d
org = args[0]; arm = opt('--arm', 'greenroom'); model = opt('--model', 'opus')
dels = opt('--deliveries', 'd1').split(',')
run = opt('--run') or J('runs', f"{datetime.date.today().isoformat()}-{org}-{arm}-{model.replace('[', '').replace(']', '')}")
home = os.path.join(run, 'home')
os.makedirs(home, exist_ok=True)
os.environ['GREENROOM_HOME'] = home
os.environ['GREENROOM_TRASH'] = os.path.join(run, 'trash')
os.environ['GREENROOM_NO_OPEN'] = '1'
sys.path.insert(0, APP)
from greenroom import workspace as W, intake, respond as R, engagements as E  # noqa: E402

orgs = {o['slug']: o for o in json.load(open(J('catalog', 'orgs.json')))['orgs']}
name = orgs[org]['name']
state = json.load(open(os.path.join(run, 'run.json'))) if os.path.exists(os.path.join(run, 'run.json')) else \
    {'org': org, 'arm': arm, 'model': model, 'started': datetime.datetime.now().isoformat(timespec='seconds'), 'steps': []}
save = lambda: json.dump(state, open(os.path.join(run, 'run.json'), 'w'), indent=1, default=str)
# every other run is forbidden one by one: this run's own workspace lives under runs/, and a deny on runs/ itself
# would stop the harness reading its own workspace (it did, on the first thin run)
FORBID = [J('keys'), J('library'), J('catalog'), J('text'), J('raw')] + \
    [J('runs', d) for d in sorted(os.listdir(J('runs'))) if os.path.isdir(J('runs', d)) and os.path.abspath(J('runs', d)) != os.path.abspath(run)]


def ev_logger(path):
    f = open(path, 'a')
    def show(e):
        f.write(json.dumps(e, default=str) + '\n'); f.flush()
        if e.get('type') == 'assistant':
            for c in e.get('message', {}).get('content', []):
                if c.get('type') == 'tool_use':
                    i = c.get('input', {})
                    print(time.strftime('%H:%M:%S'), c['name'], str(i.get('file_path') or i.get('command') or i.get('url') or '')[:120].replace('\n', ' '), flush=True)
    return show


GR = arm in ('greenroom', 'thin')     # thin: Green Room's own jobs, run with this corpus's thin skills (thin/skills) in the workspace
if GR:
    if W.slugify(name) not in W.all_workspaces():          # the same before-AI workspace build_workspaces makes, minus the key
        sys.path.insert(0, os.path.join(ROOT, 'tools')); import build_workspaces as BW
        BW.build(org, write=False, pack=False)
        for f in os.listdir(os.path.join(W.get(W.slugify(name)).root, 'inbox')): os.remove(os.path.join(W.get(W.slugify(name)).root, 'inbox', f))
    ws = W.get(W.slugify(name)); root = ws.root
    if arm == 'thin':
        for sk in sorted(os.listdir(J('thin', 'skills'))):
            shutil.copytree(J('thin', 'skills', sk), os.path.join(root, 'skills', sk), dirs_exist_ok=True)
else:
    root = os.path.join(home, 'workspaces', W.slugify(name)); os.makedirs(os.path.join(root, 'inbox'), exist_ok=True)

for d in dels:
    if any(s['step'] == f'intake-{d}' for s in state['steps']): continue
    src = J('deliveries', org, d)
    for f in os.listdir(src): shutil.copy2(os.path.join(src, f), os.path.join(root, 'inbox', f))
    t0 = time.time(); log = os.path.join(run, f'log-intake-{d}.jsonl')
    if GR:
        r = intake.intake(ws, on_event=ev_logger(log), model=model, timeout=5400, log_path=log + '.raw', forbid_paths=FORBID)
        step = {'step': f'intake-{d}', 'seconds': round(time.time() - t0), 'cost_usd': r.get('cost_usd'), 'landed': r.get('landed'),
                'uncertain': r.get('uncertain'), 'needs_person': r.get('needs_person'), 'ok': r.get('ok'),
                'problems': len(r.get('problems') or []), 'leaks': r.get('leaks')}
    else:
        prompt = (f"This folder's inbox has everything our sales team has on {name}. Load it so we can answer security "
                  "questionnaires and build decks from it." + ("" if d == 'd1' else " The inbox has new material since the last load."))
        p = subprocess.run(['claude', '-p', prompt, '--model', model, '--output-format', 'json', '--permission-mode', 'acceptEdits',
                            '--allowedTools', 'Read,Write,Edit,Glob,Grep,Bash,WebFetch'], cwd=root, capture_output=True, text=True, timeout=5400)
        open(log, 'w').write(p.stdout)
        try: j = json.loads(p.stdout); step = {'step': f'intake-{d}', 'seconds': round(time.time() - t0), 'cost_usd': j.get('total_cost_usd'), 'result': j.get('result', '')[-1200:]}
        except Exception: step = {'step': f'intake-{d}', 'seconds': round(time.time() - t0), 'error': (p.stdout + p.stderr)[-1200:]}
    state['steps'].append(step); save(); print(json.dumps(step, indent=1, default=str))

if '--skip-respond' not in args and GR:
    qdir = J('deliveries', org, 'questionnaire')
    for qf in sorted(glob.glob(os.path.join(qdir, '*'))):
        stepname = 'respond-' + os.path.basename(qf)
        if any(s['step'] == stepname for s in state['steps']): continue
        qn = R.start(ws, qf)
        t0 = time.time(); log = os.path.join(run, f'log-{stepname}.jsonl')
        r = R.draft(ws, qn, model=model, timeout=5400, on_event=ev_logger(log), log_path=log + '.raw', forbid=FORBID)
        step = {'step': stepname, 'questionnaire': qn, 'seconds': round(time.time() - t0), 'cost_usd': r.get('cost_usd'),
                'counts': r.get('counts'), 'leaks': r.get('leaks'), 'ok': r.get('ok')}
        state['steps'].append(step); save(); print(json.dumps(step, indent=1, default=str))

state['finished'] = datetime.datetime.now().isoformat(timespec='seconds')
state['cost_usd'] = round(sum(s.get('cost_usd') or 0 for s in state['steps']), 2)
state['seconds'] = sum(s.get('seconds') or 0 for s in state['steps'])
state['workspace'] = root; save()
print('run:', run, 'cost', state['cost_usd'], 'seconds', state['seconds'])
