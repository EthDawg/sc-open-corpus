"""The written test for a run: a buyer's questionnaire with traps, rendered from keys/<org>/questionnaire-spec.json by
Green Room's own rfpgen, and its score.

  <green-room>/.venv/bin/python tools/written.py make <org>              -> deliveries/<org>/questionnaire/<file> (what a run answers)
                                                                           keys/<org>/questionnaire-written-key.md (never in a workspace)
  <green-room>/.venv/bin/python tools/written.py score <workspace> <org> -> traps handled, other questions agreeing, risky answers

The score is Green Room's own (respond.score): a trap is handled or not and counts three times; a risky answer is one
given where the key sends the question to a person, or a Yes where the key says No.
"""
import os, sys, json, glob, shutil, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from greenroom_path import APP
sys.path.insert(0, APP)
J = lambda *p: os.path.join(ROOT, *p)
LAYOUT = {'atlassian': ('xlsx', 'tabs'), 'stripe': ('docx', 'tables'), 'anthropic': ('xlsx', 'register'), 'openai': ('docx', 'numbered'),
          'microsoft': ('xlsx', 'schedule'), 'gitlab': ('xlsx', 'register'), 'posthog': ('docx', 'tables'), 'supabase': ('xlsx', 'tabs')}


def spec_of(org):
    s = json.load(open(J('keys', org, 'questionnaire-spec.json')))
    for sec in s['sections']:
        for q in sec['questions']:
            for k in ('source', 'quote'): (q.get('key') or {}).pop(k, None)
    return s


def make(org):
    from greenroom import rfpgen
    spec = spec_of(org); fmt, layout = LAYOUT.get(org, ('xlsx', 'tabs'))
    tmp = tempfile.mkdtemp(); r = rfpgen.render(spec, fmt, tmp, layout=layout)
    qd = J('deliveries', org, 'questionnaire'); os.makedirs(qd, exist_ok=True)
    dst = os.path.join(qd, os.path.basename(r['path'])); shutil.copy2(r['path'], dst)
    open(J('keys', org, 'questionnaire-written-key.md'), 'w').write(rfpgen.key_md(spec, r['anchors'], spec['title']))
    n = sum(len(s['questions']) for s in spec['sections'])
    traps = sum(1 for s in spec['sections'] for q in s['questions'] if (q.get('key') or {}).get('trap') or (q.get('key') or {}).get('route_to'))
    print(f'{org}: {dst} · {n} questions, {traps} traps · key in keys/{org}/questionnaire-written-key.md')


def score(ws_root, org):
    os.environ.setdefault('GREENROOM_NO_OPEN', '1')
    from greenroom import respond as R
    files = glob.glob(os.path.join(ws_root, 'engagements', '*', 'respond', '*', 'answers.md'))
    key = R.as_answers(None, None, path=J('keys', org, 'questionnaire-written-key.md')); kid = {k['id'] for k in key}
    best = None
    for f in files:
        got = R.as_answers(None, None, path=f)
        if best is None or len({g['id'] for g in got} & kid) > len({g['id'] for g in best} & kid): best = got
    if not best: return {'note': 'no answers.md found'}
    s = R.score(best, key)
    out = {k: s[k] for k in ('score', 'of', 'n', 'traps', 'traps_handled', 'traps_partial', 'others', 'agree', 'risky', 'over_route', 'missing')}
    out['rows'] = [{'id': r['id'], 'trap': r['trap'], 'ok': r['ok'], 'why': r['why'], 'got': (r['got'] or {}).get('answer') if r['got'] else None,
                    'status': (r['got'] or {}).get('status') if r['got'] else None, 'key': r['key']['answer']} for r in s['rows']]
    return out


if __name__ == '__main__':
    if sys.argv[1] == 'make': make(sys.argv[2])
    else:
        o = score(sys.argv[2], sys.argv[3]); print(json.dumps({k: v for k, v in o.items() if k != 'rows'}, indent=1))
        for r in o.get('rows', []):
            if r['trap'] or r['ok'] is not True: print(' ', r['id'], r['trap'] or '-', r['ok'], '|', r['why'], '| got', repr(r['got']), '| key', repr(r['key']))
        if len(sys.argv) > 4: json.dump(o, open(sys.argv[4], 'w'), indent=1, default=str)
