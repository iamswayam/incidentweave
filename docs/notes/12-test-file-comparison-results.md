# Test-file retrieval comparison results

## Registration and method

Protocol: [11-test-file-retrieval-protocol.md](../architecture-review/11-test-file-retrieval-protocol.md).
Protocol commit: `8c411e2fd1ed549dd3c4af393e98ea344cc05169`.
Only the 16 development questions per repository were selected through the existing development split helper. Before any variant ran, the control was checked against the committed development `label_rank`: all 33 answerable ranks matched.

The control candidate pool is the full union of the production vector and full-text branch top fives (up to ten fused candidates). V1 and V2 are applied before the final top-five cut. The production evidence guard is applied unchanged to each resulting top five. No provider calls or production retrieval changes were made.

## Preregistered ambiguity readings

- Control candidate depth is the union of the two production top-five branch lists; this preserves the complete fused candidate pool for reranking.
- Guard improvement/regression follows the protocol: sufficient to insufficient is an improvement; insufficient to sufficient is a regression.
- R5 has a zero test-evidence denominator. It is not evaluable, and therefore is neither a pass nor a failure; it cannot satisfy the retention rule. V2 additionally requires R6, for which no separate registered stratum exists.
- Paired bootstrap percentiles use linear interpolation; the exact sign test excludes tied per-question reciprocal-rank differences.

## Per-repository and pooled metrics

Hit@k entries are successes over answerable questions. Test share uses all development questions' top-five results. Test precision is overlapping labeled test-file spans over answerable top-five test chunks. Test-source recall is not evaluable when its development evidence denominator is zero.

| Scope | Method | Answerable | Hit@1 | Hit@3 | Hit@5 | MRR | Span MRR | Test top-five share | Test-source recall (hits/denominator) | Test precision (overlaps/chunks) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| incidentweave | control | 11 | 5 | 7 | 7 | 0.515152 | 0.515152 | 37/80 (0.462500) | not evaluable (0 denominator) | 0/24 (0.000000) |
| incidentweave | V1 | 11 | 5 | 7 | 7 | 0.545455 | 0.545455 | 36/80 (0.450000) | not evaluable (0 denominator) | 0/23 (0.000000) |
| incidentweave | V2 | 11 | 5 | 7 | 7 | 0.545455 | 0.545455 | 0/44 (0.000000) | not evaluable (0 denominator) | not evaluable (0 chunks) |
| batch-processing-service | control | 11 | 6 | 9 | 10 | 0.684848 | 0.684848 | 27/80 (0.337500) | not evaluable (0 denominator) | 0/19 (0.000000) |
| batch-processing-service | V1 | 11 | 7 | 9 | 10 | 0.750000 | 0.750000 | 27/80 (0.337500) | not evaluable (0 denominator) | 0/19 (0.000000) |
| batch-processing-service | V2 | 11 | 7 | 9 | 10 | 0.750000 | 0.750000 | 0/53 (0.000000) | not evaluable (0 denominator) | not evaluable (0 chunks) |
| lifeos | control | 11 | 8 | 10 | 11 | 0.821212 | 0.821212 | 9/80 (0.112500) | not evaluable (0 denominator) | 0/5 (0.000000) |
| lifeos | V1 | 11 | 9 | 11 | 11 | 0.878788 | 0.878788 | 7/80 (0.087500) | not evaluable (0 denominator) | 0/3 (0.000000) |
| lifeos | V2 | 11 | 9 | 11 | 11 | 0.878788 | 0.878788 | 0/73 (0.000000) | not evaluable (0 denominator) | not evaluable (0 chunks) |
| Pooled | control | 33 | 19 | 26 | 28 | 0.673737 | 0.673737 | 73/240 (0.304167) | not evaluable (0 denominator) | 0/48 (0.000000) |
| Pooled | V1 | 33 | 21 | 27 | 28 | 0.724747 | 0.724747 | 70/240 (0.291667) | not evaluable (0 denominator) | 0/45 (0.000000) |
| Pooled | V2 | 33 | 21 | 27 | 28 | 0.724747 | 0.724747 | 0/170 (0.000000) | not evaluable (0 denominator) | not evaluable (0 chunks) |

## Paired pooled MRR statistics

The difference is variant MRR minus control MRR. Bootstrap uses 10,000 paired resamples of the 33 answerable questions, seed `20261031`; sign-test results are descriptive only.

| Variant | MRR difference | 95% paired bootstrap percentile interval | Sign test positive / negative / ties | Exact two-sided p-value |
|---|---:|---|---|---:|
| V1 | 0.051010 | [0.014646, 0.098497] | 7 / 0 / 26 | 0.015625 |
| V2 | 0.051010 | [0.014646, 0.098497] | 7 / 0 / 26 | 0.015625 |

## Evidence-guard comparison

The committed baseline stores no guard decision. The guard control below is the production `evaluate_evidence_sufficiency` function applied to each reconciled control top five; the same function and threshold are used for both variants.

A top five is sufficient when at least one result has vector cosine distance at or below the unchanged provisional threshold `0.5`; RRF is not the guard threshold.

| Repository | Control sufficient / insufficient | Variant | Unanswerable questions | Unchanged | Improved | Regressed | Changed development ordinals |
|---|---|---|---:|---:|---:|---:|---|
| incidentweave | 2 / 3 | V1 | 5 | 5 | 0 | 0 | none |
| incidentweave | 2 / 3 | V2 | 5 | 5 | 0 | 0 | none |
| batch-processing-service | 2 / 3 | V1 | 5 | 5 | 0 | 0 | none |
| batch-processing-service | 2 / 3 | V2 | 5 | 5 | 0 | 0 | none |
| lifeos | 2 / 3 | V1 | 5 | 5 | 0 | 0 | none |
| lifeos | 2 / 3 | V2 | 5 | 5 | 0 | 0 | none |

## Decision rules

A rule status of not-evaluable is not treated as a pass or a failure. Since all required conditions must hold, R5 cannot authorize retention on this development set when its denominator is zero.

| Variant | R1 | R2 | R3 | R4 | R5 | R6 | Passes all required rules |
|---|---|---|---|---|---|---|---|
| V1 | pass | pass | pass | pass | not-evaluable | not-evaluable | no |
| V2 | pass | pass | pass | pass | not-evaluable | fail | no |

**Mechanical outcome:** If V1 fails, keep the control and close the item as no change; V2 never overrides this without R6.

R5: not evaluable; labeled test-file evidence denominator is 0. R6: V2 is report-only because no separately registered test-evidence stratum exists.

## Limits

This comparison covers 33 answerable and 15 unanswerable development questions across three small repositories. The development set contains no answerable questions with labeled evidence in test files, so test-source recall has a zero denominator and removal-style policies cannot be penalized by this set. One rank change is about 0.015 pooled MRR. The guard threshold is provisional. The held-out split was untouched. Results are not generalizable beyond these repositories.
