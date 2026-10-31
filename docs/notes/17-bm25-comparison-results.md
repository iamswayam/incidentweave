# BM25 comparison results (item 14d)

## Protocol and method

Protocol: [12-bm25-comparison-protocol.md](../architecture-review/12-bm25-comparison-protocol.md).
Protocol commit: `a47e6fc0c981f28530a89c710bda12371f9d30e1`.
The comparison used committed S0 fixture chunks and cached query vectors through the development split helper. Before either lexical variant was evaluated, current hybrid control retrieval matched the committed baseline for all 33 answerable development questions, including label and span ranks and hit outcomes. No provider calls or held-out data were used.

B1 replaces only the lexical branch with the fixed Python BM25 index (`k1=1.2`, `b=0.75`), OR token matching, and path/start-line tie breaks. C1 is the sanitized-OR `ts_rank` reference arm and is descriptive only. Both retain top-k 5 and RRF constant 60.

## Per-repository and pooled hybrid metrics

| Scope | Arm | N | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---|---:|---:|---:|---:|---:|
| batch-processing-service | control | 11 | 6/11 | 9/11 | 10/11 | 0.684848 |
| batch-processing-service | B1 | 11 | 4/11 | 8/11 | 9/11 | 0.548485 |
| batch-processing-service | C1 | 11 | 5/11 | 7/11 | 9/11 | 0.566667 |
| incidentweave | control | 11 | 5/11 | 7/11 | 7/11 | 0.515152 |
| incidentweave | B1 | 11 | 3/11 | 5/11 | 7/11 | 0.389394 |
| incidentweave | C1 | 11 | 6/11 | 8/11 | 8/11 | 0.621212 |
| lifeos | control | 11 | 8/11 | 10/11 | 11/11 | 0.821212 |
| lifeos | B1 | 11 | 5/11 | 9/11 | 11/11 | 0.662121 |
| lifeos | C1 | 11 | 8/11 | 11/11 | 11/11 | 0.833333 |
| pooled | control | 33 | 19/33 | 26/33 | 28/33 | 0.673737 |
| pooled | B1 | 33 | 12/33 | 22/33 | 27/33 | 0.533333 |
| pooled | C1 | 33 | 19/33 | 26/33 | 28/33 | 0.673737 |

## Lexical-branch-only hit rates (descriptive)

| Scope | Arm | N | Hit@1 | Hit@3 | Hit@5 |
|---|---|---:|---:|---:|---:|
| batch-processing-service | control | 11 | 1/11 | 1/11 | 1/11 |
| batch-processing-service | B1 | 11 | 4/11 | 5/11 | 8/11 |
| batch-processing-service | C1 | 11 | 2/11 | 6/11 | 7/11 |
| incidentweave | control | 11 | 1/11 | 1/11 | 2/11 |
| incidentweave | B1 | 11 | 0/11 | 2/11 | 4/11 |
| incidentweave | C1 | 11 | 6/11 | 7/11 | 9/11 |
| lifeos | control | 11 | 1/11 | 2/11 | 2/11 |
| lifeos | B1 | 11 | 2/11 | 3/11 | 7/11 |
| lifeos | C1 | 11 | 3/11 | 6/11 | 10/11 |
| pooled | control | 33 | 3/33 | 4/33 | 5/33 |
| pooled | B1 | 33 | 6/33 | 10/33 | 19/33 |
| pooled | C1 | 33 | 11/33 | 19/33 | 26/33 |

## Paired pooled statistics and cost

B1 minus control MRR: `-0.140404`; 95% paired bootstrap interval: `[-0.237879, -0.048485]` (seed 20261031, 10,000 resamples).
Exact sign test (descriptive): 2 positive, 13 negative, 18 tied; two-sided `p=0.007385`.

| Repository | BM25 build ms | BM25 query mean ms | SQL C1 query mean ms |
|---|---:|---:|---:|
| batch-processing-service | 29.205 | 0.984 | 160.529 |
| incidentweave | 24.079 | 1.306 | 193.328 |
| lifeos | 22.756 | 0.510 | 99.410 |

The exact sign test and timing are descriptive, not decision conditions. SQL timing covers the C1 `ts_rank` statement after its sanitized query has been constructed; BM25 query timing excludes index construction.

## Guard outcomes and registered decision

| Repository | Unanswerable N | Control sufficient/insufficient | B1 unchanged | Changed ordinals |
|---|---:|---:|---:|---|
| batch-processing-service | 5 | 2/3 | 5 | none |
| incidentweave | 5 | 2/3 | 5 | none |
| lifeos | 5 | 2/3 | 5 | none |

R4 compares every unanswerable development question returned by the registered split helper. The manifest currently supplies five per repository; this conservatively checks all of them against the protocol's three-ordinal safety condition.

| Rule | Condition | Result |
|---|---|---|
| R1 | Pooled MRR improves by at least 0.030. | fail |
| R2 | Paired bootstrap 95% interval lower bound is above zero. | fail |
| R3 | No repository loses more than one Hit@5 success. | pass |
| R4 | All unanswerable development guard outcomes are unchanged. | pass |

**Mechanical decision:** keep control.

BM25 is not adopted in this comparison. Production use would require either an in-app index or a PostgreSQL extension; neither is built here.

## Honest limits

The comparison covers 33 answerable development questions from three small repositories by a single author. It is not evidence of general performance on other codebases or query distributions. Results are development-only; the held-out split was untouched.

Machine-readable aggregate report: [evaluation/experiments/bm25/results.json](../../evaluation/experiments/bm25/results.json).
