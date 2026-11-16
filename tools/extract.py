"""Plain-text cache of every original: text/<id>.txt. Used by authoring agents (read text, not binaries) and by
verify_quotes.py (every quoted span must appear here verbatim, whitespace-normalised).

  python3 tools/extract.py            extract anything missing or changed
  python3 tools/extract.py --force    re-extract everything
"""
import json, os, sys, re, subprocess, tarfile, io, zipfile, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from greenroom_path import PY


def html_text(b):
    t = b.decode('utf-8', 'replace')
    t = re.sub(r'(?is)<(script|style|noscript|svg|nav|footer|header)[^>]*>.*?</\1>', ' ', t)
    t = re.sub(r'(?i)<br\s*/?>|</(p|div|li|h[1-6]|tr|section|article)>', '\n', t)
    t = re.sub(r'(?i)<h([1-6])[^>]*>', lambda m: '\n' + '#' * int(m.group(1)) + ' ', t)
    t = re.sub(r'(?i)<li[^>]*>', '\n- ', t)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', t))
    t = re.sub(r'[ \t\r\f\v]+', ' ', t)
    return re.sub(r'\n\s*\n+', '\n\n', t).strip()


OFFICE = r'''
import sys, json
p, kind = sys.argv[1], sys.argv[2]
out = []
if kind == 'pptx':
    from pptx import Presentation
    for i, s in enumerate(Presentation(p).slides, 1):
        out.append(f'\n## Slide {i}')
        def walk(shapes):
            for sh in shapes:
                if sh.shape_type == 6: walk(sh.shapes); continue
                if sh.has_text_frame and sh.text_frame.text.strip(): out.append(sh.text_frame.text)
                if getattr(sh, 'has_table', False) and sh.has_table:
                    for r in sh.table.rows: out.append(' | '.join(c.text for c in r.cells))
        walk(s.shapes)
        if s.has_notes_slide and s.notes_slide.notes_text_frame is not None and s.notes_slide.notes_text_frame.text.strip(): out.append('Notes: ' + s.notes_slide.notes_text_frame.text)
elif kind == 'xlsx':
    import openpyxl
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    for ws in wb.worksheets:
        out.append(f'\n## Sheet {ws.title}')
        for r in ws.iter_rows(values_only=True):
            cells = [str(c).strip() for c in r if c is not None and str(c).strip()]
            if cells: out.append(' | '.join(cells))
elif kind == 'docx':
    import docx
    d = docx.Document(p)
    for para in d.paragraphs: out.append(para.text)
    for t in d.tables:
        for r in t.rows: out.append(' | '.join(c.text for c in r.cells))
print('\n'.join(out))
'''


def extract(r):
    p = os.path.join(ROOT, r['file']); k = r['kind']
    if k == 'pdf':
        return subprocess.run(['pdftotext', '-layout', p, '-'], capture_output=True, timeout=300).stdout.decode('utf-8', 'replace')
    if k in ('pptx', 'xlsx', 'docx'):
        return subprocess.run([PY, '-I', '-c', OFFICE, p, k], capture_output=True, timeout=300).stdout.decode('utf-8', 'replace')
    if k == 'html':
        return html_text(open(p, 'rb').read())
    if k in ('md', 'csv', 'json', 'txt'):
        return open(p, 'rb').read().decode('utf-8', 'replace')
    if k == 'repo':
        out = []
        with tarfile.open(p) as tf:
            for m in tf.getmembers():
                if not m.isfile(): continue
                if re.search(r'\.(md|mdx|txt|rst|yml|yaml)$', m.name, re.I) and m.size < 400_000:
                    out.append(f'\n\n===== {m.name} =====\n' + tf.extractfile(m).read().decode('utf-8', 'replace'))
                elif re.search(r'_github-api/.*\.json$', m.name) and m.size < 4_000_000:
                    try:
                        data = json.loads(tf.extractfile(m).read())
                        rows = data if isinstance(data, list) else [data]
                        txt = '\n\n'.join(f"[{x.get('user', {}).get('login', '')} {str(x.get('created_at', ''))[:10]}] {x.get('title') or ''}\n{x.get('body') or ''}" for x in rows if isinstance(x, dict))
                        out.append(f'\n\n===== {m.name} =====\n' + txt)
                    except Exception: pass
                elif m.name.lower().endswith('.pdf') and m.size < 30_000_000:
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp:
                        tmp.write(tf.extractfile(m).read()); tmp.flush()
                        t = subprocess.run(['pdftotext', '-layout', tmp.name, '-'], capture_output=True, timeout=300).stdout.decode('utf-8', 'replace')
                    out.append(f'\n\n===== {m.name} =====\n' + t)
        return ''.join(out)
    return ''


def main():
    cat = json.load(open(os.path.join(ROOT, 'catalog/sources.json')))
    os.makedirs(os.path.join(ROOT, 'text'), exist_ok=True)
    force = '--force' in sys.argv; n = 0
    for r in cat['sources']:
        out = os.path.join(ROOT, 'text', r['id'] + '.txt'); stamp = out + '.sha'
        if not force and os.path.exists(out) and os.path.exists(stamp) and open(stamp).read() == r['sha256']: continue
        try: t = extract(r)
        except Exception as e: print('FAIL', r['id'], e); continue
        open(out, 'w').write(t); open(stamp, 'w').write(r['sha256']); n += 1
        if len(t.strip()) < 400: print('THIN', r['id'], len(t.strip()))
    print('extracted', n)


if __name__ == '__main__':
    main()
