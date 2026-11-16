"""After a learn: the two respond tests, headless, through Green Room's own code.

  GREENROOM_HOME=~/Developer/sc-open-corpus/greenroom-home GREENROOM_NO_OPEN=1 <green-room>/.venv/bin/python \
    tools/test.py <org> written            # "Use as a test": the written questionnaire answered blind (key hidden), Green Room's scorer
    tools/test.py <org> vendor-form [N]    # the vendor's own completed CAIQ, blanked: Green Room reads it, then answers a seeded
                                           # sample of N rows (default 60); scored row by row against the vendor's own answers

Results go to runs/<date>-<org>-learn/test-<mode>.json (cost, time, score).
"""
import os, sys, json, glob, time, random, datetime, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from greenroom_path import APP
assert os.environ.get('GREENROOM_HOME', '').startswith(ROOT)
os.environ.setdefault('GREENROOM_NO_OPEN', '1')
sys.path.insert(0, APP); sys.path.insert(0, os.path.join(ROOT, 'tools'))
from greenroom import workspace as W, respond as R  # noqa: E402
FORBID = [os.path.join(ROOT, d) for d in ('keys', 'library', 'catalog', 'text', 'raw', 'runs', 'deliveries')]

org, mode = sys.argv[1], sys.argv[2]
name = {o['slug']: o['name'] for o in json.load(open(os.path.join(ROOT, 'catalog', 'orgs.json')))['orgs']}[org]
w = W.activate(W.slugify(name))
run = sorted(glob.glob(os.path.join(ROOT, 'runs', f'*-{org}-learn')))[-1]
out = {'org': org, 'mode': mode, 'started': datetime.datetime.now().isoformat(timespec='seconds')}
t0 = time.time()
if mode == 'written':
    import build_workspaces as BW
    from greenroom.api import respond as API
    from greenroom.evals import respond as EV
    if not API.written(w): BW.add_written(w, org)
    it = API.written(w)[0]
    r = EV.test_written(w, it['name'], progress=lambda t: print(time.strftime('%H:%M:%S'), t, flush=True))
    out.update({k: r.get(k) for k in ('score', 'of', 'traps', 'traps_handled', 'others', 'agree', 'risky', 'anchors', 'found', 'summary', 'cost_usd')})
    open(os.path.join(run, 'test-written.md'), 'w').write(r.get('detail_md') or '')
elif mode == 'buyer-file':
    # UMaine RFP 2026-065 Appendix H, the buyer's own workbook: Yes / Partial / No per requirement, scored by cell
    key = json.load(open(os.path.join(ROOT, 'keys', 'tenders', 'umaine-appendix-h', f'key-{org}.json')))
    qf = glob.glob(os.path.join(ROOT, 'deliveries', org, 'buyer', '*.xlsx'))[0]
    qn = R.start(w, qf, title='UMaine RFP 2026-065 Appendix H', customer='University of Maine System')
    r = R.draft(w, qn, timeout=5400, forbid=FORBID)
    got = {}
    for e in R.parse(R.answers_path(w, qn)):
        c = ((e.get('anchors') or {}).get('cell') or '').split('+')[0].strip().replace("'", '')
        if c: got[c] = e
    code = lambda v: (v or '').strip().lower().rstrip('.').split()[0] if (v or '').strip() else ''
    rows = []
    for k in key['rows']:
        e = got.get(k['cell']); g = code(R.split_body(e['body'])[0]) if e and e.get('body') else ''
        want = k['vendor_answer'].lower()
        if want == 'unknown': v = 'routed-ok' if not g or (e and str(e.get('status', '')).startswith('needs-person')) else ('overclaim' if g == 'yes' else 'answered-unknown')
        elif not g: v = 'routed'
        elif g == want: v = 'agree'
        elif g == 'yes': v = 'overclaim'
        else: v = 'disagree'
        rows.append({'id': k['id'], 'cell': k['cell'], 'want': want, 'got': g, 'verdict': v})
    from collections import Counter
    out.update({'questionnaire': qn, 'cost_usd': r.get('cost_usd'), 'rows': len(rows), 'verdicts': dict(Counter(x['verdict'] for x in rows)),
                'leaks': r.get('leaks'), 'detail': rows})
else:
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    qf = glob.glob(os.path.join(ROOT, 'deliveries', org, 'questionnaire', '*.xlsx'))[0]
    qn = R.start(w, qf, title=os.path.splitext(os.path.basename(qf))[0], customer='Practice')
    r1 = R.draft(w, qn, extract_only=True, timeout=3600, forbid=FORBID)
    ents = R.parse(R.answers_path(w, qn)); ids = [e['id'] for e in ents]
    pick = sorted(random.Random(f'sc-open-corpus:{org}:vendor-form').sample(ids, min(n, len(ids))))
    r2 = R.draft(w, qn, only=pick, timeout=5400, forbid=FORBID)
    import score as S
    q = S.questionnaire(w.root, org)
    scored = [x for x in q['detail'] if x['verdict'] != 'missing'] if q else []
    out.update({'questionnaire': qn, 'found_rows': len(ids), 'sampled': len(pick), 'cost_usd': round((r1.get('cost_usd') or 0) + (r2.get('cost_usd') or 0), 2),
                'answered': len(scored), 'agree': sum(1 for x in scored if x['verdict'] == 'agree'),
                'disagree': sum(1 for x in scored if x['verdict'] in ('disagree', 'risky')), 'risky_yes': sum(1 for x in scored if x['verdict'] == 'risky'),
                'routed_to_person': sum(1 for x in (q or {}).get('detail', []) if x['verdict'] == 'missing' and x['id'] in pick),
                'leaks': (r1.get('leaks') or []) + (r2.get('leaks') or [])})
    out['detail'] = [x for x in (q or {}).get('detail', []) if x['id'] in pick]
out['seconds'] = round(time.time() - t0)
json.dump(out, open(os.path.join(run, f'test-{mode}.json'), 'w'), indent=1, default=str)
print(json.dumps({k: v for k, v in out.items() if k != 'detail'}, indent=1, default=str))
