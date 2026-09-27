# Investigation Engine (Phase 5)

**Date built:** September 2026
**Status:** Drafted — review against the Phase 5 engineering log

## What I built

The investigation pipeline takes a repository question, retrieves code chunks, checks evidence sufficiency, constructs a grounded prompt, calls Gemini, parses its answer, and persists the result. The prompt instructs the model to rely only on supplied repository evidence and return `INSUFFICIENT_EVIDENCE` when that evidence does not support an answer. The CLI is `scripts/investigate.py`; successful runs persist one Investigation and exactly one Audit row containing all retrieved chunk IDs and retrieval scores.

## Why this design

Generation is separate from prompt construction so prompt behavior can be tested without calling the API. The Gemini REST call has a 60-second timeout, bounded retries for selected transient HTTP/network failures, and raises visibly rather than inventing a fallback response. Confidence is stored as the schema's categorical `high`, `medium`, or `low` string instead of a numeric probability that retrieval scores do not calibrate.

The guard runs before generation. It requires both an RRF score of at least `0.016` and an available best vector cosine distance no greater than `0.5`; empty, FTS-only, or weak evidence fails closed. Persistence distinguishes retrieved evidence from cited evidence: the Audit's `retrieved_chunk_ids` records every returned chunk, while parsed citations are stored separately.

## Key concept, explained simply

Grounding means treating retrieved repository text as the boundary for what the model may claim. Retrieval finds candidate evidence; the guard decides whether that evidence is strong enough to justify a model call; the prompt then tells the model to answer only from those chunks. Parsing can verify that a response mentions a retrieved ID or file path, but that match is not proof that every sentence is logically supported, so a real answer still needs inspection against its source.

## Walkthrough example

For `how are async sessions configured?` against `incidentweave-local`, live retrieval returned chunk `136` from `app/db/session.py:1-46` with vector distance `0.3345773321557659` and RRF `0.03278688524590164`. The guard accepted it. Gemini described `AsyncSessionLocal = async_sessionmaker(...)`, including the async engine and `expire_on_commit=False`. After the parser was extended to accept an exact retrieved file path without a line range, the CLI reported `Cited chunks: ['136']`. A later direct DB check showed one Audit row with all retrieved IDs, not only cited ones.

## What broke when I tested it

The first generation-model choice was checked against the API instead of assumed; Phase 5's log records the confirmed endpoint and retry behavior. Live output also exposed that Gemini cited `app/db/session.py` in flowing prose without a line range, while the original parser required a chunk ID or file-plus-range. The parser gained exact-file-path matching, and the live rerun resolved the response to chunk `136`; this remains best-effort citation detection, not proof of entailment.

The RRF-only guard passed an unrelated CEO-car query for `incidentweave-local` at RRF `0.01639344262295082`. Adding the cosine-distance condition rejected it at distance `0.5176320179049577`, while the answerable session query passed at `0.3345773321557659`. Persistence testing also found that creating an Audit in the retrieved-chunk loop produced multiple rows; it was changed to create one Audit per investigation and retain every retrieved ID.

## Interview-ready summary (3-4 sentences)

I built an evidence-first investigation path around retrieval, a pre-generation guard, a grounded Gemini prompt, response parsing, and auditable persistence. The guard combines RRF with raw cosine distance because live testing showed that RRF alone could admit an unrelated query. I treated citations as best-effort references and checked a real answer against its retrieved source rather than claiming parser matches prove correctness. The final persistence contract is one Investigation and one Audit per successful query, with retrieved IDs kept distinct from cited IDs.
