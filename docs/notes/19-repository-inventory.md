# Repository inventory

**Status:** Frozen snapshot (2026-11-01); superseded by docs/README.md for navigation

## Scope and method

**Observed from the tree:** This snapshot lists tracked Markdown under `docs/`, tracked Python
files directly under `scripts/` and `evaluation/`, test Python files by folder, and selected
tracked file sizes. Documentation last-change dates come from the newest commit touching each
path. Index coverage is a filename-presence check against the containing folder's `README.md`;
README files are labelled as indexes rather than treated as missing self-links. Script/module
test and documentation references are basename text-match counts against the documentation
snapshot before this inventory was added, not proof of complete behavioral test coverage or a
clickable reference. Large/data-file sizes are metadata only: baseline, results, and question
file contents were not opened.

**Observed counts:** The current snapshot contains 70 Markdown files under `docs/` (including
the root index and six folder indexes), 22 scripts, 27 evaluation modules, and 55 Python files
under `tests/` including its root conftest and fixture.

## A. Documentation inventory

### `docs/architecture/`

**Observed from the tree:** All content documents appear in the folder README index; the README
is the index itself.

| File | Title | Apparent kind | Last changed | README index |
|---|---|---|---|---|
| [01-architecture-overview.md](../architecture/01-architecture-overview.md) | IncidentWeave Architecture | Living reference | 2026-10-31 | Yes |
| [02-high-level-design.md](../architecture/02-high-level-design.md) | IncidentWeave High-Level Design | Living reference | 2026-10-31 | Yes |
| [03-low-level-design.md](../architecture/03-low-level-design.md) | IncidentWeave Low-Level Design | Living reference | 2026-10-31 | Yes |
| [04-threat-model.md](../architecture/04-threat-model.md) | Threat Model | Living security reference | 2026-10-31 | Yes |
| [README.md](../architecture/README.md) | Architecture | Index | 2026-10-24 | Index |

### `docs/architecture-review/`

**Observed from the tree:** All numbered content documents appear in the folder README index.
The folder combines immutable historical audits with living checklist/design documents and
registered protocols.

| File | Title | Apparent kind | Last changed | README index |
|---|---|---|---|---|
| [01-audit-claude.md](../architecture-review/01-audit-claude.md) | Independent Engineering Audit & AI Market Assessment: IncidentWeave | Frozen audit | 2026-10-21 | Yes |
| [02-audit-codex.md](../architecture-review/02-audit-codex.md) | IncidentWeave: Independent Engineering Audit and October 2026 Market Assessment | Frozen audit | 2026-10-21 | Yes |
| [03-fix-checklist.md](../architecture-review/03-fix-checklist.md) | IncidentWeave: Prioritized Fix Checklist (merged from the Claude and Codex audits) | Living status register / checklist | 2026-11-01 | Yes |
| [04-fix-checklist-review-codex.md](../architecture-review/04-fix-checklist-review-codex.md) | Independent review: fix checklist | Frozen review | 2026-10-21 | Yes |
| [05-implementation-workflow.md](../architecture-review/05-implementation-workflow.md) | Implementation workflow | Living workflow / how-to | 2026-10-23 | Yes |
| [06-multi-repo-evaluation-plan.md](../architecture-review/06-multi-repo-evaluation-plan.md) | 06 Multi-repo evaluation plan | Plan / reference | 2026-10-25 | Yes |
| [07-chunking-comparison-plan.md](../architecture-review/07-chunking-comparison-plan.md) | 07 Chunking comparison plan | Experiment plan / decision record | 2026-10-27 | Yes |
| [08-retrieval-ablation-protocol.md](../architecture-review/08-retrieval-ablation-protocol.md) | Retrieval ablation protocol (item 14) | Protocol | 2026-10-27 | Yes |
| [09-llm-gateway-decision.md](../architecture-review/09-llm-gateway-decision.md) | LLM gateway decision (item 18) | Decision record | 2026-10-28 | Yes |
| [10-llm-gateway-design.md](../architecture-review/10-llm-gateway-design.md) | Provider layer design (item 18a-1) | Living design reference | 2026-10-31 | Yes |
| [11-test-file-retrieval-protocol.md](../architecture-review/11-test-file-retrieval-protocol.md) | Test-file retrieval protocol (item 14b) | Protocol | 2026-10-30 | Yes |
| [12-bm25-comparison-protocol.md](../architecture-review/12-bm25-comparison-protocol.md) | BM25 comparison protocol (item 14d) | Protocol | 2026-10-31 | Yes |
| [13-degraded-response-design.md](../architecture-review/13-degraded-response-design.md) | Degraded response design (item 18d-1) | Approved design / implementation record | 2026-10-31 | Yes |
| [14-local-embedding-protocol.md](../architecture-review/14-local-embedding-protocol.md) | Local embedding-model comparison protocol (item 18c) | Protocol | 2026-11-01 | Yes |
| [README.md](../architecture-review/README.md) | Architecture review | Index | 2026-11-01 | Index |

### `docs/chunking-experiment/`

**Observed from the tree:** The folder README indexes all numbered records. The review workbook
and three independent reviews are large historical artifacts.

| File | Title | Apparent kind | Last changed | README index |
|---|---|---|---|---|
| [01-experiment-log.md](../chunking-experiment/01-experiment-log.md) | IncidentWeave: Chunking Strategy Discussion Log | Frozen experiment log | 2026-10-21 | Yes |
| [02-decision-report.md](../chunking-experiment/02-decision-report.md) | Chunking Strategy Experiment: Decision Report | Frozen decision record | 2026-10-21 | Yes |
| [03-human-review-workbook.md](../chunking-experiment/03-human-review-workbook.md) | Chunking Experiment: Human Review Workbook | Frozen review workbook | 2026-10-21 | Yes |
| [04-review-claude.md](../chunking-experiment/04-review-claude.md) | Gate 5 Review — Claude (independent reviewer) | Frozen review | 2026-10-21 | Yes |
| [05-review-copilot.md](../chunking-experiment/05-review-copilot.md) | Gate 5 independent review — Copilot | Frozen review | 2026-10-21 | Yes |
| [06-review-chatgpt.md](../chunking-experiment/06-review-chatgpt.md) | Gate 5 Independent Review — ChatGPT | Frozen review | 2026-10-21 | Yes |
| [README.md](../chunking-experiment/README.md) | Chunking experiment | Index | 2026-10-21 | Index |

### `docs/learning/`

**Observed from the tree:** The folder README indexes the template and all nine concept guides.

| File | Title | Apparent kind | Last changed | README index |
|---|---|---|---|---|
| [00-template.md](../learning/00-template.md) | \<Topic Name> | How-to template | 2026-09-25 | Yes |
| [01-project-setup.md](../learning/01-project-setup.md) | Project Setup (Phase 1) | How-to / learning note | 2026-09-30 | Yes |
| [02-database-persistence.md](../learning/02-database-persistence.md) | Database & Persistence (Phase 2) | How-to / learning note | 2026-09-26 | Yes |
| [03-ingestion-chunking.md](../learning/03-ingestion-chunking.md) | Ingestion & Chunking (Phase 3) | How-to / learning note | 2026-09-26 | Yes |
| [04-embeddings-retrieval.md](../learning/04-embeddings-retrieval.md) | Embeddings & Hybrid Retrieval (Phase 4) | How-to / learning note | 2026-09-27 | Yes |
| [05-investigation-engine.md](../learning/05-investigation-engine.md) | Investigation Engine (Phase 5) | How-to / learning note | 2026-09-27 | Yes |
| [06-langgraph-agent.md](../learning/06-langgraph-agent.md) | Grounding & Confidence with LangGraph (Phase 6) | How-to / learning note | 2026-09-27 | Yes |
| [07-mcp-integration.md](../learning/07-mcp-integration.md) | Controlled Tools & Audit (Phase 7) | How-to / learning note | 2026-09-29 | Yes |
| [08-evaluation.md](../learning/08-evaluation.md) | Evaluation (Phase 8) | How-to / learning note | 2026-09-30 | Yes |
| [09-production-api.md](../learning/09-production-api.md) | Production CLI / API (Phase 9) | How-to / learning note | 2026-09-30 | Yes |
| [README.md](../learning/README.md) | IncidentWeave — Learning Log | Index | 2026-09-30 | Index |

### `docs/notes/`

**Observed from the tree:** Numbered notes 01–18 are indexed. Note 19 is the current draft
inventory and is added to the index in this PR.

| File | Title | Apparent kind | Last changed | README index |
|---|---|---|---|---|
| [01-manual-verification.md](01-manual-verification.md) | Manual Verification and Improvements | Note / manual test record | 2026-10-21 | Yes |
| [02-deferred-optimizations.md](02-deferred-optimizations.md) | Later Optimizations and Follow-up Notes | Living deferred-work note | 2026-11-01 | Yes |
| [03-embedding-benchmark.md](03-embedding-benchmark.md) | Embedding Benchmark | Frozen benchmark note | 2026-10-24 | Yes |
| [04-offline-retrieval-evaluation.md](04-offline-retrieval-evaluation.md) | Offline Retrieval Evaluation | Evaluation reference / result | 2026-10-27 | Yes |
| [05-multi-repo-evaluation.md](05-multi-repo-evaluation.md) | Multi-Repository Evaluation | Evaluation reference / result | 2026-10-27 | Yes |
| [06-chunking-strategies.md](06-chunking-strategies.md) | Chunking strategies | Living reference / experiment summary | 2026-10-27 | Yes |
| [07-retrieval-inspection-report.md](07-retrieval-inspection-report.md) | Retrieval inspection report | How-to / report reference | 2026-10-27 | Yes |
| [08-fulltext-diagnostic.md](08-fulltext-diagnostic.md) | Full-text diagnostic (item 14c-1) | Frozen diagnostic | 2026-10-27 | Yes |
| [09-fulltext-ablation-results.md](09-fulltext-ablation-results.md) | Full-text ablation results (item 14c-2) | Frozen experiment result | 2026-10-27 | Yes |
| [10-provider-usage-log.md](10-provider-usage-log.md) | Provider Usage Log | Living telemetry reference | 2026-10-30 | Yes |
| [11-test-file-diagnostic.md](11-test-file-diagnostic.md) | Test-file retrieval diagnostic | Frozen diagnostic | 2026-10-30 | Yes |
| [12-test-file-comparison-results.md](12-test-file-comparison-results.md) | Test-file retrieval comparison results | Frozen experiment result | 2026-10-30 | Yes |
| [13-groq-generation-fallback.md](13-groq-generation-fallback.md) | Optional Groq Generation Fallback | Living route / privacy how-to | 2026-10-30 | Yes |
| [14-embedding-task-type-experiment.md](14-embedding-task-type-experiment.md) | Embedding task-type comparison (item 14a) | Protocol | 2026-10-31 | Yes |
| [15-embedding-task-type-results.md](15-embedding-task-type-results.md) | Embedding task-type comparison: development | Frozen experiment result | 2026-10-31 | Yes |
| [16-test-tiers.md](16-test-tiers.md) | Test tiers and scaling | Living how-to / test reference | 2026-10-31 | Yes |
| [17-bm25-comparison-results.md](17-bm25-comparison-results.md) | BM25 comparison results (item 14d) | Frozen experiment result | 2026-10-31 | Yes |
| [18-local-embedding-results.md](18-local-embedding-results.md) | Local embedding-model comparison results | Frozen experiment result | 2026-11-01 | Yes |
| [19-repository-inventory.md](19-repository-inventory.md) | Repository inventory | Draft inventory / proposal | 2026-11-01 | Added in this PR |
| [README.md](README.md) | Notes | Index | 2026-11-01 | Index |

### `docs/phases/`

**Observed from the tree:** The folder README indexes the nine phase records; `08b` is an
additional phase-8 record between 08 and 09.

| File | Title | Apparent kind | Last changed | README index |
|---|---|---|---|---|
| [01-project-setup.md](../phases/01-project-setup.md) | Phase 1 — Project Setup | Frozen phase log | 2026-10-21 | Yes |
| [02-database-persistence.md](../phases/02-database-persistence.md) | Phase 2 — Database & Persistence | Frozen phase log | 2026-10-21 | Yes |
| [03-ingestion-chunking.md](../phases/03-ingestion-chunking.md) | Phase 3 — Repository Ingestion & Chunking | Frozen phase log | 2026-10-21 | Yes |
| [04-embeddings-retrieval.md](../phases/04-embeddings-retrieval.md) | Phase 4 — Embeddings & Retrieval | Frozen phase log | 2026-10-21 | Yes |
| [05-investigation-engine.md](../phases/05-investigation-engine.md) | Phase 5 — Investigation Engine | Frozen phase log | 2026-10-21 | Yes |
| [06-grounding-confidence.md](../phases/06-grounding-confidence.md) | Phase 6 — Grounding & Confidence | Frozen phase log | 2026-10-21 | Yes |
| [07-controlled-tools-audit.md](../phases/07-controlled-tools-audit.md) | Phase 7 — Controlled Tools & Audit | Frozen phase log | 2026-10-21 | Yes |
| [08-evaluation.md](../phases/08-evaluation.md) | Phase 8 — Evaluation | Frozen phase log | 2026-10-21 | Yes |
| [08b-evaluation-improvements.md](../phases/08b-evaluation-improvements.md) | Phase 8b — Evaluation Improvements | Frozen phase log | 2026-10-27 | Yes |
| [09-production-api.md](../phases/09-production-api.md) | Phase 9 — Production CLI / API | Frozen phase log | 2026-10-21 | Yes |
| [README.md](../phases/README.md) | Phase build logs | Index | 2026-10-21 | Index |

### `docs/`

**Observed from the tree:** The root index links to documentation areas rather than indexing
each file directly.

| File | Title | Apparent kind | Last changed | README index |
|---|---|---|---|---|
| [README.md](../README.md) | Documentation | Root documentation index | 2026-10-30 | Index |

### Observed documentation overlaps and maintenance risks

- **Observed:** `docs/phases/` and `docs/learning/` both describe phases 1–9, with different
  purposes and audiences; several architecture and notes documents also restate implementation
  behavior.
- **Observed:** Chunking material spans the six-file historical review bundle, the living
  chunking plan, phase logs, and note 06. Readers must distinguish decision history from current
  behavior.
- **Observed:** Experiment protocols are kept in architecture-review or notes folders while
  corresponding results are in notes and aggregate JSON is under `evaluation/experiments/`.
  The relationships are indexed but not co-located.
- **Observed:** Note 16 records a 428-test run with 251 unit tests and historical timings. The
  present test tree has since expanded; its text also says the fast tier remains over the 30
  second target. The current local unit runtime is reported as about 33 seconds, so timing
  statements should be labelled by run/date and refreshed when verified.
- **Observed:** No numbered content document was absent from its folder README filename index in
  the inspected snapshot. README indexes do not link to themselves by design.
- **Observed:** No exact same-folder duplicate filenames or duplicate two-digit document numbers
  were found. `08` and `08b` in `docs/phases/` are related but distinct sequence labels.

## B. Scripts and evaluation modules

**Observed from the tree:** The list covers 22 tracked `scripts/*.py` files and 27 tracked
`evaluation/*.py` files, including package initializers. “Test matches” and “Doc matches” are
counts of files containing the basename, not a proof of complete coverage or a direct link.
“No direct match” means no basename match was found; indirect coverage remains undetermined.

### `scripts/`

| Module | Observed purpose | Test matches | Doc matches |
|---|---|---:|---:|
| [__init__.py](../../scripts/__init__.py) | Command-line scripts and importable repository utilities. | 11* | 4* |
| [benchmark_embeddings.py](../../scripts/benchmark_embeddings.py) | Live Gemini benchmark; sends existing database chunk text to the embedding API. | No direct match | 2 |
| [check_retrieval_gate.py](../../scripts/check_retrieval_gate.py) | Run manifest-selected offline retrieval gates and report per-repository and pooled metrics. | 1 | 4 |
| [compare_bm25.py](../../scripts/compare_bm25.py) | Run the registered BM25 comparison against development fixtures only. | No direct match | No direct match |
| [compare_runs.py](../../scripts/compare_runs.py) | Compare two saved evaluation reports and print deltas. | 1 | 2 |
| [compare_test_file_variants.py](../../scripts/compare_test_file_variants.py) | Run the registered test-file ranking comparison on development fixtures only. | 1 | No direct match |
| [diagnose_fulltext.py](../../scripts/diagnose_fulltext.py) | Diagnose full-text query behavior against committed development fixtures. | No direct match | No direct match |
| [diagnose_test_files.py](../../scripts/diagnose_test_files.py) | Report test-file representation and control retrieval in development fixtures. | No direct match | No direct match |
| [embed_chunks.py](../../scripts/embed_chunks.py) | Embed unembedded repository chunks using the Gemini embedding API. | 5 | 18 |
| [ingest_repo.py](../../scripts/ingest_repo.py) | Ingest a local repository into the IncidentWeave chunk schema. | 4 | 26 |
| [inspect_retrieval.py](../../scripts/inspect_retrieval.py) | Generate deterministic Markdown cards for offline retrieval inspection. | 1 | 1 |
| [investigate.py](../../scripts/investigate.py) | Run the full investigation pipeline for a repository query. | 4 | 22 |
| [run_chunking_experiment.py](../../scripts/run_chunking_experiment.py) | Prepare, embed, and evaluate the precommitted chunking comparison. | 1 | 1 |
| [run_embedding_task_type_experiment.py](../../scripts/run_embedding_task_type_experiment.py) | Plan, run, and compare the registered development embedding task-type experiment. | 1 | 1 |
| [run_eval.py](../../scripts/run_eval.py) | Run the Phase 8 retrieval and investigation evaluation. | 1 | 8 |
| [run_fulltext_ablation.py](../../scripts/run_fulltext_ablation.py) | Run the registered item 14c-2 development-only full-text ablation. | No direct match | No direct match |
| [run_local_embedding_experiment.py](../../scripts/run_local_embedding_experiment.py) | Plan, embed, and evaluate the registered development-only local models. | 1 | No direct match |
| [run_retrieval_eval.py](../../scripts/run_retrieval_eval.py) | Run the offline retrieval-only evaluation. | No direct match | 3 |
| [search_repo.py](../../scripts/search_repo.py) | Search repository chunks with hybrid vector and full-text retrieval. | No direct match | 7 |
| [serve.py](../../scripts/serve.py) | Launch the API with a psycopg-compatible Windows event loop. | 17 | 36 |
| [test_tiers.py](../../scripts/test_tiers.py) | Run a documented test tier with its required pytest settings. | 1 | 1 |
| [usage_report.py](../../scripts/usage_report.py) | Read and summarize provider usage recorded in the application database. | 2 | 2 |

### `evaluation/`

| Module | Observed purpose | Test matches | Doc matches |
|---|---|---:|---:|
| [__init__.py](../../evaluation/__init__.py) | Evaluation utilities for the retrieval and investigation pipeline. | 11* | 4* |
| [bm25.py](../../evaluation/bm25.py) | Pure BM25 ranking and decision helpers for item 14d. | 1 | 5 |
| [build_fixture.py](../../evaluation/build_fixture.py) | Build the offline retrieval fixture from cached embeddings and the evaluation DB. | 1 | 4 |
| [chunk_experiments.py](../../evaluation/chunk_experiments.py) | Chunking strategies supported by the evaluation harness only. | 3 | 6 |
| [chunking_experiment.py](../../evaluation/chunking_experiment.py) | Deterministic preparation and analysis for the chunking comparison. | 1 | 1 |
| [compare.py](../../evaluation/compare.py) | Compare evaluation runs in a stable, legacy-tolerant way. | 6 | 22 |
| [compare_chunking_runs.py](../../evaluation/compare_chunking_runs.py) | Compare saved chunking-evaluation runs without a DB or API. | 1 | 3 |
| [corpus.py](../../evaluation/corpus.py) | Pinned evaluation corpus setup, restricted to `incidentweave-eval`. | 3 | 26 |
| [embedding_task_type.py](../../evaluation/embedding_task_type.py) | Pure helpers for the registered Gemini embedding task-type experiment. | 1 | 2 |
| [fulltext_ablation.py](../../evaluation/fulltext_ablation.py) | Fixture-backed runners and metrics for the registered full-text ablation. | No direct match | No direct match |
| [fulltext_diagnostic.py](../../evaluation/fulltext_diagnostic.py) | Pure helpers for diagnosing PostgreSQL full-text query terms. | 1 | No direct match |
| [fulltext_experiment.py](../../evaluation/fulltext_experiment.py) | Execute and render the item 14c-2 development-only full-text ablation. | No direct match | No direct match |
| [gate.py](../../evaluation/gate.py) | Pure loading and evaluation for the offline retrieval regression gate. | 14 | 42 |
| [golden.py](../../evaluation/golden.py) | Golden-set loading and validation. | 5 | 21 |
| [inspection.py](../../evaluation/inspection.py) | Pure Markdown rendering for offline retrieval inspection reports. | 1 | 19 |
| [local_embedding.py](../../evaluation/local_embedding.py) | Pure helpers for the registered local embedding-model comparison. | 1 | 1 |
| [manifest.py](../../evaluation/manifest.py) | Loading and fail-closed validation for the multi-repository evaluation manifest. | 7 | 18 |
| [metrics.py](../../evaluation/metrics.py) | Pure, deterministic metrics for Phase 8 evaluation. | 8 | 22 |
| [retrieval_eval.py](../../evaluation/retrieval_eval.py) | Offline hybrid-retrieval evaluation using committed embeddings. | 5 | 6 |
| [runner.py](../../evaluation/runner.py) | Run Phase 8 evaluation without changing production pipeline behavior. | 4 | 13 |
| [span_labels.py](../../evaluation/span_labels.py) | Derive stable, chunk-independent relevance spans from golden substring labels. | 1 | 1 |
| [splits.py](../../evaluation/splits.py) | Deterministic stratified question assignments for repository evaluations. | 8 | 6 |
| [stats.py](../../evaluation/stats.py) | Small, dependency-free statistics for retrieval evaluation. | 2 | 2 |
| [test_file_comparison.py](../../evaluation/test_file_comparison.py) | Metrics and preregistered decision rules for test-file ranking variants. | 1 | No direct match |
| [test_file_diagnostic.py](../../evaluation/test_file_diagnostic.py) | Pure helpers for the test-file retrieval diagnostic. | 1 | No direct match |
| [test_file_variants.py](../../evaluation/test_file_variants.py) | Pure implementations of the registered test-file ranking variants. | 2 | No direct match |
| [test_files.py](../../evaluation/test_files.py) | Path rules for identifying test-source files in evaluation fixtures. | 1 | 3 |

**Observed maintenance signals:** `benchmark_embeddings.py` explicitly makes live provider
calls and is a manual benchmark, not an ordinary CI path. `compare_bm25.py`, the diagnostic
scripts, and `run_fulltext_ablation.py` had no direct basename test or documentation match in
the search; their relationship to the tested evaluation helpers should be checked before any
cleanup. Conversely, a basename match alone does not establish that a CLI path is executed.
Package initializer matches are broad and are not meaningful coverage (`*`).

## C. Tracked large, generated-looking, and data files

**Observed from the tree:** Sizes below are tracked-file metadata. No file in this list was
opened to read its content. Evaluation fixtures, baselines, question sets, and aggregate
reports are intentional evaluation artifacts unless their owners decide otherwise; their
generated appearance alone does not make them junk.

| Path | Size (bytes) | Observed classification |
|---|---:|---|
| `docs/assets/social-preview.png` | 784,658 | Image asset; sizable but intentional-looking |
| `docs/chunking-experiment/03-human-review-workbook.md` | 363,843 | Frozen review workbook |
| `docs/chunking-experiment/06-review-chatgpt.md` | 125,782 | Frozen review |
| `docs/phases/08b-evaluation-improvements.md` | 124,945 | Historical phase record |
| `evaluation/experiments/chunking/report-development.json` | 292,917 | Aggregate development report |
| `evaluation/experiments/fulltext/results.json` | 85,371 | Experiment aggregate output |
| `evaluation/experiments/bm25/results.json` | 8,383 | Experiment aggregate output |
| `evaluation/experiments/chunking/fixtures/batch-processing-service/s1_lines_100_20.json.gz` | 131,427 | Strategy fixture |
| `evaluation/experiments/chunking/fixtures/batch-processing-service/s2_ast_v1.json.gz` | 221,686 | Strategy fixture |
| `evaluation/experiments/chunking/fixtures/batch-processing-service/s3_ast_v1_embed_text.json.gz` | 221,804 | Strategy fixture |
| `evaluation/experiments/chunking/fixtures/incidentweave/s1_lines_100_20.json.gz` | 201,227 | Strategy fixture |
| `evaluation/experiments/chunking/fixtures/incidentweave/s2_ast_v1.json.gz` | 318,522 | Strategy fixture |
| `evaluation/experiments/chunking/fixtures/incidentweave/s3_ast_v1_embed_text.json.gz` | 318,577 | Strategy fixture |
| `evaluation/experiments/chunking/fixtures/lifeos/s1_lines_100_20.json.gz` | 160,477 | Strategy fixture |
| `evaluation/experiments/chunking/fixtures/lifeos/s2_ast_v1.json.gz` | 237,127 | Strategy fixture |
| `evaluation/experiments/chunking/fixtures/lifeos/s3_ast_v1_embed_text.json.gz` | 237,135 | Strategy fixture |
| `evaluation/fixtures/retrieval_fixture.json.gz` | 244,868 | Retrieval fixture |
| `evaluation/repos/batch-processing-service/retrieval_fixture.json.gz` | 159,548 | Repository retrieval fixture |
| `evaluation/repos/lifeos/retrieval_fixture.json.gz` | 183,993 | Repository retrieval fixture |
| `evaluation/results/baseline.json` | 248,618 | Baseline data; content not opened |
| `evaluation/results/offline-baseline.json` | 12,047 | Baseline data; content not opened |
| `evaluation/results/incidentweave-smoke-baseline.json` | 4,277 | Baseline data; content not opened |
| `evaluation/repos/batch-processing-service/questions.json` | 24,790 | Question data; content not opened |
| `evaluation/repos/lifeos/questions.json` | 20,041 | Question data; content not opened |
| `evaluation/golden_set.json` | 12,507 | Golden question/label data; content not opened |
| `evaluation/manifest.json` | 9,341 | Evaluation manifest metadata |
| `docs/notes/12-test-file-comparison-results.json` | 10,418 | Aggregate comparison data |
| `tests/fixtures/phase7_grep_probe.py` | 4,319 | Test fixture source, not a runtime output |
| `evaluation/results/runs/.gitkeep` | 0 | Empty tracked directory placeholder |

**Observed:** No obvious tracked log, temporary file, local model cache, or run-specific local
embedding vector cache was identified. The model/vector caches are ignored and therefore
outside this tracked-file listing.

## D. Naming and index observations

- **Observed:** Numbered documents generally use two digits and kebab-case, while Python files
  and test-area directories use snake_case. This is idiomatic within each ecosystem but means
  path transformation is not uniform.
- **Observed:** `docs/phases/08-evaluation.md` and `08b-evaluation-improvements.md` use a
  suffix sequence rather than a unique two-digit number; checklist subitems also use suffixes
  such as `14a-1` and `18d-4`.
- **Observed:** Experiment results and protocols use different numbering namespaces: for
  example, architecture-review item 14 is paired with notes 14/15, while item 18c results are
  note 18 and item 18d design is architecture-review 13.
- **Observed:** The documentation tree has a root index and one README in each of its six
  content folders. No unindexed content file was detected by the filename-presence check.
- **Observed:** Evaluation includes both hyphenated repository folder names and snake_case
  experiment/module names; tests have tier directories with underscore-separated area names.

## E. Current test layout

**Observed from the tree:** Counts are Python files by test tier/area, not collected test
functions. Root conftest and fixtures are listed separately. The latest test-case counts in
note 16 are historical and are not asserted as current here.

| Tier / location | Python files |
|---|---:|
| Unit | 30 |
| Evaluation | 15 |
| Integration | 8 |
| Test root (`conftest.py`) | 1 |
| Fixtures | 1 |
| **Total test-tree Python files** | **55** |

| Tier | Area | Python files |
|---|---|---:|
| Unit | api | 2 |
| Unit | db | 1 |
| Unit | evaluation | 3 |
| Unit | investigation | 7 |
| Unit | providers | 7 |
| Unit | retrieval | 4 |
| Unit | scripts | 4 |
| Evaluation | chunking | 2 |
| Evaluation | embedding_task_type | 1 |
| Evaluation | fulltext | 1 |
| Evaluation | local_embeddings | 1 |
| Evaluation | manifest_and_splits | 2 |
| Evaluation | retrieval_eval | 4 |
| Evaluation | tier root | 1 |
| Evaluation | test_files | 3 |
| Integration | db | 2 |
| Integration | ingestion | 1 |
| Integration | providers | 1 |
| Integration | retrieval | 4 |

**Observed (maintainer-reported in the task, not remeasured here):** The unit tier now runs in
about 33 seconds locally. Note 16 documents an earlier 428-test run (251 unit, 10 integration,
167 evaluation) and much slower local timing; those values should be treated as dated history,
not the current runtime.

## F. Proposed target documentation structure

**Proposal only; no folders or files were moved in this PR.**

### Option A — organize by document purpose

**Proposal:** Use `docs/reference/` for living architecture, configuration and API behavior;
`docs/decisions/` for approved/rejected decision records; `docs/experiments/` for frozen
protocol/result pairs; `docs/runbooks/` for operational procedures; `docs/how-to/` for
developer and user guides; and `docs/history/` for immutable phase logs, audits and review
artifacts. Label each document `Living`, `Frozen`, `Draft`, or `Superseded` at the top. Keep one
canonical `docs/README.md` status index that links each document with owner, status, and
superseding record; local README files can remain navigation indexes.

**Trade-off:** Purpose-based folders make current references and historical evidence easier to
distinguish at scale, but moving files creates link churn and can disrupt external references.
The migration would need redirects or stable aliases, an automated link check, and explicit
freeze rules.

### Option B — retain current folders and add canonical metadata

**Proposal:** Keep `architecture/`, `architecture-review/`, `phases/`, `learning/`,
`chunking-experiment/`, and `notes/`; add a small status/type header to documents and make
`docs/README.md` the single cross-folder status index. Preserve per-folder README files as
indexes and add explicit links between every protocol, result, decision, and current reference.

**Trade-off:** This minimizes link and history disruption and can be done incrementally, but the
existing area-based taxonomy continues to mix purposes and some historical/current behavior
overlaps remain.

**Proposal:** Prefer Option B as the first cleanup step, then consider Option A only after the
index and document lifecycle labels expose which files can be moved safely.
