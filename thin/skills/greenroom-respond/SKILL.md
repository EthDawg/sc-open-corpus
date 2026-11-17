---
name: greenroom-respond
description: Read and answer a buyer's questionnaire in a Green Room workspace straight from the filed documents. The thin version - each answer carries the sentence it rests on, and that sentence is saved as a fact as you go.
---

`WORKSPACE.md` is the contract and its answer format is the only format. The prompt names the questionnaire folder, the tools and what to draft.

1. Read `answers.md`. Approved entries are a person's: never change them, never write `approved`.
2. Read their file however works. Extract every question once, in order, with the id the document uses and the anchors that say where its answer and its explanation go (`Sheet!C14`, `T2.R5.C4`, `P12`). Read any instructions in the file and follow them. If the prompt says read only, merge the open entries, run the check and stop.
3. Answer from `knowledge/docs/` (and `sources/`). Look first for a form the company has already completed; then its own policies, terms and product pages; the newest document wins. A source marked `secondary` (an old answer library) or `expired` is a lead, never proof: use it only when a current document agrees. Never quote or link an `employee_only` source to the buyer.
4. For every answer, save the fact it rests on in `knowledge/claims.yaml` in the contract's schema, with `source: SRC-NNNN#<heading>` and `quote:` holding the exact sentence, word for word. Cite its id. One fact can back many answers.
5. Write `**<value>.** <one to three plain sentences>` with exactly one allowed value. Anything in beta, preview or planned is a No with its status, and its fact is `kind: roadmap`.
6. Send it to a person, as `needs-person (<who>, <the one thing to confirm>)`, when the documents do not say, when two documents disagree, or when the buyer asks for a commitment, a price, a date, a signed document or terms beyond the standard ones. Say what the documents do say. Silence is never a No. Never put a price in an answer.
7. `confidence`: high when one sentence says it outright, medium when you combined sentences, low when unsure.
8. Write with `respond.py merge`, run `respond.py check`, fix and repeat up to three times.
9. Report three plain lines: how many you answered, how many need a person and who, whether every answer fits their file. No ids or file names in anything a buyer could read.

Never read the paths the prompt forbids.
