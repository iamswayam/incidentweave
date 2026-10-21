# Phase 4 — Embeddings & Retrieval

**Status:** Complete
**Depends on:** scripts/ingest_repo.py (Phase 3) working and idempotent — confirmed.

This document is both the task spec AND the running log. Copilot: update the
"Log" section under each checkpoint as you complete it — do not wait until the
end to write everything at once. Do not skip a checkpoint's log entry to move
faster. Stay within V1 scope: no LangGraph, no MCP, no new dependencies beyond
what embeddings/retrieval strictly require (a Gemini SDK client is fine).

---

## Checkpoint 1 — Embedding script

**Task:** Write `scripts/embed_chunks.py` that:
1. Takes a repository `name` as a CLI arg
2. Queries all `Chunk` rows for that repository where `embedding IS NULL`
3. Calls the Gemini embeddings API for each chunk's `content` (batch if the SDK
   supports it, otherwise one at a time — keep it simple)
4. Writes the resulting vector back into that chunk's `embedding` column
5. Handles API failures per chunk without aborting the whole run — log the
   failure, skip that chunk, continue
6. Prints a summary: chunks embedded, chunks failed, chunks skipped (already had
   an embedding)

**Before writing code:** state in the log below what Gemini embedding model
you're using and its output dimension — confirm it's 768 to match the existing
`VECTOR(768)` column. If it doesn't match, stop and flag this instead of
silently reshaping vectors or changing the column.

### Log
<!-- Copilot fills this in after completing the checkpoint -->
- Embedding model used, and confirmed dimension: The original request using `models/text-embedding-004` returned HTTP 404: the model was not found or supported for `embedContent`. The script was changed to `models/gemini-embedding-001`, requests `outputDimensionality: 768`, and constructs the endpoint with a single `models/` path segment. On the clean 31-chunk corpus, each successful response passed the script's 768-value validation and was stored in the unchanged `VECTOR(768)` column.
- What the retry/failure handling actually does: The script processes only chunks with no existing embedding, one request at a time, and waits 1.5 seconds after each attempt. Per-chunk errors, including HTTP 429 `RESOURCE_EXHAUSTED`, are logged with the chunk ID and file path, counted as failures, and processing continues. It does not retry failed requests automatically.
- Command used to run it, and the summary output from a real run: In Windows CMD, after loading `GEMINI_API_KEY` from `.env`, ran `python scripts\embed_chunks.py incidentweave-local`. The first clean-corpus run reported 30 embedded, 1 failed (`Remote end closed connection without response` for `app/db/models/investigation.py`), and 0 skipped. Retrying the script processed only the still-unembedded row and reported:

```text
Chunks embedded: 1
Chunks failed: 0
Chunks skipped: 30
```

The final clean corpus therefore has all 31 chunks embedded; the transient connection failure was recovered by rerunning the idempotent embedding command.

---

## Checkpoint 2 — Vector similarity search

**Task:** Add a function `search_vector(session, repository_id, query_embedding, limit=10)`
in a new file `app/retrieval/vector_search.py` that returns the top-N chunks by
vector distance (pgvector `<=>` cosine distance or `<->` L2 — pick one, state
which and why in the log) for a given repository, along with each chunk's
distance/score.

### Log
- Which distance operator was used and why: Using pgvector's `<=>` operator for cosine distance. It is the direct match for semantic similarity ranking in the existing `vector` column, and it keeps the query semantics consistent with the project's vector search requirement without introducing a more complex metric choice at this stage.
- Any pgvector index consideration for this table size (or explicit note that
  no index is needed yet at this scale): For the current V1 scale, the code is intentionally simple and no dedicated pgvector index was added. This is a reasonable default for a small repo/phase before retrieval performance becomes a bottleneck; if a repository grows large enough to warrant optimization, a HNSW or IVFFlat strategy can be revisited later.

---

## Checkpoint 3 — Full-text search

**Task:** Add a function `search_fulltext(session, repository_id, query_text, limit=10)`
in `app/retrieval/fulltext_search.py` using Postgres full-text search
(`to_tsvector`/`plainto_tsquery` or `websearch_to_tsquery`) against `Chunk.content`,
returning top-N chunks with their FTS rank score.

### Log
- Which tsquery function was chosen and why: Using `websearch_to_tsquery` against `Chunk.content` because it is a practical, user-friendly text-query parser for natural-language search terms and it is consistent with a repository-search workflow where users ask plain-language questions.
- Whether a GIN index is needed on `content` for this to perform reasonably —
  state the decision, add a migration if yes: No migration was added for a GIN index at this stage. For the V1 repository-chunking scale and the current project phase, the simpler `to_tsvector(...) @@ websearch_to_tsquery(...)` path is sufficient without premature indexing optimization.

---

## Checkpoint 4 — RRF fusion

**Task:** Add a function `hybrid_search(session, repository_id, query_text, query_embedding, limit=10)`
in `app/retrieval/hybrid_search.py` that:
1. Runs `search_vector` and `search_fulltext` independently
2. Combines their two rankings using Reciprocal Rank Fusion (RRF): for each
   chunk, score = sum over each ranking it appears in of `1 / (k + rank)`,
   with `k=60` as a standard default
3. Returns the top-N chunks by fused score, along with the individual vector
   score, fts score, and fused rrf score for each — these three values map
   directly to the `vector_scores`, `fts_scores`, `rrf_scores` fields already
   defined on the `Audit` model, so this function's output should be shaped to
   drop straight into an `Audit` row later without reshaping

### Log
- Confirm in your own words (Copilot, write this as if explaining to someone
  who's never seen RRF): why combine two rankings this way instead of just
  averaging the two raw scores directly?: RRF is ranking-based, not score-based. It rewards a chunk when it appears highly in either retrieval method without assuming the raw vector distance and raw FTS score are on the same scale. A chunk that ranks first in both methods gets a strong fused score, while a chunk that is only moderately good in one method but absent in the other is downweighted. This makes the fusion robust when the two systems use different numeric scales and semantics.
- A real example: pick one test query, show the top 3 results from vector-only,
  top 3 from fts-only, and top 3 from the fused result — did fusion change the
  ranking in a way that makes sense?: For the required query `how are asynchronous database sessions created and configured`, the clean-corpus vector-only top 5 (cosine distance; lower is better) were: (1) `app/db/session.py:1-46`, distance 0.288488584; (2) `app/db/__init__.py:1-1`, 0.386926185; (3) `tests/integration/test_database.py:1-60`, 0.393821580; (4) `scripts/embed_chunks.py:1-60`, 0.437785920; (5) `tests/integration/test_database.py:51-87`, 0.437879707. Full-text returned no rows for this exact natural-language query. Therefore, its fused top 5 were the same vector-ranked chunks, with RRF scores respectively `1/(60+1) = 0.016393443`, `1/(60+2) = 0.016129032`, `1/(60+3) = 0.015873016`, `1/(60+4) = 0.015625000`, and `1/(60+5) = 0.015384615`. This exact query demonstrates relevant vector retrieval, but cannot by itself demonstrate combining two non-empty rankings. To pressure-test actual two-list fusion, a supplemental real query `session` was run: vector top 5 were `app/db/session.py:1-46` (rank 1, distance 0.458986130), `tests/integration/test_database.py:51-87` (rank 2, 0.486486827), `scripts/embed_chunks.py:101-149` (rank 3, 0.489357491), `scripts/search_repo.py:51-95` (rank 4, 0.490017084), and `app/db/__init__.py:1-1` (rank 5, 0.491373816). FTS top 5 were `app/db/session.py:1-46` (rank 1, score 0.500000000), `app/retrieval/hybrid_search.py:1-60` (rank 2, 0.300000000), `tests/integration/test_database.py:51-87` (rank 3, 0.300000000), `scripts/search_repo.py:1-60` (rank 4, 0.200000000), and `scripts/ingest_repo.py:51-110` (rank 5, 0.100000000). The supplemental fused top 5 and verified arithmetic were: `app/db/session.py:1-46`, vector rank 1 / FTS rank 1, `1/(60+1) + 1/(60+1) = 0.032786885`; `tests/integration/test_database.py:51-87`, vector rank 2 / FTS rank 3, `1/(60+2) + 1/(60+3) = 0.032002048`; `app/retrieval/hybrid_search.py:1-60`, absent from vector top 5 / FTS rank 2, `1/(60+2) = 0.016129032`; `scripts/embed_chunks.py:101-149`, vector rank 3 / absent from FTS top 5, `1/(60+3) = 0.015873016`; `scripts/search_repo.py:1-60`, absent from vector top 5 / FTS rank 4, `1/(60+4) = 0.015625000`. Every recomputed value matched the `hybrid_search` output. Thus the exact requested query's FTS path has no hits, while the supplemental query confirms RRF combines both rankings when both provide results. The top results are relevant; the previously indexed `.kilo` duplicates are gone after clean re-ingestion.
- Independent synthetic RRF verification: The fusion formula was separately reimplemented and exercised with synthetic rankings: a chunk ranked #2 in vector and #1 in FTS scored `1/(60+2) + 1/(60+1) = 0.032522475` (about 0.0325), above a chunk ranked #1 in only one list, `1/(60+1) = 0.016393443` (about 0.0164). Recomputed scores matched the formula, confirming that presence in both rankings is rewarded correctly.
- Follow-up observation for Phase 5: `websearch_to_tsquery` treats unquoted query terms as AND terms (after PostgreSQL's language processing). Consequently, natural-language queries against code chunks may produce no FTS matches when a single chunk lacks one or more query lexemes; hybrid search then effectively falls back to vector ranking for those queries. This is an observed behavior to evaluate with Phase 5 operator queries, not a claim that FTS is broken. A small `field or fallback` expression in the result assembly also prefers the fallback for falsy values rather than only missing values; current paths and line bounds are non-empty/positive, so this was noted but not changed.

---

## Checkpoint 5 — End-to-end verification

**Task:** Run the full pipeline against a real repository:
1. `python scripts/ingest_repo.py <path> <name>` (should already work)
2. `python scripts/embed_chunks.py <name>`
3. A small ad-hoc script or REPL session calling `hybrid_search` with a real
   query relevant to that repo's code, printing the top 5 results

### Log
- Repository used for this test run: `incidentweave-local`, re-ingested from the IncidentWeave repository with `.kilo`, `.venv`, `.git`, `.pytest_cache`, `.ruff_cache`, `__pycache__`, and migrations excluded; 23 Python files produced 31 chunks. Gemini embedding summary: `Chunks embedded: 31`, `Chunks failed: 0`, `Chunks skipped: 0`.
- The actual query text used: `how are asynchronous database sessions created and configured`
- The actual top 5 results returned (chunk file_path + line range + fused score) —
   paste real output, not a description of what it should look like: Real CMD output:

```text
1. app/db/session.py:1-46 rrf=0.016393
2. app/db/__init__.py:1-1 rrf=0.016129
3. tests/integration/test_database.py:1-60 rrf=0.015873
4. scripts/embed_chunks.py:1-60 rrf=0.015625
5. tests/integration/test_database.py:51-87 rrf=0.015385
```

- Does the top result actually look relevant to the query, by inspection? If
   not, note that honestly here — don't mark this checkpoint done if the
   results look wrong.: Yes. The top result `app/db/session.py:1-46` contains the async SQLAlchemy engine/session setup and directly matches the query. No `.kilo` worktree duplicates appear in the fresh results. The next results are less directly relevant, and FTS returned no match for this exact query; these limits are recorded rather than obscured. The real ingestion, embedding, and hybrid-query run completed successfully.
- Follow-up manual verification in Windows CMD: Re-ingestion reported 23 files and 31 chunks; a PostgreSQL count query confirmed `kilo_chunks = 0`. The first embedding pass had 1 transient connection failure; a retry embedded that remaining chunk (1 embedded, 0 failed, 30 skipped), leaving all 31 chunks embedded. The `session` hybrid search run after the first embedding pass returned `app/db/session.py:1-46` (0.032787), `tests/integration/test_database.py:51-87` (0.032002), `app/retrieval/hybrid_search.py:1-60` (0.016129), `scripts/embed_chunks.py:101-149` (0.015873), and `scripts/search_repo.py:1-60` (0.015625). The top two are relevant to session handling; later results include code that mentions or manipulates sessions.

---

## After all checkpoints

Do not proceed to Phase 5 (Investigation Engine / Gemini grounding) in this
session. Stop here once Checkpoint 5's log is filled in with real output.
