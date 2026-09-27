# Grounding & Confidence with LangGraph (Phase 6)

**Date built:** September 2026
**Status:** Drafted — review against the Phase 6 engineering log

## What I built

I added a LangGraph state graph around the Phase 5 investigation flow. It retrieves evidence, invokes the existing sufficiency guard, allows one retry at twice the initial search limit, and then either returns insufficient evidence or continues through prompt construction, Gemini generation, parsing, and confidence calibration. Persistence remains in the CLI, outside the graph; the CLI passes the graph's final confidence into persistence so the calibrated value is stored in both the Investigation and Audit rows.

## Why this design

The installed LangGraph package was checked before implementation: the venv reported version `1.2.12`, with `StateGraph`, node registration, conditional edges, and `START`/`END` available from `langgraph.graph`. A graph is used here for the explicit branch and bounded retry, not to add an open-ended agent loop. The retry reuses the existing guard decision and changes only the result limit: default 5 becomes 10; it does not reformulate the query or call another model to rewrite it.

The calibration rule is intentionally a small threshold rule, not a probability estimate. It downgrades a model-reported `high` to `medium` when best RRF is below `0.032` or best cosine distance is above `0.4`; `medium` and `low` are left alone. These margins are checked only after the existing evidence guard accepts the retrieval.

## Key concept, explained simply

A state graph makes control flow explicit: each node performs one step and returns state updates, while conditional edges choose what happens next. Here the guard's boolean result decides whether the graph proceeds, retries once with a wider retrieval limit, or stops with insufficient evidence. The graph doesn't make retrieval more informative by itself; it only controls the bounded sequence and makes its branch behavior testable.

## Walkthrough example

For the live query `what does the health endpoint return?` against `incidentweave-local`, the graph retrieved five chunks. The best RRF was `0.01639344262295082`, below the calibration margin `0.032`, while the best vector distance was `0.32330329094274324`. The model's first self-report was `high`; calibration downgraded it to `medium`. After a persistence mismatch was found and fixed, a repeated CLI run printed `Confidence: medium` and `confidence calibrated: True`; a direct DB query showed Investigation `14` stored `medium` with one Audit row.

## What broke when I tested it

The mocked tests verify that an insufficient first result causes exactly one retry at limits `[5, 10]`, that a second insufficient result stops without generation, and that a borderline high confidence rating downgrades. In live testing, none of eight tested questions changed from insufficient at limit 5 to sufficient at limit 10. The repository contained only 31 embedded chunks, so that small corpus did not provide a meaningful live retry-recovery example.

There is also a structural limitation beyond corpus size: vector search sorts cosine distance ascending and takes the top N, while the guard uses the minimum vector distance. Widening this list cannot change its nearest neighbor's distance, so a rejection caused by vector distance can never be recovered by this retry strategy if the query embedding and corpus stay fixed. RRF could sometimes change if a newly included chunk gains membership from the second retrieval list, but no such live recovery was observed. A real calibration run also exposed a persistence mismatch: the CLI showed calibrated `medium` while persistence reparsed and stored raw `high`. Passing the final confidence explicitly fixed it, and the repeated run verified `medium` in the database.

## Interview-ready summary (3-4 sentences)

I used LangGraph to make the investigation's one-retry branch explicit and bounded, while reusing the existing retrieval, guard, prompt, generation, and parsing functions. I added a threshold-based confidence downgrade when a model says `high` but the accepted retrieval is near a guard boundary, and verified that the calibrated value persists. Mocked tests cover the retry and termination paths; live tests demonstrated calibration but not a successful retry recovery. The key limitation is structural: widening a distance-ascending top-N vector search cannot improve its nearest-neighbor distance.
