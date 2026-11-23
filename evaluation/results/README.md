# Evaluation results

Back to the [evaluation guide](../README.md).

## Committed baselines

- [`baseline.json`](baseline.json) — Phase 8 answer-evaluation baseline report; it is not selected by the manifest. See the [Phase 8 evaluation log](../../docs/phases/08-evaluation.md).
- [`../repos/incidentweave/offline-baseline.json`](../repos/incidentweave/offline-baseline.json) — IncidentWeave full retrieval baseline selected by the manifest.
- [`../repos/incidentweave/smoke-baseline.json`](../repos/incidentweave/smoke-baseline.json) — IncidentWeave smoke baseline selected by the manifest.

Repository-specific baselines for `batch-processing-service` and `lifeos` are under [`../repos/`](../repos/).

## Generated output

- `runs/` contains ignored timestamped run artifacts; `.gitkeep` is retained. The four registered item 34 development run sets below are intentional committed exceptions:
  - [`end_to_end_dev_run_rq_2026-11-23.json`](runs/end_to_end_dev_run_rq_2026-11-23.json)
  - [`end_to_end_dev_run_kopf_2026-11-23.json`](runs/end_to_end_dev_run_kopf_2026-11-23.json)
  - [`end_to_end_dev_run_luigi_2026-11-23.json`](runs/end_to_end_dev_run_luigi_2026-11-23.json)
  - [`end_to_end_dev_run_client_python_2026-11-23.json`](runs/end_to_end_dev_run_client_python_2026-11-23.json)
- These raw records contain three temperature-0 runs for each of the 40 manifest-assigned development questions in each v2 repository (480 records total). Provider-unavailable outcomes and errors are retained rather than omitted.
- `run-*.json` and `evaluation_report.json` are generated run output and ignored.

Check [`../manifest.json`](../manifest.json) to distinguish registered baselines from other files. The ignore rules are in [`.gitignore`](../../.gitignore).
