# Degraded response design (item 18d-1)

**Status: Approved (maintainer, 2026-10-31); implementation in 18d-2, 18d-3, 18d-4**

This is a documentation-only design record. It does not change application behavior.

## 1. Current behavior verified in code

- **Generation failure:** `scripts/investigate.py` catches an exception around query embedding and
  graph execution, attempts to persist a generic error, then re-raises it. `app/api.py` converts
  `RuntimeError` and `TimeoutError` into HTTP 502 with `upstream_failure`; the API does not return
  retrieved evidence with that error. `generation.py` tries Gemini first and attempts Groq only
  after eligible rate-limit, server, or timeout failures and only when fallback is enabled and
  configured. It raises if both attempts fail.
- **Embedding failure:** query embedding is performed before retrieval in
  `scripts/investigate.py`. No query-embedding cache is used in this runtime path today. A provider
  `RuntimeError` is persisted through `persist_error` and returned by the API as HTTP 502. No
  retrieval has happened, so the current error audit stores no retrieved chunks. The Gemini
  embedding helper can also raise `ValueError` for malformed or wrong-dimension output; the API
  currently maps `ValueError` to HTTP 422 `validation_error`, even when it came from an upstream
  response rather than request validation.
- **Guard without vector distance:** `evaluate_evidence_sufficiency()` returns
  `is_sufficient=false` and reason `"No vector similarity score was retrieved."` when retrieved
  results have no vector score. The graph widens retrieval once and then returns
  `INSUFFICIENT_EVIDENCE`; the script persists `refused_guard`. This refusal can be misleading
  when lexical evidence exists but no vector distance can be evaluated.
- **Persistence and GET:** current error persistence creates an `Investigation` with outcome
  `error`, plus an `Audit` whose retrieved chunk lists are empty. The API GET response falls back
  to diagnosis `INSUFFICIENT_EVIDENCE` and rating `low` when those database values are empty.
  Normal guard refusals persist retrieval metadata in the audit. The API response model has no
  degraded flags or content-free evidence list today.
- **CLI:** `scripts/investigate.py` prints the diagnosis, model rating, cited IDs, model, latency,
  retry state, and tool-attempt count for normal results. It does not currently print the
  `generation_trace` returned by the investigation function.
- **Provider telemetry:** when enabled, `app/providers/usage.py` records provider, model,
  operation, status, error class, attempt count, latency, available token counts, and correlation
  ID; it does not store prompt/response text. The investigation error trace currently stores the
  Python exception class, an `error` outcome, and the configured Gemini generation model even
  when the failure occurred during query embedding.

These observations come from [app/api.py](../../app/api.py),
[app/investigation/graph.py](../../app/investigation/graph.py),
[app/investigation/guard.py](../../app/investigation/guard.py),
[app/investigation/generation.py](../../app/investigation/generation.py),
[app/investigation/persistence.py](../../app/investigation/persistence.py),
[scripts/investigate.py](../../scripts/investigate.py),
[app/providers/gemini.py](../../app/providers/gemini.py),
[app/providers/groq.py](../../app/providers/groq.py),
[app/providers/usage.py](../../app/providers/usage.py),
[app/retrieval/hybrid_search.py](../../app/retrieval/hybrid_search.py), and
[app/retrieval/fulltext_search.py](../../app/retrieval/fulltext_search.py).

The existing provider taxonomy marks rate-limit, server, and timeout errors retryable; auth,
bad-request, safety-blocked, and schema-invalid errors are non-retryable. The Groq fallback is
generation-only. See the [provider-layer design](10-llm-gateway-design.md),
[gateway decision](09-llm-gateway-decision.md), and
[Groq fallback note](../notes/13-groq-generation-fallback.md).

## 2. Failure matrix

The “current behavior” column records the code as it exists now. The “proposed contract” column
applies only after approval and implementation. An “error audit” means the existing generic
`error` outcome plus an audit row, if persistence succeeds; it does not contain retrieval evidence.
Usage logging depends on its existing enable setting.

| Case | Current HTTP status and outcome | Proposed HTTP status, outcome, flags | Proposed persistence | Usage log and trace |
|---|---|---|---|---|
| Generation unavailable after Gemini retry budget and eligible Groq fallback are exhausted | HTTP 502 `upstream_failure`; the client receives no evidence list. A generic `error` audit is attempted, with no retrieved chunks. | HTTP 200; `generation_unavailable`; `unavailable_answer=true`, `degraded=true`, `degraded_reason="generation_unavailable"`; diagnosis empty, rating `not_applicable`; return metadata-only retrieved evidence. | Persist the new outcome, flags, evidence metadata, guard result, and trace in the existing investigation/audit records. Do not persist a generated answer or source text. | Preserve provider usage entries for Gemini and Groq failures, each with its existing provider/model/operation/status/error/attempt/latency/correlation fields. Audit trace records both provider outcomes, final degraded outcome, and correlation ID. |
| Embedding service is unavailable but a compatible query-vector cache entry is available | Not representable today: there is no runtime query cache, so the embedding request fails before retrieval and produces HTTP 502 for provider runtime errors. | Cache-first lookup means a compatible hit skips the provider request and uses ordinary hybrid retrieval: HTTP 200, normal `answered` or `refused_guard` outcome, `degraded=false`, `degraded_reason=null`. If a failed request is followed by finding a compatible cache entry, use it the same way. | Persist the ordinary investigation/audit plus cache-hit metadata; never persist query text in the cache. | A cache-first hit creates no provider usage entry because no provider request occurred. If a provider request failed before a cache recovery, retain its provider failure entry and record cache recovery in the audit trace. |
| Embedding request fails and there is no compatible cache entry | HTTP 502 for provider runtime errors; error audit attempted with no retrieval. A malformed embedding response currently becomes HTTP 422 due to the broad `ValueError` mapping. | HTTP 200; `embedding_unavailable`; `unavailable_answer=true`, `degraded=true`, `degraded_reason="embedding_unavailable"`; run sanitized-OR lexical-only retrieval, return metadata-only evidence, and do not generate an answer. `evidence_check.is_sufficient=null` with reason `"not evaluated: no query embedding"`. | Persist the new outcome, lexical evidence metadata, null guard state, `evidence_source="lexical_only"`, and trace in the existing investigation/audit records. Do not persist source text or an answer. | Usage log records the Gemini query-embedding failure when enabled. Trace records embedding error class, cache miss, lexical-only mode, result count, null guard state, degraded outcome, and correlation ID. |
| Both embedding and generation provider systems are unavailable | With no cache, current query embedding fails first; generation is never attempted. The current API returns HTTP 502 for provider runtime errors and attempts only a generic error audit. | With no cache, this is the embedding-unavailable case above: HTTP 200, `embedding_unavailable`; generation is intentionally not attempted. If a compatible cache vector is available, query embedding is served from cache and any subsequent exhausted Gemini/Groq generation failure follows the `generation_unavailable` row. | Persist the applicable single degraded outcome and its audit metadata. Never claim generation failed if generation was not attempted. | Record only provider operations that actually occurred. Cache use and skipped/attempted generation are distinguishable in trace. |
| Database unavailable | Database errors are not translated by a dedicated API handler; failures generally surface as HTTP 500. If an error happens after provider execution, provider usage may still be logged independently. Persistence may fail; no investigation ID or audit is guaranteed. | Unchanged: HTTP 500 for database failures; do not disguise database failure as a degraded success. If a provider runtime failure is independently what reaches the API, existing mapping remains HTTP 502. | No persistence guarantee while the database is unavailable. | Any already-written provider usage row may exist. No audit trace can be guaranteed. Never use an in-memory fallback to claim persistence. |
| Auth, bad-request, safety-blocked, or schema-invalid provider error | These are `RuntimeError` subclasses and are currently surfaced by the API as HTTP 502 `upstream_failure` (except malformed-output `ValueError`, which currently maps to 422). Gemini does not Groq-fallback on these typed classes. A generic error audit is attempted. | Preserve the current explicit error behavior and status mapping; never convert these classes to `generation_unavailable` or a lexical degraded response. | Existing error persistence only; no degraded outcome or evidence-shaped success. | Keep typed provider usage/error entries and a sanitized failure trace. Do not log prompts or keys. |

`MAX_ACCEPTABLE_VECTOR_DISTANCE` remains provisional. The
[18a-1 design](10-llm-gateway-design.md) and [18c/18d sequence](09-llm-gateway-decision.md)
already reserve final guard validation for item 3b; this proposal does not tune or relax the guard.

## 3. Recommended contract decisions

### D1 — Generation unavailable response

**Recommended:** after Gemini and any eligible configured Groq fallback have exhausted their
retry budgets on availability failures, return HTTP 200 with outcome `generation_unavailable`,
`unavailable_answer=true`, `degraded=true`, and
`degraded_reason="generation_unavailable"`. Set `diagnosis=""` and
`model_self_rating="not_applicable"`. Include the evidence metadata described in D2. No model
response, claims, citations, or self-rating are fabricated. Auth, bad-request, safety-blocked,
and schema-invalid errors do not qualify for this response.

**Alternative rejected:** HTTP 503 with evidence in the body. It communicates service failure in
the status line, but clients, proxies, or SDKs may discard or throw before exposing the evidence
body. A 200 response is safe only when clients are required to inspect `outcome`, `unavailable_answer`,
and `degraded`; a client that ignores these fields could mistake it for a generated answer. The
explicit flags and a distinct outcome are therefore mandatory.

### D2 — Evidence without a generated answer

**Recommended:** return a content-free `evidence` array of
`{chunk_id, file_path, start_line, end_line, rank, rrf_score, vector_score}` objects. Do not return
chunk source text, excerpts, prompts, or provider response text. This lets a caller locate evidence
without making the API a new source-code distribution surface.

**Alternative rejected:** include source snippets. Snippets might be convenient for clients but
would expose repository code through a response path that currently does not return retrieved
source text, expanding privacy and access-control consequences.

### D3 — Embedding unavailable without a cache hit

**Recommended:** on a cache miss followed by a Gemini query-embedding availability failure, use
the registered sanitized-OR query (C1) as **lexical-only retrieval in degraded mode**. Do not
change normal hybrid retrieval. Return HTTP 200, outcome `embedding_unavailable`,
`unavailable_answer=true`, `degraded=true`, and
`degraded_reason="embedding_unavailable"`. Return only content-free evidence metadata.

The descriptive results in [note 17](../notes/17-bm25-comparison-results.md) measured lexical
branch-only Hit@5 at **26/33** for sanitized-OR C1 and **5/33** for the current lexical branch.
These are development-only measurements, not a production-quality guarantee.

**Alternative rejected:** fail the entire request with the current 502 and return no evidence.
That discards useful lexical retrieval during an embedding outage. The selected C1 query is
already registered and sanitized; this proposal uses it only in degraded mode so normal retrieval
remains unchanged.

### D4 — Guard behavior without a query embedding

**Recommended:** do not call the vector-distance evidence guard as if it had evaluated lexical
evidence. Return `evidence_check.is_sufficient=null` with exact reason
`"not evaluated: no query embedding"`. Do not generate an answer from unguarded lexical evidence;
return only the evidence list. The vector guard cannot evaluate lexical-only results, its threshold
is provisional pending item 3b, and the guard has had false accepts.

**Alternative rejected:** allow generation with an `unverified_evidence` flag. That risks presenting
unguarded code evidence as a diagnosis before the guard has been validated. The other alternative,
always returning an empty refusal, avoids that risk but discards potentially useful ranked paths
and line ranges. The recommended contract exposes those locations but never turns them into an
answer.

### D5 — Persistent query-embedding cache

**Recommended:** use a persistent database table with a key equal to
`(embedding_model, task_type, dimensions, SHA-256(whitespace-normalized query))`. Normalize by
trimming and collapsing each whitespace run to one ASCII space; preserve case before hashing.
Store the vector and `created_at`; **never store the query text**. Use a 30-day TTL and a fixed
10,000-row cap. Before a lookup or write, expire rows older than 30 days. After inserts, evict the
oldest-created rows first until the table is within the cap. A cache hit is used in normal
operation and avoids an embedding provider call. Different model, task type, dimensions, or query
hash values miss automatically.

This requires a migration to create the cache table and its unique lookup index. Store the vector
as a JSON numeric array so the cache can represent the dimension value in its key; validate its
length before use. The privacy benefit is that no raw query is retained, though a deterministic
hash can still be linkable for a guessed query and therefore remains protected data. The migration
adds stored query-derived vectors and requires an explicit retention/eviction test.

**Alternative rejected:** in-process LRU. It is simpler and needs no migration, but loses entries
on restart and cannot provide useful cross-restart coverage during a provider outage. It does not
meet the goal of persistent cache hits in normal operation and degraded mode.

### D6 — Interaction with item 18b

**Recommended:** `generation_unavailable` is returned only after Gemini has exhausted its retries
and any eligible, enabled, configured Groq fallback has also failed. Preserve 18b's non-fallback
classes. Embeddings remain Gemini-only; they never fall back to Groq or another embedding provider
because vectors from different embedding spaces are not interchangeable. An embedding cache is
reuse of a previously generated vector, not another provider.

**Alternative rejected:** use Groq or another provider for embeddings. A different vector space
would not be comparable to the existing indexed chunk vectors and could silently corrupt retrieval
semantics.

### D7 — Additive API, GET, and CLI compatibility

**Recommended:** add response fields with backward-compatible defaults:
`unavailable_answer=false`, `degraded=false`, `degraded_reason=null`, and `evidence=[]`.
Document the new outcome values `generation_unavailable` and `embedding_unavailable`.
Persist the outcome, flags, reason, evidence metadata, and trace in the audit JSONB payload;
`GET /investigations/{id}` reconstructs the same degraded fields from that audit. The CLI mirrors
the outcome, flags, reason, guard state, and metadata-only evidence without printing source text.
For both degraded outcomes, use an empty diagnosis, no claims or cited IDs, and
`model_self_rating="not_applicable"`.

The existing investigation `outcome` column is `String(32)` and has no model-level check
constraint; both proposed outcome values fit. Audit trace and tool-call data are JSONB. Thus this
contract can avoid a schema migration if it stores the additional fields in the audit JSONB and
uses the existing outcome column. A migration is needed only if maintainers choose dedicated
relational columns instead.

**Alternative rejected:** replace existing fields or return a separate incompatible error schema.
That would break existing API clients without adding safety; additive defaults let older consumers
continue parsing existing response keys, while consumers that understand the new contract can
reliably distinguish a refusal, an answer, and an unavailable answer.

## 4. Exact JSON response examples

The following are complete shapes for the proposed degraded API response. Values are illustrative;
no source text is present.

### Example A — Generation unavailable after normal hybrid retrieval

```json
{
  "investigation_id": 731,
  "repository_name": "example-repo",
  "query": "How does request authentication work?",
  "diagnosis": "",
  "outcome": "generation_unavailable",
  "model_self_rating": "not_applicable",
  "rating_note": "No model response was generated.",
  "cited_chunk_ids": [],
  "evidence_check": {
    "is_sufficient": true,
    "reason": "At least one retrieved chunk is within the maximum vector distance.",
    "best_rrf_score": 0.032,
    "best_vector_score": 0.31
  },
  "retry_used": false,
  "tool_calls": [],
  "claims": [],
  "uncertainty_note": "Generation unavailable after configured provider retries.",
  "citation_validation": {
    "submitted": 0,
    "valid": 0,
    "rate": null
  },
  "model": "",
  "latency_ms": null,
  "evaluation_note": "Existing evaluation note.",
  "unavailable_answer": true,
  "degraded": true,
  "degraded_reason": "generation_unavailable",
  "evidence": [
    {
      "chunk_id": "42",
      "file_path": "app/security.py",
      "start_line": 20,
      "end_line": 38,
      "rank": 1,
      "rrf_score": 0.032,
      "vector_score": 0.31
    }
  ]
}
```

### Example B — Embedding unavailable, no cache, lexical-only evidence

```json
{
  "investigation_id": 732,
  "repository_name": "example-repo",
  "query": "How does request authentication work?",
  "diagnosis": "",
  "outcome": "embedding_unavailable",
  "model_self_rating": "not_applicable",
  "rating_note": "No model response was generated.",
  "cited_chunk_ids": [],
  "evidence_check": {
    "is_sufficient": null,
    "reason": "not evaluated: no query embedding",
    "best_rrf_score": null,
    "best_vector_score": null
  },
  "retry_used": false,
  "tool_calls": [],
  "claims": [],
  "uncertainty_note": "Lexical-only evidence is returned; the vector guard and generation were not run.",
  "citation_validation": {
    "submitted": 0,
    "valid": 0,
    "rate": null
  },
  "model": "",
  "latency_ms": null,
  "evaluation_note": "Existing evaluation note.",
  "unavailable_answer": true,
  "degraded": true,
  "degraded_reason": "embedding_unavailable",
  "evidence": [
    {
      "chunk_id": "42",
      "file_path": "app/security.py",
      "start_line": 20,
      "end_line": 38,
      "rank": 1,
      "rrf_score": 0.016,
      "vector_score": null
    }
  ]
}
```

### Example C — Embedding provider unavailable, compatible cached vector used, generation unavailable

The cache provides a compatible query vector, so normal hybrid retrieval runs. The generation
providers then exhaust their eligible attempts. The response follows D1; the cache prevents an
embedding outage from forcing lexical-only retrieval.

```json
{
  "investigation_id": 733,
  "repository_name": "example-repo",
  "query": "How does request authentication work?",
  "diagnosis": "",
  "outcome": "generation_unavailable",
  "model_self_rating": "not_applicable",
  "rating_note": "No model response was generated.",
  "cited_chunk_ids": [],
  "evidence_check": {
    "is_sufficient": true,
    "reason": "At least one retrieved chunk is within the maximum vector distance.",
    "best_rrf_score": 0.032,
    "best_vector_score": 0.31
  },
  "retry_used": false,
  "tool_calls": [],
  "claims": [],
  "uncertainty_note": "Generation unavailable after configured provider retries.",
  "citation_validation": {
    "submitted": 0,
    "valid": 0,
    "rate": null
  },
  "model": "",
  "latency_ms": null,
  "evaluation_note": "Existing evaluation note.",
  "unavailable_answer": true,
  "degraded": true,
  "degraded_reason": "generation_unavailable",
  "evidence": [
    {
      "chunk_id": "42",
      "file_path": "app/security.py",
      "start_line": 20,
      "end_line": 38,
      "rank": 1,
      "rrf_score": 0.032,
      "vector_score": 0.31
    }
  ]
}
```

## 5. Degraded-event telemetry

Keep the existing provider usage schema and correlation ID. Each actual provider request records
its provider, model, operation tag, status, typed error class, attempt count, latency, available
token counts, and correlation ID. A cache hit makes no provider request and therefore creates no
provider usage row.

The investigation audit trace should record: overall outcome and degraded reason; the stage that
failed (`query_embedding` or `generation`); provider/model attempts and typed error classes;
attempt counts and elapsed time; cache hit/miss and cache identity metadata (never the query);
retrieval mode and result count; whether the guard ran and its boolean/null result; and correlation
ID. The terminal CLI may print the same summary and metadata-only evidence. Neither provider
usage records nor diagnostic trace may contain prompt text, query text as telemetry, source
snippets, model response content, or API keys. The regular API `query` field remains an ordinary
response field; it is not copied into new telemetry.

## 6. Implementation test plan and proposed split

All tests use fake providers and in-memory/fake cache behavior; no live provider call is needed.
Implement 18d-4 before 18d-3: the persistent cache-hit path is encountered before lexical-only
fallback in the query flow.

| Proposed implementation PR | Scope and tests | Schema migration |
|---|---|---|
| **18d-2 — contract and generation degradation** | Add response defaults and outcome docs; fake Gemini transient failures and enabled/disabled Groq fallback; assert generation-unavailable shape only after eligible exhaustion; ensure auth, bad-request, safety-blocked, and schema-invalid errors remain explicit; map malformed or wrong-dimension upstream embedding responses to upstream-failure (HTTP 502), not validation_error (HTTP 422); record the failed stage and that stage's model in the error audit; print the generation trace and degraded states in the CLI; assert evidence contains metadata only; verify persistence and `GET /investigations/{id}` round-trip. | No migration if the new flags/evidence/trace remain in audit JSONB and outcome uses the existing `String(32)` column. |
| **18d-4 — persistent query cache** | Verify composite identity changes for model/task type/dimensions/query; whitespace collapse with case preservation; no query-text column or serialized query; vector length validation; cache-hit reuse in normal mode; cache miss provider call; 30-day expiration; 10,000-row cap with oldest-created eviction; restart-persistent retrieval. | **Yes.** Create the persistent cache table and unique index; include rollback and retention/eviction coverage. |
| **18d-3 — lexical-only mode** | Fake query-embedding failures with and without a cache hit; assert C1 sanitized-OR lexical-only results, normal hybrid unchanged, no generation on cache miss, null guard state and exact reason, metadata-only evidence, and correct `embedding_unavailable` outcome; test provider error classes that must not degrade. | No migration; reuse current lexical retrieval and audit JSONB. |

## 7. Maintainer approval

The maintainer approved each recommendation without changes.

| Decision | Recommendation | Approved | Changed | Maintainer decision / notes |
|---|---|---|---|---|
| D1 | Recommended: HTTP 200 with explicit unavailable/degraded flags for eligible generation unavailability. | [x] | [ ] | Approved as recommended by the maintainer |
| D2 | Recommended: metadata-only evidence; no source text. | [x] | [ ] | Approved as recommended by the maintainer |
| D3 | Recommended: sanitized-OR C1 lexical-only retrieval only after embedding failure and cache miss. | [x] | [ ] | Approved as recommended by the maintainer |
| D4 | Recommended: null/not-evaluated guard, never generate from lexical-only evidence. | [x] | [ ] | Approved as recommended by the maintainer |
| D5 | Recommended: persistent, query-text-free cache; 30-day TTL; 10,000-row cap; oldest-first eviction. | [x] | [ ] | Approved as recommended by the maintainer |
| D6 | Recommended: generation-only Groq fallback; Gemini-only embeddings and cache reuse. | [x] | [ ] | Approved as recommended by the maintainer |
| D7 | Recommended: additive API fields, audit-backed GET reconstruction, matching CLI states. | [x] | [ ] | Approved as recommended by the maintainer |

**Approval date:** 2026-10-31

## 8. Honest limits

The sanitized-OR lexical-only Hit@5 result (26/33 versus 5/33 for the current lexical branch) is
measured only on 33 answerable development questions across three small repositories by one
author. It is not a general quality guarantee. The held-out split remains untouched. The evidence
guard's vector-distance threshold is provisional and must still be validated under item 3b.
Lexical-only mode cannot evaluate that guard at all; this proposal therefore returns locations for
inspection and never generates an answer from them.
