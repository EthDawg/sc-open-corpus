"""Build the portals site.

  python3 portals/build.py --public   portals/public/  for Vercel: only openly licensed files are hosted; other items
                                       show their metadata and a link to the original; private-only exports are left out
  python3 portals/build.py --local    portals/local/   everything, for runs on this Mac (serve with portals/serve.sh)
"""
import json, os, sys, shutil, glob, zipfile, io, csv
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import denylist as DENY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda *p: os.path.join(ROOT, *p)


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst): return
    try: os.link(src, dst)
    except OSError: shutil.copy2(src, dst)


def main():
    public = '--public' in sys.argv
    out = J('portals', 'public' if public else 'local')
    link = os.path.join(out, '.vercel'); keep = J('portals', '.vercel-link')
    if os.path.isdir(link): shutil.rmtree(keep, ignore_errors=True); shutil.copytree(link, keep)
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(J('portals', 'src'), out)
    if public and os.path.isdir(keep): shutil.copytree(keep, link)
    data = os.path.join(out, 'data'); os.makedirs(data)
    orgs = json.load(open(J('catalog', 'orgs.json')))['orgs']
    cat = json.load(open(J('catalog', 'sources.json')))
    idx = {'as_of': cat['as_of'], 'public': public, 'orgs': []}
    for o in orgs:
        b = J('library', o['slug'], 'build')
        if not os.path.exists(os.path.join(b, 'stacks.json')): continue
        st = json.load(open(os.path.join(b, 'stacks.json'))); ab = json.load(open(os.path.join(b, 'answerbank.json')))
        od = os.path.join(data, o['slug']); apps = ['stacks']
        if public:      # nothing on the local deny list goes public: not a file that names it, not a line about it
            TS = DENY.terms()
            txt_hit = lambda rid: bool(rid) and DENY.file_hit(J('text', rid + '.txt'), TS)
            st['items'] = [i for i in st['items'] if not DENY.hit(json.dumps({k: i.get(k) for k in ('title', 'description', 'props', 'filename')}), TS)]
            for i in st['items']:
                if txt_hit(i.get('raw')): i['redistributable'] = False
            ab['entries'] = [e for e in ab['entries'] if not DENY.hit(json.dumps(e), TS)]
        all_open = all(i['redistributable'] for i in st['items'])
        for i in st['items']:
            if public and not i['redistributable']: i['file'] = None
            elif i['file']: copy(os.path.join(b, i['file']), os.path.join(od, i['file']))
            if i.get('thumb') and (not public or i['redistributable']): copy(os.path.join(b, i['thumb']), os.path.join(od, i['thumb']))
            elif public: i['thumb'] = None
        if public: st['export'] = None; st['export_new'] = None     # zips can't be scanned for deny-listed text: files only
        else:
            for k in ('export', 'export_new'):
                if st.get(k): copy(os.path.join(b, st[k]), os.path.join(od, st[k]))
        json.dump(st, open(os.path.join(od, 'stacks.json'), 'w'))
        redist = {r['id']: r['redistributable'] for r in cat['sources']}
        if public:     # only entries resting on openly licensed sources; no export (the full export is private)
            ab['entries'] = [e for e in ab['entries'] if redist.get(str(e.get('source') or '').split('#')[0])]
            ab['export'] = None
            if len(ab['entries']) >= 15:
                json.dump(ab, open(os.path.join(od, 'answerbank.json'), 'w')); apps.append('answerbank')
        else:
            copy(os.path.join(b, ab['export']), os.path.join(od, ab['export']))
            json.dump(ab, open(os.path.join(od, 'answerbank.json'), 'w')); apps.append('answerbank')
        idx['orgs'].append({'slug': o['slug'], 'name': o['name'], 'apps': apps, 'items': len(st['items']), 'answers': len(ab['entries']),
                            'open': all_open, 'blurb': o.get('blurb', '')})
    t = J('library', 'tenders', 'build', 'tenders.json')
    if os.path.exists(t):
        T = json.load(open(t)); td = os.path.join(data, 'tenders')
        if public:
            TS = DENY.terms()
            T['opportunities'] = [op for op in T['opportunities'] if not DENY.hit(json.dumps({k: op.get(k) for k in ('title', 'summary', 'buyer', 'criteria')}), TS)]
            for op in T['opportunities']:
                op['qa'] = [x for x in op.get('qa') or [] if not DENY.hit(json.dumps(x), TS)]
                for d in op['documents']:
                    if DENY.file_hit(J('text', d['raw'] + '.txt'), TS): d['redistributable'] = False
        for op in T['opportunities']:
            op['qa_count'] = len(op.get('qa') or [])
            if public and not all(d['redistributable'] for d in op['documents']): op['qa'] = []   # buyer's words stay with the buyer
            for d in op['documents']:
                if public and not d['redistributable']: d['file'] = None
                elif d.get('file'): copy(J('library', 'tenders', 'build', d['file']), os.path.join(td, d['file']))
            if op.get('pack') and (not public or all(d['redistributable'] for d in op['documents'])):
                copy(J('library', 'tenders', 'build', op['pack']), os.path.join(td, op['pack']))
            else: op['pack'] = None
        json.dump(T, open(os.path.join(td, 'tenders.json'), 'w'))
        idx['tenders'] = len(T['opportunities'])
    json.dump(idx, open(os.path.join(data, 'index.json'), 'w'), indent=1)
    if public:
        TS = DENY.terms(); assert TS, 'No deny list on this machine: refusing to build the public cut'
        bad = [os.path.relpath(os.path.join(d, f), out) for d, _, fs in os.walk(out) for f in fs
               if not f.endswith(('.png', '.jpg')) and DENY.file_hit(os.path.join(d, f), TS)]
        if bad: raise SystemExit(f'Deny-listed terms found in the public cut: {bad[:10]}')
        json.dump({'cleanUrls': True, 'trailingSlash': True,
                   'headers': [{'source': '/data/(.*)', 'headers': [{'key': 'Cache-Control', 'value': 'public, max-age=3600'}]}]},
                  open(os.path.join(out, 'vercel.json'), 'w'), indent=1)
    n = sum(len(fs) for _, _, fs in os.walk(out)); mb = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(out) for f in fs) / 1e6
    print(f"{'public' if public else 'local'}: {len(idx['orgs'])} libraries, {idx.get('tenders', 0)} tenders, {n} files, {mb:.0f} MB -> {out}")


if __name__ == '__main__':
    main()
