# Phase 8 — Evaluation

**Status:** Not started
**Depends on:** Phase 7 (controlled tools & audit, merged to main) — confirmed.

Same pattern as Phases 3-7: this document is the task spec AND the running
log. Fill in each checkpoint's "Log" section with real detail before moving
on. Run every command for real; never simulate output. The maintainer is
away for this session: do not wait for input, make and justify the design
decisions the checkpoints ask for, and continue.

**Why this phase exists, precisely:** every quality claim so far rests on a
handful of hand-picked live queries per phase. The guard thresholds (RRF
>= 0.016, cosine distance <= 0.5) were set from a few samples, and the
logged probes show a thin margin: an in-domain question had a best distance
of about 0.491 (Phase 6, Checkpoint 7), while identifier-like and
symbol-heavy probe strings chosen to be unlike the corpus reached about 0.49
(Phase 7, Checkpoint 8). Hybrid retrieval has never been compared against
its own parts (full-text search often returned nothing for natural-language
questions). The widened-limit retry has never been shown to help on real
data, and the model's run-to-run variance has never been measured. This
phase replaces anecdotes with a repeatable measurement. The honest result
may be unflattering; that is the deliverable, not a problem to smooth over.

**Honest limits, stated up front and repeated in the final report:**
- Small sample (target 24 questions) and one corpus: this project's own
  source code. Results are diagnostic for this setup, not a benchmark, and
  say nothing about other repositories. Report counts (for example
  "11 of 16"), not percentages that imply precision.
- The golden set is drafted by the implementer from reading the same code the
  system indexes, so it will lean toward the code's own vocabulary. That is
  why it includes a paraphrased category with machine-checked anti-leakage
  rules. The set carries `review_status: pending maintainer review` until
  the maintainer changes it.
- Keyword-based answer checks are crude: they can pass a wrong answer that
  mentions the right terms and fail a correct paraphrase. Treat them as a
  screen. The report must include the full diagnosis text of every
  answerable question so a human can read them.
- No LLM judge this phase. It would add a second source of nondeterminism
  and cost, and the checks here stay deterministic and auditable. It is a
  candidate for later.
- Do not tune thresholds, prompts, or retrieval against this set. With about
  24 items, any tuning would overfit. Findings go into
  `docs/later-optimizations.md`; any change belongs to a later phase with a
  held-out set.

**Scope for this session, do not exceed it:**
- Pipeline behavior stays unchanged: no changes to guard thresholds,
  prompts, retrieval logic, or graph routing. The only permitted change to
  existing code is a minimal `persist` switch (default on, behavior
  unchanged), and only if the CLI's pipeline function cannot otherwise run
  without writing Investigation/Audit rows (see Checkpoint 2).
- No new dependencies (standard library only).
- Evaluation code lives outside `app/`, so it stays out of the Docker image.
- Database safety: create or replace data only for the repository named
  `incidentweave-eval`. Never run ingestion, deletes, or embedding against
  `incidentweave-local`, `incidentweave`, `dexterai`, or any other
  repository. Do not write to `investigations` or `audit_records` during
  evaluation.
- Never print, log, cache, or commit the value of `GEMINI_API_KEY`.
- Delete every temporary helper script before finishing and confirm none
  remain (`scripts/_*.py`, `evaluation/_*.py`).
- Windows/PowerShell: write helper code to files instead of inline `-c`
  strings (quoting has broken earlier phases). Use
  `.\.venv\Scripts\python.exe -m pytest` and `.\.venv\Scripts\ruff.exe`.
  Set the Windows selector event loop policy in any script that does async
  database access, as the existing scripts do.
- API budget: keep total Gemini generation calls under about 120 for the
  whole phase, throttle to at least 1.5 seconds between calls, count HTTP
  429 responses, and log actual call counts.

---

## Checkpoint 1 — Baseline and environment check

**Task:** Record the starting state so the end state can be compared to it:
current branch; `git rev-parse HEAD` (this is the pinned commit for the
evaluation corpus); working tree state; the baseline
`.\.venv\Scripts\python.exe -m pytest -q` count; that Postgres is reachable
and `alembic current` is at head; whether `GEMINI_API_KEY` is available to
the process (report only present or absent, never the value); and a
read-only inventory of every repository name in the database with its chunk
count.

### Log
- Branch and pinned commit SHA: `phase-8/evaluation`, HEAD `62d0e58593bb22d187ec7930274b0457afd3be74`.
- Baseline test count: `.\.venv\Scripts\python.exe -m pytest -q` returned `22 passed in 27.62s`.
- Database baseline: `alembic current` reported `20260819_0001 (head)`; TCP port 5432 was reachable (`Test-NetConnection localhost -Port 5432` returned `True`). Repository inventory was `dexterai: 774`, `incidentweave: 48`, `incidentweave-local: 72`.
- API key present (yes/no): `False` in the Python process environment at baseline. The value was not printed. The existing local evaluation commands will load `.env` without logging its value when live Gemini calls are required.
- Working tree baseline: existing docs-only changes and untracked `docs/phase8-evaluation.md` were present before Phase 8 implementation; no source/config changes were made by the baseline helper, which was deleted afterward.

---

## Checkpoint 2 — Design decisions

**Task:** Decide and write down each of the following. Recommended defaults
are in brackets; deviate only with a stated reason.

1. **Corpus snapshot** [export the pinned commit with `git archive` into a
   temporary directory, delete `tests/fixtures/` from that copy, ingest it as
   repository `incidentweave-eval`]. Reason: the working tree changes as the
   code changes; a pinned commit keeps chunks and labels stable. Confirm the
   method works on Windows without extra tools.
2. **Relevance rule** [a retrieved chunk is relevant to a question if its
   `file_path` equals a labeled file and its content contains the labeled
   substring, case-insensitive; several labels on one question mean any-of].
   Line numbers are not used because they shift.
3. **Metrics**, each with an exact written definition:
   - Retrieval (answerable questions only): hit@1, hit@3, hit@5 and MRR for
     vector-only, full-text-only and hybrid, all at the production limit of
     5 (truncate for hit@1 and hit@3), plus the count of empty full-text
     results.
   - Guard (all questions): counts of true accept, false refusal, true
     refusal and false accept at the current thresholds (import the
     constants from `guard.py`, do not retype them); best-vector and
     best-RRF distributions per category; an offline sweep of the
     vector-distance cutoff.
   - End-to-end: per answerable question an outcome of correct,
     wrong-or-incomplete, false refusal or error; per unanswerable question
     an outcome of refused, falsely answered or error. Define "refused"
     precisely and give examples from real output. Cited-chunk relevance
     (use the returned `retrieval_results` to map cited ids to content).
     Escalation statistics from the `tool_calls` trace: initial-insufficient,
     retry-recovered, grep-attempted, grep-recovered.
   - Answer-correctness screen: `must_mention` is a list of lists; each inner
     list holds acceptable alternatives (case-insensitive); a question passes
     if every inner list has at least one hit.
4. **Running the pipeline** [call the same function the CLI uses, so the
   evaluation exercises the shipped path; if it cannot run without
   persisting, add a `persist` parameter defaulting to True instead of
   copying the state-building code].
5. **Files** [suggested: an `evaluation/` package with pure metric
   functions, the golden set with its loader and validator, corpus setup and
   runners; a `scripts/run_eval.py` CLI; results in `evaluation/results/`;
   a query-embedding cache in `evaluation/cache/`, gitignored]. Make sure
   the package is importable from tests the same way `scripts` is.
6. **Nondeterminism and limits** [cache query embeddings; run the
   end-to-end evaluation twice and report how many outcomes changed between
   runs; record API errors separately and never count them as pass or
   fail].
7. **What each report records** [pinned SHA, chunk count, model names and
   thresholds imported from code, limits, date, per-question records].

### Log
- 1. Corpus snapshot: use `git archive HEAD` to export the pinned Phase 8 commit into a temporary directory, delete `tests/fixtures/` from that copy because it is a test-only fixture and not part of the production corpus, then call the existing `scripts/ingest_repo.py` and `scripts/embed_chunks.py` with repository name exactly `incidentweave-eval`. The setup must reject every other repository name and never delete or update their rows.
- 2. Relevance rule: a result is relevant when its `file_path` equals a golden label's file and its `content` contains the labeled substring case-insensitively. Multiple labels are any-of for retrieval hit metrics; line numbers are deliberately ignored because chunk boundaries can move.
- 3. Metric definitions: for answerable questions, hit@K is the count of questions whose first K results contain at least one relevant result; MRR is `1/rank` for the first relevant result, or `0` for no hit. Compute these for vector-only, full-text-only, and hybrid at production limit 5; full-text empty count is the number with zero FTS rows. Guard categories compare `is_sufficient` against answerability: true accept = answerable and sufficient, false refusal = answerable and insufficient, true refusal = unanswerable and insufficient, false accept = unanswerable and sufficient. Best-distance/RRF distributions use the observed best values, with missing values recorded as null. The offline distance sweep varies the cutoff from `0.30` through `0.60` by `0.02` without changing code. End-to-end `refused` means the final diagnosis is exactly `INSUFFICIENT_EVIDENCE` and no generation diagnosis is returned; answerable outcomes are `correct`, `wrong-or-incomplete`, `false refusal`, or `error`; unanswerable outcomes are `refused`, `falsely answered`, or `error`. The answer screen passes only when every inner `must_mention` alternative group has at least one case-insensitive hit in the diagnosis. Cited relevance maps returned cited IDs back to returned result content. Escalation counts read the stored trace: initial-insufficient, retry-recovered, grep-attempted, and grep-recovered.
- 4. How the pipeline is run: call the shipped `scripts.investigate.investigate_repository()` path with `persist=False`; add only this minimal optional switch because otherwise the CLI path writes Investigation/Audit rows. The default remains `persist=True`, preserving existing behavior. Evaluation always passes repository name `incidentweave-eval` and never calls the pipeline for any other name.
- 5. File layout: `evaluation/` contains pure metric functions, golden-set validation, corpus setup, and runners; `evaluation/golden_set.json` stores the 24 labels; `evaluation/results/` stores reports with `baseline.json` reserved for one run; `evaluation/cache/` stores query embeddings; `scripts/run_eval.py` provides the evaluation CLI; `tests/unit/test_evaluation.py` tests standard-library-only metric and schema logic.
- 6. Nondeterminism handling: cache one embedding per question, throttle embedding/generation calls by at least 1.5 seconds, run the end-to-end set twice, and compare per-question outcomes. API errors are separate records and never count as pass or fail. No LLM judge is used.
- 7. Report contents: pinned HEAD SHA, eval chunk count, model names, imported guard thresholds, retrieval limit, date, category counts, per-question labels/results/diagnoses/confidence/citations/trace/errors, metric tables, sweep rows, and run-to-run outcome changes.

---

## Checkpoint 3 — Build the evaluation index

**Task:** Implement snapshot, ingest and embed for `incidentweave-eval`. It
must be idempotent, touch only that repository name, embed every chunk, and
leave no chunk without an embedding.

### Log
- Snapshot method and location: `git archive HEAD` at `62d0e58593bb22d187ec7930274b0457afd3be74`, extracted with the Windows `tar` command to `evaluation/_snapshot/source`; `tests/fixtures/` was removed from the exported copy. The snapshot contained 40 Python files and 70 expected chunks.
- Files and chunks ingested: 40 files, 70 chunks in `incidentweave-eval`.
- Embedding summary (embedded / failed / skipped): The first attempt ran without loading `.env` and reported `embedded=0, failed=70, skipped=0` (`GEMINI_API_KEY is not set`); no key value was printed. Retried in the same process after calling `load_key_without_logging()`: `embedded=70, failed=0, skipped=0`.
- Query output proving zero chunks with a NULL embedding: `null_embeddings=0` for `incidentweave-eval` after embedding.
- Confirmation that every other repository's chunk count matches Checkpoint 1: before `{'dexterai': 774, 'incidentweave': 48, 'incidentweave-eval': 70, 'incidentweave-local': 72}`; after the successful retry the inventory was identical. The original repositories remain `dexterai: 774`, `incidentweave: 48`, and `incidentweave-local: 72`.

---

## Checkpoint 4 — Draft the golden set

**Task:** Create the golden set file. Its header records the pinned SHA,
`review_status: pending maintainer review`, and the counts. Target 24
questions:
- 8 `direct`: answerable, may share vocabulary with the code
- 8 `paraphrased`: answerable, written as an engineer new to the codebase
  would ask, without the code's identifiers
- 4 `unanswerable_far`: out of domain
- 4 `unanswerable_near`: plausible to ask of a codebase but absent from this
  one (for example a cache, message queue, user login, or deployment target
  this project does not have); choose a topic only after a search of the
  snapshot confirms it is absent

Coverage rules: answerable questions must span at least six distinct areas
(for example database session, chunking, embedding, hybrid fusion, guard,
confidence calibration, graph retry, MCP and grep, persistence, parsing),
with at most three questions per file. Questions used in earlier phase logs
(async sessions, the CEO's car, violin tuning, quartz comet, health
endpoint) may appear at most four times in total and must be marked
`seen_before: true`, so their results can be read separately.

Fields: every question has `id`, `category`, `question`. Answerable ones add
`relevant` (file and substring labels) and `must_mention`. `unanswerable_near`
ones add `absent_terms`. Unanswerable questions have no relevance labels.

### Log
- Counts per category: `direct=8`, `paraphrased=8`, `unanswerable_far=4`, `unanswerable_near=4` (24 total), read from `evaluation/golden_set.json`.
- `review_status` value written: `pending maintainer review`.
- Questions marked `seen_before`: 0. The answerable questions span 9 distinct source files/areas; the maximum answerable questions per file is 3.

---

## Checkpoint 5 — Verify the golden set against the snapshot

**Task:** Write a verification step that fails loudly on any of these:
(a) a labeled file missing from the snapshot, or its substring absent from
that file; (b) no ingested chunk in the index satisfying the relevance rule
for a question (the label must be reachable given chunk boundaries);
(c) a `paraphrased` question containing a snake_case or CamelCase identifier
from its relevant chunk, a labeled substring, or a labeled file's name stem;
(d) an `absent_terms` entry that appears in any `.py` file of the snapshot
(case-insensitive); (e) duplicate ids, invalid categories, unanswerable
questions carrying labels, or category counts that miss the targets without
a logged reason. Fix the set until it is clean. Keep the first run's failing
output in the log; do not rewrite it away.

### Log
- First run output (source and indexed-chunk checks): `{'source_validation_errors': [], 'indexed_chunk_validation_errors': [], 'indexed_chunks': 70}`.
- What was fixed: nothing in the golden set; its first complete validation passed. Added the indexed-label check to `evaluation.runner.run_evaluation()` so future evaluation runs fail if a label is not reachable in `incidentweave-eval`.
- Final clean run output: the first complete run was already clean: source-file/schema/coverage/identifier/absent-term validation returned `[]`; indexed-chunk reachability returned `[]` for 70 chunks.

---

## Checkpoint 6 — Retrieval evaluation

**Task:** Run vector-only, full-text-only and hybrid retrieval on every
answerable question at limit 5, using cached query embeddings (the only API
calls are one embedding per question). Report the table overall and split
by `direct` versus `paraphrased`, plus the full-text empty-result count.
State plainly whether hybrid beat the best single method, tied, or lost, and
by how much in counts. Do not explain away an unflattering result.

### Log
- Retrieval invocation: `retrieval_records()` evaluated 24 questions; `evaluation/cache/` contained 24 query-embedding files afterward. Generation calls: 0.
- Overall table, 16 answerable questions (`hit@1 / hit@3 / hit@5 / MRR`): vector `8 / 11 / 11 / 0.5729166666666666`; full-text `1 / 1 / 2 / 0.078125`; hybrid `8 / 11 / 11 / 0.5729166666666666`.
- Direct, 8 questions: vector `6 / 7 / 7 / 0.7916666666666666`; full-text `1 / 1 / 2 / 0.15625`; hybrid `6 / 7 / 7 / 0.7916666666666666`.
- Paraphrased, 8 questions: vector `2 / 4 / 4 / 0.3541666666666667`; full-text `0 / 0 / 0 / 0.0`; hybrid `2 / 4 / 4 / 0.3541666666666667`.
- Full-text empty-result count: 14 of 16 answerable questions.
- Plain-words comparison of hybrid against its parts: hybrid tied vector-only on hit@1, hit@3, hit@5, and MRR overall and in both categories. It exceeded full-text-only by 7, 10, and 9 hits at overall hit@1, hit@3, and hit@5 respectively; it did not beat the best single method, vector-only.

---

## Checkpoint 7 — Guard evaluation and offline threshold sweep

**Task:** Using the same retrieval results (no new API calls), compute: the
guard's true accept, false refusal, true refusal and false accept counts at
the current thresholds; min, median and max of the best vector distance and
best RRF score for answerable versus unanswerable questions; and a sweep of
the vector-distance cutoff from 0.30 to 0.60 in steps of 0.02, showing false
refusals and false accepts at each step. State whether any cutoff separates
the two groups perfectly and how wide the gap is. Do not change `guard.py`.

### Log
- Retrieval source: the same 24 query embeddings were reused from the on-disk cache; no new embedding API calls were needed. Imported production thresholds: `MIN_ACCEPTABLE_RRF_SCORE=0.016`, `MAX_ACCEPTABLE_VECTOR_DISTANCE=0.5`.
- Confusion counts at the current thresholds: true accept `16`, false refusal `0`, true refusal `4`, false accept `4` (24 total questions).
- Distribution table (answerable versus unanswerable):

  | Group | Best vector min / median / max | Best RRF min / median / max |
  |---|---:|---:|
  | Answerable (n=16) | `0.2743177312 / 0.3488702723 / 0.4125260475` | `0.0163934426 / 0.0163934426 / 0.0327868852` |
  | Unanswerable (n=8) | `0.3890554044 / 0.4863356640 / 0.5438544471` | `0.0163934426 / 0.0163934426 / 0.0163934426` |

- Sweep table (`vector cutoff : false refusals / false accepts`): `0.30: 14/0`; `0.32: 13/0`; `0.34: 11/0`; `0.36: 3/0`; `0.38: 2/0`; `0.40: 2/1`; `0.42: 0/2`; `0.44: 0/2`; `0.46: 0/2`; `0.48: 0/4`; `0.50: 0/4`; `0.52: 0/5`; `0.54: 0/7`; `0.56: 0/8`; `0.58: 0/8`; `0.60: 0/8`.
- Plain-words conclusion about the margin: no cutoff from `0.30` through `0.60` separates the groups perfectly. The ranges overlap by `0.02347064` (`unanswerable min 0.38905540 - answerable max 0.41252605`); the current `0.5` threshold has 4 false accepts and no false refusals. No threshold was changed.

---

## Checkpoint 8 — End-to-end evaluation, two runs

**Task:** Run every question through the real pipeline (retrieve, guard,
retry, grep via MCP, generate, parse, calibrate) with no persistence,
against `incidentweave-eval`, using the snapshot directory as the repository
path. Do two complete runs back to back. For each question record:
`retry_used`, `evidence_source`, the `tool_calls` trace, the diagnosis text,
confidence (raw and calibrated where available), cited ids, whether it was
refused, the outcome, and any error text. Compute outcome counts per run,
the number of questions whose outcome differed between runs, escalation
statistics, and how many "high" confidences were downgraded. List every
non-correct outcome with its id, question and diagnosis text so a human can
read it. Handle HTTP 429 by recording an error, never by crashing. Save the
full per-question records under `evaluation/results/`; keep one run as
`baseline.json` and make sure the other files are gitignored.

### Log
- Summary table (24 questions per run):

  | Run | Correct | Wrong or incomplete | Refused | Falsely answered | Errors |
  |---|---:|---:|---:|---:|---:|
  | 1 | 15 | 1 | 4 | 4 | 0 |
  | 2 | 14 | 2 | 4 | 4 | 0 |

- Questions whose outcome changed between runs: `direct-08` changed from `correct` in run 1 to `wrong-or-incomplete` in run 2. Run 1 diagnosis: `The final confidence (\`final_confidence="medium"\`) is passed into persistence via the \`persist_investigation\` function call in unit tests (e.g., \`tests/unit/test_investigation_persistence.py\`).`; run 2 diagnosis: `INSUFFICIENT_EVIDENCE`.
- Escalation statistics across both runs: `initial_insufficient=8`, `retry_recovered=0`, `grep_attempted=8`, `grep_recovered=0`.
- Calibration downgrade count: 25 raw `high` confidences were calibrated below `high` across both runs.
- Total generation calls and error counts: 40 HTTP generation calls (20 per run), 0 HTTP 429 responses, 0 per-question errors. The configured hard cap was 119 calls; no error was counted as a pass or fail.
- Citation mapping: among answerable questions across both runs, 55 cited chunk IDs were returned; all 55 mapped to a returned `retrieval_results` item, and 19 matched a golden relevance label.
- Every non-correct outcome (each listed diagnosis is the literal `INSUFFICIENT_EVIDENCE`):
  - Run 1 `paraphrased-08`, “What record keeps the retrieved evidence and response metadata together?” — wrong-or-incomplete.
  - Run 1 `unanswerable_near-01`, “How is Redis configured for this application?” — falsely answered.
  - Run 1 `unanswerable_near-02`, “How does the message queue retry failed jobs?” — falsely answered.
  - Run 1 `unanswerable_near-03`, “Where is user login and authentication implemented?” — falsely answered.
  - Run 1 `unanswerable_near-04`, “Which Kubernetes deployment target does this service use?” — falsely answered.
  - Run 2 `direct-08`, “Where is the final confidence passed into persistence?” — wrong-or-incomplete.
  - Run 2 `paraphrased-08`, “What record keeps the retrieved evidence and response metadata together?” — wrong-or-incomplete.
  - Run 2 `unanswerable_near-01`, “How is Redis configured for this application?” — falsely answered.
  - Run 2 `unanswerable_near-02`, “How does the message queue retry failed jobs?” — falsely answered.
  - Run 2 `unanswerable_near-03`, “Where is user login and authentication implemented?” — falsely answered.
  - Run 2 `unanswerable_near-04`, “Which Kubernetes deployment target does this service use?” — falsely answered.
- Full per-question records, including all answerable diagnosis text, labels, confidence fields, citations and traces: `evaluation/results/baseline.json`, `evaluation/results/run-2.json`, and the combined `evaluation/results/evaluation_report.json`. The eval repository still has 0 Investigation and 0 Audit rows after the runs.

---

## Checkpoint 9 — Unit tests (CI-safe)

**Task:** Add tests that use no database, no network and no Gemini: metric
functions against hand-computed expected values (hit@k, MRR including a
no-hit case and ties, confusion counts, the sweep); the relevance rule;
golden set schema validation (unique ids, valid categories, label and
`absent_terms` rules, category counts); and the refused-detection function
on real-looking outputs, including edge cases seen in Checkpoint 8. The
existing tests must remain unchanged.

### Log
- Test files added: `tests/unit/test_evaluation.py` (10 tests covering retrieval ranking/MRR, guard confusion and sweep, answer screening/refusal, relevance and indexed-label reachability, golden-set schema/labels/absent terms, and snapshot SHA validation). No existing test file was modified.
- Real full-suite count (baseline plus N new; state N): `32 passed in 27.75s` (`22` baseline tests + `10` Phase 8 tests).

---

## Checkpoint 10 — Findings

**Task:** Write the findings into this log and add a "Findings from Phase 8"
section to `docs/later-optimizations.md`, using Observed / Impact / Possible
later work. Every finding must trace to numbers logged above. At minimum:
the retrieval comparison; the guard margin; whether the retry or the grep
fallback ever recovered anything; run-to-run variance; false refusals and
false accepts with examples; and the limits of this evaluation. These are
recommendations only: no threshold, prompt or retrieval changes this phase.

### Log
- Retrieval (Checkpoint 6): vector-only and hybrid tied at hit@1 `8/16`, hit@3 `11/16`, hit@5 `11/16`, and MRR `0.5729166667`; full-text returned no results for `14/16` answerable questions. Hybrid did not beat its best single method.
- Guard margin (Checkpoint 7): current-threshold confusion was `16` true accepts, `0` false refusals, `4` true refusals, and `4` false accepts. Answerable and unanswerable best-vector ranges overlap by `0.02347064`; none of 16 tested cutoffs separated them perfectly.
- Escalation (Checkpoint 8): across both runs there were `8` initial-insufficient attempts, `0` retry recoveries, `8` grep attempts, and `0` grep recoveries.
- Run variance (Checkpoint 8): one question (`direct-08`, 1 of 24) changed outcome; run 1 returned a keyword-screen pass with a cited answer, while run 2 returned `INSUFFICIENT_EVIDENCE` after the guard accepted the evidence.
- False refusals and false accepts (Checkpoints 7–8): guard evaluation had `0` false refusals and `4` false accepts. The false-accept examples were the four `unanswerable_near` questions (Redis, message queue, authentication, Kubernetes); all four passed the guard in each run, and the generated diagnosis text was `INSUFFICIENT_EVIDENCE`. By the logged definition, these count as falsely answered because generation ran and no guard refusal occurred. For answerable `paraphrased-08` in both runs and `direct-08` in run 2, the guard accepted evidence but generation returned `INSUFFICIENT_EVIDENCE`; these were classified wrong-or-incomplete, not guard false refusals. The outcome label follows the measured pipeline state even though the diagnosis text reads like a refusal.
- Citation matching (Checkpoint 8): of 55 cited chunks for answerable questions, all mapped to retrieved results but only `19/55` matched a labeled relevance substring.
- Limits (Checkpoints 4, 8, and 9): this is a 24-question sample over one repository snapshot. Labels remain pending maintainer review and were drafted from the indexed source; keyword checks are a screen, not claim verification; there is no LLM judge. The results are diagnostic for this snapshot and do not establish performance on other repositories.

---

## Checkpoint 11 — Update README

**Task:** Update `README.md`:
- Phase 8 complete and Phase 9 next in the status table and the roadmap
- A "Phase 8" collapsible section (same style as Phases 1-7): what is
  measured, how to reproduce it (real commands taken from `--help` output),
  the baseline numbers as counts from the logged run with the sample size
  stated next to each, and the honest limits in two or three plain sentences
- The project structure tree (`evaluation/`, `scripts/run_eval.py`,
  `docs/phase8-evaluation.md`)
- The test count, matching Checkpoint 9
- The Technology Stack "Planned" row: remove the evaluation harness
- Wording rules: no adjectives such as robust, accurate, reliable or proven.
  Do not say the golden set was manually reviewed or who authored it; state
  its size, its categories, and how labels are verified. The review status
  lives in the golden set file header.
- If `docs/README.md` exists on this branch, add the Phase 8 entry; if it
  does not, skip that and note it here.

### Log
- Status table and roadmap: Phase 8 is marked complete and Phase 9 Production CLI / API is marked next; README milestone and completed phases are updated.
- Phase 8 section: reports the measured sample sizes and counts above, pending-review status and label-verification method, and the two-to-three-sentence evaluation limitations.
- Reproduction command: `scripts/run_eval.py --help` printed `Example: .\.venv\Scripts\python.exe scripts\run_eval.py`; the same command appears in the README.
- Project structure: added `evaluation/`, `scripts/run_eval.py`, and `docs/phase8-evaluation.md`.
- Test count: README current verification reports `32 passed`, matching Checkpoint 9.
- Technology Stack: removed the evaluation harness from the Planned row.
- Documentation index: `docs/README.md` exists and now links to `phase8-evaluation.md`.
- Text/report verification output: `{'phase8_complete': True, 'phase9_next': True, 'reproduction_command': True, 'evaluation_harness_removed_from_planned': True, 'project_tree_includes_runner': True, 'test_count': True, 'docs_index': True, 'measured_counts_match': True}`.

---

## Checkpoint 12 — Final full regression

**Task:** Run the complete verification sequence one more time, plus the
safety checks below.

### Log
- `\.venv\Scripts\python.exe -m pytest -q` — final output: `32 passed in 87.08s (0:01:27)`.
- `\.venv\Scripts\ruff.exe check .` — final output: `All checks passed!`. The first final-gate run found 9 Phase 8 lint errors (2 E501 lines, import ordering, and an unused import); after local fixes, the targeted Ruff check and this full workspace check passed.
- `docker build -f docker/Dockerfile .` — final output: `[+] Building 10.0s (10/10) FINISHED`, image `sha256:fd709cd72943c632fcde78fe0ab8c17c346b95c411cfa6a3c0f7f01cca63ea86`.
- Repository inventory after finishing: `dexterai: 774`, `incidentweave: 48`, `incidentweave-local: 72` (all match Checkpoint 1), plus `incidentweave-eval: 70`. A final DB query returned `eval_null_embeddings=0`, `eval_investigations=0`, `eval_audits=0`.
- Confirmation that no temporary helper scripts remain: searches for `scripts/_phase8*.py` and `evaluation/_phase8*.py` returned no files. `evaluation/_snapshot` is absent after the run. The only visible result file is `evaluation/results/baseline.json`; `run-2.json` and `evaluation_report.json` are gitignored.
- `git status --short`: `M .gitignore`, `M README.md`, `M docs/later-optimizations.md`, `M scripts/investigate.py`; untracked Phase 8 outputs include `docs/phase8-evaluation.md`, `evaluation/`, `scripts/run_eval.py`, and `tests/unit/test_evaluation.py`. The worktree also contains pre-existing user changes (`docs/learning/README.md`, `docs/phase1-project-setup.md`, `docs/phase2-database-persistence.md`, `docs/phase3-ingestion-chunking.md`, `docs/README.md`, `docs/learning/07-mcp-integration.md`, and the untracked `e HEAD` file); these were preserved, not treated as Phase 8 changes.
- `git diff` for existing production code: only `scripts/investigate.py` differs among production files; the prohibited `guard.py`, `prompt.py`, `generation.py`, `parsing.py`, and `graph.py` have no diff. The production change preserves default behavior and adds the optional switch:

  ```python
  persist: bool = True
  ...
  if persist:
      # existing Investigation/Audit persistence path
      ...
  ```

- `.gitignore` covers the query-embedding cache and non-baseline results: `git check-ignore -v` matched `evaluation/cache/`, `evaluation/results/run-*.json`, and `evaluation/results/evaluation_report.json`; `git check-ignore evaluation/results/baseline.json` returned no match (`baseline_ignored=False`).

---

## After all checkpoints

Do not proceed to Phase 9. Do not commit or push; that happens separately,
reviewed with the maintainer. Finish with a report containing: (1) every
golden set question in a table, for the maintainer's review; (2) the list of
non-correct outcomes and the questions that flipped between runs; (3)
anything that could not be verified.
