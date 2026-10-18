# IncidentWeave: Chunking Strategy Discussion Log

**Purpose:** the single place for all chunking-strategy discussion between Claude, GitHub Copilot in VS Code, and ChatGPT. The maintainer (Swayam) makes the final decisions.

## Participants

| Name | Role in this log | What it can see | How it takes part |
|---|---|---|---|
| **Claude** | **Strategy planner**: analysis, evaluation design, recommendations, review of Copilot's work | Only the files the maintainer uploads to the Claude chat | The maintainer pastes this file (or recent entries) into the Claude chat; Claude appends its entry |
| **ChatGPT / Codex** | **Strategy planner**: independent analysis and review; plans together with Claude | Plain ChatGPT: only what the maintainer pastes. Codex: the repository, if the maintainer gives it access (state which one is writing) | Pasted into or run by the maintainer; its answer goes in the ChatGPT block |
| **Copilot** | **Implementer** ("vibe coder") in VS Code | The repository and this file directly | Implements only what the planners have agreed; then records files changed, commit SHA, commands run and output |
| **Maintainer (Swayam)** | Decisions, relaying between tools, running commands | Everything | Updates "Decisions" and "Current status"; relays text between the tools |

**Relay rule:** Claude and ChatGPT cannot read the repository or each other's chats. They only know what is in this file plus what the maintainer pastes. So every entry must be self-contained, and file or command output they need must be pasted into the log as an entry. If a participant cites something it has not seen in this file, it must label it Unverified.

**Scope:** chunking only. Retrieval ranking and golden-set label questions are logged here only when they bear on the chunking decision.

**Status:** Harness committed and both authorized experiment arms completed; retrieval favors 100/20, but adoption remains provisional pending Gate 5 human correctness review. See "Current status" below and entries [011]–[012].

---

## Workflow and roles

1. **Planners decide together.** Claude and ChatGPT/Codex analyze, design and review. An item is **Agreed** only when both planners have recorded agreement in this log. If they disagree, both positions stay visible and the item is marked "Open: maintainer to decide".
2. **Copilot implements, only what is Agreed,** and only within the agreed scope. It does not add scope or change the plan on its own. If the plan does not fit the code, Copilot stops and records the problem instead of improvising.
3. **After each implementation step Copilot writes an entry** with: files changed, commit SHA, commands run and their output, any deviation from the plan, and anything it could not do.
4. **Planners review Copilot's report** (the maintainer pastes the diff or output to planners who cannot see the repo) and record "accepted" or "changes needed" before the next step starts.
5. **Anyone may write this file.** Follow the append-only rules below, sign every entry, and commit after each entry so the three tools do not overwrite each other's changes.
6. **Repository facts** reported by Copilot (or by Codex with repo access), with the command output pasted, count as Confirmed. Planner statements about code they have not seen are Unverified.
7. **Maintainer approval gates (proposed, pending the maintainer's confirmation as D6):** the maintainer approves (a) before Copilot starts each implementation step, (b) before any change to production ingestion or the golden set, and (c) to break a tie when planners disagree.

---

## How to use this file

1. **Append only.** Add new entries at the bottom of "Discussion log". Do not rewrite or delete earlier entries. If something turns out wrong, add a correction entry that references the original.
2. **One entry per turn,** numbered in order: `[001] Claude`, then replies `[001-R] Copilot` and `[001-G] ChatGPT`, then `[002] Claude`, and so on. Each main entry leaves a reply block for Copilot and for ChatGPT directly beneath it. Anyone may also start a numbered entry; sign it with your name.
2a. **Planners challenge each other.** Claude and ChatGPT/Codex should check each other's assumptions, reasoning and decision criteria, and say what they disagree with and why. Do not repeat the analysis. If you agree, a short statement is enough.
2b. **Disagreements stay visible.** If participants disagree, record both positions with their reasons and mark the item "Open: maintainer to decide". Do not silently overwrite another participant's position.
3. **Label every statement:** `Confirmed` (from a file, a saved report, or command output), `Recommendation`, `Hypothesis`, or `Unverified`. Say where a confirmed fact came from.
4. **Do not change production ingestion** (`scripts/ingest_repo.py`, `scripts/embed_chunks.py`, `app/`) until the maintainer approves based on evaluation evidence.
5. **Do not edit `evaluation/golden_set.json`** to improve scores. Label changes are proposed in this file and decided by the maintainer.
6. When Copilot implements something, record the files changed, the commit SHA, and the test or run output.
7. When a decision is made, update the "Decisions" table and "Current status".

---

## Current status

| Item | State |
|---|---|
| Baseline | 60-line windows, 10-line overlap, Python files only, no AST (`scripts/ingest_repo.py::chunk_lines`) |
| Baseline run used for initial analysis | `20261015T151657Z-c203e0e` (top-5 chunk IDs identical to `20261014T160330Z-305200f`) |
| Corpus | pinned SHA `62d0e58593bb22d187ec7930274b0457afd3be74`, 40 files / 70 chunks |
| Golden set | 24 questions, sha256 `5f4c27469a1e1836c47d4485e2091a9c70546dc52ce1e824b44f6380d1b42914`, status "pending maintainer review" |
| Diagnosis of the 5 Hit@5 misses | Done (entry 001) |
| Vector-ranking export (all 70 chunks per missed question) | Script provided; output not yet reviewed. Optional before building; recommended before interpreting results ([002]). |
| Completed paired experiment | 60/10 `20261018T123627Z-2274338-baseline` vs 100/20 `20261018T124223Z-2274338-w100_o20`; see [011] and [012] |
| Reviews received | Claude [001], ChatGPT [001-G], Codex with repo access [002-G], Claude review of Codex [003], ChatGPT [005], Copilot [006], Codex [007], Claude [008]. Historical empty response blocks remain unchanged. |
| Pinned-commit audit (Codex [002-G]) | Done. The uploaded `investigate.py`, `persistence.py`, `audit.py` do NOT match the pinned corpus; E3 rows based on them are superseded by [003]. Chunk count: 70 at 60/10, 52 at 100/20. |
| Planner agreement | D3, D4, and D6 are approved by the maintainer in entry [004]. The D4 disagreement in [003] remains in the historical discussion and is resolved by the maintainer's recorded decision. |
| Harness implementation | Committed as `22743382a4980d7787bc798d9ad8e2ab6ddecb18`; see [011]. |
| Evaluation-owned insertion equivalence | **Not established.** Source inspection shows evaluation chunks use the same path/range/content shape and the existing embedding helper, but no side-by-side database verification against production ingestion has been run. |
| Experiment run | **Completed** for both arms, recorded in [011]. D4 retrieval/safety gates 1–4 and 6–9 pass; Gate 5 human end-to-end correctness remains pending. No adoption approval is claimed. |

---

## Decisions

| # | Decision | Decided by | Date | Notes |
|---|---|---|---|---|
| D1 | Keep production chunker unchanged during experimentation | Maintainer | 2026-10-17 | Constraint from the original brief |
| D2 | Reuse the existing evaluation runner and golden set; no duplicate evaluation system | Maintainer | 2026-10-17 | Constraint from the original brief |
| D3 | Run a fixed-window 100/20 chunking experiment against the existing 60/10 baseline | Maintainer | 2026-10-17 | Approved in [004]. The harness is authorized; running the experiment is not authorized by this decision. |
| D4 | Apply all nine approved adoption gates recorded in [004] | Maintainer | 2026-10-17 | Approved. MRR is supporting only, not an independent adoption route. The historical planner disagreement in [003] is retained and resolved by this decision. |
| D5 | Roles: Claude and ChatGPT/Codex are strategy planners who decide together; Copilot implements and records what it did; any participant may write this file | Maintainer | 2026-10-17 | See "Workflow and roles" |
| D6 | Maintainer approves each implementation step, production-ingestion or golden-set changes, and resolution of planner disagreements | Maintainer | 2026-10-17 | Approved in [004]. |

---

## Evidence log

### E1. Baseline metrics (Confirmed: saved report `20261015T151657Z-c203e0e`)

- 16 answerable questions: vector and hybrid both hit@1/3/5 = 8/11/11, MRR 0.5729. Direct questions 6/7/7 of 8; paraphrased 2/4/4 of 8.
- Full-text search returns nothing for 14 of 16 answerable questions.
- Guard: 16 true accepts, 0 false refusals, 4 true refusals, 4 false accepts.
- Both generation passes: 40 HTTP calls, 0 errors.

### E2. The five Hit@5 misses (Confirmed unless marked)

Rank-5 vector distance for each question comes from the saved report. FTS was `None` for every top-5 chunk of these questions, so hybrid rank equals vector rank.

| Question | Expected label | Saved top-5 (both passes identical) | Rank-5 distance |
|---|---|---|---|
| direct-08 | `scripts/investigate.py`: `final_confidence=result["confidence"]` | 5 test chunks (`tests/unit/...`) | 0.38696 |
| paraphrased-03 | `scripts/embed_chunks.py`: `outputDimensionality` | `embed_chunks.py:51-110` (rank 1), `chunk.py:1-52`, `test_db_models.py:1-33`, `vector_search.py:1-56`, `graph.py:151-210` | 0.43662 |
| paraphrased-05 | `app/investigation/guard.py`: `is_sufficient =` | `graph.py:101-160`, `graph.py:151-210`, 3 test chunks | 0.37786 |
| paraphrased-07 | `app/investigation/mcp_server.py`: `casefold()` | 3 test chunks, `mcp_server.py:51-110` (rank 2), `graph.py:51-110` | 0.41551 |
| paraphrased-08 | `app/investigation/persistence.py`: `tool_calls` | `graph.py:101-160`, `parsing.py:1-60`, `parsing.py:51-97`, 2 test chunks | 0.35507 |

Other confirmed facts:
- Test-file chunks fill 14 of 25 top-5 slots across the five misses, and 35 of 80 across all answerable questions.
- The guard accepted all five (best vector distance 0.34 to 0.41, under the 0.5 limit).
- The label substrings all exist in the index. The runner validates this before each run.

### E3. Chunk-boundary findings

> **Superseded in part by [003].** Rows for direct-08, paraphrased-08 and `audit.py` were computed from files that do not match the pinned corpus (Codex [002-G]: pinned `investigate.py` is 162 lines, `persistence.py` 85, `audit.py` 42). Use Codex's pinned-commit audit in [002-G] section B for those. The rows for paraphrased-03, -05 and -07 rest on chunk text from the saved report and stand, except that paraphrased-05 is corrected in [003].

| Question | Finding | Status |
|---|---|---|
| paraphrased-03 | `embed_text` spans lines 38–74. The label (line 46) is in chunk 1-60. The rank-1 chunk, 51-110, holds only the tail of the function. `EMBEDDING_DIMENSION = 768` is on line 26, outside the function. The 1-60 chunk (which has the label) was not in the top 5. | Confirmed (chunk text in saved report) |
| paraphrased-07 | `grep_search` spans lines 21–61. The label is inside chunk 1-60. The retrieved chunk 51-110 holds only line 61 of the function plus the tool wrapper. | Confirmed (chunk text in saved report) |
| paraphrased-05 | `guard.py` is 70 lines, so only chunks 1-60 and 51-70. The label (line 51) is in both. Not a boundary issue. | Confirmed |
| direct-08 | In the *uploaded* `investigate.py` (204 lines, chunks 1-60, 51-110, 101-160, 151-204), the label is on line 137 and the persistence call (126–147) is intact inside chunk 101-160. `investigate_repository` (54–167, 114 lines) spans all four chunks. | Confirmed for the uploaded file. **Unverified** that it matches the pinned corpus. |
| paraphrased-08 | In the *uploaded* `persistence.py` (93 lines, chunks 1-60 and 51-93), `persist_investigation` (11–93) is split. `audit = Audit(` (line 49) and both docstrings that mention "audit" are only in chunk 1-60. The label (line 69) is only in chunk 51-93, which has the word "audit" only on line 91. | Confirmed for the uploaded file. **Unverified** match with pinned corpus. |
| paraphrased-08 | `audit.py` (52 lines) is a single whole-file chunk with `retrieved_chunk_ids`, `response`, `model`, `latency_ms` and `tool_calls`. It is not an accepted label. | Confirmed for the uploaded file |

**Uploaded files versus the pinned corpus:** `docs/architecture.md` (revision `e104005`) places `investigate_repository` at `scripts/investigate.py` line 42 and the persistence branch at line 90. The uploaded file has them at lines 54 and 126. So the uploaded `investigate.py` probably differs from the architecture doc's revision, and may differ from the pinned corpus. **Unverified.** The ranking export prints the actual database chunk ranges and resolves this.

### E4. Provisional classification (Hypotheses pending the ranking export)

> **Correction ([003]):** paraphrased-05 is reclassified as "evaluation label and ranking, with a possible boundary contribution". Its label substring is in both `guard.py` chunks, but the function `evaluate_evidence_sufficiency` (lines 11-70) is whole in neither at 60/10 (Codex [002-G] B).

| Question | Provisional class | Reason |
|---|---|---|
| direct-08 | Embedding or ranking | Label chunk intact; test chunks occupy the top 5 |
| paraphrased-03 | Chunk boundary | Confirmed split of the answer function |
| paraphrased-05 | Evaluation label (plus ranking) | Model answered correctly from `graph.py`; label names `guard.py` only |
| paraphrased-07 | Evaluation label (plus ranking) | Answered correctly; boundary effect is one line |
| paraphrased-08 | Evaluation label, with a boundary contribution | `audit.py` is a better answer chunk but not accepted; label chunk lacks `Audit(` |

None are classified "insufficient evidence". For direct-08 and paraphrased-08 the model abstained correctly on the context it was given, but the relevant chunks existed in the index.

### E5. Ranking export (read-only diagnostic)

- Script: `iw_rank_export.py`, kept **outside the repo** (for example `%TEMP%\iw_rank_export.py`). It ranks all 70 chunks per question by cosine distance, using the project's own `search_vector` and the cached query embeddings in `evaluation\cache`. It makes no Gemini calls and writes nothing to the database.
- **Assumptions checked by Codex ([002-G] A):** `search_vector` returns the distance under the key `distance` (the script already falls back to it), applies `.limit(limit)` with no upper cap, and all 24 cached query embeddings are present locally. **Still unverified:** the script has not been run, and its other row keys (`file_path`, `line_start`, `line_end`, `content`, `id`) are assumed.
- **Output:** *pending. Paste results here as an entry once run.*
- How to read it: compare each label chunk's gap to rank 5 against the spread of the saved top 5. Spreads: direct-08 0.031, paraphrased-03 0.024, paraphrased-05 0.028, paraphrased-07 0.059, paraphrased-08 0.016. A gap within the spread is a near miss from ranking noise. A gap several times larger points to a semantic mismatch or a label problem. This is a heuristic, not a project standard.

---

## Discussion log

### [001] Claude (2026-10-17): Recommended next experiment

**Recommendation: run one new arm, a fixed window of 100 lines with 20 overlap (100/20), against the 60/10 baseline. Defer AST-aware chunking.**

**Why this experiment**
- At 100/20 the observed answer functions fit in one chunk: `embed_text` (37 lines), `grep_search` (41), `persist_investigation` (83), the guard function (about 60). `persistence.py` and `guard.py` become single chunks.
- A 60-line cap in an AST chunker would still split `persist_investigation` (83 lines). AST only helps here if its cap is raised, and that cap is effectively the same variable as window size.
- `chunk_lines(lines, chunk_size, overlap)` already takes size and overlap parameters, so almost no new chunking code is needed.
- It tests the boundary hypothesis in either direction (see outcomes below).

**Confidence:** moderate. The ranking export has not been reviewed. If `paraphrased-03`'s label chunk ranks far below the top 5, bigger windows are unlikely to help and this choice should be revisited.

**Expected benefit**
- *Realistic:* paraphrased-03 (likely), paraphrased-08 (possible, partial), paraphrased-07 (label chunk becomes whole, but the answer was already correct).
- *Not addressed:* direct-08 (label chunk already intact; test-chunk crowding), paraphrased-05 (label and ranking), label strictness, full-text search returning nothing, guard false accepts, model variance.
- *Ceiling:* Hit@5 moves from 11 to 12 or 13 of 16. One question is 6.25 points, so this is close to noise on its own.
- *Risks:* bigger chunks can dilute embeddings and hurt direct questions (7 of 8 at Hit@5); they inflate hit-by-label scoring; and they increase prompt size.

**Proposed implementation (nothing written yet)**
- **New `evaluation/chunk_experiments.py` (small):** a strategy table (`baseline=(60,10)`, `w100_20=(100,20)`) and a context manager that temporarily replaces `scripts.ingest_repo.chunk_lines` with a version using the chosen size and overlap, then restores it. This works because `ingest_repository` calls `chunk_lines(lines)` by module name. It also provides the expected-chunk computation for the experimental repository.
- **`evaluation/runner.py`:** thread a repository name and chunking strategy through `setup_eval_corpus`, `validate_eval_index`, `retrieval_records`, `run_pipeline_once` and `run_evaluation`. Default stays `incidentweave-eval` at 60/10.
  - Relax the hard-coded check that rejects any repository name other than `incidentweave-eval`. Allow only that name or `incidentweave-eval-<strategy>`.
  - Treat the experimental repository as an eval repository in the inventory guard.
  - Record strategy, size and overlap in the run metadata and run ID.
- **`scripts/run_eval.py`:** add a strategy flag. **Unverified:** I have not seen this file.
- **Untouched:** `scripts/ingest_repo.py`, `scripts/embed_chunks.py`, everything under `app/`.
- A default run must reproduce the saved baseline results.

**Evaluation plan**
1. Commit the harness change. Run both arms from that same clean commit on the same day.
2. Confirm the default run reproduces the saved baseline: hit@1/3/5 of 8/11/11, MRR 0.5729, guard counts 16/0/4/4, and the same top-5 chunk IDs.
3. Offline audit (no API): chunk counts, size distribution, and every golden label still in some chunk.
4. Embed the experimental repository. Query embeddings come from the existing cache (the key depends only on question text), so no extra query calls.
5. Compare retrieval-only metrics first. Hold fixed: corpus SHA, golden set sha256, limit 5, guard and calibration thresholds, prompt hash, models.
6. Full pipeline, 2 passes per arm (3 if outcomes vary).
7. Build a question-level paired table over all 16 answerable questions. Read the five misses and every changed question by hand.
8. Extra metrics: hit-by-file beside hit-by-label, top-5 context size and token usage, guard false accepts, citation relevance, unsupported answers on unanswerable questions.
9. Do not retune thresholds or edit the golden set during this comparison.

**Decision criteria (proposed; maintainer to confirm before any run)**
- *Adopt as a candidate if all hold:*
  - Hit@5 at least 13/16, or MRR up at least 0.05 with Hit@3 not lower.
  - No previously hit question lost without explanation.
  - Guard false accepts at 4 or fewer, and no new answered-unanswerable cases.
  - Hand-reviewed end-to-end correctness not lower.
  - Median tokens per question within about 1.5 times the baseline.
  - Gains sit on the boundary questions (paraphrased-03, -08), not from hit-by-label inflation (check hit-by-file).
- *Keep the baseline if:* gains are 1 question or less (and MRR up less than 0.05), any direct question regresses unexplained, or any hard gate fails. A tie goes to the baseline.
- *What each outcome means:*
  - Clear win: adopt 100/20 as a candidate; AST becomes optional.
  - Boundary gains but direct-question losses (dilution): this justifies an AST experiment.
  - No gain: chunking is not the lever; move to ranking (test-chunk crowd-out check, label review).

**Immediate next action:** run the ranking export and look only at paraphrased-03 and paraphrased-08. If the label chunk's gap to rank 5 is within the spread (0.024 and 0.016), go. If it is several times larger, paste the output here and Claude will reconsider before code is written. Then the maintainer approves or rejects D3 and D4.

**Open questions for the maintainer**
- Do the uploaded `investigate.py`, `persistence.py` and `audit.py` match the pinned corpus? (`git diff --stat 62d0e58593bb22d187ec7930274b0457afd3be74 -- <paths>`, or the chunk ranges in the export output.)
- Should `audit.py` be proposed as an alternative label for paraphrased-08, and `graph.py` for paraphrased-05? This is a separate, maintainer-owned label review, not tuning.

---

#### [001-R] Copilot response

> *Space reserved for GitHub Copilot. Suggested content: agreement or objections to the plan, the real structure of `scripts/run_eval.py`, any problems found in `evaluation/runner.py` while reading it for the threading change, and effort estimate. Label statements as Confirmed, Recommendation, Hypothesis or Unverified.*

**Copilot:**

&nbsp;

#### [001-G] ChatGPT / Codex response

> *Space reserved for ChatGPT. Suggested content: independent review of the diagnosis in E2 to E4, whether 100/20 is the right single experiment versus AST-aware chunking or another approach, whether the decision criteria are sound for a 16-question set, and any risk or confound that was missed. Label statements as Confirmed, Recommendation, Hypothesis or Unverified. Note anything you could not check because you have not seen the repository.*

**ChatGPT (independent review, pasted by the maintainer 2026-10-17):**

- **Recommendation:** Agree with Claude's choice of a 100/20 fixed-window experiment as the next chunking experiment. It is simpler than AST-aware chunking and directly tests the observed boundary hypothesis.
- **Recommendation:** Do not make the full vector-ranking export a prerequisite. The existing diagnosis is sufficient to justify this limited experiment. Investigate ranking further if the results require explanation.
- **Recommendation:** Establish a fresh baseline and run both arms using the same evaluation code revision, golden set, retrieval settings, and evaluation criteria. Do not demand exact reproduction of historical metrics unless the relevant code revision and corpus are identical.
- **Caveat:** The 16 answerable questions provide a small evaluation sample. Treat a gain as evidence for a candidate strategy, not proof of general superiority. Inspect per-question changes, answer quality, regressions, and context size.
- **Boundary:** Keep production ingestion unchanged until the experiment produces evidence supporting adoption.
- **Status:** Independent review only. ChatGPT has not inspected or executed the repository code.

---

### [002] Claude

**Entry [002] Claude (2026-10-17): response to ChatGPT's review [001-G]**

**Where we agree**
- 100/20 over AST as the single next experiment.
- Production ingestion stays unchanged until there is evidence.
- A 16-question sample supports "candidate", not "proven". Per-question changes, regressions, answer quality and context size are all in the evaluation plan in [001].
- *Note:* ChatGPT has not seen the repository, so its agreement is a review of the reasoning in this log, not a check of the underlying data. That is the correct scope for this review.

**Where I adjust my own position**
1. **The ranking export is not a prerequisite. Accepted.** [001] presented it as a go/no-go gate before approving the work. That was too strong: the harness change and the 100/20 run are cheap (about 40 generation calls per arm), so approving them does not need the export.
   - *Still recommended:* run it before interpreting results, in parallel with the build. It is free and read-only, and it is the only way to tell a "no gain" result caused by ranking from one caused by chunking. Skipping it breaks nothing.
   - This supersedes the "Immediate next action" paragraph in [001].
2. **Baseline reproduction: accepted in part.**
   - *Agreed:* the arm comparison uses a fresh baseline run and a fresh experimental run from the same commit, so historical numbers are not part of the decision. Generation outcomes are not expected to reproduce (Confirmed: they varied between passes and runs).
   - *Kept, with a narrower purpose:* retrieval metrics (hit@1/3/5 8/11/11, MRR 0.5729) and top-5 chunk IDs were identical in two saved runs made from different code commits, `20261014T160330Z-305200f` and `20261015T151657Z-c203e0e` (Confirmed). The corpus SHA and the chunking code are unchanged. So I keep this as a **regression check that the harness change did not alter the default path**, not as a decision criterion. If it does not reproduce, record the difference and investigate before trusting either arm. It is not an automatic failure.

**Still open for review**
- The adoption thresholds in [001] (Hit@5 at least 13/16, or MRR up at least 0.05; token ceiling of 1.5 times the baseline). ChatGPT did not comment on them. D4 stays pending until the maintainer confirms them.

**Status:** Claude and ChatGPT both recommend the 100/20 experiment. Copilot has not replied yet (`[001-R]`). D3 and D4 remain with the maintainer.

&nbsp;

#### [002-R] Copilot response

**Copilot:**

&nbsp;

#### [002-G] ChatGPT response

**Codex (repo access, 2026-10-17):**

##### A. Verified facts

| claim | Confirmed/Refuted/Unverified | evidence |
|---|---|---|
| **Confirmed:** pinned `investigate.py` matches neither Claude's uploaded 204-line copy nor the stated line 137 label: it is 162 physical lines; `investigate_repository` starts at 53 and `final_confidence=result["confidence"]` is line 126. | Refuted | `git show 62d0e58593bb22d187ec7930274b0457afd3be74:scripts/investigate.py`; `Measure-Object -Line` reported 162. |
| **Confirmed:** pinned `persistence.py` is 85 physical lines, not 93; `tool_calls` is line 69. Pinned `audit.py` is 42 physical lines, not 52. | Refuted | Corresponding `git show` commands; `Measure-Object -Line` reported 85 and 42. |
| **Confirmed:** `search_vector` returns `id`, repository/path/range/content, and `distance`--not `vector_score`; it applies `.limit(limit)` with no upper cap. `hybrid_search` later maps that distance to `vector_score`. | Confirmed | `app/retrieval/vector_search.py:11-50`; `app/retrieval/hybrid_search.py:63`. |
| **Confirmed:** all 24 SHA-256 question-text cache files are present locally. | Confirmed | PowerShell recomputed every golden-question SHA-256 and reported `cache_missing=0 ids=`. |

##### B. Offline chunk audit (60/10 vs 100/20)

**Confirmed:** I used the pinned commit exported outside the repo, `evaluation/corpus.py::export_snapshot`'s fixture exclusion, and `scripts/ingest_repo.py::iter_python_files`/`chunk_lines` semantics. It yields 40 files, 70 chunks at 60/10, and 52 at 100/20. No API, database, or repository write was performed.

| question | 60/10 label chunk; enclosing function whole? | 100/20 label chunk; enclosing function whole? |
|---|---|---|
| direct-08 | `101-160`; `investigate_repository` 53-149: no | `81-162`; no |
| paraphrased-03 | `1-60`; `embed_text` 38-74: no | `1-100`; yes |
| paraphrased-05 | `1-60`, `51-70`; `evaluate_evidence_sufficiency` 11-70: no | `1-70`; yes |
| paraphrased-07 | `1-60`; `grep_search` 21-61: no | `1-100`; yes |
| paraphrased-08 | `51-85`; `persist_investigation` 11-85: no | `1-85`; yes |

##### C. Harness feasibility

**Confirmed:** the proposed monkeypatch is sound for the ingestion call only: `scripts.ingest_repo.ingest_repository` resolves its module-global `chunk_lines` at runtime. It is insufficient by itself because `evaluation/runner.py:30` imported `chunk_lines` directly and `setup_eval_corpus` uses that separate binding at line 214 to calculate the tuple set used for cache reuse.

**Recommendation:** add `evaluation/chunk_experiments.py` for the approved strategy definitions and expected-chunk iterator; patch `scripts.ingest_repo.chunk_lines` only around ingestion, with `finally` restoration. Use that strategy iterator directly in `setup_eval_corpus`, rather than relying on two patched module bindings.

**Confirmed:** `evaluation/runner.py` must thread repository name/strategy through `setup_eval_corpus`, `validate_eval_index`, `retrieval_records`, `run_pipeline_once`, and `run_evaluation` (current hard-coded uses at lines 206, 227, 249, 257, 276, 301, 398, 629, and 722). Add strategy/size/overlap to `build_run_metadata` and the report/run ID; otherwise the two index configurations can look alike in comparison.

**Confirmed:** the inventory guard will fail for a newly created `incidentweave-eval-w100_20`: at `runner.py:629` it exempts only `EVAL_REPOSITORY_NAME`. It must exempt the full allowed eval-name set. Cache reuse is otherwise sound because `cached_embedding` is keyed solely by question text (`runner.py:138-149`), and all 24 cache files exist.

**Confirmed:** `scripts/run_eval.py` currently has only `--passes`; it needs a constrained `--strategy` argument passed to `run_evaluation`. `tests/unit/test_evaluation.py` imports/calls `run_pipeline_once` in three tests (lines 198, 239, 290), asserts the pinned 40/70 baseline (lines 42-63), and asserts the CLI's two-pass parsing (line 768); update those call sites and add baseline/experimental repository, expected-tuple, inventory, metadata, and CLI-strategy coverage. `evaluation/corpus.py` need not change if allowed-name validation remains in the runner.

##### D. Agreement or disagreement with D3 and D4

**Recommendation:** I agree with proposed D3: 100/20 is the right single next arm. The pinned audit now establishes that it directly repairs whole-function context for four target labels; AST-aware chunking would add a second variable before testing that simpler explanation. It cannot make direct-08's 97-line function whole at this size, so do not forecast a universal fix.

**Recommendation:** I do not yet agree to D4 unchanged. Keep its no-regression, false-accept (at most 4), answer-quality, paired-review, and token ceiling gates, but require both Hit@3 and Hit@5 not to decrease for the MRR alternative. Also predeclare a paired threshold: at least two net question-level Hit@5 improvements, or one improvement plus MRR >= +0.05 with no Hit@3 loss. One changed item is 6.25% of 16 and is too fragile for adoption. D3 and D4 remain pending maintainer decision.

##### E. Risks or confounds missed

**Confirmed:** labels use a substring inside a chunk, so larger windows can improve Hit@5 without improving function-level evidence; report hit-by-file/function and inspect changed top-5 contexts.

**Recommendation:** stratify results by direct/paraphrased and test/non-test paths. Existing baseline evidence says test chunks occupy many missed top-5 slots; changed chunk counts can alter their share independent of boundary repair.

**Recommendation:** keep thresholds and query embeddings fixed, report their distributions, and do not interpret a guard change as chunking quality alone. Larger chunks change both embedding geometry and prompt/token size; generation variation remains a separate confound.

##### F. Questions for the maintainer

- **Recommendation:** Approve or reject D3 and the revised D4 criteria before implementation.
- **Recommendation:** Confirm whether the experimental repository may be retained locally after comparison, and whether `audit.py`/`graph.py` should be reviewed as additional relevance labels in a separate maintainer decision.

---

### [003] Claude (2026-10-17): review of Codex's repo-verified entry [002-G]

Codex's pinned-commit audit is the strongest evidence in the log so far, because it is the first entry computed from the actual corpus. Where it contradicts me, Codex is right.

**1. Corrections to my own earlier statements (accepted)**
- **The uploaded files were not the pinned versions.** Confirmed by Codex: pinned `investigate.py` is 162 lines (label on line 126, not 137), pinned `persistence.py` is 85 lines (label on line 69), pinned `audit.py` is 42 lines. My E3 findings for direct-08, paraphrased-08 and `audit.py` used the uploaded copies and are superseded by [002-G] section B.
  - Still holds on the pinned file: for paraphrased-08 the label chunk is `51-85` and `persist_investigation` (11-85) is whole in neither 60/10 chunk. For direct-08 the label chunk `101-160` is intact, but `investigate_repository` (53-149, 97 lines) is whole in neither strategy.
  - **Now Unverified for the pinned file:** my claims that `audit = Audit(` is on line 49 and that chunk 51-85 contains the word "audit" only once. Also unverified: the field list I gave for `audit.py`. Before anyone proposes `audit.py` as an alternative label for paraphrased-08, its pinned content must be checked.
  - This resolves the open question in [001] about whether the uploads match the pinned corpus: they do not.
- **paraphrased-05 was misclassified.** I wrote "not a boundary issue". Codex shows `evaluate_evidence_sufficiency` (11-70) is whole in neither 60/10 chunk. The label substring sits in both chunks, so the label check is unaffected, but the function is split, which may weaken the chunks' embedding relevance (**Hypothesis**). Reclassified in E4.
- **Effect on the expected benefit.** At 100/20 the enclosing function becomes whole for four of the five labels (paraphrased-03, -05, -07, -08; Confirmed by Codex B). That is necessary, not sufficient: the whole-function chunk still has to rank in the top 5. I still expect a modest gain, roughly +1 to +3 questions (**Hypothesis**). direct-08 is not helped, and its failure is a ranking problem (test files fill its top 5).
- **Cost side, now measured (Confirmed by Codex B):** 70 chunks at 60/10 become 52 at 100/20, about 26% fewer chunks to embed. Larger chunks mean fewer but heavier retrievals and larger prompts.

**2. Harness (agree with Codex's refinements)**
- Codex found that `evaluation/runner.py` imports `chunk_lines` directly (line 30) and `setup_eval_corpus` uses that separate binding at line 214. So my context-manager patch of `scripts.ingest_repo.chunk_lines` alone would fix ingestion but not the expected-chunk comparison used for cache reuse. **Agreed:** `setup_eval_corpus` takes its expected chunks from the strategy iterator in `evaluation/chunk_experiments.py` directly, and the patch is applied only around the ingestion call, restored in a `finally`.
- **Agreed:** the inventory guard (`runner.py:629`) must exempt the full allowed eval-name set, `run_eval.py` gets a constrained `--strategy` argument (argparse `choices`), and strategy, size and overlap go into the run metadata and run ID.
- **Recommendation (small addition):** add the new parameters to `setup_eval_corpus`, `validate_eval_index`, `retrieval_records`, `run_pipeline_once` and `run_evaluation` as **keyword arguments with defaults equal to today's behaviour**. Codex counted three tests that call `run_pipeline_once` (lines 198, 239, 290) plus the pinned 40/70 asserts. With defaults those existing call sites and asserts should need no change, which also proves the default path is untouched. Copilot should confirm this.

**3. D4 criteria**
- **Accepted from Codex:** Hit@3 and Hit@5 must not decrease on net. Compare against the fresh baseline run, not against the absolute 13/16. Net question-level improvements are what count.
- **Disagreement (Open: Codex to respond, maintainer to decide).** Codex's second route ("one net Hit@5 improvement plus MRR of at least +0.05, no Hit@3 loss") is satisfied by a single question alone. A miss that becomes a rank-1 hit adds 1/16 = +0.0625 MRR on its own. That is the one-question fragility Codex's own rationale rejects. **Proposed instead:** adopt as a candidate only on a net improvement of at least +2 at Hit@5. A net +1 result is **inconclusive**, which means keep the baseline and record it as a weak signal. MRR is still reported but is not an independent route to adoption.
- **Revised D4 text (proposed, pending Codex and maintainer):** Adopt as a candidate only if all hold:
  1. Net Hit@5 improvement of at least +2 over the fresh baseline, with Hit@3 and Hit@5 both not lower.
  2. No previously hit question lost without a written explanation.
  3. Guard false accepts at 4 or fewer, and no new answered-unanswerable cases.
  4. Hand-reviewed end-to-end correctness not lower.
  5. Median tokens per question within about 1.5 times the baseline.
  6. Gains are visible in hit-by-function and hit-by-file, not only hit-by-label (see section 4).
  Keep the baseline otherwise. A tie, or a net +1, goes to the baseline.

**4. Risks Codex added (accepted)**
- Stratify results by direct versus paraphrased, and by test versus non-test paths, because chunk count changes alter test chunks' share of the top 5 independently of boundary repair.
- Report **hit-by-function** (the label chunk contains the whole enclosing function) beside hit-by-file and hit-by-label. It can be computed offline with the same method as Codex's section B.
- Keep thresholds and query embeddings fixed. Report distance distributions. Do not read a guard change as a chunking effect alone.

**5. Maintainer question (Codex F)**
- **Recommendation:** keep the experimental repository `incidentweave-eval-w100_20` locally until the results are reviewed. Deleting it is a maintainer decision.
- The `audit.py` and `graph.py` label review stays a separate maintainer decision, and it needs pinned-commit content first.

**6. Status and next actions**
- **Agreed by both planners:** D3 (100/20). **Open:** the MRR route inside D4.
- **Copilot is not cleared to implement.** It needs maintainer approval of D3 and D6 first. The harness work does not depend on the D4 wording, but no experiment run may start until D4 is confirmed.
- **Next, in order:** (a) Codex replies on the D4 disagreement; (b) the maintainer decides D3, D4 and D6; (c) Copilot implements the harness per sections 2 above and [002-G] C, then records files, SHA and test output; (d) optionally, someone with the repo runs the read-only ranking export and pastes the output. If it fails on a row key, paste the error here.

&nbsp;

#### [003-R] Copilot response

**Copilot:**

&nbsp;

#### [003-G] ChatGPT / Codex response

**ChatGPT/Codex:**

&nbsp;

---

## Maintenance

- Update "Current status" and "Decisions" whenever a decision or result changes.
- If chunking is adopted into production ingestion, `docs/architecture.md` (sections 3, 8, 11, 13, and the change-history table) must be updated in the same change, per its Maintenance Rule. Re-ingestion replaces all chunk IDs, and audit rows hold chunk IDs without foreign keys, so historical IDs can become stale.

---

### [004] Maintainer (2026-10-17): Approval of D3, D4, D6 and harness implementation

**D3 — Approved:** Run a fixed-window `100/20` chunking experiment against the existing `60/10` baseline.

**D4 — Approved:** Adopt a candidate strategy only when all of the following gates pass:

1. At least two net additional Hit@5 questions compared with a fresh baseline run.
2. Hit@3 and Hit@5 must not decrease.
3. Explain every previously hit question that is lost.
4. Guard false accepts must remain at or below four, with no new answered-unanswerable cases.
5. Human-reviewed end-to-end correctness must not be lower.
6. Median tokens per question should remain within approximately 1.5 times the baseline.
7. Improvements must be visible in hit-by-function and hit-by-file, not only hit-by-label.
8. A net gain of only one Hit@5 question is inconclusive; retain the baseline.
9. MRR is a supporting metric, not an independent adoption route.

This decision resolves the MRR-route disagreement recorded in [003] without deleting or rewriting either planner's historical position.

**D6 — Approved:** The maintainer approves each implementation step, any production-ingestion or golden-set changes, and resolution of planner disagreements.

**Authorization boundary:** The maintainer authorizes implementation of the evaluation harness described in this task. This does **not** authorize running the chunking experiment. Do not run either arm, call Gemini or embedding APIs, or mutate the evaluation database until the maintainer separately approves the experiment after reviewing the harness.

**Current task scope:** Implement only the evaluation-side strategy definitions, runner/CLI threading, metadata, repository allowlist, and focused tests. Keep production ingestion, embeddings, application code, golden-set data, and the pre-existing untracked artifacts unchanged. No commit is authorized by this entry.

---

### [005] ChatGPT (2026-10-17): Review of harness safety fixes

**Review summary:** The initial harness used a temporary assignment to `scripts.ingest_repo.chunk_lines`. The safety revision removes that process-global replacement: expected ranges come from the evaluation strategy helper, and new evaluation chunk rows are inserted by `evaluation/runner.py` for the selected allowlisted repository. This keeps production ingestion code unchanged.

**Data safety:** Existing repository path/range/content tuples are compared with the selected snapshot and strategy. Exact matches are reused; mismatches fail before replacement or deletion. Only missing embeddings on a matching repository are sent to the existing embedding helper. Inventory checking now permits changes only for the selected evaluation repository and reports other repository count changes, creation, or disappearance. These properties are covered by mocked unit tests, not by a live database check.

**Review recommendation:** Keep the stale-repository behavior fail-closed; do not add an automatic reset. Before interpreting results, resolve the outstanding question of whether evaluation-owned insertion is behaviorally equivalent to production ingestion for metadata and embeddings. No side-by-side database verification has established this yet. The chunking experiment remains unauthorized and must not be run as part of harness review.

**Evidence:** Final focused evaluation and ingestion unit command reported `38 passed`; targeted Ruff reported `All checks passed!`; `git diff --check` reported no whitespace issues. No database, provider, or experiment execution was performed for this review.

---

### [006] Copilot (2026-10-17): Harness implementation and safety fixes

**Files changed across the harness and safety-fix stages:**

- `evaluation/chunk_experiments.py` — defines `baseline` (60/10) and `w100_o20` (100/20), maps them to the two approved evaluation repository names, validates strategy/repository pairing, and calculates ingestion-compatible expected ranges.
- `evaluation/runner.py` — threads the strategy and repository through setup, index validation, retrieval, pipeline passes, metadata, and run IDs. Expected chunks use the strategy iterator directly. New repositories receive evaluation-owned chunk rows; existing repositories are reused only when path/range/content tuples match, otherwise setup fails without deleting or replacing rows. Missing embeddings on exact matches can be retried through the existing embedding helper. The inventory guard allows count changes only for the selected evaluation repository.
- `scripts/run_eval.py` — adds constrained `--strategy` choices and keeps `baseline` as the default; preserves the existing `--passes` option.
- `tests/unit/test_evaluation.py` — covers strategy ranges and baseline parity, boundary/overlap/final-line and whitespace cases, repository allowlisting, selected-only inventory changes, creation/disappearance, no-write stale mismatch, exact-data reuse, missing-embedding retry, metadata/run IDs, CLI parsing, and strategy propagation.
- `docs/architecture.md` — updates the evaluation flow, source references, and architecture history to describe evaluation-owned insertion and fail-closed reuse.
- `docs/chunking-experiment.md` — records D3/D4/D6, current implementation status, this review history, and the remaining verification question.

**Verification commands and results:**

- Initial harness pass: `.\.venv\Scripts\python.exe -m pytest -q tests/unit/test_evaluation.py tests/unit/test_ingest_repo.py` — `31 passed`.
- Safety-fix pass: `.\.venv\Scripts\python.exe -m pytest -q tests/unit/test_evaluation.py tests/unit/test_ingest_repo.py` — `38 passed in 45.81s`.
- `.\.venv\Scripts\ruff.exe check evaluation/chunk_experiments.py evaluation/runner.py scripts/run_eval.py tests/unit/test_evaluation.py` — `All checks passed!`.
- `git diff --check` — no output/errors.
- Focused tests also exercised both strategy boundaries, pinned snapshot counts, selected repository routing, no-global-mutation setup, stale-data refusal, and exact-data reuse with missing-embedding retry.

**Not performed:** No chunking experiment, live baseline/experimental evaluation, database access or mutation, Gemini/embedding/API call, full repository test suite, or database integration test. The test suites run were `tests/unit/test_evaluation.py` and `tests/unit/test_ingest_repo.py`. `evaluation/golden_set.json`, `scripts/ingest_repo.py`, `scripts/embed_chunks.py`, and `app/` were not changed. Existing untracked `docs/architecture.md`, `docs/chunking-experiment.md`, and `evaluation/results/run-2.json` were preserved; `run-2.json` was not overwritten. No commit SHA exists because no commit was made.

**Outstanding review question:** Whether evaluation-owned chunk insertion matches production ingestion metadata and embedding behavior has not been established by a side-by-side database verification. No experiment is authorized until the maintainer separately approves it.

---

### [007] Codex (2026-10-17): independent working-tree review

**Review scope and checks actually run:** Read this log through [006], including decisions/current status; inspected `git status --short --branch`, changed-file diffs, `evaluation/chunk_experiments.py`, `evaluation/runner.py`, `scripts/run_eval.py`, `tests/unit/test_evaluation.py`, `scripts/ingest_repo.py`, `scripts/embed_chunks.py`, `app/db/models/chunk.py`, and the architecture update. Ran `git diff --check` (no output) and an AST parse of the four changed Python files (`AST parse: 4 changed Python files OK`). I did not run pytest, the evaluation, database checks, or provider calls.

**Confirmed -- scope and baseline:** The only tracked implementation changes are evaluation runner/CLI/tests, plus the untracked evaluation-only strategy helper; production ingestion, embedding, application code, and golden set are unchanged. `baseline` retains 60/10 and `incidentweave-eval`; `w100_o20` is constrained to 100/20 and `incidentweave-eval-w100_20` (`evaluation/chunk_experiments.py:17-45`). The range iterator has the same half-open/overlap/final-window algorithm as `scripts/ingest_repo.py::chunk_lines`; its baseline parity and the pinned 40-file/70-chunk and experimental 52-chunk counts are covered by unit tests, although I did not rerun them.

**Confirmed -- database isolation and reuse:** `resolve_evaluation_repository` rejects non-allowlisted names and mismatched strategy/repository pairs (`chunk_experiments.py:48-70`). `setup_eval_corpus` creates rows only for that resolved repository, compares existing rows by file path, line range, and content, and raises before deletion or replacement on a mismatch (`runner.py:274-371`). The inventory guard permits a count change only for the selected repository and detects changed, created, or disappeared others (`runner.py:241-271`). This is a sound fail-closed design for the evaluated repository; it does not call production `ingest_repository`, which is important because that function deletes the selected repository's chunks.

**Confirmed -- insertion metadata:** For new rows, evaluation insertion sets the same populated chunk fields as production ingestion: repository id, content, relative POSIX path, `file_type="python"`, `document_type="code"`, one-based/exclusive-end-derived line bounds, and `function_name`, `class_name`, and `symbol` to `None` (`runner.py:315-331`; `scripts/ingest_repo.py:101-115`). Remaining nullable model fields use the same ORM defaults (`app/db/models/chunk.py:17-47`). Embedding uses the existing repository helper (`runner.py:361-369`; `scripts/embed_chunks.py:77-113`).

**Potential risk -- incomplete embedding state:** The runner commits new evaluation rows before invoking the embedding helper. If the provider fails, setup raises and retrieval/pipeline execution stops, but the selected evaluation repository remains with partial/null embeddings. This matches the production two-step ingestion/embedding failure mode and is not a confirmed isolation defect; a later run retries missing embeddings. The runner trusts the helper's `failed` count rather than re-querying for null embeddings after it returns. A post-embedding completeness assertion would provide stronger defense against unexpected helper/database behavior, but live verification is needed before treating this as a code defect.

**Unverified -- test and runtime evidence:** The added setup tests use `FakeEvaluationSession` and mock `embed_repository_chunks`; they demonstrate control flow but do not prove SQLAlchemy persistence, transaction behavior, row metadata, or real embedding completion. The `38 passed`/Ruff results in [005]-[006] are recorded results, not independently rerun in this review. A separately authorized disposable-database check should compare rows created by production ingestion and evaluation insertion for the same pinned snapshot, including all populated metadata and null-embedding recovery/failure behavior. It must not be conflated with authorization to run the experiment or call Gemini.

**Confirmed -- evaluation validity and documentation:** Strategy, size, overlap, repository, and strategy-suffixed run ID enter report metadata/config hash (`runner.py:67-143`, `201-212`, `715-875`); the CLI admits only known strategies. The status table agrees with [004]-[006]: D3/D4/D6 are approved, the harness is uncommitted, evaluation-owned insertion equivalence is not established, and the experiment is not authorized or run. I found no stale top-level status statement requiring correction. The architecture update accurately labels the harness as uncommitted and does not claim live verification.

**Recommendation:** The harness is ready for the next maintainer/code-review step, not for experiment execution. Before a separate run authorization: (1) preserve the fail-closed behavior; (2) obtain an authorized disposable-DB equivalence check or explicitly accept that residual risk; (3) rerun and retain focused test/lint evidence from the exact reviewed tree; and (4) establish the approved commit/clean-tree provenance required for a paired baseline/experimental comparison. No adoption gate, historical entry, or experiment authorization was changed by this review.

---

### [008] Claude (2026-10-17): planner review of [005], [006], [007]

**Basis:** I read the log through [007]. I have not seen the diff or the code, so every point about the code below rests on Copilot's and Codex's reports. I ran nothing.

**Verdict:** the harness design is acceptable and Codex's [007] findings are sound. It is **not yet ready for run authorization**. Four items should be closed first; none needs a live database.

**1. Deviation from the agreed plan (Open: maintainer to decide).** [003] and [002-G] agreed to reuse production `ingest_repository` with a temporary patch of `chunk_lines`. [005]/[006] replaced that with evaluation-owned row insertion in `runner.py`, to avoid mutating a process-global.
- *Accepted as reasonable:* it avoids the global patch, and Codex [007] Confirmed the populated metadata fields match production and that the same embedding helper is used.
- *Cost:* it duplicates a small amount of ingestion logic, which is the equivalence risk [005] and [007] raise. Because the fields were compared in source, I rate the residual risk low.
- *Behaviour change on the baseline path:* a stale or mismatched `incidentweave-eval` now stops the run (fail closed) instead of being re-ingested as before. I accept fail closed, but Copilot should state that this changes the default path.

**2. Embedding completeness checks (Unverified; please confirm).** The pre-change runner checked `failed or skipped or embedded != chunks` after embedding. [007] says the new code trusts only the helper's `failed` count. If the `skipped` and `embedded == expected chunks` checks were dropped, restore them and add a post-embedding query that no chunk in the selected repository has a null embedding. This is a small, mockable change.

**3. Gate 7 cannot be evaluated with the current tooling.** [006] lists no hit-by-file, hit-by-function, direct/paraphrased or test/non-test stratification, or per-question paired reporting.
- *Recommendation:* a small read-only comparison script outside `evaluation/runner.py` that reads two run folders. Pass files already hold per-question `labeled_rank` and the retrieved chunks, so hit@k, hit-by-file and a paired table are computable; hit-by-function needs the pinned source and `ast`.
- *Ambiguity in gate 7 (needs a maintainer ruling):* judging from their label strings, at least 7 of the 8 direct labels are module-level constants (for example `CHUNK_SIZE = 60`, `MIN_ACCEPTABLE_RRF_SCORE = 0.016`), so they have no enclosing function (**Hypothesis**, from `golden_set.json`). **Recommendation:** apply hit-by-function only to labels inside a function or class, and report hit-by-file for the rest.

**4. Provenance.** The tree is uncommitted, and run metadata records `code_dirty`. A paired comparison needs both arms run from the same clean commit ([007] item 4). That needs a maintainer-authorized commit.
- *Scope note:* [004] authorized evaluation-side code and tests. [006] also changed `docs/architecture.md`, which is not in the [004] list, though the architecture doc's own Maintenance Rule requires such updates. It is untracked, so it cannot be diffed. The maintainer should confirm that this was intended.

**On [007]'s disposable-database check (Recommendation, not agreement).** I would not block the run on it. The baseline repository reuse already proves path, range and content equality against a production-ingested repository. For the experimental repository, a read-only SQL inspection right after setup (row count, null-embedding count, `file_type`, `document_type`, and null `function_name` counts) gives most of the same assurance. [005] says to resolve this "before interpreting results", which fits that approach. [007] says "before a separate run authorization". **Open: maintainer to decide.**

**Proposed sequence before the maintainer authorizes the run:**
1. Copilot confirms points 1 and 2, and whether the existing three `run_pipeline_once` tests and the pinned 40/70 asserts were left unchanged.
2. Copilot or Codex adds the read-only comparison script (point 3), pending the gate 7 ruling.
3. The maintainer authorizes a commit, so the run uses a clean tree.
4. Re-run the focused tests and Ruff on the committed tree and paste the output.
5. The maintainer separately authorizes the run: baseline arm first, then `w100_o20`, same day and same commit.

**Status:** nothing in [004] was changed. The experiment remains **not authorized**.

---

### [009] Copilot (2026-10-17): embedding completeness and offline comparator

**Task 1 — runner and preservation checks**

- **a) Embedding-result checks kept:** yes. After `embed_repository_chunks`, `runner.py` calculates the expected embedded/skipped counts and raises if `failed` is nonzero, `skipped` differs, or `embedded` differs from expectation (`evaluation/runner.py:371-391`).
- **b) Null embeddings:** after the helper returns, a read-only count query scoped to the selected repository raises if any chunk still has a null embedding (`evaluation/runner.py:376-385`). `test_setup_eval_corpus_checks_for_null_embeddings_after_embedding` mocks one remaining null row and asserts setup raises (`tests/unit/test_evaluation.py:339-365`); no live database was used.
- **c) Existing pipeline tests and baseline counts:** the three pre-existing `run_pipeline_once` tests remain unchanged: exact abstention (`tests/unit/test_evaluation.py:743`), a real answer mentioning the marker (`tests/unit/test_evaluation.py:782`), and an unanswerable answer mentioning the marker (`tests/unit/test_evaluation.py:825`). The existing pinned baseline assertions remain 40 files and 70 chunks (`tests/unit/test_evaluation.py:629,638`). The pinned-snapshot test now exports under `tmp_path`, and adds the experimental 52-chunk count (`tests/unit/test_evaluation.py:614-647`); no baseline assertion was changed.
- **d) Stale/mismatched repository behavior:** a stale or mismatched `incidentweave-eval` now stops with an error rather than being deleted or re-ingested (`evaluation/runner.py:354-359`). The mocked refusal test verifies no rows are added and no commit occurs (`tests/unit/test_evaluation.py:367-397`).

**Task 2 — offline comparison tool:** Added `evaluation/compare_chunking_runs.py` and synthetic tests in `tests/unit/test_compare_chunking_runs.py`. The tool reads two saved run folders and pinned source via `git show`; it does not use a database or provider. Its report includes pass-1 paired ranks/Hit@1/3/5 and hit changes, per-pass direct/paraphrased and test/non-test summaries, hit-by-file and AST-derived hit-by-function (module-level labels are `n/a` for function hits), top-5 context characters and per-question/median token counts, guard false accepts, per-pass `outcome_v2` counts and changes, and all nine gate statuses. Gate 5 is `MANUAL`; a net +1 Hit@5 is explicitly inconclusive and says to retain the baseline. Gate 7 requires a hit-by-function improvement only when function/class labels are applicable; for module-only labels, its measurable criterion is hit-by-file. Synthetic tests cover the +1 case, module-level labels and gate behavior, stratified metrics, and printed/JSON CLI output.

**Files changed or added for this harness work:**

- `evaluation/runner.py` — repaired the interrupted setup/retrieval code and added the post-embedding null check while retaining embedding-count checks.
- `evaluation/chunk_experiments.py` — evaluation strategy and repository mapping.
- `scripts/run_eval.py` — strategy CLI threading.
- `tests/unit/test_evaluation.py` — mocked completeness check and strategy coverage; preserved prior checks as described above.
- `evaluation/compare_chunking_runs.py` — read-only comparison CLI and report.
- `tests/unit/test_compare_chunking_runs.py` — synthetic comparison tests.
- `docs/architecture.md` — accepted architecture update describing evaluation-owned chunk setup.
- `docs/chunking-experiment.md` — this evidence entry.

**Focused verification (exact output):**

```text
.\.venv\Scripts\python.exe -m pytest -q tests\unit\test_evaluation.py tests\unit\test_ingest_repo.py tests\unit\test_compare_chunking_runs.py
..........................................                               [100%]
42 passed in 21.86s
```

```text
.\.venv\Scripts\ruff.exe check evaluation\runner.py evaluation\compare_chunking_runs.py evaluation\chunk_experiments.py scripts\run_eval.py tests\unit\test_evaluation.py tests\unit\test_compare_chunking_runs.py
All checks passed!
```

`git diff --check` produced no output. The focused test run initially caught a synthetic line-span mismatch after adding a duplicate module-level label occurrence; the fixture's enclosing-function line range was corrected, and the final run above passed.

**Not performed / deviations:** No experiment arm, database access or mutation, Gemini/embedding/API call, real-run comparison, full test suite, or commit was performed. The comparison behavior was validated only with synthetic run folders. The pre-existing untracked `evaluation/results/run-2.json` was left untouched.

---

### [010] Claude (2026-10-18): planner review of [009]

Scope: reviewed the [009] text, the pasted `git status`/diff, the supplied `runner.py`, and Copilot's activity transcript. I did **not** see `compare_chunking_runs.py` or `chunk_experiments.py` source directly; statements about them rest on Copilot's description and its tests.

**Verdict on the four [008] items**
1. **Embedding checks retained: Confirmed** (runner.py setup path: failed/skipped/embedded counts, plus a null-embedding query). Accept.
2. **Pre-existing tests/pinned 40/70 asserts unchanged: Confirmed by Copilot's report** (transcript shows it diffed against `HEAD`). Accept.
3. **Stale baseline fails closed: Confirmed** in code (exact tuple match or `RuntimeError`, no delete/re-ingest). Accept; note it is a deliberate behaviour change from the old re-ingest.
4. **Gate-7 tooling: Done** per [009]. Accept, with the caveat below.

**Minor findings (none blocking)**
- *Recommendation:* in `setup_eval_corpus` the null-embedding check runs before the failed/skipped/embedded count check, so a partial embedding failure would surface as the null error and hide the counts. Either order raises, so it is safe; swapping would give a clearer message.
- *Confirmed:* when an existing repo already has all embeddings, setup returns before any embedding check. That is correct for reuse, since reuse already requires an exact chunk match and zero nulls.
- *Confirmed:* `run_evaluation` still deletes and recreates `evaluation/_snapshot` inside the repo (pre-existing). It is untracked/ignored in practice, but confirm it is gitignored so the tree stays clean at run time.
- *Hypothesis:* gate 7 for module-only labels falls back to hit-by-file, which is looser than hit-by-label. If the maintainer's earlier ruling stands (at least 7 of 8 direct labels are module-level), gate 7 will mostly be satisfied by file hits. That is acceptable but means gate 7 adds little for direct questions; read the paraphrased questions' hit-by-function carefully.
- *Unverified:* evaluation-owned insertion has only mocked tests. After setup, and before the first arm, run read-only SQL: chunk count per repo (expect 70 / 52), null embeddings (expect 0), and a sample of `line_start`/`line_end` against `expected_chunk_ranges`.
- *Out of scope, flagged:* `docs/architecture.md` is untracked and was edited outside the [004] list. Recommend the maintainer accept it explicitly in the log.

**Position:** I accept [009]. Harness is ready for commit review.

**Remaining gates (maintainer decides)**
1. Record rulings: accept gate-7 module-level treatment; accept `architecture.md` change.
2. Authorize a commit of the harness files only (not `run-2.json`, not any results), and re-run focused tests and Ruff on the committed tree (Codex [007] item 3).
3. Codex independently reviews `compare_chunking_runs.py` and `chunk_experiments.py` (I have not seen them).
4. Separately authorize the run: baseline first, then `w100_o20`, same day, same clean commit, with the post-setup SQL check between.
5. Then compare with `compare_chunking_runs.py`, apply D4; gate 5 (end-to-end correctness) is a manual human review.

**Status:** experiment still **not authorized**. Update the status table to point to [009] and [010].

---

### [011] Copilot (2026-10-18): authorized run record

Commit: `2274338`.

Baseline run: `20261018T123627Z-2274338-baseline` (70 chunks, 42 generation HTTP calls, 2 HTTP 429 responses, 0 generation errors).

100/20 run: `20261018T124223Z-2274338-w100_o20` (52 chunks, 42 generation HTTP calls, 1 HTTP 429 response, 0 generation errors).

Commands:

```text
git branch --show-current
git status --short --untracked-files=all
git status --porcelain=v1
docker compose ps db
git add evaluation/runner.py evaluation/chunk_experiments.py evaluation/compare_chunking_runs.py scripts/run_eval.py tests/unit/test_evaluation.py tests/unit/test_compare_chunking_runs.py docs/architecture.md docs/chunking-experiment.md
git status --short
git diff --cached --name-only
git diff --cached --check
git diff --cached --stat
git diff --cached
git commit -m "Add chunking experiment harness (baseline vs 100/20) and offline run comparator" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
.\.venv\Scripts\python.exe -m pytest -q tests\unit\test_evaluation.py tests\unit\test_ingest_repo.py tests\unit\test_compare_chunking_runs.py
.\.venv\Scripts\ruff.exe check evaluation scripts tests\unit\test_evaluation.py tests\unit\test_compare_chunking_runs.py
git status --short
.\.venv\Scripts\python.exe scripts\run_eval.py --help
.\.venv\Scripts\python.exe scripts\run_eval.py --strategy baseline --passes 2
.\.venv\Scripts\python.exe scripts\run_eval.py --strategy w100_o20 --passes 2
.\.venv\Scripts\python.exe evaluation\compare_chunking_runs.py --help
.\.venv\Scripts\python.exe evaluation\compare_chunking_runs.py evaluation\results\runs\20261018T123627Z-2274338-baseline evaluation\results\runs\20261018T124223Z-2274338-w100_o20
```

No command failed; no other error text was reported. Full comparator output follows verbatim:

```text
Baseline: 20261018T123627Z-2274338-baseline
Experiment: 20261018T124223Z-2274338-w100_o20
Pinned SHA: 62d0e58593bb22d187ec7930274b0457afd3be74

Pass-1 answerable paired retrieval (rank and hit indicators):
id | baseline rank | experiment rank | baseline @1/@3/@5 | experiment @1/@3/@5 | file baseline/experiment | function baseline/experiment | gained | lost
direct-01 | 1 | 1 | 1/1/1 | 1/1/1 | yes/yes | n/a/n/a | - | -
direct-02 | 1 | 1 | 1/1/1 | 1/1/1 | yes/yes | n/a/n/a | - | -
direct-03 | 1 | 1 | 1/1/1 | 1/1/1 | yes/yes | n/a/n/a | - | -
direct-04 | 1 | 1 | 1/1/1 | 1/1/1 | yes/yes | n/a/n/a | - | -
direct-05 | 3 | 2 | 0/1/1 | 0/1/1 | yes/yes | n/a/n/a | - | -
direct-06 | 1 | 1 | 1/1/1 | 1/1/1 | yes/yes | n/a/n/a | - | -
direct-07 | 1 | 1 | 1/1/1 | 1/1/1 | yes/yes | n/a/n/a | - | -
direct-08 | None | 4 | 0/0/0 | 0/0/1 | no/yes | no/no | @5 | -
paraphrased-01 | 1 | 1 | 1/1/1 | 1/1/1 | yes/yes | n/a/n/a | - | -
paraphrased-02 | 2 | 1 | 0/1/1 | 1/1/1 | yes/yes | n/a/n/a | @1 | -
paraphrased-03 | None | 2 | 0/0/0 | 0/1/1 | yes/yes | no/yes | @3,@5 | -
paraphrased-04 | 3 | 2 | 0/1/1 | 0/1/1 | yes/yes | no/yes | - | -
paraphrased-05 | None | 4 | 0/0/0 | 0/0/1 | no/yes | no/yes | @5 | -
paraphrased-06 | 1 | 1 | 1/1/1 | 1/1/1 | yes/yes | yes/yes | - | -
paraphrased-07 | None | None | 0/0/0 | 0/0/0 | yes/yes | no/no | - | -
paraphrased-08 | None | 5 | 0/0/0 | 0/0/1 | no/yes | no/yes | @5 | -

pass-1 metrics:
  baseline: overall={'questions': 16, 'hit_at_1': 8, 'hit_at_3': 11, 'hit_at_5': 11, 'mrr': 0.5729166666666666}; by_category={'direct': {'questions': 8, 'hit_at_1': 6, 'hit_at_3': 7, 'hit_at_5': 7, 'mrr': 0.7916666666666666}, 'paraphrased': {'questions': 8, 'hit_at_1': 2, 'hit_at_3': 4, 'hit_at_5': 4, 'mrr': 0.3541666666666667}}; by_label_file_type={'test_file': {'questions': 0, 'hit_at_1': 0, 'hit_at_3': 0, 'hit_at_5': 0, 'mrr': 0.0}, 'non_test_file': {'questions': 16, 'hit_at_1': 8, 'hit_at_3': 11, 'hit_at_5': 11, 'mrr': 0.5729166666666666}}; hit_by_file={'hit_at_5': 13, 'questions': 16}; hit_by_function={'hit_at_5': 1, 'applicable_questions': 7, 'not_applicable_module_level': 9}; top5_median_chars=7729.5; top5_chars_per_question=[{'id': 'direct-01', 'characters': 7904}, {'id': 'direct-02', 'characters': 7488}, {'id': 'direct-03', 'characters': 7813}, {'id': 'direct-04', 'characters': 7332}, {'id': 'direct-05', 'characters': 7239}, {'id': 'direct-06', 'characters': 7787}, {'id': 'direct-07', 'characters': 7907}, {'id': 'direct-08', 'characters': 8132}, {'id': 'paraphrased-01', 'characters': 6328}, {'id': 'paraphrased-02', 'characters': 7672}, {'id': 'paraphrased-03', 'characters': 8874}, {'id': 'paraphrased-04', 'characters': 7864}, {'id': 'paraphrased-05', 'characters': 10237}, {'id': 'paraphrased-06', 'characters': 8743}, {'id': 'paraphrased-07', 'characters': 9743}, {'id': 'paraphrased-08', 'characters': 9549}, {'id': 'unanswerable_far-01', 'characters': 0}, {'id': 'unanswerable_far-02', 'characters': 0}, {'id': 'unanswerable_far-03', 'characters': 0}, {'id': 'unanswerable_far-04', 'characters': 0}, {'id': 'unanswerable_near-01', 'characters': 4641}, {'id': 'unanswerable_near-02', 'characters': 10437}, {'id': 'unanswerable_near-03', 'characters': 3637}, {'id': 'unanswerable_near-04', 'characters': 6839}]; median_tokens=2835.5; tokens_per_question=[{'id': 'direct-01', 'total_tokens': 2802}, {'id': 'direct-02', 'total_tokens': 2746}, {'id': 'direct-03', 'total_tokens': 2761}, {'id': 'direct-04', 'total_tokens': 2785}, {'id': 'direct-05', 'total_tokens': 2676}, {'id': 'direct-06', 'total_tokens': 2869}, {'id': 'direct-07', 'total_tokens': 2750}, {'id': 'direct-08', 'total_tokens': 2996}, {'id': 'paraphrased-01', 'total_tokens': 2374}, {'id': 'paraphrased-02', 'total_tokens': 2905}, {'id': 'paraphrased-03', 'total_tokens': 3095}, {'id': 'paraphrased-04', 'total_tokens': 3199}, {'id': 'paraphrased-05', 'total_tokens': 3509}, {'id': 'paraphrased-06', 'total_tokens': 3320}, {'id': 'paraphrased-07', 'total_tokens': 3392}, {'id': 'paraphrased-08', 'total_tokens': 3167}, {'id': 'unanswerable_far-01', 'total_tokens': None}, {'id': 'unanswerable_far-02', 'total_tokens': None}, {'id': 'unanswerable_far-03', 'total_tokens': None}, {'id': 'unanswerable_far-04', 'total_tokens': None}, {'id': 'unanswerable_near-01', 'total_tokens': 1971}, {'id': 'unanswerable_near-02', 'total_tokens': 3435}, {'id': 'unanswerable_near-03', 'total_tokens': 1602}, {'id': 'unanswerable_near-04', 'total_tokens': 2335}]; guard_false_accepts=4; outcome_v2_counts={'correct_labeled_context': 10, 'correct_unlabeled_context': 3, 'guard_true_refusal': 4, 'incomplete_or_wrong': 1, 'model_abstained': 4, 'retrieval_miss_abstained': 2}
  experiment: overall={'questions': 16, 'hit_at_1': 9, 'hit_at_3': 12, 'hit_at_5': 15, 'mrr': 0.7}; by_category={'direct': {'questions': 8, 'hit_at_1': 6, 'hit_at_3': 7, 'hit_at_5': 8, 'mrr': 0.84375}, 'paraphrased': {'questions': 8, 'hit_at_1': 3, 'hit_at_3': 5, 'hit_at_5': 7, 'mrr': 0.55625}}; by_label_file_type={'test_file': {'questions': 0, 'hit_at_1': 0, 'hit_at_3': 0, 'hit_at_5': 0, 'mrr': 0.0}, 'non_test_file': {'questions': 16, 'hit_at_1': 9, 'hit_at_3': 12, 'hit_at_5': 15, 'mrr': 0.7}}; hit_by_file={'hit_at_5': 16, 'questions': 16}; hit_by_function={'hit_at_5': 5, 'applicable_questions': 7, 'not_applicable_module_level': 9}; top5_median_chars=11072.0; top5_chars_per_question=[{'id': 'direct-01', 'characters': 12227}, {'id': 'direct-02', 'characters': 11036}, {'id': 'direct-03', 'characters': 11285}, {'id': 'direct-04', 'characters': 11108}, {'id': 'direct-05', 'characters': 10431}, {'id': 'direct-06', 'characters': 14216}, {'id': 'direct-07', 'characters': 8135}, {'id': 'direct-08', 'characters': 14537}, {'id': 'paraphrased-01', 'characters': 9145}, {'id': 'paraphrased-02', 'characters': 11274}, {'id': 'paraphrased-03', 'characters': 7664}, {'id': 'paraphrased-04', 'characters': 12593}, {'id': 'paraphrased-05', 'characters': 15127}, {'id': 'paraphrased-06', 'characters': 11113}, {'id': 'paraphrased-07', 'characters': 13453}, {'id': 'paraphrased-08', 'characters': 14964}, {'id': 'unanswerable_far-01', 'characters': 0}, {'id': 'unanswerable_far-02', 'characters': 0}, {'id': 'unanswerable_far-03', 'characters': 0}, {'id': 'unanswerable_far-04', 'characters': 0}, {'id': 'unanswerable_near-01', 'characters': 6951}, {'id': 'unanswerable_near-02', 'characters': 16900}, {'id': 'unanswerable_near-03', 'characters': 7267}, {'id': 'unanswerable_near-04', 'characters': 9795}]; median_tokens=3971.5; tokens_per_question=[{'id': 'direct-01', 'total_tokens': 4186}, {'id': 'direct-02', 'total_tokens': 3724}, {'id': 'direct-03', 'total_tokens': 3703}, {'id': 'direct-04', 'total_tokens': 4058}, {'id': 'direct-05', 'total_tokens': 3573}, {'id': 'direct-06', 'total_tokens': 4368}, {'id': 'direct-07', 'total_tokens': 2727}, {'id': 'direct-08', 'total_tokens': 4722}, {'id': 'paraphrased-01', 'total_tokens': 3210}, {'id': 'paraphrased-02', 'total_tokens': 4190}, {'id': 'paraphrased-03', 'total_tokens': 2869}, {'id': 'paraphrased-04', 'total_tokens': 4201}, {'id': 'paraphrased-05', 'total_tokens': 4927}, {'id': 'paraphrased-06', 'total_tokens': 3885}, {'id': 'paraphrased-07', 'total_tokens': 4512}, {'id': 'paraphrased-08', 'total_tokens': 4852}, {'id': 'unanswerable_far-01', 'total_tokens': None}, {'id': 'unanswerable_far-02', 'total_tokens': None}, {'id': 'unanswerable_far-03', 'total_tokens': None}, {'id': 'unanswerable_far-04', 'total_tokens': None}, {'id': 'unanswerable_near-01', 'total_tokens': 2498}, {'id': 'unanswerable_near-02', 'total_tokens': 5039}, {'id': 'unanswerable_near-03', 'total_tokens': 2538}, {'id': 'unanswerable_near-04', 'total_tokens': 3213}]; guard_false_accepts=4; outcome_v2_counts={'correct_labeled_context': 14, 'correct_unlabeled_context': 1, 'guard_true_refusal': 4, 'incomplete_or_wrong': 1, 'model_abstained': 4}
pass-2 metrics:
  baseline: overall={'questions': 16, 'hit_at_1': 8, 'hit_at_3': 11, 'hit_at_5': 11, 'mrr': 0.5729166666666666}; by_category={'direct': {'questions': 8, 'hit_at_1': 6, 'hit_at_3': 7, 'hit_at_5': 7, 'mrr': 0.7916666666666666}, 'paraphrased': {'questions': 8, 'hit_at_1': 2, 'hit_at_3': 4, 'hit_at_5': 4, 'mrr': 0.3541666666666667}}; by_label_file_type={'test_file': {'questions': 0, 'hit_at_1': 0, 'hit_at_3': 0, 'hit_at_5': 0, 'mrr': 0.0}, 'non_test_file': {'questions': 16, 'hit_at_1': 8, 'hit_at_3': 11, 'hit_at_5': 11, 'mrr': 0.5729166666666666}}; hit_by_file={'hit_at_5': 13, 'questions': 16}; hit_by_function={'hit_at_5': 1, 'applicable_questions': 7, 'not_applicable_module_level': 9}; top5_median_chars=7729.5; top5_chars_per_question=[{'id': 'direct-01', 'characters': 7904}, {'id': 'direct-02', 'characters': 7488}, {'id': 'direct-03', 'characters': 7813}, {'id': 'direct-04', 'characters': 7332}, {'id': 'direct-05', 'characters': 7239}, {'id': 'direct-06', 'characters': 7787}, {'id': 'direct-07', 'characters': 7907}, {'id': 'direct-08', 'characters': 8132}, {'id': 'paraphrased-01', 'characters': 6328}, {'id': 'paraphrased-02', 'characters': 7672}, {'id': 'paraphrased-03', 'characters': 8874}, {'id': 'paraphrased-04', 'characters': 7864}, {'id': 'paraphrased-05', 'characters': 10237}, {'id': 'paraphrased-06', 'characters': 8743}, {'id': 'paraphrased-07', 'characters': 9743}, {'id': 'paraphrased-08', 'characters': 9549}, {'id': 'unanswerable_far-01', 'characters': 0}, {'id': 'unanswerable_far-02', 'characters': 0}, {'id': 'unanswerable_far-03', 'characters': 0}, {'id': 'unanswerable_far-04', 'characters': 0}, {'id': 'unanswerable_near-01', 'characters': 4641}, {'id': 'unanswerable_near-02', 'characters': 10437}, {'id': 'unanswerable_near-03', 'characters': 3637}, {'id': 'unanswerable_near-04', 'characters': 6839}]; median_tokens=2867.5; tokens_per_question=[{'id': 'direct-01', 'total_tokens': 2800}, {'id': 'direct-02', 'total_tokens': 2708}, {'id': 'direct-03', 'total_tokens': 2840}, {'id': 'direct-04', 'total_tokens': 2738}, {'id': 'direct-05', 'total_tokens': 2665}, {'id': 'direct-06', 'total_tokens': 2909}, {'id': 'direct-07', 'total_tokens': 2750}, {'id': 'direct-08', 'total_tokens': 2996}, {'id': 'paraphrased-01', 'total_tokens': 2384}, {'id': 'paraphrased-02', 'total_tokens': 2895}, {'id': 'paraphrased-03', 'total_tokens': 3243}, {'id': 'paraphrased-04', 'total_tokens': 3160}, {'id': 'paraphrased-05', 'total_tokens': 3565}, {'id': 'paraphrased-06', 'total_tokens': 3311}, {'id': 'paraphrased-07', 'total_tokens': 3366}, {'id': 'paraphrased-08', 'total_tokens': 3231}, {'id': 'unanswerable_far-01', 'total_tokens': None}, {'id': 'unanswerable_far-02', 'total_tokens': None}, {'id': 'unanswerable_far-03', 'total_tokens': None}, {'id': 'unanswerable_far-04', 'total_tokens': None}, {'id': 'unanswerable_near-01', 'total_tokens': 1900}, {'id': 'unanswerable_near-02', 'total_tokens': 3435}, {'id': 'unanswerable_near-03', 'total_tokens': 1602}, {'id': 'unanswerable_near-04', 'total_tokens': 2335}]; guard_false_accepts=4; outcome_v2_counts={'correct_labeled_context': 10, 'correct_unlabeled_context': 3, 'guard_true_refusal': 4, 'incomplete_or_wrong': 2, 'model_abstained': 4, 'retrieval_miss_abstained': 1}
  experiment: overall={'questions': 16, 'hit_at_1': 9, 'hit_at_3': 12, 'hit_at_5': 15, 'mrr': 0.7}; by_category={'direct': {'questions': 8, 'hit_at_1': 6, 'hit_at_3': 7, 'hit_at_5': 8, 'mrr': 0.84375}, 'paraphrased': {'questions': 8, 'hit_at_1': 3, 'hit_at_3': 5, 'hit_at_5': 7, 'mrr': 0.55625}}; by_label_file_type={'test_file': {'questions': 0, 'hit_at_1': 0, 'hit_at_3': 0, 'hit_at_5': 0, 'mrr': 0.0}, 'non_test_file': {'questions': 16, 'hit_at_1': 9, 'hit_at_3': 12, 'hit_at_5': 15, 'mrr': 0.7}}; hit_by_file={'hit_at_5': 16, 'questions': 16}; hit_by_function={'hit_at_5': 5, 'applicable_questions': 7, 'not_applicable_module_level': 9}; top5_median_chars=11072.0; top5_chars_per_question=[{'id': 'direct-01', 'characters': 12227}, {'id': 'direct-02', 'characters': 11036}, {'id': 'direct-03', 'characters': 11285}, {'id': 'direct-04', 'characters': 11108}, {'id': 'direct-05', 'characters': 10431}, {'id': 'direct-06', 'characters': 14216}, {'id': 'direct-07', 'characters': 8135}, {'id': 'direct-08', 'characters': 14537}, {'id': 'paraphrased-01', 'characters': 9145}, {'id': 'paraphrased-02', 'characters': 11274}, {'id': 'paraphrased-03', 'characters': 7664}, {'id': 'paraphrased-04', 'characters': 12593}, {'id': 'paraphrased-05', 'characters': 15127}, {'id': 'paraphrased-06', 'characters': 11113}, {'id': 'paraphrased-07', 'characters': 13453}, {'id': 'paraphrased-08', 'characters': 14964}, {'id': 'unanswerable_far-01', 'characters': 0}, {'id': 'unanswerable_far-02', 'characters': 0}, {'id': 'unanswerable_far-03', 'characters': 0}, {'id': 'unanswerable_far-04', 'characters': 0}, {'id': 'unanswerable_near-01', 'characters': 6951}, {'id': 'unanswerable_near-02', 'characters': 16900}, {'id': 'unanswerable_near-03', 'characters': 7267}, {'id': 'unanswerable_near-04', 'characters': 9795}]; median_tokens=4001.0; tokens_per_question=[{'id': 'direct-01', 'total_tokens': 4140}, {'id': 'direct-02', 'total_tokens': 3742}, {'id': 'direct-03', 'total_tokens': 3714}, {'id': 'direct-04', 'total_tokens': 4162}, {'id': 'direct-05', 'total_tokens': 3594}, {'id': 'direct-06', 'total_tokens': 4361}, {'id': 'direct-07', 'total_tokens': 2716}, {'id': 'direct-08', 'total_tokens': 4688}, {'id': 'paraphrased-01', 'total_tokens': 3203}, {'id': 'paraphrased-02', 'total_tokens': 4256}, {'id': 'paraphrased-03', 'total_tokens': 2870}, {'id': 'paraphrased-04', 'total_tokens': 4207}, {'id': 'paraphrased-05', 'total_tokens': 4928}, {'id': 'paraphrased-06', 'total_tokens': 3862}, {'id': 'paraphrased-07', 'total_tokens': 4567}, {'id': 'paraphrased-08', 'total_tokens': 4808}, {'id': 'unanswerable_far-01', 'total_tokens': None}, {'id': 'unanswerable_far-02', 'total_tokens': None}, {'id': 'unanswerable_far-03', 'total_tokens': None}, {'id': 'unanswerable_far-04', 'total_tokens': None}, {'id': 'unanswerable_near-01', 'total_tokens': 2498}, {'id': 'unanswerable_near-02', 'total_tokens': 5039}, {'id': 'unanswerable_near-03', 'total_tokens': 2518}, {'id': 'unanswerable_near-04', 'total_tokens': 3213}]; guard_false_accepts=4; outcome_v2_counts={'correct_labeled_context': 15, 'correct_unlabeled_context': 1, 'guard_true_refusal': 4, 'model_abstained': 4}

Questions with changed outcome_v2:
  pass-1 direct-04: incomplete_or_wrong -> correct_labeled_context
  pass-1 direct-05: correct_labeled_context -> incomplete_or_wrong
  pass-1 direct-08: retrieval_miss_abstained -> correct_labeled_context
  pass-1 paraphrased-03: correct_unlabeled_context -> correct_labeled_context
  pass-1 paraphrased-05: correct_unlabeled_context -> correct_labeled_context
  pass-1 paraphrased-08: retrieval_miss_abstained -> correct_labeled_context
  pass-2 direct-04: incomplete_or_wrong -> correct_labeled_context
  pass-2 direct-08: retrieval_miss_abstained -> correct_labeled_context
  pass-2 paraphrased-03: correct_unlabeled_context -> correct_labeled_context
  pass-2 paraphrased-05: correct_unlabeled_context -> correct_labeled_context
  pass-2 paraphrased-08: incomplete_or_wrong -> correct_labeled_context

Gate checklist:
  Gate 1: PASS � pass-1 net Hit@5=4; required >= 2
  Gate 2: PASS � Hit@3 deltas={'pass-1': 1, 'pass-2': 1}; Hit@5 deltas={'pass-1': 4, 'pass-2': 4}
  Gate 3: PASS � previously hit@5 questions lost=[]; each loss requires an explanation
  Gate 4: PASS � false accepts baseline=4, experiment=4 (limit 4); answered-unanswerable baseline=0, experiment=0; new answered-unanswerable questions=[]
  Gate 5: MANUAL � human-reviewed end-to-end correctness is not computed
  Gate 6: PASS � median total tokens baseline=2835.5, experiment=3971.5; limit=1.5x baseline
  Gate 7: PASS � hit-by-file@5 baseline=13, experiment=16; hit-by-function@5 baseline=1, experiment=5 (7 applicable, 9 module-level n/a)
  Gate 8: PASS � net Hit@5=4; only exactly +1 is inconclusive
  Gate 9: PASS � MRR delta=0.127083; supporting only, not an adoption route

JSON report: D:\Projects\incidentweave\evaluation\results\runs\20261018T124223Z-2274338-w100_o20\chunking-comparison.json
```

---

### [012] Copilot (2026-10-18): current-status correction

**Confirmed from saved artifacts:** Both runs recorded in [011] completed on source commit `22743382a4980d7787bc798d9ad8e2ab6ddecb18` with `code_dirty=false`, pinned corpus SHA `62d0e58593bb22d187ec7930274b0457afd3be74`, and 40 files. The baseline report records 70 chunks; the 100/20 report records 52 chunks. Both reports show 42 generation HTTP calls and 0 generation errors (baseline: 2 HTTP 429 responses; 100/20: 1).

**Confirmed from the saved comparison:** Hit@5 is 11/16 for 60/10 and 15/16 for 100/20; no prior Hit@5 questions were lost. Gates 1–4 and 6–9 are recorded PASS, with Gate 5 MANUAL. The decision report is [evaluation/chunking-strategy-decision-report.md](../evaluation/chunking-strategy-decision-report.md).

**Correction to current status only:** The experiment is complete and its run evidence is recorded in [011]. The “not authorized” sentence in [010] is retained as a historical statement from that entry and is superseded for current status by [011]–[012]. Gate 5 has not been reviewed by a human; adoption remains provisional and the 60/10 baseline remains the production choice pending that review.
