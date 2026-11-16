"""Blank a vendor's own completed CSA CAIQ so it can be answered again and scored against the vendor's answers.

  <green-room>/.venv/bin/python -I tools/make_blank.py <org>

Reads keys/<org>/questionnaire-key.json (source raw id, sheet). Copies the original workbook, clears every answer cell
(CSP CAIQ Answer, SSRM Control Ownership, CSP Implementation Description, CSC Responsibilities) below the header row,
keeps merged cells, dropdowns and formatting, and writes library/<org>/questionnaire/<Org> - <form> (blank).xlsx.
Adds each row's answer cell (`cell: Sheet!C12`) to the key, so scoring can match by cell as well as by id.
"""
import json, os, sys, re
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = lambda *p: os.path.join(ROOT, *p)
ANSWER_HEADS = ('csp caiq answer', 'ssrm control ownership', 'csp implementation description', 'csc responsibilities')


def main(org):
    kp = J('keys', org, 'questionnaire-key.json'); key = json.load(open(kp))
    cat = {r['id']: r for r in json.load(open(J('catalog', 'sources.json')))['sources']}
    src = cat[key['source']]; sheet = (key.get('columns') or {}).get('sheet')
    wb = openpyxl.load_workbook(J(src['file']))
    ws = wb[sheet] if sheet in wb.sheetnames else next(s for s in wb.worksheets if any(str(c.value or '').strip() == 'Question ID' for c in s['A']))
    hdr = next(c.row for c in ws['A'] if str(c.value or '').strip() == 'Question ID')
    cols = [c.column for c in ws[hdr] if str(c.value or '').strip().lower().startswith(ANSWER_HEADS)]
    ans_col = next(c.column_letter for c in ws[hdr] if str(c.value or '').strip().lower().startswith('csp caiq answer'))
    rowof = {}
    for r in range(hdr + 1, ws.max_row + 1):
        qid = str(ws.cell(r, 1).value or '').strip()
        if qid: rowof[qid] = r
        for c in cols:
            cell = ws.cell(r, c)
            if type(cell).__name__ != 'MergedCell': cell.value = None
    name = {o['slug']: o['name'] for o in json.load(open(J('catalog', 'orgs.json')))['orgs']}[org]
    form = re.sub(r'[\\/:*?"<>|]', '', key['form'])
    out_dir = J('library', org, 'questionnaire'); os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f'{name} - {form} (blank).xlsx'); wb.save(out)
    n = 0
    for row in key['rows']:
        if row['id'] in rowof: row['cell'] = f"{ws.title}!{ans_col}{rowof[row['id']]}"; n += 1
    json.dump(key, open(kp, 'w'), indent=1, ensure_ascii=False)
    print(f'{org}: {out} · {n}/{len(key["rows"])} rows located · answer column {ans_col}')


if __name__ == '__main__':
    for o in sys.argv[1:]: main(o)
