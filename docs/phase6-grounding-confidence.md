# Phase 6 — Grounding & Confidence

**Status:** Complete — Checkpoint 10 passed all required verification commands.
**Depends on:** Phase 5 (investigation engine, verified working) — confirmed.

This document is both the task spec AND the running log, same pattern as
Phases 3-5. Fill in each checkpoint's "Log" section with real detail before
moving to the next one. Run every command yourself, for real — do not
simulate or predict output. The person is away for this session; do not
wait for input. Complete every checkpoint in order and log real results
honestly, including anything that doesn't work as expected.

**This phase deliberately introduces LangGraph.** The README's "V1 Scope
Discipline" section listed LangGraph as explicitly deferred — that was
correct at the time, because nothing in V1 needed branching logic. This
phase is the first place branching is actually needed (retry on weak
evidence), so this is a deliberate, documented move into V2, not scope
creep. Checkpoint 9 updates the README to reflect this honestly.

**Scope for this session, do not exceed it:**
- One retry strategy: if initial retrieval evidence is insufficient, retry
  once with a wider search limit before giving up. No query reformulation
  via an extra LLM call — that's a future enhancement, not this session.
- One confidence-calibration rule: cross-check the model's self-reported
  confidence against retrieval score strength, downgrade if they disagree.
- Wire it into the existing CLI. Test it. Document it. Nothing beyond that.

---

## Checkpoint 1 — Confirm the LangGraph package, don't assume its API

**Task:** Before writing any code, install LangGraph in the project venv and
check its actual current API from the installed package itself (not from
memory or a tutorial) — this project has twice been burned by assuming an
API/model detail instead of checking it (the deprecated embeddings model,
the citation-matching mismatch). Confirm: the exact package name to add to
`pyproject.toml`, the installed version, and the actual shape of
`StateGraph`, node functions, and conditional edges by importing it and
checking `dir()`/`help()` or its real source, not by writing code first and
hoping it matches.

### Log
- Package name and version installed: installed the PyPI distribution `langgraph` into the project venv; `importlib.metadata.version("langgraph")` returned `1.2.12`. Added `langgraph>=1.2,<2.0` to the project runtime dependencies.
- Actual StateGraph/node/conditional-edge API confirmed from the installed module: `from langgraph.graph import StateGraph, START, END` succeeds. `StateGraph` signature is `(state_schema, context_schema=None, *, input_schema=None, output_schema=None, **kwargs)`. `add_node(self, node, action=None, *, ...)` registers a node action; `add_edge(self, start_key, end_key)` adds an edge; `add_conditional_edges(self, source, path, path_map=None)` routes using a callable and optional mapping; `compile(self, checkpointer=None, *, ...)` returns a compiled state graph. Runtime constants were `START == "__start__"` and `END == "__end__"`. Inspected the installed `add_conditional_edges` source: it coerces the callable to a runnable, validates the branch name, then records the branch/path map. No graph implementation was written before this API check.
- Command output: `distribution: 1.2.12`; `StateGraph signature: (state_schema: type[StateT], context_schema: type[ContextT] | None = None, *, input_schema: type[InputT] | None = None, output_schema: type[OutputT] | None = None, **kwargs) -> None`; `START: __start__`; `END: __end__`.

---

## Checkpoint 2 — Design decisions

**Task:** Decide and write down:
1. **Retry trigger** — exact condition that causes a retry (should reuse
   `evaluate_evidence_sufficiency`'s existing result, not invent a new check)
2. **Retry strategy** — what changes on retry (wider `limit` — decide the
   new value and why)
3. **Max retries** — how many attempts before giving up and returning
   insufficient-evidence (keep this small — 1 retry, 2 attempts total)
4. **Confidence calibration rule** — the exact condition for downgrading
   self-reported confidence (e.g. model says "high" but best retrieval
   score is close to the guard's rejection threshold rather than clearly
   above it — define "close" concretely, as a number)

### Log
- Retry trigger: after each retrieval, reuse `evaluate_evidence_sufficiency(retrieval_results)`; retry only if its `is_sufficient` value is false. No second threshold or query-reformulation decision is introduced.
- Retry strategy and new limit value, and why: widen the result limit to twice the initial limit (the existing CLI default is 5, so retry at 10). Doubling is a single, bounded increase that admits lower-ranked candidates while keeping the exact query and retrieval methods unchanged. With a caller-supplied limit, the retry limit is likewise `initial_limit * 2`.
- Max retries: one retry, two retrieval attempts total. If the second guard result is still insufficient, return `INSUFFICIENT_EVIDENCE` without calling Gemini.
- Confidence calibration rule, exact condition: when the model reports `high`, downgrade to `medium` if the best retrieval RRF score is below `0.032` (twice the existing `0.016` acceptance floor) OR the best/minimum cosine distance is above `0.4` (within `0.1` of the existing `0.5` maximum). This rule only downgrades `high`; `medium` and `low` remain unchanged. Calibration runs only after evidence passes the existing guard, so both retrieval values are available. The boundaries deliberately flag evidence that passes but is close to either guard threshold; they are explicit calibration cutoffs, not probability estimates.

---

## Checkpoint 3 — Build the state graph

**Task:** Create `app/investigation/graph.py` implementing the investigation
flow as a LangGraph graph: retrieve → guard → (conditional: sufficient →
continue; insufficient → retry once with wider limit → guard again →
conditional: sufficient → continue; still insufficient → return
insufficient-evidence result) → prompt → generate → parse → calibrate
confidence → return final result (persistence stays a separate step, called
by the CLI, not inside the graph — keep the graph focused on the
decision-making, not I/O side effects).

Reuse the existing functions from `prompt.py`, `generation.py`, `parsing.py`,
`guard.py` as node functions or thin wrappers around them — do not
reimplement any of that logic inside the graph.

### Log
- File created: `app/investigation/graph.py`. Nodes: `retrieve`, `guard`, `widen_search`, `insufficient`, `build_prompt`, `generate`, `parse`, `calibrate`.
- Actual compiled graph output: nodes were `['__end__', '__start__', 'build_prompt', 'calibrate', 'generate', 'guard', 'insufficient', 'parse', 'retrieve', 'widen_search']`. Edges were `__start__ -> retrieve -> guard`; guard conditionally routes to `build_prompt` when sufficient, to `widen_search` on the first insufficient result, or to `insufficient` after retry. `widen_search -> retrieve` runs the single wider attempt. The successful path is `build_prompt -> generate -> parse -> calibrate -> __end__`; `insufficient -> __end__`.
- Delegation confirmed in source: `retrieve` wraps `hybrid_search()` with a database session; `guard` calls `evaluate_evidence_sufficiency()`; `build_prompt` calls `build_grounded_prompt()`; `generate` calls `generate_investigation()`; `parse` calls `parse_investigation_response()`. The retry and insufficient nodes only update orchestration state. The `calibrate` node delegates to an injected standalone calibration function, which is implemented in Checkpoint 4. Persistence remains outside the graph.
- Focused validation command imported and compiled `create_investigation_graph()` against installed LangGraph 1.2.12 and printed the node and edge lists above; compilation completed successfully.

---

## Checkpoint 4 — Confidence calibration function

**Task:** Implement Checkpoint 2's calibration rule as a standalone,
testable function — takes the model's self-reported confidence plus the
retrieval scores, returns the (possibly downgraded) final confidence and a
note explaining whether/why it was adjusted.

### Log
- Function name/location: `calibrate_confidence()` in `app/investigation/confidence.py`. It returns `(final_confidence, note)` and downgrades `high` to `medium` if best RRF is below `0.032` or best vector distance is above `0.4`; other confidence values are retained.
- Real runtime example using the prior live answerable `incidentweave-local` investigation's model confidence and measured retrieval scores:

```python
{
  'input': {
    'reported_confidence': 'high',
    'best_rrf_score': 0.03278688524590164,
    'best_vector_score': 0.3345773321557659,
  },
  'output': {
    'confidence': 'high',
    'note': 'High confidence retained; retrieval scores clear both calibration margins.',
  },
}
```

---

## Checkpoint 5 — Wire into the CLI

**Task:** Update `scripts/investigate.py` to use the new graph instead of
the flat function call sequence, keeping the same CLI interface (same args,
same printed output format, plus one new line showing whether a retry
happened and whether confidence was calibrated).

### Log
- What changed in `scripts/investigate.py`: the CLI builds and invokes `create_investigation_graph(calibrate_confidence)` and persists a successful graph response afterward using the existing `persist_investigation()` function. The graph receives the unchanged query embedding and initial limit; its retry limit is exactly twice the initial limit. Added one line reporting retry and calibration flags.
- CLI help validation output confirms the unchanged arguments:

```text
usage: investigate.py [-h] [--limit LIMIT] repo_name query
positional arguments:
  repo_name      Repository name stored in the database
  query          Natural-language question to investigate
options:
  -h, --help     show this help message and exit
  --limit LIMIT  Maximum hybrid-search results to consider
```

- Existing output fields remain repository, query, diagnosis, confidence, cited chunks, model, and latency; the appended format is `Retry used: <bool>; confidence calibrated: <bool>`. Persistence remains a CLI-side operation and is not a graph node.

---

## Checkpoint 6 — Automated tests

**Task:** Add unit tests (mocked, no real API/DB calls, same pattern as
existing investigation tests) covering: the graph retries exactly once
when the first guard check fails, the graph stops and returns
insufficient-evidence after the retry also fails (does not loop forever),
and confidence calibration downgrades a borderline case correctly.

### Log
- Test file added: `tests/unit/test_investigation_graph.py`; it contains mocked tests for one widened retry, termination after the retry remains insufficient (and no generation call), and downgrade of borderline high confidence. No live API/database calls are used by these tests.
- Full suite command: `\.venv\Scripts\python.exe -m pytest -q`.
- Real output: `19 passed in 19.10s`. This is exactly 3 more test cases than the prior 16-test suite; all three are in the new graph test file.

---

## Checkpoint 7 — Real live test: retry actually helps

**Task:** Find or construct a real query against the ingested repository
where the initial (narrow) search doesn't clear the evidence guard, but a
wider retry does. If you can't find a naturally-occurring one, that's a
real and useful finding too — log it honestly rather than forcing a result.

### Log
- Repository: `incidentweave-local`, queried against the real PostgreSQL index with fresh Gemini embeddings for eight concrete questions at limits 5 and 10.
- Direct repository count command output from PostgreSQL: `repository=incidentweave-local`, `repository_id=4`, `total_chunks=31`, `embedded_chunks=31`.
- Real first-attempt/retry probe output (guard values shown; every query passed at both limits, so none entered the retry branch):

```text
how are async sessions configured? | limit 5: sufficient=True, best_rrf=0.03278688524590164, best_vector=0.3345773321557659 | limit 10: sufficient=True, best_rrf=0.03278688524590164, best_vector=0.3345773321557659
how does the evidence sufficiency guard work? | limit 5: sufficient=True, best_rrf=0.01639344262295082, best_vector=0.4911416461136189 | limit 10: sufficient=True, best_rrf=0.01639344262295082, best_vector=0.4911416461136189
how does the CLI persist investigations? | limit 5: sufficient=True, best_rrf=0.01639344262295082, best_vector=0.40761815527554 | limit 10: sufficient=True, best_rrf=0.01639344262295082, best_vector=0.40761815527554
how are repository chunks embedded? | limit 5: sufficient=True, best_rrf=0.03177805800756621, best_vector=0.30839120312508383 | limit 10: sufficient=True, best_rrf=0.03177805800756621, best_vector=0.30839120312508383
how does hybrid search combine vector and full-text results? | limit 5: sufficient=True, best_rrf=0.01639344262295082, best_vector=0.2376714652693105 | limit 10: sufficient=True, best_rrf=0.01639344262295082, best_vector=0.2376714652693105
how are database migrations applied? | limit 5: sufficient=True, best_rrf=0.01639344262295082, best_vector=0.43049378643983405 | limit 10: sufficient=True, best_rrf=0.01639344262295082, best_vector=0.43049378643983405
how does Gemini response parsing extract citations? | limit 5: sufficient=True, best_rrf=0.01639344262295082, best_vector=0.39648460284316767 | limit 10: sufficient=True, best_rrf=0.01639344262295082, best_vector=0.39648460284316767
what is the project health endpoint? | limit 5: sufficient=True, best_rrf=0.01639344262295082, best_vector=0.3966187359567229 | limit 10: sufficient=True, best_rrf=0.01639344262295082, best_vector=0.3966187359567229
```

- No naturally occurring query was found where limit 5 failed and limit 10 passed. No final model diagnosis/confidence was produced for a retry case (`N/A`, because no probe entered the retry route; the probe intentionally tested retrieval/guard only). The one-retry state transition and exact `[5, 10]` limits were verified by the mocked Checkpoint 6 graph test.
- Corpus-size finding: a direct PostgreSQL count found only 31 chunks in `incidentweave-local`, all embedded. This small corpus limits the usefulness of a live retry experiment, but corpus size is not the fundamental constraint on vector-distance recovery.
- Structural retry limitation confirmed from `app/retrieval/vector_search.py`: `search_vector()` orders cosine distance ascending and then applies `.limit(limit)`. Therefore the nearest neighbor's distance is invariant as `limit` widens: the top-N vector results are a prefix of the wider top-M results, and adding lower-ranked (necessarily equal-or-worse-distance) neighbors cannot lower the minimum distance. `evaluate_evidence_sufficiency()` uses the minimum available `vector_score` as `best_vector_score`, so a guard rejection caused by vector distance can **never** be fixed by this wider-limit retry, on any corpus size (assuming the query embedding and corpus remain unchanged between attempts). This retry strategy only has a possible recovery path for an RRF-based rejection, not a vector-distance rejection.
- RRF caveat: RRF can occasionally benefit from widening if a newly included candidate gains membership from the second retrieval list it was absent from at the narrow cutoff. However, the live top result's single-list rank-1 contribution is already `1/61 = 0.01639344262295082`, above the guard floor `0.016`; this and the 31-chunk corpus help explain why none of the eight tested queries showed an RRF-based failure at limit 5 that passed at limit 10. The one-retry branch is verified by the mocked Checkpoint 6 test, but live validation did not demonstrate a successful recovery.

---

## Checkpoint 8 — Real live test: confidence calibration in action

**Task:** Find or construct a real case where the model's self-reported
confidence gets calibrated down by the new rule. Same honesty standard as
Checkpoint 7 — if you can't produce a real live example, say so and rely on
the mocked test instead, don't fabricate a plausible-looking one.

### Log
- Real confidence-calibration case found for `incidentweave-local`, query `what does the health endpoint return?`. The first live CLI run answered the query but initially showed `Confidence: medium; confidence calibrated: True`; a direct DB inspection found Investigation `13` persisted `high`, revealing that Phase 5 persistence reparsed and stored the model's raw confidence rather than the calibrated final value.
- Fixed that observed persistence mismatch by adding an optional `final_confidence` override to `persist_investigation()` and passing the graph's final confidence from the CLI. The persistence test now asserts the override is saved to both Investigation and its single Audit row.
- Repeated the same live query after the fix. Actual CLI output:

```text
Repository: incidentweave-local
Query: what does the health endpoint return?
Diagnosis: The health endpoint (`/health`) returns a dictionary with the status "ok" (`{"status": "ok"}`).
Confidence: medium
Cited chunks: []
Model: gemini-3.5-flash-lite
Latency ms: 1667
Retry used: False; confidence calibrated: True
```

- Direct DB check of the repeated run: Investigation `14` persisted `confidence=medium`; exactly one Audit row was attached. Retrieved IDs were `[137, 157, 132, 128, 145]`, RRF scores were `[0.01639344262295082, 0.016129032258064516, 0.015873015873015872, 0.015625, 0.015384615384615385]`, and vector distances were `[0.32330329094274324, 0.3566171000606657, 0.46552853477268397, 0.46711478799589634, 0.47225449629887584]`. The model's raw self-report on the first run was `high` (seen in the uncalibrated persisted record); the best RRF was below the `0.032` calibration margin, so the final confidence was downgraded to `medium` and is now persisted consistently. Citation parsing returned no cited IDs; this does not change the observed confidence calibration.

---

## Checkpoint 9 — Update README

**Task:** Update `README.md`:
- Move Phase 6 to ✅ Complete, Phase 7 to 🔜 Next, in the status table and
  roadmap
- Add a "Phase 6" collapsible detail section (same style as Phases 1-5)
  describing the retry logic and confidence calibration
- Update "V1 Scope Discipline" — remove LangGraph from the deferred list,
  and add one sentence explaining that it was deliberately adopted in
  Phase 6 specifically for retry branching, not introduced prematurely
- Update the project structure tree to include `app/investigation/graph.py`
- Update the "Current Verification" test count to match Checkpoint 6's
  real number
- Add `langgraph` to the Technology Stack table

### Log
- Confirmed all six README updates from the current file: (1) status table marks Phase 6 complete and Phase 7 next, and the roadmap styles Phase 6 complete; (2) added a Phase 6 collapsible section describing the single doubled-limit retry and confidence calibration; (3) removed LangGraph from the deferred list and documented its deliberate Phase 6 adoption for retry branching; (4) project tree includes `app/investigation/graph.py` and its supporting `confidence.py`; (5) Current Verification test count is `19 passed`, matching Checkpoint 6; (6) Technology Stack lists LangGraph under AI & Retrieval.
- Verification: targeted search of `README.md` found each status, section, scope, structure, roadmap, stack, and test-count entry; editor diagnostics reported no errors for README.

---

## Checkpoint 10 — Final full regression

**Task:** Run the complete verification sequence one more time, exactly
like the pre-commit checks used in Phases 3-5.

### Log
- `.\.venv\Scripts\python.exe -m pytest -q` — real output: `19 passed in 16.14s`.
- `.\.venv\Scripts\ruff.exe check .` — initial run reported one `F401` for unused `Sequence` in `app/investigation/graph.py`. Removed that import and reran the exact command; final output: `All checks passed!`.
- `docker build -f docker/Dockerfile .` — real output: `[+] Building 432.7s (10/10) FINISHED`; the `pip install --no-cache-dir .` layer took `372.6s`; image export completed successfully.
- All three required checks passed in the final state. Phase 6 is complete. No Phase 7 work was started and no Git commands were run.

---

## After all checkpoints

Do not proceed to Phase 7. Do not touch git in any way — no add, commit, or
push. That happens separately, reviewed together, once the person is back
and has read through this log themselves.
