# Phase 3 — Repository Ingestion & Chunking

**Status:** Complete
**Depends on:** Phase 2 schema (Repository, Chunk models + migration) — confirmed working.

---

## Checkpoint 1 — Ingestion script structure

**Task:** Walk a local repository and identify files to ingest.

### Log
- `scripts/ingest_repo.py` takes a repo path and repository `name` as CLI
  args, creates or reuses a `Repository` row, and walks the path for `.py`
  files via `rglob`, skipping any path containing a directory in `IGNORE_DIRS`.
- `IGNORE_DIRS` started as `{".git", ".venv", "__pycache__", "migrations"}`.

---

## Checkpoint 2 — Chunking window logic

**Task:** Split file content into fixed-size overlapping line windows.

### Log
- `chunk_lines()` uses a 60-line window with 10-line overlap (`step = 50`).
- **Bug found by testing, not by reading the code:** the original version
  produced a redundant final window whenever the second-to-last window
  already reached end-of-file — e.g. a 201-line file yielded a useless
  extra `(200, 201)` window on top of `(150, 201)`, which already covered
  it. Found by running the windowing logic against files of several exact
  lengths (5, 60, 61, 110, 150, 200, 201, 500 lines) and inspecting where
  the last window landed.
- **Fix:** track `previous_end` across iterations and skip any window that
  doesn't extend past it. Re-tested against the same length set — confirmed
  no redundant windows at any boundary.

---

## Checkpoint 3 — Idempotent re-ingestion

**Task:** Ensure re-running ingestion doesn't duplicate data.

### Log
- **Gap found, not by Copilot, by applying prior production experience:**
  the original script had no protection against duplicate `Chunk` rows if
  run twice on the same repository name. Caught by drawing on idempotent
  webhook-processing experience from production work (McDonald's/E-Z Auto),
  not something flagged automatically.
- **Fix:** `delete(Chunk).where(Chunk.repository_id == repository.id)`
  runs before the insert, in the same transaction, so re-ingestion is a
  clean replace, not an accumulation.

---

## Checkpoint 4 — Corpus cleanliness

**Task:** Ensure only real project code gets ingested.

### Log
- **Found downstream, in Phase 4 retrieval results, not during ingestion
  itself:** Copilot's own `.kilo` tooling directory was being ingested as
  if it were project code, occupying result slots with duplicate content.
- **Fix:** added `.kilo`, `.pytest_cache`, `.ruff_cache` to `IGNORE_DIRS`
  (final set: `.git`, `.kilo`, `.pytest_cache`, `.ruff_cache`, `.venv`,
  `__pycache__`, `migrations`).

---

## Checkpoint 5 — End-to-end verification

**Task:** Confirm real ingestion runs produce correct, clean output.

### Log
- Before the `.kilo` fix: 38 files processed, 46 chunks created (including
  `.kilo` duplicates).
- After the fix: 23 files processed, 31 chunks created — confirmed clean
  via a direct `kilo_chunks = 0` count query against the database, not
  just an assumption that the exclusion worked.
- Ingestion is now idempotent, chunk boundaries are non-redundant, and the
  corpus contains only real project files.

---

## After all checkpoints

Phase 3 turned Phase 2's unused schema into a real, populated, clean corpus
— setting up exactly what Phase 4 (embeddings + retrieval) needed to
operate on.
