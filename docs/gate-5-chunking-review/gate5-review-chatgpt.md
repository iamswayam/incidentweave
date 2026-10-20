# Gate 5 Independent Review — ChatGPT

**Reviewer:** ChatGPT (GPT-6)\
**Date:** 2026-10-19\
**Pinned source commit:** `62d0e58593bb22d187ec7930274b0457afd3be74`\
**Run IDs:** baseline `20261018T123627Z-2274338-baseline` (60/10, 70 chunks); experiment `20261018T124223Z-2274338-w100_o20` (100/20, 52 chunks).

## Independence statement

I read the human-review workbook `evaluation/chunking-human-review-workbook.md` supplied at `/mnt/data/chunking-human-review-workbook.md` and independently fetched the specified source files from the pinned commit using GitHub file reads. I did **not** read any `docs/gate5-review-*` file or the decision report, and did not use `outcome_v2`, keyword screens, or automated verdicts as evidence. I had a prior provisional opinion on `direct-04` from an earlier conversational pass; I re-evaluated it against the workbook and pinned source rather than treating that opinion as binding.

## Inspected and not inspected

- **Inspected:** all 24 question sections and four saved response instances per question in the workbook; saved citation IDs and citation-relevance metadata; the retrieved top-five spans shown in the workbook; pinned source for `guard.py`, `confidence.py`, `persistence.py`, `graph.py`, `mcp_server.py`, `session.py`, `audit.py`, `chunk.py`, `hybrid_search.py`, `embed_chunks.py`, `ingest_repo.py`, `investigate.py`, and `tests/unit/test_investigation_persistence.py`.
- **Not inspected:** raw local/ignored run JSONs; database; live application; any API; other reviewers’ files; execution of the experiment. I did not run tests or change code/configuration.
- **Important limitation:** fetching `docs/chunking-experiment.md` at the specified pinned commit returned 404. I therefore could not independently inspect entry [004] at that exact path. The run identities and stated scope below are taken from the workbook/user-provided prompt. For unanswerable questions, the workbook labels them as having no golden source; I inspected the recursive pinned repository tree, but did not fetch and text-search every blob body; repository-wide topic absence is therefore not independently proven.

## Scoring note

Scores use the requested 0–10 rubric. The overall score is a judgement, not an average. `INSUFFICIENT_EVIDENCE` on the 16 answerable questions is scored as an abstention (Correctness `—`, Completeness 0, Overall 2). For the eight designated unanswerable questions, correct abstention receives Correctness 10, Completeness `n/a`, Grounding 10, Overall 10 as required. Citation relevance metadata is treated as a pointer for inspection, not as proof. Source verification is based on the fetched pinned code; where I could not inspect full chunk bodies, I say so rather than claiming source-level confirmation.

## Priority questions

### Question: direct-04
**Question:** What constant controls the minimum RRF score?
**Expected answer / authoritative reference:** app/investigation/guard.py: `MIN_ACCEPTABLE_RRF_SCORE = 0.016`. Pinned source line(s): `app/investigation/guard.py:7`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 9 | 7 | 8 |
| 100/20 — Pass 1 | 10 | 9 | 7 | 9 |
| 60/10 — Pass 2 | 9 | 8 | 0 | 7 |
| 100/20 — Pass 2 | 10 | 9 | 7 | 9 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** The constant controlling the minimum RRF score is `MIN_ACCEPTABLE_RRF_SCORE`.
- **Citations:** 1458, 1459. Workbook relevance flags: 1 relevant of 2 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 9; grounding 7; overall 8. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** The constant `MIN_ACCEPTABLE_RRF_SCORE` (set to `0.016` in `app/investigation/guard.py`) controls the minimum RRF score required for evidence sufficiency. Additionally, `MIN_CLEAR_RRF_SCORE` (set to `0.032` in `app/investigation/confidence.py`) is used for confidence calibration regarding clear RRF scores.
- **Citations:** 1558, 1552. Workbook relevance flags: 1 relevant of 2 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 9; grounding 7; overall 9. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** The constant `MIN_ACCEPTABLE_RRF_SCORE` controls the minimum RRF score.
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
- **Score rationale:** Correctness 9; completeness 8; grounding 0; overall 7. Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** The constant controlling the minimum acceptable RRF score is `MIN_ACCEPTABLE_RRF_SCORE` (set to `0.016` in `app/investigation/guard.py`). Additionally, `MIN_CLEAR_RRF_SCORE` (set to `0.032` in `app/investigation/confidence.py`) controls the clear RRF score threshold used for confidence calibration.
- **Citations:** 1558, 1552. Workbook relevance flags: 1 relevant of 2 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 9; grounding 7; overall 9. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 9 vs 60/10 8 | Better (minor) |
| Pass 2 | 100/20 9 vs 60/10 7 | Better (minor) |

#### Question-level conclusion

100/20 is better in both passes: it includes the threshold value and cites the guard chunk. The confidence-calibration detail is true but not required and its citation is not primary evidence for the asked constant. Baseline pass 2 loses grounding by omitting citations.

### Question: direct-05
**Question:** What constant controls the maximum vector distance?
**Expected answer / authoritative reference:** app/investigation/guard.py: `MAX_ACCEPTABLE_VECTOR_DISTANCE = 0.5`. Pinned source line(s): `app/investigation/guard.py:8`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 7 | 9 |
| 100/20 — Pass 1 | 10 | 9 | 8 | 8 |
| 60/10 — Pass 2 | 10 | 10 | 7 | 9 |
| 100/20 — Pass 2 | 10 | 10 | 9 | 9 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** The constant that controls the maximum vector distance is `MAX_ACCEPTABLE_VECTOR_DISTANCE` (set to `0.5`).
- **Citations:** 1458, 1459. Workbook relevance flags: 1 relevant of 2 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 10; grounding 7; overall 9. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** The constant `MAX_ACCEPTABLE_VECTOR_DISTANCE` controls the maximum vector distance.
- **Citations:** 1558. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 9; grounding 8; overall 8. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** The constant controlling the maximum acceptable vector distance is `MAX_ACCEPTABLE_VECTOR_DISTANCE`, which is set to `0.5` in `app/investigation/guard.py`.
- **Citations:** 1458, 1459. Workbook relevance flags: 1 relevant of 2 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 10; grounding 7; overall 9. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** The constant `MAX_ACCEPTABLE_VECTOR_DISTANCE` controls the maximum vector distance (set to `0.5`).
- **Citations:** 1558. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 9; overall 9. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 8 vs 60/10 9 | Worse (minor) |
| Pass 2 | 100/20 9 vs 60/10 9 | Same (equivalent) |

#### Question-level conclusion

Pass 1 is effectively close: baseline gives the value and experiment gives only the symbol, so baseline is more complete; experiment has the cleaner single relevant citation. Pass 2 is approximately equivalent, with the baseline naming the file/value and experiment naming the value but still citing the relevant chunk.

### Question: direct-08
**Question:** Where is the final confidence passed into persistence?
**Expected answer / authoritative reference:** scripts/investigate.py: `final_confidence=result["confidence"]`. Pinned source line(s): `scripts/investigate.py:118-126`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | — | 0 | 0 | 2 |
| 100/20 — Pass 1 | 10 | 9 | 7 | 8 |
| 60/10 — Pass 2 | — | 0 | 0 | 2 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** The question is answerable from the pinned source, but the run abstained. This is a material completeness failure; citations are absent or do not support an answer.
- **Score rationale:** Correctness —; completeness 0; grounding 0; overall 2. The question is answerable from the pinned source, but the run abstained. This is a material completeness failure; citations are absent or do not support an answer.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** The final confidence is passed into persistence via `final_confidence=result["confidence"]` (or explicitly as `final_confidence="medium"` in unit tests) when calling `persist_investigation`.
- **Citations:** 1592, 1575. Workbook relevance flags: 1 relevant of 2 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 9; grounding 7; overall 8. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** The question is answerable from the pinned source, but the run abstained. This is a material completeness failure; citations are absent or do not support an answer.
- **Score rationale:** Correctness —; completeness 0; grounding 0; overall 2. The question is answerable from the pinned source, but the run abstained. This is a material completeness failure; citations are absent or do not support an answer.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** The final confidence is passed into persistence via the `final_confidence` parameter in `persist_investigation(...)`. For example, in tests it is passed explicitly (e.g., `final_confidence="medium"`), and in `scripts/investigate.py`, it is passed as `final_confidence=result["confidence"]`.
- **Citations:** 1575. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 8 vs 60/10 2 | Better (clear) |
| Pass 2 | 100/20 10 vs 60/10 2 | Better (clear) |

#### Question-level conclusion

Clear improvement in both passes: baseline abstains on an answerable question, while 100/20 retrieves the persistence call and answers it. Pass-1 experiment cites one relevant chunk plus one irrelevant chunk; pass 2 cites the relevant chunk only.

### Question: paraphrased-03
**Question:** How does the project turn text into numeric vectors before storage?
**Expected answer / authoritative reference:** scripts/embed_chunks.py: `outputDimensionality`. Pinned source line(s): `scripts/embed_chunks.py:25-26, 38-75`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 9 | 8 | 5 | 7 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 9 | 8 | 5 | 7 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** The project embeds repository chunk text using an external Gemini API request (via `scripts/embed_chunks.py`), parses the JSON response to extract the embedding values, validates that the values form a list of length equal to `EMBEDDING_DIMENSION` (768), converts each value to a float, and assigns the resulting list to `chunk.embedding = embed_text(chunk.content)` before persisting it in the database.
- **Citations:** 1477. Workbook relevance flags: 0 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is broadly consistent with pinned source, but none of the listed citations is marked relevant in the workbook; source support is not demonstrated by these citations.
- **Score rationale:** Correctness 9; completeness 8; grounding 5; overall 7. Claim is broadly consistent with pinned source, but none of the listed citations is marked relevant in the workbook; source support is not demonstrated by these citations.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** The project turns text into numeric vectors by calling the Gemini embeddings API (`models/gemini-embedding-001`) via the `embed_text` function in `scripts/embed_chunks.py`. This function sends an HTTP POST request with the text content, model name, and an output dimensionality of 768, and returns the resulting list of floating-point values from the API response.
- **Citations:** 1570. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** The project embeds repository chunks by sending an HTTP POST request to the Gemini API (using `scripts/embed_chunks.py`), parsing the response JSON to extract the `"embedding"` values list, validating that the dimension matches `EMBEDDING_DIMENSION`, converting each value to a float, and assigning the resulting list of floats to `chunk.embedding` before saving it to the database where it is stored in a `VECTOR(768)` column.
- **Citations:** 1477, 1444, 1492. Workbook relevance flags: 0 relevant of 3 listed, where flags are present.
- **Assessment:** Claim is broadly consistent with pinned source, but none of the listed citations is marked relevant in the workbook; source support is not demonstrated by these citations.
- **Score rationale:** Correctness 9; completeness 8; grounding 5; overall 7. Claim is broadly consistent with pinned source, but none of the listed citations is marked relevant in the workbook; source support is not demonstrated by these citations.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** The project turns text into numeric vectors before storage by calling the Gemini embeddings API (`models/gemini-embedding-001`) via the `embed_text` function in `scripts/embed_chunks.py`. This function sends a POST request with the text payload and output dimensionality of 768 to the Gemini API endpoint, parses the returned embedding values into a list of floats, and assigns them to the `chunk.embedding` attribute.
- **Citations:** 1570. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 10 vs 60/10 7 | Better (clear) |
| Pass 2 | 100/20 10 vs 60/10 7 | Better (clear) |

#### Question-level conclusion

100/20 is better in both passes because it retrieves and cites the embedding implementation. Baseline answers are technically accurate but cite only chunks marked irrelevant; pass 2 also adds a VECTOR(768) storage claim not directly grounded by its citations.

### Question: paraphrased-05
**Question:** What stops a weak search result from reaching the language model?
**Expected answer / authoritative reference:** app/investigation/guard.py: `is_sufficient =`. Pinned source line(s): `app/investigation/guard.py:7-8, 51-67`; `app/investigation/graph.py:164-203`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | — | 0 | 0 | 2 |
| 100/20 — Pass 1 | — | 0 | 0 | 2 |
| 60/10 — Pass 2 | — | 0 | 0 | 2 |
| 100/20 — Pass 2 | — | 0 | 0 | 2 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** A weak search result is evaluated for sufficiency using `evaluate_evidence_sufficiency`, and if it is deemed insufficient, the investigation graph either retries with a widened search limit, falls back to a literal grep search, or ultimately stops and returns an insufficient diagnosis (such as `INSUFFICIENT_EVIDENCE`) via `return_insufficient`, preventing generation from running.
- **Citations:** 1454, 1455, 1498, 1502, 1504. Workbook relevance flags: 0 relevant of 5 listed, where flags are present.
- **Assessment:** The question is answerable from the pinned source, but the run abstained. This is a material completeness failure; citations are absent or do not support an answer.
- **Score rationale:** Correctness —; completeness 0; grounding 0; overall 6. The question is answerable from the pinned source, but the run abstained. This is a material completeness failure; citations are absent or do not support an answer.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** A weak search result is evaluated by the evidence sufficiency guard (`evaluate_evidence_sufficiency`), which checks if its RRF score meets or exceeds `MIN_ACCEPTABLE_RRF_SCORE` (0.016) and its vector cosine distance is less than or equal to `MAX_ACCEPTABLE_VECTOR_DISTANCE` (0.5). If the evidence is deemed insufficient, `route_after_guard` prevents it from proceeding to prompt building and generation; instead, if it is the first retry attempt (`retry_count == 0` and evidence source is hybrid), the graph triggers a wider search retry or falls back to literal grep search, and ultimately returns "INSUFFICIENT_EVIDENCE" with low confidence if the evidence remains insufficient.
- **Citations:** 1586, 1554, 1585, 1558, 1556. Workbook relevance flags: 1 relevant of 5 listed, where flags are present.
- **Assessment:** The question is answerable from the pinned source, but the run abstained. This is a material completeness failure; citations are absent or do not support an answer.
- **Score rationale:** Correctness —; completeness 0; grounding 0; overall 8. The question is answerable from the pinned source, but the run abstained. This is a material completeness failure; citations are absent or do not support an answer.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** A weak search result is evaluated for sufficiency using `evaluate_evidence_sufficiency`. If the evidence check determines the results are insufficient (`is_sufficient` is False), `route_after_guard` handles the routing: if it is a literal search source, it stops; if the retry count is 0, it retries with a widened search; otherwise, it proceeds to grep. If evidence remains insufficient after retries and literal fallback (e.g., when grep has no match), the graph routes to `return_insufficient`, which returns an "INSUFFICIENT_EVIDENCE" diagnosis, preventing generation from running without sufficient evidence.
- **Citations:** 1454, 1455, 1498, 1502, 1504. Workbook relevance flags: 0 relevant of 5 listed, where flags are present.
- **Assessment:** The question is answerable from the pinned source, but the run abstained. This is a material completeness failure; citations are absent or do not support an answer.
- **Score rationale:** Correctness —; completeness 0; grounding 0; overall 6. The question is answerable from the pinned source, but the run abstained. This is a material completeness failure; citations are absent or do not support an answer.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** A weak search result is evaluated by the evidence quality guard (`evaluate_evidence_sufficiency`), which checks if the result meets the required thresholds (such as `MIN_ACCEPTABLE_RRF_SCORE` of 0.016 and `MAX_ACCEPTABLE_VECTOR_DISTANCE` of 0.5). If the evidence is deemed insufficient (`is_sufficient` is False), the investigation graph routes via `route_after_guard`: if it is the first retry count and the source is hybrid, it triggers a wider search (`retry`), falls back to a literal grep search (`grep`), or stops/returns insufficient evidence (`INSUFFICIENT_EVIDENCE`), thereby preventing weak search results from proceeding directly to prompt generation and the language model.
- **Citations:** 1586, 1554, 1585, 1558, 1556. Workbook relevance flags: 1 relevant of 5 listed, where flags are present.
- **Assessment:** The question is answerable from the pinned source, but the run abstained. This is a material completeness failure; citations are absent or do not support an answer.
- **Score rationale:** Correctness —; completeness 0; grounding 0; overall 8. The question is answerable from the pinned source, but the run abstained. This is a material completeness failure; citations are absent or do not support an answer.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 8 vs 60/10 6 | Better (minor) |
| Pass 2 | 100/20 8 vs 60/10 6 | Better (minor) |

#### Question-level conclusion

100/20 is better in both passes because it cites the guard chunk and describes the thresholds/routing more specifically. Grounding remains imperfect: the answer describes graph routing/retry/fallback, but the citations are mostly irrelevant and do not fully evidence all graph-level claims.

### Question: paraphrased-08
**Question:** What record keeps the retrieved evidence and response metadata together?
**Expected answer / authoritative reference:** app/investigation/persistence.py: `tool_calls`. Pinned source line(s): `app/investigation/persistence.py:49-90`; `app/db/models/audit.py:18-42`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | — | 0 | 0 | 2 |
| 100/20 — Pass 1 | 9 | 8 | 0 | 7 |
| 60/10 — Pass 2 | 8 | 8 | 4 | 5 |
| 100/20 — Pass 2 | 9 | 8 | 0 | 7 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** The question is answerable from the pinned source, but the run abstained. This is a material completeness failure; citations are absent or do not support an answer.
- **Score rationale:** Correctness —; completeness 0; grounding 0; overall 2. The question is answerable from the pinned source, but the run abstained. This is a material completeness failure; citations are absent or do not support an answer.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** The `Audit` record keeps the retrieved evidence (such as `retrieved_chunk_ids`, `vector_scores`, `fts_scores`, `rrf_scores`, and detailed retrieval results) and response metadata (such as `query`, `repository_id`, `model`, `response`, `latency_ms`, `token_usage`, `confidence`, and `tool_calls`) together.
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
- **Score rationale:** Correctness 9; completeness 8; grounding 0; overall 7. Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** `persist_investigation` stores the investigation record (keeping the query, response, model, latency, token usage, retrieval results, and other metadata together, as shown in `tests/unit/test_investigation_persistence.py`).
- **Citations:** 1506. Workbook relevance flags: 0 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is broadly consistent with pinned source, but none of the listed citations is marked relevant in the workbook; source support is not demonstrated by these citations.
- **Score rationale:** Correctness 8; completeness 8; grounding 4; overall 5. Claim is broadly consistent with pinned source, but none of the listed citations is marked relevant in the workbook; source support is not demonstrated by these citations.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** An Audit record (or Audit model) keeps the retrieved evidence and response metadata together by storing retrieval results, scores, tool calls, response text, model, latency, token usage, and confidence alongside the investigation ID.
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
- **Score rationale:** Correctness 9; completeness 8; grounding 0; overall 7. Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 7 vs 60/10 2 | Better (clear) |
| Pass 2 | 100/20 7 vs 60/10 5 | Better (minor) |

#### Question-level conclusion

100/20 is better in both passes. Baseline pass 1 abstains; baseline pass 2 discusses persistence generally but does not clearly name the `Audit` record asked for. Experiment names the Audit record and enumerates stored fields, but both experiment answers lack citations.

### Question: paraphrased-07
**Question:** How can the application find an exact phrase in its local source tree?
**Expected answer / authoritative reference:** app/investigation/mcp_server.py: `casefold()`. Pinned source line(s): `app/investigation/mcp_server.py:21-54`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 9 | 8 | 5 | 7 |
| 100/20 — Pass 1 | 9 | 8 | 0 | 7 |
| 60/10 — Pass 2 | 9 | 8 | 5 | 7 |
| 100/20 — Pass 2 | 9 | 8 | 5 | 7 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** The application can find a literal keyword in Python source files under a local repository path by using the `grep_search` tool (or `call_grep_search_mcp`), which searches raw local Python sources using the same file and directory exclusions as ingestion.
- **Citations:** 1500, 1461, 1501, 1453, 1499. Workbook relevance flags: 0 relevant of 5 listed, where flags are present.
- **Assessment:** Claim is broadly consistent with pinned source, but none of the listed citations is marked relevant in the workbook; source support is not demonstrated by these citations.
- **Score rationale:** Correctness 9; completeness 8; grounding 5; overall 7. Claim is broadly consistent with pinned source, but none of the listed citations is marked relevant in the workbook; source support is not demonstrated by these citations.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** The application can find an exact phrase (or literal keyword) in its local source tree by using the `grep_search` function (or via the MCP tool `grep_search`), which searches raw local Python source files under a local repository path using the same file and directory exclusions as ingestion.
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
- **Score rationale:** Correctness 9; completeness 8; grounding 0; overall 7. Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** The application can find a literal keyword in Python source files under a local repository path using the `grep_search` tool (or `call_grep_search_mcp`), which searches raw local Python sources using the same file and directory exclusions as ingestion.
- **Citations:** 1461, 1453. Workbook relevance flags: 0 relevant of 2 listed, where flags are present.
- **Assessment:** Claim is broadly consistent with pinned source, but none of the listed citations is marked relevant in the workbook; source support is not demonstrated by these citations.
- **Score rationale:** Correctness 9; completeness 8; grounding 5; overall 7. Claim is broadly consistent with pinned source, but none of the listed citations is marked relevant in the workbook; source support is not demonstrated by these citations.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** The application can find a literal keyword (or exact phrase) in its local source tree by using the `grep_search` function/tool (or the `grep_search_tool` MCP tool), which searches raw local Python sources under a local repository path while applying the same file and directory exclusions as ingestion.
- **Citations:** 1588, 1587, 1560. Workbook relevance flags: 0 relevant of 3 listed, where flags are present.
- **Assessment:** Claim is broadly consistent with pinned source, but none of the listed citations is marked relevant in the workbook; source support is not demonstrated by these citations.
- **Score rationale:** Correctness 9; completeness 8; grounding 5; overall 7. Claim is broadly consistent with pinned source, but none of the listed citations is marked relevant in the workbook; source support is not demonstrated by these citations.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 7 vs 60/10 7 | Same (equivalent) |
| Pass 2 | 100/20 7 vs 60/10 7 | Same (equivalent) |

#### Question-level conclusion

No decisive strategy winner. All four answers identify literal grep search accurately, but the cited chunks are absent or marked irrelevant. The main weakness is evidence grounding, not the core answer. Exact-phrase semantics are slightly broader than simple case-insensitive substring matching.

## Remaining questions

### Question: direct-01
**Question:** How is AsyncSessionLocal configured?
**Expected answer / authoritative reference:** app/db/session.py: `AsyncSessionLocal = async_sessionmaker`. Pinned source line(s): `app/db/session.py:35-39`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 9 | 9 | 9 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 9 | 9 | 9 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** AsyncSessionLocal is configured in `app/db/session.py` using `async_sessionmaker` with `bind=engine`, `class_=AsyncSession`, and `expire_on_commit=False`.
- **Citations:** 1447. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** `AsyncSessionLocal` is configured in `app/db/session.py` using `async_sessionmaker` with `bind=engine`, `class_=AsyncSession`, and `expire_on_commit=False`. The underlying async engine is created via `create_async_engine` using a database URL converted by `_async_database_url` (which replaces `"postgresql://"` with `"postgresql+psycopg://"`) and configured with `pool_pre_ping=True`. Additionally, an event listener on `engine.sync_engine` registers pgvector types for each async psycopg connection.
- **Citations:** 1550. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 9; grounding 9; overall 9. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** AsyncSessionLocal is configured in app/db/session.py using `async_sessionmaker` with `bind=engine`, `class_=AsyncSession`, and `expire_on_commit=False`.
- **Citations:** 1447. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** AsyncSessionLocal is configured in `app/db/session.py` using `async_sessionmaker` bound to an asynchronous SQLAlchemy engine created with `create_async_engine`, with `pool_pre_ping=True`, the psycopg async dialect URL conversion, a pgvector connection event listener, and `class_=AsyncSession` and `expire_on_commit=False`.
- **Citations:** 1550. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 9; grounding 9; overall 9. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 9 vs 60/10 10 | Worse (minor) |
| Pass 2 | 100/20 9 vs 60/10 10 | Worse (minor) |

#### Question-level conclusion

Both strategies answer correctly with relevant citations. Baseline is concise and fully answers the question; experiment adds accurate engine/URL/pgvector details but they are not needed. Slight preference for baseline concision, not a material quality difference.

### Question: direct-02
**Question:** What chunk size does ingest_repo.py use?
**Expected answer / authoritative reference:** scripts/ingest_repo.py: `CHUNK_SIZE = 60`. Pinned source line(s): `scripts/ingest_repo.py:22`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 9 | 0 | 8 |
| 100/20 — Pass 1 | 9 | 8 | 0 | 7 |
| 60/10 — Pass 2 | 10 | 9 | 7 | 8 |
| 100/20 — Pass 2 | 10 | 10 | 7 | 9 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** The `ingest_repo.py` script uses a chunk size of 60 lines (`CHUNK_SIZE = 60`) with an overlap size of 10 lines (`OVERLAP_SIZE = 10`), as defined by module-level constants and used in the `chunk_lines` function.
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
- **Score rationale:** Correctness 10; completeness 9; grounding 0; overall 8. Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** `ingest_repo.py` uses a chunk size of 60 lines (defined by `CHUNK_SIZE = 60`).
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
- **Score rationale:** Correctness 9; completeness 8; grounding 0; overall 7. Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** `scripts/ingest_repo.py` uses a chunk size defined by the constant `CHUNK_SIZE = 60`.
- **Citations:** 1479, 1480, 1481. Workbook relevance flags: 1 relevant of 3 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 9; grounding 7; overall 8. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** `scripts/ingest_repo.py` uses a chunk size of 60 lines (`CHUNK_SIZE = 60`) with an overlap size of 10 lines (`OVERLAP_SIZE = 10`).
- **Citations:** 1572, 1573. Workbook relevance flags: 1 relevant of 2 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 10; grounding 7; overall 9. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 7 vs 60/10 8 | Worse (minor) |
| Pass 2 | 100/20 9 vs 60/10 8 | Better (minor) |

#### Question-level conclusion

Answers are factually correct, but no citations in pass 1; pass 2 includes a relevant citation alongside irrelevant ones. Experiment pass 1 answers only chunk size, while baseline adds overlap (true but unasked); pass 2 experiment is the most complete. Minor 100/20 advantage overall, with grounding weakness across both.

### Question: direct-03
**Question:** Which Gemini embedding model is configured?
**Expected answer / authoritative reference:** scripts/embed_chunks.py: `models/gemini-embedding-001`. Pinned source line(s): `scripts/embed_chunks.py:25-26`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 9 | 7 | 8 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 9 | 7 | 8 |
| 100/20 — Pass 2 | 10 | 9 | 0 | 8 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** The configured Gemini embedding model is `"models/gemini-embedding-001"`, defined by the `GEMINI_MODEL` constant in `scripts/embed_chunks.py`.
- **Citations:** 1476, 1477, 1478. Workbook relevance flags: 1 relevant of 3 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 9; grounding 7; overall 8. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** The Gemini embedding model configured in `scripts/embed_chunks.py` is `models/gemini-embedding-001`.
- **Citations:** 1570, 1571. Workbook relevance flags: 1 relevant of 2 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** The configured Gemini embedding model is `"models/gemini-embedding-001"`, defined by the constant `GEMINI_MODEL` in `scripts/embed_chunks.py`.
- **Citations:** 1476, 1477, 1478. Workbook relevance flags: 1 relevant of 3 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 9; grounding 7; overall 8. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** The Gemini embedding model configured is `models/gemini-embedding-001` (also referenced in the CLI description as `gemini-gemini-embedding-001`).
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
- **Score rationale:** Correctness 10; completeness 9; grounding 0; overall 8. Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 10 vs 60/10 8 | Better (minor) |
| Pass 2 | 100/20 8 vs 60/10 8 | Same (equivalent) |

#### Question-level conclusion

All answers identify `models/gemini-embedding-001`. Experiment pass 1 has relevant evidence and is best grounded. Experiment pass 2 includes the odd CLI-description wording `gemini-gemini-embedding-001`; this describes a help string, not the configured model, and is unnecessary. Its lack of citations makes that pass weaker.

### Question: direct-06
**Question:** What is the high-confidence RRF calibration margin?
**Expected answer / authoritative reference:** app/investigation/confidence.py: `MIN_CLEAR_RRF_SCORE = 0.032`. Pinned source line(s): `app/investigation/confidence.py:5`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** The high-confidence RRF calibration margin is defined by `MIN_CLEAR_RRF_SCORE = 0.032` in `app/investigation/confidence.py`.
- **Citations:** 1449. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** The high-confidence RRF calibration margin is defined as `MIN_CLEAR_RRF_SCORE = 0.032` in `app/investigation/confidence.py`.
- **Citations:** 1552. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** The high-confidence RRF calibration margin is defined as `MIN_CLEAR_RRF_SCORE = 0.032` in `app/investigation/confidence.py`.
- **Citations:** 1449. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** The high-confidence RRF calibration margin is defined as `MIN_CLEAR_RRF_SCORE = 0.032` in `app/investigation/confidence.py`.
- **Citations:** 1552. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 10 vs 60/10 10 | Same (equivalent) |
| Pass 2 | 100/20 10 vs 60/10 10 | Same (equivalent) |

#### Question-level conclusion

All four answers correctly state `MIN_CLEAR_RRF_SCORE = 0.032` and cite the relevant confidence source. Equivalent performance.

### Question: direct-07
**Question:** Which MCP server class is instantiated?
**Expected answer / authoritative reference:** app/investigation/mcp_server.py: `server = FastMCP`. Pinned source line(s): `app/investigation/mcp_server.py:18`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 7 | 9 |
| 100/20 — Pass 1 | 10 | 10 | 7 | 9 |
| 60/10 — Pass 2 | 10 | 10 | 7 | 9 |
| 100/20 — Pass 2 | 10 | 10 | 0 | 9 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** The `FastMCP` class is instantiated to create the MCP server (`server = FastMCP("IncidentWeave local investigation tools")`).
- **Citations:** 1460, 1462. Workbook relevance flags: 1 relevant of 2 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 10; grounding 7; overall 9. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** The MCP server class instantiated is `FastMCP`.
- **Citations:** 1559, 1560. Workbook relevance flags: 1 relevant of 2 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 10; grounding 7; overall 9. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** The `FastMCP` class is instantiated to create the MCP server (`server = FastMCP("IncidentWeave local investigation tools")`).
- **Citations:** 1460, 1462. Workbook relevance flags: 1 relevant of 2 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 10; grounding 7; overall 9. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** The FastMCP class (`FastMCP`) is instantiated to create the MCP server instance (`server = FastMCP("IncidentWeave local investigation tools")`).
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
- **Score rationale:** Correctness 10; completeness 10; grounding 0; overall 9. Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 9 vs 60/10 9 | Same (equivalent) |
| Pass 2 | 100/20 9 vs 60/10 9 | Same (equivalent) |

#### Question-level conclusion

All four correctly identify `FastMCP`; relevant citation is present in each response, often with an irrelevant extra citation. Baseline adds the instantiation call, which is a small useful detail. Equivalent overall.

### Question: paraphrased-01
**Question:** How does the database layer establish non-blocking connections and create request-scoped objects?
**Expected answer / authoritative reference:** app/db/session.py: `create_async_engine`. Pinned source line(s): `app/db/session.py:21-23, 35-46`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 9 | 8 | 8 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 9 | 8 | 8 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** The database layer establishes non-blocking connections using SQLAlchemy's `create_async_engine` with a converted PostgreSQL URL (`postgresql+psycopg://`) and `pool_pre_ping=True`, while registering pgvector types asynchronously on connection events. It creates request-scoped objects (sessions) using an `async_sessionmaker` configured with `AsyncSession` and `expire_on_commit=False`, which are yielded as async generators via `get_db_session()`.
- **Citations:** 1447. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 9; grounding 8; overall 8. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** The database layer establishes non-blocking connections using SQLAlchemy's `create_async_engine` with a URL converted to the `psycopg` async dialect via `_async_database_url()` and `pool_pre_ping=True`. Additionally, `pgvector` types are registered for each async connection using an event listener on `engine.sync_engine` that calls `dbapi_connection.run_async(register_vector_async)`. Request-scoped objects (specifically asynchronous database sessions) are created using `async_sessionmaker` bound to the engine (`AsyncSessionLocal`), which are yielded as request-scoped sessions through the asynchronous generator function `get_db_session()`.
- **Citations:** 1550. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** The database layer establishes non-blocking connections by using SQLAlchemy's `create_async_engine` with a URL converted to the `postgresql+psycopg` async dialect (via `_async_database_url`) and `pool_pre_ping=True`. Request-scoped database sessions are created using `async_sessionmaker` bound to this engine (configured as `AsyncSessionLocal`), and the asynchronous generator `get_db_session` yields an `AsyncSession` context manager instance (`async with AsyncSessionLocal() as session:`).
- **Citations:** 1447. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 9; grounding 8; overall 8. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** The database layer establishes non-blocking connections using SQLAlchemy's `create_async_engine` with a URL converted to the psycopg async dialect (`postgresql+psycopg://`), along with `pool_pre_ping=True` and an event listener that registers pgvector types asynchronously via `dbapi_connection.run_async(register_vector_async)`. It creates request-scoped objects (specifically asynchronous database sessions) using an `async_sessionmaker` named `AsyncSessionLocal` bound to the engine, with `expire_on_commit=False`, which are yielded as an `AsyncSession` via the `get_db_session()` asynchronous generator function using an `async with` context manager.
- **Citations:** 1550. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 10 vs 60/10 8 | Better (minor) |
| Pass 2 | 100/20 10 vs 60/10 8 | Better (minor) |

#### Question-level conclusion

100/20 is better in both passes: it explains async engine creation, session factory, and request-scoped session yielding, with relevant evidence. Baseline is generally correct but less complete or weaker in citation support.

### Question: paraphrased-02
**Question:** How are source files divided into overlapping pieces for indexing?
**Expected answer / authoritative reference:** scripts/ingest_repo.py: `OVERLAP_SIZE = 10`. Pinned source line(s): `scripts/ingest_repo.py:22-23, 49-66`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 9 | 7 | 9 |
| 100/20 — Pass 1 | 10 | 9 | 7 | 9 |
| 60/10 — Pass 2 | 10 | 9 | 7 | 9 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** Source files are divided into overlapping pieces for indexing using the `chunk_lines` function in `scripts/ingest_repo.py`. This function takes a list of lines, a `chunk_size` (defaulting to 60), and an `overlap` size (defaulting to 10). It calculates a step size (`chunk_size - overlap`) and iterates through the lines using `range(0, len(lines), step)` to yield overlapping start and end index windows for each chunk, provided that each new window adds at least one new line beyond the prior window (`end_index > previous_end`).
- **Citations:** 1480, 1479, 1481. Workbook relevance flags: 1 relevant of 3 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 9; grounding 7; overall 9. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** Source files are divided into overlapping pieces for indexing using the `chunk_lines` function defined in `scripts/ingest_repo.py`.  - By default, files are split into windows using a `CHUNK_SIZE` of 60 lines and an `OVERLAP_SIZE` of 10 lines. - The step size between windows is calculated as `chunk_size - overlap` (which defaults to 50 lines). - Windows are yielded starting at index 0 up to the total number of lines, ensuring that each new window adds at least one new line beyond the prior window (`end_index > previous_end`).  - Empty chunk contents or non-redundant windows where `end_index <= previous_end` are skipped.
- **Citations:** 1572, 1573. Workbook relevance flags: 1 relevant of 2 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 9; grounding 7; overall 9. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** Source files are divided into overlapping pieces for indexing using the `chunk_lines` function in `scripts/ingest_repo.py`. It uses a default `CHUNK_SIZE` of 60 and an `OVERLAP_SIZE` of 10 to calculate a step size (`chunk_size - overlap`), then loops through the file's lines from `0` to `len(lines)` with that step size to yield non-redundant overlapping windows defined by `(start_index, end_index)`.
- **Citations:** 1480, 1479, 1481. Workbook relevance flags: 1 relevant of 3 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 9; grounding 7; overall 9. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** Source files (specifically Python files) are divided into overlapping pieces for indexing using the `chunk_lines` function defined in `scripts/ingest_repo.py`.   The segmentation process works as follows: - It uses a defined `CHUNK_SIZE` of 60 lines and an `OVERLAP_SIZE` of 10 lines. - The step size between windows is calculated as `step = chunk_size - overlap` (which defaults to 50 lines). - Windows are yielded over the file's lines using `range(0, len(lines), step)`, where each window spans from `start_index` to `min(start_index + chunk_size, len(lines))`. - Windows are only yielded (and `previous_end` is updated) when they add at least one new line beyond the prior window (`end_index > previous_end`), preventing redundant or non-advancing windows. - Empty chunk contents are filtered out during ingestion before creating `Chunk` records.
- **Citations:** 1572, 1584, 1573. Workbook relevance flags: 1 relevant of 3 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 9 vs 60/10 9 | Same (equivalent) |
| Pass 2 | 100/20 10 vs 60/10 9 | Better (minor) |

#### Question-level conclusion

Both strategies correctly explain sliding windows and overlap. Experiment pass 2 is more complete and has a relevant chunk citation; longer explanation is useful here because it explains the step and boundary behavior. Some irrelevant extra citations remain.

### Question: paraphrased-04
**Question:** How are two independent search rankings combined into one ordered result?
**Expected answer / authoritative reference:** app/retrieval/hybrid_search.py: `rrf_score += 1 / (60 +`. Pinned source line(s): `app/retrieval/hybrid_search.py:9-70`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 9 | 7 | 8 |
| 100/20 — Pass 1 | 9 | 8 | 0 | 7 |
| 60/10 — Pass 2 | 10 | 9 | 7 | 9 |
| 100/20 — Pass 2 | 9 | 8 | 0 | 7 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** Two independent search rankings (vector search results and full-text search results) are combined into one ordered result using reciprocal rank fusion (RRF) in the `hybrid_search` function (`app/retrieval/hybrid_search.py`).   The combination process works as follows: 1. Vector search and full-text search are performed independently to retrieve result lists up to the specified limit. 2. The ranks for each result ID in the vector and full-text search results are determined (where rank is index + 1). 3. The union of candidate IDs from both search methods is collected. 4. For each candidate ID, an `rrf_score` is computed by summing reciprocal rank terms: $1 / (60 + \text{vector\_rank})$ (if present in vector results) and $1 / (60 + \text{fts\_rank})$ (if present in FTS results). 5. The combined results are sorted in descending order based on their `rrf_score`, and the top results up to the limit are returned.
- **Citations:** 1473, 1494, 1472. Workbook relevance flags: 1 relevant of 3 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 9; grounding 7; overall 8. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** Two independent search rankings (vector search and full-text search) are combined into one ordered result using Reciprocal Rank Fusion (RRF) in the `hybrid_search` function. Specifically, it computes ranks from the `vector_results` and `fts_results` lists (using 1-based indexing), aggregates candidate chunk IDs, calculates an `rrf_score` for each candidate by summing $1 / (60 + \text{rank})$ for each search method where the chunk appears, sorts the fused results in descending order by `rrf_score`, and returns up to the specified `limit`.
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
- **Score rationale:** Correctness 9; completeness 8; grounding 0; overall 7. Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** Two independent search rankings (vector search and full-text search) are combined into one ordered result using reciprocal rank fusion (RRF). Specifically: 1. The `hybrid_search` function performs both a vector search (`search_vector`) and a full-text search (`search_fulltext`). 2. It maps the results of each search to determine the rank (starting from 1) of each chunk ID in both lists (`vector_rank_by_id` and `fts_rank_by_id`). 3. It collects all unique candidate chunk IDs from both searches and calculates an `rrf_score` for each candidate by summing $1 / (60 + \text{rank})$ for whichever ranking lists contain that chunk ID. 4. Finally, the fused results are sorted in descending order based on their `rrf_score` and truncated to the specified `limit`.
- **Citations:** 1473, 1494, 1472. Workbook relevance flags: 1 relevant of 3 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 9; grounding 7; overall 9. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** Two independent search rankings (vector search and full-text search) are combined into one ordered result using Reciprocal Rank Fusion (RRF) in the `hybrid_search` function. Specifically, it retrieves results from `search_vector` and `search_fulltext`, computes each result's rank (1-indexed) within each list, and calculates an `rrf_score` for each candidate chunk ID by summing $1 / (60 + \text{rank})$ for whichever ranking systems returned that chunk. Finally, the combined results are sorted in descending order by their `rrf_score` and sliced to the specified `limit`.
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.
- **Score rationale:** Correctness 9; completeness 8; grounding 0; overall 7. Substantive gist is assessed against pinned source. No citations were supplied, so grounding is weak even where the factual claim is correct.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 7 vs 60/10 8 | Worse (minor) |
| Pass 2 | 100/20 7 vs 60/10 9 | Worse (minor) |

#### Question-level conclusion

Mixed result. Baseline pass 1 and pass 2 cite a relevant RRF chunk and accurately explain fusion; experiment pass 1 has no citations, and experiment pass 2 also lacks citations. 100/20 does not improve end-to-end grounding on this item despite correct content.

### Question: paraphrased-06
**Question:** How is a model's certainty adjusted when the supporting search evidence is borderline?
**Expected answer / authoritative reference:** app/investigation/confidence.py: `return "medium"`. Pinned source line(s): `app/investigation/confidence.py:5-36`. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** When a model's reported confidence is "high" and the supporting search evidence is borderline (such as when the best RRF score is below the clear threshold `MIN_CLEAR_RRF_SCORE` of 0.032, or the best vector distance is above the clear threshold `MAX_CLEAR_VECTOR_DISTANCE` of 0.4), the confidence rating is downgraded to "medium". If the normalized confidence is not "high", it is retained without downgrade.
- **Citations:** 1449, 1498. Workbook relevance flags: 1 relevant of 2 listed, where flags are present.
- **Assessment:** Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Core claim is supported by at least one relevant cited chunk, but extra citations are irrelevant and add noise. Any extra implementation detail is only credited where checked against the pinned source.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** When a model's reported confidence is "high" and the supporting search evidence is borderline—specifically if the best RRF score is below `MIN_CLEAR_RRF_SCORE` (0.032) or the best vector distance is above `MAX_CLEAR_VECTOR_DISTANCE` (0.4)—the confidence rating is downgraded to "medium". If the normalized confidence is anything other than "high", it is retained without calibration downgrade.
- **Citations:** 1552. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** When a model's reported confidence is "high" and the supporting search evidence is borderline (specifically, when the best RRF score is below `MIN_CLEAR_RRF_SCORE` of `0.032` or the best vector distance is above `MAX_CLEAR_VECTOR_DISTANCE` of `0.4`), the `calibrate_confidence` function downgrades the confidence rating from "high" to "medium" and appends the specific threshold violation reasons to a note. If the reported confidence is anything other than "high", it is retained without calibration.
- **Citations:** 1449. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** When the supporting search evidence is borderline (such as when the best RRF score is below the clear margin threshold of `0.032` or the best vector distance is above the clear threshold of `0.4`), a high model confidence rating is downgraded to "medium" by `calibrate_confidence`. If the reported confidence is not "high", it is retained without being downgraded.
- **Citations:** 1552. Workbook relevance flags: 1 relevant of 1 listed, where flags are present.
- **Assessment:** Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.
- **Score rationale:** Correctness 10; completeness 10; grounding 10; overall 10. Claim is supported by relevant cited evidence and matches the pinned implementation; no material factual defect identified.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 10 vs 60/10 10 | Same (equivalent) |
| Pass 2 | 100/20 10 vs 60/10 10 | Same (equivalent) |

#### Question-level conclusion

All answers correctly explain high confidence is downgraded to medium when RRF or vector-distance margins are not clear. All have relevant citations. The 100/20 pass 2 is slightly more explicit about the calibration note, but the difference is immaterial.

### Question: unanswerable_far-01
**Question:** How do I bake sourdough bread at high altitude?
**Expected answer / authoritative reference:** No labeled source (unanswerable question).. Pinned source line(s): no single source line; benchmark marks this prompt unanswerable. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 10 vs 60/10 10 | Same (equivalent) |
| Pass 2 | 100/20 10 vs 60/10 10 | Same (equivalent) |

#### Question-level conclusion

Both strategies produce correct abstentions on this unanswerable prompt. No quality difference is visible in the saved answer; retrieval and latency differences are outside this answer-quality verdict.

### Question: unanswerable_far-02
**Question:** Which telescope can observe the rings of Saturn?
**Expected answer / authoritative reference:** No labeled source (unanswerable question).. Pinned source line(s): no single source line; benchmark marks this prompt unanswerable. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 10 vs 60/10 10 | Same (equivalent) |
| Pass 2 | 100/20 10 vs 60/10 10 | Same (equivalent) |

#### Question-level conclusion

Both strategies produce correct abstentions on this unanswerable prompt. No quality difference is visible in the saved answer; retrieval and latency differences are outside this answer-quality verdict.

### Question: unanswerable_far-03
**Question:** How should a wooden canoe be repaired?
**Expected answer / authoritative reference:** No labeled source (unanswerable question).. Pinned source line(s): no single source line; benchmark marks this prompt unanswerable. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 10 vs 60/10 10 | Same (equivalent) |
| Pass 2 | 100/20 10 vs 60/10 10 | Same (equivalent) |

#### Question-level conclusion

Both strategies produce correct abstentions on this unanswerable prompt. No quality difference is visible in the saved answer; retrieval and latency differences are outside this answer-quality verdict.

### Question: unanswerable_far-04
**Question:** Why do coral reefs bleach during marine heatwaves?
**Expected answer / authoritative reference:** No labeled source (unanswerable question).. Pinned source line(s): no single source line; benchmark marks this prompt unanswerable. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 10 vs 60/10 10 | Same (equivalent) |
| Pass 2 | 100/20 10 vs 60/10 10 | Same (equivalent) |

#### Question-level conclusion

Both strategies produce correct abstentions on this unanswerable prompt. No quality difference is visible in the saved answer; retrieval and latency differences are outside this answer-quality verdict.

### Question: unanswerable_near-01
**Question:** How is Redis configured for this application?
**Expected answer / authoritative reference:** No labeled source (unanswerable question).. Pinned source line(s): no single source line; benchmark marks this prompt unanswerable. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** 1439, 1506, 1507, 1440, 1492. Workbook relevance flags: 0 relevant of 5 listed, where flags are present.
- **Assessment:** Correct abstention; workbook shows no generated answer and no source-backed claim. Retrieved/cited IDs are not needed to answer and do not establish topic support.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct abstention; workbook shows no generated answer and no source-backed claim. Retrieved/cited IDs are not needed to answer and do not establish topic support.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 10 vs 60/10 10 | Same (equivalent) |
| Pass 2 | 100/20 10 vs 60/10 10 | Same (equivalent) |

#### Question-level conclusion

Both strategies produce correct abstentions on this unanswerable prompt. No quality difference is visible in the saved answer; retrieval and latency differences are outside this answer-quality verdict.

### Question: unanswerable_near-02
**Question:** How does the message queue retry failed jobs?
**Expected answer / authoritative reference:** No labeled source (unanswerable question).. Pinned source line(s): no single source line; benchmark marks this prompt unanswerable. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 10 vs 60/10 10 | Same (equivalent) |
| Pass 2 | 100/20 10 vs 60/10 10 | Same (equivalent) |

#### Question-level conclusion

Both strategies produce correct abstentions on this unanswerable prompt. No quality difference is visible in the saved answer; retrieval and latency differences are outside this answer-quality verdict.

### Question: unanswerable_near-03
**Question:** Where is user login and authentication implemented?
**Expected answer / authoritative reference:** No labeled source (unanswerable question).. Pinned source line(s): no single source line; benchmark marks this prompt unanswerable. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 10 vs 60/10 10 | Same (equivalent) |
| Pass 2 | 100/20 10 vs 60/10 10 | Same (equivalent) |

#### Question-level conclusion

Both strategies produce correct abstentions on this unanswerable prompt. No quality difference is visible in the saved answer; retrieval and latency differences are outside this answer-quality verdict.

### Question: unanswerable_near-04
**Question:** Which Kubernetes deployment target does this service use?
**Expected answer / authoritative reference:** No labeled source (unanswerable question).. Pinned source line(s): no single source line; benchmark marks this prompt unanswerable. The named lines were fetched from the pinned commit.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 1**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**60/10 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
**100/20 — Pass 2**
- **Answer (faithful gist / saved answer):** INSUFFICIENT_EVIDENCE
- **Citations:** none. Workbook relevance flags: 0 relevant of 0 listed, where flags are present.
- **Assessment:** Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.
- **Score rationale:** Correctness 10; completeness n/a; grounding 10; overall 10. Correct `INSUFFICIENT_EVIDENCE` abstention; no answer claims or citations. Topic treated as absent from this repository corpus; repository-wide absence search is a limitation noted below.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 10 vs 60/10 10 | Same (equivalent) |
| Pass 2 | 100/20 10 vs 60/10 10 | Same (equivalent) |

#### Question-level conclusion

Both strategies produce correct abstentions on this unanswerable prompt. No quality difference is visible in the saved answer; retrieval and latency differences are outside this answer-quality verdict.

## Final report

### 1. Summary table

| Question | Pass 1 verdict | Pass 2 verdict | Main reason |
|---|---|---|---|
| direct-04 | Better | Better | 100/20 is better in both passes: it includes the threshold value and cites the guard chunk. The confidence-calibration detail is true but not required and its citation is not primary evidence for the asked constant. Baseline pass 2 loses grounding by omitting citations. |
| direct-05 | Worse | Same | Pass 1 is effectively close: baseline gives the value and experiment gives only the symbol, so baseline is more complete; experiment has the cleaner single relevant citation. Pass 2 is approximately equivalent, with the baseline naming the file/value and experiment naming the value but still citing the relevant chunk. |
| direct-08 | Better | Better | Clear improvement in both passes: baseline abstains on an answerable question, while 100/20 retrieves the persistence call and answers it. Pass-1 experiment cites one relevant chunk plus one irrelevant chunk; pass 2 cites the relevant chunk only. |
| paraphrased-03 | Better | Better | 100/20 is better in both passes because it retrieves and cites the embedding implementation. Baseline answers are technically accurate but cite only chunks marked irrelevant; pass 2 also adds a VECTOR(768) storage claim not directly grounded by its citations. |
| paraphrased-05 | Better | Better | 100/20 is better in both passes because it cites the guard chunk and describes the thresholds/routing more specifically. Grounding remains imperfect: the answer describes graph routing/retry/fallback, but the citations are mostly irrelevant and do not fully evidence all graph-level claims. |
| paraphrased-08 | Better | Better | 100/20 is better in both passes. Baseline pass 1 abstains; baseline pass 2 discusses persistence generally but does not clearly name the `Audit` record asked for. Experiment names the Audit record and enumerates stored fields, but both experiment answers lack citations. |
| paraphrased-07 | Same | Same | No decisive strategy winner. All four answers identify literal grep search accurately, but the cited chunks are absent or marked irrelevant. The main weakness is evidence grounding, not the core answer. Exact-phrase semantics are slightly broader than simple case-insensitive substring matching. |
| direct-01 | Worse | Worse | Both strategies answer correctly with relevant citations. Baseline is concise and fully answers the question; experiment adds accurate engine/URL/pgvector details but they are not needed. Slight preference for baseline concision, not a material quality difference. |
| direct-02 | Worse | Better | Answers are factually correct, but no citations in pass 1; pass 2 includes a relevant citation alongside irrelevant ones. Experiment pass 1 answers only chunk size, while baseline adds overlap (true but unasked); pass 2 experiment is the most complete. Minor 100/20 advantage overall, with grounding weakness across both. |
| direct-03 | Better | Same | All answers identify `models/gemini-embedding-001`. Experiment pass 1 has relevant evidence and is best grounded. Experiment pass 2 includes the odd CLI-description wording `gemini-gemini-embedding-001`; this describes a help string, not the configured model, and is unnecessary. Its lack of citations makes that pass weaker. |
| direct-06 | Same | Same | All four answers correctly state `MIN_CLEAR_RRF_SCORE = 0.032` and cite the relevant confidence source. Equivalent performance. |
| direct-07 | Same | Same | All four correctly identify `FastMCP`; relevant citation is present in each response, often with an irrelevant extra citation. Baseline adds the instantiation call, which is a small useful detail. Equivalent overall. |
| paraphrased-01 | Better | Better | 100/20 is better in both passes: it explains async engine creation, session factory, and request-scoped session yielding, with relevant evidence. Baseline is generally correct but less complete or weaker in citation support. |
| paraphrased-02 | Same | Better | Both strategies correctly explain sliding windows and overlap. Experiment pass 2 is more complete and has a relevant chunk citation; longer explanation is useful here because it explains the step and boundary behavior. Some irrelevant extra citations remain. |
| paraphrased-04 | Worse | Worse | Mixed result. Baseline pass 1 and pass 2 cite a relevant RRF chunk and accurately explain fusion; experiment pass 1 has no citations, and experiment pass 2 also lacks citations. 100/20 does not improve end-to-end grounding on this item despite correct content. |
| paraphrased-06 | Same | Same | All answers correctly explain high confidence is downgraded to medium when RRF or vector-distance margins are not clear. All have relevant citations. The 100/20 pass 2 is slightly more explicit about the calibration note, but the difference is immaterial. |
| unanswerable_far-01 | Same | Same | Correct abstention on an unanswerable prompt; no answer-quality difference. |
| unanswerable_far-02 | Same | Same | Correct abstention on an unanswerable prompt; no answer-quality difference. |
| unanswerable_far-03 | Same | Same | Correct abstention on an unanswerable prompt; no answer-quality difference. |
| unanswerable_far-04 | Same | Same | Correct abstention on an unanswerable prompt; no answer-quality difference. |
| unanswerable_near-01 | Same | Same | Correct abstention on an unanswerable prompt; no answer-quality difference. |
| unanswerable_near-02 | Same | Same | Correct abstention on an unanswerable prompt; no answer-quality difference. |
| unanswerable_near-03 | Same | Same | Correct abstention on an unanswerable prompt; no answer-quality difference. |
| unanswerable_near-04 | Same | Same | Correct abstention on an unanswerable prompt; no answer-quality difference. |

### 2. Verdict counts — Pass 1

- All 24 questions (including the eight designated unanswerable prompts, which are Same because both arms abstain): {'Better': 7, 'Same': 13, 'Worse': 4, 'Uncertain': 0}.
- 16 answerable questions only: {'Better': 7, 'Same': 5, 'Worse': 4, 'Uncertain': 0}.

### 2. Verdict counts — Pass 2

- All 24 questions (including the eight designated unanswerable prompts, which are Same because both arms abstain): {'Better': 8, 'Same': 14, 'Worse': 2, 'Uncertain': 0}.
- 16 answerable questions only: {'Better': 8, 'Same': 6, 'Worse': 2, 'Uncertain': 0}.

### 3. Mean scores on the 16 answerable questions (descriptive only)

| Response set | Mean correctness | Mean completeness | Mean grounding | Mean overall |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 9.85 | 7.50 | 5.62 | 7.31 |
| 100/20 — Pass 1 | 9.73 | 8.56 | 5.94 | 8.25 |
| 60/10 — Pass 2 | 9.64 | 7.94 | 5.88 | 7.50 |
| 100/20 — Pass 2 | 9.80 | 8.81 | 6.06 | 8.50 |

### 4. Important correctness regressions, grounding weaknesses, completeness improvements

- **No clear source-factual regression in the answerable set** was identified from the pinned files and saved answer text, but absence of a discovered regression is not proof that every detail in every long answer is fully verified.
- **Clear answerability failures:** `direct-08` and `paraphrased-08` baseline pass 1 abstain on answerable questions. `direct-08` baseline pass 2 also abstains. `paraphrased-08` baseline pass 2 describes persistence but does not directly identify the `Audit` record.
- **Grounding weakness:** `direct-02` pass 1 has no citations in either arm; `direct-04` baseline pass 2 has no citations; `direct-03` experiment pass 2 has no citations; `paraphrased-03` baseline citations are marked irrelevant; `paraphrased-04` experiment answers have no citations; `paraphrased-07` answers have citations absent or marked irrelevant; `paraphrased-08` experiment answers are uncited.
- **Irrelevant citation clutter:** several answers include multiple IDs when only one chunk is relevant, notably `direct-04`, `direct-05`, `direct-07`, `paraphrased-02`, and `paraphrased-05`. More citations are not automatically better.
- **Completeness improvements:** 100/20 improves the answerable baseline on `direct-08`, `paraphrased-03`, `paraphrased-05`, `paraphrased-08`, `paraphrased-01`, and `paraphrased-02` in this scoring. These are human judgments of the saved answer, not the automated labels.

### 5. Citation behaviour

- **60/10 — Pass 1:** 1 non-abstaining answerable responses with no citations; 3 abstentions; 12 non-abstaining answerable responses with at least one citation.
- **100/20 — Pass 1:** 4 non-abstaining answerable responses with no citations; 1 abstentions; 11 non-abstaining answerable responses with at least one citation.
- **60/10 — Pass 2:** 1 non-abstaining answerable responses with no citations; 2 abstentions; 13 non-abstaining answerable responses with at least one citation.
- **100/20 — Pass 2:** 4 non-abstaining answerable responses with no citations; 1 abstentions; 11 non-abstaining answerable responses with at least one citation.

Counting rule: only the 16 answerable questions are included in these citation counts. A response with `INSUFFICIENT_EVIDENCE` is counted separately as an abstention, not as an uncited substantive answer. Citation IDs listed in the workbook are counted as citations even when the relevance flag says they are irrelevant. The pattern is mixed: the experiment improves citation support on some cases, but still produces uncited correct answers, while the baseline has uncited responses and some irrelevant citations too.

### 6. Questions where the two passes disagree

- `direct-04`: baseline overall falls from 8 to 7 because pass 2 drops citations; experiment remains 9.
- `direct-02`: experiment improves from 7 to 9 as pass 2 includes overlap detail and relevant evidence; baseline remains 8.
- `direct-03`: experiment pass 2 is weaker than pass 1 because it has no citations and adds odd CLI-description wording.
- `paraphrased-04`: baseline improves from 8 to 9 in pass 2 due to relevant citations; experiment falls from 7 to 7 and remains uncited.
- `paraphrased-08`: baseline pass 2 improves from abstention to a partial answer, while experiment stays a more complete but uncited answer.
- `paraphrased-07`: no overall score difference between passes or arms, but citation quality is poor throughout.
- All eight unanswerable prompts remain correct abstentions in both passes; any retrieval/routing/latency variation does not change the answer-quality verdict.

### 7. Limitations

- The raw JSONs were not inspected, so saved metadata and exact answer strings are taken from the workbook. I did not rerun the experiment or regenerate responses.
- The required experiment log entry [004] could not be fetched at `docs/chunking-experiment.md` at the pinned commit (404). I did not substitute a similarly named local artifact or decision report.
- Source files were fetched at the pinned commit for the named implementation paths. The workbook’s source spans and citation relevance flags were used to connect each answer to retrieved evidence. I did not re-open every cited chunk body independently for every response; consequently, some grounding judgments remain limited to the workbook’s span/metadata rather than full independent inspection of every cited text block.
- I inspected the recursive tree at the pinned commit and the relevant implementation/source files, but did not fetch and search every blob body to prove that each unanswerable topic is absent. The workbook labels those prompts as unanswerable; the abstention quality judgment is conditional on that benchmark designation.
- The scoring is independent human-like judgment but still one reviewer’s judgment. The scoring scale is coarse and there is no adjudication yet.

### 8. Concise Gate 5 assessment

**Preliminary independent assessment: inconclusive for adoption; positive evidence for some answerable cases, but no basis to approve 100/20 for production.** In this 24-question saved set, 100/20 improves several answerable responses, especially where the baseline abstains, and it often retrieves a more useful chunk. However, grounding is still inconsistent: several answers have no citations or citations marked irrelevant, and some questions show no improvement or a pass-to-pass decline. All eight designated unanswerable questions abstain under both strategies, so they do not distinguish answer quality here.

Keep retrieval effectiveness separate: the workbook’s reported retrieval ranking metrics may indicate a retrieval advantage, but improved retrieval is not the same as improved end-to-end answer correctness, citation grounding, or abstention calibration. Gate 5’s criterion is human-reviewed end-to-end correctness not lower; this review alone does not establish that across the full set with sufficient certainty, and it cannot authorize a production change. **60/10 remains production until human review is complete and a maintainer separately approves any change.**

### 9. Unresolved issues

- Complete independent inspection of every cited chunk body and every pinned source line that supports long multi-claim answers.
- Resolve whether `paraphrased-07` should be evaluated as answerable under literal-substring search semantics; the source performs case-insensitive substring matching, which is not identical to every interpretation of an “exact phrase.”
- Decide how to treat citations that point to retrieved chunks but do not support the claims, and whether citation validity should be a hard gate rather than just a score dimension.
- Confirm the pinned experiment log entry [004] path/content with the maintainer.
- Human maintainer review and explicit adoption approval remain required.

## Methodology critique

### Overall assessment

The rubric is understandable but not fully reproducible as currently phrased. Correctness/completeness/grounding are distinct in principle, but “overall” can vary between reviewers without anchor examples. Citation IDs and retrieval rank metadata are useful pointers, but they do not replace reading the actual cited chunk. Two passes help reveal generation variability, yet they are not independent experimental replicates if both use the same retrieved context and same code/configuration.

### Essential changes proposed for approval

| Proposal | Benefit | Cost |
|---|---|---|
| Require a source-evidence note for every factual claim, with exact pinned file and line range; cite the actual source text, not just chunk ID. | Makes grounding auditable and reduces “citation present = grounded” errors. | More review time; long answers require claim-by-claim notes.
| Add explicit score anchors for 0, 2, 5, 7, 8, and 10 for each dimension, including a rule for partially correct multi-claim answers. | Improves inter-reviewer consistency. | Requires rubric revision and reviewer calibration.
| Separate answerability/abstention correctness from answer correctness; record “abstention appropriate?” as its own binary or 0–10 field. | Prevents a good abstention on an unanswerable prompt from being conflated with a complete answer, and exposes wrong abstentions on answerable prompts. | Adds one field per response and slightly more work.
| Require independent review of cited chunk body and pinned source body before assigning Grounding above 6. | Makes grounding score defensible. | Slower; may require opening many chunks and source spans.
| Publish deterministic aggregation rules before reviews begin (per-pass comparison, question-level summary, answerable-only averages, and treatment of ties). | Reduces post-hoc choice of the preferred summary metric. | Requires agreement before interpreting totals.
| Confirm the full pinned corpus and benchmark file paths, including the experiment log entry, before review begins. | Avoids ambiguity about what constitutes authoritative context. | Small setup overhead; maintainer must attach or identify the missing log.

### Optional changes

| Proposal | Benefit | Cost |
|---|---|---|
| Add a “material unsupported extra claim” flag. | Captures answers that answer the main question correctly but add unrequested unsupported details. | Additional reviewer judgment and reporting complexity.
| Add token/context cost and latency as a separate trade-off table, not inside answer quality. | Preserves efficiency trade-offs without rewarding verbosity. | Requires maintaining an additional metrics summary.
| Randomize response labels during scoring (A/B/C/D) and reveal the strategy after scoring. | Reduces anchoring toward the expected experiment winner. | Makes reviewer workflow slightly less convenient.
| Include more paraphrase families and a larger question set in a later evaluation. | Improves coverage and reduces overfitting to 24 prompts. | More benchmark authoring and review effort; outside this Gate 5 scope.
| Ask a second human reviewer to adjudicate disagreements greater than two overall points. | Targets scarce adjudication effort where it matters most. | Requires additional reviewer time.

These are proposals only; none changes the agreed Gate 5 method or project architecture in this review.
