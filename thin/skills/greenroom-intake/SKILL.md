---
name: greenroom-intake
description: File everything in a Green Room workspace's inbox/ into sources and readable docs. The thin version - it files and writes no facts; facts are written later by the job that uses them.
---

`WORKSPACE.md` is the contract. Read it first, then `sources/index.json` and `sources/failed.json` if they exist. Headless tools only.

1. Take every file in `inbox/` and every line of `inbox/links.txt`. Unpack an export. If it has a manifest, the manifest says what each item is.
2. Leave out, and record in `sources/failed.json` with the reason: anything marked internal or confidential, anything flagged not for AI, and a document that is about another company. File byte-identical copies once. Employee-only items are fine to learn from but never to send: file them with `employee_only: true`. Items past their expiry date are filed with `expired: true`: a lead, never proof.
3. File each remaining original as `sources/SRC-NNNN-<slug>.<ext>` and add it to `sources/index.json` with the contract's fields (the document's own title and date; `origin`; `sha256`). An answer-library sheet is filed like any source, with `secondary: true`: it is a person's old answers, never the truth.
4. Write one clean Markdown doc per source in `knowledge/docs/<slug>.md`: front matter `title`, `source: SRC-NNNN`, `date`; then the content with its headings. A sheet becomes a table. A scan with no text is filed and reported, never guessed.
5. Write no claims and no answers. Take filed items out of `inbox/`.
6. Run `gr check .` and fix what it reports; after three tries stop and say what is wrong.
7. Finish with three plain lines: `Landed:`, `Uncertain:`, `Needs a person:`.

A link that will not fetch goes in `sources/failed.json`; never work around a refusal. Never delete a source.
