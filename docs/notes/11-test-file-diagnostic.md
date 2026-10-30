# Test-file retrieval diagnostic

## Method

The classifier applies the path rules in `evaluation/test_files.py` to fixture chunk paths. Only development question records are decoded and selected through the manifest split helper. The control is the production hybrid retrieval: exact pgvector cosine ranking and PostgreSQL English full-text ranking, fused with RRF (constant 60) and the production deterministic tie-break. Fixture chunks are supplied through a query-local JSONB CTE; the query runs in a read-only PostgreSQL transaction and does not insert or modify rows. Cached fixture query embeddings are used; no provider is called.

## Held-out handling disclosure

During the review of item 14b-1, an assistant opened the first lines of the committed baseline files directly instead of through the development split helper. This exposed baseline row metadata for a small number of held-out rows and an all-split summary in a tool output. No held-out question text was opened, no held-out retrieval or provider call was run, and nothing exposed was used for any decision in this item. It is recorded here so the single registered held-out run in item 3b can take it into account. All later access to baseline and question files goes through the development split helper only.

## Control reconciliation

Baseline label ranks were compared only for the 11 answerable development questions per repository. Rank `—` means no substring match in the top five. Hit@5 and MRR use these 11 questions as the denominator, counting misses as zero for MRR. Unanswerable questions were not compared because the baseline rows expose no evidence-guard decision. The earlier aggregate comparison used all-split totals and is replaced by this development-only comparison.

| Repository | Answerable questions compared | Identical ranks | Baseline label_rank present | Differing ranks (ordinal: baseline → diagnostic) | Baseline hit@5; MRR | Diagnostic hit@5; MRR | Unanswerable guard | Verdict |
|---:|---:|---:|---:|---|---|---|---|---|
| incidentweave | 11 | 11 | 7 | none | 7; 0.515152 | 7; 0.515152 | not compared; baseline rows expose no evidence-guard decision | all answerable development ranks match |
| batch-processing-service | 11 | 11 | 10 | none | 10; 0.684848 | 10; 0.684848 | not compared; baseline rows expose no evidence-guard decision | all answerable development ranks match |
| lifeos | 11 | 11 | 11 | none | 11; 0.821212 | 11; 0.821212 | not compared; baseline rows expose no evidence-guard decision | all answerable development ranks match |

## Per-repository results

| Repository | Chunks | Tagged test chunks | Tagged share | Top-5 tagged test results | Top-5 results | Top-5 test share | Answerable questions with test-file evidence | Hit at rank <=5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| incidentweave | 70 | 20 | 28.6% | 37 | 80 | 46.2% | 0 | 0 |
| batch-processing-service | 38 | 14 | 36.8% | 27 | 80 | 33.8% | 0 | 0 |
| lifeos | 49 | 6 | 12.2% | 9 | 80 | 11.2% | 0 | 0 |
| **Pooled** | 157 | 40 | — | 73 | 240 | 30.4% | 0 | 0 |

### Tagged paths

#### `incidentweave`

- `tests/conftest.py`
- `tests/integration/test_database.py`
- `tests/integration/test_database_models_integration.py`
- `tests/unit/test_db_models.py`
- `tests/unit/test_health.py`
- `tests/unit/test_hybrid_search.py`
- `tests/unit/test_ingest_repo.py`
- `tests/unit/test_investigation_graph.py`
- `tests/unit/test_investigation_mcp_tools.py`
- `tests/unit/test_investigation_parsing.py`
- `tests/unit/test_investigation_persistence.py`

#### `batch-processing-service`

- `tests/conftest.py`
- `tests/test_api.py`
- `tests/test_idempotency.py`
- `tests/test_rate_limiter.py`
- `tests/test_worker.py`

#### `lifeos`

- `apps/accounts/tests.py`
- `apps/interviews/tests.py`
- `apps/journal/tests.py`
- `apps/todos/tests.py`

### Untagged paths containing `test` (manual review)

#### `incidentweave`

- (none)

#### `batch-processing-service`

- (none)

#### `lifeos`

- (none)

### Tagged test chunks in each development question's top five

| Repository | Development question ordinal | Tagged test chunks in top five |
|---|---:|---:|
| incidentweave | 1 | 4 |
| incidentweave | 2 | 1 |
| incidentweave | 3 | 0 |
| incidentweave | 4 | 2 |
| incidentweave | 5 | 1 |
| incidentweave | 6 | 5 |
| incidentweave | 7 | 3 |
| incidentweave | 8 | 1 |
| incidentweave | 9 | 1 |
| incidentweave | 10 | 3 |
| incidentweave | 11 | 3 |
| incidentweave | 12 | 5 |
| incidentweave | 13 | 2 |
| incidentweave | 14 | 0 |
| incidentweave | 15 | 3 |
| incidentweave | 16 | 3 |
| batch-processing-service | 1 | 2 |
| batch-processing-service | 2 | 1 |
| batch-processing-service | 3 | 3 |
| batch-processing-service | 4 | 2 |
| batch-processing-service | 5 | 0 |
| batch-processing-service | 6 | 2 |
| batch-processing-service | 7 | 2 |
| batch-processing-service | 8 | 2 |
| batch-processing-service | 9 | 0 |
| batch-processing-service | 10 | 3 |
| batch-processing-service | 11 | 2 |
| batch-processing-service | 12 | 3 |
| batch-processing-service | 13 | 2 |
| batch-processing-service | 14 | 0 |
| batch-processing-service | 15 | 1 |
| batch-processing-service | 16 | 2 |
| lifeos | 1 | 0 |
| lifeos | 2 | 0 |
| lifeos | 3 | 0 |
| lifeos | 4 | 0 |
| lifeos | 5 | 0 |
| lifeos | 6 | 0 |
| lifeos | 7 | 0 |
| lifeos | 8 | 0 |
| lifeos | 9 | 2 |
| lifeos | 10 | 2 |
| lifeos | 11 | 1 |
| lifeos | 12 | 2 |
| lifeos | 13 | 2 |
| lifeos | 14 | 0 |
| lifeos | 15 | 0 |
| lifeos | 16 | 0 |

## What this does not show

This is a descriptive control inventory, not a comparison of ranking variants and not evidence that test files should be downweighted or excluded. It does not measure answer quality, guard outcomes, or whether test-file evidence is preferable for a particular query. The small development fixtures do not establish generalization beyond these repositories.
