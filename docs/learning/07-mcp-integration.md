# Controlled Tools & Audit (Phase 7)

**Date built:** September 2026
**Status:** Drafted - author sections pending

## What I built

I added a local MCP server at `app/investigation/mcp_server.py` with two tools: the existing `hybrid_search` wrapper and a new literal `grep_search` over raw Python source files. The investigation graph uses a fixed escalation order: hybrid retrieval, one widened retry, then `grep_search` through a separate MCP stdio process. Each investigation now records the ordered tool attempts, parameters, and outcomes in `Audit.tool_calls`.

## Why this design

The graph, not the model, controls escalation. This keeps the phase deterministic: the model cannot decide to call arbitrary tools or loop indefinitely. The MCP boundary is intentionally real even though a direct function call would be simpler for this single-process application; the point of this phase is to verify a real tool schema, child server process, stdio transport, and client call.

`grep_search` reuses `iter_python_files()` and its existing exclusion set instead of inventing a second file-selection policy. It performs case-insensitive literal matching, which is useful for pasted error strings, unusual identifiers, and exact source phrases. It does not pretend raw grep matches have vector or RRF scores.

## Key concept, explained simply

<!-- Write this as if explaining to an interviewer with no context — one paragraph,
no jargon you can't unpack further if asked. -->

## Walkthrough example

The real Checkpoint 9 case used the constructed fixture `tests/fixtures/phase7_grep_probe.py`, whose literal line answered `Is the quartz comet purple?`. The fixture was ingested and embedded, then its two database embeddings were manually set to `NULL` so the fallback path could be exercised while the raw file remained available to grep. The live Audit trace recorded hybrid limit 5 as insufficient with best vector distance `0.5213384114223907`, hybrid limit 10 as still insufficient with the same distance, and `grep_search` as sufficient with one match. The investigation returned the diagnosis that the quartz comet was purple, and the database showed exactly one Audit row with the three attempts in order.

## What broke when I tested it

The first short marker was found by hybrid retrieval, so it did not exercise MCP. A later violin-query attempt reached all three tools but returned `INSUFFICIENT_EVIDENCE`; the model correctly refused to treat a literal match as proof that the source answered the question. That intermediate run also matched a temporary debug helper, which was removed before the final fixture run.

The final live success depended on a deliberately constructed case and manually nulled fixture embeddings; re-embedding the fixture changes the retrieval outcome. The graph calls only `grep_search` through MCP; `hybrid_search` is exposed by the server but remains an in-process graph call. Unit tests mock `call_grep_search_mcp()` and do not spawn MCP subprocesses; the separate-process behavior was verified by dedicated live probes.

## Interview-ready summary (3-4 sentences)

<!-- The condensed version you'd actually say out loud if asked "tell me about this part
of the project." Write this last, once everything above is filled in. -->
