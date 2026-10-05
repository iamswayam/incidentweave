# Evaluation (Phase 8)

**Date built:** September 2026
**Status:** Drafted - author sections pending

## What I built

I added an evaluation package, a validated 24-question golden set, cached query embeddings, retrieval and guard metrics, and two end-to-end runs against a pinned 70-chunk source snapshot. The evaluation compares vector-only, full-text-only, and hybrid retrieval, measures guard decisions and fallback behavior, and records per-question outcomes without changing the investigation pipeline.

## Why this design

The pinned snapshot and checked labels make the measurements repeatable against one known corpus, while cached embeddings avoid repeating embedding calls. The metrics and keyword answer screen are deterministic and auditable; no LLM judge or threshold tuning was added. The log treats the results as diagnostic for this one 24-question sample, not a benchmark, because the labels are pending review and keyword checks are only a screen.

## Key concept, explained simply
Write this as if explaining to an interviewer with no context — one paragraph,
no jargon you can't unpack further if asked.

## Walkthrough example

Across 16 answerable questions, vector-only and hybrid both scored hit@1 `8/16`, hit@3 `11/16`, hit@5 `11/16`, and MRR `0.5729166667`; full-text returned no results for `14/16`. For the 24-question guard check, there were 16 true accepts, 0 false refusals, 4 true refusals, and 4 false accepts. In the two 24-question end-to-end runs, outcomes were 15 correct/1 wrong-or-incomplete/4 refused/4 falsely answered in run 1 and 14/2/4/4 in run 2; `direct-08` changed from correct to wrong-or-incomplete.

## What broke when I tested it

Hybrid retrieval did not beat vector-only on any reported retrieval metric. No tested vector cutoff from `0.30` through `0.60` separated answerable from unanswerable questions: their best-vector ranges overlapped by `0.02347064`, and the current guard produced 4 false accepts. Across both runs, 8 initial-insufficient attempts led to 0 retry recoveries and 8 grep attempts led to 0 grep recoveries. The near-unanswerable Redis, message-queue, authentication, and Kubernetes questions passed the guard in both runs; the generated text was `INSUFFICIENT_EVIDENCE`, but under the logged outcome definition they counted as falsely answered because generation ran.

## Interview-ready summary (3-4 sentences)
The condensed version you'd actually say out loud if asked "tell me about this part
of the project." Write this last, once everything above is filled in.