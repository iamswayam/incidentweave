# Embedding task-type comparison: development

## Protocol metadata

- Protocol: [14-embedding-task-type-experiment.md](14-embedding-task-type-experiment.md)
- Protocol commit: `d02945dd6d78e9c25ef65f06797632483806fc7e`
- Cache version: `gemini-embedding-001-768-task-type-v1`
- Selection split: development only.

| Scope | Method | Answerable | Hit@1 | Hit@3 | Hit@5 | MRR | Span MRR | Test top-five share | Test-source recall | Test precision |
|---|---|---:|---:|---:|---:|---:|---:|---|---|---|
| incidentweave | control | 11 | 5 | 7 | 7 | 0.515152 | 0.515152 | 37/80 (0.462500) | not evaluable (0 denominator) | 0/24 (0.000000) |
| incidentweave | candidate | 11 | 5 | 9 | 10 | 0.628788 | 0.628788 | 21/80 (0.262500) | not evaluable (0 denominator) | 0/15 (0.000000) |
| batch-processing-service | control | 11 | 6 | 9 | 10 | 0.684848 | 0.684848 | 27/80 (0.337500) | not evaluable (0 denominator) | 0/19 (0.000000) |
| batch-processing-service | candidate | 11 | 5 | 9 | 9 | 0.621212 | 0.666667 | 21/80 (0.262500) | not evaluable (0 denominator) | 0/17 (0.000000) |
| lifeos | control | 11 | 8 | 10 | 11 | 0.821212 | 0.821212 | 9/80 (0.112500) | not evaluable (0 denominator) | 0/5 (0.000000) |
| lifeos | candidate | 11 | 9 | 10 | 11 | 0.881818 | 0.881818 | 12/80 (0.150000) | not evaluable (0 denominator) | 0/7 (0.000000) |
| Pooled | control | 33 | 19 | 26 | 28 | 0.673737 | 0.673737 | 73/240 (0.304167) | not evaluable (0 denominator) | 0/48 (0.000000) |
| Pooled | candidate | 33 | 19 | 28 | 30 | 0.710606 | 0.725758 | 54/240 (0.225000) | not evaluable (0 denominator) | 0/39 (0.000000) |

## Paired pooled MRR

Difference: 0.036869; 95% paired bootstrap interval: [-0.026263, 0.105051] (seed 20261031, 10000 resamples). The exact sign test is descriptive only: 6 positive, 3 negative, 24 tied; p=0.507812.

## Evidence-guard changes

| Repository | Unanswerable | Unchanged | Improved | Regressed | Changed development ordinals |
|---|---:|---:|---:|---:|---|
| incidentweave | 5 | 2 | 0 | 3 | 12, 13, 14 |
| batch-processing-service | 5 | 2 | 0 | 3 | 12, 13, 14 |
| lifeos | 5 | 2 | 0 | 3 | 12, 13, 14 |

## Registered decision

| Rule | Retention condition | Result |
|---|---|---|
| R1 | Pooled development MRR over 33 answerable questions improves by at least 0.03 versus control. | pass |
| R2 | The 95% paired-bootstrap lower bound of the pooled MRR difference is above 0. | fail |
| R3 | Per-repository answerable Hit@5 successes do not decrease. | fail |
| R4 | Per-repository guard decisions on every unanswerable development question are unchanged or improved. | fail |

**Mechanical decision:** Keep the current control; the candidate does not qualify under the registered rules.

## Limits

- This comparison covers 33 answerable and 15 unanswerable development questions across three small repositories; results may not generalize to other repositories or query distributions.
- A successful retrieval metric does not establish answer quality; the held-out split remains untouched.
- The evidence-guard threshold of 0.5 is provisional and was set on the control embeddings. A candidate may shift distances and change guard decisions; an R4 failure for that reason is valid, and threshold recalibration is out of scope for this comparison (item 3b).

## Reading of the result (written after the result, not part of the registered rule)

- R1 passed, but R2 to R4 failed, so the control is kept.
- The same three unanswerable development ordinals flipped from refusal to answer in every repository. This is consistent with the provisional 0.5 distance threshold, set on the control embeddings, no longer fitting the candidate's shifted distances, but this was not tested.
- The candidate's top-five test-file share fell from 73/240 to 54/240; this is a side observation only.
- A fair re-test needs the threshold recalibrated first (item 3b). The held-out split is untouched.
