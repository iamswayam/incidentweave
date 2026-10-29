# Evaluation experiments

Back to the [evaluation guide](../README.md).

| Path | Contents | Regeneration |
|---|---|---|
| `chunking/` | `protocol.json` defines the comparison; `report-development.json` and `.md` record its development report. `fixtures/<repository>/<strategy>.json.gz` contains per-repository, per-strategy fixtures. | `scripts.run_chunking_experiment` has `prepare-sources`, `plan`, `embed`, and `evaluate` subcommands. `embed` calls the provider; `evaluate` writes the development reports. |
| `fulltext/` | `results.json` and `report.md` record the full-text ablation. | `scripts.run_fulltext_ablation` runs the analysis and rewrites both tracked files. It has no help mode; do not run it to check usage. |

The chunking candidates, selection rule, and result are described in [the chunking strategies note](../../docs/notes/06-chunking-strategies.md). The full-text protocol and result are indexed in [the evaluation guide](../README.md#7-documentation-map).
