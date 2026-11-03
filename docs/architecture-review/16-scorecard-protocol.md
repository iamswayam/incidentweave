# Retrieval and guard scorecard protocol (item 32)

## 1. Registration and scope

This protocol freezes retrieval and evidence-guard measures before the item 32a v1
development baseline and before the item 32b v2 development baseline. The scorecard is
offline: it reads only committed questions, manifest-selected fixtures, and cached
retrieval outputs. It makes no provider calls and uses no database.

The v1 scorecard contains exactly the three manifest repositories:
`incidentweave`, `batch-processing-service`, and `lifeos`. It selects each repository's
development split only and must fail closed for a held-out split or repository. V2
development repositories are added in item 32b, after item 31c freezes dataset v2.0.
The scorecard reports results separately for every repository and pooled.

## 2. Relevance and retrieval ranking

A retrieved chunk is relevant when its file and inclusive line range overlap at least one
gold span, using the existing `evaluation.metrics.is_relevant_span` rule. Relevance is
binary: a chunk either overlaps a gold span or it does not.

Report Hit@1, Hit@3, Hit@5, Hit@10, and Hit@20 over answerable questions. A hit is one
when at least one relevant chunk appears in the first k ranked chunks; otherwise it is
zero. Report the Wilson 95% interval for each hit proportion.

MRR is the mean reciprocal rank of the first span-relevant chunk, with misses scored zero.
Its cutoff is the existing control retrieval limit of five chunks; it is therefore
MRR@5. Ranks are one-based positions in the deterministic fused result order. Ties in
reciprocal-rank fusion score are ordered by vector rank, then full-text rank, then file
path, line start, and line end, matching `app.retrieval.hybrid_search.hybrid_search`.

nDCG@5 and nDCG@10 use binary gain and the discount `1 / log2(rank + 1)`. For each
answerable question, ideal DCG is the sum of those discounts for the first
`min(R, k)` ranks, where `R` is the number of distinct chunks in that repository's pinned
fixture corpus whose file and line ranges overlap any gold span for that question. The
committed v1 fixtures contain the complete pinned chunk corpus and all v1 development
gold spans overlap at least one fixture chunk, so they provide the inputs needed to
compute `R`. If a future fixture lacks corpus chunks needed to establish `R`, the
scorecard must fail rather than assume an ideal ranking.

Recall@20 is the fraction of a question's distinct gold spans overlapped by at least one
chunk in the first 20 results, averaged over answerable questions. Context precision@5 is
the fraction of the first five retrieved chunks that are relevant, averaged over
answerable questions; questions with no returned chunks have precision zero.

## 3. Guard measures

The provisional vector-distance threshold is `0.5`. A question is refused if the evidence
guard refuses it and accepted otherwise. For descriptive threshold calculations, the
guard accepts when the minimum non-null vector distance among returned chunks is at or
below the cutoff; a missing distance means refusal. RRF is a ranking signal, not a
sufficiency gate.

Report per repository and pooled:

- False-accept rate: unanswerable questions accepted / all unanswerable questions.
- Correct-refusal rate: unanswerable questions refused / all unanswerable questions.
- False-refusal rate: answerable questions refused / all answerable questions.
- Refusal precision and recall, with refusal as the positive class.
- AUROC for separating unanswerable from answerable questions using the best (minimum)
  vector distance, where larger distances indicate the positive, unanswerable class.
  Equal scores receive average ranks (equivalently, half credit for each positive-negative
  tie).
- A descriptive threshold sweep from `0.300` through `0.700` inclusive in increments of
  `0.025`, with false-accept and false-refusal counts, denominators, and rates at each
  point.
- A guard-outcome breakdown for unanswerable kinds present in the data, including `far`
  and `near-miss`/`near` where available.

The sweep is descriptive; the threshold is not tuned on development data. It is
re-validated once in item 3b on the authorized held-out data.

## 4. Intervals and reporting

Use Wilson 95% intervals for proportions. Use per-question, percentile-bootstrap 95%
intervals for means and AUROC with seed `20261031` and 10,000 resamples. Resample
questions within each repository; preserve answerability-class counts within a repository
when bootstrapping AUROC so every replicate has both classes. For pooled results, sample
within repository strata, retaining each repository's original question count before
pooling. Report the numerator and denominator or question count `n` with every value and
interval. If a metric is undefined for the selected data, report it as unavailable with
the reason rather than substituting a value.

## 5. Registered cross-check

Before reporting the new metrics, reproduce the published pooled development control
values from `evaluation/experiments/bm25/results.json` or the same committed fixtures:
Hit@1 = 19/33, Hit@3 = 26/33, Hit@5 = 28/33, MRR = 0.673737 (reported as 0.674),
correct guard refusals = 9/15, and false accepts = 6/15. The BM25 artifact must identify
`metadata.split` as `development` and `metadata.held_out_used` as `false`. A mismatch is
a failure to explain and resolve, not a value to hide or silently reconcile.

## 6. Exclusions

This scorecard does not measure latency, cost, or errors (item 33), citation validity or
stability (item 34), or answer faithfulness and correctness (item 17).
