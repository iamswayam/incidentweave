# Full-text ablation results (item 14c-2)

## Method

The control, c1 and c2 runs used the committed S0 retrieval fixtures, their cached query
embeddings, the local PostgreSQL database and the development split. The control was run
first. For each of the three manifest repositories, its answerable development-question
IDs, label/span ranks, and hit outcomes matched the committed baseline exactly before c1
or c2 ran. No held-out questions, live embeddings, or provider APIs were used.

c1 tokenization followed the registered `[A-Za-z0-9_]+` rule, retained unique tokens in
first-occurrence order, removed stop words identified by `ts_debug('english', :term)`,
quoted each remaining token and joined them with `OR`. The 32-token cap was applied after
stop-word removal; truncation was recorded in the machine-readable report. Every query
value was bound as a SQL parameter. c2 used the c1 query and appended split
snake_case/camelCase identifiers extracted from chunk content only; file paths were not
included. The searchable-text version was `identifier-split-v1`.

Following the protocol comparison column, c1 is compared with control and c2 with c1.
The four-condition keep rule is explicitly control-relative, so each candidate's rule
conditions are also evaluated against the fixed control. The c2-versus-control paired
statistics are reported to make that decision auditable. Paired bootstrap intervals use
seed `20261026`, 10,000 resamples and 95% confidence; the exact paired sign test is
descriptive only.

Metrics use the 11 answerable development questions per repository (33 pooled). Hit@k
shows successes and rate. The tests/ share is the number of top-five results under
`tests/` divided by all returned top-five results, and is reported only. Context cost
unions overlapping file-line ranges and sums `len(line) + 1` from the local source
snapshots; their revisions matched the three manifest-pinned commits. P95 uses nearest
rank.

## Development quality results

| Variant | Repository | N | Hit@1 success/rate | Hit@3 success/rate | Hit@5 success/rate | Span MRR | Non-empty text branch | Top-5 from tests/ | Mean raw chars | P95 raw chars |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| control | batch-processing-service | 11 | 6/11 (0.545) | 9/11 (0.818) | 10/11 (0.909) | 0.6848 | 1/11 (0.091) | 19/55 (0.345) | 8769.4 | 10730 |
| control | incidentweave | 11 | 5/11 (0.455) | 7/11 (0.636) | 7/11 (0.636) | 0.5152 | 2/11 (0.182) | 24/55 (0.436) | 7668.5 | 9727 |
| control | lifeos | 11 | 8/11 (0.727) | 10/11 (0.909) | 11/11 (1.000) | 0.8212 | 3/11 (0.273) | 0/55 (0.000) | 6375.3 | 8322 |
| control | pooled | 33 | 19/33 (0.576) | 26/33 (0.788) | 28/33 (0.848) | 0.6737 | 6/33 (0.182) | 43/165 (0.261) | 7604.4 | 10592 |
| c1 | batch-processing-service | 11 | 5/11 (0.455) | 8/11 (0.727) | 9/11 (0.818) | 0.5788 | 11/11 (1.000) | 23/55 (0.418) | 9029.2 | 10687 |
| c1 | incidentweave | 11 | 6/11 (0.545) | 8/11 (0.727) | 8/11 (0.727) | 0.6212 | 11/11 (1.000) | 16/55 (0.291) | 8478.5 | 10431 |
| c1 | lifeos | 11 | 8/11 (0.727) | 11/11 (1.000) | 11/11 (1.000) | 0.8333 | 11/11 (1.000) | 0/55 (0.000) | 7087.4 | 8188 |
| c1 | pooled | 33 | 19/33 (0.576) | 27/33 (0.818) | 28/33 (0.848) | 0.6778 | 33/33 (1.000) | 39/165 (0.236) | 8198.3 | 10486 |
| c2 | batch-processing-service | 11 | 3/11 (0.273) | 8/11 (0.727) | 9/11 (0.818) | 0.4879 | 11/11 (1.000) | 21/55 (0.382) | 8846.2 | 10539 |
| c2 | incidentweave | 11 | 6/11 (0.545) | 8/11 (0.727) | 8/11 (0.727) | 0.6061 | 11/11 (1.000) | 17/55 (0.309) | 8652.1 | 10351 |
| c2 | lifeos | 11 | 6/11 (0.545) | 10/11 (0.909) | 11/11 (1.000) | 0.7152 | 11/11 (1.000) | 0/55 (0.000) | 7089.2 | 8343 |
| c2 | pooled | 33 | 15/33 (0.455) | 26/33 (0.788) | 28/33 (0.848) | 0.6030 | 33/33 (1.000) | 38/165 (0.230) | 8195.8 | 10486 |

No c1 or c2 query exceeded the 32-token cap; the report records zero truncations for all
48 development questions in each variant.

## Paired reciprocal-rank comparisons

| Pair | Repository | Delta span MRR | 95% paired bootstrap CI | Wins / losses / ties | Exact sign-test p (descriptive) |
|---|---|---:|---|---:|---:|
| c1 vs control | batch-processing-service | -0.1061 | [-0.3030, +0.0909] | 2 / 4 / 5 | 0.687500 |
| c1 vs control | incidentweave | +0.1061 | [-0.0758, +0.3030] | 3 / 1 / 7 | 0.625000 |
| c1 vs control | lifeos | +0.0121 | [-0.1364, +0.1788] | 2 / 2 / 7 | 1.000000 |
| c1 vs control | pooled | +0.0040 | [-0.1010, +0.1111] | 7 / 7 / 19 | 1.000000 |
| c2 vs c1 | batch-processing-service | -0.0909 | [-0.2576, +0.0303] | 1 / 2 / 8 | 1.000000 |
| c2 vs c1 | incidentweave | -0.0152 | [-0.0455, +0.0000] | 0 / 1 / 10 | 1.000000 |
| c2 vs c1 | lifeos | -0.1182 | [-0.2909, +0.0000] | 0 / 2 / 9 | 0.500000 |
| c2 vs c1 | pooled | -0.0747 | [-0.1525, -0.0101] | 1 / 5 / 27 | 0.218750 |
| c2 vs control | batch-processing-service | -0.1970 | [-0.3970, +0.0182] | 2 / 6 / 3 | 0.289062 |
| c2 vs control | incidentweave | +0.0909 | [-0.1212, +0.3030] | 3 / 1 / 7 | 0.625000 |
| c2 vs control | lifeos | -0.1061 | [-0.2303, +0.0000] | 1 / 4 / 6 | 0.375000 |
| c2 vs control | pooled | -0.0707 | [-0.1818, +0.0434] | 6 / 11 / 16 | 0.332306 |

## Registered decision

The protocol requires all four conditions, evaluated against control:

| Candidate | No repository loses >1 Hit@5 | No repository loses >0.03 span MRR | Pooled span delta MRR >= +0.02 | Non-empty text-branch share increases | Qualifies? |
|---|---|---|---|---|---|
| c1 | Pass | Fail | Fail | Pass | No |
| c2 | Pass | Fail | Fail | Pass | No |

The rule therefore retains current behavior. **This item adopts nothing.** Any future
adoption under this result is closed with no change; reopen only after a separately
registered comparison.

## Protocol lesson

With 11 development answerable questions per repository, moving one question from rank 1
to rank 2 changes span MRR by about 0.045. The per-repository MRR-loss limit of 0.03 is
finer than this dataset can resolve, so almost any such change fails it. The 14c decision
does not depend on that limit: the pooled gain of +0.004 fails the +0.02 condition on its
own. The registered rule is not rewritten. Future protocols should state per-repository
tolerances in whole questions.

## c3 equivalence and timing

c3 used a temporary PostgreSQL table with a generated `tsvector` column and GIN index.
The chunk IDs matched the query-time `to_tsvector('english', content)` expression for
all 16 development questions in each repository (48/48 total).

| Repository | Chunks | Development questions | Equivalent | Query-time median / p95 ms | Generated-vector median / p95 ms | Generated-vector index used |
|---|---:|---:|---|---:|---:|---:|
| incidentweave | 70 | 16 | Yes | 47.9755 / 52.3390 | 3.5585 / 7.0330 | 7/16 |
| batch-processing-service | 38 | 16 | Yes | 31.4395 / 38.1870 | 3.0885 / 6.1810 | 0/16 |
| lifeos | 49 | 16 | Yes | 24.0565 / 52.0900 | 3.3130 / 5.3900 | 0/16 |

The GIN index was not selected for most questions at these table sizes. These small,
noisy timing measurements are not meaningful performance evidence and imply no quality
claim or c3 adoption decision.

## Honest limits

There are only 33 development answerable questions across three tiny, single-author
repositories. The results may not transfer to other repositories or query distributions.
Held-out questions were not used. c1 and c2 remain opt-in evaluation variants; production
defaults, baselines, gates, manifest and the binding protocol were not changed.
The opt-in c1/c2 code remains in `app/retrieval` to reproduce the committed results; it is
not adopted.

Machine-readable report and full per-question details:
[evaluation/experiments/fulltext/results.json](../../evaluation/experiments/fulltext/results.json).
