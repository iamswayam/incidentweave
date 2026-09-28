# Phase 7 — Controlled Tools & Audit

**Status:** Complete — Checkpoint 11 passed all required verification commands.
**Depends on:** Phase 6 (LangGraph retry/calibration, verified working) — confirmed.

Same pattern as Phases 3-6: this document is the task spec AND the running
log. Fill in each checkpoint's "Log" section with real detail before moving
on. Run every command for real — no simulated output. The person is away
for this session; do not wait for input, make and justify design decisions
yourself where the checkpoint asks for one, and continue.

**Why this phase exists, precisely:** Phase 6 found, and proved
mathematically, that widening the search limit can never fix a guard
rejection caused by vector distance — the nearest neighbor's distance is
invariant to limit, by construction. This phase adds a genuinely different
fallback: a literal keyword search over the raw source files on disk,
which doesn't share that limitation, exposed as a real MCP tool. This is
the first place "AI Agents + MCP" becomes a fully real, defensible claim
rather than a course-level one.

**Honest note on MCP here, stated plainly rather than glossed over:** a
single-process app calling its own function through MCP is more machinery
than the app strictly needs — a direct function call would work identically.
The reason to do it anyway is genuine MCP experience: a real process
boundary (client/server over stdio), a real tool schema, a real client
call — not a class that wraps a function and calls itself an MCP tool. Say
this in the log, don't hide it.

**Scope for this session, do not exceed it:**
- One new tool: `grep_search` — literal keyword search over raw ingested
  source files (not the chunked/embedded index).
- Exposed via a real local MCP server (stdio transport, the SDK's simplest
  option) alongside the existing `hybrid_search` as a second MCP tool.
- **Controlled** escalation: a fixed, deterministic order (widen-limit
  retry from Phase 6 → if still insufficient, try `grep_search` via MCP →
  if still insufficient, return `INSUFFICIENT_EVIDENCE`). The LLM does NOT
  freely choose which tool to call — that's a future, riskier enhancement,
  not this session. "Controlled" is the operative word in this phase's name.
- `Audit.tool_calls` (a field designed back in Phase 2, barely used since)
  finally gets a full, real multi-step trace of what was tried and why.
- No human-in-the-loop gate this phase — there's no remediation action to
  gate yet, only diagnosis. That's a later phase, once there's something
  real for a human to approve.

---

## Checkpoint 1 — Confirm the MCP SDK, don't assume its API

**Task:** Before writing any code, install the official Python MCP SDK in
the project venv and check its real current API from the installed package
itself — same discipline as Phase 6 Checkpoint 1 for LangGraph, and for the
same reason this project has been burned twice already by assumed APIs.
Confirm: the exact package name for `pyproject.toml`, the installed
version, and the real shape of server creation, tool registration
(decorator or explicit registration — check which), and client connection
(stdio transport specifically) by importing and inspecting the real
package, not from memory or a tutorial.

### Log
- Package name and version installed: official PyPI package `mcp`, version `1.30.0` in the project venv. An initial unpinned install selected MCP 2.x; importing `mcp.server.fastmcp` raised the package's own `ModuleNotFoundError` explaining that FastMCP was renamed in 2.x. Per that installed-package message, installed the compatible v1 line and added the explicit runtime bound `mcp>=1.30,<2.0` to `pyproject.toml`.
- Real server/tool-registration/client API confirmed from installed 1.30.0: `FastMCP(name=...)` creates the server; `@server.tool(name=..., description=...)` is the actual decorator API and calls `self.add_tool(...)`; `server.run(transport="stdio")` selects stdio; `StdioServerParameters(command=..., args=..., env=..., cwd=...)` configures the child process; `stdio_client(server_params)` is an async context manager that spawns that process and transfers newline-delimited JSON-RPC over child stdin/stdout; `ClientSession(read_stream, write_stream)` wraps the transport and exposes session methods. Inspected the installed signatures and source, not a tutorial.
- Actual package inspection output: `distribution: 1.30.0`; `FastMCP.tool(self, name=None, title=None, description=None, ...)`; `FastMCP.run(self, transport: Literal['stdio', 'sse', 'streamable-http']='stdio', ...)`; `StdioServerParameters(*, command: str, args: list[str]=..., env: dict[str, str] | None=None, cwd: str | Path | None=None, ...)`; `stdio_client(server: StdioServerParameters, errlog=sys.stderr)`. The inspected stdio-client source confirms it launches a subprocess and communicates over stdin/stdout.
- Install verification: after adding the constraint, `python -m pip install -e .` reported `Requirement already satisfied: mcp<2.0,>=1.30 ... (1.30.0)` and ended `Successfully installed incidentweave-0.1.0`.

---

## Checkpoint 2 — Design decisions

**Task:** Decide and write down:
1. **`grep_search` behavior** — exact search method (plain substring? simple
   regex?), which files it searches (same `IGNORE_DIRS` as `ingest_repo.py`,
   reused not reinvented), what it returns, and how that return shape maps
   onto the same fields `hybrid_search` results use (`file_path`,
   `line_start`, `line_end`, `content`) so it can flow into the existing
   guard/prompt machinery without special-casing
2. **Escalation trigger** — exact condition for trying `grep_search`
   (should be: widen-limit retry from Phase 6 already happened AND still
   insufficient)
3. **`grep_search` "sufficient" determination** — since it has no RRF/vector
   score, decide how its results get evaluated for evidence-sufficiency
   (e.g. any non-empty match count counts as sufficient, or require a
   minimum number of matches — pick one, state why)
4. **`tool_calls` audit shape** — exact JSON structure for the full
   multi-step trace (each attempted tool, its parameters, and its outcome,
   in order)

### Log
- `grep_search` behavior and return shape: case-insensitive literal substring matching (not regex) over Python source files under an explicit local repository root. Reuse `scripts.ingest_repo.iter_python_files()`, which applies the exact ingestion `IGNORE_DIRS` and `.py` selection. Return one mapping per matched source line, with a synthetic string `id` such as `grep-1`, `repository_id`, `file_path`, `line_start`, `line_end` (the same line), `content` (the matching line), and `vector_score=None`, `fts_score=None`, `rrf_score=None`. The synthetic reference is useful for prompt/citation display but is not a database `Chunk.id`; persistence excludes it from `retrieved_chunk_ids`. No retrieval relevance scores are invented. Cap matches to keep the tool result bounded.
- Escalation trigger, exact condition: call `grep_search` only after the initial hybrid search was insufficient, the single widened-limit retry has run, and that retry's `evaluate_evidence_sufficiency()` result is still insufficient. This route is fixed in the graph; the LLM does not choose a tool.
- `grep_search` sufficiency rule: one or more literal source-line matches count as sufficient. A unique identifier may occur only once; requiring multiple matches would reject direct source evidence without adding meaningful grounding. Zero matches are insufficient. Keep using the existing `evaluate_evidence_sufficiency()` for hybrid results; the grep branch sets the same evidence-check state shape with `is_sufficient`, reason, and null score fields rather than fabricating vector/RRF scores.
- `tool_calls` trace shape: store an ordered `attempts` list; each record contains `tool`, `stage`, `parameters`, and `outcome`. Example structure (schema illustration; actual values will be recorded from the live run):

```json
{
  "attempts": [
    {
      "tool": "hybrid_search",
      "stage": "initial",
      "parameters": {"limit": 5},
      "outcome": {"result_count": 5, "sufficient": false, "reason": "..."}
    },
    {
      "tool": "hybrid_search",
      "stage": "widened_retry",
      "parameters": {"limit": 10},
      "outcome": {"result_count": 10, "sufficient": false, "reason": "..."}
    },
    {
      "tool": "grep_search",
      "stage": "literal_fallback",
      "parameters": {"keyword": "...", "repo_path": "..."},
      "outcome": {"match_count": 1, "sufficient": true}
    }
  ]
}
```

---

## Checkpoint 3 — Build the MCP server exposing `hybrid_search`

**Task:** Create an MCP server (new file, e.g. `app/investigation/mcp_server.py`)
exposing the existing `hybrid_search` function as a real MCP tool over
stdio transport — wrapping it, not reimplementing its logic.

### Log
- File created: `app/investigation/mcp_server.py`. Registered the `hybrid_search` tool with inputs `repository_name: str`, `query_text: str`, `query_embedding: list[float]`, and `limit: int = 10`; its implementation resolves the repository and delegates to the existing `hybrid_search()` function, returning its result as JSON text.
- Real stdio discovery check: launched a separate child process with `StdioServerParameters(command=sys.executable, args=['-m', 'app.investigation.mcp_server'], cwd=<repository root>)`, initialized `ClientSession`, and called `list_tools()`. Actual output: `[('hybrid_search', 'Search one indexed repository with vector and PostgreSQL full-text retrieval.')]`. The probe script was temporary and removed after this successful server/client round trip.

---

## Checkpoint 4 — Build `grep_search` and expose it via the same server

**Task:** Implement `grep_search` per Checkpoint 2's design, and register
it as a second tool on the same MCP server built in Checkpoint 3.

### Log
- File/function location: `grep_search()` in `app/investigation/mcp_server.py`; `grep_search_tool()` exposes it on the same `FastMCP` server as `hybrid_search`. It imports `iter_python_files()` from `scripts.ingest_repo` and returns one hybrid-compatible mapping per matching line, with literal grep IDs and all vector/FTS/RRF fields explicitly `None`.
- Direct real test command: `.\.venv\Scripts\python.exe -c "from app.investigation.mcp_server import grep_search; from pathlib import Path; hits = grep_search(Path('.'), 'AsyncSessionLocal', 4, limit=5); print(hits)"`.
- Actual output:

```python
[
    {'id': 'grep-1', 'repository_id': 4, 'file_path': 'app/db/session.py', 'line_start': 35, 'line_end': 35, 'content': 'AsyncSessionLocal = async_sessionmaker(', 'vector_score': None, 'fts_score': None, 'rrf_score': None},
    {'id': 'grep-2', 'repository_id': 4, 'file_path': 'app/db/session.py', 'line_start': 45, 'line_end': 45, 'content': '    async with AsyncSessionLocal() as session:', 'vector_score': None, 'fts_score': None, 'rrf_score': None},
    {'id': 'grep-3', 'repository_id': 4, 'file_path': 'app/investigation/graph.py', 'line_start': 10, 'line_end': 10, 'content': 'from app.db.session import AsyncSessionLocal', 'vector_score': None, 'fts_score': None, 'rrf_score': None},
    {'id': 'grep-4', 'repository_id': 4, 'file_path': 'app/investigation/graph.py', 'line_start': 48, 'line_end': 48, 'content': '        async with AsyncSessionLocal() as session:', 'vector_score': None, 'fts_score': None, 'rrf_score': None},
    {'id': 'grep-5', 'repository_id': 4, 'file_path': 'app/investigation/mcp_server.py', 'line_start': 14, 'line_end': 14, 'content': 'from app.db.session import AsyncSessionLocal', 'vector_score': None, 'fts_score': None, 'rrf_score': None}
]
```

- Real MCP tool discovery after registration returned: `[('hybrid_search', 'Search one indexed repository with vector and PostgreSQL full-text retrieval.'), ('grep_search', 'Find a literal keyword in Python source files under a local repository path; uses the same file and directory exclusions as ingestion.')]`.

---

## Checkpoint 5 — MCP client + graph escalation wiring

**Task:** Update `app/investigation/graph.py` to add an MCP client that
calls the server built in Checkpoints 3-4. Add a new node/edge: after the
Phase 6 widen-limit retry still fails the guard, call `grep_search` via
the real MCP client (not a direct function call) before falling back to
`insufficient`. Reuse the existing `evaluate_evidence_sufficiency` guard
logic where it applies; extend it, don't fork a parallel copy of it, for
the `grep_search` sufficiency check from Checkpoint 2.

### Log
- Graph changes: retained Phase 6's direct hybrid retrieval, guard, and single widened-limit retry. The guard now routes deterministically: sufficient hybrid evidence proceeds to prompt; first insufficient result widens once; insufficient widened result routes to `grep_search`; the literal-result pass reuses `evaluate_evidence_sufficiency(..., evidence_source="literal")`; a non-match terminates at `insufficient`, while a match proceeds to prompt/generation. The grep node calls `call_grep_search_mcp()` and records its outcome in ordered `tool_calls`; the LLM does not select tools.
- Real client/server round trip: a temporary client script spawned `python -m app.investigation.mcp_server` with `stdio_client`, initialized `ClientSession`, then called `grep_search` for `AsyncSessionLocal`. Actual output began `isError: False`; returned JSON contained two matches, `app/db/session.py:35` (`AsyncSessionLocal = async_sessionmaker(`) and `app/db/session.py:45` (`    async with AsyncSessionLocal() as session:`), each with null vector/FTS/RRF scores. This was a separate child process communicating over stdio, not an in-process function call. The temporary probe file was deleted after the run.

---

## Checkpoint 6 — Populate the full `tool_calls` audit trace

**Task:** Update `app/investigation/persistence.py` (or wherever the graph
result is assembled) so `Audit.tool_calls` records the complete real
sequence of what was attempted this investigation — narrow search, retry
widen (if it happened), `grep_search` (if it happened) — each with its
parameters and outcome, per Checkpoint 2's shape. This is the field Phase 2
designed for exactly this and Phase 5 only partially used.

### Log
- `persist_investigation()` now accepts an optional ordered `tool_call_trace` and stores it under `Audit.tool_calls.attempts`, alongside the existing `cited_chunk_ids` and `retrieval_results`. The graph trace records each tool, stage, parameters, and outcome; the CLI passes it to persistence.
- Grep results carry synthetic string IDs (`grep-N`) and null vector/FTS/RRF scores. Persistence now copies only integer IDs or digit-only strings into `retrieved_chunk_ids`, so grep references are not misrepresented as database chunk IDs. Their matching file, line, content, and attempt are retained in `tool_calls`.
- Focused real test command: `\.venv\Scripts\python.exe -m pytest tests\unit\test_investigation_persistence.py -q`; actual output: `1 passed in 3.94s`. The test asserts one Audit row, existing numeric chunk IDs and score arrays, final calibrated confidence, and the three-step initial/retry/grep trace. No existing Audit field assertion was removed.

---

## Checkpoint 7 — Automated tests

**Task:** Add unit tests (mocked MCP calls where feasible, no real server
process needed for unit tests) covering: `grep_search`'s matching logic
against known content, the graph only escalates to `grep_search` after the
widen-limit retry has already failed (not before), the graph still returns
`INSUFFICIENT_EVIDENCE` if `grep_search` also fails (no infinite loop, no
third escalation), and `tool_calls` records the correct multi-step trace
for a scenario that exercises all three attempts.

### Log
- Test file added: `tests/unit/test_investigation_mcp_tools.py`. It tests case-insensitive literal matching and ignored-directory behavior; asserts deterministic hybrid limits `[5, 10]` precede the MCP grep call; asserts an empty grep result returns `INSUFFICIENT_EVIDENCE` without generation; and asserts the returned graph trace lists initial hybrid, widened retry, and grep in order with the actual outcomes.
- The existing `tests/unit/test_investigation_persistence.py` was extended to assert that the ordered three-attempt trace persists in one Audit row while numeric chunk IDs and score fields remain correct.
- Focused command output: `.venv\\Scripts\\python.exe -m pytest tests\\unit\\test_investigation_mcp_tools.py tests\\unit\\test_investigation_graph.py tests\\unit\\test_investigation_persistence.py -q` returned `7 passed in 14.87s`.
- Full suite command: `.venv\\Scripts\\python.exe -m pytest -q`; actual output: `22 passed in 16.32s`, exactly 3 more tests than Phase 6's 19.

---

## Checkpoint 8 — Real live test: construct a case that actually exercises escalation

**Task:** Phase 6 honestly found that the existing 31-chunk corpus rarely
triggers any guard failure at all, so the retry path was never really
exercised live. Don't let that happen again here — deliberately construct
a real test case: add one new, real file to the ingested repository
containing a distinctive literal keyword or phrase that would plausibly be
*missed* by vector/FTS search (e.g. an unusual identifier, a typo-like
term, or phrasing that doesn't paraphrase well) but *would* be caught by a
literal grep. Ingest it for real, then run a real query using that keyword
and confirm the full escalation path actually fires: initial search
insufficient → widen-limit retry insufficient → `grep_search` finds it →
investigation succeeds.

### Log
- File added: `tests/fixtures/phase7_grep_probe.py`. It contains a long block of unrelated source-like fixture context and one literal Q/A line: `phase7_probe_marker = "Is the quartz comet purple? Yes, for this Phase 7 fallback fixture."` The question phrase is outside this repository's domain; its measured best cosine distance against the remaining embedded corpus was `0.550950447252399`, above the `0.5` guard limit.
- First live attempt: an earlier short token marker was found by hybrid retrieval, so the CLI did not escalate (`Retry used: False; Tool attempts: 1`). That attempt was retained as a failed fixture design, not reported as success. I expanded the single fixture with unrelated context, then selected the out-of-domain violin query based on measured distance; its first CLI attempt reached all three tools but Gemini returned `INSUFFICIENT_EVIDENCE` because the fixture only contained the query string, not an answer. I then changed the same fixture line to the self-contained Q/A above.
- Real ingestion and embedding: re-ingested the repository including the one fixture file; command output was `Files processed: 41` and `Chunks created: 72`. Ran the actual Gemini embedding CLI; output was `Chunks embedded: 72`, `Chunks failed: 0`, `Chunks skipped: 0`. To make this case exercise the documented missing-vector fallback, directly set the two fixture chunk embeddings to `NULL` after embedding; the real DB preparation output was `fixture_chunk_ids_with_embedding_cleared: [1343, 1344]`, `total_chunks: 72`, `embedded_chunks: 70`. The raw fixture remains in the source tree for literal grep and FTS.
- Real query and CLI outcome: query `Is the quartz comet purple?` on `incidentweave-local` with `--limit 5 --repo-path D:\\Projects\\incidentweave`. Actual output:

```text
Repository: incidentweave-local
Query: Is the quartz comet purple?
Diagnosis: Yes, the quartz comet is purple, according to the phase 7 fallback fixture.
Confidence: high
Cited chunks: ['grep-1']
Model: gemini-3.5-flash-lite
Latency ms: 1543
Retry used: True; confidence calibrated: False
Tool attempts: 3
```

This final live run did exercise the full route: initial hybrid search insufficient (best cosine distance `0.5213384114223907`); widened limit 10 still insufficient with the same best distance; then MCP `grep_search` found one literal match, which the shared literal-evidence guard accepted, and Gemini answered from it. The setup deliberately simulated an embedding failure for only the fixture chunks; it is a constructed integration case, not evidence that this exact escalation arose naturally from the original 31-chunk corpus.

- Additional live violin-query result: `how to tune a violin using harmonics` also traversed all three tool attempts and returned `INSUFFICIENT_EVIDENCE` with low confidence. The actual CLI output was:

```text
Repository: incidentweave-local
Query: how to tune a violin using harmonics
Diagnosis: INSUFFICIENT_EVIDENCE
Confidence: low
Cited chunks: []
Model: gemini-3.5-flash-lite
Latency ms: 1081
Retry used: True; confidence calibrated: False
Tool attempts: 3
```

This is a positive behavior finding: controlled escalation surfaced a literal match to the model, but did not force the model to treat “evidence was found” as “evidence answers the question.” Important caveat: at the time of this run, a temporary debug helper in the raw source tree contained the query string itself, and MCP grep found that helper line (plus the fixture's then-current marker line). The model still refused to claim that this established violin-tuning instructions. The helper was removed before the final quartz-comet success run, so this violin attempt is logged as an intermediate behavior check, not as the final clean-fixture proof.

---

## Checkpoint 9 — Real live test: audit trail

**Task:** For the same investigation from Checkpoint 8, query the database
directly and confirm `Audit.tool_calls` contains the complete, accurate
multi-step trace.

### Log
- Direct DB query found Investigation `18`, response `Yes, the quartz comet is purple, according to the phase 7 fallback fixture.`, confidence `high`, and exactly one Audit row. `retrieved_chunk_ids` is empty because the final evidence came from raw source grep and has synthetic `grep-N` IDs, not persisted Chunk-table IDs. The actual `Audit.tool_calls` value was:

```json
{
  "attempts": [
    {
      "tool": "hybrid_search",
      "stage": "initial",
      "outcome": {
        "reason": "Best vector cosine distance is above the maximum threshold.",
        "sufficient": false,
        "result_count": 5,
        "best_rrf_score": 0.01639344262295082,
        "best_vector_score": 0.5213384114223907
      },
      "parameters": {
        "limit": 5,
        "query": "Is the quartz comet purple?",
        "repository_name": "incidentweave-local"
      }
    },
    {
      "tool": "hybrid_search",
      "stage": "widened_retry",
      "outcome": {
        "reason": "Best vector cosine distance is above the maximum threshold.",
        "sufficient": false,
        "result_count": 10,
        "best_rrf_score": 0.01639344262295082,
        "best_vector_score": 0.5213384114223907
      },
      "parameters": {
        "limit": 10,
        "query": "Is the quartz comet purple?",
        "repository_name": "incidentweave-local"
      }
    },
    {
      "tool": "grep_search",
      "stage": "literal_fallback",
      "outcome": {
        "reason": "Literal source matches were found.",
        "sufficient": true,
        "match_count": 1
      },
      "parameters": {
        "limit": 20,
        "keyword": "Is the quartz comet purple?",
        "repository_name": "incidentweave-local",
        "repository_path": "D:\\Projects\\incidentweave"
      }
    }
  ],
  "cited_chunk_ids": ["grep-1"],
  "retrieval_results": [
    {
      "id": "grep-1",
      "line_end": 36,
      "file_path": "tests/fixtures/phase7_grep_probe.py",
      "fts_score": null,
      "rrf_score": null,
      "line_start": 36,
      "vector_score": null
    }
  ]
}
```

- This matches Checkpoint 8: attempt order is initial hybrid at 5, widened hybrid at 10, then grep; both hybrid attempts failed for the same vector-distance reason, and grep returned one sufficient literal match. The single Audit row invariant held. The raw grep result is present in `tool_calls.retrieval_results`, while `retrieved_chunk_ids` correctly remains empty for non-database grep IDs.

---

## Checkpoint 10 — Update README

**Task:** Update `README.md`:
- Move Phase 7 to ✅ Complete, Phase 8 to 🔜 Next, in the status table and
  roadmap
- Add a "Phase 7" collapsible detail section (same style as Phases 1-6)
  describing the MCP tool exposure, the `grep_search` fallback, and the
  controlled (deterministic, not LLM-chosen) escalation policy
- Update "V1 Scope Discipline" — remove MCP from the deferred list, add one
  sentence explaining its deliberate adoption here, same honest framing as
  the LangGraph note from Phase 6
- Update the project structure tree (new MCP server file, any new modules)
- Update "Current Verification" test count to match Checkpoint 7's real
  number
- Add MCP to the Technology Stack table

### Log
- Confirmed all six README updates in the current file: (1) Phase 7 is complete and Phase 8 is next in the status table and roadmap; (2) a Phase 7 collapsible section describes MCP tools, literal grep, and deterministic escalation; (3) MCP was removed from the deferred list and its deliberate stdio/protocol-learning use is explained honestly; (4) the project tree includes `app/investigation/mcp_server.py`; (5) Current Verification reports `22 passed`, matching Checkpoint 7; (6) MCP is listed in the Technology Stack.
- Targeted search found the updated status, section, rationale, tree, roadmap, and count; editor diagnostics reported no README errors.

---

## Checkpoint 11 — Final full regression

**Task:** Run the complete verification sequence one more time.

### Log
- `\.venv\Scripts\python.exe -m pytest -q` — actual output: `22 passed in 17.77s`.
- `\.venv\Scripts\ruff.exe check .` — initial run reported one `I001` import-order issue in `app/investigation/mcp_server.py`. A manual reorder did not satisfy Ruff; Ruff's `check app/investigation/mcp_server.py --fix` reported `Found 1 error (1 fixed, 0 remaining)`. The required full rerun then printed `All checks passed!`.
- `docker build -f docker/Dockerfile .` — actual output: `[+] Building 296.7s (10/10) FINISHED`; image export completed and wrote image `sha256:2a7e14b2e1eff69b78a3483461e9d74f821dfe6fd526b...`.
- All three checks passed in the final state. Phase 7 is complete. No Phase 8 work was started, and no commit or push was performed.

---

## After all checkpoints

Do not proceed to Phase 8. Do not touch git beyond what Checkpoint 0 (branch
creation, see the prompt) already covers — no further commit or push. That
happens separately, reviewed together, once the person is back and has read
through this entire log themselves.
