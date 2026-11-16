# SC Open Corpus

A public test company for sales knowledge. Real, public material from real companies (GitLab, Atlassian, Stripe,
Anthropic, OpenAI, Microsoft, PostHog, Supabase) and real buyers (UK Digital Marketplace, 18F, universities, states),
set up the way a solution consultant actually inherits it, with sealed keys to score whatever your harness makes of it.

Fresh as of **2026-11-16**. Every file records its own fetch date, licence and sha256; `tools/refresh.py` makes the
next delivery from the live web.

- **Before AI**: the originals, sitting in three portals with their real mess: **Stacks** (a sales content library
  shaped like a real enterprise content library's item model), **Answerbank** (an RFP answer library with owners and review dates) and
  **Tenderline** (public opportunities with documents, addenda and clarification answers).
- **The AI step**: your harness loads the portal exports. In this project that is Green Room
  ([green-room](https://github.com/EthDawg/green-room)), whose intake is a skill run by Claude Code: the harness is the importer.
- **After AI**: the workspace it made, kept per run in `runs/`, with model, time and cost.
- **Scored** by `tools/score.py` against `keys/`: each vendor's own completed questionnaire, buyers' published
  answers, quote-checked fact questions, and every fault planted in the libraries.

Read `VISION.md` (what this project accepts and refuses), `DESIGN.md` (why it is shaped this way), `PROTOCOL.md` (how a run is done and scored, written before any run),
`HARVEST.md` (how sources were collected) and `catalog/STATS.md` (what is in it).

Want more material to test with? `docs/SOURCES.md` points to where good public SC material lives, by kind, without ranking it.

## Do a run

```
python3 tools/catalog.py && python3 tools/extract.py          # catalog and text cache
<green-room>/.venv/bin/python tools/build_library.py   # libraries, exports, deliveries
python3 tools/run.py <org> --arm greenroom --model opus       # fresh GREENROOM_HOME, d1, intake, respond
python3 tools/score.py runs/<run>/home/workspaces/<org> <org> --judge
python3 portals/build.py --local && portals/serve.sh           # browse at 127.0.0.1:8781 what the run started from
```

## Licences and sharing

`catalog/sources.json` records each original's licence. Openly licensed files (CC BY, CC BY-SA, MIT, Apache, OGL, US
public domain) are hosted on the public portals and can be redistributed under their own terms; everything else is for
private testing only and is never redistributed: the public cut links to the original and `tools/fetch.py` fetches it
for you. The libraries contain deliberate faults for testing; nothing in them is an official statement by the
companies named. Code: MIT (`LICENSE`). Fixtures and keys written for this corpus: CC BY 4.0 (`LICENSE-CONTENT.md`).
