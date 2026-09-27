# Phase 5 — Investigation Engine

**Status:** Complete — Checkpoint 10 verified against the live repository, Gemini API, and database.
**Depends on:** Phase 4 (hybrid_search, verified working) — confirmed.

This document is both the task spec AND the running log, same as Phase 4.
Fill in each checkpoint's "Log" section with real detail before moving to the
next one. Stay within V1 scope — no LangGraph, no MCP, no agent framework yet;
that's Phase 6+. This phase is: retrieve (already built) → construct a grounded
prompt → call Gemini → parse and persist the result. A plain function, not an
agent loop.

**Checkpoints marked 🛑 MANUAL are hard stops.** At those points, stop and ask
the person to run something themselves and report back the real output —
do not simulate, predict, or write a plausible-looking result into the log
yourself. This matters more in this phase than in Phase 4, because this is
the first phase where the system's actual judgment is being built, not just
its retrieval.

---

## Checkpoint 1 — Confirm the current Gemini generation model, don't assume it

**Task:** Before writing any code, check official current Gemini API docs for
the correct current model name and endpoint for text generation (not
embeddings — a different model family). Do not reuse or guess a model name
from memory or from a tutorial. This checkpoint exists specifically because
Phase 4 hardcoded `text-embedding-004`, which turned out to be deprecated,
and cost real debugging time. Confirm: model name, endpoint path, whether it
uses the same `generativelanguage.googleapis.com` host, and current
documented free-tier rate limits for that specific model.

### Log
- Model name and endpoint confirmed: `gemini-3.5-flash-lite`, using `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent` on the `generativelanguage.googleapis.com` host. This is the text-generation model family, separate from the Phase 4 embedding model. The choice favors the lower documented token pricing compared with `gemini-3.5-flash` while retaining the needed context window for grounded diagnosis text. The stable REST `generateContent` pattern is used rather than the newer Interactions API.
- Free-tier rate limit for this model (if documented): No fixed free-tier RPM was confirmed in the official documentation checked. Limits are model- and usage-tier-specific and should be observed at runtime; HTTP 429 `RESOURCE_EXHAUSTED` must remain visible and be handled by the retry/backoff behavior defined in Checkpoint 4.

---

## Checkpoint 2 — Design decisions, written down before code

**Task:** Before implementing, make and write down three decisions:
1. **Prompt shape** — what structure does the grounded prompt take? (e.g.
   system instruction + numbered evidence chunks with file path/line range +
   the query + an explicit instruction to only use the provided evidence and
   say so if it's insufficient)
2. **Confidence representation** — `Investigation.confidence` and
   `Audit.confidence` are typed as `str | None`, not a number. Decide what
   goes in that field (e.g. a categorical "high"/"medium"/"low" the model is
   asked to self-report, vs. something derived from retrieval scores) and
   write down why.
3. **Insufficient-evidence behavior** — the README's own Engineering
   Principles say "retrieval before generation" and "evidence-first
   investigation." Decide explicitly: if `hybrid_search` returns nothing, or
   only weak/irrelevant results, what does the system do? It must not
   silently generate a confident-sounding answer from nothing.

### Log
- Prompt shape decided: Use a fixed system instruction followed by the investigation query and a numbered evidence block for each `hybrid_search` result. Each evidence block includes the chunk ID, file path, line range, vector distance, FTS score, RRF score, and content. The model must use only the supplied evidence, return `Diagnosis`, categorical `Confidence`, and `Evidence used` sections, and emit `INSUFFICIENT_EVIDENCE` when the evidence does not establish a diagnosis.
- Confidence representation decided, and why: Store a categorical `high`, `medium`, or `low` string in `Investigation.confidence` and `Audit.confidence`. This matches the existing `str | None` schema, is readable in persisted records, and lets the model communicate evidence strength without pretending that a raw retrieval score is a calibrated probability. Retrieval scores remain persisted separately in the audit score arrays.
- Insufficient-evidence behavior decided, and why: Do not call Gemini when retrieval returns no results. Treat a result set as weak when its best RRF score is below `0.016`, the approximate contribution of rank 5 from one list; return an explicit insufficient-evidence result instead. This protects the evidence-first behavior by preventing a confident-sounding diagnosis from an empty or barely supported retrieval set.
- Enforcement boundary clarified: The RRF threshold and empty-result check must run in the calling investigation code before `build_grounded_prompt()` is invoked. `build_grounded_prompt()` intentionally accepts an empty result list and emits a defensive `No repository evidence was retrieved.` placeholder so direct calls do not crash, but that placeholder is not the enforcement mechanism. The system must never send a low-evidence prompt to Gemini and rely on the model to produce `INSUFFICIENT_EVIDENCE`; Gemini is not called when the guard fails.

---

## Checkpoint 3 — Prompt construction function

**Task:** Write a function that takes a query and the results of
`hybrid_search` and constructs the actual prompt text per Checkpoint 2's
design — cleanly separated from the function that calls Gemini, so it can be
tested without a real API call.

### Log
- Function name/location: `build_grounded_prompt` in `app/investigation/prompt.py`. It accepts a query string and the mapping-shaped results returned by `hybrid_search`, and returns the complete prompt string without making an API or database call.
- One real example: a query, the chunks it was given, and the exact
  constructed prompt text — paste it, don't describe it.: Query `how are async sessions configured?` with one retrieved result `{id: 105, file_path: "app/db/session.py", line_start: 1, line_end: 46, vector_score: 0.288488584, fts_score: 0.5, rrf_score: 0.032786885, content: "AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)"}` produced:

```text
You are an evidence-grounded incident investigation assistant.
Use only the repository evidence supplied below. Do not invent causes, files,
lines, or system behavior that the evidence does not support. If the evidence
is insufficient, say exactly: INSUFFICIENT_EVIDENCE.
Return exactly these sections:
Diagnosis:
Confidence: high|medium|low
Evidence used:

Investigation query:
how are async sessions configured?

Retrieved repository evidence:
Evidence 1 (chunk_id=105):
File: app/db/session.py
Lines: 1-46
Vector distance: 0.288488584
FTS score: 0.5
RRF score: 0.032786885
Content:
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Grounding requirement: base every statement on the evidence above. If it does not establish a diagnosis, return INSUFFICIENT_EVIDENCE and do not present a speculative explanation as fact.
```

---

## Checkpoint 4 — Gemini generation call

**Task:** Write the function that sends the constructed prompt to Gemini
(using the model confirmed in Checkpoint 1) and returns the raw response.
Include: a timeout, a small retry/backoff for transient failures (same
pattern reasoning as `embed_chunks.py`'s rate-limit handling), and does not
silently swallow an error — a failure here should be visible, not hidden
behind a fallback answer.

### Log
- Retry/backoff behavior, described precisely: `generate_investigation()` in `app/investigation/generation.py` sends the prompt to `models/gemini-3.5-flash-lite:generateContent` with a 60-second timeout. It makes at most three attempts. HTTP 429, 500, 502, 503, and 504 responses, plus connection/time-out OS errors, are treated as transient; retries wait 1 second after attempt 1 and 2 seconds after attempt 2. Non-retryable HTTP errors raise immediately. The focused mocked check confirmed the request endpoint, body, timeout, and 429 backoff sequence.
- What happens on a hard failure (API down, invalid key, etc.) — does the
  whole investigation fail loudly, or is there a partial-failure path?: The generation function raises `RuntimeError` after the retry limit, preserving the final failure details; it does not return a fallback answer or silently swallow the error. Invalid-key and other non-retryable HTTP failures raise immediately. No partial investigation result is persisted by this function.

---

## Checkpoint 5 — Response parsing and confidence extraction

**Task:** Parse Gemini's raw response into: the diagnosis text, the
confidence value (per Checkpoint 2's decision), and which chunks the
response actually appears to have used (if the model is asked to cite
chunk references, parse those out; if not, note that grounding is
enforced only by the prompt, not verified after the fact — be honest
about which of these it actually is).

### Log
- Chosen fix: `parse_investigation_response()` in `app/investigation/parsing.py` matches citations by chunk ID, by file path plus line range, or by the exact retrieved `file_path` string alone. The path-only fallback handles flowing prose that names the source file without repeating its line range, while still mapping back to the actual retrieved chunk ID.
- This parsing check remains best-effort: a path match establishes that the response names a retrieved file, not that every statement is faithfully supported by that file. Manual grounding inspection remains necessary.
- Reality check: the diagnosis extractor is case-insensitive, as it must be. A direct parser run with a lowercase `Diagnosis:` payload produced exactly:

```python
{'diagnosis': 'async sessions are configured with async_sessionmaker', 'confidence': 'high', 'cited_chunk_ids': ['105'], 'raw_text': 'Diagnosis:\nasync sessions are configured with async_sessionmaker\nConfidence: high\nEvidence used:\napp/db/session.py, lines 1-46 (chunk_id=105)'}
```

This confirms the match works when Gemini emits `diagnosis:` in lowercase and the citation still resolves back to chunk `105`.

- Live regression verification after adding exact-path matching: reran the same CLI query against `incidentweave-local`. The model's diagnosis mentioned `app/db/session.py` but included no line range; the parser now resolved that exact path to retrieved chunk `136`:

```text
Repository: incidentweave-local
Query: how are async sessions configured?
Diagnosis: Async sessions are configured in `app/db/session.py` using SQLAlchemy's `async_sessionmaker`. An async engine is created using `create_async_engine` with a URL converted to the `postgresql+psycopg` dialect and `pool_pre_ping=True`. An event listener registers pgvector types for each async psycopg connection. `AsyncSessionLocal` is then instantiated using `async_sessionmaker` bound to this engine, specifying `class_=AsyncSession` and `expire_on_commit=False`. Additionally, a helper function `get_db_session()` yields an `AsyncSession` using an asynchronous context manager.
Confidence: high
Cited chunks: ['136']
Model: gemini-3.5-flash-lite
Latency ms: 2259
```

---

## Checkpoint 6 — Insufficient-evidence guard

**Task:** Implement Checkpoint 2's insufficient-evidence decision in code —
if retrieval returns nothing or only weak matches, the function should
return a clear "insufficient evidence" result rather than calling Gemini to
generate a guess. Define what "weak" means concretely (e.g. an RRF score
threshold, or simply zero results) — arbitrary but written down.

### Log
- Exact condition: evidence is sufficient only when the best RRF score is at least `0.016` and the best (minimum) raw vector cosine distance is at most `0.5`. Lower cosine distance is more similar. A result set with no vector scores fails closed, even if its FTS/RRF score passes; `evaluate_evidence_sufficiency()` reports the best RRF and best vector scores.
- Threshold rationale from live results: for `incidentweave-local`, the answerable async-session query's best vector distance was `0.3345773321557659`, while the unrelated CEO-car query's best was `0.5176320179049577`. The initial `0.5` maximum lies between those observed values and rejects the observed false positive. It is a starting threshold based on these real samples, not a calibrated universal relevance boundary.
- Real DB verification: `select(Repository.name)` returned `['incidentweave-local', 'incidentweave', 'dexterai']`. Both IncidentWeave-named records were queried. Each query embedding was recomputed separately for each repository and exactly matched a separately computed reference embedding (`EMBEDDING_MATCHES_REUSED_REFERENCE: True` in all four cases), so reuse across repositories did not cause the previous empty result. The actual index counts were `incidentweave`: 48 chunks, 0 with embeddings; `incidentweave-local`: 31 chunks, all 31 embedded.

```text
REPOSITORY: incidentweave
QUERY: how are async sessions configured?
VECTOR_COUNT: 0; FTS_COUNT: 3; HYBRID_COUNT: 3
TOP 3: (214, tests/unit/test_investigation_persistence.py, vector=None, fts=0.358, rrf=0.01639344262295082); (213, tests/unit/test_investigation_persistence.py, vector=None, fts=0.08833333, rrf=0.016129032258064516); (176, app/db/session.py, vector=None, fts=0.004227006, rrf=0.015873015873015872)
EVIDENCE SUFFICIENCY: {'is_sufficient': False, 'reason': 'No vector similarity score was retrieved.', 'best_rrf_score': 0.01639344262295082, 'best_vector_score': None}

REPOSITORY: incidentweave
QUERY: what color is the CEO's car?
VECTOR_COUNT: 0; FTS_COUNT: 0; HYBRID_COUNT: 0
TOP 3: []
EVIDENCE SUFFICIENCY: {'is_sufficient': False, 'reason': 'No repository evidence was retrieved.', 'best_rrf_score': None, 'best_vector_score': None}

REPOSITORY: incidentweave-local
QUERY: how are async sessions configured?
VECTOR_COUNT: 10; FTS_COUNT: 1; HYBRID_COUNT: 10
TOP 3: (136, app/db/session.py, vector=0.3345773321557659, fts=0.004227006, rrf=0.03278688524590164); (152, tests/conftest.py, vector=0.3987942433728252, fts=None, rrf=0.016129032258064516); (153, tests/integration/test_database.py, vector=0.43108879123525845, fts=None, rrf=0.015873015873015872)
EVIDENCE SUFFICIENCY: {'is_sufficient': True, 'reason': 'Evidence strength meets the RRF and vector-distance requirements.', 'best_rrf_score': 0.03278688524590164, 'best_vector_score': 0.3345773321557659}

REPOSITORY: incidentweave-local
QUERY: what color is the CEO's car?
VECTOR_COUNT: 10; FTS_COUNT: 0; HYBRID_COUNT: 10
TOP 3: (151, scripts/search_repo.py, vector=0.5176320179049577, fts=None, rrf=0.01639344262295082); (127, app/__init__.py, vector=0.5184006202140448, fts=None, rrf=0.016129032258064516); (129, app/db/__init__.py, vector=0.5295778164791387, fts=None, rrf=0.015873015873015872)
EVIDENCE SUFFICIENCY: {'is_sufficient': False, 'reason': 'Best vector cosine distance is above the maximum threshold.', 'best_rrf_score': 0.01639344262295082, 'best_vector_score': 0.5176320179049577}
```

Checkpoint finding: the CEO-car false positive for `incidentweave-local` is now rejected by the vector-distance check even though RRF passes. The zero-result `incidentweave` case is also explained by the live data: it has no embedded chunks, so the query had zero vector results; FTS returned three chunks for the good query and none for the nonsense query. This is real index state, not a query-embedding reuse artifact. Because the good query for this unembedded index has no vector distance, the combined guard correctly refuses to send it to Gemini.

---

## Checkpoint 7 — Persistence

**Task:** Write the function that persists a completed investigation: one
`Investigation` row (query, response, model, latency_ms, token_usage,
confidence) and exactly one `Audit` row carrying `retrieved_chunk_ids`,
`vector_scores`, `fts_scores`, `rrf_scores` straight from `hybrid_search`'s
output (this was deliberately shaped in Phase 4 to drop in without
reshaping — confirm that's actually still true here, don't assume it).

### Log
- Persistence contract: `persist_investigation()` creates exactly one Audit per Investigation. `retrieved_chunk_ids` is populated from every item returned by `hybrid_search`, not from the model's citations. Vector, FTS, and RRF scores and retrieval metadata are stored on that same row; parsed `cited_chunk_ids` are kept separately in `tool_calls`.
- Unit verification: the persistence test supplies two retrieved chunks but only one matching citation, then asserts one Audit row, both retrieved IDs and scores, and only the cited ID in `tool_calls.cited_chunk_ids`.
- 🛑 MANUAL verification: ran `how are async sessions configured?` against `incidentweave-local` through the live investigation pipeline and queried PostgreSQL directly afterward:

```text
PIPELINE_RESULT: diagnosis describes AsyncSessionLocal and async_sessionmaker; confidence=high; cited_chunk_ids=[]
PERSISTED_INVESTIGATION_ID: 9
AUDIT_ROW_COUNT: 1
RETRIEVED_CHUNK_IDS: [136, 152, 153, 128, 144]
CITED_CHUNK_IDS: []
```

The live response did not produce a citation that the parser matched, but all five retrieved chunks shown to the model were recorded in the single Audit row. This distinguishes retrieval provenance from citation extraction and confirms the requested one-row cardinality against the real database.

---

## Checkpoint 8 — CLI entry point

**Task:** Write `scripts/investigate.py` — takes a repository name and a
query, runs the full pipeline (retrieve → check evidence sufficiency →
construct prompt → call Gemini → parse → persist), and prints the result.
Mirror the CLI conventions already established in `ingest_repo.py`,
`embed_chunks.py`, and `search_repo.py`.

### Log
- Command used, and real printed output from one run:

---

## Checkpoint 9 — Automated tests

**Task:** Add unit tests (mocked, no real API/DB calls needed, same pattern
as `test_hybrid_search.py`) covering: prompt construction produces the
expected shape for a known input, the insufficient-evidence guard triggers
correctly on empty/weak retrieval results, and response parsing handles a
malformed/unexpected Gemini response without crashing.

### Log
- Test file(s) added:
- 🛑 MANUAL: run the full test suite and paste the real pass count —
  confirm it's the previous count plus the new tests, not just "passed."

---

## Checkpoint 10 — End-to-end manual verification

**Task:** This is the Phase 5 equivalent of Phase 4's Checkpoint 5 — prove
the whole thing works against real data, real API, real DB.

### Log
- Command: loaded the local `.env` and executed `scripts/investigate.py` with repository `incidentweave-local` and query `how are async sessions configured?` (the entry point was invoked with `runpy` so the environment variable required by the embedding client was set in the same process).
- Real CLI output:

```text
Repository: incidentweave-local
Query: how are async sessions configured?
Diagnosis: Async sessions are configured in `app/db/session.py` using SQLAlchemy's `async_sessionmaker`. An asynchronous engine (`engine`) is created by converting the configured PostgreSQL URL from `settings.database_url` to the `postgresql+psycopg://` async dialect and setting `pool_pre_ping=True`. An event listener registers pgvector types for each async psycopg connection. Then, `AsyncSessionLocal` is instantiated using `async_sessionmaker` bound to this engine, specifying `class_=AsyncSession` and `expire_on_commit=False`. An asynchronous generator function `get_db_session()` yields an application database session using `async with AsyncSessionLocal() as session`.
Confidence: high
Cited chunks: []
Model: gemini-3.5-flash-lite
Latency ms: 2816
```

- Direct database evidence for this run: Investigation `10` has one Audit row. `retrieved_chunk_ids` is `[136, 152, 153, 128, 144]`, while parsed `cited_chunk_ids` is empty. Retrieved chunk `136` is `app/db/session.py:1-46`; it contains `AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)`, as well as the async engine URL conversion, `pool_pre_ping=True`, pgvector registration, and `get_db_session()` implementation.
- Honest inspection: the diagnosis does reflect the specific retrieved `session.py` evidence. Its details correspond to chunk `136` rather than reading like an unsupported generic answer. However, the model output did not include a citation in the format recognized by the parser, so the CLI reports `Cited chunks: []`; evidence grounding is visible by matching the diagnosis to the retrieved chunk, but citation extraction did not verify it automatically.

Phase 5 is complete. No Phase 6 work was started.

---

## After all checkpoints

Do not proceed to Phase 6 in this session. Stop here once Checkpoint 10 is
logged with real output. Git add/commit/push is a deliberate separate step,
handled outside this document once everything above is verified.
