# Evaluation studies

Completed experiment implementations live here; their result artifacts remain in their
existing locations. The `scripts.*` commands below are retained as thin CLI wrappers.

| Study | What it tested | Status | Command | Result artifacts |
|---|---|---|---|---|
| [Full-text](fulltext/) | PostgreSQL full-text diagnostics and registered retrieval ablation. | Completed, kept reproducible | `python -m scripts.run_fulltext_ablation`; `python -m scripts.diagnose_fulltext` | `evaluation/experiments/fulltext/`; diagnostic note in `docs/notes/08-fulltext-diagnostic.md` |
| [BM25](bm25/) | Registered BM25 ranking candidate against the production control. | Completed, kept reproducible | `python -m scripts.compare_bm25` | `evaluation/experiments/bm25/` |
| [Test files](test_files/) | Test-file classification, diagnostics, and registered ranking variants. | Completed, kept reproducible | `python -m scripts.diagnose_test_files`; `python -m scripts.compare_test_file_variants` | `docs/notes/11-test-file-diagnostic.md` and `docs/notes/12-test-file-comparison-results.md` with the adjacent JSON; no result artifact moved |
| [Chunking](chunking/) | Registered chunking candidates and offline comparison of saved evaluation runs. | Completed, kept reproducible | `python -m scripts.run_chunking_experiment`; `python -m evaluation.studies.chunking.compare_chunking_runs` | `evaluation/experiments/chunking/`; comparison JSON remains alongside the selected run under `evaluation/results/runs/` |
| [Embedding task type](embedding_task_type/) | Registered Gemini document/query task-type candidate against the control. | Completed, kept reproducible | `python -m scripts.run_embedding_task_type_experiment` | Ignored candidate cache under `evaluation/cache/embedding_task_type_v1/`; results note in `docs/notes/15-embedding-task-type-results.md` |
| [Local embeddings](local_embedding/) | Registered local embedding-model candidates against the Gemini control. | Completed, kept reproducible | `python -m scripts.run_local_embedding_experiment` | Ignored candidate cache under `evaluation/cache/local_embedding_v1/`; results note in `docs/notes/18-local-embedding-results.md` |

Study code lives under `evaluation/studies/`; result artifacts stay in their existing
`evaluation/experiments/<name>/` or documented notes locations.

The full-text study uses shared helpers from the chunking study; this cross-study dependency
does not make the evaluation core depend on either study.
