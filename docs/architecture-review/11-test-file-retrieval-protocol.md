# Test-file retrieval protocol (item 14b)

## Question and status

Determine whether and how test-file chunks should be treated in the final retrieval ranking.
Commit this protocol before implementing or running either ranking variant.

## Control

The control is current production retrieval: hybrid vector and PostgreSQL full-text search with
RRF fusion and deterministic tie-breaks. Use the current 14c-3 full-text behavior unchanged,
S0 60/10 chunks, cached fixture embeddings, and a top-five result list for every question.
Use only the frozen development split: 16 questions per repository, including 11 answerable
questions per repository. Do not run or inspect the held-out split.

## Test-file definition and reviewed paths

Use the exact rule implemented by
[`evaluation/test_files.py`](../../evaluation/test_files.py): normalize backslashes to forward
slashes and lowercase the path; tag a file if any directory segment is exactly `test`, `tests`,
`__tests__`, `spec`, or `specs`; or if its filename matches `test_*.py`, `*_test.py`,
`conftest.py`, `*.test.*`, `*.spec.*`, `tests.py`, `*Test.java`, or `*Tests.java` (case
insensitive).

The diagnostic's sorted, distinct tagged paths are:

| Repository | Tagged paths |
|---|---|
| `incidentweave` | `tests/conftest.py`; `tests/integration/test_database.py`; `tests/integration/test_database_models_integration.py`; `tests/unit/test_db_models.py`; `tests/unit/test_health.py`; `tests/unit/test_hybrid_search.py`; `tests/unit/test_ingest_repo.py`; `tests/unit/test_investigation_graph.py`; `tests/unit/test_investigation_mcp_tools.py`; `tests/unit/test_investigation_parsing.py`; `tests/unit/test_investigation_persistence.py` |
| `batch-processing-service` | `tests/conftest.py`; `tests/test_api.py`; `tests/test_idempotency.py`; `tests/test_rate_limiter.py`; `tests/test_worker.py` |
| `lifeos` | `apps/accounts/tests.py`; `apps/interviews/tests.py`; `apps/journal/tests.py`; `apps/todos/tests.py` |

The diagnostic found no untagged fixture paths containing the substring `test` in any of the
three repositories. Any path changed during maintainer review must be updated in the classifier
and reviewed here before variants run.

## Variants

Compare exactly these two variants with the control:

| Variant | Change |
|---|---|
| V1 downweight | After fusion, multiply the fused score of every chunk tagged test by `0.5`, then re-sort using the existing deterministic tie-break. |
| V2 exclude | Drop chunks tagged test from the candidate list before the top-k cut. |

Evaluate the evidence guard on each resulting top-k list, exactly as production would.

## Metrics

The primary metric is pooled development MRR using the existing substring labels. Report
per-repository answerable Hit@5 success counts. Secondary metrics are Hit@1, Hit@3, spans MRR,
test share of top-five results, test-source recall (the number of answerable questions whose
labeled evidence is in a test file and that hit at rank <=5), and test precision (the share of
top-five test chunks for answerable questions that overlap a labeled evidence span by file and
line range).

The control diagnostic found zero answerable questions with labeled evidence spans in test files
in each repository, so the denominator for test-source recall is zero in this development set.

**Maintainer review.** Keep R5's one-question tolerance exactly as registered below, but decide
before 14b-2 whether its zero-denominator result is treated as vacuously no decrease or whether
the comparison pauses for a reviewed test-file evidence stratum. The available diagnostic cannot
measure a test-source-recall loss with no such questions; this paragraph does not change the
threshold.

## Decision rule

A variant is retained only if every condition holds:

| Rule | Required condition |
|---|---|
| R1 | Pooled MRR improves by at least `0.03`. |
| R2 | The lower bound of the 95% paired-bootstrap confidence interval for pooled MRR difference is above `0`. |
| R3 | In every repository, answerable Hit@5 successes do not decrease (tolerance: 0 questions). |
| R4 | In every repository, the evidence-guard decision for every unanswerable development question is unchanged or improved (tolerance: 0 questions). A change from sufficient to insufficient is an improvement; a change from insufficient to sufficient is a regression. |
| R5 | Pooled test-source recall decreases by at most 1 question. |

If both variants pass, retain V1 as the milder change. If neither passes, keep the control and
close the item as no change.

## Statistics

Use paired bootstrap resampling over answerable questions, with seed `20261031`, `10000`
resamples, and a 95% interval. Report the exact two-sided sign test descriptively only; it is
never part of the decision rule.

## Safeguards and scope

Use no held-out data. Do not change chunking, lexical settings, or the evidence-guard threshold.
Run offline from committed fixtures with no provider calls. Production adoption—including a
`document_type` column, migration, and ingestion change—is a separate later item and proceeds
only if a variant is retained.

## Outputs for 14b-2

Commit the machine-readable results JSON, a report, and a notes file recording the registered
decision.

## Limits

The comparison covers 48 development questions across three small repositories by one author:
33 answerable questions and 15 unanswerable questions. Tolerances are in whole questions because
one rank change moves pooled MRR by about `0.015`. Results do not generalize beyond these
repositories.
