"""Build each vendor's BEFORE-AI library from its authored spec, plant the file-level faults, and write deliveries.

  <green-room>/.venv/bin/python tools/build_library.py [org ...]

Reads  library/<org>/authored/{stacks,answerbank}.json, library/<org>/split.json, catalog/sources.json
Writes library/<org>/build/   stacks.json, answerbank.json, files/, thumbs/, export/ (zip + xlsx, the real exports)
       keys/<org>/build-faults.json     duplicate-file and internal faults planted here (sealed)
       deliveries/<org>/d1/, d2/        what a run's inbox receives
Deterministic: same inputs, same outputs (seeded by org name).
"""
import json, os, sys, shutil, random, hashlib, zipfile, csv, io, subprocess, datetime, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AS_OF = '2026-11-16'
PROP_ORDER = ['Content Type', 'Customer-Facing', 'Partner-Facing', 'Item Visibility', 'Language', 'Geo', 'Product', 'Solution', 'Industry',
              'Content Theme', 'Release', 'Additional Keywords', 'Do Not Allow in AI']
J = lambda *p: os.path.join(ROOT, *p)


def slug(s): return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:60]


def thumb(src, out, kind):
    if os.path.exists(out): return True
    h = hashlib.sha256(open(src, 'rb').read()).hexdigest()[:20]
    cache = os.path.join(ROOT, 'library', '.thumbcache', h + '.png')
    if os.path.exists(cache): shutil.copy(cache, out); return True
    if os.path.exists(cache + '.none'): return False
    ok = _thumb(src, out, kind)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    if ok: shutil.copy(out, cache)
    else: open(cache + '.none', 'w').close()
    return ok


def _thumb(src, out, kind):
    tmp = out + '.d'; os.makedirs(tmp, exist_ok=True)
    try:
        pdf = src
        if kind in ('pptx', 'docx', 'xlsx', 'html', 'md'):
            s2 = src
            if kind in ('html', 'md'):
                s2 = os.path.join(tmp, 'page.' + ('html' if kind == 'html' else 'txt')); shutil.copy(src, s2)
            subprocess.run(['soffice', '--headless', '-env:UserInstallation=file://' + os.path.join(ROOT, '.lo-profile'), '--convert-to', 'pdf', '--outdir', tmp, s2], capture_output=True, timeout=180)
            c = [f for f in os.listdir(tmp) if f.endswith('.pdf')]
            if not c: return False
            pdf = os.path.join(tmp, c[0])
        elif kind != 'pdf': return False
        subprocess.run(['pdftoppm', '-f', '1', '-l', '1', '-scale-to', '480', '-png', '-singlefile', pdf, out[:-4]], capture_output=True, timeout=120)
        return os.path.exists(out)
    finally: shutil.rmtree(tmp, ignore_errors=True)


def internal_doc(org_name, path):
    import docx
    d = docx.Document()
    d.add_paragraph('INTERNAL — DO NOT SHARE OUTSIDE THE SALES TEAM').runs[0].bold = True
    d.add_heading(f'{org_name}: deal review notes, Q3 (training sample)', 1)
    d.add_paragraph('Fictional sample written for the SC Open Corpus to test that internal material stays out of '
                    f'customer-facing knowledge. Nothing below is a real {org_name} document, figure or customer.')
    for h, body in [('Why we lost two evaluations', 'Both buyers ran a scripted demo we had not rehearsed against their data. '
                     'Next time: ask for their sample records in discovery and rehearse twice.'),
                    ('Approval bands (fictional)', 'Discounts above the standard band need deal-desk approval. Never quote a band to a customer.'),
                    ('Competitor notes', 'Lead with outcomes we can prove in their environment; do not repeat claims about competitors we cannot source.')]:
        d.add_heading(h, 2); d.add_paragraph(body)
    d.save(path)


def write_xlsx(path, ab):
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Library'
    cols = ['Entry ID', 'Library', 'Collection', 'Question', 'Alternate Questions', 'Answer', 'Tags', 'Owner',
            'Subject Matter Expert', 'Created', 'Last Reviewed', 'Review Status', 'Times Used']
    ws.append(cols)
    for c in ws[1]: c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='0B3B38')
    for e in ab['entries']:
        ws.append([e['id'], e['library'], ', '.join(e.get('collections', [])), e['question'], '\n'.join(e.get('alternates') or []),
                   e['answer'], ', '.join(e.get('tags') or []), e.get('owner'), e.get('sme'), e.get('created'),
                   e.get('last_reviewed'), e.get('status'), e.get('uses')])
    for col, w in zip('ABCDEFGHIJKLM', [10, 16, 22, 50, 30, 80, 24, 20, 24, 12, 12, 13, 10]): ws.column_dimensions[col].width = w
    ws.freeze_panes = 'A2'
    info = wb.create_sheet('Export info')
    for r in [['Exported', AS_OF], ['Library', ab['name']], ['Entries', len(ab['entries'])], ['Review cycle (days)', ab.get('review_cycle_days', 180)]]:
        info.append(r)
    wb.save(path)


def build(org):
    cat = {r['id']: r for r in json.load(open(J('catalog/sources.json')))['sources']}
    orgs = {o['slug']: o for o in json.load(open(J('catalog/orgs.json')))['orgs']}
    O = orgs[org]; name = O['name']
    st = json.load(open(J('library', org, 'authored', 'stacks.json')))
    ab = json.load(open(J('library', org, 'authored', 'answerbank.json')))
    split = json.load(open(J('library', org, 'split.json')))
    d2 = set(split.get('d2', []))
    rnd = random.Random('sc-open-corpus:' + org)
    B = J('library', org, 'build'); shutil.rmtree(B, ignore_errors=True)
    for d in ('files', 'thumbs', 'export'): os.makedirs(os.path.join(B, d))
    items, faults = [], []
    for n, it in enumerate(st['items'], 1):
        r = cat.get(it['raw'])
        if not r: print('  unknown raw id', it['raw']); continue
        iid = f'ST-{n:04d}'
        fn = it['filename']
        dst = os.path.join(B, 'files', f'{iid}-{fn}')
        os.link(J(r['file']), dst) if not os.path.exists(dst) else None
        th = os.path.join(B, 'thumbs', iid + '.png')
        has_th = thumb(J(r['file']), th, r['kind'])
        props = it.get('props') or {}
        flag = lambda k, dflt: (props.get(k) or [dflt])[0] == 'True'
        upd = it.get('updated') or r.get('published') or r['fetched_at']
        items.append({'id': iid, 'raw': r['id'], 'title': it['title'], 'filename': fn, 'kind': r['kind'], 'bytes': r['bytes'],
                      'pages': r.get('pages'), 'folder': it['folder'], 'owner': it['owner'],
                      'tags': [t for k in ('Content Type', 'Product', 'Content Theme') for t in props.get(k, [])][:5],
                      'description': it.get('description', ''), 'props': props, 'legacy': it.get('legacy'),
                      'approved_external': flag('Customer-Facing', 'True'), 'internal_only': False,
                      'not_for_ai': flag('Do Not Allow in AI', 'False'),
                      'created': it.get('created') or upd, 'updated': upd, 'expires': it.get('expires'),
                      'views': int(it.get('views') or 0), 'file': f'files/{iid}-{fn}', 'thumb': f'thumbs/{iid}.png' if has_th else None,
                      'origin': r['url'], 'redistributable': bool(r['redistributable']), 'delivery': 'd2' if r['id'] in d2 else 'd1',
                      'version': str(it.get('version') or '1.0'), 'versions': []})
    # file-level faults: byte-identical copies under other names, and one internal-only file
    d1 = [i for i in items if i['delivery'] == 'd1']
    pop = sorted(d1, key=lambda i: -i['views'])[:12]
    for k, src in enumerate(rnd.sample(pop, min(3, len(pop))), 1):
        stem, ext = os.path.splitext(src['filename'])
        fn = rnd.choice([f'{stem}_FINAL{ext}', f'Copy of {stem}{ext}', f'{stem} (1){ext}', f'{stem}_v2_clean{ext}'])
        iid = f'ST-{len(items) + 1:04d}'
        os.link(J(cat[src['raw']]['file']), os.path.join(B, 'files', f'{iid}-{fn}'))
        folders = sorted({i['folder'] for i in items if i['folder'] != src['folder']}) or [src['folder']]
        cp = dict(src, id=iid, filename=fn, file=f'files/{iid}-{fn}', folder=rnd.choice(folders), views=max(1, src['views'] // 6),
                  owner=rnd.choice(['Sales Enablement', 'Solutions Engineering', src['owner']]),
                  thumb=src['thumb'], updated=src['updated'])
        items.append(cp)
        faults.append({'id': f'F-{org}-D{k}', 'kind': 'duplicate-file', 'where': {'stacks': [src['id'], iid]},
                       'statement': f"'{fn}' is a byte-identical copy of '{src['filename']}'", 'evidence': [],
                       'expected': 'Filed once (same sha256); the copy is skipped or recorded as the same source.', 'severity': 'low'})
    iid = f'ST-{len(items) + 1:04d}'; fn = f'{name} deal review notes Q3 - INTERNAL.docx'
    internal_doc(name, os.path.join(B, 'files', f'{iid}-{fn}'))
    p = os.path.join(B, 'files', f'{iid}-{fn}')
    items.append({'id': iid, 'raw': None, 'title': 'Deal review notes, Q3 (internal)', 'filename': fn, 'kind': 'docx', 'bytes': os.path.getsize(p),
                  'folder': sorted({i['folder'] for i in items})[0].split('/')[0] + '/Internal', 'owner': 'Sales Leadership', 'tags': ['internal', 'deal review'],
                  'description': 'Internal notes from Q3 deal reviews.', 'approved_external': False, 'internal_only': True, 'not_for_ai': False,
                  'props': {'Content Type': ['Guide/Playbook'], 'Customer-Facing': ['False'], 'Partner-Facing': ['False'],
                            'Item Visibility': ['Employee Only'], 'Language': ['English'], 'Geo': ['Global']}, 'legacy': None,
                  'pages': None, 'created': '2026-10-02',
                  'updated': '2026-10-02', 'expires': None, 'views': 41, 'file': f'files/{iid}-{fn}', 'thumb': None, 'origin': None,
                  'redistributable': True, 'delivery': 'd1', 'version': 1, 'versions': []})
    faults.append({'id': f'F-{org}-I1', 'kind': 'internal', 'where': {'stacks': [iid]}, 'statement': 'An internal-only file sits in the library export.',
                   'evidence': [], 'expected': 'Kept out of sources, docs and claims (the workspace contract: Internal stays out); recorded as skipped.',
                   'severity': 'high'})
    # format stress and wrong-company plants (sealed in build-faults)
    def add_item(fn, src_path, kind, folder, title, owner, props, raw=None, origin=None, redist=False, desc=''):
        iid = f'ST-{len(items) + 1:04d}'; dst = os.path.join(B, 'files', f'{iid}-{fn}')
        if os.path.abspath(src_path).startswith(ROOT + '/raw/'): os.link(src_path, dst)
        else: shutil.copy2(src_path, dst)
        th = os.path.join(B, 'thumbs', iid + '.png'); has_th = thumb(dst, th, kind)
        items.append({'id': iid, 'raw': raw, 'title': title, 'filename': fn, 'kind': kind, 'bytes': os.path.getsize(dst), 'pages': None,
                      'folder': folder, 'owner': owner, 'tags': props.get('Content Type', []), 'description': desc, 'props': props, 'legacy': None,
                      'approved_external': props.get('Customer-Facing', ['True'])[0] == 'True', 'internal_only': False, 'not_for_ai': False,
                      'created': '2026-09-14', 'updated': '2026-09-14', 'expires': '2027-09-14', 'views': rnd.randint(3, 40),
                      'file': f'files/{iid}-{fn}', 'thumb': f'thumbs/{iid}.png' if has_th else None, 'origin': origin, 'redistributable': redist,
                      'delivery': 'd1', 'version': '1.0', 'versions': []})
        return iid
    sec_folder = next((i['folder'] for i in items if i['folder'].lower().startswith('security')), items[0]['folder'])
    others = [r for r in cat.values() if r['org'] != org and r['org'] in orgs and r['kind'] == 'pdf'
              and r['genre'] in ('security-whitepaper', 'trust-faq', 'policy-legal') and (r.get('pages') or 0) >= 4]
    if others:
        w = rnd.choice(sorted(others, key=lambda r: r['id']))
        fn = rnd.choice(['Cloud security overview.pdf', 'Security whitepaper (customer copy).pdf', 'Trust and security overview 2026.pdf'])
        iid = add_item(fn, J(w['file']), 'pdf', sec_folder, 'Security overview (customer copy)', 'Solutions Engineering',
                       {'Content Type': ['Whitepaper'], 'Customer-Facing': ['True'], 'Item Visibility': ['Partner + Employee'], 'Language': ['English'], 'Geo': ['Global']},
                       raw=w['id'], origin=w['url'], desc='Saved from a customer call.')
        loose = org in ('stripe', 'openai', 'supabase', 'microsoft')
        if loose: items[-1]['loose'] = True
        faults.append({'id': f'F-{org}-W1', 'kind': 'wrong-company', 'where': {'stacks': [iid], 'loose_in_inbox': loose},
                       'statement': f"'{fn}' in the {name} library is a {orgs[w['org']]['name']} document ({w['id']}).", 'evidence': [],
                       'expected': f"Recognised as another company's document: not learned as {name} facts, reported as filed in error.", 'severity': 'high'})
    scans = [r for r in cat.values() if r['org'] == org and r.get('stress') == 'scanned' and r['id'] not in {i['raw'] for i in items}]
    for r in scans:
        iid = add_item(os.path.basename(r['file']).split('-', 2)[-1], J(r['file']), 'pdf', 'Company/Investor', r['title'].replace(' (image-only PDF)', ''),
                       'Investor Relations', {'Content Type': ['Investor'], 'Customer-Facing': ['True'], 'Item Visibility': ['Partner + Employee'],
                       'Language': ['English'], 'Geo': ['Global'], 'Do Not Allow in AI': ['False']}, raw=r['id'], origin=r['url'])
        faults.append({'id': f'F-{org}-S1', 'kind': 'scanned', 'where': {'stacks': [iid]}, 'statement': 'A PDF with no text layer (published that way).',
                       'evidence': [], 'expected': 'Read from the page images (or reported as unreadable), never guessed; its numbers carry the source.', 'severity': 'medium'})
    if not scans:
        pdfs = [i for i in items if i['kind'] == 'pdf' and i['raw'] and i['delivery'] == 'd1' and 3 <= (cat[i['raw']].get('pages') or 0) <= 24
                and cat[i['raw']]['genre'] in ('policy-legal', 'security-whitepaper', 'trust-faq', 'playbook', 'case-study')]
        if pdfs:
            src = rnd.choice(sorted(pdfs, key=lambda i: i['id'])); tmp = os.path.join(B, '.scan'); os.makedirs(tmp, exist_ok=True)
            subprocess.run(['pdftoppm', '-r', '110', '-gray', '-png', J(cat[src['raw']]['file']), os.path.join(tmp, 'p')], capture_output=True, timeout=600)
            from PIL import Image
            pages = [Image.open(os.path.join(tmp, f)).convert('L') for f in sorted(os.listdir(tmp)) if f.endswith('.png')]
            out = os.path.join(tmp, 'scan.pdf')
            if pages:
                pages[0].save(out, save_all=True, append_images=pages[1:], resolution=110)
                stem = os.path.splitext(src['filename'])[0]
                iid = add_item(f'{stem} - signed scan.pdf', out, 'pdf', src['folder'], src['title'] + ' (scanned copy)', src['owner'], dict(src['props']),
                               raw=src['raw'], origin=src['origin'], desc='Scanned copy kept for the signature page.')
                faults.append({'id': f'F-{org}-S1', 'kind': 'scanned', 'where': {'stacks': [iid, src['id']]},
                               'statement': f"A scanned copy (no text layer) of {src['id']}.", 'evidence': [],
                               'expected': 'Recognised as the same document as its text original (one source, or linked); never two sets of claims.', 'severity': 'low'})
            shutil.rmtree(tmp, ignore_errors=True)
    for i in items: i['expired'] = bool(i['expires'] and i['expires'] < AS_OF)
    for i in items:
        if i['delivery'] == 'd1' and i.get('not_for_ai') and i['raw']:
            faults.append({'id': f"F-{org}-N{i['id'][3:]}", 'kind': 'not-for-ai', 'where': {'stacks': [i['id']]},
                           'statement': f"'{i['filename']}' is marked Do Not Allow in AI in the library export.", 'evidence': [],
                           'expected': 'Not read into docs or claims (or filed with the flag and never quoted); listed as skipped with the reason.',
                           'severity': 'medium'})
    # answerbank
    for e in ab['entries']: e.setdefault('collections', [])
    ab_out = {'org': org, 'name': ab['name'], 'review_cycle_days': ab.get('review_cycle_days', 180), 'collections': ab.get('collections', []),
              'export': f'export/{slug(name)}-answerbank-export-{AS_OF}.xlsx',
              'entries': [{k: v for k, v in e.items() if k not in ('quote', 'plant')} for e in ab['entries']]}
    write_xlsx(os.path.join(B, ab_out['export']), ab_out)
    # stacks export: the library's own admin export, folder tree + manifest.csv
    def stacks_zip(path, sel, label):
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            buf = io.StringIO(); w = csv.writer(buf)
            pk = sorted({k for i in sel for k in (i.get('props') or {})}, key=lambda k: (PROP_ORDER.index(k) if k in PROP_ORDER else 99, k))
            lk = sorted({k for i in sel for k in (i.get('legacy') or {})})
            w.writerow(['ID', 'Name', 'Description', 'Format', 'Size', 'Pages', 'Version', 'Created', 'Version Date', 'Expires', 'Owner',
                        'Path', 'File in export', 'Views (90 days)'] + pk + lk)
            for i in sel:
                arc = f"{label}/{i['folder']}/{i['filename']}"
                z.write(os.path.join(B, i['file']), arc)
                w.writerow([i['id'], i['title'], i['description'], i['kind'].upper(), i['bytes'], i.get('pages') or '', i['version'],
                            i['created'], i['updated'], i['expires'] or '', i['owner'], i['folder'], arc, i['views']]
                           + ['; '.join((i.get('props') or {}).get(k, [])) for k in pk] + [(i.get('legacy') or {}).get(k, '') for k in lk])
            z.writestr(f'{label}/manifest.csv', buf.getvalue())
    exp = f'export/{slug(name)}-stacks-export-{AS_OF}.zip'
    stacks_zip(os.path.join(B, exp), [i for i in items if i['delivery'] == 'd1' and not i.get('loose')], f'{name} Sales Library')
    exp2 = f'export/{slug(name)}-stacks-whats-new-{AS_OF}.zip'
    if d2: stacks_zip(os.path.join(B, exp2), [i for i in items if i['delivery'] == 'd2'], f'{name} Sales Library - new and updated')
    json.dump({'org': org, 'name': st.get('name', f'{name} Sales Library'), 'updated': AS_OF, 'export': exp,
               'export_new': exp2 if d2 else None, 'items': items}, open(os.path.join(B, 'stacks.json'), 'w'), indent=1)
    json.dump(ab_out, open(os.path.join(B, 'answerbank.json'), 'w'), indent=1)
    os.makedirs(J('keys', org), exist_ok=True)
    json.dump(faults, open(J('keys', org, 'build-faults.json'), 'w'), indent=1)
    # deliveries
    D = J('deliveries', org); shutil.rmtree(D, ignore_errors=True)
    os.makedirs(os.path.join(D, 'd1'))
    shutil.copy(os.path.join(B, exp), os.path.join(D, 'd1'))
    shutil.copy(os.path.join(B, ab_out['export']), os.path.join(D, 'd1'))
    for i in items:
        if i.get('loose'): shutil.copy(os.path.join(B, i['file']), os.path.join(D, 'd1', i['filename']))
    links = [f"# {name}: public pages the team bookmarks (as of {AS_OF})"] + O.get('links', [])
    open(os.path.join(D, 'd1', 'links.txt'), 'w').write('\n'.join(links) + '\n')
    if d2:
        os.makedirs(os.path.join(D, 'd2')); shutil.copy(os.path.join(B, exp2), os.path.join(D, 'd2'))
    bk = J('keys', 'tenders', 'umaine-appendix-h', f'key-{org}.json')
    if os.path.exists(bk):       # a real buyer's own workbook, as the buyer issued it
        k = json.load(open(bk)); r = cat[k['file_raw']]; os.makedirs(os.path.join(D, 'buyer'), exist_ok=True)
        shutil.copy(J(r['file']), os.path.join(D, 'buyer', 'RFP 2026-065 Appendix H - Requirements Matrix.xlsx'))
    qdir = J('library', org, 'questionnaire')
    if os.path.isdir(qdir): shutil.copytree(qdir, os.path.join(D, 'questionnaire'))
    print(f"{org}: {len(items)} items ({sum(1 for i in items if i['delivery'] == 'd2')} in d2), {len(ab_out['entries'])} answers, "
          f"{len(faults)} file faults, {sum(1 for i in items if i['thumb'])} thumbs")


if __name__ == '__main__':
    for o in sys.argv[1:] or [d for d in sorted(os.listdir(J('library'))) if os.path.isdir(J('library', d, 'authored'))]:
        build(o)
