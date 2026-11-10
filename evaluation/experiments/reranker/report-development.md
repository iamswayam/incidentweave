# Reranker development report

Decision: **REJECT**

## Primary metric

Paired, repository-stratified 95% percentile bootstrap interval (seed 20261031; 10,000 resamples; linear interpolation).

| Scope | n | Baseline MRR@5 | Treatment MRR@5 | Difference | Paired 95% interval |
|---|---:|---:|---:|---:|---|
| batch-processing-service | 11 | 0.6666666666666666 | 0.6848484848484848 | 0.018181818181818177 | [-0.1970, 0.2273] |
| incidentweave | 11 | 0.5151515151515151 | 0.7045454545454546 | 0.1893939393939394 | [-0.0833, 0.4697] |
| lifeos | 11 | 0.8212121212121212 | 0.9545454545454546 | 0.13333333333333333 | [0.0000, 0.2818] |
| Pooled | 33 | 0.6676767676767676 | 0.7813131313131313 | 0.11363636363636363 | [-0.0131, 0.2414] |

## Decision conditions

- FAIL: MRR@5 paired 95% interval lower bound is not above zero
- FAIL: added median latency exceeds 500 ms or is unavailable
- FAIL: added p95 latency exceeds 1,500 ms or is unavailable

## Secondary retrieval metrics

| Metric | Baseline | Treatment | Difference | n | Wins | Losses | Ties | Sign-test p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| hit_at_1 | 0.5757575757575758 | 0.6666666666666666 | 0.09090909090909091 | 33 | 6 | 3 | 24 | 0.5078125 |
| hit_at_3 | 0.7878787878787878 | 0.8787878787878788 | 0.09090909090909091 | 33 | 5 | 2 | 26 | 0.453125 |
| hit_at_5 | 0.8181818181818182 | 0.9393939393939394 | 0.12121212121212122 | 33 | 4 | 0 | 29 | 0.125 |
| hit_at_10 | 1.0 | 0.9393939393939394 | -0.06060606060606061 | 33 | 0 | 2 | 31 | 0.5 |
| hit_at_20 | 1.0 | 1.0 | 0.0 | 33 | 0 | 0 | 33 | 1.0 |
| ndcg_at_5 | 0.6961855325350761 | 0.7854947782386249 | 0.08930924570354883 | 33 | - | - | - | - |
| ndcg_at_10 | 0.753728814815589 | 0.8025874087618515 | 0.04885859394626257 | 33 | - | - | - | - |
| recall_at_20 | 0.9848484848484849 | 0.9848484848484849 | 0.0 | 33 | - | - | - | - |
| context_precision_at_5 | 0.2 | 0.20606060606060608 | 0.006060606060606062 | 33 | - | - | - | - |
| test_file_share | 0.3090909090909091 | 0.24242424242424243 | -0.06666666666666667 | 33 | - | - | - | - |

## Guard metrics

| Scope | Metric | n | Baseline | Treatment |
|---|---|---:|---:|---:|
| batch-processing-service | guard.false_accept_rate | 5 | 0.4 | 0.4 |
| batch-processing-service | guard.correct_refusal_rate | 5 | 0.6 | 0.6 |
| batch-processing-service | guard.false_refusal_rate | 11 | 0.0 | 0.0 |
| batch-processing-service | guard.refusal_precision | 3 | 1.0 | 1.0 |
| batch-processing-service | guard.refusal_recall | 5 | 0.6 | 0.6 |
| incidentweave | guard.false_accept_rate | 5 | 0.4 | 0.4 |
| incidentweave | guard.correct_refusal_rate | 5 | 0.6 | 0.6 |
| incidentweave | guard.false_refusal_rate | 11 | 0.0 | 0.0 |
| incidentweave | guard.refusal_precision | 3 | 1.0 | 1.0 |
| incidentweave | guard.refusal_recall | 5 | 0.6 | 0.6 |
| lifeos | guard.false_accept_rate | 5 | 0.4 | 0.4 |
| lifeos | guard.correct_refusal_rate | 5 | 0.6 | 0.6 |
| lifeos | guard.false_refusal_rate | 11 | 0.0 | 0.0 |
| lifeos | guard.refusal_precision | 3 | 1.0 | 1.0 |
| lifeos | guard.refusal_recall | 5 | 0.6 | 0.6 |
| Pooled | guard.false_accept_rate | 15 | 0.4 | 0.4 |
| Pooled | guard.correct_refusal_rate | 15 | 0.6 | 0.6 |
| Pooled | guard.false_refusal_rate | 33 | 0.0 | 0.0 |
| Pooled | guard.refusal_precision | 9 | 1.0 | 1.0 |
| Pooled | guard.refusal_recall | 15 | 0.6 | 0.6 |

## Latency, cost, and errors

- Added latency: p50=1521.662 ms; p95=2138.404 ms (nearest-rank).
- Cost per 1,000 queries: 0.0 USD.
- Estimated list-price cost per operation: 0.0 USD per million tokens (https://huggingface.co/Qwen/Qwen3-Reranker-0.6B).
- Rerank failures with baseline fallback: 0.

## Per-question paired differences

| Repository | Question | Added latency (ms) | Tokens | Estimated cost (USD) | Fallback | Metric differences |
|---|---|---:|---:|---:|---|---|
| batch-processing-service | direct-01 | 2112.266 | 10982 | 0.0 | False | `{"context_precision_at_5": -0.2, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": -0.18247040964605554, "ndcg_at_5": -0.38685280723454163, "recall_at_20": 0.0, "test_file_share": 0.19999999999999996}` |
| batch-processing-service | direct-02 | 2148.078 | 10996 | 0.0 | False | `{"context_precision_at_5": 0.2, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 1.0, "hit_at_5": 1.0, "mrr_at_5": 0.5, "ndcg_at_10": 0.27472256646343535, "ndcg_at_5": 0.6309297535714575, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| batch-processing-service | direct-03 | 1956.927 | 9796 | 0.0 | False | `{"context_precision_at_5": -0.2, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": -0.16844537041637753, "ndcg_at_5": -0.38685280723454163, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| batch-processing-service | direct-05 | 2138.404 | 9829 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": 0.0, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| batch-processing-service | direct-07 | 2030.177 | 9392 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": 0.0, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| batch-processing-service | direct-08 | 2044.205 | 10306 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 1.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.5, "ndcg_at_10": 0.36907024642854247, "ndcg_at_5": 0.36907024642854247, "recall_at_20": 0.0, "test_file_share": -0.2}` |
| batch-processing-service | paraphrased-01 | 2139.068 | 11047 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": -1.0, "hit_at_5": 0.0, "mrr_at_5": -0.1333333333333333, "ndcg_at_10": -0.11314719276545837, "ndcg_at_5": -0.11314719276545837, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| batch-processing-service | paraphrased-03 | 2101.96 | 11197 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": -1.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": -0.31546487678572877, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": 0.19999999999999996}` |
| batch-processing-service | paraphrased-04 | 2033.121 | 10613 | 0.0 | False | `{"context_precision_at_5": -0.19999999999999996, "hit_at_1": 1.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.5, "ndcg_at_10": 0.19436454333385456, "ndcg_at_5": 0.053097570474025524, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| batch-processing-service | paraphrased-05 | 2032.419 | 10775 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": -1.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": -0.6666666666666667, "ndcg_at_10": -0.3065735963827292, "ndcg_at_5": -0.3065735963827292, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| batch-processing-service | paraphrased-07 | 2027.064 | 11257 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": -1.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": -0.5, "ndcg_at_10": -0.34907907019286744, "ndcg_at_5": -0.34907907019286744, "recall_at_20": 0.0, "test_file_share": -0.2}` |
| batch-processing-service | unanswerable_far-01 | 1801.571 | 9238 | 0.0 | False | `{}` |
| batch-processing-service | unanswerable_far-02 | 1944.247 | 9239 | 0.0 | False | `{}` |
| batch-processing-service | unanswerable_far-04 | 1586.511 | 8718 | 0.0 | False | `{}` |
| batch-processing-service | unanswerable_near-01 | 1971.386 | 11246 | 0.0 | False | `{}` |
| batch-processing-service | unanswerable_near-02 | 1928.92 | 10956 | 0.0 | False | `{}` |
| incidentweave | direct-01 | 1436.381 | 8684 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": -1.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": -1.0, "hit_at_5": 0.0, "mrr_at_5": -0.75, "ndcg_at_10": -0.5693234419266069, "ndcg_at_5": -0.5693234419266069, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| incidentweave | direct-02 | 1470.422 | 7951 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": 0.0, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| incidentweave | direct-03 | 1394.057 | 9121 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": 0.0, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| incidentweave | direct-05 | 1508.986 | 9416 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.16666666666666669, "ndcg_at_10": 0.13092975357145753, "ndcg_at_5": 0.13092975357145753, "recall_at_20": 0.0, "test_file_share": -0.2}` |
| incidentweave | direct-07 | 1474.929 | 7116 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": 0.0, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| incidentweave | direct-08 | 1521.662 | 10027 | 0.0 | False | `{"context_precision_at_5": 0.2, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 1.0, "hit_at_5": 1.0, "mrr_at_5": 0.5, "ndcg_at_10": 0.2975964202381242, "ndcg_at_5": 0.6309297535714575, "recall_at_20": 0.0, "test_file_share": -0.8}` |
| incidentweave | paraphrased-01 | 1375.009 | 8301 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": 0.0, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| incidentweave | paraphrased-03 | 1472.955 | 8269 | 0.0 | False | `{"context_precision_at_5": 0.2, "hit_at_1": 1.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 1.0, "hit_at_5": 1.0, "mrr_at_5": 1.0, "ndcg_at_10": 0.6437928128919779, "ndcg_at_5": 1.0, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| incidentweave | paraphrased-04 | 1684.23 | 9818 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.16666666666666669, "ndcg_at_10": 0.13092975357145753, "ndcg_at_5": 0.13092975357145753, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| incidentweave | paraphrased-05 | 1685.097 | 10277 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": -1.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": -0.20438239758848611, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": -0.19999999999999996}` |
| incidentweave | paraphrased-07 | 1545.418 | 9195 | 0.0 | False | `{"context_precision_at_5": 0.2, "hit_at_1": 1.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 1.0, "hit_at_5": 1.0, "mrr_at_5": 1.0, "ndcg_at_10": 0.6666666666666667, "ndcg_at_5": 1.0, "recall_at_20": 0.0, "test_file_share": -0.39999999999999997}` |
| incidentweave | unanswerable_far-01 | 1677.068 | 8816 | 0.0 | False | `{}` |
| incidentweave | unanswerable_far-02 | 1529.985 | 9443 | 0.0 | False | `{}` |
| incidentweave | unanswerable_far-04 | 1686.843 | 9367 | 0.0 | False | `{}` |
| incidentweave | unanswerable_near-01 | 1479.199 | 7476 | 0.0 | False | `{}` |
| incidentweave | unanswerable_near-02 | 1557.44 | 10049 | 0.0 | False | `{}` |
| lifeos | direct-01 | 1483.689 | 7425 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": 0.0, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| lifeos | direct-02 | 1461.447 | 7522 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": 0.0, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": -0.4}` |
| lifeos | direct-03 | 1436.299 | 7678 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": 0.0, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| lifeos | direct-05 | 1458.377 | 6533 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": 0.0, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| lifeos | direct-07 | 1467.427 | 6439 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": 0.0, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| lifeos | direct-08 | 1533.553 | 6760 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": 0.0, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| lifeos | paraphrased-01 | 1502.703 | 8005 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": 0.0, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| lifeos | paraphrased-03 | 1487.617 | 6020 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 1.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.6666666666666667, "ndcg_at_10": 0.5, "ndcg_at_5": 0.5, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| lifeos | paraphrased-04 | 1483.469 | 6264 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 1.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.5, "ndcg_at_10": 0.36907024642854247, "ndcg_at_5": 0.36907024642854247, "recall_at_20": 0.0, "test_file_share": -0.2}` |
| lifeos | paraphrased-05 | 1494.338 | 6000 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 1.0, "hit_at_5": 0.0, "mrr_at_5": 0.3, "ndcg_at_10": 0.2440769463369159, "ndcg_at_5": 0.2440769463369159, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| lifeos | paraphrased-07 | 1487.774 | 5489 | 0.0 | False | `{"context_precision_at_5": 0.0, "hit_at_1": 0.0, "hit_at_10": 0.0, "hit_at_20": 0.0, "hit_at_3": 0.0, "hit_at_5": 0.0, "mrr_at_5": 0.0, "ndcg_at_10": 0.0, "ndcg_at_5": 0.0, "recall_at_20": 0.0, "test_file_share": 0.0}` |
| lifeos | unanswerable_far-01 | 1494.056 | 5836 | 0.0 | False | `{}` |
| lifeos | unanswerable_far-02 | 1503.117 | 6706 | 0.0 | False | `{}` |
| lifeos | unanswerable_far-04 | 1486.741 | 5936 | 0.0 | False | `{}` |
| lifeos | unanswerable_near-01 | 1461.847 | 6649 | 0.0 | False | `{}` |
| lifeos | unanswerable_near-02 | 1470.418 | 6575 | 0.0 | False | `{}` |
