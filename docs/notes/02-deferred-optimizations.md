# Later Optimizations and Follow-up Notes

**As of 2026-11-01.**

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

## Later ideas from the restructuring

| Idea | Why | Evidence needed |
|---|---|---|
| Generate the status index from machine-readable document metadata. | A manually maintained index can drift as the documentation set grows. | Define a small metadata format, validate every tracked Markdown path, and prove generated links and statuses match the intended index before adopting generation. |
| Move documents into the purpose-based Option A structure. | Reference, decisions, experiments, runbooks, and how-to guides would be easier to discover at scale. | Keep current Option B labels and links stable first; then test a migration with link validation, redirects or aliases, and an explicit freeze policy. |
| Pair each new experiment in its own folder with protocol, results, and data. | Current protocols, notes, and artifacts are split across separate numbering schemes and folders. | Pilot one newly registered experiment and verify development/held-out boundaries, artifact retention, and navigation before changing existing records. |
| Publish a documentation site. | A searchable rendered site could improve navigation beyond Markdown indexes. | Evaluate hosting, access control for private repository material, link preservation, and an offline build before deployment. |
| Add a changelog and release tags. | A user-facing release history would separate shipped changes from checklist progress. | Agree on release boundaries, versioning, migration notes, and a repeatable release process before creating tags. |

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

### 8) Phase 8b follow-up: measurement validity and run comparability

**Observed:** The final Phase 8b run `20261015T151657Z-c203e0e` used the pinned 40-file / 70-chunk snapshot and stored per-question generation metadata under a unique run ID. Each of its two 24-question passes recorded `correct_labeled_context` 10, `correct_unlabeled_context` 2, `retrieval_miss_abstained` 2, `incomplete_or_wrong` 2, `guard_true_refusal` 4, and `model_abstained` 4. It made 40 generation HTTP calls with 0 HTTP 429 responses and 0 errors; the corrected diagnostics counted 0 RRF, 4 vector, and 0 other rejections.

**Impact:** The new run registry and additive taxonomy provide a consistent measurement baseline, but the underlying evaluation still uses a small known corpus and keyword labels rather than a review-grade benchmark.

**Possible later work:** Expand the set, review the labels, and compare run-level deltas on a larger held-out evaluation before making any guard or retrieval changes.

This file is intentionally a holding area for improvement work that should be revisited later once the core implementation is complete and verified.

## Phase 9 API follow-ups

- Invalid-secret requests are rejected before rate limiting, so unauthenticated traffic is not bounded by the per-IP limiter.
- The 502 mapping has unit coverage, but a live failing-provider response has not been exercised.

## Later ideas from items 14d and 18d

### BM25 B2 as a separately registered comparison

- **Idea:** Compare a separately registered BM25 variant with stop words, stemming, and identifier splitting for `snake_case` and `camelCase`.
- **Why:** [Note 17](./17-bm25-comparison-results.md) tested only naive BM25 without stemming or a stop list, and that variant lost to `ts_rank`.
- **Evidence needed:** Preregistered development-split conditions and a paired comparison against the same control before considering production registration.

### Weighted or learned fusion

- **Idea:** Compare weighted or learned fusion with equal-weight reciprocal-rank fusion.
- **Why:** The BM25 arm lost partly because noisy lexical hits displaced vector hits; different fusion weights may protect strong vector results.
- **Evidence needed:** A separately registered comparison with per-repository and per-question results showing repeatable improvement without safety regressions.

### Reranking the top results

- **Idea:** Evaluate a reranker over the top retrieved results.
- **Why:** A second-stage ranking may improve ordering while leaving the existing candidate retrieval and evidence guard intact.
- **Evidence needed:** An offline comparison showing better paired ranking metrics at acceptable latency and without weakening refusal behavior.

### AST or function-level chunking

- **Idea:** Compare tree-sitter AST/function-level chunks with the current line windows.
- **Why:** The 60/10 line windows cut about a third of functions, which may separate relevant code from its context.
- **Evidence needed:** A registered chunking experiment reporting retrieval quality, function-boundary coverage, chunk counts, and indexing cost across representative repositories and languages.

### Larger and more varied question sets

- **Idea:** Expand evaluation to 100+ questions across more repositories and languages.
- **Why:** With 33 answerable development questions, one rank change is about 0.015 pooled MRR.
- **Evidence needed:** Maintainer-reviewed questions and labels with repository/language coverage and a frozen held-out split kept out of tuning.

### Revisit HTTP 503 for generation unavailability

- **Idea:** Revisit HTTP 503 instead of HTTP 200 for `generation_unavailable`.
- **Why:** A real client that ignores `unavailable_answer`, `degraded`, or `outcome` could mistake the response for a generated answer.
- **Evidence needed:** Client integration evidence that degraded flags are ignored or mishandled, weighed against whether clients discard useful evidence bodies on 503.

### Optional source snippets in degraded evidence

- **Idea:** Consider optional source snippets in degraded evidence behind explicit access control.
- **Why:** Snippets could make retrieved locations easier to inspect without a second source lookup.
- **Evidence needed:** A reviewed authorization model, privacy assessment, and user need that justify exposing code in this response path.

### Diagnose why hybrid retrieval did not improve

- **Idea:** Analyze why hybrid retrieval did not improve even when lexical-only recall rose from 5/33 to 26/33.
- **Why:** The remaining limit may be vector ranking, chunk boundaries, or how the hybrid fusion ranks candidates rather than lexical matching.
- **Evidence needed:** Per-question branch ranks, candidate overlap, chunk-boundary diagnostics, and controlled development-split comparisons that isolate each cause.

### Measure cache hit rate and consider cache warm-up

- **Idea:** Add a privacy-preserving cache hit-rate metric and evaluate an explicit warm-up workflow.
- **Why:** Hit-rate data can establish whether persistent caching reduces provider calls; warm-up may help recurring workloads avoid cold-start latency.
- **Evidence needed:** Aggregate hit/miss counts without query text or hashes, measured provider-call reduction, and a workload showing startup cache misses are material.

### Evaluate semantic or near-duplicate query caching

- **Idea:** Compare exact normalized-query keys with semantic or near-duplicate query matching.
- **Why:** Similar questions may produce useful reusable vectors even when whitespace-normalized strings differ.
- **Evidence needed:** A privacy review and offline nearest-neighbor comparison showing that reuse does not change retrieval quality or merge materially different questions.

### Consider pgvector storage for cached vectors

- **Idea:** Move the cached JSON vector to a pgvector column if cache lookup requirements expand to similarity search.
- **Why:** Current lookups use exact identity only, so JSON is sufficient; a vector index would only help if similarity-based cache lookup is justified.
- **Evidence needed:** A concrete similarity-query use case, measured lookup bottleneck, and migration/index cost comparison.

### Register a weighted or tuned lexical fallback

- **Idea:** Compare a weighted lexical fallback or BM25 B2 after it is separately registered.
- **Why:** The current fallback reuses sanitized-OR C1; a better lexical ranker may improve degraded-mode evidence ordering.
- **Evidence needed:** Preregistered development-split conditions, paired per-question metrics, and a separate quality review before production use.

### Monitor degraded-mode frequency and quality

- **Idea:** Aggregate how often `generation_unavailable` and `embedding_unavailable` occur and measure their real quality impact.
- **Why:** The modes currently make safe, explicit responses, but their frequency and operational effect are unknown.
- **Evidence needed:** Privacy-reviewed counters and representative evaluations linking degradation events to service outcomes without retaining query text.

### Degrade earlier when the provider circuit opens

- **Idea:** Consider circuit-breaker-aware early degradation instead of waiting for the retry budget to finish.
- **Why:** An open circuit indicates recent provider unavailability and may avoid repeated latency from doomed attempts.
- **Evidence needed:** Provider outage traces showing retry delays dominate response time, plus tests demonstrating prompt recovery and no false early degradation.

## Later ideas from item 18c

### Check answerable guard refusals in embedding protocols

- **Idea:** Add an answerable guard-refusal check to future embedding comparison protocols.
- **Why:** R4 checks only unanswerable questions, so a model that refuses more can pass without revealing refusals of answerable questions.
- **Evidence needed:** Development and held-out comparisons reporting answerable refusals alongside unanswerable false accepts at a preregistered threshold.

### Re-run local embedding models with more resources

- **Idea:** Re-run local model embedding on a machine with more free memory or in a GPU notebook.
- **Why:** The laptop had about 0.5 GiB free memory during the measured runs, and the resulting CPU timings may overstate cost on better-resourced hardware.
- **Evidence needed:** Reproducible timing and memory measurements on the same registered inputs, with model builds and runtime configuration recorded.

### Compare larger code-specific embedding models

- **Idea:** Register larger code-focused models such as nomic-embed-code, CodeRankEmbed, or Salesforce SFR code embeddings.
- **Why:** A larger model trained for source code may improve retrieval on code concepts or identifiers.
- **Evidence needed:** A separately registered development comparison with model/license/footprint facts, control-path equivalence, paired metrics, and held-out validation before adoption.

### Compare higher Gemini embedding dimensions

- **Idea:** Register Gemini embedding output at 1536 or 3072 dimensions.
- **Why:** More output dimensions may preserve useful semantic detail that is compressed at 768 dimensions.
- **Evidence needed:** A separate preregistered run and a reviewed production vector-column migration plan, with retrieval and operational comparisons.

### Calibrate per-model evidence-guard thresholds

- **Idea:** Set an evidence-guard threshold per embedding model under item 3b.
- **Why:** Cosine-distance distributions differ across models, so the Gemini threshold may not represent equivalent evidence quality.
- **Evidence needed:** Approved held-out calibration and validation data with false-accept and false-refusal trade-offs.

### Add a cross-encoder reranker

- **Idea:** Rerank the fused top results with a separately evaluated cross-encoder.
- **Why:** A second-stage relevance model may improve ordering without changing initial candidate retrieval.
- **Evidence needed:** A preregistered paired comparison, measured latency and resource cost, and evidence that guard and citation behavior remain safe.

### Evaluate Matryoshka truncation

- **Idea:** Test Matryoshka truncation for a compatible local embedding model.
- **Why:** A shorter vector may reduce memory and compute while retaining retrieval quality.
- **Evidence needed:** Model documentation confirming supported truncation, a separate retrieval comparison, and measured storage/latency effects.

### Assess quantized or ONNX production serving

- **Idea:** Evaluate quantized or ONNX serving only if a local model is later selected for production.
- **Why:** Optimized inference may reduce serving footprint and improve throughput.
- **Evidence needed:** A production-representative benchmark for latency, memory, throughput, numerical drift, licensing, and operational maintenance.

## Later ideas after the 18c comparison

### Register Voyage AI embedding and reranking candidates

- **Idea:** Register Voyage AI `voyage-code-4` for code embeddings and `rerank-3` for reranking. Voyage's pricing page is reported to offer 200 million free tokens per account for these models, compared with roughly 0.1 million tokens in the development corpus.
- **Why:** The allowance could support a bounded development experiment covering both code embeddings and reranking.
- **Evidence needed:** A registered protocol like 14a/18c; before any use, verify Voyage's current data-use and training terms, rate limits without billing, free-tier eligibility, and output dimensions. Production uses a 768-dimensional vector column, so a different output size requires a column migration only if a candidate wins.

### Rerank the top 5–10 retrieved results

- **Idea:** Compare Voyage `rerank-3`, Cohere rerank (trial), and an open cross-encoder over the top 5–10 results.
- **Why:** The control hit@1 is 19/33, hit@3 is 26/33, and hit@5 is 28/33: descriptively, 9 questions have the correct chunk in the top five but not first, versus 5 that miss the top five. Reranking targets the larger group.
- **Evidence needed:** A separate registered paired evaluation that distinguishes ranking gains from retrieval recall, reports latency/resource/privacy costs, and preserves guard and citation behavior.

### Preserve a documented local path for private-code embeddings

- **Idea:** Keep a local embedding-model path documented as a privacy-driven option even though the tested local candidates lost on retrieval quality.
- **Why:** The development comparison measured pooled MRR of 0.505 for Jina and 0.535 for BGE, versus 0.674 for Gemini, while hosted free tiers may use inputs for product improvement.
- **Evidence needed:** Verify each provider's current data-use and training terms before indexing private code, and compare the privacy benefit, local operating cost, and retrieval-quality trade-off for the intended repositories.

### Test Gemini embeddings at larger output dimensions

- **Idea:** Register a lower-priority comparison of Gemini embedding outputs at 1536 or 3072 dimensions.
- **Why:** More dimensions may retain useful detail that is compressed in the current 768-dimensional vector.
- **Evidence needed:** A registered development run with control equivalence and a migration review; change the production vector column only if the candidate wins.

### Grow the development question set

- **Idea:** Expand beyond 33 answerable development questions.
- **Why:** With this sample, a single rank change shifts pooled MRR by about 0.015, making small comparisons coarse.
- **Evidence needed:** A larger, reviewed, repository-diverse question set with frozen split membership, explicit labels, and enough questions per repository to support the registered whole-question tolerances.
