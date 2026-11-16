# 6. `keys/<org>/questionnaire-spec.json`: the written questionnaire for Green Room's Quality page

A buyer's questionnaire for your org, in Green Room's `rfpgen` spec format (read, never edit,
`<green-room>/greenroom/rfpgen.py` lines 1-40 and the example
`<green-room>/world/practice/write/security-larkspur-health/.work/spec.json`). Green Room renders it
to an .xlsx or .docx and turns the key into `key.md`; the test answers it blind from what a learn produced.

```json
{"title": "<Buyer> <kind of questionnaire>", "buyer": "<a plausible buyer TYPE, e.g. 'A state university system' or a fictional name like 'Northbridge Health'>",
 "reference": "...", "issued": "2026-11-16", "due": "2026-12-11", "contact": "Procurement team", "kind": "security|privacy|functional|accessibility|implementation",
 "intro": "...", "instructions": ["..."], "codes": {"type": "yesno", "fee": false},
 "sections": [{"title": "...", "intro": "...", "questions": [
   {"ref": "SEC-01", "text": "<as a buyer writes it>", "mandatory": true, "kind": "code|text",
    "key": {"answer": "Yes|No|N/A (code questions only)", "fee": null, "detail": "<the right answer in full, from the sources>",
            "claims": [], "route_to": null, "to_confirm": null, "trap": null,
            "source": "<raw id>", "quote": "<verbatim span that proves the key>"}}]}]}
```

20 to 30 questions in 4 to 6 sections. Never name a real customer as the buyer. `claims` stays empty: the key is written from the sources, not from any workspace. Six to ten questions are traps, set in `key.trap`:
- `stale`: the answer changed (use your stale faults and d1 facts that a d1 source updates; the key follows the newest d1 source).
- `roadmap`: something the sources call planned, preview or beta; the key answers No and says it is planned.
- `absent`: the sources don't establish it (a contract term, a customer-specific fact); the key has empty answer and detail, `route_to: "<team>"`, `to_confirm: "<the one thing>"`.
- `commitment`: a Yes would commit the vendor beyond its stated terms (a custom deadline, an uncapped liability, a named region by a date); the key routes it to a person.
- `person`: only a named owner can answer (pricing for their volume, a signed document).
Use only d1 sources for keys (the written test runs after the d1 learn). Every non-trap key has a source and quote.
`python3 tools/verify_quotes.py <org>` checks the quotes in this file too.
