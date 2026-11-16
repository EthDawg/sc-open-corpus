# Harvest rules (every harvester follows these)

Goal: the highest-signal PUBLIC material a solution consultant (SC) or GTM team actually uses to absorb a product,
answer RFx and security questionnaires, present, demo and keep up with releases. Cut through marketing: prefer documents
that carry checkable facts (security whitepapers, trust FAQs, questionnaire responses, handbooks and playbooks, release
notes and deprecations, public roadmaps, pricing pages, system cards, buyer RFx packs with Q&A addenda, real decks).

## Where files go
- Originals: `raw/<org>/<org>-NNN-<slug>.<ext>` exactly as fetched (pdf, pptx, xlsx, docx, html, md, csv, json, or a
  `.tar.gz` of a repo subtree). Never edit an original. NNN is 001, 002... within the org.
- One JSON object per line in `catalog/parts/<track>.jsonl` per original (schema below). Failures go one per line in
  `catalog/parts/<track>.failed.jsonl` as {org, url, tried, reason, suggestion}.

## Record schema (all keys required; null where unknown)
{"id":"gitlab-001","org":"gitlab","title":"<the document's own title>","kind":"pdf|pptx|xlsx|docx|html|md|csv|json|repo",
 "genre":"<one of the list below>","audience":"seller|buyer|both","url":"<exact url fetched>","fetched_at":"2026-11-16",
 "published":"<doc's own published/updated date YYYY-MM-DD or null>","file":"raw/gitlab/gitlab-001-slug.pdf",
 "sha256":"...","bytes":123,"pages":<pdf pages / deck slides / null>,"licence":"CC-BY-SA-4.0|MIT|Apache-2.0|OGL-UK-3.0|US-PD|CC-BY-4.0|proprietary|unknown",
 "redistributable":true|false,"why":"<one line: what an SC learns or answers from it>",
 "sc_jobs":["absorb","respond","present","demo","discover","compete","price","relearn"]}

genre: handbook, playbook, value-framework, competitive, demo-script, product-doc, security-whitepaper, trust-faq,
questionnaire-response (a vendor's own completed CAIQ/HECVAT/SIG etc.), questionnaire-blank, rfx (buyer's RFP/RFQ/tender),
rfx-qa (buyer clarification Q&A or addendum), proposal (a submitted/winning response), deck, release-note, deprecation,
roadmap, pricing, case-study, investor, training, system-card, policy-legal, talk.

`redistributable` is true only when the licence clearly allows sharing a copy (CC BY, CC BY-SA, MIT, Apache, OGL, US
federal public domain). Vendor web pages, PDFs and decks without an open licence are `proprietary` and false: they are
kept for private testing only and the public dataset ships a fetch script for them.

## Fetching
- `curl -sSL --max-time 120 -o <file> <url>` with curl's own user agent. A 403, bot wall, login wall, CAPTCHA or empty
  JavaScript shell is a failure: record it, never work around it (no fake user agents, proxies, caches or archive.org
  copies). WebFetch may be used to READ a page to find links, but files on disk must be the real bytes fetched by curl.
- Google Slides/Docs that are publicly shared may be exported with `/export/pptx`, `/export/pdf`, `/export/docx`
  (that is the owner's own export). If it needs sign-in, it's a failure.
- Repos: `git clone --depth 1 --filter=blob:none --sparse` then `git sparse-checkout set <paths>`, and keep a
  `.tar.gz` of only the useful subtree. Note the commit in `why`.
- Check every file after download: `file <f>` must match the kind; HTML must contain real text (not a JS shell); PDFs
  must give text with `pdftotext`. Delete and record as failed anything that doesn't.
- Never log in, never accept terms on someone's behalf, never submit a form. Skip anything marked Confidential or Internal.

## Headless only
Never open a file in PowerPoint, Excel, Keynote, Preview or any desktop app: no `open`, no `open -a`, no AppleScript.
Use pdftotext, pdftoppm, `soffice --headless`, python-pptx, openpyxl (python at
`<green-room>/.venv/bin/python`).

## Budget
Quality over volume. Aim for 30 to 70 originals per track, at most ~400 MB per track. Prefer one great 40-page
whitepaper to ten thin marketing pages. Every record's `why` must say what an SC actually gets from it.
