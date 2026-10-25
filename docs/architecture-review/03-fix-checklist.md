# IncidentWeave: Prioritized Fix Checklist (merged from the Claude and Codex audits)

*Written 2026-10-21 by Claude (Sonnet 5.5); revised 2026-10-22 after the independent Codex review in `04-fix-checklist-review-codex.md`. Source reports: `01-audit-claude.md` and `02-audit-codex.md` in this folder. Code reference: the Codex review inspected commit `59f38fd`, which descends from `main` @ `e98da82` and from the evaluation harness @ `12edf8e`; that commit has 64 `test_` functions and 70 executed tests. The figures in Parts A and B come from the pinned evaluation snapshot (`62d0e58`).*

**How to use this file**
1. Work in the order of the **Recommended order** table in section 1 (it replaces the original top-to-bottom order). Item numbers are stable labels, not a sequence.
2. One item at a time. Each item has a **Done when** test. Do not start the next until the test passes.
3. After any change that affects retrieval or the guard, re-run the evaluation and record the result.
4. Effort: **S** = under half a day, **M** = 1–3 days, **L** = a week or more.
5. Item 1 is implemented and merged. The other entries were reviewed by Codex and the accepted changes are folded in below. Test counts and metrics are quoted only from a command that was actually run.

**Evidence tags** (same as in my audit): **[SRC]** read from code, **[EXEC]** I ran it, **[ART]** author-reported in repo docs/artifacts, **[INF]** my inference.

---

## Progress log

One row per item, updated when an item starts, finishes or is blocked. Status values: In progress, Done, Blocked (reason), Skipped (reason).

| Item | Status | PR | Note |
|---|---|---|---|
| 1 | Done | n/a | Input caps merged. |
| 2 | Done | #16 | Literal grep fallback removed from the investigation graph. |
| 3a | Done | #18 | Guard decides per chunk on vector distance; RRF is no longer a gate; threshold unchanged until 3b. |
| 4 | Done | #20 | Insufficient-evidence answers are forced to low confidence; citations are kept. |
| 5a | Done | #22 | Send the Gemini API key in a header; remove the moot MCP/grep timeout item. |
| 19 | Done | #25 | Confidence renamed to model self-rating. |
| 7 | Done | #26 | Every outcome is persisted. |
| 12a | Done | #29 | Evidence tags and secret skip. |
| 9 | Done | #30 | Ingest runs and upsert ingestion. |
| 8 | Done | #33 | Replayable audit record. |
| 11 | Done | #34 | Structured output and citation validation. |
| 10 | Done | #36 | Async, batched provider client; first benchmark recorded in docs/notes/03-embedding-benchmark.md. |
| 13a | Done | #38 | Span labels, statistics, offline retrieval evaluation. |
| 13b | Done | #40 | CI gate and generation settings. |
| 16a | Done | #42 | multi-repo harness |
| 16b | In progress | pending | batch-processing-service data |
| Plan 06 added | Done | n/a | docs commit |

## 1. Fix-order checklist (summary)

| # | ✔ | Fix | Priority | Effort | Raised by |
|---|---|---|---|---|---|
| 1 | ☑ | Cap `limit`, query length and prompt size | High | S | Both |
| 2 | ☑ | Remove the literal grep fallback (as wired, the API could search the wrong repository) | High | S | Claude (Codex partial) |
| 3a | ☑ | Fix the evidence guard (per-chunk check, drop the vacuous RRF gate, literal evidence never sufficient) | **Critical** | S | Both |
| 3b | ☐ | Re-validate the guard thresholds on the held-out split (after item 16) | High | S | Both |
| 4 | ☑ | Make abstention consistent (low confidence; keep citations that explain the abstention; literal-evidence rule) | High | S | Claude |
| 5a | ☑ | Hardening now: API key in header | Medium | S | Both |
| 5b | ☐ | Hardening later: Docker non-root and env, healthcheck | Medium | S | Both |
| 6 | ☐ | Keep README/docs claims matching the code (done inside each item, not a standalone phase) | Medium | S | Both |
| 7 | ☑ | Persist every outcome (answered, refused, abstained, error) | High | M | Both |
| 8 | ☑ | Store a replayable audit (raw output, raw confidence, prompt, versions, thresholds) | High | M | Both |
| 9 | ☑ | Source versioning and upsert ingestion (commit SHA, content hashes, stable chunk IDs) | High | M | Both |
| 10 | ☑ | Async, batched provider client with deadlines and retries | High | M | Both |
| 11 | ☑ | Structured output and server-side citation validation | High | M | Both (Codex stronger) |
| 12a | ☑ | Injection and secret controls, early: evidence tags, secret skip, short threat-model note | Medium | S–M | Codex (Claude minor) |
| 12b | ☐ | Wider prompt-injection testing (later) | Low | M | Codex |
| 13a | ☑ | Evaluation foundation, part a: span labels, statistics, offline retrieval evaluation | High | M | Both |
| 13b | ☑ | Evaluation foundation, part b: CI regression gate, temperature 0, recorded generation settings | High | M | Both |
| 14 | ☐ | Cheap retrieval ablations: embedding task type, test-file policy, full-text fix | High | S–M each | Both |
| 15a | ☐ | Chunking upgrade, staged comparison, after 16a and 16b: function-aware chunks, enriched embedding text, parent expansion | High | M | New (data-driven, see Part A) |
| 16a | ☑ | Multi-repo evaluation harness: manifest, split-aware reports, smoke/held-out selection and per-repository gate | High | M | Both |
| 16b | ☐ | Multi-repo evaluation data: batch-processing-service’s approved questions, fixture and baseline | High | M | Both |
| 16c | ☐ | Multi-repo evaluation data: lifeos’s approved questions, fixture and baseline | High | M | Both |
| 17 | ☐ | LLM judge, claim-level citation scoring, larger abstention set | Medium | M | Both |
| 18 | ☐ | Tracing, cost and latency telemetry | Medium | M | Both |
| 19 | ☑ | Rename API/CLI confidence output as model self-rating | Medium | S–M | Codex (Claude data) |
| 20 | ☐ | Multi-artifact ingestion (docs, configs, logs) with metadata | Medium | L | Both |
| 21 | ☐ | Reranker experiment | Low | M | Both |
| 22 | ☐ | Incident-replay evaluation and hypothesis loop (flagship feature) | Medium | L | Claude |
| 23 | ☐ | Security and operability layer (auth scopes, distributed limits, load test; threat model and secret scanning moved to 12a) | Medium | L | Codex |
| 24 | ☐ | Provider adapter and model comparison, version pinning | Low | M | Codex |
| 25 | ☐ | Three separate decisions: grep fallback (settled by 2 and 3a), MCP/LangGraph rationale, hosted demo | Low | M | Both |
| 26 | ☐ | Layering cleanup: `app/api.py` must not import `scripts/investigate.py` | Low | S | Codex review |

**Recommended order (after the Codex review)**

| Step | Items | Why now |
|---|---|---|
| 1 | **1** (done), **2**, **3a**, **4**, **5a**, **19** | Small changes that stop unsafe or misleading behaviour |
| 2 | **7**, **8** (with a minimal terminal trace event), **9**, **11**, **12a** | Auditable, versioned, validated answers; security boundary |
| 3 | **13**, **16a**, **16b**, **15a** (**16c** in parallel), **17**, **3b** | Measurement you can trust before tuning |
| 4 | **14**, **10**, **5b**, **21** | Retrieval and provider execution, measured against step 3 |
| 5 | **20**, **12b**, **18** (rest), **22**, **23** (rest), **24**, **25**, **26** | Breadth, production posture, architecture decisions |

Item 13's span labels depend on none of items 9, 11 and 12, so they may start earlier if the guard change (3a) should be measured sooner. Either order is defensible.

Item 15a (chunking upgrade) is scheduled after items 9, 13, 16a and 16b, so chunker versions can be selected on development data from two repositories and evaluated fairly. Item 3b follows 16b and 16c so its held-out evidence covers both new repositories.

---

## 2. Item details (Why / Fix / Done when)

### Phase 1: quick safety and honesty fixes

**1. Cap `limit`, query length and prompt size.**
- *Why:* `limit: int = Field(default=5, gt=0)` has no maximum, `query` has no max length, and `build_grounded_prompt` inserts every chunk with no ceiling [SRC: `app/api.py`, `app/investigation/prompt.py`]. An authenticated caller can create outsized cost and latency.
- *Fix:* `limit` `ge=1, le=20`; `query` `max_length=2000`; in the prompt builder enforce a total evidence budget (for example 24,000 characters), drop the lowest-ranked chunks first, and record what was dropped in the audit.
- *Done when:* `limit=1000` and an oversized query return 422; evidence content never exceeds the 24,000-character budget; the total prompt is bounded by the evidence budget plus the query cap plus fixed instruction and metadata overhead (a worst-case test is added with item 11, when the prompt is restructured). Dropped chunk IDs appear in the `prompt_budget` trace entry but not yet in the per-chunk audit snapshot; item 8 closes that.
- **Status:** 2026-10-21; branch `fix/01-input-caps`; changed `app/investigation/limits.py`, `app/api.py`, `scripts/investigate.py`, `app/investigation/prompt.py`, `app/investigation/graph.py`, `tests/unit/test_api.py`, `tests/unit/test_prompt.py`, `tests/unit/test_investigation_graph.py`, `tests/unit/test_investigate_limits.py`, `docs/architecture-review/03-fix-checklist.md`; `ruff check .`: All checks passed!; `pytest tests/unit -q`: 84 passed in 45.42s; `pytest -q`: 87 passed in 44.83s.

**2. Remove the literal grep fallback.**
- *Why:* `POST /investigations` calls `investigate_repository(...)` without `repo_path`, so the default is IncidentWeave's own checkout (`REPO_ROOT`). For any other repository the literal fallback can return IncidentWeave source as evidence [SRC]. In the final evaluation run grep recovered 0 of 8 attempts [ART], so removing it loses nothing measured.
- *Fix:* remove the literal grep fallback from the investigation graph entirely (maintainer decision, 2026-10-22; it recovered 0 of 8 attempts in the final evaluation run [ART] and, as wired, can search IncidentWeave's own tree). The MCP tool code stays until the item 25 decision. Do not store a mutable `source_path` on `Repository`; durable source binding comes with item 9's immutable ingest runs.
- *Done when:* a test with a repository other than IncidentWeave, and a query matching IncidentWeave's source, shows no literal search runs and no IncidentWeave source appears as evidence.
- **Status:** 2026-10-22; branch `fix/02-remove-literal-grep`; changed `app/investigation/graph.py`, `app/investigation/guard.py`, `scripts/investigate.py`, `evaluation/runner.py`, `tests/unit/test_investigation_graph.py`, `tests/unit/test_investigation_mcp_tools.py`, `tests/unit/test_investigation_parsing.py`, `README.md`, `docs/architecture/01-architecture-overview.md`, `docs/architecture/02-high-level-design.md`, `docs/architecture/03-low-level-design.md`, `docs/architecture-review/03-fix-checklist.md`; `ruff check .`: All checks passed!; `pytest -q`: 88 passed in 37.69s.

**3a. Fix the evidence guard (now). 3b. Re-validate the thresholds (after items 16b and 16c).**
- *Why:* (a) `MIN_ACCEPTABLE_RRF_SCORE = 0.016` is below `1/61 = 0.016393`, so any rank-1 vector hit passes; I executed this [EXEC]. (b) The guard takes the best RRF and best vector distance from *different* chunks independently (`max` and `min` over all results), so no single chunk has to satisfy both [SRC; found by Codex]. Result: 4 of 8 unanswerable questions pass the guard [ART].
- *Fix:* decide sufficiency per chunk; the RRF number is for ranking, not a gate. Literal (grep) evidence never counts as sufficient by itself. Example rule: the top chunk's own vector distance ≤ T, or it has a lexical match and distance ≤ T2. T is provisional and must not be tuned on the same 24 questions; 3b re-validates it on the item 16 split. Update the README sentence about "both an RRF threshold and a vector-distance threshold".
- *Done when:* unit tests show the guard accepts only if one chunk passes, including: RRF and vector success on different chunks (accepted when the chunk with the close distance qualifies on its own; refused when no chunk has a distance within the cutoff), a rank-one vector-only hit, an FTS-only hit, and a literal-only result (never sufficient); the README matches the code. The evaluation re-run (false accepts, new threshold) belongs to 3b, because it needs the held-out split and live provider calls. On the current 24 questions the guard's behaviour is unchanged (4 of 8 unanswerable questions still pass).
- **Status (3a):** 2026-10-23; branch fix/03-evidence-guard; changed app/investigation/guard.py, tests/unit/test_investigation_parsing.py, tests/unit/test_investigation_graph.py, README.md, docs/architecture/01-architecture-overview.md, docs/architecture/03-low-level-design.md and docs/architecture-review/03-fix-checklist.md; ruff check .: All checks passed!; pytest -q: 92 passed in 56.57s. Threshold unchanged at 0.5 until 3b.

**4. Make abstention consistent.**
- *Why:* a response with `Diagnosis: INSUFFICIENT_EVIDENCE` and `Confidence: high` is stored as `high` [EXEC]. For literal-grep evidence, calibration retains `high` with the note "retrieval scores clear both calibration margins", which is false because there are no scores [EXEC].
- *Fix:* after parsing, if the diagnosis equals `INSUFFICIENT_EVIDENCE` then confidence = `low`. Do not erase citations that explain the abstention; distinguish "supporting evidence" from "positive diagnosis evidence". For literal-only evidence cap confidence at `medium` with an honest note (moot now that item 2 removes the literal path). The generated-abstention rule is completed in item 11.
- *Done when:* parser and calibration tests cover both cases.
- **Status:** 2026-10-23; branch fix/04-consistent-abstention; changed app/investigation/parsing.py, tests/unit/test_investigation_parsing.py and the docs in the diff; ruff check .: All checks passed!; pytest -q: 97 passed in 54.50s. Citations are kept; the supporting-versus-positive evidence split comes with item 11.

**5a. Hardening now. 5b. Hardening later.**
- *Why:* the Gemini key is in the URL query string [SRC] (it can leak into logs); the grep subprocess call has no deadline [SRC; Codex]; the Dockerfile runs as root and Compose passes neither `GEMINI_API_KEY` nor `API_PROTECTION_SECRET`, so the container cannot generate or authenticate [SRC].
- *Fix:* **5a (now):** send the key in the `x-goog-api-key` header (generation and embedding); ~~wrap the MCP call in `asyncio.wait_for(..., 10)~~ (moot: no MCP call exists in the graph since item 2). **5b (later):** add `USER` (non-root) to the Dockerfile; pass env via `env_file`; add a healthcheck on `/health`.
- *Done when:* each is covered by a test or a `docker compose up` smoke check.
- **Status:** 2026-10-23; branch fix/05-api-key-header; changed app/investigation/generation.py, scripts/embed_chunks.py, tests/unit/test_gemini_api_key_header.py and docs/architecture-review/03-fix-checklist.md; ruff check .: All checks passed!; pytest -q: 99 passed in 38.81s.

**6. Make docs match code.**
- *Why:* the README says retrieval must clear both thresholds (not true, item 3); "one Audit row per query" (not true for refusals); the raw model response is persisted (not true: only the parsed diagnosis is stored); the test count is stated as both 41 and 53, and `main` contains both phases [SRC].
- *Fix:* not a standalone phase. Every behaviour change fixes its own README sentence. Test counts come only from an executed command.
- *Done when:* every README claim maps to a code location or a test.

### Phase 2: audit and provenance

**7. Persist every outcome.**
- *Why:* when the guard fails, `investigate_repository` returns before persistence, so there is no row, `investigation_id` is `None`, and refusals cannot be reviewed [SRC].
- *Fix:* add an `outcome` column (`answered`, `refused_guard`, `abstained_model`, `error`) via Alembic migration `0002`. Store a row for refusals with the evidence check and a retrieval summary. The API returns an ID for refusals. Also persist provider, validation and MCP errors (sanitized error class, terminal status).
- *Done when:* a refused POST returns an ID and `GET /investigations/{id}` returns the refusal reason.
- **Status:** 2026-10-24; branch fix/07-persist-every-outcome; changed migrations/versions/20261024_0002_investigation_outcome.py, app/db/models/investigation.py, app/investigation/persistence.py, scripts/investigate.py, app/api.py, tests/unit/test_investigation_persistence.py, tests/unit/test_investigate_limits.py, tests/unit/test_api.py, tests/unit/test_db_models.py, README.md, docs/architecture/01-architecture-overview.md, docs/architecture/02-high-level-design.md, docs/architecture/03-low-level-design.md and docs/architecture-review/03-fix-checklist.md; ruff check .: All checks passed!; pytest -q: 107 passed in 55.23s.

**8. Store a replayable audit.**
- *Why:* only the parsed diagnosis is stored. Missing: raw model text, raw confidence, prompt, model and embedding versions, generation settings, thresholds [SRC].
- *Fix:* one versioned per-chunk record (chunk ID, content hash, rank, scores, kept or dropped) instead of parallel score arrays. Store the raw response, raw confidence, prompt template version, generation parameters, thresholds, embedding model and a source reference. A prompt hash alone is not replayable. The prompt contains source code, so restrict who can read stored prompts. Include a minimal terminal trace event (correlation ID, outcome, model, generation latency, error class); per-stage timings are deferred to item 18.
- *Done when:* an old investigation can be explained from its stored data alone.
- **Status:** 2026-10-27; branch `fix/08-replayable-audit`; changed `migrations/versions/20261026_0004_replayable_audit.py`, `app/db/models/audit.py`, `app/investigation/graph.py`, `app/investigation/persistence.py`, `app/investigation/prompt.py`, `app/investigation/replay.py`, `scripts/investigate.py`, `tests/unit/test_api.py`, `tests/unit/test_investigate_limits.py`, `tests/unit/test_investigation_graph.py`, `tests/unit/test_investigation_persistence.py`, `tests/unit/test_investigation_replay.py`, `README.md`, `docs/architecture/01-architecture-overview.md`, `docs/architecture/02-high-level-design.md`, `docs/architecture/03-low-level-design.md`, `docs/architecture/04-threat-model.md` and `docs/architecture-review/03-fix-checklist.md`; `ruff check .`: All checks passed!; `pytest -q`: 122 passed in 38.84s.

**9. Source versioning and upsert ingestion.**
- *Why:* `ingest_repository` deletes all chunks and reinserts them, so chunk IDs change and embeddings are lost. `Audit.retrieved_chunk_ids` has no foreign key and no content snapshot. No commit SHA is stored [SRC].
- *Fix:* an `ingest_runs` table (`repository_id`, `source_path`, `git_remote`, `commit_sha`, `dirty`, `started_at`, `chunker_version`, `embedding_model`); `chunks.ingest_run_id` and `chunks.content_hash`; upsert by (repository, file, range, content hash) so unchanged chunks keep their ID and embedding; audit rows reference the `ingest_run_id`. Make ingest runs immutable; an upsert alone cannot preserve historical evidence.
- *Done when:* tests verify unchanged IDs/embeddings, changed and removed chunk behavior, and an audit row linked to the latest IngestRun.
- **Status:** 2026-10-24; branch `fix/09-ingest-runs-upsert`; changed `migrations/versions/20261025_0003_ingest_runs.py`, `app/db/models/ingest_run.py`, `app/db/models/chunk.py`, `app/db/models/audit.py`, `app/db/models/__init__.py`, `scripts/ingest_repo.py`, `app/investigation/persistence.py`, `scripts/investigate.py`, `evaluation/runner.py`, `tests/integration/test_ingest_repo_integration.py`, `tests/integration/test_database.py`, `tests/integration/test_database_models_integration.py`, `tests/unit/test_db_models.py`, `tests/unit/test_ingest_repo.py`, `tests/unit/test_investigation_persistence.py`, `tests/unit/test_investigate_limits.py`, `README.md`, `docs/architecture/01-architecture-overview.md`, `docs/architecture/02-high-level-design.md`, `docs/architecture/03-low-level-design.md` and `docs/architecture-review/03-fix-checklist.md`; `ruff check .`: All checks passed!; `pytest -q`: 121 passed in 47.58s.

### Phase 3: answer contract

**10. Async, batched provider client.**
- *Why:* blocking provider calls and per-chunk embedding requests constrained responsiveness and throughput. A Gemini batch embedding endpoint is available.
- *Fix:* use an `httpx.AsyncClient`; batch embeddings with a bounded-concurrency semaphore; retry selected HTTP statuses and timeout/network failures with jitter; enforce provider and end-to-end deadlines. Add a live benchmark script that reads existing chunk contents without writing to the database.
- *Done when:* a test with a slow fake provider shows other requests stay responsive, batching and concurrency are tested, and the benchmark script is added. No throughput promise is made; measured numbers remain pending the maintainer's live run.
- **Status:** 2026-10-24; branch `fix/10-async-provider-client`; changed `app/api.py`, `app/investigation/generation.py`, `app/investigation/graph.py`, `app/providers/__init__.py`, `app/providers/gemini.py`, `evaluation/runner.py`, `pyproject.toml`, `scripts/benchmark_embeddings.py`, `scripts/embed_chunks.py`, `scripts/investigate.py`, `scripts/search_repo.py`, `tests/integration/test_ingest_repo_integration.py`, `tests/unit/test_api.py`, `tests/unit/test_embed_chunks_async.py`, `tests/unit/test_evaluation.py`, `tests/unit/test_gemini_api_key_header.py`, `tests/unit/test_gemini_provider.py`, `tests/unit/test_investigate_limits.py`, `tests/unit/test_investigation_graph.py`, `README.md`, `docs/architecture/01-architecture-overview.md`, `docs/architecture/02-high-level-design.md`, `docs/architecture/03-low-level-design.md`, and `docs/architecture-review/03-fix-checklist.md`; `ruff check .`: All checks passed!; `pytest -q`: 141 passed in 73.61s; benchmark recorded in docs/notes/03-embedding-benchmark.md (one run; indicative only).

**11. Structured output and server-side citation validation.**
- *Why:* citations are string mentions. A response calling `app/config.py` "unrelated" still cites it, and a nonexistent line range still cites every chunk from that file [EXEC]. In the final run only 9 of 22 and 9 of 31 cited chunks matched a labeled-relevant substring [ART].
- *Fix:* request the provider's JSON-schema output: `{outcome, diagnosis, self_rating, uncertainty_note, claims:[{text, evidence:[{chunk_id, quote}]}]}`. Invalid JSON or incorrectly typed fields raise `ModelOutputError`. The server checks that each `chunk_id` was retrieved and each quote is at least 10 characters and a case-sensitive substring of that chunk after whitespace normalization. Invalid evidence and claims without valid evidence are dropped; an answered response without a surviving claim becomes `INSUFFICIENT_EVIDENCE`. Valid claims remain available for a model-declared insufficient-evidence outcome, whose effective rating is low. `cited_chunk_ids` is derived from validated claims. A valid quote proves the reference exists, not that the claim follows from it: report reference-validity separately from faithfulness (item 17). The JSON-schema request follows the documented Gemini REST format; this change was not tested against the live API. This item also completes the generated-abstention rule from item 4.
- *Done when:* tests cover hallucinated chunk IDs, quotes absent from a chunk and under 10 characters, a valid quote including whitespace normalization, answered output with no valid claim, model-declared abstention retaining valid claims and a low effective rating, and invalid JSON/type errors. The evaluation run summary reports citation validity as valid/submitted references for answered runs, or `None` when none were submitted.
- **Status:** 2026-10-24; branch `fix/11-structured-output`; changed `README.md`, `app/api.py`, `app/investigation/generation.py`, `app/investigation/graph.py`, `app/investigation/parsing.py`, `app/investigation/persistence.py`, `app/investigation/prompt.py`, `docs/architecture/01-architecture-overview.md`, `docs/architecture/02-high-level-design.md`, `docs/architecture/03-low-level-design.md`, `evaluation/metrics.py`, `evaluation/runner.py`, `scripts/investigate.py`, `tests/integration/test_ingest_repo_integration.py`, `tests/unit/test_api.py`, `tests/unit/test_evaluation.py`, `tests/unit/test_gemini_api_key_header.py`, `tests/unit/test_investigation_graph.py`, `tests/unit/test_investigation_parsing.py`, `tests/unit/test_investigation_persistence.py`, `tests/unit/test_prompt.py`; `ruff check .`: All checks passed!; `pytest -q`: 126 passed in 44.62s.

**12a. Injection and secret controls (early). 12b. Wider injection testing (later).**
- *Why:* repository text is concatenated into the prompt with no trust boundary, and code sent to an external model may contain secrets [SRC; Codex].
- *Fix:* wrap each chunk in explicit tags (`<evidence id=… path=…>…</evidence>`) and instruct the model that evidence is untrusted data. Scan for secrets at ingestion (regex for keys and tokens) and redact or skip with a warning. Document the data policy.
- *Scope:* **12a** = evidence tags, secret skip before chunks enter storage and can be sent to a provider, and a short threat-model note. **12b** = wider injection testing.
- *Done when:* prompt structure and secret skipping are tested; behavioral injection testing is checklist item 12b.
- **Status:** 2026-10-24; branch `fix/12a-injection-secret-controls`; changed `app/investigation/prompt.py`, `app/secret_scan.py`, `scripts/ingest_repo.py`, `tests/unit/test_prompt.py`, `tests/unit/test_secret_scan.py`, `tests/unit/test_ingest_repo.py`, `README.md`, `docs/architecture/01-architecture-overview.md`, `docs/architecture/02-high-level-design.md`, `docs/architecture/03-low-level-design.md`, `docs/architecture/04-threat-model.md`, `docs/architecture/README.md` and `docs/architecture-review/03-fix-checklist.md`; `ruff check .`: All checks passed!; `pytest -q`: 118 passed in 83.05s.

### Phase 4: measurement foundation, then retrieval gains

**13. Evaluation foundation (before tuning anything).** Delivered as items 13a and 13b. Why and design are in Part B. Minimum set:
- Chunk-agnostic labels: the evidence is a file plus line range, and a retrieved chunk is a hit if it overlaps or contains it.
- A retrieval-only mode (no LLM call) that uses cached query and chunk embeddings committed as a small fixture, so CI can run it offline.
- Generation settings recorded and `temperature=0`.
- Confidence intervals and a paired per-question comparison (exact sign or McNemar test) in every report; overlapping intervals are not a significance test for paired data.
- Span labels depend on none of items 9, 11 and 12 and may start earlier to measure the guard change (3a).
- *Done when:* a CI job runs the retrieval evaluation offline and fails if Hit@5 or MRR drops beyond a stored tolerance.
- **Status:** 2026-10-24; branch `fix/13a-evaluation-foundation`; changed `evaluation/stats.py`, `evaluation/span_labels.py`, `evaluation/golden.py`, `evaluation/golden_set.json`, `evaluation/metrics.py`, `evaluation/build_fixture.py`, `evaluation/fixtures/retrieval_fixture.json.gz`, `evaluation/retrieval_eval.py`, `evaluation/results/offline-baseline.json`, `scripts/run_retrieval_eval.py`, `tests/unit/test_evaluation.py`, `tests/unit/test_evaluation_foundation.py`, `tests/integration/test_offline_retrieval.py`, `README.md`, `docs/notes/README.md`, `docs/notes/04-offline-retrieval-evaluation.md`, and `docs/architecture-review/03-fix-checklist.md`; `ruff check .`: All checks passed!; `pytest -m "not integration" -q`: 148 passed, 5 deselected in 109.49s; `pytest tests/integration/test_offline_retrieval.py -q`: 1 passed in 125.64s; offline retrieval baseline: Hit@1/3/5 = 8/16, 11/16, 11/16 and MRR 0.573 for both substring labels and spans.

**Status (13b):** 2026-10-25; branch `fix/13b-retrieval-gate`; changed `.github/workflows/ci.yml`, `README.md`, `app/investigation/generation.py`, `app/investigation/graph.py`, `evaluation/gate.json`, `evaluation/gate.py`, `evaluation/runner.py`, `scripts/check_retrieval_gate.py`, `scripts/investigate.py`, `tests/unit/test_evaluation.py`, `tests/unit/test_gemini_api_key_header.py`, `tests/unit/test_investigate_limits.py`, `tests/unit/test_investigation_graph.py`, `tests/unit/test_retrieval_gate.py`, `docs/notes/04-offline-retrieval-evaluation.md`, and `docs/architecture-review/03-fix-checklist.md`; `ruff check .`: All checks passed!; `pytest -q`: 163 passed in 143.96s; offline gate: all four checks passed, with Hit@5 11 and MRR 0.5729166666666666 for both label types.

**14. Cheap retrieval ablations (each is one row in an ablation table).**
- *Why:* full-text returned nothing for 14 of 16 answerable questions [ART], consistent with and likely amplified by `websearch_to_tsquery` ANDing all words [PostgreSQL docs] (the SQL has not been traced to rule out stemming, stop words or query wording; sub-experiment (c) includes a one-query check); no `task_type` is sent to the embedding API although `RETRIEVAL_DOCUMENT` and `CODE_RETRIEVAL_QUERY` exist [Google docs]; 44% of top-5 results come from `tests/` [EXEC on the committed `baseline.json`].
- *Fix, as three separate experiments:*
  - (a) Add `task_type` (documents `RETRIEVAL_DOCUMENT`, queries `CODE_RETRIEVAL_QUERY`) and re-embed.
  - (b) Tag tests `document_type="test"`, then compare keep / downweight / exclude.
  - (c) Build an OR query from extracted identifiers and keywords, split `snake_case` and `camelCase` into extra searchable text, and add a generated `tsvector` column with a GIN index.
- *Done when:* a committed ablation table with confidence intervals; keep only changes that help without hurting. One change per run, with re-embedding versioned. Report test-file recall and precision, not only aggregate Hit@5. HNSW and GIN indexes are scale work, not a quality ablation at 70 chunks.

**15a. Chunking upgrade (staged, after 16a and 16b).** See Part A. First compare 60/10, 100/20, function-aware, and function-aware with parent expansion under one fixed test-file policy on development data from IncidentWeave and repository 2; function-aware is a strong candidate, not a proven winner. Freeze the choice before evaluating either repository’s held-out split. *Done when:* the comparison runs on the item 13 metrics and the winner is chosen by a rule fixed in advance.

### Phase 5: scale and breadth

**16a. Multi-repo evaluation harness.**
- *Fix:* generalise the evaluation harness with a versioned manifest, per-repository question/split/fixture/baseline selection, per-repository and pooled reporting, fixed development-only smoke selection, and one fail-closed offline gate per repository. The manifest records pinned source, content hashes, versions and fixture-size limits. This item contains code and synthetic/unit-test fixtures only.
- *Done when:* unit and integration tests show that the harness rejects missing or mismatched manifest, question, fixture and baseline inputs; reports each selected repository and the pooled total; keeps held-out questions out of tuning paths; and fails the overall gate when any selected repository fails or is missing.
- **Status:** 2026-10-25; branch `fix/16a-multi-repo-harness`; changed `.github/workflows/ci.yml`, `README.md`, `evaluation/build_fixture.py`, `evaluation/chunk_experiments.py`, `evaluation/compare_chunking_runs.py`, `evaluation/gate.py`, `evaluation/manifest.json`, `evaluation/manifest.py`, `evaluation/retrieval_eval.py`, `evaluation/results/incidentweave-smoke-baseline.json`, `evaluation/runner.py`, `evaluation/smoke-gate.json`, `evaluation/splits.py`, `scripts/check_retrieval_gate.py`, `scripts/run_eval.py`, `scripts/run_retrieval_eval.py`, `tests/integration/test_offline_retrieval.py`, `tests/unit/test_evaluation.py`, `tests/unit/test_manifest.py`, `tests/unit/test_multi_repo_gate.py`, `tests/unit/test_retrieval_gate.py`, `tests/unit/test_splits.py`, `docs/notes/04-offline-retrieval-evaluation.md`, `docs/notes/05-multi-repo-evaluation.md`, `docs/notes/README.md`, and `docs/architecture-review/03-fix-checklist.md`; `ruff check .`: All checks passed!; `pytest -q`: 190 passed in 73.81s; smoke and full offline gates passed with observed metrics equal to their baselines.

**16b. First new-repository evaluation data: `iamswayam/batch-processing-service`.**
- *Fix:* add the approved Python repository under `06-multi-repo-evaluation-plan.md` with its reviewed 24-question set, explicit development/held-out/smoke assignments, pinned snapshot, offline fixture and reviewed baseline.
- *Done when:* the approved manifest entry, questions, label/span and absence review, fixture and baseline pass 16a’s validation and its smoke gate runs without provider calls.

**16c. Second new-repository evaluation data: `iamswayam/lifeos`.**
- *Fix:* add the second approved Python repository with the same reviewed inputs as 16b. Run it in parallel with 15a if ready, but do not use its results to revise the 15a design.
- *Done when:* both new-repository entries pass 16a’s validation and gates; their frozen held-out results can be reported as a two-repository external-replication result with stated denominators and limitations.

**17. LLM judge and a larger abstention set.**
- *Fix:* judge prompts for faithfulness (is each claim supported by its quote?), correctness against a reference answer, and completeness against a required-facts list. Prefer a different model from the generator. Validate the judge on at least 30 human-labeled answers and report agreement (30 labels is a pilot, not proof of reliability; temperature 0 does not guarantee determinism). Keep the keyword screen as a cheap smoke test. Grow unanswerable questions to at least 20 (far, near-miss, false-premise).
- *Done when:* the report shows judge agreement with humans.

**18. Tracing, cost, latency.**
- *Fix:* the minimal terminal trace event is built inside items 7 and 8. Then OpenTelemetry spans per graph node, tokens and estimated cost per request, p50/p95 per stage; self-hosted Langfuse or Grafana.
- *Done when:* one request shows every stage with timings and cost.

**19. Model self-rating.**
- *Why:* in the committed baseline the model labeled 15 of 16 answers `high`, and retrieval calibration moved 13 to `medium` [EXEC]. The label has not been checked against correctness.
- *Fix:* rename the API field to `model_self_rating` and include an evidence-based note. A real reliability table (bucket → accuracy) needs at least 100 labeled answers and comes later.
- *Done when:* API output uses `model_self_rating` and a note that it is not measured probability; CLI output says model self-rating; no API `confidence` or `raw_confidence` fields remain.
- **Status:** 2026-10-24; branch fix/19-model-self-rating; changed app/api.py, scripts/investigate.py, tests/unit/test_api.py, README.md, docs/architecture/01-architecture-overview.md, docs/architecture/03-low-level-design.md and docs/architecture-review/03-fix-checklist.md; ruff check .: All checks passed!; pytest -q: 100 passed in 22.44s.

**20. Multi-artifact ingestion.**
- *Fix:* Markdown by heading; YAML/TOML/JSON by top-level key; Dockerfile and CI files whole; logs by time window or request ID with stack traces kept intact. Fill `document_type`, `service`, `environment`, `timestamp`, `incident_id` (the columns already exist but are unused) and filter on them.
- *Done when:* questions over a README, a runbook and a config are answered with valid citations.

**21. Reranker experiment.** Re-rank the top 20 into the top 5. Keep it only if held-out Hit@5 or nDCG improves beyond the confidence interval at acceptable latency and cost.

**22. Incident-replay evaluation and hypothesis loop.**
- *Why:* this is the biggest gap versus the AI-SRE product category [market research in my report].
- *Fix:* a small containerized sample service with injected faults; capture its logs, alerts and deploy diff; 10–20 labeled incidents with root cause and evidence; the system proposes ranked hypotheses, tests each with read-only queries, and may end "inconclusive"; score root-cause accuracy, evidence validity, time and cost.
- *Done when:* a report across all incidents exists.

**23. Security and operability.**
- *Fix:* the threat model and secret scanning are done early in 12a; the rest stays here: per-user API keys (hashed) with scopes; distributed rate limiting; a per-request cost budget; structured logs with request IDs; a load test (20 concurrent requests); a threat-model document (prompt injection, data exfiltration, secrets, tenant isolation); CI type checking, `pip-audit` and secret scanning.
- *Done when:* the threat model and load-test report are committed.

**24. Provider adapter and model comparison.** Add an `LLMClient` interface, pin model versions in config and audit, and run the harness on `gemini-3.5-flash-lite`, `gemini-3.8-flash` and one other provider.

**25. MCP, LangGraph, deployment.** Either remove the per-call stdio MCP grep (use in-process exact search) or expose IncidentWeave as a read-only MCP server. Keep LangGraph only if the hypothesis loop genuinely needs branching or checkpoints. Deploy a hosted demo. These are three separate decisions: (1) the grep fallback, settled by items 2 and 3a; (2) the MCP and LangGraph rationale; (3) the hosted deployment.

**26. Layering cleanup.** `app/api.py` imports `scripts/investigate.py`; move the shared logic into `app/` so the API does not depend on a script. *Done when:* no module under `app/` imports from `scripts/`. Low priority.

---

## 3. Part A: Can the chunking strategy be better? **Yes.**

**What chunking is (plain language).** The system cannot give the whole repository to the model, so it cuts files into pieces ("chunks"), turns each piece into a vector of numbers (an "embedding") that captures its meaning, and later finds the pieces whose vectors are closest to the question's vector. If a chunk is too big, its vector blends many topics and the prompt gets expensive. If it is too small or cut in the wrong place, the model sees a fragment, such as half a function without its start.

**What the project does now** [SRC: `scripts/ingest_repo.py`]: every Python file is cut into fixed windows of 60 lines with 10 lines of overlap. The cut ignores code structure. `function_name`, `class_name` and `symbol` are left empty.

**What the data says** (my analysis [EXEC] on the pinned snapshot used by the evaluation; script in the appendix):

| Measure | Result |
|---|---|
| Chunks at 60/10 and 100/20 | 70 and 52. These match the repo's own report, so my reproduction is faithful. |
| Median file length | 50.5 lines |
| Non-test function length | median 21.5, 90th percentile 60, max 177 lines |
| Functions/methods cut across chunk boundaries at 60/10 | **16 of 48 (33%)** non-test |
| Same at 100/20 | **5 of 48 (10%)** non-test |
| Test files in the top 5 results | 44% (35 of 80), 15 of 16 answerable questions [EXEC on `baseline.json`] |

**What this means.**
- The 100/20 gain (Hit@5 11/16 → 15/16 [ART]) has a concrete explanation: far fewer functions are cut in half. This is stronger evidence than the sample size alone suggests.
- It also says the real problem is **cutting without regard to structure**, so bigger windows are a blunt fix. A function-aware chunker is a strong candidate to help further, not a proven winner; item 15 tests it.
- I have not measured the retrieval effect of function-aware chunking. That needs embeddings and a model, which I could not run [INF].
- Test files add noise to the top results regardless of chunk size.

**Options compared**

| Strategy | How it works | Good | Bad | Verdict |
|---|---|---|---|---|
| Fixed windows (current) | N lines, overlap | Simple | Cuts functions; ignores structure | Baseline |
| Bigger windows (100/20) | Fewer, larger pieces | Fewer cut functions; fewer chunks | +40% tokens; blends topics; near whole-file on small files | Interim only |
| **Function-aware (`ast`)** | One chunk per function/class; split very long functions | Matches how people ask questions; fills the empty metadata columns; stdlib only | Needs fallbacks (syntax errors, non-Python) | **Recommended** |
| **Function-aware + header in embedding text** | Prepend path, class, function name and docstring to the text that is embedded | Questions that name a file or function match better | Slightly more code | **Recommended with the above** |
| **Parent-child ("retrieve small, answer big")** | Search small chunks, expand to the enclosing class or neighbours before prompting | Precise search, full context for the answer | Needs a token budget | **Recommended** |
| LLM or semantic chunking | A model decides the cuts | Flexible | Slow, costly, non-deterministic | Not now |
| Non-code (Markdown, config, logs) | Headings, keys, time windows/request IDs with stack traces whole | Needed for real incidents | New parsers | Item 20 |

**Recommended design**
1. Python: one chunk per top-level function or class; methods separately if a class is longer than about 80 lines; merge tiny neighbours (imports, constants) into a "module header" chunk; split functions longer than about 100 lines at blank-line boundaries with a 10-line overlap. Fill `symbol`, `function_name`, `class_name` and the line range.
2. Embed `File: … / Symbol: … / Docstring: … / <code>` but keep `content` raw for display and citations.
3. Tag tests with `document_type="test"` and decide the policy (keep, downweight, exclude) by ablation.
4. Record `chunker_version` in `ingest_runs` (item 9) so audits stay reproducible.
5. Decide by experiment: compare 60/10, 100/20, function-aware and function-aware with parent expansion under one fixed test-file policy first, scored with the item 13 metrics, with the decision rule written down before running. A quick throwaway prototype of mine produced 88 chunks with median 27 lines (max 177, a very long function). It is not in the appendix; treat the numbers as indicative.

**Caveats.** The corpus is small (40 files; the top 5 of 70 chunks is 7% of everything), so Hit@5 is easy here and will drop on real repositories. Do not treat conclusions as general.

---

## 4. Part B: Can the evaluation stage be better? **Yes.**

**What evaluation means for a RAG system (plain language).** There are two separate things to test. **Retrieval:** did the search put the right evidence in front of the model? **Generation:** given that evidence, was the answer correct, complete and supported? Test them separately, otherwise you cannot tell which part broke. Add two more: **citations** (do they point at real support?) and **abstention** (does it refuse when it should?).

**Glossary**

| Term | Meaning |
|---|---|
| Hit@k / Recall@k | Share of questions where the right evidence is in the top k results |
| MRR | Average of 1/rank of the first right result; rewards putting it first |
| nDCG@k | Like MRR but handles several relevant results and graded relevance |
| Context precision | Share of the top k results that are actually relevant (catches noise such as test files) |
| Faithfulness | Is every claim in the answer supported by the cited evidence? |
| Citation precision/recall | Of the citations given, how many truly support the claim; of the needed support, how much was cited |
| Abstention precision/recall | When it refuses, was it right to; when it should refuse, did it |
| Confidence interval | The range the true value plausibly lies in given the sample size |
| Ablation | Change one thing at a time and measure |
| Held-out set | Questions never used to tune anything |

**What is good already** [ART/SRC]: pinned corpus, run metadata (hashes, dirty flag), a validator that stops paraphrased questions leaking source identifiers, near/far unanswerable categories, and a distance-cutoff sweep.

**Problems, ranked**
1. **The sample is too small to settle anything.** 16 answerable questions. Wilson 95% intervals [EXEC]: Hit@5 60/10 is 11/16 [44%, 86%]; 100/20 is 15/16 [72%, 99%]. They overlap. Guard false accepts are 4/8 [22%, 78%]. Answer screen correct is 12/16 [51%, 90%]. A paired exact sign test on the 4-wins-0-losses Hit@5 gain gives two-sided p = 0.125: suggestive, not decisive. Overlapping intervals are not themselves a significance test for paired data.
2. **Self-referential, author-drafted, unreviewed.** The system is judged on its own source, the questions were drafted from the indexed content, and the status is "pending maintainer review" [ART].
3. **Labels depend on chunk text** (file + substring). I checked whether this favors big chunks: each label matches exactly one chunk at every size (two at 60/10 for one question) [EXEC]. So this bias is small here. The real limits are that substring labels cannot say "this answer needs two pieces of evidence" and do not penalize noisy results.
4. **Answer scoring is keyword groups.** It can accept a wrong answer or reject a correct paraphrase. `direct-05` shows an answer that omitted the required value yet ranked better [ART].
5. **Non-determinism and weak replication.** Generation uses "provider default" settings. Retrieval is deterministic, so a second pass adds no retrieval information [ART/INF].
6. **Not usable as a regression gate.** The harness calls a live provider; CI has no offline retrieval check [SRC].
7. **Confidence is never checked against correctness** [SRC: no such metric in `evaluation/metrics.py`].
8. **Process weight.** Docs are about 4,450 lines and the experiment comparator is 761 lines for a two-arm comparison [EXEC]. Simplify once the basics work.

**Recommended design: three layers**

| Layer | Runs | What it measures | Cost |
|---|---|---|---|
| 1. Retrieval | Every pull request (offline, cached embeddings) | Hit@k, MRR, nDCG@10, context precision@5, by question type and file type | Free |
| 2. Generation | Nightly or manual | Faithfulness, correctness, completeness (LLM judge validated on human labels), claim-level citation precision/recall, at `temperature=0`, at least 3 runs, with intervals | Tokens |
| 3. Abstention and safety | Nightly or manual | At least 20 unanswerable (far, near-miss, false-premise), injection and secret fixtures; refusal precision/recall | Tokens |
| 4. Incident replay (later) | Manual | Root-cause accuracy over labeled incidents (item 22) | Tokens |

**Dataset:** start with 30, grow to 60 or more, across two or more sources, split into dev and a frozen test set; types: direct, paraphrased, multi-file, config, error-message/stack-trace, unanswerable; written independently and human-reviewed; version-controlled with a changelog.

**Experiment discipline:** write the hypothesis and decision rule first; change one thing at a time; report the effect with an interval and a paired test; never tune thresholds on the frozen test set.

**Scorecard to report each run**

| Metric | Value | 95% interval | Change vs baseline |
|---|---|---|---|
| Hit@5, MRR, nDCG@10, context precision@5 | | | |
| Faithfulness, correctness, completeness | | | |
| Citation precision / recall | | | |
| Abstention precision / recall | | | |
| Median and p95 latency, tokens, cost per correct answer | | | |

**A practical learning path (tied to the checklist)**
1. Implement nDCG and context precision in `metrics.py` with unit tests (item 13).
2. Write the function-aware chunker and print how the chunk boundaries change for two files (item 15).
3. Run the ablation and read the table (item 14).
4. Write the judge prompt, label 30 answers yourself, compare (item 17).
5. Learn just enough statistics to read an interval and a paired test.

---

## 5. Corrections to my own earlier audit

- I said label matching "favors larger chunks". The label-reachability check shows the count effect is small here (Part B problem 3). The better explanation for 100/20's gain is fewer cut functions (33% → 10%).
- I said AST-aware chunking was a "later" item. Both audits said later. The function-splitting data justifies moving it earlier (item 15), but only after the evaluation foundation (item 13) so the gain can be measured.

- After the Codex review (commit `59f38fd`): the original header wrongly described `main` @ `e98da82` as the reference with 51 tests. The reviewed commit contains the evaluation harness and has 64 `test_` functions and 70 executed tests.
- Item 1's Done-when said the *prompt* never exceeds the budget, but the implementation caps the *evidence content* (24,000 characters); the query is capped separately. Reworded.
- Item 3 is Critical, not High: the product claims grounded, evidence-checked answers and the guard lets 4 of 8 unanswerable questions through.
- The claim that full-text was empty because `websearch_to_tsquery` ANDs terms is now stated as "consistent with, and likely amplified by"; the query was not traced.
- Overlapping Wilson intervals are not a significance test for paired data; the paired exact sign test (p = 0.125) is the right comparison.
- Items 5, 12 and 15 are split or staged because they were too heavy for one developer in one step; item 6 is no longer a standalone phase; item 26 is new.

---

## 6. Review status

The independent Codex review of the original checklist is in `04-fix-checklist-review-codex.md`. Its accepted changes are folded into this file. Still unverified: live Gemini calls (embeddings, generation, batch, cost, retention); the saved 60/10 vs 100/20 experiment was not re-run live; golden labels still say "pending maintainer review"; no query-plan analysis of the empty full-text results; no load, injection or deployed-container test.

---

## Appendix: analysis script (stdlib only)

Run it on the pinned evaluation snapshot, **outside** the snapshot directory, with `python3 -I`. It reads files with `ast.parse` and never executes repository code.

```python
"""Stdlib-only chunking/evaluation analysis for IncidentWeave's pinned snapshot.

Usage (from any directory, NOT inside the untrusted snapshot):
    git -C <repo> archive 62d0e58593bb22d187ec7930274b0457afd3be74 | tar -x -C /tmp/snap
    rm -rf /tmp/snap/tests/fixtures
    git -C <repo> show origin/main:evaluation/golden_set.json > /tmp/golden.json
    python3 -I chunk_eval_analysis.py /tmp/snap /tmp/golden.json
"""
import ast
import json
import statistics
import sys
from math import sqrt
from pathlib import Path

ROOT, GOLDEN = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text())
IGNORE = {".git", ".kilo", ".pytest_cache", ".ruff_cache", ".venv", "__pycache__", "migrations"}
STRATEGIES = {"60/10": (60, 10), "100/20": (100, 20)}


def load_files():
    out = {}
    for p in sorted(ROOT.rglob("*.py")):
        rel = p.relative_to(ROOT)
        if not any(part in IGNORE for part in rel.parts):
            out[rel.as_posix()] = p.read_text(encoding="utf-8", errors="replace")
    return out


def windows(n, size, overlap):  # mirrors scripts/ingest_repo.py::chunk_lines
    step, prev = size - overlap, 0
    for s in range(0, n, step):
        e = min(s + size, n)
        if e > prev:
            yield s, e  # half-open, 0-based
            prev = e


files = load_files()
print(f"files={len(files)}  median file length={statistics.median(len(s.splitlines()) for s in files.values())} lines")

# 1) chunk counts (should equal the repo's reported 70 and 52) and function splitting
funcs = []
for name, src in files.items():
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append((name, node.lineno, node.end_lineno))
for label, (size, ov) in STRATEGIES.items():
    n_chunks = sum(len(list(windows(len(s.splitlines()), size, ov))) for s in files.values())
    for scope, keep in (("non-test", lambda n: not n.startswith("tests/")), ("all", lambda n: True)):
        total = split = 0
        for name, s, e in funcs:
            if not keep(name):
                continue
            ws = list(windows(len(files[name].splitlines()), size, ov))
            total += 1
            split += not any(a + 1 <= s and e <= b for a, b in ws)
        print(f"[{label}] chunks={n_chunks}  {scope} functions/methods={total} split across chunks={split} ({split/total:.0%})")
lens = sorted(e - s + 1 for n, s, e in funcs if not n.startswith("tests/"))
print(f"non-test function length: median={statistics.median(lens)}  p90={lens[int(len(lens)*.9)]}  max={lens[-1]}")

# 2) label reachability: how many chunks match each question's file+substring label
chunks = {}
for label, (size, ov) in STRATEGIES.items():
    chunks[label] = [(n, "\n".join(s.splitlines()[a:b])) for n, s in files.items()
                     for a, b in windows(len(s.splitlines()), size, ov)]
chunks["whole-file"] = list(files.items())
print("\nlabeled chunks per answerable question (60/10, 100/20, whole-file):")
for q in GOLDEN["questions"]:
    if q["category"] in ("direct", "paraphrased"):
        row = [sum(1 for n, c in chunks[k] if any(l["file_path"] == n and l["substring"].casefold() in c.casefold()
                                                   for l in q["relevant"])) for k in ("60/10", "100/20", "whole-file")]
        print(f"  {q['id']:15s} {row}")


# 3) uncertainty on the headline numbers
def wilson(k, n, z=1.96):
    p, d = k / n, 1 + z * z / n
    c, m = p + z * z / (2 * n), z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - m) / d, (c + m) / d


print("\nWilson 95% intervals:")
for name, k, n in [("Hit@5 60/10", 11, 16), ("Hit@5 100/20", 15, 16),
                   ("guard false accepts on unanswerable", 4, 8), ("answer screen correct", 12, 16)]:
    lo, hi = wilson(k, n)
    print(f"  {name}: {k}/{n}  [{lo:.0%}, {hi:.0%}]")
```

**Expected output when I ran it** [EXEC]: 40 files, median 50.5 lines; 70 chunks at 60/10 and 52 at 100/20; non-test functions cut across chunks 16 of 48 (33%) at 60/10 and 5 of 48 (10%) at 100/20; non-test function length median 21.5, p90 60, max 177; one labeled chunk per question at every size except `paraphrased-05` at 60/10 (two); Wilson intervals as in Part B.
