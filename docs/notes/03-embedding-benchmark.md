# Embedding Benchmark

**Purpose:** Measure the item 10 batch embedding path.

**Date:** 2026-10-24

**Command:** `scripts.benchmark_embeddings incidentweave-local --count 50 --single-sample 20`

`--count 100` was requested, but the repository has only 72 chunks.

| Mode | Chunks | Time | Throughput |
|---|---:|---:|---:|
| Single sequential | 20 | 140.816 s | 0.14 chunks/s |
| Batch concurrent | 50 | 3.741 s | 13.37 chunks/s |
| Retries | 0 | — | — |

**Defaults in effect:** batch size 50; concurrency 4.

## Limits of this measurement

- One run, one machine, one repository.
- The single run came first (cold connection) and creates a client per call.
- Chunk counts differ (20 vs 50).
- About 7 s per single request was not investigated and is not explained.
- No throughput promise is made from this note.
