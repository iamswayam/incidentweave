# Gate 5 Review — Claude (independent reviewer)

**Status:** Review complete. **This is an AI reviewer's input to Gate 5, not the Gate 5 verdict.** D4 requires human-reviewed end-to-end correctness; the maintainer decides. Production remains 60/10. This file changes no code, configuration, chunking setting, or evaluation artifact.

**Reviewer:** Claude (Sonnet 5.5), planner role.
**Date:** 2026-10-19.
**Companion files:** [`chunking-human-review-workbook.md`](./chunking-human-review-workbook.md) (saved answers, by question anchor), [`chunking-strategy-decision-report.md`](./chunking-strategy-decision-report.md).

## 0. Independence disclosure, method and limits

- **Prior opinion.** Before this review I told the maintainer, from the decision report alone, that the automated `direct-05` pass-1 "regression" looked like a scoring artifact. I scored every response afresh and report where that held (it did) and where my expectation did not (the citation pattern in section 4, which I had not anticipated).
- **What I inspected.** (1) The workbook's saved answers, cited IDs, and top-five spans for all 24 questions × 4 responses = 96 instances. (2) The **actual source at pinned commit `62d0e58593bb22d187ec7930274b0457afd3be74`**, read from the public repo: `app/investigation/guard.py`, `confidence.py`, `persistence.py`, `graph.py`, `mcp_server.py`, `app/db/session.py`, `app/db/models/audit.py`, `app/retrieval/hybrid_search.py`, `scripts/embed_chunks.py`, `ingest_repo.py`, `investigate.py`, `tests/unit/test_investigation_persistence.py`. Every factual claim below marked "verified" was checked against those files by line number.
- **What I did not inspect.** The raw run JSON files (local/git-ignored). The bodies of individual retrieved chunks in the workbook's evidence library: I judged grounding from each chunk's file path and line span against the pinned source (a chunk spanning lines N-M contains those lines). I did not rerun anything.
- **Not used as evidence:** `outcome_v2`, keyword screens, the decision report's verdicts, or other reviewers' conclusions.
- **Answers are condensed.** The "Answer (gist)" lines preserve meaning, not wording. The verbatim text is in the workbook under the matching question anchor.

### Scoring conventions (so this can be reproduced)

| Score | Meaning |
|---|---|
| 10 | Fully correct / complete / supported; nothing material missing |
| 8-9 | Correct, with a minor omission, loose wording, or one uncited or off-topic point |
| 6-7 | Correct but thin, or noticeably under-supported |
| 3-5 | Partly wrong, misleading, or largely unsupported |
| 0-2 | Wrong, or no answer when the evidence supported one |

- **Correctness** judges claims against the pinned source. **Completeness** judges whether the question as asked is fully answered; unrequested values are a small plus but not required. **Grounding** judges whether claims are supported by retrieved evidence *and* whether citations exist and point at supporting chunks. **Overall** is a judgement, not an average.
- **"—"** means correctness is not meaningful because the response abstained (no claims). An abstention on an answerable question gets Completeness 0 and Overall 2. A correct abstention on an unanswerable question gets 10s; Completeness is n/a.
- **Verdict rule (applied mechanically):** compare Overall for the same pass. Higher for 100/20 = Better, lower = Worse, equal = Same. Magnitude: 0 = effectively equivalent, 1-2 = minor, 3 or more = clear. "Uncertain" is used only when evidence cannot decide; none were needed.

---

## 1. Priority questions first

Order: `direct-04`, `direct-05`, `direct-08`, `paraphrased-03`, `paraphrased-05`, `paraphrased-08`, `paraphrased-07`, then the rest in established order.

### Question: direct-04

**Question:** What constant controls the minimum RRF score?

**Expected answer / authoritative reference:** `app/investigation/guard.py` line 7 `MIN_ACCEPTABLE_RRF_SCORE = 0.016`.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 8 | 9 | 8 |
| 100/20 — Pass 1 | 10 | 10 | 9 | 9 |
| 60/10 — Pass 2 | 10 | 8 | 6 | 7 |
| 100/20 — Pass 2 | 10 | 10 | 9 | 9 |

**60/10 — Pass 1**
- Answer (gist): `MIN_ACCEPTABLE_RRF_SCORE`. No value given.
- Citations: 1458 (`guard.py:1-60`), 1459 (`guard.py:51-70`)
- Assessment: Correct and answers the question as asked. Omits the value 0.016. 1458 supports it; 1459 is not relevant.
- Scores: correctness 10, completeness 8, grounding 9, overall 8. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): `MIN_ACCEPTABLE_RRF_SCORE` (0.016, guard.py), plus `MIN_CLEAR_RRF_SCORE` (0.032, confidence.py) for calibration.
- Citations: 1558 (`guard.py:1-70`), 1552 (`confidence.py:1-38`)
- Assessment: Both values verified (guard.py line 7, confidence.py line 5). The 0.032 addition is true and correctly labelled but not asked for (-1 overall).
- Scores: correctness 10, completeness 10, grounding 9, overall 9. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): `MIN_ACCEPTABLE_RRF_SCORE`. No value.
- Citations: none (no citations)
- Assessment: Correct, uncited, no value. 1458 was rank 1 in the retrieved context, so support existed.
- Scores: correctness 10, completeness 8, grounding 6, overall 7. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): Same as experiment pass 1.
- Citations: 1558, 1552
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 9, overall 9. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Better** (Minor improvement) |
| Pass 2 | 100/20 against 60/10 | **Better** (Minor improvement) |

#### Question-level conclusion

The automated screen flagged the baseline as wrong only because it omitted 0.016. A human would call the baseline correct but thinner. The 100/20 answers are more complete and cited, at the cost of an unrequested second constant.

---

### Question: direct-05

**Question:** What constant controls the maximum vector distance?

**Expected answer / authoritative reference:** `app/investigation/guard.py` line 8 `MAX_ACCEPTABLE_VECTOR_DISTANCE = 0.5`.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 9 | 9 |
| 100/20 — Pass 1 | 10 | 9 | 10 | 9 |
| 60/10 — Pass 2 | 10 | 10 | 9 | 9 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

**60/10 — Pass 1**
- Answer (gist): `MAX_ACCEPTABLE_VECTOR_DISTANCE` (set to 0.5).
- Citations: 1458, 1459
- Assessment: Correct with value. 1459 not relevant.
- Scores: correctness 10, completeness 10, grounding 9, overall 9. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): `MAX_ACCEPTABLE_VECTOR_DISTANCE` controls the maximum vector distance.
- Citations: 1558
- Assessment: Correct and complete for the question asked. Omits the value 0.5, which the question does not request. Cites only the relevant chunk.
- Scores: correctness 10, completeness 9, grounding 10, overall 9. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): `MAX_ACCEPTABLE_VECTOR_DISTANCE`, 0.5, in guard.py.
- Citations: 1458, 1459
- Assessment: Correct.
- Scores: correctness 10, completeness 10, grounding 9, overall 9. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): `MAX_ACCEPTABLE_VECTOR_DISTANCE` (set to 0.5).
- Citations: 1558
- Assessment: Correct, with value and a single relevant citation.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Better** (Minor improvement) |

#### Question-level conclusion

The automated pass-1 "regression" is not confirmed. The 100/20 answer names the right constant; it only omits an unrequested value, and it cites more cleanly than the baseline. I rate pass 1 equivalent (baseline has the value, experiment has cleaner citations).

---

### Question: direct-08

**Question:** Where is the final confidence passed into persistence?

**Expected answer / authoritative reference:** `scripts/investigate.py` line 126 `final_confidence=result["confidence"]` inside the `persist_investigation(...)` call (lines 118-133). Unit test passes `final_confidence="medium"` at `tests/unit/test_investigation_persistence.py:102`.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | — | 0 | 10 | 2 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | — | 0 | 10 | 2 |
| 100/20 — Pass 2 | 10 | 9 | 8 | 9 |

**60/10 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (explicit abstention, confidence low).
- Citations: none (no citations)
- Assessment: No false claim, but the question was answerable and the answer was not given. Top 5 held only test chunks and graph code, not `investigate.py`, so the abstention was reasonable given the evidence (grounding 10).
- Scores: correctness —, completeness 0, grounding 10, overall 2. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): `final_confidence=result["confidence"]` when calling `persist_investigation`, or `final_confidence="medium"` in unit tests.
- Citations: 1592, 1575
- Assessment: Both claims verified. 1575 (`investigate.py:81-180`) contains line 126; 1592 contains test line 102.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): `INSUFFICIENT_EVIDENCE`.
- Citations: none (no citations)
- Assessment: Same as pass 1.
- Scores: correctness —, completeness 0, grounding 10, overall 2. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): `final_confidence` parameter of `persist_investigation(...)`; passed as `final_confidence=result["confidence"]` in investigate.py; tests pass `"medium"`.
- Citations: 1575
- Assessment: Correct. The test claim came from chunk 1592, which was retrieved at rank 1 but not cited.
- Scores: correctness 10, completeness 9, grounding 8, overall 9. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Better** (Clear improvement) |
| Pass 2 | 100/20 against 60/10 | **Better** (Clear improvement) |

#### Question-level conclusion

A real gain. The baseline retrieval missed `investigate.py` entirely and abstained twice; 100/20 retrieved it at rank 4 and answered correctly in both passes.

---

### Question: paraphrased-03

**Question:** How does the project turn text into numeric vectors before storage?

**Expected answer / authoritative reference:** `scripts/embed_chunks.py`: `embed_text` (lines 38-74) sends `outputDimensionality` 768 (line 46), validates dimension, and `chunk.embedding = embed_text(chunk.content)` (line 100).

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 8 | 9 | 9 |
| 100/20 — Pass 1 | 10 | 8 | 10 | 9 |
| 60/10 — Pass 2 | 10 | 9 | 9 | 9 |
| 100/20 — Pass 2 | 10 | 9 | 10 | 9 |

**60/10 — Pass 1**
- Answer (gist): Gemini API request; parse JSON; validate length equals `EMBEDDING_DIMENSION` (768); convert to float; assign to `chunk.embedding` before persisting.
- Citations: 1477 (`51-110`)
- Assessment: All verified. Omits model name and the `outputDimensionality` request parameter. Chunk 1477 covers lines 65-74 and 98-100 but not the request build (38-50).
- Scores: correctness 10, completeness 8, grounding 9, overall 9. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): `models/gemini-embedding-001`, HTTP POST with text, model and `outputDimensionality` 768, returns floats.
- Citations: 1570 (`1-100`)
- Assessment: Verified. Omits validation and the storage step, though the question says "before storage".
- Scores: correctness 10, completeness 8, grounding 10, overall 9. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): Same as pass 1, plus stored in a `VECTOR(768)` column.
- Citations: 1477, 1444, 1492
- Assessment: Verified: `VECTOR(768)` is at `chunk.py` line 45 (chunk 1444).
- Scores: correctness 10, completeness 9, grounding 9, overall 9. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): Calls Gemini embeddings API, POST with `outputDimensionality` 768, parses floats, assigns to `chunk.embedding`.
- Citations: 1570
- Assessment: Verified.
- Scores: correctness 10, completeness 9, grounding 10, overall 9. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Same** (Effectively equivalent) |

#### Question-level conclusion

Both answer correctly from different parts of `embed_text`. The retrieval gain (label chunk now retrieved) did not change answer quality because the baseline answered correctly from an adjacent chunk.

---

### Question: paraphrased-05

**Question:** What stops a weak search result from reaching the language model?

**Expected answer / authoritative reference:** `guard.py` `evaluate_evidence_sufficiency` (lines 12-70; threshold check 45-48) plus `graph.py` `route_after_guard` (164-171) and `return_insufficient` (193-203).

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 7 | 8 | 8 |
| 100/20 — Pass 1 | 10 | 9 | 8 | 9 |
| 60/10 — Pass 2 | 10 | 8 | 8 | 8 |
| 100/20 — Pass 2 | 10 | 9 | 8 | 9 |

**60/10 — Pass 1**
- Answer (gist): `evaluate_evidence_sufficiency` then routing: retry widened search, grep fallback, `return_insufficient` with `INSUFFICIENT_EVIDENCE`.
- Citations: 1454, 1455, 1498, 1502, 1504
- Assessment: Verified against graph.py. Does not state the thresholds that define "weak"; guard.py was not retrieved. Three of five citations are test chunks.
- Scores: correctness 10, completeness 7, grounding 8, overall 8. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): Guard checks RRF >= 0.016 and vector distance <= 0.5; `route_after_guard` retry, grep, or `INSUFFICIENT_EVIDENCE` with low confidence.
- Citations: 1586, 1554, 1585, 1558, 1556
- Assessment: All verified (guard.py lines 7-8, 45-48; graph.py 164-171, 193-203). Names the actual guard thresholds.
- Scores: correctness 10, completeness 9, grounding 8, overall 9. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): Routing in detail: literal source stops, retry count 0 retries, otherwise grep; ends in `INSUFFICIENT_EVIDENCE`.
- Citations: 1454, 1455, 1498, 1502, 1504
- Assessment: Verified. More precise routing than pass 1; still no thresholds.
- Scores: correctness 10, completeness 8, grounding 8, overall 8. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): Guard thresholds plus routing.
- Citations: 1586, 1554, 1585, 1558, 1556
- Assessment: Verified.
- Scores: correctness 10, completeness 9, grounding 8, overall 9. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Better** (Minor improvement) |
| Pass 2 | 100/20 against 60/10 | **Better** (Minor improvement) |

#### Question-level conclusion

The 100/20 answers are more complete because `guard.py` was retrieved and they state the threshold logic. The baseline is correct but describes only the routing.

---

### Question: paraphrased-08

**Question:** What record keeps the retrieved evidence and response metadata together?

**Expected answer / authoritative reference:** `app/db/models/audit.py` `Audit` (lines 18-52) built in `persistence.py` (lines 49-90): `retrieved_chunk_ids`, score arrays, `tool_calls` JSON (with `retrieval_results`), `model`, `response`, `latency_ms`, `token_usage`, `confidence`.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | — | 0 | 10 | 2 |
| 100/20 — Pass 1 | 10 | 9 | 6 | 8 |
| 60/10 — Pass 2 | 4 | 3 | 5 | 3 |
| 100/20 — Pass 2 | 10 | 8 | 6 | 8 |

**60/10 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE`.
- Citations: none (no citations)
- Assessment: Answerable question, no answer. Reasonable given retrieved chunks (graph, parsing, test files), so grounding 10.
- Scores: correctness —, completeness 0, grounding 10, overall 2. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): The `Audit` record keeps `retrieved_chunk_ids`, vector/FTS/RRF scores, retrieval results, and `query`, `repository_id`, `model`, `response`, `latency_ms`, `token_usage`, `confidence`, `tool_calls`.
- Citations: none (no citations)
- Assessment: Every field verified against audit.py and persistence.py. `persistence.py:1-93` (rank 5) supports all of it. No citations.
- Scores: correctness 10, completeness 9, grounding 6, overall 8. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): `persist_investigation` stores "the investigation record" with query, response, model, latency, tokens, retrieval results.
- Citations: 1506 (a test chunk)
- Assessment: Does not name the Audit record. Retrieval results are stored in the Audit row, not the Investigation row, so the claim is misleading. Weak support from a test chunk.
- Scores: correctness 4, completeness 3, grounding 5, overall 3. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): An Audit record (or model) stores retrieval results, scores, tool calls, response, model, latency, tokens, confidence, alongside the investigation ID.
- Citations: none (no citations)
- Assessment: Verified (`investigation_id` FK, audit.py line 24). No citations.
- Scores: correctness 10, completeness 8, grounding 6, overall 8. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Better** (Clear improvement) |
| Pass 2 | 100/20 against 60/10 | **Better** (Clear improvement) |

#### Question-level conclusion

A real gain: the baseline abstained or gave a misleading answer. 100/20 retrieved `persistence.py` at rank 5 and answered correctly. Caveat: no citations in either 100/20 pass, so grounding relies on the retrieved context rather than cited IDs.

---

### Question: paraphrased-07

**Question:** How can the application find an exact phrase in its local source tree?

**Expected answer / authoritative reference:** `app/investigation/mcp_server.py` `grep_search` (lines 21-61): case-insensitive (`casefold`) substring match, line by line, over ingester-visible Python files, default limit 20; exposed as MCP tool `grep_search` (lines 92-119).

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 6 | 8 | 7 |
| 100/20 — Pass 1 | 10 | 6 | 5 | 6 |
| 60/10 — Pass 2 | 10 | 6 | 9 | 7 |
| 100/20 — Pass 2 | 10 | 6 | 8 | 7 |

**60/10 — Pass 1**
- Answer (gist): Use the `grep_search` tool (or `call_grep_search_mcp`), searching raw local Python sources with the same exclusions as ingestion.
- Citations: 1500, 1461, 1501, 1453, 1499
- Assessment: Correct (from the tool description, lines 92-98). Omits case-insensitivity, line-level matching, and the 20-result limit. 1461 contains the tool description.
- Scores: correctness 10, completeness 6, grounding 8, overall 7. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): Same, calling it "exact phrase (or literal keyword)".
- Citations: none (no citations)
- Assessment: Correct but uncited, and "exact" is loose because matching is case-insensitive. Same omissions.
- Scores: correctness 10, completeness 6, grounding 5, overall 6. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): Same as baseline pass 1.
- Citations: 1461, 1453
- Assessment: Same omissions; cites relevant chunks.
- Scores: correctness 10, completeness 6, grounding 9, overall 7. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): Same; names `grep_search_tool` as the MCP tool.
- Citations: 1588, 1587, 1560
- Assessment: Same omissions. Citations include a mix of test and `mcp_server.py:81-131`.
- Scores: correctness 10, completeness 6, grounding 8, overall 7. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Worse** (Minor regression) |
| Pass 2 | 100/20 against 60/10 | **Same** (Effectively equivalent) |

#### Question-level conclusion

Neither arm retrieved the `grep_search` function body (lines 21-61), so both answer from the tool description and miss case-insensitivity. This remains a retrieval miss in both arms. The pass-1 difference is only the missing citations.

---

### Question: direct-01

**Question:** How is AsyncSessionLocal configured?

**Expected answer / authoritative reference:** `app/db/session.py` lines 35-39: `async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)`; engine at 21-24.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

**60/10 — Pass 1**
- Answer (gist): Configured in session.py with `async_sessionmaker`, `bind=engine`, `class_=AsyncSession`, `expire_on_commit=False`.
- Citations: 1447 (`session.py:1-46`, whole file)
- Assessment: All three arguments verified against lines 35-39.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): Same three arguments, plus `create_async_engine`, `_async_database_url` (`postgresql://` to `postgresql+psycopg://`), `pool_pre_ping=True`, pgvector listener on `engine.sync_engine`.
- Citations: 1550 (`session.py:1-46`)
- Assessment: Extras verified at lines 12-32. Relevant to "configured", not padding.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): Same as baseline pass 1.
- Citations: 1447
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): `async_sessionmaker` bound to the async engine, with `pool_pre_ping`, psycopg dialect conversion, pgvector listener, `class_=AsyncSession`, `expire_on_commit=False`.
- Citations: 1550
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Same** (Effectively equivalent) |

#### Question-level conclusion

Both arms retrieve the whole of `session.py` at rank 1 and answer correctly. The 100/20 answers add accurate engine details at about 1,300 extra tokens. No quality difference.

---

### Question: direct-02

**Question:** What chunk size does ingest_repo.py use?

**Expected answer / authoritative reference:** `scripts/ingest_repo.py` line 22 `CHUNK_SIZE = 60` (line 23 `OVERLAP_SIZE = 10`).

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 7 | 9 |
| 100/20 — Pass 1 | 10 | 10 | 7 | 9 |
| 60/10 — Pass 2 | 10 | 10 | 9 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 9 | 10 |

**60/10 — Pass 1**
- Answer (gist): 60 lines (`CHUNK_SIZE = 60`), overlap 10 (`OVERLAP_SIZE = 10`), used by `chunk_lines`.
- Citations: none (no citations)
- Assessment: Correct. No citations, but chunk 1479 (`ingest_repo.py:1-60`, rank 1) contains lines 22-23, so it was supported by retrieved evidence but uncited.
- Scores: correctness 10, completeness 10, grounding 7, overall 9. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): 60 lines (`CHUNK_SIZE = 60`).
- Citations: none (no citations)
- Assessment: Correct. Uncited; chunk 1572 (`1-100`, rank 1) contains line 22.
- Scores: correctness 10, completeness 10, grounding 7, overall 9. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): `CHUNK_SIZE = 60`.
- Citations: 1479, 1480, 1481
- Assessment: Correct. 1479 supports it; the other two cited chunks are redundant.
- Scores: correctness 10, completeness 10, grounding 9, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): 60 lines, overlap 10.
- Citations: 1572, 1573
- Assessment: Correct. 1572 supports it.
- Scores: correctness 10, completeness 10, grounding 9, overall 10. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Same** (Effectively equivalent) |

#### Question-level conclusion

Identical correctness. Both arms omit citations in pass 1 only. Note the answers describe the constants in the code (60/10), which is correct for the question and independent of which chunking the experiment arm used.

---

### Question: direct-03

**Question:** Which Gemini embedding model is configured?

**Expected answer / authoritative reference:** `scripts/embed_chunks.py` line 25 `GEMINI_MODEL = "models/gemini-embedding-001"`.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 8 | 10 | 6 | 9 |

**60/10 — Pass 1**
- Answer (gist): `models/gemini-embedding-001`, constant `GEMINI_MODEL`.
- Citations: 1476, 1477, 1478
- Assessment: Verified. 1476 contains line 25.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): `models/gemini-embedding-001` in embed_chunks.py.
- Citations: 1570, 1571
- Assessment: Verified. 1570 (`1-100`) contains line 25.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): Same as pass 1.
- Citations: 1476, 1477, 1478
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): `models/gemini-embedding-001`, "also referenced in the CLI description as `gemini-gemini-embedding-001`".
- Citations: none (no citations)
- Assessment: Core answer correct. The aside is wrong: the real CLI description (line 121) reads "...with Gemini gemini-embedding-001." There is no string `gemini-gemini-embedding-001`. It misquotes retrieved text (chunk 1571). No citations.
- Scores: correctness 8, completeness 10, grounding 6, overall 9. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Worse** (Minor regression) |

#### Question-level conclusion

Pass 2 of 100/20 gives the right model but adds a garbled quote and no citations. This is a small fabrication-style defect rather than a wrong answer. It is not repeated in pass 1.

---

### Question: direct-06

**Question:** What is the high-confidence RRF calibration margin?

**Expected answer / authoritative reference:** `app/investigation/confidence.py` line 5 `MIN_CLEAR_RRF_SCORE = 0.032`.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

**60/10 — Pass 1**
- Answer (gist): `MIN_CLEAR_RRF_SCORE = 0.032` in confidence.py.
- Citations: 1449
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): Same.
- Citations: 1552
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): Same.
- Citations: 1449
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): Same.
- Citations: 1552
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Same** (Effectively equivalent) |

#### Question-level conclusion

Identical answers. 100/20 used about 52% more tokens (4,368 vs 2,869 in pass 1) for no quality gain here.

---

### Question: direct-07

**Question:** Which MCP server class is instantiated?

**Expected answer / authoritative reference:** `app/investigation/mcp_server.py` line 18 `server = FastMCP("IncidentWeave local investigation tools")`.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 6 | 9 |

**60/10 — Pass 1**
- Answer (gist): `FastMCP`, with the constructor call.
- Citations: 1460, 1462
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): `FastMCP`.
- Citations: 1559, 1560
- Assessment: Verified. 1559 (`1-100`) contains line 18.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): Same as pass 1.
- Citations: 1460, 1462
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): `FastMCP` with the constructor call.
- Citations: none (no citations)
- Assessment: Correct, uncited. 1559 (rank 1) contained the line.
- Scores: correctness 10, completeness 10, grounding 6, overall 9. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Worse** (Minor regression) |

#### Question-level conclusion

Answers are equally correct. The only difference is that 100/20 pass 2 omitted citations.

---

### Question: paraphrased-01

**Question:** How does the database layer establish non-blocking connections and create request-scoped objects?

**Expected answer / authoritative reference:** `app/db/session.py`: `create_async_engine` (lines 21-24), `async_sessionmaker` (35-39), `get_db_session` generator (42-46).

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 9 | 10 | 10 | 9 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

**60/10 — Pass 1**
- Answer (gist): `create_async_engine` with psycopg URL conversion and `pool_pre_ping`; pgvector registration; sessions via `async_sessionmaker`, yielded by `get_db_session()`.
- Citations: 1447
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): Same, with the `run_async(register_vector_async)` listener detail.
- Citations: 1550
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): Same, but says `get_db_session` "yields an AsyncSession context manager instance".
- Citations: 1447
- Assessment: The generator yields the session obtained from `async with AsyncSessionLocal()`, not a context manager. Imprecise wording.
- Scores: correctness 9, completeness 10, grounding 10, overall 9. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): Same, via `async with` and `AsyncSession`.
- Citations: 1550
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Better** (Minor improvement) |

#### Question-level conclusion

Both are correct. The one-point pass-2 gap is a wording imprecision in the baseline.

---

### Question: paraphrased-02

**Question:** How are source files divided into overlapping pieces for indexing?

**Expected answer / authoritative reference:** `scripts/ingest_repo.py`: `chunk_lines` (lines 49-67), `CHUNK_SIZE`/`OVERLAP_SIZE` (22-23); empty-chunk skip in `ingest_repository` (line 104).

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

**60/10 — Pass 1**
- Answer (gist): `chunk_lines`: size 60, overlap 10, step 50, windows only yielded when `end_index > previous_end`.
- Citations: 1480, 1479, 1481
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): Same, plus empty-content skip.
- Citations: 1572, 1573
- Assessment: Verified. The empty-content claim is true (line 104).
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): Same.
- Citations: 1480, 1479, 1481
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): Same, plus Python-only and empty-content filtering.
- Citations: 1572, 1584, 1573
- Assessment: Verified. 1584 is a test chunk, harmless.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Same** (Effectively equivalent) |

#### Question-level conclusion

Both correct and complete. Retrieval of the label chunk improved (rank 2 to 1) but answer quality is unchanged.

---

### Question: paraphrased-04

**Question:** How are two independent search rankings combined into one ordered result?

**Expected answer / authoritative reference:** `app/retrieval/hybrid_search.py`: RRF `1 / (60 + rank)` at lines 39 and 41; union at 30; sort and limit at 69-70.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 9 | 5 | 8 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 9 | 5 | 8 |

**60/10 — Pass 1**
- Answer (gist): RRF in `hybrid_search`: independent vector and FTS searches, 1-based ranks, union of IDs, sum of `1/(60+rank)`, sort descending, apply limit.
- Citations: 1473, 1494, 1472
- Assessment: All five steps verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): Same mechanism in compact form.
- Citations: none (no citations)
- Assessment: Correct. Uncited, though chunk 1567 (`hybrid_search.py:1-70`, rank 2) covers the whole function. Less detail than baseline (no mention that both searches use the limit).
- Scores: correctness 10, completeness 9, grounding 5, overall 8. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): Same four steps.
- Citations: 1473, 1494, 1472
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): Same compact form.
- Citations: none (no citations)
- Assessment: Correct, uncited.
- Scores: correctness 10, completeness 9, grounding 5, overall 8. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Worse** (Minor regression) |
| Pass 2 | 100/20 against 60/10 | **Worse** (Minor regression) |

#### Question-level conclusion

Content is equally correct. The difference is entirely grounding behavior: the 100/20 answers cite nothing, and are slightly less detailed.

---

### Question: paraphrased-06

**Question:** How is a model's certainty adjusted when the supporting search evidence is borderline?

**Expected answer / authoritative reference:** `app/investigation/confidence.py` `calibrate_confidence` (lines 9-38): high downgraded to medium if RRF < 0.032 or distance > 0.4.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 9 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

**60/10 — Pass 1**
- Answer (gist): High downgraded to medium when RRF < `MIN_CLEAR_RRF_SCORE` (0.032) or distance > `MAX_CLEAR_VECTOR_DISTANCE` (0.4); non-high retained.
- Citations: 1449, 1498
- Assessment: Verified. 1498 is a test chunk.
- Scores: correctness 10, completeness 10, grounding 9, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): Same.
- Citations: 1552
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): Same, naming `calibrate_confidence` and the reason note.
- Citations: 1449
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): Same, naming `calibrate_confidence`.
- Citations: 1552
- Assessment: Verified.
- Scores: correctness 10, completeness 10, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Same** (Effectively equivalent) |

#### Question-level conclusion

Identical in substance. Token use is about 17% higher with 100/20.

---

### Question: unanswerable_far-01

**Question:** How do I bake sourdough bread at high altitude?

**Expected answer / authoritative reference:** No source in the corpus. Correct behavior is to abstain.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Same** (Effectively equivalent) |

#### Question-level conclusion

Guard refuses at retrieval stage in both arms, so this is independent of chunking. Wall time is 15-24 s in all runs because of the retry and grep fallback.

---

### Question: unanswerable_far-02

**Question:** Which telescope can observe the rings of Saturn?

**Expected answer / authoritative reference:** No source in the corpus. Correct behavior is to abstain.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Same** (Effectively equivalent) |

#### Question-level conclusion

Guard refuses at retrieval stage in both arms, so this is independent of chunking. Wall time is 15-24 s in all runs because of the retry and grep fallback.

---

### Question: unanswerable_far-03

**Question:** How should a wooden canoe be repaired?

**Expected answer / authoritative reference:** No source in the corpus. Correct behavior is to abstain.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Same** (Effectively equivalent) |

#### Question-level conclusion

Guard refuses at retrieval stage in both arms, so this is independent of chunking. Wall time is 15-24 s in all runs because of the retry and grep fallback.

---

### Question: unanswerable_far-04

**Question:** Why do coral reefs bleach during marine heatwaves?

**Expected answer / authoritative reference:** No source in the corpus. Correct behavior is to abstain.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): `INSUFFICIENT_EVIDENCE` (guard refused: no repository evidence retrieved; generation not called).
- Citations: none (no citations)
- Assessment: Correct refusal. No claims made.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Same** (Effectively equivalent) |

#### Question-level conclusion

Guard refuses at retrieval stage in both arms, so this is independent of chunking. Wall time is 15-24 s in all runs because of the retry and grep fallback.

---

### Question: unanswerable_near-01

**Question:** How is Redis configured for this application?

**Expected answer / authoritative reference:** No Redis in the pinned corpus (grep of the pinned tree finds none). Correct behavior is to abstain.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 6 | 8 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE`, confidence `medium`.
- Citations: 1439, 1506, 1507, 1440, 1492
- Assessment: Abstains correctly but reports `medium` confidence and cites five unrelated chunks while refusing. The metadata contradicts the abstention.
- Scores: correctness 10, completeness n/a, grounding 6, overall 8. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE`, confidence `low`.
- Citations: none (no citations)
- Assessment: Clean abstention.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): `INSUFFICIENT_EVIDENCE`, confidence `low`.
- Citations: none (no citations)
- Assessment: Clean abstention.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): `INSUFFICIENT_EVIDENCE`, confidence `low`.
- Citations: none (no citations)
- Assessment: Clean abstention.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Better** (Minor improvement) |
| Pass 2 | 100/20 against 60/10 | **Same** (Effectively equivalent) |

#### Question-level conclusion

All eight responses abstain; no one answers falsely. Baseline pass 1 has inconsistent metadata. The guard accepts the evidence in both arms (a known false accept), costing tokens but not correctness.

---

### Question: unanswerable_near-02

**Question:** How does the message queue retry failed jobs?

**Expected answer / authoritative reference:** No message queue in the corpus. Correct behavior is to abstain.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE`, low.
- Citations: none (no citations)
- Assessment: Clean.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): Same, low.
- Citations: none (no citations)
- Assessment: Clean.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): Same.
- Citations: none (no citations)
- Assessment: Clean.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): Same.
- Citations: none (no citations)
- Assessment: Clean.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Same** (Effectively equivalent) |

#### Question-level conclusion

Equivalent. 100/20 uses about 47% more tokens (5,039 vs 3,435) for the same abstention.

---

### Question: unanswerable_near-03

**Question:** Where is user login and authentication implemented?

**Expected answer / authoritative reference:** No authentication code in the pinned corpus. Correct behavior is to abstain.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 8 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 8 |

**60/10 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE`, low.
- Citations: none (no citations)
- Assessment: Clean.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE`, confidence `medium`.
- Citations: none (no citations)
- Assessment: Correct abstention, but `medium` confidence on a refusal is miscalibrated.
- Scores: correctness 10, completeness n/a, grounding 10, overall 8. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): Same, low.
- Citations: none (no citations)
- Assessment: Clean.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): `INSUFFICIENT_EVIDENCE`, confidence `medium`.
- Citations: none (no citations)
- Assessment: Same miscalibration.
- Scores: correctness 10, completeness n/a, grounding 10, overall 8. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Worse** (Minor regression) |
| Pass 2 | 100/20 against 60/10 | **Worse** (Minor regression) |

#### Question-level conclusion

Both 100/20 passes abstain correctly but report `medium` confidence, a consistent small defect in this question. Both baseline passes report `low`.

---

### Question: unanswerable_near-04

**Question:** Which Kubernetes deployment target does this service use?

**Expected answer / authoritative reference:** No Kubernetes configuration in the corpus. Correct behavior is to abstain.

#### Response assessments

| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

**60/10 — Pass 1**
- Answer (gist): `INSUFFICIENT_EVIDENCE`, low.
- Citations: none (no citations)
- Assessment: Clean.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 1**
- Answer (gist): Same.
- Citations: none (no citations)
- Assessment: Clean.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**60/10 — Pass 2**
- Answer (gist): Same.
- Citations: none (no citations)
- Assessment: Clean.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

**100/20 — Pass 2**
- Answer (gist): Same.
- Citations: none (no citations)
- Assessment: Clean.
- Scores: correctness 10, completeness n/a, grounding 10, overall 10. Overall is a judgement; see the assessment above for what moved it.

#### Comparative verdict

| Pass | Comparison | Verdict |
|---|---|---|
| Pass 1 | 100/20 against 60/10 | **Same** (Effectively equivalent) |
| Pass 2 | 100/20 against 60/10 | **Same** (Effectively equivalent) |

#### Question-level conclusion

Equivalent.

---

## 2. Final report

### 2.1 Summary table

| Question | Pass 1 | Pass 2 | Main reason |
|---|---|---|---|
| direct-01 | Same | Same | Equivalent; 100/20 adds accurate engine detail. |
| direct-02 | Same | Same | Equivalent; both uncited in pass 1. |
| direct-03 | Same | Worse | P2: 100/20 adds a garbled `gemini-gemini-embedding-001` aside and no citations. |
| direct-04 | Better | Better | 100/20 gives the value and cites; baseline omits 0.016 (and pass 2 is uncited). |
| direct-05 | Same | Better | Equivalent in P1 (baseline has the value; 100/20 cites more cleanly); 100/20 better in P2. |
| direct-06 | Same | Same | Identical; 100/20 costs ~52% more tokens. |
| direct-07 | Same | Worse | P2: 100/20 uncited; content equal. |
| direct-08 | Better | Better | Baseline abstained twice; 100/20 answers correctly and cites. |
| paraphrased-01 | Same | Better | Equivalent; baseline P2 has a loose phrase. |
| paraphrased-02 | Same | Same | Equivalent. |
| paraphrased-03 | Same | Same | Equivalent; both correct from different parts of `embed_text`. |
| paraphrased-04 | Worse | Worse | Content equal; 100/20 gives no citations. |
| paraphrased-05 | Better | Better | 100/20 states the guard thresholds; baseline describes only routing. |
| paraphrased-06 | Same | Same | Identical. |
| paraphrased-07 | Worse | Same | Both miss case-insensitivity; P1 100/20 uncited. |
| paraphrased-08 | Better | Better | Baseline abstained or misattributed; 100/20 names `Audit` correctly (uncited). |
| unanswerable_far-01 | Same | Same | Guard refusal in both arms. |
| unanswerable_far-02 | Same | Same | Guard refusal in both arms. |
| unanswerable_far-03 | Same | Same | Guard refusal in both arms. |
| unanswerable_far-04 | Same | Same | Guard refusal in both arms. |
| unanswerable_near-01 | Better | Same | Baseline P1 abstains but reports medium confidence and cites 5 chunks. |
| unanswerable_near-02 | Same | Same | Equivalent; 100/20 ~47% more tokens. |
| unanswerable_near-03 | Worse | Worse | 100/20 reports `medium` confidence on a refusal in both passes. |
| unanswerable_near-04 | Same | Same | Equivalent. |

### 2.2 Verdict counts (100/20 against 60/10, per pass, 24 questions)

| Pass | Better | Same | Worse | Uncertain |
|---|---:|---:|---:|---:|
| Pass 1 | 5 | 16 | 3 | 0 |
| Pass 2 | 6 | 14 | 4 | 0 |

Of these, 8 questions are unanswerable and are refusals in both arms; 4 of them (the far questions) never reach generation. Counting the 16 answerable questions only:

| Pass | Better | Same | Worse |
|---|---:|---:|---:|
| Pass 1 | 4 | 10 | 2 |
| Pass 2 | 6 | 7 | 3 |

**Mean scores on the 16 answerable questions** (descriptive only; n is too small for inference; correctness excludes abstentions):

| Response set | Correctness | Completeness | Grounding | Overall |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 8.06 | 9.31 | 8.38 |
| 100/20 — Pass 1 | 10 | 9.38 | 8.75 | 9.19 |
| 60/10 — Pass 2 | 9.53 | 8.38 | 9.06 | 8.38 |
| 100/20 — Pass 2 | 9.88 | 9.38 | 8.44 | 9.19 |

### 2.3 Most important findings

**Completeness / correctness improvements (clear, both passes):**
1. `direct-08`: baseline abstained twice (`investigate.py` never retrieved); 100/20 answered correctly and cited the right chunk.
2. `paraphrased-08`: baseline abstained once and gave a misleading "investigation record" answer once; 100/20 named the `Audit` record with every field verified against `audit.py` and `persistence.py`.

**Minor improvements:** `direct-04` (value and citations), `direct-05` pass 2, `paraphrased-05` (states the guard thresholds), `paraphrased-01` pass 2, `unanswerable_near-01` pass 1 (cleaner abstention metadata).

**Correctness regressions:** none material. The only incorrect claim attributable to 100/20 is the garbled `gemini-gemini-embedding-001` aside in `direct-03` pass 2 (core answer right).

**Grounding weaknesses (the main negative signal):**
- **100/20 omits citations far more often.** Counting the 32 answerable responses per arm, 100/20 has **8 with no citations** (all of them real answers: `direct-02` P1, `direct-03` P2, `direct-07` P2, `paraphrased-04` P1 and P2, `paraphrased-07` P1, `paraphrased-08` P1 and P2). The baseline has 5, but 3 of those are abstentions, so only **2 of 29 non-abstaining baseline answers** (`direct-02` P1, `direct-04` P2) are uncited. This is a counted fact from the workbook's saved tables. The *cause* is unknown (**Hypothesis:** larger chunks make the model less likely to emit chunk IDs; not tested).
- Every uncited 100/20 answer was still supported by evidence in the retrieved top five, with one exception: the garbled aside in `direct-03` pass 2. So the defect is mainly missing citations, not unsupported claims. It does reduce auditability.
- `unanswerable_near-03`: 100/20 reports `medium` confidence on a correct refusal in both passes.

**Cases where the passes disagree for the same question (verdict differs between P1 and P2):** `direct-03` (Same, Worse), `direct-05` (Same, Better), `direct-07` (Same, Worse), `paraphrased-01` (Same, Better), `paraphrased-07` (Worse, Same), `unanswerable_near-01` (Better, Same). All differences are one or two points and driven by citation presence or a single phrase. Generation variance is therefore of the same size as most of the differences that are not `direct-08` and `paraphrased-08`.

**Pre-existing, chunking-independent findings (worth knowing, not caused by 100/20):**
- `paraphrased-07`: neither arm retrieves the `grep_search` function body, so neither answer mentions case-insensitive matching.
- Four near-unanswerable questions pass the guard (a known false accept), cost tokens, and are then correctly refused by the model.

### 2.4 Limitations
- I read chunk spans, not chunk bodies, and not the raw JSON. Grounding judgements rest on line spans against the pinned source.
- Reviewer is an AI model; not blind to arm identity. See section 3.
- The golden set is "pending maintainer review". The two clear improvements (`direct-08`, `paraphrased-08`) depend on those labels being right; I verified that the answers are correct against source independent of the labels.
- Two generation passes share identical retrieval, so they are not two independent samples of retrieval quality.
- Sixteen answerable questions on one 40-file corpus. Many 100/20 chunks are whole files (`guard.py:1-70`, `persistence.py:1-93`, `embed_chunks.py:1-100`), so results may not transfer to repositories with large files.

### 2.5 Gate 5 assessment (input only)

D4 Gate 5 asks that human-reviewed end-to-end correctness is **not lower**. On this evidence:

- **Correctness and completeness: not lower, and modestly higher.** Two questions go from abstention or a misleading answer to correct. No answer changes from correct to wrong.
- **Grounding hygiene: lower.** Citation omission is more frequent in 100/20 (8/32 vs 2/29), and one unanswerable question shows a miscalibrated confidence. These are minor per instance but systematic.
- **Cost:** about 40% higher median tokens (already measured; I did not re-measure).

My assessment: **the evidence supports "not lower" on answer correctness and completeness, with a real but minor citation-behaviour regression.** I would classify the result as a **minor-to-moderate improvement overall**, concentrated in two questions. It does not by itself justify a production change; that remains the maintainer's decision after a human reads at least the priority questions. I did not record the Gate 5 verdict in the workbook.

### 2.6 Unresolved issues needing inspection
1. Why do 100/20 answers cite less? Check the prompt-building code for how chunk IDs are presented, and whether chunk size interacts with it.
2. Human read of `paraphrased-08` experiment answers: I verified the field list against source, but a maintainer should confirm that uncited is acceptable for adoption.
3. `unanswerable_near-03`: confirm why abstentions report `medium` confidence in one arm.
4. The label-review question for `paraphrased-07`, `paraphrased-05` and `paraphrased-08` (whether `graph.py`/`audit.py` should count as relevant labels) remains open and is maintainer-owned.

---

## 3. Critique of the review methodology

**Is the rubric objective and reproducible?** Partly. Four /10 scores per response is not reproducible between reviewers: the difference between 8 and 9 is not defined, and "Overall is not an average" removes the one constraint that would anchor it. I added anchors (section 0) and a mechanical verdict rule to reduce this, but the prompt itself does not require them.

**Missing dimensions.**
- **Citation behaviour** as its own item. In this experiment it is the single most consistent difference, and a /10 "grounding" score blends it with factual support.
- **Confidence calibration / metadata consistency** (found in `unanswerable_near-01` and `-03`).
- **Cost** (tokens, latency) next to quality, since D4 gate 6 already weighs it.

**Reviewer bias and inconsistency risks.**
- The reviewer sees which arm is the experiment, and the priority list mirrors the report's highlights. Both invite confirmation of the expected result.
- Longer, more detailed answers tend to score higher unless the rubric explicitly penalises unrequested detail; the prompt does, but only in prose.
- 32 of the 96 instances are responses to unanswerable questions, and about 10 of the 16 answerable-question pairs get the same verdict in pass 1. Scoring all of them at the same depth dilutes attention from the few pairs that actually differ (`direct-08`, `paraphrased-08`, and a handful of minor ones).
- Gate 5 requires a **human**; three AI reviewers are not independent samples of one judge, and none is blind.

**What I would change.**

| # | Change | Class | Benefit | Cost |
|---|---|---|---|---|
| 1 | Replace /10 scores with 3 levels (Correct / Partial / Wrong; Grounded / Weak / Ungrounded) and a fixed verdict rule | **Essential** | Reproducible across reviewers; same result with less noise | Loses fine ranking |
| 2 | Add a separate citation-behaviour line and a calibration check | **Essential** | Captures the main observed difference explicitly | One extra column |
| 3 | Report answerable questions (16) as the primary result; treat the 8 unanswerable as a separate safety check | **Essential** | Stops 8 non-informative questions diluting counts | None |
| 4 | Define "not lower" operationally: for example, no clear regression (3+ points) and net Better >= net Worse | **Essential** | Removes discretion at the decision point | Needs maintainer approval |
| 5 | Randomise and hide arm labels (X/Y) per question | Optional | Removes arm-identity bias | Setup effort; hard for an LLM to truly blind |
| 6 | Pre-filter pairs whose answers are identical in substance and review only the differing ones in depth | Optional | Likely cuts review volume substantially (I estimate roughly half or more; not measured) | Needs a diff rule |
| 7 | Have the maintainer read only the 7 priority questions plus any pair flagged Worse | Optional | Satisfies "human-reviewed" at realistic cost | Still a judgement call |
| 8 | Do not treat two passes as two samples; report them as generation variance | Optional | Honest uncertainty statement | None |

None of these changes the approved architecture or scope. **I have not applied any of them to the agreed method; they are proposals for approval.**
