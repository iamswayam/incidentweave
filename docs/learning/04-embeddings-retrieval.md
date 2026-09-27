# Embeddings & Hybrid Retrieval (Phase 4)

**Date built:** September 2026
**Status:** Drafted — review against the Phase 4 engineering log

## What I built

The ingestion pipeline's chunks can be embedded with Gemini's `gemini-embedding-001` model and stored as 768-dimensional vectors in PostgreSQL with pgvector. Retrieval combines cosine-distance vector search and PostgreSQL full-text search, then fuses their rankings with Reciprocal Rank Fusion (RRF). The search results carry each available raw score plus the fused score so later investigation and audit code can inspect the evidence.

## Why this design

I chose cosine distance for vector retrieval because it provides a direct semantic-similarity ranking for these embeddings; lower distance means more similar. I kept PostgreSQL full-text search beside vector search because literal code terms can be useful even when their embedding rank is weaker. RRF combines ranks rather than averaging raw scores: cosine distances and FTS rank scores have different meanings and scales, so treating them as directly comparable numbers would be misleading.

The embedding model was explicitly configured for 768 dimensions to match the existing `VECTOR(768)` schema. No vector index was added for the small V1 corpus; the phase log deferred index selection until measured scale or latency justifies it.

## Key concept, explained simply

An embedding represents text as a list of numbers so that text with related meaning can be compared geometrically. Cosine distance measures how far apart two vectors point: a smaller distance indicates greater similarity. Full-text search instead looks for matching words. RRF combines the order from both methods, rewarding a chunk that ranks well in both without pretending their raw scores are interchangeable.

## Walkthrough example

The live query `how are asynchronous database sessions created and configured` returned `app/db/session.py:1-46` first from vector search, at cosine distance `0.288488584`. Full-text search returned no rows for that exact query, so the fused results followed the vector ranking. The first RRF score was `1/(60+1) = 0.016393443`; the next scores were `0.016129032`, `0.015873016`, `0.015625000`, and `0.015384615`. A supplemental live query `session` returned rows from both methods; `app/db/session.py:1-46` ranked first in both and received `1/61 + 1/61 = 0.032786885`.

## What broke when I tested it

The original embedding request used `models/text-embedding-004` and received HTTP 404 because that model was not found or supported for `embedContent`. I switched to `models/gemini-embedding-001` and explicitly requested 768 output dimensions; the script validated each returned vector length before storage.

On the clean 31-chunk corpus, the first embedding run embedded 30 chunks and hit one transient connection failure. Rerunning the idempotent script embedded the remaining chunk and skipped the 30 already embedded. The phase log also records that the required natural-language query returned no FTS rows; hybrid retrieval still returned a relevant vector result. This means FTS should not be described as contributing to every query.

## Interview-ready summary (3-4 sentences)

I built retrieval around two complementary signals: pgvector cosine distance for semantic similarity and PostgreSQL full-text search for literal matches. I used RRF to combine their rankings without mixing incompatible raw-score scales. A real dimension mismatch risk led me to verify the embedding model and explicitly request 768 values to match the database column. Live tests confirmed relevant vector retrieval and also exposed that some natural-language queries produce no FTS results, which I recorded rather than hiding.
