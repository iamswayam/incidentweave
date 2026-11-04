# Evaluation studies

Completed experiment implementations live here; their result artifacts remain in their
existing locations. The `scripts.*` commands below are retained as thin CLI wrappers.

| Study | What it tested | Status | Command | Result artifacts |
|---|---|---|---|---|
| [Full-text](fulltext/) | PostgreSQL full-text diagnostics and registered retrieval ablation. | Completed, kept reproducible | `python -m scripts.run_fulltext_ablation`; `python -m scripts.diagnose_fulltext` | `evaluation/experiments/fulltext/`; diagnostic note in `docs/notes/08-fulltext-diagnostic.md` |
| [BM25](bm25/) | Registered BM25 ranking candidate against the production control. | Completed, kept reproducible | `python -m scripts.compare_bm25` | `evaluation/experiments/bm25/` |
| [Test files](test_files/) | Test-file classification, diagnostics, and registered ranking variants. | Completed, kept reproducible | `python -m scripts.diagnose_test_files`; `python -m scripts.compare_test_file_variants` | `docs/notes/11-test-file-diagnostic.md` and `docs/notes/12-test-file-comparison-results.md` with the adjacent JSON; no result artifact moved |

Study code lives under `evaluation/studies/`; result artifacts stay in their existing
`evaluation/experiments/<name>/` or documented notes locations.
