# Retrieval ablation protocol (item 14)

## Purpose and status

This protocol preregisters the retrieval comparisons for checklist items 14c-2 and 14c-3.
It follows the diagnostic in [note 08](../notes/08-fulltext-diagnostic.md). No variant,
database migration, or retrieval-code change is part of item 14c-1. Register and commit this
protocol before implementing any variant.

## Control

Use current production retrieval after item 13d's deterministic ordering, the development split,
all three manifest repositories, S0 60/10 chunks, and the committed cached embeddings. Keep
retrieval limits, labels, score fusion, and all non-tested settings fixed.

## Variants

Each row changes one component relative to its stated comparator.

| Variant | Change | Comparison |
|---|---|---|
| c1 | Build a websearch OR query from sanitized question keywords and identifiers only. | c1 versus control |
| c2 | Apply c1, plus split `snake_case` and `camelCase` identifiers in chunk text for searchable text. File-path tokens are **not** included in c2 searchable text. | c2 versus c1 |
| c3 | Add a generated `tsvector` column and GIN index for the existing searchable text. | Query-time versus generated-vector equivalence and performance only; no retrieval-quality claim or adoption decision. |

BM25 is item 14d; test-file policy is item 14b; embedding task type is item 14a. They are out of
scope for these comparisons.

## Query safety and construction

Tokenize question text with `[A-Za-z0-9_]+`, preserving first-occurrence order and removing
duplicates case-insensitively. For c1, drop terms that PostgreSQL's English configuration
identifies as stop words; retain other keywords and identifiers. Quote each token and join them
with `OR`. Cap each query at 32 unique tokens after stop-word removal; if a question exceeds the
cap, truncate deterministically and record the truncation in the run report. Do not interpolate
source text into SQL; bind all values as query parameters. Do not include file paths in c2. Keep
the tokenization, stop-word rule, cap, and searchable-text version fixed and reported for a run.

## Metrics and decision rule

For each variant, report per-repository and pooled development span Hit@1/3/5 and MRR, the share
of answerable questions with a non-empty text branch, the share of top-five results from `tests/`
(reported only, not a gate), and mean/p95 unique raw source characters in the top five after
de-duplicating overlapping file-line ranges. Report the exact paired sign test on per-question
reciprocal-rank changes; it is descriptive and does not gate.

Use paired bootstrap resampling with seed `20261026`, `10000` resamples, and a 95% interval, as in
[the chunking comparison plan](./07-chunking-comparison-plan.md).

A quality variant is kept only if, versus control, no repository loses more than one Hit@5
success, no repository loses more than `0.03` span MRR, pooled span delta-MRR is at least `+0.02`,
and the share of answerable questions with a non-empty text branch is larger. Apply all four
conditions; otherwise retain the current behavior. c3 is a storage/query performance comparison
only and cannot be selected as a quality winner.

## Safety and limits

Use the development split only; leave held-out questions unobserved. Record the result and decision
before adoption. Refresh baselines only in the adoption PR, with gate tolerances unchanged.
There are 33 development answerable questions across tiny, single-author repositories, so results
may not transfer to other repositories or query distributions.
