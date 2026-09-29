# Later Optimizations and Follow-up Notes

This file tracks issues and improvements that are valid, useful, and worth doing later, but are not required for the current phase to function correctly.

## 1) Noisy repository ingestion filtering

### Summary
This is a general follow-up for ingestion of arbitrary repositories, including non-Python repositories. Generated, vendored, or third-party source can dilute retrieval quality, but the specific directories to exclude depend on the repository's languages and tooling.

### Scope and provenance
This note was added after testing broad investigation questions against the separately ingested `dexterai` repository, where retrieval produced weak or insufficient project-level evidence. The observed results did not establish that any particular directory caused the retrieval behavior. IncidentWeave's current ingester only indexes `*.py` files, so these JavaScript-oriented examples are not claims about noise in IncidentWeave's own indexed corpus.

### Observed pattern
When a repository has weak retrieval quality, the system correctly refuses to guess. The failure mode is usually:
- `Cited chunks: []`
- `Diagnosis: INSUFFICIENT_EVIDENCE`
- low confidence

This does not indicate a bug in the core investigation pipeline; it indicates the indexed repo content is noisy or not well filtered.

### Recommended later work
- When ingestion is broadened beyond Python files, consider filtering generated or dependency directories appropriate to each repository's ecosystem. Examples for JavaScript/Node.js repositories include:
  - `node_modules`
  - `dist`
  - `build`
  - `vendor`
  - `.next`
  - `.cache`
  - `coverage`
- For Python repositories, evaluate relevant generated, vendored, or dependency directories based on actual corpus and retrieval evidence rather than applying the JavaScript list.
- Consider a repository-specific allowlist/denylist policy for large external dependencies.
- Re-ingest noisy repos after filtering and re-test project-level questions.

## 2) Repo-level question quality improvements

### Summary
Broad questions like “what does this project do?” are often too high-level for a repository that does not contain a clear README, entrypoint, or app structure in the indexed evidence.

### Recommended later work
- Prefer queries about concrete evidence sources:
  - main entry point
  - startup files
  - root config files
  - build scripts
  - package manifests
  - module structure
- Improve retrieval by excluding generated and dependency-heavy folders before indexing.

## 3) Citation matching robustness

### Summary
The parser currently matches citations by file path + line range when the model emits prose references, which prevents false negatives from natural-language evidence references.

### Status
This is already implemented in the current parser and validated with a live Gemini response.

## 4) Phase discipline

### Summary
This project explicitly separates core functionality from later optimization work. If a branch or issue is not required to complete the current phase, it should be documented here rather than mixed into the implementation work itself.

### Rule
When a problem is caused by noisy data, generated dependencies, or repo quality rather than a bug in the investigation engine, log it here and continue the phase work without widening scope.

## Findings from Phases 5-7

### 1) Widening cannot repair vector-distance rejection

**Observed:** `search_vector()` orders cosine distance ascending and applies a top-N limit; the Phase 6 guard uses the minimum returned vector distance as `best_vector_score`.

**Impact:** Widening the limit cannot change the nearest neighbor or improve the minimum vector distance, so a vector-distance rejection cannot be repaired by this retry on any corpus. RRF may still change when a wider candidate gains membership in the second retrieval list.

**Possible later work:** Use a different fallback or retrieval strategy for vector-distance failures rather than relying on a wider top-N query.

### 2) Literal grep receives the full query

**Observed:** `graph.py` passes `state["query"]` directly as the `keyword` argument to `call_grep_search_mcp()`, which sends it unchanged to `grep_search`.

**Impact:** `grep_search` looks for the entire query string as one case-insensitive literal substring in a source line. It is useful for pasted error strings, exact phrases, or identifiers, but generally will not match ordinary natural-language questions unless that full question appears verbatim in one line.

**Possible later work:** Extract identifiers or rare tokens from a query before calling grep, without adding an unconstrained LLM tool-choice loop.

### 3) Only grep_search is called through MCP

**Observed:** `graph.py` calls `hybrid_search()` directly in its `retrieve` node. Only `call_grep_search_mcp()` creates the stdio MCP client and calls the `grep_search` tool. The MCP server exposes both `hybrid_search` and `grep_search`.

**Impact:** The hybrid-search MCP tool is exposed and discoverable, but unused by the graph; hybrid retrieval remains an in-process call while grep crosses the MCP process boundary.

**Possible later work:** Decide whether exposing hybrid search through MCP provides value for another process or client before routing it through MCP solely for symmetry.

### 4) MCP process cost

**Observed:** Each `call_grep_search_mcp()` invocation constructs `StdioServerParameters`, enters `stdio_client()`, starts `python -m app.investigation.mcp_server`, initializes a `ClientSession`, calls grep, and exits the context.

**Impact:** A new server subprocess is created for each grep call. This is a real process boundary for the Phase 7 claim, but it adds startup and teardown cost to every fallback.

**Possible later work:** Reuse a long-lived MCP client/server session if fallback volume or latency makes per-call process startup material.

### 5) Docker app-to-scripts dependency

**Observed:** `app/investigation/mcp_server.py` imports `iter_python_files` from `scripts.ingest_repo`, while `docker/Dockerfile` copies only `pyproject.toml` and `app/`, not `scripts/`.

**Impact:** The built image would not contain the imported `scripts` package, so importing the MCP server inside that image would fail. This is a packaging/inversion issue, not fixed in this docs-only audit.

**Possible later work:** Move shared ingestion file-selection logic into an application package or package/copy `scripts` deliberately before relying on MCP inside the container.

### 6) Gemini key loading is split between settings and scripts

**Observed:** `app/config.py` defines `gemini_api_key` through `Settings` and `.env` configuration, but `generation.py` and `scripts/embed_chunks.py` each call `os.getenv("GEMINI_API_KEY")` directly. Neither path calls `load_dotenv()` itself.

**Impact:** Those direct script/API calls require `GEMINI_API_KEY` to already be in the process environment; defining `gemini_api_key` in `Settings` does not automatically make `os.getenv()` return it.

**Possible later work:** Centralize secret loading/config access so CLI and application paths use one explicit configuration mechanism.

### 7) Citation matching is not claim verification

**Observed:** `parsing.py` marks a retrieved result as cited when the response contains its chunk ID, file path, or file path plus line range.

**Impact:** This detects that a retrieved file was mentioned, but it does not verify that each diagnosis claim is supported by the cited lines.

**Possible later work:** Add a separate verifier pass that checks claims against cited evidence, with its own evaluation and failure behavior.

### 8) Phase 7 fallback reproducibility depends on manual embedding state

**Observed:** The Checkpoint 8 success case used `tests/fixtures/phase7_grep_probe.py`, re-ingested and embedded it, then manually set its two database embeddings to `NULL` before running the literal fallback. The fixture remains inside the indexed source tree.

**Impact:** Re-embedding the fixture changes the retrieval outcome, and the constructed escalation case is not a naturally reproducible result from a clean embedding run. The exact case requires the fixture plus the embedding-null preparation.

**Possible later work:** Add a deterministic integration fixture or test database setup that models the missing-vector condition without mutating a shared working database.

### 9) Small original corpus limited natural retry testing

**Observed:** Phase 6 measured the original `incidentweave-local` corpus at 31 chunks, all embedded; the Phase 7 corpus was later expanded with Phase 7 files and fixture content.

**Impact:** The original small corpus rarely produced a meaningful limit-5 versus limit-10 retry case, so Phase 6's live retry recovery was not demonstrated naturally.

**Possible later work:** Evaluate retry and escalation on larger, representative repositories rather than treating the small local corpus as a general performance or recall benchmark.

## Findings from Phases 5-7

### 1) Widening cannot repair vector-distance rejection

**Observed:** `search_vector()` orders cosine distance ascending and applies a top-N limit; the Phase 6 guard uses the minimum returned vector distance as `best_vector_score`.

**Impact:** Widening the limit cannot change the nearest neighbor or improve the minimum vector distance, so a vector-distance rejection cannot be repaired by this retry on any corpus. RRF may still change when a wider candidate gains membership in the second retrieval list.

**Possible later work:** Use a different fallback or retrieval strategy for vector-distance failures rather than relying on a wider top-N query.

### 2) Literal grep receives the full query

**Observed:** `graph.py` passes `state["query"]` directly as the `keyword` argument to `call_grep_search_mcp()`, which sends it unchanged to `grep_search`.

**Impact:** `grep_search` looks for the entire query string as one case-insensitive literal substring in a source line. It is useful for pasted error strings, exact phrases, or identifiers, but generally will not match ordinary natural-language questions unless that full question appears verbatim in one line.

**Possible later work:** Extract identifiers or rare tokens from a query before calling grep, without adding an unconstrained LLM tool-choice loop.

### 3) Only grep_search is called through MCP

**Observed:** `graph.py` calls `hybrid_search()` directly in its `retrieve` node. Only `call_grep_search_mcp()` creates the stdio MCP client and calls the `grep_search` tool. The MCP server exposes both `hybrid_search` and `grep_search`.

**Impact:** The hybrid-search MCP tool is exposed and discoverable, but unused by the graph; hybrid retrieval remains an in-process call while grep crosses the MCP process boundary.

**Possible later work:** Decide whether exposing hybrid search through MCP provides value for another process or client before routing it through MCP solely for symmetry.

### 4) MCP server process cost

**Observed:** Each `call_grep_search_mcp()` invocation constructs `StdioServerParameters`, enters `stdio_client()`, starts `python -m app.investigation.mcp_server`, initializes a `ClientSession`, calls grep, and exits the context.

**Impact:** A new server subprocess is created for each grep call. This is a real process boundary for the Phase 7 claim, but it adds startup and teardown cost to every fallback.

**Possible later work:** Reuse a long-lived MCP client/server session if fallback volume or latency makes per-call process startup material.

### 5) Docker app-to-scripts dependency

**Observed:** `app/investigation/mcp_server.py` imports `iter_python_files` from `scripts.ingest_repo`, while `docker/Dockerfile` copies only `pyproject.toml` and `app/`, not `scripts/`.

**Impact:** The built image would not contain the imported `scripts` package, so importing the MCP server inside that image would fail. This is a packaging/inversion issue, not fixed in this docs-only audit.

**Possible later work:** Move shared ingestion file-selection logic into an application package or package/copy `scripts` deliberately before relying on MCP inside the container.

### 6) Gemini key loading is split between settings and scripts

**Observed:** `app/config.py` defines `gemini_api_key` through `Settings` and `.env` configuration, but `generation.py` and `scripts/embed_chunks.py` each call `os.getenv("GEMINI_API_KEY")` directly. Neither script calls `load_dotenv()` itself.

**Impact:** Those direct script/API calls require `GEMINI_API_KEY` to already be in the process environment; defining `gemini_api_key` in `Settings` does not automatically make `os.getenv()` return it.

**Possible later work:** Centralize secret loading/config access so CLI and application paths use one explicit configuration mechanism.

### 7) Citation matching is not claim verification

**Observed:** `parsing.py` marks a retrieved result as cited when the response contains its chunk ID, file path, or file path plus line range.

**Impact:** This detects that a retrieved file was mentioned, but it does not verify that each diagnosis claim is supported by the cited lines.

**Possible later work:** Add a separate verifier pass that checks claims against cited evidence, with its own evaluation and failure behavior.

### 8) Phase 7 fallback reproducibility depends on manual embedding state

**Observed:** The Checkpoint 8 success case used `tests/fixtures/phase7_grep_probe.py`, re-ingested and embedded it, then manually set its two database embeddings to `NULL` before running the literal fallback. The fixture remains inside the indexed source tree.

**Impact:** Re-embedding the fixture changes the retrieval outcome, and the constructed escalation case is not a naturally reproducible result from a clean embedding run. The exact case requires the fixture plus the embedding-null preparation.

**Possible later work:** Add a deterministic integration fixture or test database setup that models the missing-vector condition without mutating a shared working database.

### 9) Small original corpus limited natural retry testing

**Observed:** Phase 6 measured the original `incidentweave-local` corpus at 31 chunks, all embedded; the Phase 7 corpus was later expanded with Phase 7 files and fixture content.

**Impact:** The original small corpus rarely produced a meaningful limit-5 versus limit-10 retry case, so Phase 6's live retry recovery was not demonstrated naturally.

**Possible later work:** Evaluate retry and escalation on larger, representative repositories rather than treating the small local corpus as a general performance or recall benchmark.

---

## Findings from Phase 8

### 1) Hybrid retrieval tied vector-only

**Observed:** On 16 answerable questions, vector-only and hybrid both produced hit@1 `8/16`, hit@3 `11/16`, hit@5 `11/16`, and MRR `0.5729166667`. Full-text was empty for 14 of 16 questions (Phase 8 Checkpoint 6).

**Impact:** Hybrid did not improve these metrics over the best single method, vector-only. The small sample does not establish that fusion is generally unhelpful.

**Possible later work:** Repeat the comparison with a held-out set and another repository before considering retrieval changes.

### 2) Guard distance ranges overlap

**Observed:** At the production thresholds there were 16 true accepts, 0 false refusals, 4 true refusals, and 4 false accepts. The maximum answerable best-vector distance was `0.41252605`; the minimum unanswerable value was `0.38905540`, an overlap of `0.02347064`. No cutoff in the tested `0.30`–`0.60` sweep separated both groups perfectly (Checkpoint 7).

**Impact:** A vector-distance cutoff alone did not cleanly separate answerable and unanswerable questions in this sample.

**Possible later work:** Collect and independently review a larger held-out set before evaluating any threshold change.

### 3) Retry and grep did not recover evidence

**Observed:** Across two runs there were 8 initial-insufficient attempts, 0 widened-retry recoveries, 8 grep attempts, and 0 grep recoveries (Checkpoint 8).

**Impact:** Neither fallback added a recovered question in this evaluation. These counts are from one 24-question set and are not a general estimate of fallback utility.

**Possible later work:** Evaluate fallback behavior on a held-out set that includes exact-string queries suited to literal grep, without tuning this phase's golden set.

### 4) One outcome changed between runs

**Observed:** `direct-08` was correct by the keyword screen in run 1 and wrong-or-incomplete in run 2; 1 of 24 question outcomes changed. There were 40 generation HTTP calls total, 20 per run, no 429 responses, and no errors (Checkpoint 8).

**Impact:** The two runs show one observed outcome change, but this small sample is insufficient to characterize model variance.

**Possible later work:** Repeat runs on a held-out set and report outcome changes separately from API errors.

### 5) False accepts and refusal-style diagnoses need careful reading

**Observed:** The guard false-accepted all 4 near-unanswerable questions and false-refused none of the 16 answerable questions. The generated diagnosis for each false accept was the literal `INSUFFICIENT_EVIDENCE`; because generation ran, the Phase 8 outcome definition classified them as falsely answered. For `paraphrased-08` in both runs and `direct-08` in run 2, the guard accepted the evidence but generation returned the same marker, resulting in wrong-or-incomplete outcomes (Checkpoints 7–8).

**Impact:** Guard sufficiency, whether generation ran, and diagnosis text are distinct signals. The keyword screen and refusal-state rule should not be read as semantic verification of the model's answer.

**Possible later work:** Review the outcome taxonomy against human-labeled answers on a held-out set; no classifier, prompt, or guard changes were made in Phase 8.

### 6) Citation matches are not claim verification

**Observed:** All 55 cited IDs for answerable questions mapped to returned retrieval results, but only 19 matched a golden relevance label (Checkpoint 8).

**Impact:** A citation mapping to a retrieved chunk does not establish that it supports the diagnosis claim.

**Possible later work:** Evaluate claim-to-evidence support separately with reviewed examples.

### 7) Evaluation limits

**Observed:** The evaluation used 24 questions against one pinned IncidentWeave source snapshot; labels remain pending maintainer review, and answer correctness uses keyword groups (Checkpoints 4 and 9).

**Impact:** These results are diagnostic for this corpus and are not a benchmark or evidence about other repositories. Keyword checks can accept wrong content or reject valid paraphrases.

**Possible later work:** Obtain maintainer review, add a held-out corpus, and consider a separately scoped answer-judging method.

This file is intentionally a holding area for improvement work that should be revisited later once the core implementation is complete and verified.
