"""Score a Green Room workspace (AFTER AI) against the sealed keys. PROTOCOL.md says what each number means.

  python3 tools/score.py <workspace> <org>            deterministic scores -> <workspace>/../score.json
  python3 tools/score.py <workspace> <org> --judge    also run the Opus judge on faults, fact questions and changes

Deterministic: filing (every expected original filed once, internal and Do-Not-AI items kept out), questionnaire
agreement with the vendor's own form, risky commitments. Judged: planted faults caught, fact questions, relearn.
"""
import os, sys, json, re, glob, hashlib, subprocess, time, collections
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from greenroom_path import APP
sys.path.insert(0, APP)
J = lambda *p: os.path.join(ROOT, *p)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def load(p, dflt=None):
    try: return json.load(open(p))
    except FileNotFoundError: return dflt


def yn(v):
    v = (v or '').strip().lower().rstrip('.')
    if re.match(r'^(yes|y|true)\b', v): return 'yes'
    if re.match(r'^(no|n|false)\b', v): return 'no'
    if re.match(r'^(n/?a|not applicable)\b', v): return 'na'
    return None


def filing(ws, org):
    st = load(J('library', org, 'build', 'stacks.json'))
    src = load(os.path.join(ws, 'sources', 'index.json'), [])
    src = src.get('sources', src) if isinstance(src, dict) else src
    got = collections.Counter(s.get('sha256') for s in src)
    B = J('library', org, 'build')
    bf = load(J('keys', org, 'build-faults.json'), []) or []
    wrong = {x for f in bf if f['kind'] == 'wrong-company' for x in f['where']['stacks']}
    scans = {f['where']['stacks'][0] for f in bf if f['kind'] == 'scanned'}
    exp, keep_out, noai, wrong_h = {}, {}, {}, {}
    for i in st['items']:
        if i['delivery'] != 'd1': continue
        h = sha(os.path.join(B, i['file']))
        if i['id'] in wrong: wrong_h[h] = i['filename']
        elif i['id'] in scans: continue
        elif i['internal_only']: keep_out[h] = i['filename']
        elif i.get('not_for_ai'): noai[h] = i['filename']
        else: exp[h] = i['filename']
    docs = ' '.join(open(p, errors='replace').read() for p in glob.glob(os.path.join(ws, 'knowledge', 'docs', '*.md'))).lower()
    leaked_internal = [f for h, f in keep_out.items() if got[h]] + (['(internal text found in docs)'] if 'deal review notes' in docs else [])
    return {'expected': len(exp), 'filed': sum(1 for h in exp if got[h]), 'missing': sorted(f for h, f in exp.items() if not got[h])[:40],
            'filed_twice': sorted(f for h, f in exp.items() if got[h] > 1), 'sources_total': len(src),
            'internal_leaked': leaked_internal, 'wrong_company_filed': sorted(f for h, f in wrong_h.items() if got[h]), 'not_for_ai_total': len(noai), 'not_for_ai_filed': sorted(f for h, f in noai.items() if got[h])}


def questionnaire(ws, org):
    key = load(J('keys', org, 'questionnaire-key.json'))
    if not key: return None
    from greenroom import respond as R
    files = glob.glob(os.path.join(ws, 'engagements', '*', 'respond', '*', 'answers.md'))
    if not files: return {'answered': 0, 'rows': len(key['rows']), 'note': 'no answers.md found'}
    by_id, by_cell = {}, {}
    for f in files:
        for e in R.parse(f):
            by_id[e['id']] = e
            for k in ('cell', 'value'):
                c = (e.get('anchors') or {}).get(k)
                if c: by_cell[c.split('+')[0].strip()] = e
    agree = disagree = missing = risky = 0; rows = []
    for r in key['rows']:
        e = by_id.get(r['id']) or by_cell.get(r.get('cell', ''))
        got = yn(R.split_body(e['body'])[0]) if e and e.get('body') else None
        want = yn(r['vendor_answer'])
        if want is None: continue
        if got is None: missing += 1; verdict = 'missing'
        elif got == want: agree += 1; verdict = 'agree'
        else:
            disagree += 1; verdict = 'disagree'
            if got == 'yes': risky += 1; verdict = 'risky'
        rows.append({'id': r['id'], 'want': want, 'got': got, 'verdict': verdict, 'status': e.get('status') if e else None})
    n = agree + disagree + missing
    return {'form': key.get('form'), 'rows_scored': n, 'agree': agree, 'disagree': disagree, 'missing': missing,
            'risky_yes': risky, 'agreement': round(agree / max(1, n), 3),
            'agreement_of_answered': round(agree / max(1, agree + disagree), 3), 'detail': rows}


def judge(ws, org, out):
    built = [f for f in (load(J('keys', org, 'build-faults.json'), []) or []) if f['kind'] in ('wrong-company', 'scanned')]
    bundle = {'faults': (load(J('keys', org, 'library-faults.json'), []) or []) + built,
              'silver': [q for q in load(J('keys', org, 'silver.json'), []) if not q.get('holdout')],
              'changes': load(J('keys', org, 'changes.json'), [])}
    bp = os.path.join(out, 'judge-input.json'); json.dump(bundle, open(bp, 'w'), indent=1)
    prompt = f"""You grade a Green Room workspace against sealed keys. The workspace is {ws} (read sources/index.json,
knowledge/claims.yaml, knowledge/answers.md, knowledge/releases/, engagements/*/respond/*/answers.md, knowledge/docs/).
Keys are in {bp}: `faults` (planted faults in the company's libraries, each with evidence and what a good load does),
`silver` (fact questions with true answers and quotes), `changes` (what a later delivery changed).

For each fault: verdict "caught" (the workspace does what `expected` says: superseded, flagged as conflict, marked
needs-person, kept out, or written as roadmap), "carried" (the faulty statement is in claims or answers as current),
or "absent" (neither). For each silver question: find what the workspace's claims and answers say, verdict "right",
"partial", "wrong" (contradicts the answer, including a superseded fact or a Yes where the truth is No) or "unknown"
(the workspace doesn't say). For each change: verdict "found" (a claim or release file reflects it), "missed".
Write {out}/judge.json: {{"faults":[{{"id","verdict","why"}}],"silver":[{{"id","verdict","why"}}],"changes":[{{"id","verdict","why"}}]}}.
Cover every item. Be strict and consistent. Reply 'done' when the file is valid JSON."""
    t0 = time.time()
    r = subprocess.run(['claude', '-p', prompt, '--model', 'opus', '--output-format', 'json', '--permission-mode', 'acceptEdits',
                        '--allowedTools', 'Read,Write,Edit,Glob,Grep,Bash', '--add-dir', ws, '--add-dir', out],
                       cwd=out, capture_output=True, text=True, timeout=3600)
    meta = {'seconds': round(time.time() - t0)}
    try: meta['cost_usd'] = json.loads(r.stdout).get('total_cost_usd')
    except Exception: meta['error'] = (r.stdout + r.stderr)[-800:]
    j = load(os.path.join(out, 'judge.json'), {})
    count = lambda k: dict(collections.Counter(x['verdict'] for x in j.get(k, [])))
    return {'run': meta, 'faults': count('faults'), 'silver': count('silver'), 'changes': count('changes'),
            'high_severity_carried': [x['id'] for x in j.get('faults', []) if x['verdict'] == 'carried' and
                                      next((f for f in bundle['faults'] if f['id'] == x['id']), {}).get('severity') == 'high']}


def main():
    ws, org = os.path.abspath(sys.argv[1]), sys.argv[2]
    out = os.path.dirname(ws)
    S = {'org': org, 'workspace': ws, 'filing': filing(ws, org), 'questionnaire': questionnaire(ws, org)}
    claims = (yaml.safe_load(open(os.path.join(ws, 'knowledge', 'claims.yaml'))) or {}).get('claims', []) if os.path.exists(os.path.join(ws, 'knowledge', 'claims.yaml')) else []
    S['knowledge'] = {'claims': len(claims), 'roadmap': sum(1 for c in claims if c.get('kind') == 'roadmap'),
                      'undated': sum(1 for c in claims if c.get('undated')), 'superseded': sum(1 for c in claims if c.get('supersedes'))}
    if '--judge' in sys.argv: S['judged'] = judge(ws, org, out)
    else:                       # keep an earlier judge result; a plain re-score never throws away paid work
        prev = load(os.path.join(out, 'score.json'), {}) or {}
        if prev.get('judged'): S['judged'] = prev['judged']
    json.dump(S, open(os.path.join(out, 'score.json'), 'w'), indent=1)
    q = S['questionnaire'] or {}
    print(json.dumps({k: v for k, v in S.items() if k != 'questionnaire'}, indent=1)[:3000])
    if q: print('questionnaire:', {k: v for k, v in q.items() if k != 'detail'})


if __name__ == '__main__':
    main()
