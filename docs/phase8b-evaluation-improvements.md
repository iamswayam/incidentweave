# Phase 8b — Evaluation Improvements

**Status:** Not started
**Depends on:** Phase 9 (merged). Phase 8 evaluation (`evaluation/`, `scripts/run_eval.py`) exists.
**Document type:** Task spec AND running log, same pattern as `phase5` to `phase9`. This file is the single shared record of the whole Claude / Copilot / maintainer conversation about this work.

---

## 0. How to maintain this document (read first)

### 0.1 Roles

| Who | Role | May edit |
|---|---|---|
| **Claude** (reviewer / architect) | Wrote the spec. Reviews each gate. Never edits the repository. | Spec sections and every `Reviewer verdict` block, via the maintainer |
| **Copilot** (implementer) | Reads this file, implements one task at a time, records what it did. | **Only** the `Copilot log` block of the current task, the Progress tracker row, the Deviations table and the Open questions list |
| **Maintainer** (you) | Relays between the two. Pastes Claude's verdicts in. Decides when to proceed. | Anything |

### 0.2 Rules

1. **Copilot does not edit spec text.** If the spec looks wrong or unworkable, record it under the task's "Deviations" and "Open questions for reviewer" and stop. Do not silently change the plan.
2. **One task at a time, one commit per task.** Record the commit SHA in the log.
3. **Real output only.** Paste real command output (`pytest`, `ruff`, `run_eval.py`). Never simulate output or invent numbers.
4. **Log before moving on.** A task is not done until its log is filled in and its acceptance checklist is ticked or explained.
5. **Stop at every gate.** Gates are marked `🛑 PAUSE`. At a gate Copilot stops, the maintainer sends this file (plus the items listed at the gate) to Claude, and Claude fills in the `Reviewer verdict`. Work continues only when the verdict is **Approved** or **Approved with changes** (then do the listed changes first).
6. **Changes requested by Claude** are added by the maintainer as a new `Round N` entry inside that task's `Reviewer verdict` block. Copilot answers in a matching `Round N response` entry inside the same `Copilot log`. Nothing is overwritten; history stays visible.
7. **Never commit secrets.** Do not print or store `GEMINI_API_KEY` or `API_PROTECTION_SECRET`. `.env` stays git-ignored.
8. Dates use `YYYY-MM-DD`. Commands use `.\.venv\Scripts\python.exe` on Windows.

### 0.3 Status markers

`⬜ not started` · `🟡 in progress` · `✅ done (awaiting review)` · `🟢 approved` · `🔴 rework requested` · `⛔ blocked`

### 0.4 Copilot log template (copy this inside each task's log)

```
Status: 
Date: 
Commit SHA: 
Files and functions inspected: 
Analysis and decisions (what I found, what I decided, why): 
Changes made (file -> summary): 
Deviations from spec (or "none"): 
Commands run and real output (pytest, ruff, others): 
Acceptance checklist results: 
Open questions for reviewer: 
```

### 0.5 What the maintainer sends Claude at each gate

1. This file (with logs filled in).
2. `git diff --stat` and the full diff of the commits listed in the log.
3. Real `pytest -q` and `ruff check .` output.
4. At Gate C and later: the header section of the new `report.json` (everything except the `records` array).

### 0.6 Kickoff prompt to give Copilot (paste once per session)

> Read `docs/phase8b-evaluation-improvements.md` fully. Follow section 0 exactly. Work only on the task I name. Do not edit spec text, only the `Copilot log`, Progress tracker, Deviations and Open questions. Respect the hard constraints in section 1. When the task is done, fill in the log with real output and stop. If the task ends at a `🛑 PAUSE`, do not start the next task.

Per task, add one line: *"Now implement Task N only."*

---

## 1. Context and hard constraints

**Purpose.** Phase 8 produced a useful diagnostic evaluation, but a review of the code and result files found validity problems that make the numbers hard to interpret and impossible to compare across runs. This phase fixes the **measurement**, not the system under test.

**Hard constraints (apply to every task)**

- Do **not** change: `app/investigation/guard.py` thresholds, `confidence.py`, `prompt.py`, `generation.py`, any file in `app/retrieval/`, graph nodes or routing in `graph.py`, or the questions and labels in `evaluation/golden_set.json`.
- No new dependencies (standard library only). **No Langfuse or other tracing backend in this phase.**
- Keep `persist=False` in the evaluation. Only the `incidentweave-eval` repository may be written to. Keep the "non-eval repository changed" inventory check.
- Never print, log or store `GEMINI_API_KEY`. Keep `safe_error_text`.
- Keep the evaluation code outside `app/`. The only permitted `app/` change is the small pure helper in Task 2.
- Do not invent result numbers in docs. Fill them in only from a real run.
- Counts, not percentages, in reports (existing Phase 8 convention).

---

## 2. Findings that motivate the work (reviewer's analysis)

Facts below were verified against the repository and the result files in `evaluation/results/`.

| # | Finding | Evidence |
|---|---|---|
| F1 | The evaluation snapshot is exported from `HEAD`, but the golden set is pinned to `62d0e58593bb22d187ec7930274b0457afd3be74`. On the current HEAD the golden-set validation fails: the SHA does not match, and `unanswerable_near-03` fails because "authentication" now appears in `app/api_security.py`. Any commit to `app/` also changes the corpus. | `evaluation/runner.py::run_evaluation`, `snapshot_sha()` |
| F2 | The outcome taxonomy conflates failures. All 4 `falsely answered` records are the model correctly returning `INSUFFICIENT_EVIDENCE`. The 3 `wrong-or-incomplete` answerable records (`paraphrased-08` both runs, `direct-08` run 2) had **no labeled chunk in context**. | `metrics.is_refused`, `runner.classify_outcomes`, `results/*.json` |
| F3 | The keyword screen credits answers whose labeled chunk never reached the model: 4 such "correct" answers in run 1, 3 in run 2. | `metrics.answer_screen`, `retrieval_results` vs `relevant` |
| F4 | No per-question latency, token usage, raw response or prompt fingerprint is recorded in evaluation results (`persist=False` drops them). | record keys in `results/baseline.json` |
| F5 | Each run overwrites `baseline.json`, `run-2.json` and `evaluation_report.json`. There is no run ID or configuration fingerprint, so runs cannot be compared. | `scripts/run_eval.py`, `.gitignore` |
| F6 | The guard's RRF check cannot reject anything when vector results exist. A rank-1 hit scores 1/61 = 0.016393, above the 0.016 threshold. Minimum RRF is identical for answerable and unanswerable questions. | `guard.py`, `guard_distributions` in the report |
| F7 | Citation quality is only visible per record. Across both runs only 19 of 55 cited chunks matched a labeled relevance substring. | `cited_chunk_relevance` |

**Baseline facts from the Phase 8 results (sanity checks only, not assertions):**
snapshot 40 files / 70 chunks · retrieval vector and hybrid hit@1 8/16, hit@3 11/16, hit@5 11/16, MRR 0.5729 · full-text empty for 14/16 · guard 16 true accepts, 0 false refusals, 4 true refusals, 4 false accepts · 40 generation HTTP calls, 0 HTTP 429.

---

## 3. Progress tracker

*(Copilot updates its own column. Claude's verdict column is updated by the maintainer.)*

| Task | Title | Copilot status | Commit SHA | Gate | Reviewer verdict |
|---|---|---|---|---|---|
| 1 | Freeze the corpus | ✅ done (awaiting review) | pending | 🛑 A | |
| 2 | Per-question capture | ⬜ | | | |
| 3 | Outcome taxonomy v2 | ⬜ | | 🛑 B | |
| 4 | Run registry, metadata, compare script | ⬜ | | 🛑 C (after manual run) | |
| 5 | Report diagnostics | ⬜ | | | |
| 6 | Docs addendum | ⬜ | | 🛑 D (final) | |

---

## 4. Task 1: Freeze the corpus (do this first)

**Problem (F1).** The corpus changes whenever the code changes, so runs are not comparable and the evaluation currently cannot run on HEAD.

**Desired behavior.** The snapshot is always exported from `golden_set["pinned_sha"]`. The code under test is whatever is checked out. The report records both.

**Files to inspect and modify**
- `evaluation/runner.py`: `snapshot_sha`, `run_evaluation`
- `evaluation/corpus.py`: `export_snapshot`
- `evaluation/golden.py`: `validate_golden_set` (read only, do not change)

**Changes**
- [ ] Add a pure `resolve_corpus_sha(data: dict) -> str` in `runner.py`. It returns `data["pinned_sha"]` and raises `ValueError` if missing or empty.
- [ ] In `run_evaluation`, call `export_snapshot(ROOT, corpus_sha, ...)` and `validate_golden_set(data, snapshot_root, corpus_sha)`.
- [ ] Keep `snapshot_sha()` but use it only as `code_sha`.
- [ ] In `corpus.py`, add `commit_exists(root, sha)` using `git cat-file -e <sha>^{commit}`. If it fails, raise a clear `RuntimeError` saying the pinned commit is not in this clone and full history must be fetched.
- [ ] Add `code_sha` and `code_dirty` (`git status --porcelain` non-empty) to the report. Keep the top-level `pinned_sha` key (equal to the corpus SHA).

**Tests**
- [ ] `resolve_corpus_sha` returns the pinned value, not HEAD, and raises on missing or empty input.
- [ ] `ruff check .` and the full existing test suite still pass.

**Acceptance**
- [ ] Golden validation passes on the current HEAD (can be checked without Gemini or DB by running validation against the exported snapshot).
- [ ] The exported snapshot has 40 files and 70 chunks, matching Phase 8.
- [ ] `golden_set.json` is unchanged.

### Copilot log: Task 1

```
Status: ✅ done (awaiting review)
Date: 2026-10-05
Commit SHA: pending commit
Files and functions inspected: evaluation/runner.py::{snapshot_sha, resolve_corpus_sha, run_evaluation}; evaluation/corpus.py::{commit_exists, export_snapshot}; evaluation/golden.py::validate_golden_set
Analysis and decisions (what I found, what I decided, why): The root cause was in run_evaluation: it exported the current HEAD and validated the golden set against HEAD, even though the repo expects the pinned corpus SHA from golden_set["pinned_sha"]. I kept snapshot_sha() as code_sha only, added resolve_corpus_sha() to force the pinned corpus, and gated export_snapshot() on an explicit git cat-file check so missing history fails clearly before any archive is created.
Changes made (file -> summary): evaluation/runner.py -> added resolve_corpus_sha(data); run_evaluation now uses corpus_sha for snapshot export and validation; records code_sha and code_dirty in the report. evaluation/corpus.py -> added commit_exists(root, sha) and a clear RuntimeError when the pinned commit is missing locally. tests/unit/test_evaluation.py -> added targeted regression tests for the pinned SHA behavior.
Deviations from spec (or "none"): none
Commands run and real output (pytest, ruff, others):
- & "D:\Projects\incidentweave\.venv\Scripts\python.exe" -m pytest -q tests/unit/test_evaluation.py
  11 passed in 19.05s
- & "D:\Projects\incidentweave\.venv\Scripts\python.exe" -m pytest -q
  2 integration failures; both fail because PostgreSQL on localhost:5432 is unavailable: psycopg.errors.ConnectionTimeout: connection timeout expired
- & "D:\Projects\incidentweave\.venv\Scripts\ruff.exe" check .
  All checks passed!
- & "D:\Projects\incidentweave\.venv\Scripts\python.exe" -c "...validate_golden_set..."
  snapshot_files 40
  snapshot_chunks 70
  validation_errors []
Acceptance checklist results: [x] resolve_corpus_sha returns the pinned value and raises on missing or empty input. [x] Golden validation passes on the current HEAD (snapshot_files 40, snapshot_chunks 70, validation_errors []). [x] The exported snapshot has 40 files and 70 chunks, matching Phase 8. [x] golden_set.json is unchanged. [ ] Full existing test suite still pass (unticked: the project-wide pytest run fails due a missing local PostgreSQL instance, not because of the Task 1 code change).
Open questions for reviewer: none
```

### Reviewer verdict: Task 1

```
Verdict: (Approved / Approved with changes / Rework)
Reviewed on: 
Notes: 
Required follow-ups: 
```

> ### 🛑 PAUSE: Gate A
> **Copilot stops here.** Send Claude this file, the Task 1 diff, and `pytest` / `ruff` output. Do **not** start Task 2 until the verdict above is **Approved**.

---

## 5. Task 2: Per-question capture

**Problem (F4).** Evaluation records have no latency, token usage, raw response or prompt fingerprint.

**Desired behavior.** Each evaluation record carries the generation details for that question, with no change to pipeline behavior or to the API response shape.

**Files to inspect and modify**
- `app/investigation/parsing.py`: reuse `_response_text`, add one pure helper
- `scripts/investigate.py`: `investigate_repository` (both return dicts)
- `evaluation/runner.py`: `run_pipeline_once`, the `counted_urlopen` wrapper
- `app/api.py` (read only): confirm the response is built from explicit fields so an extra key in the result dict is ignored

**Changes**
- [ ] In `parsing.py`, add a pure `extract_generation_trace(prompt, response_payload) -> dict | None`. Return `None` if there is no payload. Otherwise return:
  ```
  {"prompt_sha256", "prompt_chars", "raw_text",
   "finish_reason" (candidates[0].finishReason or None),
   "usage" (dict copy of usageMetadata, or {}),
   "total_tokens" (usageMetadata.totalTokenCount or None)}
  ```
  Never include the full payload or any URL.
- [ ] In `investigate_repository`, add `"generation_trace": extract_generation_trace(result.get("prompt"), result.get("response_payload"))` on the success path, and `None` on the insufficient-evidence branch. Do not change any existing key. (`graph.py` already carries `prompt` and `response_payload` in final state; no graph change is needed.)
- [ ] In `run_pipeline_once`, store per question:
  - `wall_ms`: `perf_counter` around `investigate_repository`
  - `throttle_wait_ms`: accumulate the milliseconds `counted_urlopen` sleeps for throttling
  - `generation_ms`: `result["latency_ms"] - throttle_wait_ms`, or `None` if no generation
  - `generation_http_calls`: per-question delta of `call_stats["http_calls"]`
  - `generation_trace`
  - the same keys with `None` values on the error-path record

**Tests**
- [ ] `extract_generation_trace` with a sample Gemini payload including `usageMetadata` and `finishReason`.
- [ ] `extract_generation_trace` with a payload missing usage (`usage == {}`, `total_tokens is None`).
- [ ] `extract_generation_trace(None, None)` returns `None`.
- [ ] `tests/unit/test_api.py` and `tests/unit/test_investigation_graph.py` still pass unchanged.

**Acceptance**
- [ ] `git diff` shows no change to `graph.py`, `guard.py`, `prompt.py`, `generation.py`, `confidence.py`, or retrieval modules.
- [ ] The API response shape is unchanged.

### Copilot log: Task 2

```
Status: 
Date: 
Commit SHA: 
Files and functions inspected: 
Analysis and decisions (what I found, what I decided, why): 
Changes made (file -> summary): 
Deviations from spec (or "none"): 
Commands run and real output (pytest, ruff, others): 
Acceptance checklist results: 
Open questions for reviewer: 
```

### Reviewer verdict: Task 2

```
Verdict: 
Reviewed on: 
Notes: 
Required follow-ups: 
```

*(No separate gate. Tasks 2 and 3 are reviewed together at Gate B. Copilot may start Task 3 once Task 2 is committed and logged.)*

---

## 6. Task 3: Outcome taxonomy v2 (additive)

**Problem (F2, F3).** The legacy `outcome` field conflates guard refusals, model abstentions and retrieval misses, and credits answers without checking whether the labeled chunk reached the model.

**Desired behavior.** Every record gets explicit fields that separate the guard, the model and the retrieval. The legacy `outcome` field and `classify_outcomes` stay unchanged for continuity.

**Files to inspect and modify**
- `evaluation/metrics.py`: add pure functions next to `is_refused`, `answer_screen`, `first_relevant_rank`
- `evaluation/runner.py`: `classify_outcomes`, `summarize_run`, `run_pipeline_once`

**New pure functions in `metrics.py`**
- [ ] `abstention_kind(diagnosis, generation_ran, raw_text) -> "explicit" | "parse_fallback" | None`
  - `None` if generation did not run, or the diagnosis is not `INSUFFICIENT_EVIDENCE`.
  - `"explicit"` if the diagnosis is `INSUFFICIENT_EVIDENCE` and `raw_text` contains `INSUFFICIENT_EVIDENCE`.
  - `"parse_fallback"` if the diagnosis is `INSUFFICIENT_EVIDENCE` but `raw_text` does not contain it. `parsing.py` falls back to that string when it cannot parse a diagnosis, so a malformed response must not count as a deliberate abstention.
- [ ] `classify_outcome_v2(category, error, guard_refused, abstained, labeled_in_context, screen_pass) -> str`

| Question type | Condition | `outcome_v2` |
|---|---|---|
| any | `error` set | `error` |
| answerable | guard refused | `guard_false_refusal` |
| answerable | abstained, label not in context | `retrieval_miss_abstained` |
| answerable | abstained, label in context | `model_false_abstention` |
| answerable | answered, screen pass, label in context | `correct_labeled_context` |
| answerable | answered, screen pass, label not in context | `correct_unlabeled_context` |
| answerable | answered, screen fail | `incomplete_or_wrong` |
| unanswerable | guard refused | `guard_true_refusal` |
| unanswerable | abstained | `model_abstained` |
| unanswerable | otherwise | `answered_unanswerable` |

- [ ] `value_distribution(values) -> {"min", "median", "max", "count"}` (nulls skipped; `None` fields when empty).

**Per-record fields to add (runner)**
- [ ] `guard_refused` (the existing `refused` value)
- [ ] `generation_ran`
- [ ] `abstention_kind`
- [ ] `labeled_rank` (`first_relevant_rank(retrieval_results, labels)`, answerable only)
- [ ] `labeled_chunk_in_context`
- [ ] `screen_pass`
- [ ] `outcome_v2`

**Summaries**
- [ ] `run_summaries[i]` gains `outcome_v2_counts` alongside the existing `outcome_counts`.

**Tests**
- [ ] `classify_outcome_v2` table-driven, covering all 10 branches.
- [ ] `abstention_kind` for explicit, parse_fallback, and not-generated.
- [ ] `value_distribution` with values, with nulls, and empty.
- [ ] Existing `is_refused`, `answer_screen` and golden-validation tests still pass unchanged.

**Acceptance**
- [ ] Legacy `outcome` values are unchanged for the same inputs.
- [ ] No `outcome_v2` value falls outside the table above.

### Copilot log: Task 3

```
Status: 
Date: 
Commit SHA: 
Files and functions inspected: 
Analysis and decisions (what I found, what I decided, why): 
Changes made (file -> summary): 
Deviations from spec (or "none"): 
Commands run and real output (pytest, ruff, others): 
Acceptance checklist results: 
Open questions for reviewer: 
```

### Reviewer verdict: Task 3 (and Task 2)

```
Verdict: 
Reviewed on: 
Notes: 
Required follow-ups: 
```

> ### 🛑 PAUSE: Gate B
> **Copilot stops here.** Send Claude this file, the Task 2 and Task 3 diffs, and `pytest` / `ruff` output. Do **not** start Task 4 until the verdict above is **Approved**.

---

## 7. Task 4: Run registry, metadata and compare script

**Problem (F5).** Runs overwrite each other and carry no configuration, so two runs cannot be compared meaningfully.

**Desired behavior.** Every run is saved under a unique ID with enough configuration to explain why two runs differ. Nothing is overwritten.

**Files to inspect and modify**
- `evaluation/runner.py`: `run_evaluation`, `write_json`
- `scripts/run_eval.py`
- new: `evaluation/compare.py`, `scripts/compare_runs.py`
- `.gitignore`, new `evaluation/results/runs/.gitkeep`
- read only: `app/investigation/guard.py`, `confidence.py`, `prompt.py`, for constants to import

**Changes**
- [ ] `run_id = f"{UTC:%Y%m%dT%H%M%SZ}-{code_sha[:7]}"`.
- [ ] Write the full report to `evaluation/results/runs/<run_id>/report.json`. Stop writing `baseline.json`, `run-2.json` and `evaluation_report.json`. Leave the existing committed `baseline.json` untouched as a historical Phase 8 artifact.
- [ ] Update `scripts/run_eval.py` to print `run_id` and the output path. Keep deleting `evaluation/_snapshot`.
- [ ] `.gitignore`: add `evaluation/results/runs/*` and `!evaluation/results/runs/.gitkeep`. Add the `.gitkeep`.
- [ ] Add a pure `build_run_metadata(...)` returning:
  ```
  run_id, started_at, finished_at, corpus_sha (== pinned_sha), code_sha, code_dirty,
  golden_set_sha256 (hash of the file bytes), golden_review_status,
  models {embedding, generation}, limit,
  thresholds {guard_rrf, guard_vector, calibration_rrf, calibration_vector}
      (import the constants; do not copy values),
  prompt_sha256 (hash of SYSTEM_INSTRUCTION), generation_config: "provider default (none set)",
  passes, config_sha256 (hash of the sorted JSON of the fields above, excluding times and run_id)
  ```
  Keep the top-level `pinned_sha` key for compatibility.
- [ ] `evaluation/compare.py::compare_reports(a, b) -> dict`. It must tolerate legacy reports that lack new fields (treat missing as `None`) and return:
  - config fields that differ
  - count deltas for `outcome_v2_counts`, `guard_counts`, `retrieval_tables`
  - per-question flips in `outcome_v2` or `labeled_rank` (pass 1 of each report)
  - median generation latency and total-token deltas
- [ ] `scripts/compare_runs.py <report_a> <report_b>` prints the result as readable text (argparse).
- [ ] *(Optional, only if trivial)* `--passes N` (default 2) in `run_eval.py`, scaling the generation budget but keeping the existing `MAX_GENERATION_HTTP_CALLS` cap.

**Tests**
- [ ] `build_run_metadata`: `config_sha256` is stable for equal inputs and changes when a threshold or the prompt hash changes (monkeypatch the constant).
- [ ] `compare_reports`: detects an `outcome_v2` flip and a `labeled_rank` change, reports config differences, and does not crash on a legacy report.
- [ ] Existing tests and `ruff check .` pass.

### 7.1 Manual verification run (needs Postgres and a Gemini key; about 40 generation calls)

Run `.\.venv\Scripts\python.exe scripts\run_eval.py`, then check:

- [ ] It completes on the current HEAD and a new `runs/<run_id>/report.json` exists.
- [ ] `snapshot_files == 40`, `snapshot_chunks == 70`, `corpus_sha` is `62d0e58593bb22d187ec7930274b0457afd3be74`.
- [ ] Deterministic results match the old report: `guard_counts` 16/0/4/4; retrieval tables hit@1 8, hit@3 11, hit@5 11, MRR about 0.5729 for vector and hybrid.
- [ ] `incidentweave-eval` has no rows in `investigations` or `audit_records`; chunk counts of the other repositories are unchanged.
- [ ] The four `unanswerable_near-*` records are `model_abstained` with `abstention_kind: "explicit"`. The four `unanswerable_far-*` are `guard_true_refusal`. There are zero `answered_unanswerable`.
- [ ] `paraphrased-08` is `retrieval_miss_abstained`. `paraphrased-03`, `-05`, `-07` are expected to be `correct_unlabeled_context` (model output may vary; explain any difference).
- [ ] `scripts\compare_runs.py` run on two reports prints sensible output, and no earlier report was overwritten.
- [ ] No API key value appears anywhere in the report or logs.

### Copilot log: Task 4 (including the manual run)

```
Status: 
Date: 
Commit SHA: 
Files and functions inspected: 
Analysis and decisions (what I found, what I decided, why): 
Changes made (file -> summary): 
Deviations from spec (or "none"): 
Commands run and real output (pytest, ruff, run_eval.py summary): 
Acceptance checklist results (including section 7.1): 
Run ID of the manual run: 
Open questions for reviewer: 
```

### Reviewer verdict: Task 4

```
Verdict: 
Reviewed on: 
Notes: 
Required follow-ups: 
```

> ### 🛑 PAUSE: Gate C
> **Copilot stops here.** Send Claude this file, the Task 4 diff, `pytest` / `ruff` output, and the **header section of the new `report.json`** (everything except `records`). Do **not** start Task 5 until the verdict above is **Approved**.

---

## 8. Task 5: Report diagnostics (measurement only)

**Problem (F6, F7, F4).** Citation quality, guard signal behavior, latency and tokens are not summarized at report level.

**Desired behavior.** Add these top-level report keys. Nothing here changes pipeline behavior.

**Files to inspect and modify**
- `evaluation/metrics.py`, `evaluation/runner.py::run_evaluation`
- read only: `guard.py` constants

**Changes**
- [ ] `citation_summary` (per pass, answerable questions only): `cited_total`, `cited_relevant` (from existing `cited_chunk_relevance`), `answers_with_zero_citations`.
- [ ] `guard_diagnostics` (computed, **not asserted**):
  ```
  rrf_threshold, rrf_rank1_floor (= 1/(60+1)),
  rrf_gate_can_reject_nonempty_vector_results (= rrf_threshold > rrf_rank1_floor),
  rrf_rejections (count of checks whose reason mentions the RRF threshold),
  vector_rejections (count mentioning vector distance)
  ```
- [ ] `latency_summary` and `token_summary`: `value_distribution` over `generation_ms`, `wall_ms` and `total_tokens` for records where generation ran, per pass.

**Tests**
- [ ] `guard_diagnostics` returns `can_reject == False` at threshold 0.016 and `True` at 0.02.
- [ ] Citation summary arithmetic is correct on synthetic data.
- [ ] Existing tests and `ruff check .` pass.

### Copilot log: Task 5

```
Status: 
Date: 
Commit SHA: 
Files and functions inspected: 
Analysis and decisions (what I found, what I decided, why): 
Changes made (file -> summary): 
Deviations from spec (or "none"): 
Commands run and real output (pytest, ruff, others): 
Acceptance checklist results: 
Open questions for reviewer: 
```

### Reviewer verdict: Task 5

```
Verdict: 
Reviewed on: 
Notes: 
Required follow-ups: 
```

*(No separate gate. Task 5 is reviewed together with Task 6 at Gate D.)*

---

## 9. Task 6: Docs addendum (only after a real run exists)

**Changes**
- [ ] Add a short "Phase 8b" addendum at the end of `docs/phase8-evaluation.md`: what changed, the new record and report fields, and the run ID of the verification run.
- [ ] Add one entry to `docs/later-optimizations.md` listing deferred items (section 10).
- [ ] Add a Phase 8b entry to `docs/README.md` linking this file.
- [ ] In the root `README.md` Phase 8 section, replace the "4 falsely answered" wording with the split taxonomy, **using real counts from the verification run only**. Do not use adjectives such as robust, accurate, reliable or proven (existing Phase 8 wording rule).
- [ ] Do not edit `golden_set.json`, and do not change its `review_status`.

### Copilot log: Task 6

```
Status: 
Date: 
Commit SHA: 
Files and functions inspected: 
Analysis and decisions (what I found, what I decided, why): 
Changes made (file -> summary): 
Deviations from spec (or "none"): 
Commands run and real output (pytest, ruff, others): 
Acceptance checklist results: 
Open questions for reviewer: 
```

### Reviewer verdict: Task 6 and overall

```
Verdict: 
Reviewed on: 
Notes: 
Required follow-ups: 
Langfuse spike go / no-go: 
```

> ### 🛑 PAUSE: Gate D (final)
> **Copilot stops here.** Send Claude this file, all diffs since Gate C, `pytest` / `ruff` output, and the final `report.json` header. Claude gives the overall verdict and decides whether the Langfuse spike (separate document) should start.

---

## 10. Out of scope (do not implement in this phase)

- Persisting refusals, prompts or raw responses to `Audit` (needs a migration and a production behavior decision).
- Fixing full-text query semantics (`websearch_to_tsquery` ANDs every term), the guard's ineffective RRF check, or any threshold. These are retrieval and guard changes and need a held-out set first.
- An LLM judge or groundedness model.
- Langfuse or any tracing backend.
- Adding or editing golden-set questions or labels.

---

## 11. Deviations from spec

*(Copilot adds a row whenever it departs from the spec. An empty table at Gate D means no deviations.)*

| Date | Task | What changed | Why | Reviewer decision |
|---|---|---|---|---|
| | | | | |

---

## 12. Open questions

*(Copilot adds questions for the reviewer here and in the task log. The maintainer pastes Claude's answers in the "Answer" column.)*

| # | Date | Task | Question | Answer (from Claude) |
|---|---|---|---|---|
| | | | | |

---

## 13. Decision log

| Date | Decision | By | Reason |
|---|---|---|---|
| 2026-10-05 | Langfuse deferred until the evaluation validity fixes are done | Maintainer, with Claude | Langfuse would sit on top of a corpus that drifts with HEAD and an outcome taxonomy that mislabels abstentions; it fixes neither |
| 2026-10-05 | Keep legacy `outcome` and add `outcome_v2` | Claude | Preserves continuity with Phase 8 docs and the committed `baseline.json` |
| 2026-10-05 | Do not change guard thresholds, retrieval or prompts in this phase | Claude | Phase 8 rule: no tuning against a 24-question set without a held-out set |

---

## 14. Final hand-off checklist (before Gate D)

- [ ] All six tasks have a filled log and a reviewer verdict of Approved.
- [ ] `pytest -q` and `ruff check .` pass on the final commit.
- [ ] One real evaluation run exists in `evaluation/results/runs/` and is referenced in the docs.
- [ ] Deviations table and Open questions table are resolved.
- [ ] `git diff` against the Phase 9 commit shows no change to the do-not-change files listed in section 1.
- [ ] No secrets in the repository, logs or reports.
