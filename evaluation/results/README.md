# Evaluation results

Back to the [evaluation guide](../README.md).

## Committed baselines

- [`baseline.json`](baseline.json) — legacy answer-evaluation baseline artifact.
- [`offline-baseline.json`](offline-baseline.json) — IncidentWeave full retrieval baseline selected by the manifest.
- [`incidentweave-smoke-baseline.json`](incidentweave-smoke-baseline.json) — IncidentWeave smoke baseline selected by the manifest.

Repository-specific baselines for `batch-processing-service` and `lifeos` are under [`../repos/`](../repos/).

## Generated output

- `runs/` contains timestamped run artifacts and is ignored; `.gitkeep` is retained.
- `run-*.json` and `evaluation_report.json` are generated run output and ignored.

Check [`../manifest.json`](../manifest.json) to distinguish registered baselines from other files. The ignore rules are in [`.gitignore`](../../.gitignore).
