# SC Open Corpus: design

**What it is.** Real, public material from real companies, set up the way a solution consultant (SC) actually finds it
on day one, so Green Room can be tested, improved, demoed and (for the openly licensed part) shared. As of
**2026-11-16**; every source carries its own fetch date and refreshes on demand.

## The one idea: Green Room is the AI step

Davies proved it for bank files: a frontier model in a harness reads messy originals better than an importer written
for them, so ship a fixed shape, checks, a page and a small skill, and score the load against sealed truth. This
corpus applies the same method to SC knowledge:

```
 BEFORE AI                                   THE AI STEP                     AFTER AI                 SCORED BY
 originals where they really live     ─►     Green Room intake / respond ─►  a Green Room workspace ─► sealed answer keys
 (content library, answer library,           (harness + skill + checks)      (sources, docs, claims,   (the vendor's own
  tender portal, vendor sites)                                                answers, slides)          questionnaires, buyer
                                                                                                        Q&A, quote-checked facts,
                                                                                                        planted library faults)
```

- **Before AI** is never cleaned by hand. It is the originals exactly as fetched, plus the places an SC collates them
  from: a sales content library, an answer library and a buyer's tender portal (`portals/`). Those carry the real
  mess: duplicate copies, `FINAL_v2` files, expired items, an internal-only file that must stay out, answers past
  their review date, answers a release has made untrue.
- **After AI** is only ever what Green Room produces. Each run is kept as a dated snapshot in `runs/` with its model,
  time and cost, so arms (models, skill versions, template vs empty folder) can be compared.
- **Answer keys** are independent of Green Room and sealed in `keys/` (runs never read it):
  1. *Gold by construction*: a vendor's own completed questionnaire (CAIQ, HECVAT) answers that vendor's blank form;
     a buyer's published clarification answers answer the questions vendors asked.
  2. *Planted truth*: every fault planted in the libraries, with the evidence that makes it a fault.
  3. *Silver*: questions written from the originals whose quoted span is checked to exist verbatim in the source.

## What earlier runs taught (and how the design answers)

| Learned | Where | So the corpus... |
|---|---|---|
| A real sales library is mostly decks (58% PPTX, 21% PDF of 5,696 items); almost every item has an expiry; half are past v1; ~22% are marked Do Not Allow in AI; ~40% are employee-only; hundreds carry a previous tool's fields after a migration | A real enterprise sales library of 5,696 items, 14 Nov (structure and counts only) | Stacks uses that item shape and those proportions, and its export is a zip plus a manifest with those columns |
| Public onboarding of a big vendor stalls on fetching: product and trust pages refuse, docs are JavaScript shells, and no public .pptx existed, so 0 slides landed | A large enterprise vendor's public material, 15 Nov | Companies were chosen for what an SC can actually get; real decks were a priority; every refusal is recorded, not worked around |
| A webinar PDF stamped Confidential slipped into knowledge and had to be withdrawn by hand | Same run | Every library carries an internal-only file and Do-Not-AI items; keeping them out is scored |
| Reading is solved; the misses are meaning calls, in lumps. Score in impact, not just counts. A fixed shape plus checks is worth what plugs into it | Davies, "The harness is the importer" | Green Room's harness intake is the AI step; risky commitments (a Yes the vendor says No to) are scored separately |
| Holdouts stay unseen while a tool is built | Proving Ground, E6 | One third of every key is sealed |
| Public decks are rare: of 300 Google Slides links in GitLab's handbook, 286 need sign-in and 7 are deleted; one exported deck said "internal only" on its last slide | This harvest, 16 Nov | Real decks are kept wherever they exist (GitLab, Microsoft readiness decks, a federal industry-day deck); the internal one was dropped |
| Vendor docs now carry text addressed to AI agents (Supabase's markdown asks the agent to make the user send feedback) | This harvest | Scored: a good load treats it as page text and says it found it |
| Retired services break harvests (UK Digital Marketplace DOS now 500s); many trust centres gate the best documents behind request flows | This harvest | Failed fetches are recorded with reasons; the corpus says what it could not get |

## Deliveries, like the bank files

A company's knowledge arrives over time. `deliveries/<org>/d1` is the as-of snapshot as the SC would first collate
it; `d2` is what changed (new release notes, a deprecation, a refreshed whitepaper, a superseded answer). Fresh
agents load each delivery with no memory but the workspace, exactly as the Davies data-model test did. The refresh
tool makes the next real delivery from the live web: re-fetch, diff, write what changed.

## What is in it

| Track | Orgs | Why they are here |
|---|---|---|
| Open handbooks | GitLab, PostHog, Supabase | The best public sales/SA/CS playbooks anywhere (GitLab's handbook is CC BY-SA), real decks, monthly releases and deprecations, open-source-built products |
| SaaS trust | Atlassian, Stripe | Security whitepapers, completed CAIQ, a public cloud roadmap (tests roadmap vs capability), builder docs, pricing |
| AI labs | Anthropic, OpenAI, Microsoft | System cards, business guides, data-use answers buyers ask about AI, model deprecations; Microsoft adoption kits as real .pptx/.xlsx |
| Buyers | UK Digital Marketplace, 18F/TTS, universities and states, CSA, NIH | Real RFx with real buyer Q&A, completed vendor questionnaires (answer keys), winning proposals, buyer evaluation criteria |

Private material never enters this repository; it runs through a local overlay with the same tools.

## Sharing

Every source records its licence. `redistributable: true` (CC BY, CC BY-SA, MIT, Apache, OGL, US public domain) ships
in the public cut and on the public portals; everything else stays on this Mac for private testing and the public
cut ships the exact URL and a fetch script instead (the HECVAT pattern already used in the Proving Ground).

## Layout

```
HARVEST.md            rules every harvester followed
catalog/sources.json  every original: org, genre, kind, url, dates, sha256, licence, why, SC jobs
raw/<org>/            the originals, byte for byte              (before AI, layer 0)
library/              the collated mess: content library, answer library, tender packs (before AI, layer 1)
portals/              the three portals that serve library/, built static for Vercel
deliveries/<org>/dN/  what a run receives in its inbox
keys/                 sealed answer keys                         (never read by a run)
runs/<date>-<org>-<arm>/  Green Room workspaces after the AI step, with cost and time
tasks/                graded tasks (TheAgentCompany format, as in the Proving Ground)
tools/                catalog, check, build library, deliver, refresh, score
PROTOCOL.md           how a run is done and scored, written before any run
```
