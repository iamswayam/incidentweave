# Ingestion & Chunking (Phase 3)

**Date built:** September 2026
**Status:** Working, pressure-tested

## What I built

`scripts/ingest_repo.py` — a CLI script that walks a local Python repository,
splits each `.py` file into fixed-size overlapping line windows (60 lines,
10-line overlap), and writes them as `Chunk` rows tied to a `Repository` row
in Postgres. It's idempotent: re-running it for the same repository name
deletes that repository's existing chunks before re-inserting, so repeated
runs don't accumulate duplicates. It skips `.git`, `.kilo`, `.pytest_cache`,
`.ruff_cache`, `.venv`, `__pycache__`, and `migrations`.

## Why this design

Line-window chunking instead of AST-aware (function/class-boundary) chunking
— deliberately, to keep V1 simple and get a working ingestion → embedding →
retrieval pipeline end to end before investing in smarter chunk boundaries.
The `chunk_lines()` window logic specifically tracks `previous_end` and skips
any window that wouldn't add new content beyond what's already covered — this
was a fix, not the original design (see "what broke" below).

Idempotency via delete-then-insert, not upsert-by-content-hash — simpler to
reason about, and matches how this script is actually used (re-ingest a whole
repo at once, not update individual chunks).

## Key concept, explained simply

<!-- Write this yourself: explain fixed-size overlapping chunking — what
problem the overlap solves, and why a chunk boundary landing mid-function is
an acceptable tradeoff for V1 — as if to someone who's never seen a RAG
pipeline before. -->

## Walkthrough example

Ran against the IncidentWeave repo itself twice, before and after excluding
Copilot's own `.kilo` tooling directory:

- **Before excluding `.kilo`:** 38 files processed, 46 chunks created —
  including duplicate content from `.kilo/worktrees/...` polluting retrieval
  results later in Phase 4.
- **After adding `.kilo`, `.pytest_cache`, `.ruff_cache` to `IGNORE_DIRS`:**
  23 files processed, 31 chunks created — confirmed clean via a direct
  `kilo_chunks = 0` count query against the database.

## What broke when I tested it

Two real bugs found by testing, not by reading:

1. **Redundant trailing window.** The original `chunk_lines()` produced a
   near-duplicate final window for files where the second-to-last window
   already reached the end of the file — e.g. a 201-line file yielded a
   useless extra `(200, 201)` window on top of `(150, 201)`, which already
   covered it. Found by running the windowing logic against files of several
   exact lengths (5, 60, 61, 110, 150, 200, 201, 500 lines) and checking
   where the last window landed. Fixed by tracking `previous_end` and
   skipping any window that doesn't extend past it.

2. **Not idempotent.** The original script had no protection against
   duplicate rows if run twice on the same repository — an actual gap I
   caught by applying my own production experience with idempotent webhook
   processing (McDonald's/E-Z Auto work) to this script, rather than
   something Copilot flagged on its own. Fixed with a `delete(Chunk).where(...)`
   before the insert, in the same transaction.

3. **`.kilo` pollution** — Copilot's own internal working directory was
   getting ingested as if it were project code, occupying result slots in
   Phase 4's retrieval output with duplicate content. Not a logic bug, a
   scope bug — `IGNORE_DIRS` didn't know about tooling directories that
   don't exist in a typical repo checkout.

## Interview-ready summary (3-4 sentences)

<!-- Write this yourself, once the "key concept" section above is filled in.
Should cover: what the script does, the idempotency decision, and the
redundant-window bug as a concrete example of testing revealing something
code review alone wouldn't have caught. -->
