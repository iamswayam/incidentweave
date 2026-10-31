# BM25 comparison protocol (item 14d)

## Purpose and registration

Compare a fixed Python BM25 lexical branch with the current hybrid retrieval control on the
development split. This protocol is committed before the BM25 implementation is run. No production
retrieval change is part of this comparison.

## Control

The control is current retrieval exactly as registered for the 14c control: PostgreSQL `ts_rank`
lexical branch plus vector branch, reciprocal-rank fusion (RRF), and deterministic ordering.

## Variants

| Arm | Definition | Eligibility |
|---|---|---|
| B1 | Python BM25 over the same chunk text, replacing only the lexical branch in the hybrid pipeline. Use fixed `k1=1.2` and `b=0.75`, with no tuning. Tokenize as lowercase alphanumeric runs; keep identifiers intact; do not stem or remove stop words. Match by OR over query tokens. Keep the control top-k and RRF settings. Resolve deterministic ties by file path, then start line. | The only candidate eligible for the registered decision. |
| C1 | The already-registered sanitized-OR `ts_rank` query. | Reference arm only; descriptive and never eligible for retention. |

## Data and metrics

Use the 33 answerable development questions across the three repositories. One rank change is
approximately `0.015` pooled MRR; all decision tolerances are expressed in whole questions.
Validate the control against the committed development baseline for every question before any
variant result is counted.

Report per-repository and pooled MRR and Hit@1/3/5 successes for the control, B1, and C1. Also
report lexical-branch-only hit rates descriptively, along with per-repository index build time and
per-query time for Python BM25 versus the SQL query. Cost measurements are reported, not decision
conditions.

Use paired bootstrap resampling over the 33 answerable questions with seed `20261031`, 10,000
resamples, and a 95% interval. Report the exact sign test as descriptive only.

## Decision rule

B1 is retained only if every condition below passes:

| Rule | Required condition |
|---|---|
| R1 | Pooled MRR improves over control by at least `0.030` (about two questions). |
| R2 | The lower bound of the paired-bootstrap 95% interval for pooled MRR difference is above `0`. |
| R3 | No repository loses more than one answerable Hit@5 success versus control. |
| R4 | In each repository, all three unanswerable development ordinals keep the same answer/refusal outcome as control. The evidence guard is vector-based; this is a safety check against an unintended outcome change. |

If R1-R4 all pass, the decision is: **candidate: a separately registered production comparison
(14d-2) is justified**. Otherwise, the decision is **keep control**. The exact sign test and
timing/cost results are descriptive and cannot override this rule.

BM25 is not adopted in this comparison. Production use would require either an in-app index or a
PostgreSQL extension; neither is built here.

## Scope and safeguards

Use the existing development split and fixture helpers only. Do not inspect held-out questions or
run provider calls. No database schema change or dependency is in scope. Report lexical-branch-only
hit rates as descriptive results; the registered decision is based on the hybrid pipeline.

## Limits

The comparison uses 33 answerable development questions from three small repositories by a single
author. Results may not generalize to other repositories or query distributions.
