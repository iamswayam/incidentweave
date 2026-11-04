# Evaluation metrics reference

**As of 2026-11-04.**

## 1. How to read this scorecard

These are provisional v1 development results, not held-out results. The scorecard uses
48 questions across `batch-processing-service`, `incidentweave`, and `lifeos`: 33
answerable questions for retrieval metrics and 15 unanswerable questions for guard
metrics. Wilson intervals are used for proportions; percentile-bootstrap intervals are
used for means and AUROC. Bootstrap resampling uses seed `20261031`, 10,000 resamples,
and repository strata. Each row reports its applicable sample size, retrieval view,
dataset version, scoring commit, run date, and source JSON.

The **production view** uses retrieval limit 5 and is the only view compared with the
published control. The **deep view** uses limit 20 for diagnostic-depth metrics; its
values are not compared with published control values. The exported best vector distance
and guard decision are shared across both views. The scorecard refuses held-out data.

## 2. Current results

Values and intervals below are rounded to three decimals from the scorecard JSON. For
proportions, the value includes successes/denominator; `n` is the denominator (or the
number of questions for AUROC). The AUROC positive class is unanswerable.

### Pooled

| Metric | Value | 95% interval | n | View | Dataset version | Git commit | Run date | Source file |
|---|---:|---|---:|---|---|---|---|---|
| Hit@1 | 19/33 (0.576) | [0.408, 0.728] | 33 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| Hit@3 | 26/33 (0.788) | [0.622, 0.893] | 33 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| Hit@5 | 28/33 (0.848) | [0.691, 0.933] | 33 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| MRR@5 | 0.674 | [0.543, 0.800] | 33 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| nDCG@5 | 0.708 | [0.590, 0.822] | 33 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| Context precision@5 | 0.206 | [0.170, 0.242] | 33 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| Hit@10 | 33/33 (1.000) | [0.896, 1.000] | 33 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| Hit@20 | 33/33 (1.000) | [0.896, 1.000] | 33 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| nDCG@10 | 0.754 | [0.660, 0.845] | 33 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| Recall@20 | 0.985 | [0.955, 1.000] | 33 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| False-accept rate | 6/15 (0.400) | [0.198, 0.643] | 15 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| Correct-refusal rate | 9/15 (0.600) | [0.357, 0.802] | 15 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| False-refusal rate | 0/33 (0.000) | [0.000, 0.104] | 33 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| Refusal precision | 9/9 (1.000) | [0.701, 1.000] | 9 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| Refusal recall | 9/15 (0.600) | [0.357, 0.802] | 15 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| AUROC | 0.893 | [0.790, 0.976] | 48 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| Far refusal rate | 9/9 (1.000) | [0.701, 1.000] | 9 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| Near-miss refusal rate | 0/6 (0.000) | [0.000, 0.390] | 6 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |

### Per repository

| Repository | Metric | Value | 95% interval | n | View | Dataset version | Git commit | Run date | Source file |
|---|---|---:|---|---:|---|---|---|---|---|
| batch-processing-service | Hit@1 | 6/11 (0.545) | [0.280, 0.787] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | Hit@3 | 9/11 (0.818) | [0.523, 0.949] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | Hit@5 | 10/11 (0.909) | [0.623, 0.984] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | MRR@5 | 0.685 | [0.461, 0.894] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | nDCG@5 | 0.713 | [0.512, 0.885] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | Context precision@5 | 0.273 | [0.182, 0.364] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | Hit@10 | 11/11 (1.000) | [0.741, 1.000] | 11 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | Hit@20 | 11/11 (1.000) | [0.741, 1.000] | 11 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | nDCG@10 | 0.739 | [0.577, 0.886] | 11 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | Recall@20 | 0.955 | [0.864, 1.000] | 11 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | False-accept rate | 2/5 (0.400) | [0.118, 0.769] | 5 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | Correct-refusal rate | 3/5 (0.600) | [0.231, 0.882] | 5 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | False-refusal rate | 0/11 (0.000) | [0.000, 0.259] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | Refusal precision | 3/3 (1.000) | [0.438, 1.000] | 3 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | Refusal recall | 3/5 (0.600) | [0.231, 0.882] | 5 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | AUROC | 0.873 | [0.636, 1.000] | 16 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | Far refusal rate | 3/3 (1.000) | [0.438, 1.000] | 3 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| batch-processing-service | Near-miss refusal rate | 0/2 (0.000) | [0.000, 0.658] | 2 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | Hit@1 | 5/11 (0.455) | [0.213, 0.720] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | Hit@3 | 7/11 (0.636) | [0.354, 0.848] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | Hit@5 | 7/11 (0.636) | [0.354, 0.848] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | MRR@5 | 0.515 | [0.242, 0.788] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | nDCG@5 | 0.545 | [0.273, 0.818] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | Context precision@5 | 0.127 | [0.073, 0.182] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | Hit@10 | 11/11 (1.000) | [0.741, 1.000] | 11 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | Hit@20 | 11/11 (1.000) | [0.741, 1.000] | 11 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | nDCG@10 | 0.657 | [0.472, 0.848] | 11 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | Recall@20 | 1.000 | [1.000, 1.000] | 11 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | False-accept rate | 2/5 (0.400) | [0.118, 0.769] | 5 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | Correct-refusal rate | 3/5 (0.600) | [0.231, 0.882] | 5 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | False-refusal rate | 0/11 (0.000) | [0.000, 0.259] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | Refusal precision | 3/3 (1.000) | [0.438, 1.000] | 3 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | Refusal recall | 3/5 (0.600) | [0.231, 0.882] | 5 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | AUROC | 0.927 | [0.782, 1.000] | 16 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | Far refusal rate | 3/3 (1.000) | [0.438, 1.000] | 3 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| incidentweave | Near-miss refusal rate | 0/2 (0.000) | [0.000, 0.658] | 2 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | Hit@1 | 8/11 (0.727) | [0.434, 0.903] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | Hit@3 | 10/11 (0.909) | [0.623, 0.984] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | Hit@5 | 11/11 (1.000) | [0.741, 1.000] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | MRR@5 | 0.821 | [0.630, 1.000] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | nDCG@5 | 0.865 | [0.720, 1.000] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | Context precision@5 | 0.218 | [0.200, 0.255] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | Hit@10 | 11/11 (1.000) | [0.741, 1.000] | 11 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | Hit@20 | 11/11 (1.000) | [0.741, 1.000] | 11 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | nDCG@10 | 0.865 | [0.720, 1.000] | 11 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | Recall@20 | 1.000 | [1.000, 1.000] | 11 | deep | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | False-accept rate | 2/5 (0.400) | [0.118, 0.769] | 5 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | Correct-refusal rate | 3/5 (0.600) | [0.231, 0.882] | 5 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | False-refusal rate | 0/11 (0.000) | [0.000, 0.259] | 11 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | Refusal precision | 3/3 (1.000) | [0.438, 1.000] | 3 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | Refusal recall | 3/5 (0.600) | [0.231, 0.882] | 5 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | AUROC | 0.964 | [0.836, 1.000] | 16 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | Far refusal rate | 3/3 (1.000) | [0.438, 1.000] | 3 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |
| lifeos | Near-miss refusal rate | 0/2 (0.000) | [0.000, 0.658] | 2 | production | v1 | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` | 2026-11-04 | `evaluation/experiments/scorecard/v1-development.json` |

## 3. Metric definitions

- **Hit@k:** share of answerable questions with a span-overlapping chunk in the first k results.
- **MRR@5:** mean reciprocal rank of the first relevant chunk, with misses scored zero.
- **nDCG@k:** binary-gain discounted cumulative gain normalized by the ideal ranking.
- **Recall@20:** fraction of distinct gold spans covered by the deep view's first 20 chunks.
- **Context precision@5:** share of the production view's first five chunks that are relevant.
- **False accept/refusal and correct refusal:** guard outcomes at the registered vector-distance threshold.
- **Refusal precision/recall:** refusal is the positive class.
- **AUROC:** separation of answerable and unanswerable questions by best vector distance; score ties receive half credit.

See the [registered scorecard protocol](../architecture-review/16-scorecard-protocol.md)
for formulas, cutoffs, tie handling, view assignment, threshold sweep, and interval methods.

## 4. Not measured and why

- **Throughput:** a load test would primarily measure the provider's rate limit rather than
  the offline scorecard.
- **p99 latency:** defer until at least 1,000 requests are available.
- **Availability:** no service-level or uptime measurement is part of this scorecard.
- Cost, operational errors, citation validity and stability, faithfulness, and answer
  correctness are outside this scorecard's scope.

## 5. Planned

- Item 33: operational latency, usage, cost, error, degradation, and cache metrics.
- Item 34: citation validity and end-to-end stability.
- Item 17: answer faithfulness and correctness.
- Item 3b: one registered v2 held-out evaluation and guard-threshold re-validation.
- Item 32b: final v2 development baseline after item 31c and frozen before item 3b.

## 6. History

| Date | Change | Commit |
|---|---|---|
| 2026-11-04 | Added dual-view scoring and generated the provisional v1 development scorecard. | `7d235785a6af453d0adbc4b0a168c1e74ad015c3` |
