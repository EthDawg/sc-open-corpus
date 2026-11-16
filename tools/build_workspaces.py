"""Make each org's BEFORE-AI Green Room workspace (v3 contract) in this corpus's own data root, and pack it.

  GREENROOM_HOME=~/Developer/sc-open-corpus/greenroom-home GREENROOM_NO_OPEN=1 \
    <green-room>/.venv/bin/python tools/build_workspaces.py [org ...] [--no-write] [--no-pack]

Per workspace: workspace.yaml (name, website, brand, as_of), inbox/ = delivery d1 exactly (the library's zip export,
the answer library's Excel export, links.txt), nothing learned; products/catalogue.yaml from library/<org>/catalogue.yaml;
team/people.yaml; engagements/Practice/engagement.yaml; and engagements/Practice/write/<name>/ = the written test
questionnaire rendered by Green Room's own rfpgen from keys/<org>/questionnaire-spec.json, with key.md (left out with
--no-write, for blind learns: the key must not be readable during a learn). Then `gr check`, then `gr ws pack`.
Green Room's code is imported read-only; nothing is written outside GREENROOM_HOME.
"""
import os, sys, json, shutil, datetime, subprocess, copy
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from greenroom_path import APP
J = lambda *p: os.path.join(ROOT, *p)
assert os.environ.get('GREENROOM_HOME', '').startswith(ROOT), 'Set GREENROOM_HOME to this corpus (greenroom-home), never ~/Green Room'
os.environ.setdefault('GREENROOM_NO_OPEN', '1')
sys.path.insert(0, APP)
from greenroom import workspace as W, engagements as E, rfpgen  # noqa: E402

AS_OF = '2026-11-16'
LAYOUT = {'atlassian': ('xlsx', 'tabs'), 'stripe': ('docx', 'tables'), 'anthropic': ('xlsx', 'register'), 'openai': ('docx', 'numbered'),
          'microsoft': ('xlsx', 'schedule'), 'gitlab': ('xlsx', 'register'), 'posthog': ('docx', 'tables'), 'supabase': ('xlsx', 'tabs')}


def strip_key(spec):
    s = copy.deepcopy(spec)
    for sec in s['sections']:
        for q in sec['questions']:
            for k in ('source', 'quote'): (q.get('key') or {}).pop(k, None)
    return s


def add_written(w, org):
    """The written test questionnaire + key.md, rendered by Green Room's own rfpgen. Add only after a learn."""
    if not os.path.exists(J('keys', org, 'questionnaire-spec.json')): return None
    spec = strip_key(json.load(open(J('keys', org, 'questionnaire-spec.json'))))
    fmt, layout = LAYOUT.get(org, ('xlsx', 'tabs'))
    name = W.slugify(spec['title'])[:48]
    d = os.path.join(w.root, 'engagements', 'Practice', 'write', name); os.makedirs(os.path.join(d, '.work'), exist_ok=True)
    r = rfpgen.render(spec, fmt, d, layout=layout)
    open(os.path.join(d, 'key.md'), 'w').write(rfpgen.key_md(spec, r['anchors'], spec['title']))
    json.dump(spec, open(os.path.join(d, '.work', 'spec.json'), 'w'), indent=1)
    traps = sum(1 for s in spec['sections'] for q in s['questions'] if (q.get('key') or {}).get('trap'))
    json.dump({'title': spec['title'], 'buyer': spec.get('buyer'), 'type': spec.get('kind'), 'format': fmt, 'layout': r['layout'],
               'questions': rfpgen.count(spec), 'routed': sum(1 for s in spec['sections'] for q in s['questions'] if (q.get('key') or {}).get('route_to')),
               'traps': traps, 'made': datetime.datetime.now().isoformat(timespec='minutes'), 'file': os.path.basename(r['path']),
               'written_by': 'SC Open Corpus (keys from the sources, not from this workspace)'},
              open(os.path.join(d, '.work', 'meta.json'), 'w'), indent=1)
    return d


def build(org, write=True, pack=True):
    O = {o['slug']: o for o in json.load(open(J('catalog', 'orgs.json')))['orgs']}[org]
    slug = W.slugify(O['name'])
    if slug in W.all_workspaces():
        old = W.get(slug).root; dst = os.path.join(os.environ['GREENROOM_HOME'], 'trash', f"{slug}-{datetime.datetime.now():%Y%m%d-%H%M%S}")
        os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.move(old, dst)
    w = W.create(O['name'], website=O.get('website'), accent=O.get('accent'))
    man = yaml.safe_load(open(os.path.join(w.root, 'workspace.yaml')))
    man['as_of'] = AS_OF; man['brand'] = {'name': O['name'], 'colors': {'accent': O.get('accent', '3B6FD8')}}
    yaml.safe_dump(man, open(os.path.join(w.root, 'workspace.yaml'), 'w'), sort_keys=False, allow_unicode=True)
    E.practice(w)
    for f in sorted(os.listdir(J('deliveries', org, 'd1'))): shutil.copy2(J('deliveries', org, 'd1', f), os.path.join(w.root, 'inbox', f))
    cat = J('library', org, 'catalogue.yaml')
    if os.path.exists(cat): shutil.copy2(cat, w.path('products'))
    if write: add_written(w, org)
    chk = subprocess.run([os.path.join(APP, 'greenroom', 'gr'), 'check', w.root], capture_output=True, text=True, env=os.environ)
    line = (chk.stdout.strip().splitlines() or [''])[-1]
    out = W.pack(slug) if pack else None
    print(f"{org}: {w.root} · inbox {len(os.listdir(os.path.join(w.root, 'inbox')))} files · check: {line} · pack: {out}")
    return chk.returncode


if __name__ == '__main__':
    a = sys.argv[1:]; orgs = [x for x in a if not x.startswith('--')]
    rc = 0
    if '--add-written' in a:
        for o in orgs:
            O = {x['slug']: x for x in json.load(open(J('catalog', 'orgs.json')))['orgs']}[o]; w = W.get(W.slugify(O['name']))
            print(o, add_written(w, o)); subprocess.run([os.path.join(APP, 'greenroom', 'gr'), 'check', w.root], env=os.environ)
        sys.exit(0)
    for o in orgs or [o['slug'] for o in json.load(open(J('catalog', 'orgs.json')))['orgs'] if os.path.isdir(J('deliveries', o['slug']))]:
        rc |= build(o, write='--no-write' not in a, pack='--no-pack' not in a)
    sys.exit(rc)
