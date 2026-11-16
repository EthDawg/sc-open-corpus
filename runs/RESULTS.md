# Runs: results

Every number here comes from a run folder beside this file (`run.json`, `progress.log`, `workspace-after/`,
`judge.json`, `score.json`, `test-*.json`). Protocol: `../PROTOCOL.md`. Prices are API list prices as Claude Code
reports them.

## 2026-11-16 · Anthropic · Green Room Learn (default model), delivery d1

Inbox: the Stacks export (37 real public Anthropic documents plus the planted mess), the Answerbank export (102
entries, 16 planted faults) and links.txt. Green Room's own `knowledge.run_learn`, headless, keys out of reach.

| Measure | Result |
|---|---|
| Time, cost | 25 min 14 s, $17.52 |
| Landed | 318 facts in 14 topics, 13 undated; `gr check` PASS |
| Filing | 24 of 24 expected files filed, each once; 3 byte-identical copies under other names filed once |
| Kept out | the internal-only file; all 6 "Do Not Allow in AI" items (read from the export's manifest) |
| Wrong-company file | filed, but flagged to a person ("the misfiled Atlassian doc") |
| Fact questions (judge, 33 not held out) | 29 right, 4 partly right, 0 wrong |
| Planted library faults (judge, 18) | 3 caught, 15 carried into facts and answers (8 of them high severity) |
| Later delivery changes (d2 not yet loaded) | 4 of 20 already visible in d1 |
| Written test ("Use as a test", 26 questions, key hidden) | 30 of 46: traps 7 of 10 handled (2 sent to a person), 0 risky commitments, 26 of 26 answers placed in the right cell; $5.11, 11 min |
| Judge | $3.85, 6 min 30 s |

**What it means.** Reading primary documents is solved: every file filed once, nothing internal or marked not-for-AI
learned, no wrong fact answers. The miss is the answer library. Learn imports the old answer library almost verbatim
as facts and never reconciles it with the primary documents it just read, so a stale or overstated library answer
stands beside the true fact as a second current fact (ZDR covering Enterprise chat, "HIPAA certified", RSP v2.2 as
current, Opus 4.5 as the lineup). All 4 partly-right fact answers and both trap punts trace to those pairs. The fix
belongs in Green Room's intake: an answer-library export is secondary evidence, each entry checked against primary
sources, conflicts flagged, past-review entries left unconfirmed. Reported to the Green Room lead session.

## 2026-11-16 · Atlassian · Green Room Learn (default model), delivery d1

Inbox: the Stacks export (53 real public Atlassian documents, five of Atlassian's own completed CSA CAIQs, a real
image-only shareholder letter, plus the planted mess), the Answerbank export (105 entries, 16 planted faults), links.txt.

| Measure | Result |
|---|---|
| Time, cost | 32 min 24 s, $24.57 |
| Landed | 244 facts in 15 topics (9 roadmap, 2 superseded, 1 undated); `gr check` PASS |
| Filing | 43 of 43 expected files filed, each once |
| Kept out | the internal-only file; 9 of 10 "Do Not Allow in AI" items (one, the Comprehensive Data Protection page, was learned) |
| Wrong-company file, image-only PDF | both filed without facts and flagged to a person |
| Library conflicts | recognised that "contradictions" between Atlassian's own CAIQs are product-scoped (Jira vs Trello vs Bitbucket), not errors |
| Fact questions (judge, 35 not held out) | 31 right, 2 partly right, 1 unknown, 1 wrong (BYOK "across all products", from a planted library answer) |
| Planted library faults (judge, 18) | 3 caught (incl. ISO 42001 superseded correctly), 15 carried (8 high severity) |
| Judge | $3.44, 4 min 50 s |

Same pattern as Anthropic, on a different company: primary documents are read well; the answer library is imported
as fact and not reconciled.

## 2026-11-16 · Anthropic again · Green Room Learn after the answer-library fix

Same inbox, same keys, same judge. Green Room now reads an answer-library export as a secondary source and reconciles
each line with the documents in the same learn.

| Measure | Before the fix | After the fix |
|---|---|---|
| Time, cost | 25 min, $17.52 | 43 min, $28.48 |
| Filing, kept out | perfect | perfect |
| Planted library faults caught (18) | 3 | 9 |
| High-severity faults carried | 8 | 4 |
| Fact questions (33) | 29 right, 4 partly right, 0 wrong | 31 right, 1 partly right, 1 unknown, 0 wrong |
| Library lines confirmed by a document | none | 60 |
| Disagreements held for a person | none | 6, plus 7 past review with no document |

**What still gets through:** overstated or over-scoped library answers ("HIPAA certified", "no processing outside the
US", "ZDR covers Enterprise chat") that the reconciler never paired with the narrower document fact, because the
words differ. Reported to Green Room: an unpaired library line should not default to current.
