# Protocol: how a run is done and scored

Written on 2026-11-16, before any run. Change it only by adding a dated section; never edit a rule after seeing a score.

## The question each run answers

How much of a real company's public knowledge does the AI step (Green Room's harness intake, then respond) turn into
answers that are right, current and safe to send, starting from the mess an SC actually inherits?

## A run

1. **Fresh root.** `GREENROOM_HOME` points to a new folder under `runs/<date>-<org>-<arm>-<model>/home`. Nothing else
   from earlier runs is visible.
2. **Delivery.** Copy `deliveries/<org>/d1/` into the workspace `inbox/` (the arm decides what the workspace looks like).
   d1 is exactly what the portals hand an SC: the Stacks library export (zip with its `manifest.csv`), the Answerbank
   export (`.xlsx`) and `links.txt` with the vendor's public pages. Nothing in `keys/` is ever copied or readable.
3. **The AI step.** One shot, no repairs, no hints beyond the arm's prompt. Log model, wall time, cost as the harness
   reports it, and every tool call.
4. **Respond.** Copy the blank questionnaire for the org (`deliveries/<org>/questionnaire/`) into a new engagement and
   run respond. One shot.
5. **Later deliveries.** For d2, d3... a fresh agent with no memory but the workspace loads the next delivery, as in the
   Davies data-model test.
6. **Snapshot.** The finished workspace, the logs and `score.json` stay in the run folder.

## Arms

| Arm | Workspace at start | Prompt |
|---|---|---|
| `greenroom` | Green Room template (`gr ws new`), its skills and checks | The app's own Knowledge and Respond jobs |
| `thin` | Green Room template plus the two workspace skills in `thin/skills` (added 17 Nov 2026) | The app's own Knowledge and Respond jobs; the thin skills file sources, answer from the documents and save the fact behind each answer |
| `bare` | An empty folder | "This folder's inbox has everything our sales team has on <Org>. Load it so we can answer security questionnaires and build decks from it, then answer the questionnaire in questionnaire/." |

Models: Opus 5.5 is the reference. Sonnet 5.5 and Haiku 5.5 give the cost curve. Same delivery, same scorer.

## Scores (tools/score.py), all against `keys/`

| Measure | What counts | How |
|---|---|---|
| Filing | Every original filed once; byte-identical copies filed once; internal-only items kept out; expired items not used as current | Deterministic from `sources/index.json`, sha256 and `keys/<org>/library-faults.json` |
| Faults caught | Each planted fault (stale answer, duplicate answer that disagrees, roadmap written as fact, past-review answer, internal file) is caught: superseded, flagged as a conflict, marked needs-person, or kept out | Deterministic where the fault has a fixed signature; otherwise an Opus judge reads the fault's evidence and the workspace |
| Questionnaire agreement | The workspace's Yes / No / N/A against the vendor's own completed form, row by row | Deterministic |
| Risky commitments | Rows answered Yes where the vendor's own answer is No or N/A. These are the costly misses | Deterministic |
| Fact questions | Silver questions from the originals, each with a verbatim quote checked against the source; judged right, partly right or wrong | Opus judge plus 20 hand checks per run |
| Relearn | After d2: the changes the delivery carries, found and turned into stop-saying lines | Matched against `keys/<org>/changes.json` |
| Cost and time | As the harness reports, API list price | From the run log |

Holdout: one third of the silver questions and one questionnaire per buyer pack are sealed in `keys/holdout/` and only
opened for a final run after a tool change. A score after fixing a tool on the holdout is not proof.

## Rules

- Score in counts and in money-equivalents of risk: a wrong Yes on encryption is worse than a missing answer.
- A run that reads `keys/` is void.
- Every judge decision is kept with its reason, and 20 per run are checked by hand before a number is quoted.
