# Local embedding-model comparison results

Protocol: [item 18c local embedding comparison](../architecture-review/14-local-embedding-protocol.md).

## Method and limits

The registered control and candidates were evaluated on development data only. No held-out question, label, retrieval result, or vector was read or used. The question and baseline records were selected with the existing development-only split helper; fixture JSON containing all question vectors was not deserialized. Only development Gemini query vectors were loaded by text hash, and document vectors were read from the named evaluation repositories. The control evaluator matched all 33 answerable development baseline ranks before candidate metrics were calculated.

The paired bootstrap uses seed 20261031, 10,000 resamples, and linear-interpolated 95% endpoints. The exact sign test is descriptive only. The guard threshold remains 0.5; its calibration is Gemini-specific. The two candidate comparisons have no multiplicity correction, and no model is adopted automatically.

One rank change is approximately 0.015 pooled MRR. Results cover only 33 answerable and 15 unanswerable questions across three small, single-author repositories. Local inference makes no provider API calls or provider usage charges; model downloads are the only network requirement.

## Retrieval results

| Model | Dimensions | Pooled MRR | Hit@1 | Hit@3 | Hit@5 |
|---|---:|---:|---:|---:|---:|
| Gemini control | 768 | 0.6737 | 19 | 26 | 28 |
| `jinaai/jina-embeddings-v2-base-code` | 768 | 0.5045 | 12 | 22 | 25 |
| `BAAI/bge-small-en-v1.5` | 384 | 0.5354 | 12 | 22 | 26 |

### Control per repository

| Repository | MRR | Hit@1 | Hit@3 | Hit@5 |
|---|---:|---:|---:|---:|
| incidentweave | 0.5152 | 5 | 7 | 7 |
| batch-processing-service | 0.6848 | 6 | 9 | 10 |
| lifeos | 0.8212 | 8 | 10 | 11 |

## Candidate retention rules

### `jinaai/jina-embeddings-v2-base-code`

| Rule | Result |
|---|---|
| R1 | FAIL |
| R2 | FAIL |
| R3 | FAIL |
| R4 | PASS |

- Outcome: **keep control**
- MRR delta vs control: -0.1692
- Paired bootstrap 95% interval: [-0.2884, -0.0525]
- Exact sign test (descriptive): p=0.0490
- Model size: 0.64 GB; license: Apache-2.0; network need: model download only
- Mean CPU embedding time: 21345.895 ms per unique development chunk/document and 1622.828 ms per unique development query (duplicate exact texts reuse a cached vector).
- CPU runtime: AMD64 Family 22 Model 48 Stepping 1, AuthenticAMD (4 logical CPUs; CPUExecutionProvider).
- Top-five test-file share: 22.5000%.

| Repository | MRR | Hit@1 | Hit@3 | Hit@5 |
|---|---:|---:|---:|---:|
| incidentweave | 0.3636 | 2 | 7 | 7 |
| batch-processing-service | 0.5985 | 5 | 8 | 9 |
| lifeos | 0.5515 | 5 | 7 | 9 |

Vector distance distributions (model-specific, not comparable):

| Question group | Count | Minimum | Median | Maximum |
|---|---:|---:|---:|---:|
| answerable | 33 | 0.281042 | 0.472001 | 0.687586 |
| unanswerable | 15 | 0.439386 | 0.679610 | 0.865882 |

Per-repository unanswerable false accepts: incidentweave=0, batch-processing-service=1, lifeos=0.
Per-repository unanswerable guard decisions (accepted/refused): incidentweave=0/5, batch-processing-service=1/4, lifeos=0/5.
Development ordinals whose unanswerable guard decisions changed: incidentweave=[4, 5]; batch-processing-service=[4]; lifeos=[4, 5].

### `BAAI/bge-small-en-v1.5`

| Rule | Result |
|---|---|
| R1 | FAIL |
| R2 | FAIL |
| R3 | FAIL |
| R4 | FAIL |

- Outcome: **keep control**
- MRR delta vs control: -0.1384
- Paired bootstrap 95% interval: [-0.2960, 0.0157]
- Exact sign test (descriptive): p=0.3593
- Model size: 0.067 GB; license: MIT; network need: model download only
- Mean CPU embedding time: 5548.949 ms per unique development chunk/document and 422.877 ms per unique development query (duplicate exact texts reuse a cached vector).
- CPU runtime: AMD64 Family 22 Model 48 Stepping 1, AuthenticAMD (4 logical CPUs; CPUExecutionProvider).
- Top-five test-file share: 24.5833%.

| Repository | MRR | Hit@1 | Hit@3 | Hit@5 |
|---|---:|---:|---:|---:|
| incidentweave | 0.5000 | 4 | 7 | 7 |
| batch-processing-service | 0.4394 | 3 | 6 | 8 |
| lifeos | 0.6667 | 5 | 9 | 11 |

Vector distance distributions (model-specific, not comparable):

| Question group | Count | Minimum | Median | Maximum |
|---|---:|---:|---:|---:|
| answerable | 33 | 0.153769 | 0.286146 | 0.430645 |
| unanswerable | 15 | 0.250505 | 0.346882 | 0.551735 |

Per-repository unanswerable false accepts: incidentweave=5, batch-processing-service=4, lifeos=3.
Per-repository unanswerable guard decisions (accepted/refused): incidentweave=5/0, batch-processing-service=4/1, lifeos=3/2.
Development ordinals whose unanswerable guard decisions changed: incidentweave=[1, 2, 3]; batch-processing-service=[1, 3]; lifeos=[3].

## Control distances and limitations

Control vector-distance distributions:

| Question group | Count | Minimum | Median | Maximum |
|---|---:|---:|---:|---:|
| answerable | 33 | 0.229325 | 0.331018 | 0.455547 |
| unanswerable | 15 | 0.327137 | 0.503531 | 0.555965 |

Control unanswerable guard decisions (accepted/refused): incidentweave=2/3, batch-processing-service=2/3, lifeos=2/3.
Control top-five test-file share: 30.4167%.


The models and distances have not been evaluated on held-out data. Three small, single-author repositories and 48 development questions are insufficient to establish general performance. Candidate guard thresholds remain unvalidated; the 0.5 threshold was calibrated to Gemini. A passing candidate requires a separately registered held-out validation, a per-model guard threshold under item 3b, and a production migration plan before any adoption.
