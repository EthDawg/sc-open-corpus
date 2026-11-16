"""Build Tenderline (the buyer portal) from library/tenders/authored/tenders.json.

  python3 tools/build_tenders.py

Authored shape (one per opportunity; documents are raw ids from the catalog, Q&A is the buyer's own published text):
{"opportunities": [{"id": "uk-dos-...", "title", "buyer", "buyer_type", "country", "ref", "published", "closes", "status",
   "value", "summary", "criteria": [{"name", "weight"}], "source_url", "licence",
   "documents": [{"raw": "<id>", "name": "<file name as the buyer posted it>", "added": "YYYY-MM-DD", "addendum": false}],
   "qa": [{"n": 1, "q": "...", "a": "...", "date": null, "source": "<raw id>", "quote": "<verbatim span of the answer>"}],
   "pairs_with": ["<vendor org slug whose library could answer it>"]}]}
Writes library/tenders/build/: tenders.json, files/, packs/<id>.zip.
"""
import json, os, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda *p: os.path.join(ROOT, *p)


def main():
    cat = {r['id']: r for r in json.load(open(J('catalog', 'sources.json')))['sources']}
    A = json.load(open(J('library', 'tenders', 'authored', 'tenders.json')))
    B = J('library', 'tenders', 'build'); os.makedirs(os.path.join(B, 'files'), exist_ok=True); os.makedirs(os.path.join(B, 'packs'), exist_ok=True)
    out = []
    for o in A['opportunities']:
        docs = []
        for d in o['documents']:
            r = cat[d['raw']]; fn = d['name']; rel = f"files/{o['id']}/{fn}"
            os.makedirs(os.path.join(B, 'files', o['id']), exist_ok=True)
            dst = os.path.join(B, rel)
            if not os.path.exists(dst): os.link(J(r['file']), dst)
            docs.append({'name': fn, 'kind': r['kind'], 'bytes': r['bytes'], 'added': d.get('added'), 'addendum': bool(d.get('addendum')),
                         'file': rel, 'origin': r['url'], 'redistributable': bool(r['redistributable']), 'raw': r['id']})
        pack = f"packs/{o['id']}.zip"
        with zipfile.ZipFile(os.path.join(B, pack), 'w', zipfile.ZIP_DEFLATED) as z:
            for d in docs: z.write(os.path.join(B, d['file']), f"{o.get('ref') or o['id']}/{d['name']}")
            if o.get('qa'):
                z.writestr(f"{o.get('ref') or o['id']}/Clarification questions and answers.txt",
                           '\n\n'.join(f"Q{x.get('n') or i + 1}. {x['q']}\nA. {x['a']}" for i, x in enumerate(o['qa'])))
        out.append({**{k: v for k, v in o.items() if k not in ('documents', 'qa')}, 'documents': docs,
                    'qa': [{k: x.get(k) for k in ('n', 'q', 'a', 'date')} for x in o.get('qa', [])], 'pack': pack})
    json.dump({'opportunities': out}, open(os.path.join(B, 'tenders.json'), 'w'), indent=1)
    print(f"{len(out)} opportunities, {sum(len(o['documents']) for o in out)} documents, {sum(len(o['qa']) for o in out)} clarification answers")


if __name__ == '__main__':
    main()
