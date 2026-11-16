# SC Open Corpus: notes for agents

Plain-text companion to the SC Open Corpus page. Same facts, no layout. Read `VISION.md` before changing anything.

## What it is

A public test company for sales knowledge. Real, public material from eight companies (Atlassian, Stripe, Anthropic,
OpenAI, Microsoft 365 Copilot, GitLab, PostHog, Supabase) and thirteen real public tenders, laid out the way a solution
consultant (SC) inherits it, with answer keys that score what any harness makes of it. As of 2026-11-16.

## The shape

1. Before AI: the originals, byte for byte, sitting in three portals with their real mess.
   - Stacks: a sales content library. Its export is a zip with a manifest (version, expiry, customer-facing,
     employee-only, Do Not Allow in AI, fields left over from a previous tool).
   - Answerbank: an RFP answer library. Its export is a spreadsheet (question, answer, owner, last reviewed).
   - Tenderline: buyers' public opportunities with documents, addenda and clarification answers.
2. The AI step: your harness loads a delivery. In Green Room that is the Learn job, a skill run by Claude Code (or
   Codex), held to the workspace contract by `gr check`. The corpus ships no importer.
3. After AI: the workspace the run made, kept as a dated run with model, time and cost.
4. Scored by `tools/score.py` and `tools/test.py` against `keys/`, which a run never reads while it loads.

## The mess, and where each kind came from

- Byte-identical copies under other names (FINAL, Copy of, (1)): real libraries.
- Expired items: almost every item in a real library has an expiry date.
- Employee-only and Do Not Allow in AI flags: about two fifths and one fifth of a real 5,696-item library.
- An internal file in the export: a confidential-stamped PDF slipped into a real load and had to be withdrawn.
- A document about another company: misfiling happens; Green Room checks loose files for it.
- A scan with no text layer: one company publishes its shareholder letter that way.
- Answers a release made untrue, answers that overstate the source, roadmap written as fact: what drifts in answer libraries.
- Text addressed to AI agents inside vendor docs: found in real documentation during the harvest.
- Real faults in a vendor's own material, kept as found: for example a questionnaire that gives a release day the release notes contradict.

## Keys

- Gold by construction: vendors' own completed CSA CAIQs (Atlassian, GitLab; more vendors in the buyer track) answer
  their own blanked forms; buyers' published clarification answers.
- Planted truth: every planted fault with the evidence that makes it a fault.
- Fact questions: each with a verbatim quote checked against the source text (`tools/verify_quotes.py`).
- Keys for openly licensed material are public. Proof comes from the next delivery, which no tool has seen.
- A Yes the vendor says No to is a risky commitment and is counted on its own.

## What the first runs found (Green Room Learn, default model, 16 Nov 2026)

- Anthropic: 25 min, $17.52, 318 facts. Every expected file filed once; internal and Do-Not-AI items kept out;
  fact questions 29 right, 4 partly right, 0 wrong. Planted library faults: 3 caught, 15 carried.
- Atlassian: 32 min, $24.57, 244 facts. 43 of 43 files filed once; fact questions 31 right, 2 partly right, 1 unknown,
  1 wrong. Planted faults: 3 caught, 15 carried. Atlassian's own CAIQ, blanked, 60 rows sampled: 42 answered and all
  42 agree with Atlassian's answers, 18 sent to a person, 0 risky Yes ($7.57).
- The finding: reading documents is solved; the old answer library was imported as fact and never reconciled with the
  documents. Green Room changed Learn the same day so an answer-library export is a secondary source, reconciled
  against primary facts, with conflicts shown side by side.

## Choices, and why

- Real public material over a synthetic company: tools must face real layouts, refusals and drift.
- The mess left in over a cleaned set: the mess is what an SC inherits and what tools get wrong.
- The harness as importer over a shipped importer: a frontier model in a harness reads messy files better; ship a
  shape, checks and a skill.
- Runs over gold: a run is evidence of one tool on one day, never the truth.
- Open keys plus fresh deliveries over a hidden holdout: anyone can score; the next delivery is the unseen test.
- Two repositories (the tool, the corpus) over one: the corpus never bends to make one tool look good.
- Private material never enters the repository: a deny list outside the repository blocks it at every public cut.

## Use it

- Browse: https://sc-open-corpus.vercel.app (openly licensed files hosted; others link to their originals).
- Load: build the libraries and workspaces, then run Learn with your harness (`README.md`, "Do a run").
- Refresh: `python3 tools/refresh.py` turns real changes on the live web into the next delivery.
