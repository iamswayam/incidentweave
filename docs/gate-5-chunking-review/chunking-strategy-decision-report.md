# Chunking Strategy Experiment: Decision Report

## 1. Executive Summary

**Retrieval winner: 100/20.** Across both passes and the same 16 answerable questions, the experimental 100-line window with 20-line overlap increased Hit@5 from 11/16 (68.75%) to 15/16 (93.75%), a net gain of four questions (+25 percentage points). Hit@1 increased by one question, Hit@3 by one, hit-by-file@5 increased from 13/16 to 16/16, and hit-by-function@5 increased from 1/7 to 5/7 applicable labels.

The evidence **supports 100/20 as the retrieval winner, but does not yet establish that it should be adopted**. Approved gates 1–4 and 6–9 pass on the saved comparison; Gate 5, human-reviewed end-to-end correctness, remains **MANUAL / pending**. The experimental run improved several recorded answer outcomes but also regressed on `direct-05` in pass 1: the answer omitted the required value `0.5` despite a better labeled rank. Retrieval ranking and generated-answer correctness are distinct measures.

The main measured trade-off is increased context and token use: median top-5 context grew 43.24%, and median total tokens per question grew about 40% in each pass. Both token ratios remain below the approved approximate 1.5× threshold. Recommendation: **retain the 60/10 baseline as the production choice until Gate 5 is completed; provisionally prefer 100/20 for retrieval, subject to human review and the limitations below.**

## 2. Experiment Context

| Arm | Strategy | Run ID | Corpus files / chunks | Evaluated source SHA |
|---|---|---|---:|---|
| Baseline | 60-line windows / 10-line overlap | `20261018T123627Z-2274338-baseline` | 40 / 70 | `22743382a4980d7787bc798d9ad8e2ab6ddecb18` |
| Experiment | 100-line windows / 20-line overlap | `20261018T124223Z-2274338-w100_o20` | 40 / 52 | `22743382a4980d7787bc798d9ad8e2ab6ddecb18` |

Both runs used pinned corpus SHA `62d0e58593bb22d187ec7930274b0457afd3be74`, the same golden-set SHA (`5f4c27469a1e1836c47d4485e2091a9c70546dc52ce1e824b44f6380d1b42914`), the same prompt SHA, and report `code_dirty=false`. The golden set's recorded review status is **pending maintainer review**.

Saved artifacts:

- Baseline metadata and summaries: [`report.json`](../../evaluation/results/runs/20261018T123627Z-2274338-baseline/report.json)
- Baseline pass records: [`pass-1.json`](../../evaluation/results/runs/20261018T123627Z-2274338-baseline/pass-1.json), [`pass-2.json`](../../evaluation/results/runs/20261018T123627Z-2274338-baseline/pass-2.json)
- Experimental metadata and summaries: [`report.json`](../../evaluation/results/runs/20261018T124223Z-2274338-w100_o20/report.json)
- Experimental pass records: [`pass-1.json`](../../evaluation/results/runs/20261018T124223Z-2274338-w100_o20/pass-1.json), [`pass-2.json`](../../evaluation/results/runs/20261018T124223Z-2274338-w100_o20/pass-2.json)
- Saved paired metrics and gate assessment: [`chunking-comparison.json`](../../evaluation/results/runs/20261018T124223Z-2274338-w100_o20/chunking-comparison.json)
- Run commands and captured comparison output: [`chunking-experiment.md`, entry 011](./chunking-experiment.md)
- Approved decision criteria: [`chunking-experiment.md`, entry 004](./chunking-experiment.md)

The repository architecture assigns run comparison and evaluation reports to `evaluation/`; therefore the report's source artifacts remain there ([architecture reference index](../architecture.md)).

## 3. Quantitative Comparison

Retrieval metrics were identical in pass 1 and pass 2. The denominator for the overall, direct, paraphrased, and label-file-type retrieval metrics is shown in each row.

### Retrieval metrics

| Slice | Arm | Questions | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---|---:|---:|---:|---:|---:|
| Overall | 60/10 | 16 | 8/16 (50.00%) | 11/16 (68.75%) | 11/16 (68.75%) | 0.572917 |
| Overall | 100/20 | 16 | 9/16 (56.25%) | 12/16 (75.00%) | 15/16 (93.75%) | 0.700000 |
| Direct | 60/10 | 8 | 6/8 (75.00%) | 7/8 (87.50%) | 7/8 (87.50%) | 0.791667 |
| Direct | 100/20 | 8 | 6/8 (75.00%) | 7/8 (87.50%) | 8/8 (100%) | 0.843750 |
| Paraphrased | 60/10 | 8 | 2/8 (25.00%) | 4/8 (50.00%) | 4/8 (50.00%) | 0.354167 |
| Paraphrased | 100/20 | 8 | 3/8 (37.50%) | 5/8 (62.50%) | 7/8 (87.50%) | 0.556250 |

Overall deltas are +1 Hit@1 (+6.25 percentage points), +1 Hit@3 (+6.25 points), +4 Hit@5 (+25 points), and +0.127083 MRR. The direct-question Hit@5 gain is +1/8; the paraphrased-question gains are +1/8 at Hit@1, +1/8 at Hit@3, and +3/8 at Hit@5.

### Label-file-type split

All 16 answerable golden-set labels are in non-test files; the saved comparison has no test-file labels. Consequently the test-file stratum has a zero denominator and cannot support a test-vs-non-test comparison.

| Label file type | Arm | Questions | Hit@1 | Hit@3 | Hit@5 | MRR |
|---|---|---:|---:|---:|---:|---:|
| Non-test | 60/10 | 16 | 8/16 | 11/16 | 11/16 | 0.572917 |
| Non-test | 100/20 | 16 | 9/16 | 12/16 | 15/16 | 0.700000 |
| Test | 60/10 | 0 | n/a | n/a | n/a | n/a |
| Test | 100/20 | 0 | n/a | n/a | n/a | n/a |

### File/function coverage, context, tokens, and generation

| Measure | 60/10 | 100/20 | Difference |
|---|---:|---:|---:|
| Hit-by-file@5 | 13/16 (81.25%) | 16/16 (100%) | +3 questions / +18.75 percentage points |
| Hit-by-function@5, applicable labels only | 1/7 (14.29%) | 5/7 (71.43%) | +4 questions / +57.14 percentage points |
| Module-level labels excluded from function metric | 9 (n/a) | 9 (n/a) | No change |
| Median top-5 context characters, each pass | 7,729.5 | 11,072.0 | +3,342.5 / +43.24% |
| Pass 1 median total tokens per question | 2,835.5 (20 records) | 3,971.5 (20 records) | +1,136 / +40.06%; 1.401× baseline |
| Pass 2 median total tokens per question | 2,867.5 (20 records) | 4,001.0 (20 records) | +1,133.5 / +39.53%; 1.395× baseline |

The token median uses the 20 records with token usage; the four far-unanswerable records have no token total. Function-level hit evaluation applies only where the label is inside a function or class, as ruled by the maintainer; module-level labels are n/a, not misses.

| Safety / run measure | 60/10 | 100/20 |
|---|---:|---:|
| Guard false accepts | 4/24 | 4/24 |
| `answered_unanswerable` under outcome_v2 | 0/24 | 0/24 |
| Generation errors | 0/42 HTTP calls | 0/42 HTTP calls |
| HTTP 429 responses | 2 | 1 |

Do not conflate the legacy `falsely answered` category with outcome_v2 `answered_unanswerable`: the saved runs report four legacy falsely-answered records per pass and zero v2 answered-unanswerable records. Legacy outcome counts and v2 outcome counts are shown below for all 24 records per pass.

| Pass | Arm | Legacy correct | Legacy wrong/incomplete | Legacy refused | Legacy falsely answered | V2 correct_labeled_context | V2 correct_unlabeled_context | V2 incomplete_or_wrong | V2 retrieval_miss_abstained | V2 guard_true_refusal | V2 model_abstained |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 60/10 | 13 | 3 | 4 | 4 | 10 | 3 | 1 | 2 | 4 | 4 |
| 1 | 100/20 | 15 | 1 | 4 | 4 | 14 | 1 | 1 | 0 | 4 | 4 |
| 2 | 60/10 | 13 | 3 | 4 | 4 | 10 | 3 | 2 | 1 | 4 | 4 |
| 2 | 100/20 | 16 | 0 | 4 | 4 | 15 | 1 | 0 | 0 | 4 | 4 |

Each row's categories sum to 24. The saved report records 42 generation HTTP calls in each run; the 429 counts differ, but the reported generation-error count is zero for both.

## 4. Question-Level Analysis

The table below contains all 16 answerable questions. `Rank` is the labeled chunk's rank (— means not in the top five); the hit triplet is Hit@1/Hit@3/Hit@5. `Gained` lists newly met cutoffs; no previously met cutoff was lost.

| Question | 60/10 rank | 100/20 rank | 60/10 hits | 100/20 hits | Retrieval change |
|---|---:|---:|---|---|---|
| `direct-01` | 1 | 1 | 1/1/1 | 1/1/1 | Unchanged |
| `direct-02` | 1 | 1 | 1/1/1 | 1/1/1 | Unchanged |
| `direct-03` | 1 | 1 | 1/1/1 | 1/1/1 | Unchanged |
| `direct-04` | 1 | 1 | 1/1/1 | 1/1/1 | Unchanged rank/hits; answer outcome improves |
| `direct-05` | 3 | 2 | 0/1/1 | 0/1/1 | Rank improves; threshold hits unchanged; pass-1 answer regresses |
| `direct-06` | 1 | 1 | 1/1/1 | 1/1/1 | Unchanged |
| `direct-07` | 1 | 1 | 1/1/1 | 1/1/1 | Unchanged |
| `direct-08` | — | 4 | 0/0/0 | 0/0/1 | Gained @5 |
| `paraphrased-01` | 1 | 1 | 1/1/1 | 1/1/1 | Unchanged |
| `paraphrased-02` | 2 | 1 | 0/1/1 | 1/1/1 | Gained @1 |
| `paraphrased-03` | — | 2 | 0/0/0 | 0/1/1 | Gained @3 and @5 |
| `paraphrased-04` | 3 | 2 | 0/1/1 | 0/1/1 | Rank improves; threshold hits unchanged |
| `paraphrased-05` | — | 4 | 0/0/0 | 0/0/1 | Gained @5 |
| `paraphrased-06` | 1 | 1 | 1/1/1 | 1/1/1 | Unchanged |
| `paraphrased-07` | — | — | 0/0/0 | 0/0/0 | Unchanged miss |
| `paraphrased-08` | — | 5 | 0/0/0 | 0/0/1 | Gained @5 |

There are no retrieval regressions at Hit@1/3/5; four questions newly enter Hit@5 (`direct-08`, `paraphrased-03`, `paraphrased-05`, and `paraphrased-08`). `paraphrased-02` additionally moves from rank 2 to rank 1. `direct-05` moves from rank 3 to rank 2, but this improved rank did not prevent its pass-1 answer from failing the recorded answer screen.

### Generated-answer outcome changes and `direct-05`

These saved answer records are reproduced verbatim below for the questions whose outcome_v2 changes in at least one pass. Outcome labels are the recorded values; they are not independent human correctness judgments. Retrieved evidence is identified by saved chunk IDs and file/line ranges. Citation IDs mean cited chunk IDs in the corresponding record.

#### `direct-04` — threshold constant; improved outcome in both passes

- **Retrieved evidence:** baseline labeled chunk 1458 (`app/investigation/guard.py:1-60`), rank 1; experiment labeled chunk 1558 (`app/investigation/guard.py:1-70`), rank 1. Experimental citations were 1558 and 1552 (`app/investigation/confidence.py:1-38`).
- **Recorded outcomes:** baseline pass 1/2 `wrong-or-incomplete` / `incomplete_or_wrong`; experiment pass 1/2 `correct` / `correct_labeled_context`.
- **Baseline pass 1:** “The constant controlling the minimum RRF score is `MIN_ACCEPTABLE_RRF_SCORE`.”
- **Baseline pass 2:** “The constant `MIN_ACCEPTABLE_RRF_SCORE` controls the minimum RRF score.”
- **Experiment pass 1:** “The constant `MIN_ACCEPTABLE_RRF_SCORE` (set to `0.016` in `app/investigation/guard.py`) controls the minimum RRF score required for evidence sufficiency. Additionally, `MIN_CLEAR_RRF_SCORE` (set to `0.032` in `app/investigation/confidence.py`) is used for confidence calibration regarding clear RRF scores.”
- **Experiment pass 2:** “The constant controlling the minimum acceptable RRF score is `MIN_ACCEPTABLE_RRF_SCORE` (set to `0.016` in `app/investigation/guard.py`). Additionally, `MIN_CLEAR_RRF_SCORE` (set to `0.032` in `app/investigation/confidence.py`) controls the clear RRF score threshold used for confidence calibration.”

#### `direct-05` — maximum vector distance; pass-1 regression

- **Retrieved evidence:** baseline labeled chunks 1458/1459 (`app/investigation/guard.py:1-60`, `51-70`), rank 3; experiment labeled chunk 1558 (`app/investigation/guard.py:1-70`), rank 2. The experimental record cites chunk 1558.
- **Recorded outcomes:** baseline pass 1/2 `correct` / `correct_labeled_context`; experiment pass 1 `wrong-or-incomplete` / `incomplete_or_wrong`; experiment pass 2 `correct` / `correct_labeled_context`.
- **Baseline pass 1:** “The constant that controls the maximum vector distance is `MAX_ACCEPTABLE_VECTOR_DISTANCE` (set to `0.5`).”
- **Baseline pass 2:** “The constant controlling the maximum acceptable vector distance is `MAX_ACCEPTABLE_VECTOR_DISTANCE`, which is set to `0.5` in `app/investigation/guard.py`.”
- **Experiment pass 1:** “The constant `MAX_ACCEPTABLE_VECTOR_DISTANCE` controls the maximum vector distance.”
- **Experiment pass 2:** “The constant `MAX_ACCEPTABLE_VECTOR_DISTANCE` controls the maximum vector distance (set to `0.5`).”

This is a concrete counterexample to equating rank with answer correctness: the experimental pass-1 answer omitted `0.5`, which the recorded answer screen required, even though the labeled chunk ranked higher and was cited. The experimental pass-2 answer supplied `0.5` and passed. Human review should verify completeness and grounding in both answers and determine how much significance to assign to this single-pass regression.

#### `direct-08` — final confidence passed to persistence; newly retrieved and answered

- **Retrieved evidence:** baseline had no labeled chunk in top five and no citations. Experiment labeled chunk 1575 (`scripts/investigate.py:81-180`) ranked 4 and was cited; chunk 1592 (`tests/unit/test_investigation_persistence.py:81-120`) was also cited.
- **Recorded outcomes:** baseline pass 1/2 `wrong-or-incomplete` / `retrieval_miss_abstained`; experiment pass 1/2 `correct` / `correct_labeled_context`.
- **Baseline pass 1 and pass 2:** `INSUFFICIENT_EVIDENCE`
- **Experiment pass 1:** “The final confidence is passed into persistence via `final_confidence=result["confidence"]` (or explicitly as `final_confidence="medium"` in unit tests) when calling `persist_investigation`.”
- **Experiment pass 2:** “The final confidence is passed into persistence via the `final_confidence` parameter in `persist_investigation(...)`. For example, in tests it is passed explicitly (e.g., `final_confidence="medium"`), and in `scripts/investigate.py`, it is passed as `final_confidence=result["confidence"]`.”

#### `paraphrased-03` — embedding API flow; outcome subtype changes in both passes

- **Retrieved evidence:** baseline's labeled `scripts/embed_chunks.py` chunk 1477 was outside top five; its citations included 1477. Experiment's labeled chunk 1570 (`scripts/embed_chunks.py:1-100`) ranked 2 and was cited.
- **Recorded outcomes:** baseline pass 1/2 `correct` / `correct_unlabeled_context`; experiment pass 1/2 `correct` / `correct_labeled_context`. The legacy outcome remains `correct` in both arms.
- **Baseline pass 1:** “The project embeds repository chunk text using an external Gemini API request (via `scripts/embed_chunks.py`), parses the JSON response to extract the embedding values, validates that the values form a list of length equal to `EMBEDDING_DIMENSION` (768), converts each value to a float, and assigns the resulting list to `chunk.embedding = embed_text(chunk.content)` before persisting it in the database.”
- **Baseline pass 2:** “The project embeds repository chunks by sending an HTTP POST request to the Gemini API (using `scripts/embed_chunks.py`), parsing the response JSON to extract the `"embedding"` values list, validating that the dimension matches `EMBEDDING_DIMENSION`, converting each value to a float, and assigning the resulting list of floats to `chunk.embedding` before saving it to the database where it is stored in a `VECTOR(768)` column.”
- **Experiment pass 1:** “The project turns text into numeric vectors by calling the Gemini embeddings API (`models/gemini-embedding-001`) via the `embed_text` function in `scripts/embed_chunks.py`. This function sends an HTTP POST request with the text content, model name, and an output dimensionality of 768, and returns the resulting list of floating-point values from the API response.”
- **Experiment pass 2:** “The project turns text into numeric vectors before storage by calling the Gemini embeddings API (`models/gemini-embedding-001`) via the `embed_text` function in `scripts/embed_chunks.py`. This function sends a POST request with the text payload and output dimensionality of 768 to the Gemini API endpoint, parses the returned embedding values into a list of floats, and assigns them to the `chunk.embedding` attribute.”

#### `paraphrased-05` — weak evidence routing; outcome subtype changes in both passes

- **Retrieved evidence:** baseline top five included graph chunks 1454/1455 (`app/investigation/graph.py:101-160`, `151-210`), but not the labeled guard chunk; citations included those graph chunks and test chunks. Experiment's labeled chunk 1558 (`app/investigation/guard.py:1-70`) ranked 4 and was cited; its other citations included graph chunks 1554/1556 and test chunks.
- **Recorded outcomes:** baseline pass 1/2 `correct` / `correct_unlabeled_context`; experiment pass 1/2 `correct` / `correct_labeled_context`. Legacy outcome remains `correct` in both arms.
- **Baseline pass 1:** “A weak search result is evaluated for sufficiency using `evaluate_evidence_sufficiency`, and if it is deemed insufficient, the investigation graph either retries with a widened search limit, falls back to a literal grep search, or ultimately stops and returns an insufficient diagnosis (such as `INSUFFICIENT_EVIDENCE`) via `return_insufficient`, preventing generation from running.”
- **Baseline pass 2:** “A weak search result is evaluated for sufficiency using `evaluate_evidence_sufficiency`. If the evidence check determines the results are insufficient (`is_sufficient` is False), `route_after_guard` handles the routing: if it is a literal search source, it stops; if the retry count is 0, it retries with a widened search; otherwise, it proceeds to grep. If evidence remains insufficient after retries and literal fallback (e.g., when grep has no match), the graph routes to `return_insufficient`, which returns an "INSUFFICIENT_EVIDENCE" diagnosis, preventing generation from running without sufficient evidence.”
- **Experiment pass 1:** “A weak search result is evaluated by the evidence sufficiency guard (`evaluate_evidence_sufficiency`), which checks if its RRF score meets or exceeds `MIN_ACCEPTABLE_RRF_SCORE` (0.016) and its vector cosine distance is less than or equal to `MAX_ACCEPTABLE_VECTOR_DISTANCE` (0.5). If the evidence is deemed insufficient, `route_after_guard` prevents it from proceeding to prompt building and generation; instead, if it is the first retry attempt (`retry_count == 0` and evidence source is hybrid), the graph triggers a wider search retry or falls back to literal grep search, and ultimately returns "INSUFFICIENT_EVIDENCE" with low confidence if the evidence remains insufficient.”
- **Experiment pass 2:** “A weak search result is evaluated by the evidence quality guard (`evaluate_evidence_sufficiency`), which checks if the result meets the required thresholds (such as `MIN_ACCEPTABLE_RRF_SCORE` of 0.016 and `MAX_ACCEPTABLE_VECTOR_DISTANCE` of 0.5). If the evidence is deemed insufficient (`is_sufficient` is False), the investigation graph routes via `route_after_guard`: if it is the first retry count and the source is hybrid, it triggers a wider search (`retry`), falls back to a literal grep search (`grep`), or stops/returns insufficient evidence (`INSUFFICIENT_EVIDENCE`), thereby preventing weak search results from proceeding directly to prompt generation and the language model.”

#### `paraphrased-08` — Audit record; citation concern

- **Retrieved evidence:** baseline's labeled `app/investigation/persistence.py` chunk 1562 was not in its top five; baseline pass 2 cited chunk 1506 (`tests/unit/test_investigation_persistence.py:51-110`). Experiment's labeled chunk 1562 (`app/investigation/persistence.py:1-93`) ranked 5 in both passes, but **the experimental records cite no chunks**.
- **Recorded outcomes:** baseline pass 1 `wrong-or-incomplete` / `retrieval_miss_abstained`; baseline pass 2 `wrong-or-incomplete` / `incomplete_or_wrong`; experiment pass 1/2 `correct` / `correct_labeled_context`.
- **Baseline pass 1:** `INSUFFICIENT_EVIDENCE`
- **Baseline pass 2:** “`persist_investigation` stores the investigation record (keeping the query, response, model, latency, token usage, retrieval results, and other metadata together, as shown in `tests/unit/test_investigation_persistence.py`).”
- **Experiment pass 1:** “The `Audit` record keeps the retrieved evidence (such as `retrieved_chunk_ids`, `vector_scores`, `fts_scores`, `rrf_scores`, and detailed retrieval results) and response metadata (such as `query`, `repository_id`, `model`, `response`, `latency_ms`, `token_usage`, `confidence`, and `tool_calls`) together.”
- **Experiment pass 2:** “An Audit record (or Audit model) keeps the retrieved evidence and response metadata together by storing retrieval results, scores, tool calls, response text, model, latency, token usage, and confidence alongside the investigation ID.”

The experimental answer is recorded as correct by the evaluation, but its empty citation list means this artifact does not demonstrate cited grounding for the answer. Human review should check the actual retrieved context and whether the answer's claims are supported.

### What the metrics establish—and do not establish

The paired retrieval results show that, for this pinned corpus and these 16 answerable questions, the 100/20 strategy placed more labeled chunks in the top five without losing any existing Hit@5 question. The two saved passes also show consistent retrieval metrics. The answer-screen labels show recorded outcomes for these evaluation executions, including the `direct-05` pass-1 regression and `paraphrased-08`'s missing citations.

These results do not establish general performance beyond this small corpus/question set, correctness as judged by a human, that a passing answer-screen label guarantees completeness or grounding, or that performance will be stable across other codebases, questions, or generation runs. The 24-question set is still marked pending maintainer review.

## 5. Gate 5: Human Correctness Review

**Status: PENDING — not performed by this report.** The preceding section compares the exact saved baseline and experimental answers, retrieved evidence, and recorded outcome labels for all questions whose outcome_v2 changes in either pass. That comparison is material for a reviewer; it is not itself an approval or a human correctness verdict.

Manual review should pay particular attention to:

1. `direct-05`, experimental pass 1: required `0.5` is absent; pass 2 includes it. Check correctness, completeness, and whether the cited chunk supports each answer.
2. `paraphrased-08`, experimental passes 1 and 2: labeled chunk is rank 5, while cited chunk IDs are empty. Verify grounding against the actual retrieved top-five context.
3. `direct-04`, `direct-08`, `paraphrased-03`, and `paraphrased-05`: confirm answer completeness and support in the recorded cited/retrieved chunks, not only agreement with the label substring or automated screen.

The saved run artifacts do not contain a human verdict. The human-review workbook now records the maintainer's current 55% lean toward 100/20 and 45% toward 60/10, while concluding that the evidence does not establish a clear winner. Gate 5 remains neutral and pending further review; this position does not mark Gate 5 PASS or authorize adoption under D4.

## 6. Approved D4 Adoption-Gate Checklist

The criteria below are the approved D4 criteria in [`chunking-experiment.md`, entry 004](./chunking-experiment.md). The report preserves the criteria and their interpretation; Gate 5 is not inferred from automated outcomes. Gate 7 counts function hits only for labels inside a function or class and treats module-level labels as not applicable.

| Gate | Approved criterion | Result | Evidence |
|---:|---|---|---|
| 1 | At least two net additional Hit@5 questions compared with a fresh baseline run. | **PASS** | The saved baseline and experimental runs are paired on the same pinned SHA; pass 1 Hit@5 is 11/16 vs 15/16, net +4 (required at least +2). |
| 2 | Hit@3 and Hit@5 must not decrease. | **PASS** | Both passes: Hit@3 delta +1 question; Hit@5 delta +4. |
| 3 | Explain every previously hit question that is lost. | **PASS** | No previously Hit@5 question was lost; loss list is empty. |
| 4 | Guard false accepts must remain at or below four, with no new answered-unanswerable cases. | **PASS** | False accepts are 4/24 in each arm; outcome_v2 answered-unanswerable is 0/24 in each; no new answered-unanswerable questions. Legacy falsely-answered is separately 4 in each arm. |
| 5 | Human-reviewed end-to-end correctness must not be lower. | **MANUAL — PENDING** | The workbook records the maintainer's current neutral position, not a final Gate 5 verdict. Answer comparisons are in sections 4–5; the gate cannot yet pass. |
| 6 | Median tokens per question should remain within approximately 1.5 times the baseline. | **PASS** | Pass 1: 3,971.5 / 2,835.5 = 1.401×. Pass 2: 4,001 / 2,867.5 = 1.395×. Both are below approximately 1.5×. |
| 7 | Improvements must be visible in hit-by-function and hit-by-file, not only hit-by-label. | **PASS** | Hit-by-file@5: 13/16 → 16/16. Hit-by-function@5: 1/7 → 5/7. Nine module-level labels are n/a for function hits. |
| 8 | A net gain of only one Hit@5 question is inconclusive; retain the baseline. | **PASS** | Net Hit@5 gain is +4, not +1. |
| 9 | MRR is a supporting metric, not an independent adoption route. | **PASS — SUPPORTING ONLY** | MRR increases 0.572917 → 0.700000 (+0.127083); this is supporting evidence only and does not replace any other gate. |

## 7. Trade-Off Analysis

**Measured facts**

- The 100/20 arm uses 52 chunks instead of 70 for the same 40-file corpus: 18 fewer chunks (25.71% fewer).
- Retrieval gains are largest for paraphrased questions at Hit@5 (4/8 to 7/8); direct questions improve from 7/8 to 8/8.
- Median top-five retrieved context is 43.24% larger. Median total tokens per question are about 40% higher in both passes.
- Guard false accepts do not increase, no v2 answered-unanswerable cases are reported, and both runs report zero generation errors. The runs have 2 and 1 HTTP 429 responses respectively.
- No retrieval cutoff regressed, but `direct-05` shows an answer-quality regression in one experimental pass, and `paraphrased-08` has no recorded experimental citations.

**Interpretation / risk**

The larger windows appear to improve labeled-chunk coverage—especially on paraphrases—while lowering the number of chunks in the evaluation corpus. The cost is more retrieved text and tokens per question, which can affect latency and operational cost; this evaluation does not establish the cost at production scale. The `direct-05` variation illustrates that retrieval rank alone does not ensure the generation step includes required details. The citation gap in `paraphrased-08` also means outcome labels alone are insufficient evidence of grounding.

These are two runs over a small, fixed evaluation set, not a broad benchmark. The token increase is within the approved gate but remains a real trade-off; its business acceptability beyond that gate is not measured here.

## 8. Final Recommendation

**Provisional recommendation: keep 60/10 as the adopted production strategy until Gate 5 is manually completed; consider 100/20 the retrieval-favored candidate.**

The saved evidence establishes a repeatable retrieval improvement on this 16-question set, with no Hit@3/Hit@5 losses and gains in both file and applicable function coverage. It also establishes higher context/token use and exposes answer-level issues that retrieval metrics cannot resolve.

The workbook now records the maintainer's overall 55/45 lean but finds no clear winner and keeps Gate 5 neutral pending further review. Before adoption, the remaining review must resolve whether end-to-end correctness is not lower, especially considering `direct-05`'s omitted required value and `paraphrased-08`'s empty citations. Until a final human decision is made, the approved all-gates requirement is unmet; this report does not claim approval.

## 9. Evidence References and Limitations

| Evidence | What it supports |
|---|---|
| `evaluation/results/runs/20261018T123627Z-2274338-baseline/report.json` | Baseline run identity, configuration, generation summary, legacy and v2 outcome totals, token/citation/guard summaries. |
| `evaluation/results/runs/20261018T123627Z-2274338-baseline/pass-1.json` and `pass-2.json` | Baseline per-question answers, citations, retrieved chunks, ranks, and outcome labels. |
| `evaluation/results/runs/20261018T124223Z-2274338-w100_o20/report.json` | Experimental run identity, configuration, generation summary, legacy and v2 outcome totals, token/citation/guard summaries. |
| `evaluation/results/runs/20261018T124223Z-2274338-w100_o20/pass-1.json` and `pass-2.json` | Experimental per-question answers, citations, retrieved chunks, ranks, and outcome labels. |
| `evaluation/results/runs/20261018T124223Z-2274338-w100_o20/chunking-comparison.json` | Paired ranks/hits, category and label-file metrics, outcome_v2 changes, and computed gate evidence. |
| `chunking-experiment.md`, entries 004 and 011 | Approved D4 criteria and the recorded commands/comparator output. |
| `../architecture.md`, section 14 and verification notes | Evaluation report ownership and cautions about local/ignored artifacts and evidence scope. |

**Insufficient or missing evidence:** a final human Gate 5 decision (the current overall position is neutral/pending); test-file label subgroup (zero questions); performance outside the 40-file pinned corpus and 24-question set; broader multi-run generation variance; production-scale latency/cost; independent verification of all cited answer claims. The run artifacts may be ignored or local to this checkout and are not guaranteed to exist in other clones. The golden set remains marked “pending maintainer review,” including its labels.
