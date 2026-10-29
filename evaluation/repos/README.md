# Repository evaluation data

Back to the [evaluation guide](../README.md).

Each repository directory contains six manifest-selected files:

| File | Role |
|---|---|
| `questions.json` | Repository questions, labels, and pinned source revision |
| `retrieval_fixture.json.gz` | Committed chunks and query embeddings |
| `gate.json` | Full retrieval-gate thresholds |
| `offline-baseline.json` | Full baseline report |
| `smoke-gate.json` | Smoke retrieval-gate thresholds |
| `smoke-baseline.json` | Smoke baseline report |

The directories are [`batch-processing-service/`](batch-processing-service/) and [`lifeos/`](lifeos/).

IncidentWeave's own question set, full gate, smoke gate, fixture, and baselines remain at the evaluation root and in `fixtures/` and `results/` until item 27b normalizes the layout. The [manifest](../manifest.json) pins the paths and hashes for all repositories.
