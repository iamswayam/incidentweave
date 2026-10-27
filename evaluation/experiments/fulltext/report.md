# Full-text ablation results (item 14c-2)

## Method

The control and c1/c2 runs use the committed S0 fixtures, cached query embeddings, the local PostgreSQL database, and development questions only. Before any variant ran, every answerable control question rank and hit outcome was checked against the committed baseline. No embedding or provider API was called. c1 stop words came from `ts_debug('english', :term)`; questions and query text were always passed as bound parameters. c2 appends split identifiers from chunk content only; file paths are not searchable text.

The comparison column is read sequentially: c1 versus control, then c2 versus c1. The registered four-condition decision rule is nevertheless applied to each quality candidate versus the fixed control, exactly as the protocol's rule says. The additional c2-versus-control comparison is reported to make that decision auditable. Bootstrap and exact sign-test results use paired per-question span reciprocal ranks.

## Development results

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

Hit@k cells show successes/question count; MRR is span-based. Test-file share is the number of retrieved top-five chunks under `tests/` divided by all returned top-five chunks. Context cost unions overlapping file-line ranges and sums `len(line) + 1` from the pinned local source snapshot.

## Query-cap truncation

| Variant | Repository | Truncated development queries |
|---|---|---:|
| c1 | batch-processing-service | 0/16 |
| c1 | incidentweave | 0/16 |
| c1 | lifeos | 0/16 |
| c2 | batch-processing-service | 0/16 |
| c2 | incidentweave | 0/16 |
| c2 | lifeos | 0/16 |

## Paired comparisons

| Pair | Repository | Delta span MRR | 95% paired bootstrap CI | Wins / losses / ties | Exact sign-test p (descriptive) |
|---|---|---:|---|---:|---:|
| c1_vs_control | batch-processing-service | -0.1061 | [-0.3030, +0.0909] | 2 / 4 / 5 | 0.687500 |
| c1_vs_control | incidentweave | +0.1061 | [-0.0758, +0.3030] | 3 / 1 / 7 | 0.625000 |
| c1_vs_control | lifeos | +0.0121 | [-0.1364, +0.1788] | 2 / 2 / 7 | 1.000000 |
| c1_vs_control | pooled | +0.0040 | [-0.1010, +0.1111] | 7 / 7 / 19 | 1.000000 |
| c2_vs_c1 | batch-processing-service | -0.0909 | [-0.2576, +0.0303] | 1 / 2 / 8 | 1.000000 |
| c2_vs_c1 | incidentweave | -0.0152 | [-0.0455, +0.0000] | 0 / 1 / 10 | 1.000000 |
| c2_vs_c1 | lifeos | -0.1182 | [-0.2909, +0.0000] | 0 / 2 / 9 | 0.500000 |
| c2_vs_c1 | pooled | -0.0747 | [-0.1525, -0.0101] | 1 / 5 / 27 | 0.218750 |
| c2_vs_control | batch-processing-service | -0.1970 | [-0.3970, +0.0182] | 2 / 6 / 3 | 0.289062 |
| c2_vs_control | incidentweave | +0.0909 | [-0.1212, +0.3030] | 3 / 1 / 7 | 0.625000 |
| c2_vs_control | lifeos | -0.1061 | [-0.2303, +0.0000] | 1 / 4 / 6 | 0.375000 |
| c2_vs_control | pooled | -0.0707 | [-0.1818, +0.0434] | 6 / 11 / 16 | 0.332306 |

## Registered decision rule

| Candidate | Hit@5 loss <= 1/repo | Span MRR loss <= 0.03/repo | Pooled delta MRR >= +0.02 | Text branch share increases | Qualifies to advance? |
|---|---|---|---|---|---|
| c1 | pass | fail | fail | pass | no |
| c2 | pass | fail | fail | pass | no |

The rule is mechanical; a quality variant must pass all four conditions. No variant is adopted in item 14c-2. Item 14c-3 is the adoption step.

## c3 generated-vector equivalence and timing

Each repository was loaded into a temporary PostgreSQL table with a generated `tsvector` column and a temporary GIN index. Query-time and generated-vector matching chunk IDs were compared for every development question.

| Repository | Chunks | Development questions | Equivalent | Query-time median/p95 ms | Generated-vector median/p95 ms | Generated index used |
|---|---:|---:|---|---:|---:|---:|
| incidentweave | 70 | 16 | True | 47.9755 / 52.3390 | 3.5585 / 7.0330 | 7/16 |
| batch-processing-service | 38 | 16 | True | 31.4395 / 38.1870 | 3.0885 / 6.1810 | 0/16 |
| lifeos | 49 | 16 | True | 24.0565 / 52.0900 | 3.3130 / 5.3900 | 0/16 |

Timing is descriptive only: these fixtures contain only 38–70 chunks per repository, so the timings are too small and noise-sensitive to support a performance claim. c3 has no quality claim and does not qualify as a winner.

## Honest limits

The quality sample is 33 development answerable questions across three tiny, single-author repositories. It does not establish transfer to other repositories or query distributions. Held-out data was not used. c1 and c2 are opt-in evaluation variants only; production defaults, baselines, gates, manifest, and the registered protocol remain unchanged.

Protocol: [item 14 retrieval ablation](../../../docs/architecture-review/08-retrieval-ablation-protocol.md).
