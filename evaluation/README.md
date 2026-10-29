# Evaluation

## 1. Purpose

The evaluation package contains offline retrieval checks, answer-evaluation tooling, and registered experiments.
The manifest selects pinned repositories, questions, fixtures, baselines, and gates.
Offline retrieval uses committed fixtures and question embeddings; the answer runner invokes the investigation pipeline.
This guide points to the relevant commands, data, modules, and evaluation records.

## 2. Commands

Evaluation commands that would write data or call a provider are marked **not run here**. CLI help was checked where it completed.

| Command | What it does | Needs database | Needs Gemini key | Source |
|---|---|---:|---:|---|
| `.\.venv\Scripts\python.exe -m scripts.run_retrieval_eval --out evaluation/results/offline-baseline.json` — tracked output; not run here | Runs retrieval-only evaluation using the committed fixtures and cached question vectors; makes no provider calls. This documented invocation overwrites the committed baseline at `evaluation/results/offline-baseline.json`. Safe alternative: `.\.venv\Scripts\python.exe -m scripts.run_retrieval_eval --out evaluation/results/runs/offline-check.json` (ignored output). | No | No | [Root README](../README.md), [offline retrieval note](../docs/notes/04-offline-retrieval-evaluation.md), [CLI](../scripts/run_retrieval_eval.py) |
| `.\.venv\Scripts\python.exe -m scripts.check_retrieval_gate --split smoke` — run (exit 0) | Runs each manifest repository's deterministic smoke gate and reports repository and pooled retrieval metrics. Pooled Hit@1/3/5 was 9/15, 13/15, 14/15; pooled MRR was 0.724 for substring labels and spans. The CI job provisions PostgreSQL for the job, but this gate reads committed evaluation inputs. | No for the gate command | No | [Root README](../README.md), [CI workflow](../.github/workflows/ci.yml), [offline retrieval note](../docs/notes/04-offline-retrieval-evaluation.md) |
| `.\.venv\Scripts\python.exe -m evaluation.build_fixture` — tracked output; not run here | Builds an offline retrieval fixture from evaluation-database chunks and cached question embeddings; the default IncidentWeave output is the manifest-pinned `evaluation/fixtures/retrieval_fixture.json.gz`. | Yes | No | [Offline retrieval note](../docs/notes/04-offline-retrieval-evaluation.md) |
| `.\.venv\Scripts\python.exe -m scripts.inspect_retrieval` — not run here | Writes per-question retrieval cards and repository summaries from committed fixtures; defaults to development. | No | No | [Retrieval inspection note](../docs/notes/07-retrieval-inspection-report.md) |
| `.\.venv\Scripts\python.exe -m scripts.run_chunking_experiment --help` — help only; `evaluate` has tracked outputs | Shows the `prepare-sources`, `plan`, `embed`, and `evaluate` subcommands for the registered chunking comparison. The `embed` subcommand calls the embedding provider and supports `--batch-delay-seconds` pacing; `evaluate` rewrites the tracked `evaluation/experiments/chunking/report-development.json` and `.md`. | No | Yes, for `embed` only | [Chunking strategy note](../docs/notes/06-chunking-strategies.md), [CLI help](../scripts/run_chunking_experiment.py) |
| `scripts.run_fulltext_ablation` — tracked outputs; not run here | Rewrites `evaluation/experiments/fulltext/results.json` and `report.md` (tracked). No help mode; do not run it to check usage. | Yes | No | [Ablation protocol](../docs/architecture-review/08-retrieval-ablation-protocol.md), [ablation results](../docs/notes/09-fulltext-ablation-results.md), [entry point](../scripts/run_fulltext_ablation.py) |
| `.\.venv\Scripts\python.exe -m scripts.diagnose_fulltext --help` — help only; default output tracked | Has `--help`; writes `docs/notes/08-fulltext-diagnostic.md` by default (tracked); pass `--output` to write elsewhere. The diagnostic was not run here. | Yes | No | [Full-text diagnostic note](../docs/notes/08-fulltext-diagnostic.md), [entry point](../scripts/diagnose_fulltext.py) |
| `.\.venv\Scripts\python.exe scripts\run_eval.py` — not run here | Runs the two-pass answer evaluation against an allowlisted repository and records evaluation run artifacts. | Yes | Yes | [Root README](../README.md), [Phase 8 evaluation log](../docs/phases/08-evaluation.md), [runner CLI](../scripts/run_eval.py) |

The fixture builder needs existing database embeddings and cached question embeddings; it does not fetch embeddings. The answer runner and chunking `embed` subcommand can make live provider calls, so they were not run.

Commands that write to tracked files are marked; rerunning them changes registered artifacts.

## 3. Directory and file map

“Versioned” means tracked as project input, code, documentation, or baseline. “Ignored/generated” means local or generated data excluded by [`.gitignore`](../.gitignore); `results/` contains both.

| Path | Role | Status |
|---|---|---|
| [`README.md`](README.md) | Entry point for evaluation commands, organization, data, and rules. | Versioned |
| [`__init__.py`](__init__.py) | Marks the evaluation package and describes its scope. | Versioned |
| [`build_fixture.py`](build_fixture.py) | Builds and reads the offline retrieval fixtures. | Versioned |
| [`chunk_experiments.py`](chunk_experiments.py) | Defines evaluation-only chunking strategies. | Versioned |
| [`chunking_experiment.py`](chunking_experiment.py) | Prepares and analyzes the chunking comparison. | Versioned |
| [`compare.py`](compare.py) | Compares saved evaluation reports. | Versioned |
| [`compare_chunking_runs.py`](compare_chunking_runs.py) | Compares saved chunking-evaluation runs. | Versioned |
| [`corpus.py`](corpus.py) | Sets up the pinned evaluation corpus. | Versioned |
| [`fulltext_ablation.py`](fulltext_ablation.py) | Implements fixture-backed full-text ablation helpers and metrics. | Versioned |
| [`fulltext_diagnostic.py`](fulltext_diagnostic.py) | Provides pure helpers for full-text query-term diagnostics. | Versioned |
| [`fulltext_experiment.py`](fulltext_experiment.py) | Executes and renders the registered full-text ablation. | Versioned |
| [`gate.json`](gate.json) | IncidentWeave full retrieval-gate configuration. | Versioned |
| [`gate.py`](gate.py) | Loads and evaluates the offline retrieval regression gate. | Versioned |
| [`golden.py`](golden.py) | Loads and validates question sets. | Versioned |
| [`golden_set.json`](golden_set.json) | IncidentWeave questions and their labels. | Versioned |
| [`inspection.py`](inspection.py) | Renders offline retrieval-inspection reports. | Versioned |
| [`manifest.json`](manifest.json) | Selects the repositories and pins their evaluation inputs. | Versioned |
| [`manifest.py`](manifest.py) | Loads and validates the multi-repository manifest and its assets. | Versioned |
| [`metrics.py`](metrics.py) | Implements deterministic evaluation metrics. | Versioned |
| [`retrieval_eval.py`](retrieval_eval.py) | Runs offline hybrid-retrieval evaluation. | Versioned |
| [`runner.py`](runner.py) | Runs the Phase 8 retrieval and investigation evaluation. | Versioned |
| [`smoke-gate.json`](smoke-gate.json) | IncidentWeave smoke retrieval-gate configuration. | Versioned |
| [`span_labels.py`](span_labels.py) | Derives chunk-independent relevance spans from question labels. | Versioned |
| [`splits.py`](splits.py) | Defines deterministic stratified question assignments. | Versioned |
| [`stats.py`](stats.py) | Provides dependency-free retrieval statistics. | Versioned |
| `cache/` | Local embedding cache used by fixture construction and experiments. | Ignored/generated |
| [`experiments/`](experiments/) | Chunking and full-text experiment protocols, fixtures, and reports. | Versioned |
| [`fixtures/`](fixtures/) | Shared IncidentWeave offline retrieval fixture. | Versioned |
| `inspection/` | Generated retrieval-inspection cards and summaries. | Ignored/generated |
| [`repos/`](repos/) | Questions, fixtures, gates, and baselines for the other repositories. | Versioned |
| [`results/`](results/) | Committed baselines plus ignored run artifacts. | Mixed; see section 8 |
| `_snapshot/` | Local source snapshots and experiment working data. | Ignored/generated |
| `__pycache__/` | Python bytecode cache. | Ignored/generated |

The IncidentWeave questions and full gate are at the evaluation root; its retrieval fixture is in `fixtures/`, and its baselines are in `results/`. The `batch-processing-service` and `lifeos` questions, fixtures, gates, and baselines are grouped under [`repos/`](repos/) by repository name. This asymmetry is a known layout issue handled in item 27b.

## 4. Module map

The descriptions below are taken from each module's docstring.

### Manifest and data

- [`__init__.py`](__init__.py) — Evaluation utilities for the IncidentWeave retrieval and investigation pipeline.
- [`manifest.py`](manifest.py) — Loading and fail-closed validation for the multi-repository evaluation manifest.
- [`golden.py`](golden.py) — Golden-set loading and validation.
- [`splits.py`](splits.py) — Deterministic stratified question assignments for repository evaluations.
- [`span_labels.py`](span_labels.py) — Derive stable, chunk-independent relevance spans from golden substring labels.
- [`metrics.py`](metrics.py) — Pure, deterministic metrics for Phase 8 evaluation.
- [`stats.py`](stats.py) — Small, dependency-free statistics for retrieval evaluation.

### Fixture build

- [`corpus.py`](corpus.py) — Pinned evaluation corpus setup, restricted to incidentweave-eval.
- [`build_fixture.py`](build_fixture.py) — Build the offline retrieval fixture from cached embeddings and the evaluation DB.

### Retrieval evaluation

- [`retrieval_eval.py`](retrieval_eval.py) — Offline hybrid-retrieval evaluation using committed embeddings.
- [`gate.py`](gate.py) — Pure loading and evaluation for the offline retrieval regression gate.
- [`inspection.py`](inspection.py) — Pure Markdown rendering for offline retrieval inspection reports.

### Answer evaluation

- [`runner.py`](runner.py) — Run the Phase 8 evaluation without changing production pipeline behavior.
- [`compare.py`](compare.py) — Utilities to compare evaluation runs in a stable, legacy-tolerant way.

### Experiments

- [`chunk_experiments.py`](chunk_experiments.py) — Chunking strategies supported by the evaluation harness only.
- [`chunking_experiment.py`](chunking_experiment.py) — Deterministic preparation and analysis for the chunking comparison.
- [`compare_chunking_runs.py`](compare_chunking_runs.py) — Compare two saved chunking-evaluation runs without database or API access.
- [`fulltext_ablation.py`](fulltext_ablation.py) — Fixture-backed runners and metrics for the registered full-text ablation.
- [`fulltext_diagnostic.py`](fulltext_diagnostic.py) — Pure helpers for diagnosing PostgreSQL full-text query terms.
- [`fulltext_experiment.py`](fulltext_experiment.py) — Execute and render the item 14c-2 development-only full-text ablation.

`chunk_experiments.py` defines chunking strategies; `chunking_experiment.py` runs the experiment. Item 27b may rename `chunk_experiments.py`.

## 5. Data model

[`manifest.json`](manifest.json) is the versioned source of truth for three repositories. Each entry selects the repository's pinned source revision, question file, retrieval fixture, full and smoke baselines, and full and smoke gates, with SHA-256 values for the resources. The IncidentWeave questions are in `golden_set.json`; the other repositories' question sets are in `repos/<name>/questions.json`.

Each question file has 24 questions per repository. The manifest assigns 16 to development and 8 to held-out; the fixed 8-question smoke subset is drawn from development. The manifest records split counts of 11 answerable and 5 unanswerable development questions, 5 answerable and 3 unanswerable held-out questions, and 5 answerable and 3 unanswerable smoke questions per repository. No held-out question IDs or results are included in this guide.

Each retrieval fixture contains the pinned source chunks and the question vectors used by offline retrieval. Full and smoke gates compare results against their separately selected baselines. [`manifest.py`](manifest.py) validates manifest shape, resource paths, SHA-256 pins, repository/question/fixture metadata, split assignments, fixture-size limits, and baseline-to-gate references. Per the multi-repository note, JSON hashes normalize CRLF to LF and binary fixtures are hashed as stored.

## 6. Rules

- The held-out split is frozen before chunking or threshold experiments and is never tuned on. The registered chunking plan calls for one post-selection held-out confirmation; checklist item 3b separately re-validates guard thresholds on held-out after retrieval changes. Both require explicit maintainer approval and are for reporting/validation, not design selection.
- Commit the evaluation rule and planned statistics before examining results.
- Do not retroactively edit the binding protocol; record results against the protocol that was committed before the experiment.
- Change a baseline only in a pull request that states why; do not rebuild baselines as a CI side effect.
- Keep smoke as a fixed development-only regression subset, not a way to choose a design or threshold.

These safeguards are described in the [multi-repository plan](../docs/architecture-review/06-multi-repo-evaluation-plan.md), [chunking comparison plan](../docs/architecture-review/07-chunking-comparison-plan.md), [retrieval ablation protocol](../docs/architecture-review/08-retrieval-ablation-protocol.md), and [multi-repository evaluation note](../docs/notes/05-multi-repo-evaluation.md).

The earlier multi-repository and chunking plans describe a one-time held-out report after a design is fixed. The no-run/no-inspection rule above is the current instruction for this guide; it does not authorize that evaluation.

## 7. Documentation map

| Document | Question it answers |
|---|---|
| [Root README evaluation section](../README.md) | What evaluation commands and CI checks are currently presented to project users? |
| [Documentation index](../docs/README.md) | Where are the project's documentation areas indexed? |
| [Fix checklist](../docs/architecture-review/03-fix-checklist.md) | What approved evaluation work and follow-up items are tracked? |
| [Multi-repo evaluation plan](../docs/architecture-review/06-multi-repo-evaluation-plan.md) | How are repositories, questions, splits, and multi-repo gates designed? |
| [Chunking comparison plan](../docs/architecture-review/07-chunking-comparison-plan.md) | What chunking candidates, metrics, and selection rule were registered? |
| [Retrieval ablation protocol](../docs/architecture-review/08-retrieval-ablation-protocol.md) | What full-text variants and decision rules were preregistered? |
| [Phase 8 evaluation log](../docs/phases/08-evaluation.md) | How was the original answer and retrieval evaluation specified and recorded? |
| [Phase 8b evaluation improvements](../docs/phases/08b-evaluation-improvements.md) | What measurement, run-registry, and evidence-bundle improvements were made? |
| [Offline retrieval evaluation note](../docs/notes/04-offline-retrieval-evaluation.md) | How do committed fixtures, labels, offline metrics, and the retrieval gate work? |
| [Multi-repository evaluation note](../docs/notes/05-multi-repo-evaluation.md) | How do the manifest, split assignments, question process, and gates work? |
| [Chunking strategies note](../docs/notes/06-chunking-strategies.md) | Which chunking candidates were defined, and how is embedding pacing handled? |
| [Retrieval inspection note](../docs/notes/07-retrieval-inspection-report.md) | How are generated retrieval cards read, and what are their limits? |
| [Full-text diagnostic note](../docs/notes/08-fulltext-diagnostic.md) | How were PostgreSQL full-text terms, stop words, and OR matches diagnosed? |
| [Full-text ablation results](../docs/notes/09-fulltext-ablation-results.md) | What development-only ablation was measured, and what decision followed? |
| [Chunking-experiment index](../docs/chunking-experiment/README.md) | Where are the chunking experiment log, decision, workbook, and reviews? |
| [Chunking experiment log](../docs/chunking-experiment/01-experiment-log.md) | What decisions and experiment history were recorded for the chunking work? |
| [Chunking decision report](../docs/chunking-experiment/02-decision-report.md) | What decision and evidence were recorded for the chunking comparison? |
| [Human review workbook](../docs/chunking-experiment/03-human-review-workbook.md) | Where are the answer-level human review observations recorded? |
| [Claude review](../docs/chunking-experiment/04-review-claude.md) | What independent review of the chunking experiment was recorded by Claude? |
| [Copilot review](../docs/chunking-experiment/05-review-copilot.md) | What independent review of the chunking experiment was recorded by Copilot? |
| [ChatGPT review](../docs/chunking-experiment/06-review-chatgpt.md) | What independent review of the chunking experiment was recorded by ChatGPT? |

## 8. Committed versus generated

| Path or pattern | Contents | Status |
|---|---|---|
| `cache/` | Local cached embeddings used by fixture construction and experiments. | Generated and ignored |
| `_snapshot/` | Local pinned-source snapshots and experiment working copies. | Generated and ignored |
| `inspection/` | Generated per-question cards and repository summaries. | Generated and ignored |
| `results/runs/` | Timestamped run reports and related artifacts; `.gitkeep` is retained. | Generated and ignored, except tracked `.gitkeep` |
| `results/run-*.json` and `results/evaluation_report.json` | Non-baseline run output. | Generated and ignored |
| `results/baseline.json`, `results/offline-baseline.json`, `results/incidentweave-smoke-baseline.json` | Versioned evaluation baseline reports. | Committed |
| Other files under `results/` | Includes any additional tracked report files; check the manifest before treating a report as a gate baseline. | Versioned if tracked; run outputs follow the ignore rules above |
| `experiments/`, `fixtures/`, `repos/`, `manifest.json`, question files, gates, and Python modules | Registered experiment artifacts, evaluation inputs, baselines/gates, and implementation. | Committed |
| `__pycache__/` | Python bytecode cache. | Generated and ignored |

The ignore rules are in [`.gitignore`](../.gitignore). Do not commit local cache, snapshot, inspection, or ignored run-output files.
