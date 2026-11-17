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

## 2026-11-16 · Anthropic · Green Room 3.0.2 library check (reconcile only, on the learn above)

Green Room re-read the 102 library lines of the run above against the documents: "agrees" now needs every part to agree,
and a line a document backs only in part is held as "partly". The lead ran it twice. Same keys, same judge.
Folders: `2026-11-16-anthropic-v302-a` and `-b`.

| Measure | After the fix | 3.0.2 run a | 3.0.2 run b |
|---|---|---|---|
| Reconcile time, cost | (in the learn) | 20 min, $1.37 | 6.5 min, $1.56 |
| Planted library faults caught (18) | 9 | 15 | 14 |
| High-severity faults carried | 4 | 0 | 0 |
| Fact questions (33) | 31 right, 0 wrong | 32 right, 1 unknown, 0 wrong | 32 right, 1 unknown, 0 wrong |
| Lines sent to Confirm (disputed + held) | 13 | 47 | 47 |
| Judge | | $4.29 | $4.03 |

**The cost:** the new "partly" hold is mostly wrong about which lines to hold. Run a held 26 lines as partly, and 3 of
them were planted faults. Run b held 28, and 2 were. The other 23–26 are correct library answers. Nearly every reason
they were held is "the document doesn't mention part X", which means the documents are silent on it, not that they
narrow it. Disputes are precise: 11 of 14 (a) and 11 of 12 (b) are planted faults, and 2 of the other 3 are fair
narrowings the corpus didn't plant. Detail: `2026-11-16-anthropic-v302-a/HOLDS.md`.

**Still through:** MCP tunnels (a document table row Learn never made a fact), 32 MB (no primary document states it),
the old Fable price (held "partly", but the judge counts a held line with no superseding fact as carried), and in run b
the account-team line (small-model variance).

## 2026-11-17 · Anthropic · Green Room 3.0.3: partly-silent lines stay in use with a note

3.0.3 keeps a part-backed line in use, with an `unbacked:` note naming the part no document mentions, and disputes
only lines a document narrows. Respond now refuses to cite disputed, held or retired facts (the judge can't see
that). Folder: `2026-11-16-anthropic-v303-c`.

| Measure | 3.0.2 run a | 3.0.2 run b | 3.0.3 run c |
|---|---|---|---|
| Reconcile time, cost | 20 min, $1.37 | 6.5 min, $1.56 | 6.6 min, $1.60 |
| Planted library faults caught (18) | 15 | 14 | 14 |
| High-severity faults carried | 0 | 0 | 0 |
| Fact questions (33) | 32 right, 1 unknown | 32 right, 1 unknown | 32 right, 1 unknown |
| Lines sent to Confirm | 47 | 47 | 26 |
| Disputes that are planted faults, or fair narrowings | 13 of 14 | 12 of 12 | 13 of 18 |
| Judge | $4.29 | $4.03 | $5.78 |

**Result:** the same catch as 3.0.2 at a little over half the Confirm load. The 25 noted lines include 2 planted
faults. AB-0090 (old price) is safe only if drafting obeys the note; AB-0006's real fault is its 48-hour clash with
AB-0007, and AB-0007 is disputed. Disputes got looser: 5 of 18 are false.
- AB-0010: SCIM is Enterprise, but Learn wrote a loose "Team and Enterprise" fact.
- AB-0052: the library already says "for some classifiers".
- AB-0068: mixes up Claude Code via Foundry with Claude in Foundry, as before.
- AB-0085: reverse engineering is in the terms document, but no fact was written for it.
- AB-0099: the document says ZDR is available on request for those platforms, word for word.
Three of the five come from a missing or loose learned fact, not from reconcile.

Still carried: MCP tunnels, 32 MB, the old Fable price (the judge counts a noted line as current), and the
account-team line (it varies between runs).

## 2026-11-17 · Anthropic · Green Room 3.0.4: lists don't exclude, unbacked parts lower confidence

3.0.4 tells reconcile that a list doesn't exclude anything unless it says only, not, except or excluding, and it
counts the library line's own some, may and on-request. Respond drops an answer resting on an unbacked part to Check it,
or to Needs you when it states a number that only the note carries (the judge can't see this).
Folders: `2026-11-16-anthropic-v304-d` and `-e`.

| Measure | 3.0.3 run c | 3.0.4 run d | 3.0.4 run e |
|---|---|---|---|
| Planted library faults caught (18) | 14 | 13 | 14 |
| High-severity faults carried | 0 | 1 (AB-0032, no processing outside the US) | 0 |
| Fact questions (33) | 32 right, 1 unknown | 32 right, 1 partly right | 31 right, 1 partly right, 1 unknown |
| Disputes: planted / fair / false | 11 / 2 / 5 | 10 / 2 / 2 | 11 / 2 / 3 |
| Judge | $5.78 | $3.90 | $4.65 |

False disputes:
- Run d: AB-0010 (the lumped SCIM fact) and AB-0013 (the Compliance API document says what the library says).
- Run e: AB-0027 (the DPA has the self-service clause), AB-0054 (the 3.01% figure is in the Sonnet 5.5 system card) and
  AB-0099 (the "list as exclusive" misreading again).
- Three of the five are facts Learn never wrote or lumped together.
- One false dispute cost a fact: in run e, question Q-042's figures exist only in AB-0054, which was disputed, so it
  dropped to partly right.

**Reading:** run to run, the noise is about as large as the change. AB-0032 is caught in one 3.0.4 run and missed in the other.
The lever left is Learn precision (one fact per table row and per terms clause, no lumped plans), as the lead said.

## 2026-11-17 · A plain prompt as the control (Atlassian, Anthropic)

The `bare` idea from the protocol, run for the first time: an empty folder, the same delivery d1, one plain prompt (kept as
`prompt.txt` in each run folder), Claude Code on Opus, keys out of reach. One run each.

| Test | Plain prompt | Green Room Respond after Learn (16 Nov) |
|---|---|---|
| Atlassian's own CAIQ, blanked, the same 60 seeded rows | 59 agree, 0 disagree, 1 left to a person; 349 s; $2.59 | 42 agree, 0 disagree, 18 left to a person; 728 s; $7.57, after a 32 min, $24.57 learn |
| Anthropic written test, 26 questions, 10 traps | 10 traps handled, 0 risky, none sent to a person that the key answers; 346 s; $2.21 | 7 traps handled, 2 partial, 0 risky; 677 s; $5.11, after a 25 min, $17.52 learn |

- Atlassian: the plain prompt also wrote the buyer's workbook itself. 59 of 59 answered cells hold the vendor's value, both
  data validations and all 215 merged ranges survive. It flagged five rows with reasons and left one blank because the vendor's
  published No conflicts with its own explanation.
- Anthropic: Green Room's scorer marks 8 of the 10 traps handled; the other two (HR-02, MG-01) are free-text answers the scorer
  cannot compare, and both match the key when read (inference_geo "us" at 1.1x; RSP 3.4 effective July 8, 2026).
- Limits: one run each. The completed CAIQ is inside the library export for both arms, so the Atlassian test rewards finding
  and reusing last year's answers, and 59 of its 60 key answers are Yes.
- What it showed about Green Room: Respond's rule "a Yes only when a saved fact states it outright" sent 18 answerable rows
  to a person. Folders: `2026-11-17-atlassian-bare-vendor-form`, `2026-11-17-anthropic-bare-written`.

## 2026-11-17 · Thin skills, and packs from the open deliveries (GitLab, PostHog, Supabase)

Green Room's own intake and respond jobs, run with the two short workspace skills in `thin/skills` (a workspace skill replaces
the app's skill of the same name): thin intake files the sources and writes no facts; thin respond answers from the documents
and saves the fact behind each answer with the exact sentence it rests on. Inputs are the deliveries a public cut of this
repository builds by itself (openly licensed originals only, no links fetched). Sonnet, one run each. The questionnaire is each
company's written test, cut to the questions whose sources are all open.

| | GitLab | PostHog | Supabase |
|---|---|---|---|
| Filing: time, cost | 143 s, $0.75 | 69 s, $0.38 | 84 s, $0.43 |
| Sources filed | 34 | 16 | 15 |
| Answering: time, cost | 124 s, $0.66 | 142 s, $0.72 | 155 s, $0.71 |
| Questions answered / sent to a person | 11 / 3 | 12 / 4 | 13 / 6 |
| Traps handled | 6 of 6 | 5 of 5 | 5 of 8, 2 more sent to a person (safe) |
| Risky answers | 0 | 0 | 0 |
| Facts saved, each with its sentence | 20 | 21 | 23 |
| `gr check` | pass, 4 warnings | pass, 5 warnings | pass |
| Whole run | 4.5 min, $1.41 | 3.5 min, $1.10 | 4.0 min, $1.14 |

- Filing honoured the mess: items flagged not for AI and the internal file were kept out, byte-identical copies were filed once.
- GitLab has one wrong answer (PLT-03: a No where the key says Yes, as an add-on). Several free-text answers the scorer marks
  "different" match the key when read.
- Each finished workspace is a pack in `packs/` (`packs/index.json` lists bytes and sha256). A pack imports into Green Room with
  its own unpack in under a second, passes its checks, and needs no paid job. The buyer's file is in each pack with the drafted
  answers written back by Green Room's return code.
- Compare the earlier learns on this page: 25 to 43 minutes and $17 to $28 before a single question was answered.
