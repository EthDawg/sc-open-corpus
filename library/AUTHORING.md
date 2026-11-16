# Authoring a vendor's library and keys (one agent per org)

You turn one org's harvested originals into (1) the BEFORE-AI state an SC inherits at that company: its sales content
library (Stacks) and its RFP answer library (Answerbank), with realistic, planted faults; and (2) the sealed answer
keys that score what Green Room makes of it. Read `DESIGN.md` and `PROTOCOL.md` first.

Inputs: `catalog/sources.json` (records for your org), `text/<id>.txt` (plain text of every original; read these,
not the binaries).

## 0. `library/<org>/split.json`: what arrives when
`{"d1": [ids], "d2": [ids], "why": "..."}`. Every original of your org is in exactly one. d2 is the later delivery:
3 to 8 of the newest originals that change what a seller says (a new retention rule, the latest system card, a
deprecation, the newest release notes, a refreshed whitepaper). d1 must stand on its own without them.
Write only under `library/<org>/authored/` and `keys/<org>/`. Headless only: never open files in desktop apps, no
`open`, no AppleScript.

Everything you state about the company must be true to a source and carry a verbatim quote, EXCEPT the planted faults,
which are true to an older source (stale), or deliberately wrong in a way the keys explain. Never invent numbers,
certifications, customers or dates. `python3 tools/verify_quotes.py <org>` must pass (quotes are matched
case-insensitively with whitespace and curly quotes normalised; keep quotes short, 8 to 40 words, copied exactly from
the text file, no ellipses).

## 1. `library/<org>/authored/stacks.json`: how each original sits in the content library

Stacks mirrors a real enterprise sales content library's item shape (learned from a 5,696-item real library, structure
only): every item has an expiry; about half are past version 1; items carry ~20 filter properties; about a fifth are
marked "Do Not Allow in AI"; about two fifths are employee-only; and a few hundred still carry a previous tool's fields
from a migration.
```json
{"name": "<Org> Sales Library", "items": [
  {"raw": "<id>", "title": "<what the enablement team would call it>", "filename": "<a realistic human file name with extension>",
   "folder": "Security & Trust/Whitepapers", "owner": "<team: Product Marketing | Security & Compliance | Sales Enablement | Solutions Engineering | Legal | Investor Relations | Developer Relations>",
   "description": "<one or two plain lines a seller would read>", "version": "2.1", "created": "YYYY-MM-DD", "updated": "YYYY-MM-DD",
   "expires": "YYYY-MM-DD", "views": 0,
   "props": {"Content Type": ["Deck (First Call) | Deck (Customer) | Deck (Internal) | Guide/Playbook | Overview | Solution Brief | Whitepaper | Battle Card | Competitive Brief | Customer Story | Demo | Questionnaire Response | Release Notes | Pricing | Datasheet | Training | Investor"],
             "Customer-Facing": ["True|False"], "Partner-Facing": ["True|False"], "Item Visibility": ["Partner + Employee | Employee Only"],
             "Language": ["English"], "Geo": ["Global | AMER | EMEA | APJ"], "Product": ["..."], "Solution": ["..."], "Industry": ["..."],
             "Content Theme": ["..."], "Release": ["<release name if tied to one>"], "Additional Keywords": ["..."],
             "Do Not Allow in AI": ["True|False"]},
   "legacy": null}
]}
```
Every d1 and d2 original for your org gets exactly one item (buyer-side genres excepted). Folders: a realistic tree of
6 to 12 folders, at most two levels deep (Security & Trust, Product, Sales Plays, Competitive, Decks, Pricing &
Packaging, Customer Stories, Release Updates, AI, Legal, Company, Enablement). `updated` is the source's own date if it
has one, else its fetch date; `created` on or before it; `version` "1.0" for most, higher for living documents
(whitepapers, pricing, playbooks). `expires` is what a real library would set (usually 12 months after `updated`); an
item whose source is genuinely out of date (an older release note, a superseded system card, a retired model) has
an `expires` in the past. `views` is a plausible 90-day count (skewed: a few items get most views).
Truthful flags: enablement material written for sellers (handbook sales pages, internal-style training) is
`Customer-Facing: False`, `Item Visibility: Employee Only`; set `Do Not Allow in AI: True` on roughly a fifth of
items where a real team plausibly would (investor material, licensed analyst-style content, competitive pages, anything
with third-party logos or quotes). For about 10% of items set `legacy` to a previous tool's fields, e.g.
`{"Legacy Library ID": "HS-48213", "Legacy Added Date": "2023-04-11", "Legacy Content Type": "Sales Deck"}`.

## 2. `library/<org>/authored/answerbank.json`: the answer library a proposal team built by hand
```json
{"name": "<Org> Answer Library", "review_cycle_days": 180, "collections": ["Security questionnaire core", "AI and data use", "..."],
 "entries": [{"id": "AB-0001", "library": "Security | Privacy | Compliance | AI and Data | Product | Integration | Legal and Commercial | Company",
   "question": "...", "alternates": ["..."], "answer": "...", "owner": "<team>", "sme": "<role, e.g. Security Engineering lead>",
   "created": "YYYY-MM-DD", "last_reviewed": "YYYY-MM-DD", "status": "Current | Review due | Archived", "tags": ["..."], "uses": 0,
   "source": "<raw id>", "quote": "<verbatim span the answer rests on>"}]}
```
60 to 120 entries, written the way proposal teams write: the question as buyers ask it (security questionnaires,
RFPs, AI risk reviews, procurement), the answer in two to six plain sentences, starting "Yes." / "No." where the
question is yes/no. If the org has a completed questionnaire (CAIQ, HECVAT) in its originals, at least a third of the
entries come from it, with the vendor's own answer text. `status` follows `last_reviewed` against the 180-day cycle
as of 2026-11-16 (Review due when older).

## 3. Planted faults: write them INTO answerbank.json / stacks.json and describe each in `keys/<org>/library-faults.json`
Plant 10 to 16 faults, a realistic mix, each one something that really happens in libraries:
- `stale`: an answer that was true per an older source and is now untrue per a newer one (a retired model, a changed
  limit or price, a renamed plan, a superseded certification scope). Evidence: the old quote AND the new quote.
- `duplicate-conflict`: two entries for the same question that disagree (one current, one stale or overstated).
- `roadmap-as-fact`: an answer that states something the sources call planned, beta, preview or coming as available.
- `overstated`: an answer that upgrades the source's strength ("supports" written as "guarantees", a partial scope
  written as all products, a regional option written as default).
- `past-review`: an answer marked Current though last reviewed long ago and now wrong or incomplete.
- `expired`: a Stacks item past its expiry whose content is out of date.
- `duplicate-file`, `internal`, `wrong-company`, `not-for-ai`: the build tool plants or derives these itself; don't write them.
```json
[{"id": "F-<org>-01", "kind": "stale", "where": {"answerbank": "AB-0042"}, "statement": "<the faulty claim as planted>",
  "evidence": [{"source": "<raw id>", "quote": "...", "role": "old|new|truth"}],
  "expected": "<what a good load does: supersede it, flag the conflict, mark needs-person, keep it out, say roadmap>",
  "severity": "high|medium|low"}]
```
Faulty entries look exactly like real ones (no hints in tags, owners or dates beyond what a real library would show).

## 4. `keys/<org>/silver.json`: fact questions with checkable answers
40 to 60 questions an enterprise buyer, security reviewer or procurement lead would ask, answerable from d1 originals,
spread across security, privacy, compliance, AI and data use, product scope, integration, commercial and company.
```json
[{"id": "Q-<org>-001", "question": "...", "answer": "<short, exact>", "type": "fact|number|date|yes-no|list|policy",
  "source": "<raw id>", "quote": "<verbatim span that proves it>", "holdout": false}]
```
Mark a random third `holdout: true`. Include at least 8 `yes-no`, 8 `number` or `date`, and 4 questions whose true
answer is "No" or "not offered" (a tool that says yes to everything must lose points).

## 5. `keys/<org>/changes.json`: what delivery d2 changes
For each d2 original (see split.json), the facts it changes about what a seller should say:
```json
[{"id": "C-<org>-01", "source": "<d2 raw id>", "quote": "<verbatim from the d2 source>", "stop_saying": "...",
  "say_instead": "...", "old_source": "<d1 raw id or null>", "old_quote": "<verbatim or null>"}]
```
Only real changes. A d2 item that changes nothing a seller says gets no entry.

## Finish
Run `python3 tools/verify_quotes.py <org>` until it passes. Report counts (items, entries, faults by kind, silver,
holdout, changes) and anything you doubted.
