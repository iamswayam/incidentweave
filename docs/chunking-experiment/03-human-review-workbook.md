# Chunking Experiment: Human Review Workbook

> **Purpose:** a readable, evidence-linked worksheet for manually reviewing end-to-end answers under 60/10 and 100/20. This workbook does not make or imply a Gate 5 decision.

## How to use this workbook

1. Review all 24 questions, both generation passes, and both strategies. Do not use `outcome_v2` or keyword labels as a substitute for your judgment.
2. Assess factual correctness, completeness, and grounding in retrieved/cited evidence. Each question links to full exact saved chunk text in the evidence library.
3. Compare baseline versus experiment separately for pass 1 and pass 2; record better / same / worse / uncertain and explain differences.
4. For unanswerable questions, assess whether abstention was appropriate and whether any answer is unsupported.
5. Gate 5 remains **NEUTRAL / PENDING** while further review continues. This position is not a verdict for any individual question and does not mark Gate 5 as passed. Production remains 60/10 until a final decision is made.

## Human reviewer overall position

> As a human reviewer, I currently lean 55% toward 100/20 and 45% toward 60/10. However, the evidence does not establish a clear winner. Gate 5 remains neutral pending further review, and production chunking will stay at 60/10 until a final decision is made.

This is an overall position only. It does not replace or change any question-level assessment below, and Gate 5 remains pending rather than passed.

Pass-1 and pass-2 retrieval lists are identical within each strategy in the saved artifacts, so each strategy context is listed once per question. Answers and metadata are listed separately for all four arm/pass combinations.

## Experiment identity

| Arm | Strategy | Run ID | Files / chunks | Source SHA | Pinned corpus SHA |
|---|---|---|---:|---|---|
| 60/10 baseline | 60/10 | `20261018T123627Z-2274338-baseline` | 40 / 70 | `22743382a4980d7787bc798d9ad8e2ab6ddecb18` | `62d0e58593bb22d187ec7930274b0457afd3be74` |
| 100/20 experiment | 100/20 | `20261018T124223Z-2274338-w100_o20` | 40 / 52 | `22743382a4980d7787bc798d9ad8e2ab6ddecb18` | `62d0e58593bb22d187ec7930274b0457afd3be74` |

Both reports record `code_dirty=False` / `False`; golden review status is `pending maintainer review`. The referenced JSON files are local/ignored artifacts; this workbook does not alter or copy them.

### Question index (24)

| ID | Category | Question | 60/10 rank | 100/20 rank |
|---|---|---|---:|---:|
| [direct-01](#direct-01) | direct | How is AsyncSessionLocal configured? | 1 | 1 |
| [direct-02](#direct-02) | direct | What chunk size does ingest_repo.py use? | 1 | 1 |
| [direct-03](#direct-03) | direct | Which Gemini embedding model is configured? | 1 | 1 |
| [direct-04](#direct-04) | direct | What constant controls the minimum RRF score? | 1 | 1 |
| [direct-05](#direct-05) | direct | What constant controls the maximum vector distance? | 3 | 2 |
| [direct-06](#direct-06) | direct | What is the high-confidence RRF calibration margin? | 1 | 1 |
| [direct-07](#direct-07) | direct | Which MCP server class is instantiated? | 1 | 1 |
| [direct-08](#direct-08) | direct | Where is the final confidence passed into persistence? | n/a | 4 |
| [paraphrased-01](#paraphrased-01) | paraphrased | How does the database layer establish non-blocking connections and create request-scoped objects? | 1 | 1 |
| [paraphrased-02](#paraphrased-02) | paraphrased | How are source files divided into overlapping pieces for indexing? | 2 | 1 |
| [paraphrased-03](#paraphrased-03) | paraphrased | How does the project turn text into numeric vectors before storage? | n/a | 2 |
| [paraphrased-04](#paraphrased-04) | paraphrased | How are two independent search rankings combined into one ordered result? | 3 | 2 |
| [paraphrased-05](#paraphrased-05) | paraphrased | What stops a weak search result from reaching the language model? | n/a | 4 |
| [paraphrased-06](#paraphrased-06) | paraphrased | How is a model's certainty adjusted when the supporting search evidence is borderline? | 1 | 1 |
| [paraphrased-07](#paraphrased-07) | paraphrased | How can the application find an exact phrase in its local source tree? | n/a | n/a |
| [paraphrased-08](#paraphrased-08) | paraphrased | What record keeps the retrieved evidence and response metadata together? | n/a | 5 |
| [unanswerable_far-01](#unanswerable_far-01) | unanswerable_far | How do I bake sourdough bread at high altitude? | n/a | n/a |
| [unanswerable_far-02](#unanswerable_far-02) | unanswerable_far | Which telescope can observe the rings of Saturn? | n/a | n/a |
| [unanswerable_far-03](#unanswerable_far-03) | unanswerable_far | How should a wooden canoe be repaired? | n/a | n/a |
| [unanswerable_far-04](#unanswerable_far-04) | unanswerable_far | Why do coral reefs bleach during marine heatwaves? | n/a | n/a |
| [unanswerable_near-01](#unanswerable_near-01) | unanswerable_near | How is Redis configured for this application? | n/a | n/a |
| [unanswerable_near-02](#unanswerable_near-02) | unanswerable_near | How does the message queue retry failed jobs? | n/a | n/a |
| [unanswerable_near-03](#unanswerable_near-03) | unanswerable_near | Where is user login and authentication implemented? | n/a | n/a |
| [unanswerable_near-04](#unanswerable_near-04) | unanswerable_near | Which Kubernetes deployment target does this service use? | n/a | n/a |

## Question-by-question review

<a id="direct-01"></a>
<details><summary><strong>direct-01</strong> - How is AsyncSessionLocal configured?</summary>

**Category:** `direct`\
**Question:** How is AsyncSessionLocal configured?
**Golden relevant label(s):** app/db/session.py: `AsyncSessionLocal = async_sessionmaker`\
**Automated must-mention screen (not a human verdict):** (`async_sessionmaker`) AND (`expire_on_commit`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | correct | correct_labeled_context | False | True | 1447 | 2802 | 2007 | none |
| 100/20 experiment | 1 | correct | correct_labeled_context | False | True | 1550 | 4186 | 1501 | none |
| 60/10 baseline | 2 | correct | correct_labeled_context | False | True | 1447 | 2800 | 1259 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | 1550 | 4140 | 1448 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `high`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `2427 ms`; generation `2007 ms`; throttle `0 ms`; tokens `2802`.
Evidence check: sufficient `True`; best RRF `0.032018442622950824`; best vector `0.27431773122582614`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1447`. Citation relevance flags: [{'id': '1447', 'found_in_retrieval_results': True, 'relevant': True}].

> AsyncSessionLocal is configured in `app/db/session.py` using `async_sessionmaker` with `bind=engine`, `class_=AsyncSession`, and `expire_on_commit=False`.

**100/20 experiment - pass-1** - confidence `high`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1786 ms`; generation `1501 ms`; throttle `0 ms`; tokens `4186`.
Evidence check: sufficient `True`; best RRF `0.032018442622950824`; best vector `0.27431773122582614`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1550`. Citation relevance flags: [{'id': '1550', 'found_in_retrieval_results': True, 'relevant': True}].

> `AsyncSessionLocal` is configured in `app/db/session.py` using `async_sessionmaker` with `bind=engine`, `class_=AsyncSession`, and `expire_on_commit=False`. The underlying async engine is created via `create_async_engine` using a database URL converted by `_async_database_url` (which replaces `"postgresql://"` with `"postgresql+psycopg://"`) and configured with `pool_pre_ping=True`. Additionally, an event listener on `engine.sync_engine` registers pgvector types for each async psycopg connection.

**60/10 baseline - pass-2** - confidence `high`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1680 ms`; generation `1259 ms`; throttle `0 ms`; tokens `2800`.
Evidence check: sufficient `True`; best RRF `0.032018442622950824`; best vector `0.27431773122582614`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1447`. Citation relevance flags: [{'id': '1447', 'found_in_retrieval_results': True, 'relevant': True}].

> AsyncSessionLocal is configured in app/db/session.py using `async_sessionmaker` with `bind=engine`, `class_=AsyncSession`, and `expire_on_commit=False`.

**100/20 experiment - pass-2** - confidence `high`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1705 ms`; generation `1448 ms`; throttle `0 ms`; tokens `4140`.
Evidence check: sufficient `True`; best RRF `0.032018442622950824`; best vector `0.27431773122582614`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1550`. Citation relevance flags: [{'id': '1550', 'found_in_retrieval_results': True, 'relevant': True}].

> AsyncSessionLocal is configured in `app/db/session.py` using `async_sessionmaker` bound to an asynchronous SQLAlchemy engine created with `create_async_engine`, with `pool_pre_ping=True`, the psycopg async dialect URL conversion, a pgvector connection event listener, and `class_=AsyncSession` and `expire_on_commit=False`.

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1447](#baseline-chunk-1447) | `app/db/session.py:1-46` | 0.27431773122582614 | 0.0015151516 | 0.032018442622950824 | yes | yes | none (file boundary) | none (file boundary) |
| 2 | [1503](#baseline-chunk-1503) | `tests/unit/test_investigation_parsing.py:1-60` | None | 0.05 | 0.01639344262295082 | no | no | none (file boundary) | [retrieved chunk 1504](#baseline-chunk-1504) |
| 3 | [1504](#baseline-chunk-1504) | `tests/unit/test_investigation_parsing.py:51-95` | None | 0.05 | 0.016129032258064516 | no | no | [retrieved chunk 1503](#baseline-chunk-1503) | none (file boundary) |
| 4 | [1507](#baseline-chunk-1507) | `tests/unit/test_investigation_persistence.py:101-120` | 0.3510612619362281 | None | 0.016129032258064516 | no | no | [retrieved chunk 1506](#baseline-chunk-1506) | none (file boundary) |
| 5 | [1506](#baseline-chunk-1506) | `tests/unit/test_investigation_persistence.py:51-110` | 0.3711715531572327 | None | 0.015873015873015872 | no | no | [tests/unit/test_investigation_persistence.py:1-60](#baseline-context-91193a850a6b0918) | [retrieved chunk 1507](#baseline-chunk-1507) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1550](#experiment-chunk-1550) | `app/db/session.py:1-46` | 0.27431773122582614 | 0.0015151516 | 0.032018442622950824 | yes | yes | none (file boundary) | none (file boundary) |
| 2 | [1591](#experiment-chunk-1591) | `tests/unit/test_investigation_persistence.py:1-100` | 0.3980543698012816 | 0.0021276595 | 0.03125763125763126 | no | no | none (file boundary) | [retrieved chunk 1592](#experiment-chunk-1592) |
| 3 | [1590](#experiment-chunk-1590) | `tests/unit/test_investigation_parsing.py:1-95` | None | 0.05 | 0.01639344262295082 | no | no | none (file boundary) | none (file boundary) |
| 4 | [1570](#experiment-chunk-1570) | `scripts/embed_chunks.py:1-100` | None | 0.005091903 | 0.016129032258064516 | no | no | none (file boundary) | [retrieved chunk 1571](#experiment-chunk-1571) |
| 5 | [1592](#experiment-chunk-1592) | `tests/unit/test_investigation_persistence.py:81-120` | 0.36713059588700325 | None | 0.016129032258064516 | no | no | [retrieved chunk 1591](#experiment-chunk-1591) | none (file boundary) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="direct-02"></a>
<details><summary><strong>direct-02</strong> - What chunk size does ingest_repo.py use?</summary>

**Category:** `direct`\
**Question:** What chunk size does ingest_repo.py use?
**Golden relevant label(s):** scripts/ingest_repo.py: `CHUNK_SIZE = 60`\
**Automated must-mention screen (not a human verdict):** (`60`) AND (`chunk`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | correct | correct_labeled_context | False | True | none | 2746 | 1179 | none |
| 100/20 experiment | 1 | correct | correct_labeled_context | False | True | none | 3724 | 1126 | none |
| 60/10 baseline | 2 | correct | correct_labeled_context | False | True | 1479, 1480, 1481 | 2708 | 1021 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | 1572, 1573 | 3742 | 1273 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1434 ms`; generation `1179 ms`; throttle `0 ms`; tokens `2746`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.28372615968198334`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> The `ingest_repo.py` script uses a chunk size of 60 lines (`CHUNK_SIZE = 60`) with an overlap size of 10 lines (`OVERLAP_SIZE = 10`), as defined by module-level constants and used in the `chunk_lines` function.

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1363 ms`; generation `1126 ms`; throttle `0 ms`; tokens `3724`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.2798917658097364`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> `ingest_repo.py` uses a chunk size of 60 lines (defined by `CHUNK_SIZE = 60`).

**60/10 baseline - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1324 ms`; generation `1021 ms`; throttle `0 ms`; tokens `2708`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.28372615968198334`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1479`, `1480`, `1481`. Citation relevance flags: [{'id': '1479', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1480', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1481', 'found_in_retrieval_results': True, 'relevant': False}].

> `scripts/ingest_repo.py` uses a chunk size defined by the constant `CHUNK_SIZE = 60`.

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1553 ms`; generation `1273 ms`; throttle `0 ms`; tokens `3742`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.2798917658097364`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1572`, `1573`. Citation relevance flags: [{'id': '1572', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1573', 'found_in_retrieval_results': True, 'relevant': False}].

> `scripts/ingest_repo.py` uses a chunk size of 60 lines (`CHUNK_SIZE = 60`) with an overlap size of 10 lines (`OVERLAP_SIZE = 10`).

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1479](#baseline-chunk-1479) | `scripts/ingest_repo.py:1-60` | 0.28372615968198334 | None | 0.01639344262295082 | no | yes | none (file boundary) | [retrieved chunk 1480](#baseline-chunk-1480) |
| 2 | [1480](#baseline-chunk-1480) | `scripts/ingest_repo.py:51-110` | 0.2934451183578036 | None | 0.016129032258064516 | no | yes | [retrieved chunk 1479](#baseline-chunk-1479) | [retrieved chunk 1481](#baseline-chunk-1481) |
| 3 | [1481](#baseline-chunk-1481) | `scripts/ingest_repo.py:101-158` | 0.3053164754910196 | None | 0.015873015873015872 | no | yes | [retrieved chunk 1480](#baseline-chunk-1480) | none (file boundary) |
| 4 | [1476](#baseline-chunk-1476) | `scripts/embed_chunks.py:1-60` | 0.35324822951494317 | None | 0.015625 | no | no | none (file boundary) | [retrieved chunk 1477](#baseline-chunk-1477) |
| 5 | [1495](#baseline-chunk-1495) | `tests/unit/test_ingest_repo.py:1-20` | 0.35794326148580125 | None | 0.015384615384615385 | no | no | none (file boundary) | none (file boundary) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1572](#experiment-chunk-1572) | `scripts/ingest_repo.py:1-100` | 0.2798917658097364 | None | 0.01639344262295082 | no | yes | none (file boundary) | [retrieved chunk 1573](#experiment-chunk-1573) |
| 2 | [1573](#experiment-chunk-1573) | `scripts/ingest_repo.py:81-158` | 0.30988066904293243 | None | 0.016129032258064516 | no | yes | [retrieved chunk 1572](#experiment-chunk-1572) | none (file boundary) |
| 3 | [1570](#experiment-chunk-1570) | `scripts/embed_chunks.py:1-100` | 0.3364146947535933 | None | 0.015873015873015872 | no | no | none (file boundary) | [retrieved chunk 1571](#experiment-chunk-1571) |
| 4 | [1584](#experiment-chunk-1584) | `tests/unit/test_ingest_repo.py:1-20` | 0.35794326148580125 | None | 0.015625 | no | no | none (file boundary) | none (file boundary) |
| 5 | [1547](#experiment-chunk-1547) | `app/db/models/chunk.py:1-52` | 0.3630479413480133 | None | 0.015384615384615385 | no | no | none (file boundary) | none (file boundary) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="direct-03"></a>
<details><summary><strong>direct-03</strong> - Which Gemini embedding model is configured?</summary>

**Category:** `direct`\
**Question:** Which Gemini embedding model is configured?
**Golden relevant label(s):** scripts/embed_chunks.py: `models/gemini-embedding-001`\
**Automated must-mention screen (not a human verdict):** (`gemini-embedding-001`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | correct | correct_labeled_context | False | True | 1476, 1477, 1478 | 2761 | 1342 | none |
| 100/20 experiment | 1 | correct | correct_labeled_context | False | True | 1570, 1571 | 3703 | 1174 | none |
| 60/10 baseline | 2 | correct | correct_labeled_context | False | True | 1476, 1477, 1478 | 2840 | 1274 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | none | 3714 | 1223 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `high`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1712 ms`; generation `1342 ms`; throttle `0 ms`; tokens `2761`.
Evidence check: sufficient `True`; best RRF `0.03278688524590164`; best vector `0.3361928273531093`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1476`, `1477`, `1478`. Citation relevance flags: [{'id': '1476', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1477', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1478', 'found_in_retrieval_results': True, 'relevant': False}].

> The configured Gemini embedding model is `"models/gemini-embedding-001"`, defined by the `GEMINI_MODEL` constant in `scripts/embed_chunks.py`.

**100/20 experiment - pass-1** - confidence `high`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1428 ms`; generation `1174 ms`; throttle `0 ms`; tokens `3703`.
Evidence check: sufficient `True`; best RRF `0.03252247488101534`; best vector `0.3455308475035963`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1570`, `1571`. Citation relevance flags: [{'id': '1570', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1571', 'found_in_retrieval_results': True, 'relevant': False}].

> The Gemini embedding model configured in `scripts/embed_chunks.py` is `models/gemini-embedding-001`.

**60/10 baseline - pass-2** - confidence `high`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1601 ms`; generation `1274 ms`; throttle `0 ms`; tokens `2840`.
Evidence check: sufficient `True`; best RRF `0.03278688524590164`; best vector `0.3361928273531093`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1476`, `1477`, `1478`. Citation relevance flags: [{'id': '1476', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1477', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1478', 'found_in_retrieval_results': True, 'relevant': False}].

> The configured Gemini embedding model is `"models/gemini-embedding-001"`, defined by the constant `GEMINI_MODEL` in `scripts/embed_chunks.py`.

**100/20 experiment - pass-2** - confidence `high`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1545 ms`; generation `1223 ms`; throttle `0 ms`; tokens `3714`.
Evidence check: sufficient `True`; best RRF `0.03252247488101534`; best vector `0.3455308475035963`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> The Gemini embedding model configured is `models/gemini-embedding-001` (also referenced in the CLI description as `gemini-gemini-embedding-001`).

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1476](#baseline-chunk-1476) | `scripts/embed_chunks.py:1-60` | 0.3361928273531093 | 0.009047619 | 0.03278688524590164 | yes | yes | none (file boundary) | [retrieved chunk 1477](#baseline-chunk-1477) |
| 2 | [1450](#baseline-chunk-1450) | `app/investigation/generation.py:1-60` | 0.35582294726336094 | None | 0.016129032258064516 | no | no | none (file boundary) | [app/investigation/generation.py:51-71](#baseline-context-da287e9758a22061) |
| 3 | [1439](#baseline-chunk-1439) | `app/config.py:1-20` | 0.36842165496281887 | None | 0.015873015873015872 | no | no | none (file boundary) | none (file boundary) |
| 4 | [1477](#baseline-chunk-1477) | `scripts/embed_chunks.py:51-110` | 0.3696827677937491 | None | 0.015625 | yes | yes | [retrieved chunk 1476](#baseline-chunk-1476) | [retrieved chunk 1478](#baseline-chunk-1478) |
| 5 | [1478](#baseline-chunk-1478) | `scripts/embed_chunks.py:101-149` | 0.3859680127905797 | None | 0.015384615384615385 | yes | yes | [retrieved chunk 1477](#baseline-chunk-1477) | none (file boundary) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1570](#experiment-chunk-1570) | `scripts/embed_chunks.py:1-100` | 0.34952385942834463 | 0.009047619 | 0.03252247488101534 | yes | no | none (file boundary) | [retrieved chunk 1571](#experiment-chunk-1571) |
| 2 | [1553](#experiment-chunk-1553) | `app/investigation/generation.py:1-71` | 0.3455308475035963 | None | 0.01639344262295082 | no | no | none (file boundary) | none (file boundary) |
| 3 | [1542](#experiment-chunk-1542) | `app/config.py:1-20` | 0.36842165496281887 | None | 0.015873015873015872 | no | no | none (file boundary) | none (file boundary) |
| 4 | [1577](#experiment-chunk-1577) | `scripts/search_repo.py:1-95` | 0.3788537389175488 | None | 0.015625 | no | no | none (file boundary) | none (file boundary) |
| 5 | [1571](#experiment-chunk-1571) | `scripts/embed_chunks.py:81-149` | 0.38198789988860304 | None | 0.015384615384615385 | yes | no | [retrieved chunk 1570](#experiment-chunk-1570) | none (file boundary) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="direct-04"></a>
<details><summary><strong>direct-04</strong> - What constant controls the minimum RRF score?</summary>

**Category:** `direct`\
**Question:** What constant controls the minimum RRF score?
**Golden relevant label(s):** app/investigation/guard.py: `MIN_ACCEPTABLE_RRF_SCORE = 0.016`\
**Automated must-mention screen (not a human verdict):** (`0.016`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | wrong-or-incomplete | incomplete_or_wrong | False | True | 1458, 1459 | 2785 | 1639 | none |
| 100/20 experiment | 1 | correct | correct_labeled_context | False | True | 1558, 1552 | 4058 | 1560 | none |
| 60/10 baseline | 2 | wrong-or-incomplete | incomplete_or_wrong | False | True | none | 2738 | 1161 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | 1558, 1552 | 4162 | 1517 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `False`; finish `STOP`; wall `1889 ms`; generation `1639 ms`; throttle `0 ms`; tokens `2785`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3439681244766959`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1458`, `1459`. Citation relevance flags: [{'id': '1458', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1459', 'found_in_retrieval_results': True, 'relevant': False}].

> The constant controlling the minimum RRF score is `MIN_ACCEPTABLE_RRF_SCORE`.

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1825 ms`; generation `1560 ms`; throttle `0 ms`; tokens `4058`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.32989309633399`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1558`, `1552`. Citation relevance flags: [{'id': '1558', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1552', 'found_in_retrieval_results': True, 'relevant': False}].

> The constant `MIN_ACCEPTABLE_RRF_SCORE` (set to `0.016` in `app/investigation/guard.py`) controls the minimum RRF score required for evidence sufficiency. Additionally, `MIN_CLEAR_RRF_SCORE` (set to `0.032` in `app/investigation/confidence.py`) is used for confidence calibration regarding clear RRF scores.

**60/10 baseline - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `False`; finish `STOP`; wall `1555 ms`; generation `1161 ms`; throttle `0 ms`; tokens `2738`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3439681244766959`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> The constant `MIN_ACCEPTABLE_RRF_SCORE` controls the minimum RRF score.

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1771 ms`; generation `1517 ms`; throttle `0 ms`; tokens `4162`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.32989309633399`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1558`, `1552`. Citation relevance flags: [{'id': '1558', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1552', 'found_in_retrieval_results': True, 'relevant': False}].

> The constant controlling the minimum acceptable RRF score is `MIN_ACCEPTABLE_RRF_SCORE` (set to `0.016` in `app/investigation/guard.py`). Additionally, `MIN_CLEAR_RRF_SCORE` (set to `0.032` in `app/investigation/confidence.py`) controls the clear RRF score threshold used for confidence calibration.

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1458](#baseline-chunk-1458) | `app/investigation/guard.py:1-60` | 0.3439681244766959 | None | 0.01639344262295082 | yes | no | none (file boundary) | [retrieved chunk 1459](#baseline-chunk-1459) |
| 2 | [1459](#baseline-chunk-1459) | `app/investigation/guard.py:51-70` | 0.3602848721816593 | None | 0.016129032258064516 | yes | no | [retrieved chunk 1458](#baseline-chunk-1458) | none (file boundary) |
| 3 | [1498](#baseline-chunk-1498) | `tests/unit/test_investigation_graph.py:101-155` | 0.38054551322299723 | None | 0.015873015873015872 | no | no | [retrieved chunk 1497](#baseline-chunk-1497) | none (file boundary) |
| 4 | [1473](#baseline-chunk-1473) | `app/retrieval/hybrid_search.py:51-70` | 0.38156839092016237 | None | 0.015625 | no | no | [retrieved chunk 1472](#baseline-chunk-1472) | none (file boundary) |
| 5 | [1504](#baseline-chunk-1504) | `tests/unit/test_investigation_parsing.py:51-95` | 0.391530584056732 | None | 0.015384615384615385 | no | no | [retrieved chunk 1503](#baseline-chunk-1503) | none (file boundary) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1558](#experiment-chunk-1558) | `app/investigation/guard.py:1-70` | 0.32989309633399 | None | 0.01639344262295082 | yes | yes | none (file boundary) | none (file boundary) |
| 2 | [1586](#experiment-chunk-1586) | `tests/unit/test_investigation_graph.py:81-155` | 0.39584401134216296 | None | 0.016129032258064516 | no | no | [retrieved chunk 1585](#experiment-chunk-1585) | none (file boundary) |
| 3 | [1552](#experiment-chunk-1552) | `app/investigation/confidence.py:1-38` | 0.3961618275807508 | None | 0.015873015873015872 | yes | yes | none (file boundary) | none (file boundary) |
| 4 | [1567](#experiment-chunk-1567) | `app/retrieval/hybrid_search.py:1-70` | 0.4282053357271466 | None | 0.015625 | no | no | none (file boundary) | none (file boundary) |
| 5 | [1583](#experiment-chunk-1583) | `tests/unit/test_hybrid_search.py:1-49` | 0.42840166297899396 | None | 0.015384615384615385 | no | no | none (file boundary) | none (file boundary) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="direct-05"></a>
<details><summary><strong>direct-05</strong> - What constant controls the maximum vector distance?</summary>

**Category:** `direct`\
**Question:** What constant controls the maximum vector distance?
**Golden relevant label(s):** app/investigation/guard.py: `MAX_ACCEPTABLE_VECTOR_DISTANCE = 0.5`\
**Automated must-mention screen (not a human verdict):** (`0.5`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | correct | correct_labeled_context | False | True | 1458, 1459 | 2676 | 1209 | none |
| 100/20 experiment | 1 | wrong-or-incomplete | incomplete_or_wrong | False | True | 1558 | 3573 | 1127 | none |
| 60/10 baseline | 2 | correct | correct_labeled_context | False | True | 1458, 1459 | 2665 | 1010 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | 1558 | 3594 | 1193 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1537 ms`; generation `1209 ms`; throttle `0 ms`; tokens `2676`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.4112533923952568`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1458`, `1459`. Citation relevance flags: [{'id': '1458', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1459', 'found_in_retrieval_results': True, 'relevant': False}].

> The constant that controls the maximum vector distance is `MAX_ACCEPTABLE_VECTOR_DISTANCE` (set to `0.5`).

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `False`; finish `STOP`; wall `1373 ms`; generation `1127 ms`; throttle `0 ms`; tokens `3573`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.4112533923952568`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1558`. Citation relevance flags: [{'id': '1558', 'found_in_retrieval_results': True, 'relevant': True}].

> The constant `MAX_ACCEPTABLE_VECTOR_DISTANCE` controls the maximum vector distance.

**60/10 baseline - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1328 ms`; generation `1010 ms`; throttle `0 ms`; tokens `2665`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.4112533923952568`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1458`, `1459`. Citation relevance flags: [{'id': '1458', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1459', 'found_in_retrieval_results': True, 'relevant': False}].

> The constant controlling the maximum acceptable vector distance is `MAX_ACCEPTABLE_VECTOR_DISTANCE`, which is set to `0.5` in `app/investigation/guard.py`.

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1455 ms`; generation `1193 ms`; throttle `0 ms`; tokens `3594`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.4112533923952568`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1558`. Citation relevance flags: [{'id': '1558', 'found_in_retrieval_results': True, 'relevant': True}].

> The constant `MAX_ACCEPTABLE_VECTOR_DISTANCE` controls the maximum vector distance (set to `0.5`).

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1474](#baseline-chunk-1474) | `app/retrieval/vector_search.py:1-56` | 0.4112533923952568 | None | 0.01639344262295082 | no | no | none (file boundary) | none (file boundary) |
| 2 | [1492](#baseline-chunk-1492) | `tests/unit/test_db_models.py:1-33` | 0.4412972996360123 | None | 0.016129032258064516 | no | no | none (file boundary) | none (file boundary) |
| 3 | [1458](#baseline-chunk-1458) | `app/investigation/guard.py:1-60` | 0.4439173837928364 | None | 0.015873015873015872 | yes | yes | none (file boundary) | [retrieved chunk 1459](#baseline-chunk-1459) |
| 4 | [1459](#baseline-chunk-1459) | `app/investigation/guard.py:51-70` | 0.44403404860828477 | None | 0.015625 | yes | yes | [retrieved chunk 1458](#baseline-chunk-1458) | none (file boundary) |
| 5 | [1498](#baseline-chunk-1498) | `tests/unit/test_investigation_graph.py:101-155` | 0.45569828205221385 | None | 0.015384615384615385 | no | no | [retrieved chunk 1497](#baseline-chunk-1497) | none (file boundary) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1568](#experiment-chunk-1568) | `app/retrieval/vector_search.py:1-56` | 0.4112533923952568 | None | 0.01639344262295082 | no | no | none (file boundary) | none (file boundary) |
| 2 | [1558](#experiment-chunk-1558) | `app/investigation/guard.py:1-70` | 0.4409762712313079 | None | 0.016129032258064516 | yes | yes | none (file boundary) | none (file boundary) |
| 3 | [1581](#experiment-chunk-1581) | `tests/unit/test_db_models.py:1-33` | 0.4412972996360123 | None | 0.015873015873015872 | no | no | none (file boundary) | none (file boundary) |
| 4 | [1586](#experiment-chunk-1586) | `tests/unit/test_investigation_graph.py:81-155` | 0.4569356676702051 | None | 0.015625 | no | no | [retrieved chunk 1585](#experiment-chunk-1585) | none (file boundary) |
| 5 | [1585](#experiment-chunk-1585) | `tests/unit/test_investigation_graph.py:1-100` | 0.4575406918999796 | None | 0.015384615384615385 | no | no | none (file boundary) | [retrieved chunk 1586](#experiment-chunk-1586) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="direct-06"></a>
<details><summary><strong>direct-06</strong> - What is the high-confidence RRF calibration margin?</summary>

**Category:** `direct`\
**Question:** What is the high-confidence RRF calibration margin?
**Golden relevant label(s):** app/investigation/confidence.py: `MIN_CLEAR_RRF_SCORE = 0.032`\
**Automated must-mention screen (not a human verdict):** (`0.032`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | correct | correct_labeled_context | False | True | 1449 | 2869 | 1097 | none |
| 100/20 experiment | 1 | correct | correct_labeled_context | False | True | 1552 | 4368 | 1452 | none |
| 60/10 baseline | 2 | correct | correct_labeled_context | False | True | 1449 | 2909 | 1348 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | 1552 | 4361 | 1540 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1382 ms`; generation `1097 ms`; throttle `0 ms`; tokens `2869`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.35403200784661604`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1449`. Citation relevance flags: [{'id': '1449', 'found_in_retrieval_results': True, 'relevant': True}].

> The high-confidence RRF calibration margin is defined by `MIN_CLEAR_RRF_SCORE = 0.032` in `app/investigation/confidence.py`.

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1719 ms`; generation `1452 ms`; throttle `0 ms`; tokens `4368`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.35403200784661604`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1552`. Citation relevance flags: [{'id': '1552', 'found_in_retrieval_results': True, 'relevant': True}].

> The high-confidence RRF calibration margin is defined as `MIN_CLEAR_RRF_SCORE = 0.032` in `app/investigation/confidence.py`.

**60/10 baseline - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1688 ms`; generation `1348 ms`; throttle `0 ms`; tokens `2909`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.35403200784661604`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1449`. Citation relevance flags: [{'id': '1449', 'found_in_retrieval_results': True, 'relevant': True}].

> The high-confidence RRF calibration margin is defined as `MIN_CLEAR_RRF_SCORE = 0.032` in `app/investigation/confidence.py`.

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1772 ms`; generation `1540 ms`; throttle `0 ms`; tokens `4361`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.35403200784661604`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1552`. Citation relevance flags: [{'id': '1552', 'found_in_retrieval_results': True, 'relevant': True}].

> The high-confidence RRF calibration margin is defined as `MIN_CLEAR_RRF_SCORE = 0.032` in `app/investigation/confidence.py`.

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1449](#baseline-chunk-1449) | `app/investigation/confidence.py:1-38` | 0.35403200784661604 | None | 0.01639344262295082 | yes | yes | none (file boundary) | none (file boundary) |
| 2 | [1498](#baseline-chunk-1498) | `tests/unit/test_investigation_graph.py:101-155` | 0.3740861022348442 | None | 0.016129032258064516 | no | no | [retrieved chunk 1497](#baseline-chunk-1497) | none (file boundary) |
| 3 | [1458](#baseline-chunk-1458) | `app/investigation/guard.py:1-60` | 0.3894888401883513 | None | 0.015873015873015872 | no | no | none (file boundary) | [retrieved chunk 1459](#baseline-chunk-1459) |
| 4 | [1459](#baseline-chunk-1459) | `app/investigation/guard.py:51-70` | 0.40065406735420284 | None | 0.015625 | no | no | [retrieved chunk 1458](#baseline-chunk-1458) | none (file boundary) |
| 5 | [1496](#baseline-chunk-1496) | `tests/unit/test_investigation_graph.py:1-60` | 0.401613331834374 | None | 0.015384615384615385 | no | no | none (file boundary) | [retrieved chunk 1497](#baseline-chunk-1497) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1552](#experiment-chunk-1552) | `app/investigation/confidence.py:1-38` | 0.35403200784661604 | None | 0.01639344262295082 | yes | yes | none (file boundary) | none (file boundary) |
| 2 | [1558](#experiment-chunk-1558) | `app/investigation/guard.py:1-70` | 0.3718804152797921 | None | 0.016129032258064516 | no | no | none (file boundary) | none (file boundary) |
| 3 | [1586](#experiment-chunk-1586) | `tests/unit/test_investigation_graph.py:81-155` | 0.3812976420869302 | None | 0.015873015873015872 | no | no | [retrieved chunk 1585](#experiment-chunk-1585) | none (file boundary) |
| 4 | [1554](#experiment-chunk-1554) | `app/investigation/graph.py:1-100` | 0.42453417774308944 | None | 0.015625 | no | no | none (file boundary) | [retrieved chunk 1555](#experiment-chunk-1555) |
| 5 | [1555](#experiment-chunk-1555) | `app/investigation/graph.py:81-180` | 0.42490374640750506 | None | 0.015384615384615385 | no | no | [retrieved chunk 1554](#experiment-chunk-1554) | [retrieved chunk 1556](#experiment-chunk-1556) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="direct-07"></a>
<details><summary><strong>direct-07</strong> - Which MCP server class is instantiated?</summary>

**Category:** `direct`\
**Question:** Which MCP server class is instantiated?
**Golden relevant label(s):** app/investigation/mcp_server.py: `server = FastMCP`\
**Automated must-mention screen (not a human verdict):** (`FastMCP`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | correct | correct_labeled_context | False | True | 1460, 1462 | 2750 | 1386 | none |
| 100/20 experiment | 1 | correct | correct_labeled_context | False | True | 1559, 1560 | 2727 | 1199 | none |
| 60/10 baseline | 2 | correct | correct_labeled_context | False | True | 1460, 1462 | 2750 | 1189 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | none | 2716 | 1214 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1729 ms`; generation `1386 ms`; throttle `0 ms`; tokens `2750`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3479594526627605`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1460`, `1462`. Citation relevance flags: [{'id': '1460', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1462', 'found_in_retrieval_results': True, 'relevant': False}].

> The `FastMCP` class is instantiated to create the MCP server (`server = FastMCP("IncidentWeave local investigation tools")`).

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1487 ms`; generation `1199 ms`; throttle `0 ms`; tokens `2727`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.34085856748421917`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1559`, `1560`. Citation relevance flags: [{'id': '1559', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1560', 'found_in_retrieval_results': True, 'relevant': False}].

> The MCP server class instantiated is `FastMCP`.

**60/10 baseline - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1460 ms`; generation `1189 ms`; throttle `0 ms`; tokens `2750`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3479594526627605`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1460`, `1462`. Citation relevance flags: [{'id': '1460', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1462', 'found_in_retrieval_results': True, 'relevant': False}].

> The `FastMCP` class is instantiated to create the MCP server (`server = FastMCP("IncidentWeave local investigation tools")`).

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1514 ms`; generation `1214 ms`; throttle `0 ms`; tokens `2716`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.34085856748421917`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> The FastMCP class (`FastMCP`) is instantiated to create the MCP server instance (`server = FastMCP("IncidentWeave local investigation tools")`).

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1460](#baseline-chunk-1460) | `app/investigation/mcp_server.py:1-60` | 0.3479594526627605 | None | 0.01639344262295082 | yes | yes | none (file boundary) | [retrieved chunk 1461](#baseline-chunk-1461) |
| 2 | [1453](#baseline-chunk-1453) | `app/investigation/graph.py:51-110` | 0.415727064842386 | None | 0.016129032258064516 | no | no | [retrieved chunk 1452](#baseline-chunk-1452) | [retrieved chunk 1454](#baseline-chunk-1454) |
| 3 | [1462](#baseline-chunk-1462) | `app/investigation/mcp_server.py:101-131` | 0.4168694795583202 | None | 0.015873015873015872 | yes | yes | [retrieved chunk 1461](#baseline-chunk-1461) | none (file boundary) |
| 4 | [1452](#baseline-chunk-1452) | `app/investigation/graph.py:1-60` | 0.4459846547733578 | None | 0.015625 | no | no | none (file boundary) | [retrieved chunk 1453](#baseline-chunk-1453) |
| 5 | [1507](#baseline-chunk-1507) | `tests/unit/test_investigation_persistence.py:101-120` | 0.45522670864213954 | None | 0.015384615384615385 | no | no | [retrieved chunk 1506](#baseline-chunk-1506) | none (file boundary) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1559](#experiment-chunk-1559) | `app/investigation/mcp_server.py:1-100` | 0.34085856748421917 | None | 0.01639344262295082 | yes | no | none (file boundary) | [retrieved chunk 1560](#experiment-chunk-1560) |
| 2 | [1560](#experiment-chunk-1560) | `app/investigation/mcp_server.py:81-131` | 0.3738937161236239 | None | 0.016129032258064516 | yes | no | [retrieved chunk 1559](#experiment-chunk-1559) | none (file boundary) |
| 3 | [1556](#experiment-chunk-1556) | `app/investigation/graph.py:161-260` | 0.45599274412169266 | None | 0.015873015873015872 | no | no | [retrieved chunk 1555](#experiment-chunk-1555) | [app/investigation/graph.py:241-273](#experiment-context-6e7fbcc3f9f32261) |
| 4 | [1543](#experiment-chunk-1543) | `app/db/__init__.py:1-1` | 0.45688269407159965 | None | 0.015625 | no | no | none (file boundary) | none (file boundary) |
| 5 | [1541](#experiment-chunk-1541) | `app/__init__.py:1-1` | 0.4641822900029251 | None | 0.015384615384615385 | no | no | none (file boundary) | none (file boundary) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="direct-08"></a>
<details><summary><strong>direct-08</strong> - Where is the final confidence passed into persistence?</summary>

**Category:** `direct`\
**Question:** Where is the final confidence passed into persistence?
**Golden relevant label(s):** scripts/investigate.py: `final_confidence=result["confidence"]`\
**Automated must-mention screen (not a human verdict):** (`final_confidence`) AND (`confidence`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | wrong-or-incomplete | retrieval_miss_abstained | False | True | none | 2996 | 1247 | none |
| 100/20 experiment | 1 | correct | correct_labeled_context | False | True | 1592, 1575 | 4722 | 1419 | none |
| 60/10 baseline | 2 | wrong-or-incomplete | retrieval_miss_abstained | False | True | none | 2996 | 1065 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | 1575 | 4688 | 2332 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1582 ms`; generation `1247 ms`; throttle `0 ms`; tokens `2996`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3555490021205523`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1663 ms`; generation `1419 ms`; throttle `0 ms`; tokens `4722`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.36738245943262304`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1592`, `1575`. Citation relevance flags: [{'id': '1592', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1575', 'found_in_retrieval_results': True, 'relevant': True}].

> The final confidence is passed into persistence via `final_confidence=result["confidence"]` (or explicitly as `final_confidence="medium"` in unit tests) when calling `persist_investigation`.

**60/10 baseline - pass-2** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1366 ms`; generation `1065 ms`; throttle `0 ms`; tokens `2996`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3555490021205523`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `2607 ms`; generation `2332 ms`; throttle `0 ms`; tokens `4688`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.36738245943262304`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1575`. Citation relevance flags: [{'id': '1575', 'found_in_retrieval_results': True, 'relevant': True}].

> The final confidence is passed into persistence via the `final_confidence` parameter in `persist_investigation(...)`. For example, in tests it is passed explicitly (e.g., `final_confidence="medium"`), and in `scripts/investigate.py`, it is passed as `final_confidence=result["confidence"]`.

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1496](#baseline-chunk-1496) | `tests/unit/test_investigation_graph.py:1-60` | 0.3555490021205523 | None | 0.01639344262295082 | no | no | none (file boundary) | [retrieved chunk 1497](#baseline-chunk-1497) |
| 2 | [1506](#baseline-chunk-1506) | `tests/unit/test_investigation_persistence.py:51-110` | 0.37536075993178764 | None | 0.016129032258064516 | no | no | [tests/unit/test_investigation_persistence.py:1-60](#baseline-context-91193a850a6b0918) | [retrieved chunk 1507](#baseline-chunk-1507) |
| 3 | [1499](#baseline-chunk-1499) | `tests/unit/test_investigation_mcp_tools.py:1-60` | 0.3765043852344785 | None | 0.015873015873015872 | no | no | none (file boundary) | [retrieved chunk 1500](#baseline-chunk-1500) |
| 4 | [1498](#baseline-chunk-1498) | `tests/unit/test_investigation_graph.py:101-155` | 0.37769532574133313 | None | 0.015625 | no | no | [retrieved chunk 1497](#baseline-chunk-1497) | none (file boundary) |
| 5 | [1507](#baseline-chunk-1507) | `tests/unit/test_investigation_persistence.py:101-120` | 0.38695906307630723 | None | 0.015384615384615385 | no | no | [retrieved chunk 1506](#baseline-chunk-1506) | none (file boundary) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1592](#experiment-chunk-1592) | `tests/unit/test_investigation_persistence.py:81-120` | 0.36738245943262304 | None | 0.01639344262295082 | yes | no | [retrieved chunk 1591](#experiment-chunk-1591) | none (file boundary) |
| 2 | [1586](#experiment-chunk-1586) | `tests/unit/test_investigation_graph.py:81-155` | 0.3751551350543436 | None | 0.016129032258064516 | no | no | [retrieved chunk 1585](#experiment-chunk-1585) | none (file boundary) |
| 3 | [1554](#experiment-chunk-1554) | `app/investigation/graph.py:1-100` | 0.37936906550009186 | None | 0.015873015873015872 | no | no | none (file boundary) | [retrieved chunk 1555](#experiment-chunk-1555) |
| 4 | [1575](#experiment-chunk-1575) | `scripts/investigate.py:81-180` | 0.3816250670769157 | None | 0.015625 | yes | yes | [retrieved chunk 1574](#experiment-chunk-1574) | [scripts/investigate.py:161-186](#experiment-context-fbbc24cd3500764e) |
| 5 | [1585](#experiment-chunk-1585) | `tests/unit/test_investigation_graph.py:1-100` | 0.38360431030656894 | None | 0.015384615384615385 | no | no | none (file boundary) | [retrieved chunk 1586](#experiment-chunk-1586) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="paraphrased-01"></a>
<details><summary><strong>paraphrased-01</strong> - How does the database layer establish non-blocking connections and create request-scoped objects?</summary>

**Category:** `paraphrased`\
**Question:** How does the database layer establish non-blocking connections and create request-scoped objects?
**Golden relevant label(s):** app/db/session.py: `create_async_engine`\
**Automated must-mention screen (not a human verdict):** (`async`) AND (`engine`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | correct | correct_labeled_context | False | True | 1447 | 2374 | 1373 | none |
| 100/20 experiment | 1 | correct | correct_labeled_context | False | True | 1550 | 3210 | 1412 | none |
| 60/10 baseline | 2 | correct | correct_labeled_context | False | True | 1447 | 2384 | 1194 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | 1550 | 3203 | 1695 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1719 ms`; generation `1373 ms`; throttle `0 ms`; tokens `2374`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.35360602386405293`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1447`. Citation relevance flags: [{'id': '1447', 'found_in_retrieval_results': True, 'relevant': True}].

> The database layer establishes non-blocking connections using SQLAlchemy's `create_async_engine` with a converted PostgreSQL URL (`postgresql+psycopg://`) and `pool_pre_ping=True`, while registering pgvector types asynchronously on connection events. It creates request-scoped objects (sessions) using an `async_sessionmaker` configured with `AsyncSession` and `expire_on_commit=False`, which are yielded as async generators via `get_db_session()`.

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1648 ms`; generation `1412 ms`; throttle `0 ms`; tokens `3210`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.35360602386405293`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1550`. Citation relevance flags: [{'id': '1550', 'found_in_retrieval_results': True, 'relevant': True}].

> The database layer establishes non-blocking connections using SQLAlchemy's `create_async_engine` with a URL converted to the `psycopg` async dialect via `_async_database_url()` and `pool_pre_ping=True`. Additionally, `pgvector` types are registered for each async connection using an event listener on `engine.sync_engine` that calls `dbapi_connection.run_async(register_vector_async)`. Request-scoped objects (specifically asynchronous database sessions) are created using `async_sessionmaker` bound to the engine (`AsyncSessionLocal`), which are yielded as request-scoped sessions through the asynchronous generator function `get_db_session()`.

**60/10 baseline - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1443 ms`; generation `1194 ms`; throttle `0 ms`; tokens `2384`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.35360602386405293`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1447`. Citation relevance flags: [{'id': '1447', 'found_in_retrieval_results': True, 'relevant': True}].

> The database layer establishes non-blocking connections by using SQLAlchemy's `create_async_engine` with a URL converted to the `postgresql+psycopg` async dialect (via `_async_database_url`) and `pool_pre_ping=True`. Request-scoped database sessions are created using `async_sessionmaker` bound to this engine (configured as `AsyncSessionLocal`), and the asynchronous generator `get_db_session` yields an `AsyncSession` context manager instance (`async with AsyncSessionLocal() as session:`).

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1942 ms`; generation `1695 ms`; throttle `0 ms`; tokens `3203`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.35360602386405293`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1550`. Citation relevance flags: [{'id': '1550', 'found_in_retrieval_results': True, 'relevant': True}].

> The database layer establishes non-blocking connections using SQLAlchemy's `create_async_engine` with a URL converted to the psycopg async dialect (`postgresql+psycopg://`), along with `pool_pre_ping=True` and an event listener that registers pgvector types asynchronously via `dbapi_connection.run_async(register_vector_async)`. It creates request-scoped objects (specifically asynchronous database sessions) using an `async_sessionmaker` named `AsyncSessionLocal` bound to the engine, with `expire_on_commit=False`, which are yielded as an `AsyncSession` via the `get_db_session()` asynchronous generator function using an `async with` context manager.

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1447](#baseline-chunk-1447) | `app/db/session.py:1-46` | 0.35360602386405293 | None | 0.01639344262295082 | yes | yes | none (file boundary) | none (file boundary) |
| 2 | [1440](#baseline-chunk-1440) | `app/db/__init__.py:1-1` | 0.3635121858856949 | None | 0.016129032258064516 | no | no | none (file boundary) | none (file boundary) |
| 3 | [1489](#baseline-chunk-1489) | `tests/integration/test_database.py:1-60` | 0.39793298048595005 | None | 0.015873015873015872 | no | no | none (file boundary) | [retrieved chunk 1490](#baseline-chunk-1490) |
| 4 | [1490](#baseline-chunk-1490) | `tests/integration/test_database.py:51-87` | 0.4257619101994681 | None | 0.015625 | no | no | [retrieved chunk 1489](#baseline-chunk-1489) | none (file boundary) |
| 5 | [1506](#baseline-chunk-1506) | `tests/unit/test_investigation_persistence.py:51-110` | 0.44030516793910257 | None | 0.015384615384615385 | no | no | [tests/unit/test_investigation_persistence.py:1-60](#baseline-context-91193a850a6b0918) | [retrieved chunk 1507](#baseline-chunk-1507) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1550](#experiment-chunk-1550) | `app/db/session.py:1-46` | 0.35360602386405293 | None | 0.01639344262295082 | yes | yes | none (file boundary) | none (file boundary) |
| 2 | [1543](#experiment-chunk-1543) | `app/db/__init__.py:1-1` | 0.3635121858856949 | None | 0.016129032258064516 | no | no | none (file boundary) | none (file boundary) |
| 3 | [1579](#experiment-chunk-1579) | `tests/integration/test_database.py:1-87` | 0.39702118459086344 | None | 0.015873015873015872 | no | no | none (file boundary) | none (file boundary) |
| 4 | [1592](#experiment-chunk-1592) | `tests/unit/test_investigation_persistence.py:81-120` | 0.44348768446060693 | None | 0.015625 | no | no | [retrieved chunk 1591](#experiment-chunk-1591) | none (file boundary) |
| 5 | [1554](#experiment-chunk-1554) | `app/investigation/graph.py:1-100` | 0.4475157991394807 | None | 0.015384615384615385 | no | no | none (file boundary) | [retrieved chunk 1555](#experiment-chunk-1555) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="paraphrased-02"></a>
<details><summary><strong>paraphrased-02</strong> - How are source files divided into overlapping pieces for indexing?</summary>

**Category:** `paraphrased`\
**Question:** How are source files divided into overlapping pieces for indexing?
**Golden relevant label(s):** scripts/ingest_repo.py: `OVERLAP_SIZE = 10`\
**Automated must-mention screen (not a human verdict):** (`overlap`) AND (`10`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | correct | correct_labeled_context | False | True | 1480, 1479, 1481 | 2905 | 2447 | none |
| 100/20 experiment | 1 | correct | correct_labeled_context | False | True | 1572, 1573 | 4190 | 2298 | none |
| 60/10 baseline | 2 | correct | correct_labeled_context | False | True | 1480, 1479, 1481 | 2895 | 1455 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | 1572, 1584, 1573 | 4256 | 2062 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `2831 ms`; generation `2447 ms`; throttle `0 ms`; tokens `2905`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.31996245383725896`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1480`, `1479`, `1481`. Citation relevance flags: [{'id': '1480', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1479', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1481', 'found_in_retrieval_results': True, 'relevant': False}].

> Source files are divided into overlapping pieces for indexing using the `chunk_lines` function in `scripts/ingest_repo.py`. This function takes a list of lines, a `chunk_size` (defaulting to 60), and an `overlap` size (defaulting to 10). It calculates a step size (`chunk_size - overlap`) and iterates through the lines using `range(0, len(lines), step)` to yield overlapping start and end index windows for each chunk, provided that each new window adds at least one new line beyond the prior window (`end_index > previous_end`).

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `2579 ms`; generation `2298 ms`; throttle `0 ms`; tokens `4190`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3565466628165569`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1572`, `1573`. Citation relevance flags: [{'id': '1572', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1573', 'found_in_retrieval_results': True, 'relevant': False}].

> Source files are divided into overlapping pieces for indexing using the `chunk_lines` function defined in `scripts/ingest_repo.py`.\
> - By default, files are split into windows using a `CHUNK_SIZE` of 60 lines and an `OVERLAP_SIZE` of 10 lines.
> - The step size between windows is calculated as `chunk_size - overlap` (which defaults to 50 lines).
> - Windows are yielded starting at index 0 up to the total number of lines, ensuring that each new window adds at least one new line beyond the prior window (`end_index > previous_end`).\
> - Empty chunk contents or non-redundant windows where `end_index <= previous_end` are skipped.

**60/10 baseline - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1746 ms`; generation `1455 ms`; throttle `0 ms`; tokens `2895`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.31996245383725896`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1480`, `1479`, `1481`. Citation relevance flags: [{'id': '1480', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1479', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1481', 'found_in_retrieval_results': True, 'relevant': False}].

> Source files are divided into overlapping pieces for indexing using the `chunk_lines` function in `scripts/ingest_repo.py`. It uses a default `CHUNK_SIZE` of 60 and an `OVERLAP_SIZE` of 10 to calculate a step size (`chunk_size - overlap`), then loops through the file's lines from `0` to `len(lines)` with that step size to yield non-redundant overlapping windows defined by `(start_index, end_index)`.

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `2347 ms`; generation `2062 ms`; throttle `0 ms`; tokens `4256`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3565466628165569`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1572`, `1584`, `1573`. Citation relevance flags: [{'id': '1572', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1584', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1573', 'found_in_retrieval_results': True, 'relevant': False}].

> Source files (specifically Python files) are divided into overlapping pieces for indexing using the `chunk_lines` function defined in `scripts/ingest_repo.py`.\
>\
> The segmentation process works as follows:
> - It uses a defined `CHUNK_SIZE` of 60 lines and an `OVERLAP_SIZE` of 10 lines.
> - The step size between windows is calculated as `step = chunk_size - overlap` (which defaults to 50 lines).
> - Windows are yielded over the file's lines using `range(0, len(lines), step)`, where each window spans from `start_index` to `min(start_index + chunk_size, len(lines))`.
> - Windows are only yielded (and `previous_end` is updated) when they add at least one new line beyond the prior window (`end_index > previous_end`), preventing redundant or non-advancing windows.
> - Empty chunk contents are filtered out during ingestion before creating `Chunk` records.

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1480](#baseline-chunk-1480) | `scripts/ingest_repo.py:51-110` | 0.31996245383725896 | None | 0.01639344262295082 | yes | yes | [retrieved chunk 1479](#baseline-chunk-1479) | [retrieved chunk 1481](#baseline-chunk-1481) |
| 2 | [1479](#baseline-chunk-1479) | `scripts/ingest_repo.py:1-60` | 0.3422917425514378 | None | 0.016129032258064516 | yes | yes | none (file boundary) | [retrieved chunk 1480](#baseline-chunk-1480) |
| 3 | [1495](#baseline-chunk-1495) | `tests/unit/test_ingest_repo.py:1-20` | 0.3775762191191494 | None | 0.015873015873015872 | no | no | none (file boundary) | none (file boundary) |
| 4 | [1481](#baseline-chunk-1481) | `scripts/ingest_repo.py:101-158` | 0.39120174212374714 | None | 0.015625 | yes | yes | [retrieved chunk 1480](#baseline-chunk-1480) | none (file boundary) |
| 5 | [1500](#baseline-chunk-1500) | `tests/unit/test_investigation_mcp_tools.py:51-110` | 0.3970601613934096 | None | 0.015384615384615385 | no | no | [retrieved chunk 1499](#baseline-chunk-1499) | [retrieved chunk 1501](#baseline-chunk-1501) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1572](#experiment-chunk-1572) | `scripts/ingest_repo.py:1-100` | 0.3565466628165569 | None | 0.01639344262295082 | yes | yes | none (file boundary) | [retrieved chunk 1573](#experiment-chunk-1573) |
| 2 | [1584](#experiment-chunk-1584) | `tests/unit/test_ingest_repo.py:1-20` | 0.3775762191191494 | None | 0.016129032258064516 | no | yes | none (file boundary) | none (file boundary) |
| 3 | [1547](#experiment-chunk-1547) | `app/db/models/chunk.py:1-52` | 0.39989613675460634 | None | 0.015873015873015872 | no | no | none (file boundary) | none (file boundary) |
| 4 | [1588](#experiment-chunk-1588) | `tests/unit/test_investigation_mcp_tools.py:81-180` | 0.4057460109353167 | None | 0.015625 | no | no | [retrieved chunk 1587](#experiment-chunk-1587) | [retrieved chunk 1589](#experiment-chunk-1589) |
| 5 | [1573](#experiment-chunk-1573) | `scripts/ingest_repo.py:81-158` | 0.4088075173358233 | None | 0.015384615384615385 | yes | yes | [retrieved chunk 1572](#experiment-chunk-1572) | none (file boundary) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="paraphrased-03"></a>
<details><summary><strong>paraphrased-03</strong> - How does the project turn text into numeric vectors before storage?</summary>

**Category:** `paraphrased`\
**Question:** How does the project turn text into numeric vectors before storage?
**Golden relevant label(s):** scripts/embed_chunks.py: `outputDimensionality`\
**Automated must-mention screen (not a human verdict):** (`768`) AND (`embedding`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | correct | correct_unlabeled_context | False | True | 1477 | 3095 | 1396 | none |
| 100/20 experiment | 1 | correct | correct_labeled_context | False | True | 1570 | 2869 | 1581 | none |
| 60/10 baseline | 2 | correct | correct_unlabeled_context | False | True | 1477, 1444, 1492 | 3243 | 1510 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | 1570 | 2870 | 1433 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1671 ms`; generation `1396 ms`; throttle `0 ms`; tokens `3095`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.41252604745737387`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1477`. Citation relevance flags: [{'id': '1477', 'found_in_retrieval_results': True, 'relevant': False}].

> The project embeds repository chunk text using an external Gemini API request (via `scripts/embed_chunks.py`), parses the JSON response to extract the embedding values, validates that the values form a list of length equal to `EMBEDDING_DIMENSION` (768), converts each value to a float, and assigns the resulting list to `chunk.embedding = embed_text(chunk.content)` before persisting it in the database.

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1848 ms`; generation `1581 ms`; throttle `0 ms`; tokens `2869`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.41669062968022885`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1570`. Citation relevance flags: [{'id': '1570', 'found_in_retrieval_results': True, 'relevant': True}].

> The project turns text into numeric vectors by calling the Gemini embeddings API (`models/gemini-embedding-001`) via the `embed_text` function in `scripts/embed_chunks.py`. This function sends an HTTP POST request with the text content, model name, and an output dimensionality of 768, and returns the resulting list of floating-point values from the API response.

**60/10 baseline - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1813 ms`; generation `1510 ms`; throttle `0 ms`; tokens `3243`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.41252604745737387`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1477`, `1444`, `1492`. Citation relevance flags: [{'id': '1477', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1444', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1492', 'found_in_retrieval_results': True, 'relevant': False}].

> The project embeds repository chunks by sending an HTTP POST request to the Gemini API (using `scripts/embed_chunks.py`), parsing the response JSON to extract the `"embedding"` values list, validating that the dimension matches `EMBEDDING_DIMENSION`, converting each value to a float, and assigning the resulting list of floats to `chunk.embedding` before saving it to the database where it is stored in a `VECTOR(768)` column.

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1670 ms`; generation `1433 ms`; throttle `0 ms`; tokens `2870`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.41669062968022885`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1570`. Citation relevance flags: [{'id': '1570', 'found_in_retrieval_results': True, 'relevant': True}].

> The project turns text into numeric vectors before storage by calling the Gemini embeddings API (`models/gemini-embedding-001`) via the `embed_text` function in `scripts/embed_chunks.py`. This function sends a POST request with the text payload and output dimensionality of 768 to the Gemini API endpoint, parses the returned embedding values into a list of floats, and assigns them to the `chunk.embedding` attribute.

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1477](#baseline-chunk-1477) | `scripts/embed_chunks.py:51-110` | 0.41252604745737387 | None | 0.01639344262295082 | yes | yes | [retrieved chunk 1476](#baseline-chunk-1476) | [retrieved chunk 1478](#baseline-chunk-1478) |
| 2 | [1444](#baseline-chunk-1444) | `app/db/models/chunk.py:1-52` | 0.41669062968022885 | None | 0.016129032258064516 | no | yes | none (file boundary) | none (file boundary) |
| 3 | [1492](#baseline-chunk-1492) | `tests/unit/test_db_models.py:1-33` | 0.4289963690699605 | None | 0.015873015873015872 | no | yes | none (file boundary) | none (file boundary) |
| 4 | [1474](#baseline-chunk-1474) | `app/retrieval/vector_search.py:1-56` | 0.4325519398792852 | None | 0.015625 | no | no | none (file boundary) | none (file boundary) |
| 5 | [1455](#baseline-chunk-1455) | `app/investigation/graph.py:151-210` | 0.43661535737009183 | None | 0.015384615384615385 | no | no | [retrieved chunk 1454](#baseline-chunk-1454) | [app/investigation/graph.py:201-260](#baseline-context-d3469f915cc50c2d) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1547](#experiment-chunk-1547) | `app/db/models/chunk.py:1-52` | 0.41669062968022885 | None | 0.01639344262295082 | no | no | none (file boundary) | none (file boundary) |
| 2 | [1570](#experiment-chunk-1570) | `scripts/embed_chunks.py:1-100` | 0.42555257357927745 | None | 0.016129032258064516 | yes | yes | none (file boundary) | [retrieved chunk 1571](#experiment-chunk-1571) |
| 3 | [1581](#experiment-chunk-1581) | `tests/unit/test_db_models.py:1-33` | 0.4289963690699605 | None | 0.015873015873015872 | no | no | none (file boundary) | none (file boundary) |
| 4 | [1568](#experiment-chunk-1568) | `app/retrieval/vector_search.py:1-56` | 0.4325519398792852 | None | 0.015625 | no | no | none (file boundary) | none (file boundary) |
| 5 | [1543](#experiment-chunk-1543) | `app/db/__init__.py:1-1` | 0.4409951739494148 | None | 0.015384615384615385 | no | no | none (file boundary) | none (file boundary) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="paraphrased-04"></a>
<details><summary><strong>paraphrased-04</strong> - How are two independent search rankings combined into one ordered result?</summary>

**Category:** `paraphrased`\
**Question:** How are two independent search rankings combined into one ordered result?
**Golden relevant label(s):** app/retrieval/hybrid_search.py: `rrf_score += 1 / (60 +`\
**Automated must-mention screen (not a human verdict):** (`rank`) AND (`RRF`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | correct | correct_labeled_context | False | True | 1473, 1494, 1472 | 3199 | 2004 | none |
| 100/20 experiment | 1 | correct | correct_labeled_context | False | True | none | 4201 | 1755 | none |
| 60/10 baseline | 2 | correct | correct_labeled_context | False | True | 1473, 1494, 1472 | 3160 | 2166 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | none | 4207 | 1532 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `2309 ms`; generation `2004 ms`; throttle `0 ms`; tokens `3199`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.36212025647838564`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1473`, `1494`, `1472`. Citation relevance flags: [{'id': '1473', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1494', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1472', 'found_in_retrieval_results': True, 'relevant': True}].

> Two independent search rankings (vector search results and full-text search results) are combined into one ordered result using reciprocal rank fusion (RRF) in the `hybrid_search` function (`app/retrieval/hybrid_search.py`).\
>\
> The combination process works as follows:
> 1. Vector search and full-text search are performed independently to retrieve result lists up to the specified limit.
> 2. The ranks for each result ID in the vector and full-text search results are determined (where rank is index + 1).
> 3. The union of candidate IDs from both search methods is collected.
> 4. For each candidate ID, an `rrf_score` is computed by summing reciprocal rank terms: $1 / (60 + \text{vector\_rank})$ (if present in vector results) and $1 / (60 + \text{fts\_rank})$ (if present in FTS results).
> 5. The combined results are sorted in descending order based on their `rrf_score`, and the top results up to the limit are returned.

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `2007 ms`; generation `1755 ms`; throttle `0 ms`; tokens `4201`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3654755565959501`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> Two independent search rankings (vector search and full-text search) are combined into one ordered result using Reciprocal Rank Fusion (RRF) in the `hybrid_search` function. Specifically, it computes ranks from the `vector_results` and `fts_results` lists (using 1-based indexing), aggregates candidate chunk IDs, calculates an `rrf_score` for each candidate by summing $1 / (60 + \text{rank})$ for each search method where the chunk appears, sorts the fused results in descending order by `rrf_score`, and returns up to the specified `limit`.

**60/10 baseline - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `2435 ms`; generation `2166 ms`; throttle `0 ms`; tokens `3160`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.36212025647838564`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1473`, `1494`, `1472`. Citation relevance flags: [{'id': '1473', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1494', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1472', 'found_in_retrieval_results': True, 'relevant': True}].

> Two independent search rankings (vector search and full-text search) are combined into one ordered result using reciprocal rank fusion (RRF). Specifically:
> 1. The `hybrid_search` function performs both a vector search (`search_vector`) and a full-text search (`search_fulltext`).
> 2. It maps the results of each search to determine the rank (starting from 1) of each chunk ID in both lists (`vector_rank_by_id` and `fts_rank_by_id`).
> 3. It collects all unique candidate chunk IDs from both searches and calculates an `rrf_score` for each candidate by summing $1 / (60 + \text{rank})$ for whichever ranking lists contain that chunk ID.
> 4. Finally, the fused results are sorted in descending order based on their `rrf_score` and truncated to the specified `limit`.

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1809 ms`; generation `1532 ms`; throttle `0 ms`; tokens `4207`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3654755565959501`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> Two independent search rankings (vector search and full-text search) are combined into one ordered result using Reciprocal Rank Fusion (RRF) in the `hybrid_search` function. Specifically, it retrieves results from `search_vector` and `search_fulltext`, computes each result's rank (1-indexed) within each list, and calculates an `rrf_score` for each candidate chunk ID by summing $1 / (60 + \text{rank})$ for whichever ranking systems returned that chunk. Finally, the combined results are sorted in descending order by their `rrf_score` and sliced to the specified `limit`.

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1473](#baseline-chunk-1473) | `app/retrieval/hybrid_search.py:51-70` | 0.36212025647838564 | None | 0.01639344262295082 | yes | yes | [retrieved chunk 1472](#baseline-chunk-1472) | none (file boundary) |
| 2 | [1494](#baseline-chunk-1494) | `tests/unit/test_hybrid_search.py:1-49` | 0.3654755565959501 | None | 0.016129032258064516 | yes | yes | none (file boundary) | none (file boundary) |
| 3 | [1472](#baseline-chunk-1472) | `app/retrieval/hybrid_search.py:1-60` | 0.37921096067014926 | None | 0.015873015873015872 | yes | yes | none (file boundary) | [retrieved chunk 1473](#baseline-chunk-1473) |
| 4 | [1454](#baseline-chunk-1454) | `app/investigation/graph.py:101-160` | 0.40975600726379713 | None | 0.015625 | no | no | [retrieved chunk 1453](#baseline-chunk-1453) | [retrieved chunk 1455](#baseline-chunk-1455) |
| 5 | [1469](#baseline-chunk-1469) | `app/retrieval/__init__.py:1-7` | 0.4225957537460995 | None | 0.015384615384615385 | no | no | none (file boundary) | none (file boundary) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1583](#experiment-chunk-1583) | `tests/unit/test_hybrid_search.py:1-49` | 0.3654755565959501 | None | 0.01639344262295082 | no | no | none (file boundary) | none (file boundary) |
| 2 | [1567](#experiment-chunk-1567) | `app/retrieval/hybrid_search.py:1-70` | 0.37645013121552917 | None | 0.016129032258064516 | no | no | none (file boundary) | none (file boundary) |
| 3 | [1565](#experiment-chunk-1565) | `app/retrieval/__init__.py:1-7` | 0.4225957537460995 | None | 0.015873015873015872 | no | no | none (file boundary) | none (file boundary) |
| 4 | [1555](#experiment-chunk-1555) | `app/investigation/graph.py:81-180` | 0.4523021757214857 | None | 0.015625 | no | no | [retrieved chunk 1554](#experiment-chunk-1554) | [retrieved chunk 1556](#experiment-chunk-1556) |
| 5 | [1554](#experiment-chunk-1554) | `app/investigation/graph.py:1-100` | 0.4611349330071267 | None | 0.015384615384615385 | no | no | none (file boundary) | [retrieved chunk 1555](#experiment-chunk-1555) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="paraphrased-05"></a>
<details><summary><strong>paraphrased-05</strong> - What stops a weak search result from reaching the language model?</summary>

**Category:** `paraphrased`\
**Question:** What stops a weak search result from reaching the language model?
**Golden relevant label(s):** app/investigation/guard.py: `is_sufficient =`\
**Automated must-mention screen (not a human verdict):** (`evidence`) AND (`insufficient`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | correct | correct_unlabeled_context | False | True | 1454, 1455, 1498, 1502, 1504 | 3509 | 1901 | none |
| 100/20 experiment | 1 | correct | correct_labeled_context | False | True | 1586, 1554, 1585, 1558, 1556 | 4927 | 1794 | none |
| 60/10 baseline | 2 | correct | correct_unlabeled_context | False | True | 1454, 1455, 1498, 1502, 1504 | 3565 | 1098 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | 1586, 1554, 1585, 1558, 1556 | 4928 | 1240 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `2152 ms`; generation `1901 ms`; throttle `0 ms`; tokens `3509`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3495334867594725`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1454`, `1455`, `1498`, `1502`, `1504`. Citation relevance flags: [{'id': '1454', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1455', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1498', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1502', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1504', 'found_in_retrieval_results': True, 'relevant': False}].

> A weak search result is evaluated for sufficiency using `evaluate_evidence_sufficiency`, and if it is deemed insufficient, the investigation graph either retries with a widened search limit, falls back to a literal grep search, or ultimately stops and returns an insufficient diagnosis (such as `INSUFFICIENT_EVIDENCE`) via `return_insufficient`, preventing generation from running.

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `2137 ms`; generation `1794 ms`; throttle `0 ms`; tokens `4927`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.368621108571515`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1586`, `1554`, `1585`, `1558`, `1556`. Citation relevance flags: [{'id': '1586', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1554', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1585', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1558', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1556', 'found_in_retrieval_results': True, 'relevant': False}].

> A weak search result is evaluated by the evidence sufficiency guard (`evaluate_evidence_sufficiency`), which checks if its RRF score meets or exceeds `MIN_ACCEPTABLE_RRF_SCORE` (0.016) and its vector cosine distance is less than or equal to `MAX_ACCEPTABLE_VECTOR_DISTANCE` (0.5). If the evidence is deemed insufficient, `route_after_guard` prevents it from proceeding to prompt building and generation; instead, if it is the first retry attempt (`retry_count == 0` and evidence source is hybrid), the graph triggers a wider search retry or falls back to literal grep search, and ultimately returns "INSUFFICIENT_EVIDENCE" with low confidence if the evidence remains insufficient.

**60/10 baseline - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `6287 ms`; generation `1098 ms`; throttle `484 ms`; tokens `3565`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3495334867594725`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1454`, `1455`, `1498`, `1502`, `1504`. Citation relevance flags: [{'id': '1454', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1455', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1498', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1502', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1504', 'found_in_retrieval_results': True, 'relevant': False}].

> A weak search result is evaluated for sufficiency using `evaluate_evidence_sufficiency`. If the evidence check determines the results are insufficient (`is_sufficient` is False), `route_after_guard` handles the routing: if it is a literal search source, it stops; if the retry count is 0, it retries with a widened search; otherwise, it proceeds to grep. If evidence remains insufficient after retries and literal fallback (e.g., when grep has no match), the graph routes to `return_insufficient`, which returns an "INSUFFICIENT_EVIDENCE" diagnosis, preventing generation from running without sufficient evidence.

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `16790 ms`; generation `1240 ms`; throttle `500 ms`; tokens `4928`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.368621108571515`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1586`, `1554`, `1585`, `1558`, `1556`. Citation relevance flags: [{'id': '1586', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1554', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1585', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1558', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1556', 'found_in_retrieval_results': True, 'relevant': False}].

> A weak search result is evaluated by the evidence quality guard (`evaluate_evidence_sufficiency`), which checks if the result meets the required thresholds (such as `MIN_ACCEPTABLE_RRF_SCORE` of 0.016 and `MAX_ACCEPTABLE_VECTOR_DISTANCE` of 0.5). If the evidence is deemed insufficient (`is_sufficient` is False), the investigation graph routes via `route_after_guard`: if it is the first retry count and the source is hybrid, it triggers a wider search (`retry`), falls back to a literal grep search (`grep`), or stops/returns insufficient evidence (`INSUFFICIENT_EVIDENCE`), thereby preventing weak search results from proceeding directly to prompt generation and the language model.

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1454](#baseline-chunk-1454) | `app/investigation/graph.py:101-160` | 0.3495334867594725 | None | 0.01639344262295082 | yes | yes | [retrieved chunk 1453](#baseline-chunk-1453) | [retrieved chunk 1455](#baseline-chunk-1455) |
| 2 | [1455](#baseline-chunk-1455) | `app/investigation/graph.py:151-210` | 0.36495364757619897 | None | 0.016129032258064516 | yes | yes | [retrieved chunk 1454](#baseline-chunk-1454) | [app/investigation/graph.py:201-260](#baseline-context-d3469f915cc50c2d) |
| 3 | [1498](#baseline-chunk-1498) | `tests/unit/test_investigation_graph.py:101-155` | 0.37511128757459655 | None | 0.015873015873015872 | yes | yes | [retrieved chunk 1497](#baseline-chunk-1497) | none (file boundary) |
| 4 | [1502](#baseline-chunk-1502) | `tests/unit/test_investigation_mcp_tools.py:151-206` | 0.3766178595990324 | None | 0.015625 | yes | yes | [retrieved chunk 1501](#baseline-chunk-1501) | none (file boundary) |
| 5 | [1504](#baseline-chunk-1504) | `tests/unit/test_investigation_parsing.py:51-95` | 0.3778638912353812 | None | 0.015384615384615385 | yes | yes | [retrieved chunk 1503](#baseline-chunk-1503) | none (file boundary) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1586](#experiment-chunk-1586) | `tests/unit/test_investigation_graph.py:81-155` | 0.368621108571515 | None | 0.01639344262295082 | yes | yes | [retrieved chunk 1585](#experiment-chunk-1585) | none (file boundary) |
| 2 | [1554](#experiment-chunk-1554) | `app/investigation/graph.py:1-100` | 0.3771553616174408 | None | 0.016129032258064516 | yes | yes | none (file boundary) | [retrieved chunk 1555](#experiment-chunk-1555) |
| 3 | [1585](#experiment-chunk-1585) | `tests/unit/test_investigation_graph.py:1-100` | 0.3828094528530701 | None | 0.015873015873015872 | yes | yes | none (file boundary) | [retrieved chunk 1586](#experiment-chunk-1586) |
| 4 | [1558](#experiment-chunk-1558) | `app/investigation/guard.py:1-70` | 0.3873620565214584 | None | 0.015625 | yes | yes | none (file boundary) | none (file boundary) |
| 5 | [1556](#experiment-chunk-1556) | `app/investigation/graph.py:161-260` | 0.3949939103968906 | None | 0.015384615384615385 | yes | yes | [retrieved chunk 1555](#experiment-chunk-1555) | [app/investigation/graph.py:241-273](#experiment-context-6e7fbcc3f9f32261) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="paraphrased-06"></a>
<details><summary><strong>paraphrased-06</strong> - How is a model's certainty adjusted when the supporting search evidence is borderline?</summary>

**Category:** `paraphrased`\
**Question:** How is a model's certainty adjusted when the supporting search evidence is borderline?
**Golden relevant label(s):** app/investigation/confidence.py: `return "medium"`\
**Automated must-mention screen (not a human verdict):** (`medium`) AND (`high`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | correct | correct_labeled_context | False | True | 1449, 1498 | 3320 | 1413 | none |
| 100/20 experiment | 1 | correct | correct_labeled_context | False | True | 1552 | 3885 | 1330 | none |
| 60/10 baseline | 2 | correct | correct_labeled_context | False | True | 1449 | 3311 | 1499 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | 1552 | 3862 | 1604 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1663 ms`; generation `1413 ms`; throttle `0 ms`; tokens `3320`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.34820705781712924`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1449`, `1498`. Citation relevance flags: [{'id': '1449', 'found_in_retrieval_results': True, 'relevant': True}, {'id': '1498', 'found_in_retrieval_results': True, 'relevant': False}].

> When a model's reported confidence is "high" and the supporting search evidence is borderline (such as when the best RRF score is below the clear threshold `MIN_CLEAR_RRF_SCORE` of 0.032, or the best vector distance is above the clear threshold `MAX_CLEAR_VECTOR_DISTANCE` of 0.4), the confidence rating is downgraded to "medium". If the normalized confidence is not "high", it is retained without downgrade.

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1619 ms`; generation `1330 ms`; throttle `0 ms`; tokens `3885`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.34820705781712924`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1552`. Citation relevance flags: [{'id': '1552', 'found_in_retrieval_results': True, 'relevant': True}].

> When a model's reported confidence is "high" and the supporting search evidence is borderline—specifically if the best RRF score is below `MIN_CLEAR_RRF_SCORE` (0.032) or the best vector distance is above `MAX_CLEAR_VECTOR_DISTANCE` (0.4)—the confidence rating is downgraded to "medium". If the normalized confidence is anything other than "high", it is retained without calibration downgrade.

**60/10 baseline - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1825 ms`; generation `1499 ms`; throttle `0 ms`; tokens `3311`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.34820705781712924`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1449`. Citation relevance flags: [{'id': '1449', 'found_in_retrieval_results': True, 'relevant': True}].

> When a model's reported confidence is "high" and the supporting search evidence is borderline (specifically, when the best RRF score is below `MIN_CLEAR_RRF_SCORE` of `0.032` or the best vector distance is above `MAX_CLEAR_VECTOR_DISTANCE` of `0.4`), the `calibrate_confidence` function downgrades the confidence rating from "high" to "medium" and appends the specific threshold violation reasons to a note. If the reported confidence is anything other than "high", it is retained without calibration.

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1928 ms`; generation `1604 ms`; throttle `0 ms`; tokens `3862`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.34820705781712924`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1552`. Citation relevance flags: [{'id': '1552', 'found_in_retrieval_results': True, 'relevant': True}].

> When the supporting search evidence is borderline (such as when the best RRF score is below the clear margin threshold of `0.032` or the best vector distance is above the clear threshold of `0.4`), a high model confidence rating is downgraded to "medium" by `calibrate_confidence`. If the reported confidence is not "high", it is retained without being downgraded.

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1449](#baseline-chunk-1449) | `app/investigation/confidence.py:1-38` | 0.34820705781712924 | None | 0.01639344262295082 | yes | yes | none (file boundary) | none (file boundary) |
| 2 | [1498](#baseline-chunk-1498) | `tests/unit/test_investigation_graph.py:101-155` | 0.35881596172149355 | None | 0.016129032258064516 | yes | no | [retrieved chunk 1497](#baseline-chunk-1497) | none (file boundary) |
| 3 | [1504](#baseline-chunk-1504) | `tests/unit/test_investigation_parsing.py:51-95` | 0.36640741642610397 | None | 0.015873015873015872 | no | no | [retrieved chunk 1503](#baseline-chunk-1503) | none (file boundary) |
| 4 | [1502](#baseline-chunk-1502) | `tests/unit/test_investigation_mcp_tools.py:151-206` | 0.37017443839738307 | None | 0.015625 | no | no | [retrieved chunk 1501](#baseline-chunk-1501) | none (file boundary) |
| 5 | [1463](#baseline-chunk-1463) | `app/investigation/parsing.py:1-60` | 0.37031183627258335 | None | 0.015384615384615385 | no | no | none (file boundary) | [retrieved chunk 1464](#baseline-chunk-1464) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1552](#experiment-chunk-1552) | `app/investigation/confidence.py:1-38` | 0.34820705781712924 | None | 0.01639344262295082 | yes | yes | none (file boundary) | none (file boundary) |
| 2 | [1586](#experiment-chunk-1586) | `tests/unit/test_investigation_graph.py:81-155` | 0.35870407098426704 | None | 0.016129032258064516 | no | no | [retrieved chunk 1585](#experiment-chunk-1585) | none (file boundary) |
| 3 | [1589](#experiment-chunk-1589) | `tests/unit/test_investigation_mcp_tools.py:161-206` | 0.3827491727658112 | None | 0.015873015873015872 | no | no | [retrieved chunk 1588](#experiment-chunk-1588) | none (file boundary) |
| 4 | [1558](#experiment-chunk-1558) | `app/investigation/guard.py:1-70` | 0.3848176426786273 | None | 0.015625 | no | no | none (file boundary) | none (file boundary) |
| 5 | [1585](#experiment-chunk-1585) | `tests/unit/test_investigation_graph.py:1-100` | 0.39009508145676375 | None | 0.015384615384615385 | no | no | none (file boundary) | [retrieved chunk 1586](#experiment-chunk-1586) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="paraphrased-07"></a>
<details><summary><strong>paraphrased-07</strong> - How can the application find an exact phrase in its local source tree?</summary>

**Category:** `paraphrased`\
**Question:** How can the application find an exact phrase in its local source tree?
**Golden relevant label(s):** app/investigation/mcp_server.py: `casefold()`\
**Automated must-mention screen (not a human verdict):** (`literal`) AND (`source`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | correct | correct_unlabeled_context | False | True | 1500, 1461, 1501, 1453, 1499 | 3392 | 1753 | none |
| 100/20 experiment | 1 | correct | correct_unlabeled_context | False | True | none | 4512 | 1365 | none |
| 60/10 baseline | 2 | correct | correct_unlabeled_context | False | True | 1461, 1453 | 3366 | 1264 | none |
| 100/20 experiment | 2 | correct | correct_unlabeled_context | False | True | 1588, 1587, 1560 | 4567 | 1394 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `2107 ms`; generation `1753 ms`; throttle `0 ms`; tokens `3392`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3561837518223805`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1500`, `1461`, `1501`, `1453`, `1499`. Citation relevance flags: [{'id': '1500', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1461', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1501', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1453', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1499', 'found_in_retrieval_results': True, 'relevant': False}].

> The application can find a literal keyword in Python source files under a local repository path by using the `grep_search` tool (or `call_grep_search_mcp`), which searches raw local Python sources using the same file and directory exclusions as ingestion.

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1625 ms`; generation `1365 ms`; throttle `0 ms`; tokens `4512`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3571845894121699`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> The application can find an exact phrase (or literal keyword) in its local source tree by using the `grep_search` function (or via the MCP tool `grep_search`), which searches raw local Python source files under a local repository path using the same file and directory exclusions as ingestion.

**60/10 baseline - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1616 ms`; generation `1264 ms`; throttle `0 ms`; tokens `3366`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3561837518223805`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1461`, `1453`. Citation relevance flags: [{'id': '1461', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1453', 'found_in_retrieval_results': True, 'relevant': False}].

> The application can find a literal keyword in Python source files under a local repository path using the `grep_search` tool (or `call_grep_search_mcp`), which searches raw local Python sources using the same file and directory exclusions as ingestion.

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1666 ms`; generation `1394 ms`; throttle `0 ms`; tokens `4567`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3571845894121699`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1588`, `1587`, `1560`. Citation relevance flags: [{'id': '1588', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1587', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1560', 'found_in_retrieval_results': True, 'relevant': False}].

> The application can find a literal keyword (or exact phrase) in its local source tree by using the `grep_search` function/tool (or the `grep_search_tool` MCP tool), which searches raw local Python sources under a local repository path while applying the same file and directory exclusions as ingestion.

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1500](#baseline-chunk-1500) | `tests/unit/test_investigation_mcp_tools.py:51-110` | 0.3561837518223805 | None | 0.01639344262295082 | yes | no | [retrieved chunk 1499](#baseline-chunk-1499) | [retrieved chunk 1501](#baseline-chunk-1501) |
| 2 | [1461](#baseline-chunk-1461) | `app/investigation/mcp_server.py:51-110` | 0.38616473590043965 | None | 0.016129032258064516 | yes | yes | [retrieved chunk 1460](#baseline-chunk-1460) | [retrieved chunk 1462](#baseline-chunk-1462) |
| 3 | [1501](#baseline-chunk-1501) | `tests/unit/test_investigation_mcp_tools.py:101-160` | 0.4072261819791102 | None | 0.015873015873015872 | yes | no | [retrieved chunk 1500](#baseline-chunk-1500) | [retrieved chunk 1502](#baseline-chunk-1502) |
| 4 | [1453](#baseline-chunk-1453) | `app/investigation/graph.py:51-110` | 0.40830237938219305 | None | 0.015625 | yes | yes | [retrieved chunk 1452](#baseline-chunk-1452) | [retrieved chunk 1454](#baseline-chunk-1454) |
| 5 | [1499](#baseline-chunk-1499) | `tests/unit/test_investigation_mcp_tools.py:1-60` | 0.41551314461699496 | None | 0.015384615384615385 | yes | no | none (file boundary) | [retrieved chunk 1500](#baseline-chunk-1500) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1588](#experiment-chunk-1588) | `tests/unit/test_investigation_mcp_tools.py:81-180` | 0.3571845894121699 | None | 0.01639344262295082 | no | yes | [retrieved chunk 1587](#experiment-chunk-1587) | [retrieved chunk 1589](#experiment-chunk-1589) |
| 2 | [1587](#experiment-chunk-1587) | `tests/unit/test_investigation_mcp_tools.py:1-100` | 0.36861238520865613 | None | 0.016129032258064516 | no | yes | none (file boundary) | [retrieved chunk 1588](#experiment-chunk-1588) |
| 3 | [1577](#experiment-chunk-1577) | `scripts/search_repo.py:1-95` | 0.405792443735038 | None | 0.015873015873015872 | no | no | none (file boundary) | none (file boundary) |
| 4 | [1560](#experiment-chunk-1560) | `app/investigation/mcp_server.py:81-131` | 0.4084722488357799 | None | 0.015625 | no | yes | [retrieved chunk 1559](#experiment-chunk-1559) | none (file boundary) |
| 5 | [1572](#experiment-chunk-1572) | `scripts/ingest_repo.py:1-100` | 0.42163211197579853 | None | 0.015384615384615385 | no | no | none (file boundary) | [retrieved chunk 1573](#experiment-chunk-1573) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="paraphrased-08"></a>
<details><summary><strong>paraphrased-08</strong> - What record keeps the retrieved evidence and response metadata together?</summary>

**Category:** `paraphrased`\
**Question:** What record keeps the retrieved evidence and response metadata together?
**Golden relevant label(s):** app/investigation/persistence.py: `tool_calls`\
**Automated must-mention screen (not a human verdict):** (`audit`) AND (`retrieved`)

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | wrong-or-incomplete | retrieval_miss_abstained | False | True | none | 3167 | 1090 | none |
| 100/20 experiment | 1 | correct | correct_labeled_context | False | True | none | 4852 | 1332 | none |
| 60/10 baseline | 2 | wrong-or-incomplete | incomplete_or_wrong | False | True | 1506 | 3231 | 1371 | none |
| 100/20 experiment | 2 | correct | correct_labeled_context | False | True | none | 4808 | 2019 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1346 ms`; generation `1090 ms`; throttle `0 ms`; tokens `3167`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.33962814911559847`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `1768 ms`; generation `1332 ms`; throttle `0 ms`; tokens `4852`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.34048455146747025`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> The `Audit` record keeps the retrieved evidence (such as `retrieved_chunk_ids`, `vector_scores`, `fts_scores`, `rrf_scores`, and detailed retrieval results) and response metadata (such as `query`, `repository_id`, `model`, `response`, `latency_ms`, `token_usage`, `confidence`, and `tool_calls`) together.

**60/10 baseline - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `False`; finish `STOP`; wall `1772 ms`; generation `1371 ms`; throttle `0 ms`; tokens `3231`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.33962814911559847`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1506`. Citation relevance flags: [{'id': '1506', 'found_in_retrieval_results': True, 'relevant': False}].

> `persist_investigation` stores the investigation record (keeping the query, response, model, latency, token usage, retrieval results, and other metadata together, as shown in `tests/unit/test_investigation_persistence.py`).

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `None`; answer screen `True`; finish `STOP`; wall `2256 ms`; generation `2019 ms`; throttle `0 ms`; tokens `4808`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.34048455146747025`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> An Audit record (or Audit model) keeps the retrieved evidence and response metadata together by storing retrieval results, scores, tool calls, response text, model, latency, token usage, and confidence alongside the investigation ID.

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1454](#baseline-chunk-1454) | `app/investigation/graph.py:101-160` | 0.33962814911559847 | None | 0.01639344262295082 | no | no | [retrieved chunk 1453](#baseline-chunk-1453) | [retrieved chunk 1455](#baseline-chunk-1455) |
| 2 | [1463](#baseline-chunk-1463) | `app/investigation/parsing.py:1-60` | 0.34177732145979656 | None | 0.016129032258064516 | no | no | none (file boundary) | [retrieved chunk 1464](#baseline-chunk-1464) |
| 3 | [1506](#baseline-chunk-1506) | `tests/unit/test_investigation_persistence.py:51-110` | 0.34551028974216424 | None | 0.015873015873015872 | no | yes | [tests/unit/test_investigation_persistence.py:1-60](#baseline-context-91193a850a6b0918) | [retrieved chunk 1507](#baseline-chunk-1507) |
| 4 | [1464](#baseline-chunk-1464) | `app/investigation/parsing.py:51-97` | 0.3466618058943225 | None | 0.015625 | no | no | [retrieved chunk 1463](#baseline-chunk-1463) | none (file boundary) |
| 5 | [1504](#baseline-chunk-1504) | `tests/unit/test_investigation_parsing.py:51-95` | 0.3550697439770609 | None | 0.015384615384615385 | no | no | [retrieved chunk 1503](#baseline-chunk-1503) | none (file boundary) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1561](#experiment-chunk-1561) | `app/investigation/parsing.py:1-97` | 0.34048455146747025 | None | 0.01639344262295082 | no | no | none (file boundary) | none (file boundary) |
| 2 | [1592](#experiment-chunk-1592) | `tests/unit/test_investigation_persistence.py:81-120` | 0.34350301603165634 | None | 0.016129032258064516 | no | no | [retrieved chunk 1591](#experiment-chunk-1591) | none (file boundary) |
| 3 | [1575](#experiment-chunk-1575) | `scripts/investigate.py:81-180` | 0.3444056363361082 | None | 0.015873015873015872 | no | no | [retrieved chunk 1574](#experiment-chunk-1574) | [scripts/investigate.py:161-186](#experiment-context-fbbc24cd3500764e) |
| 4 | [1590](#experiment-chunk-1590) | `tests/unit/test_investigation_parsing.py:1-95` | 0.3535563420026676 | None | 0.015625 | no | no | none (file boundary) | none (file boundary) |
| 5 | [1562](#experiment-chunk-1562) | `app/investigation/persistence.py:1-93` | 0.3535694745576531 | None | 0.015384615384615385 | no | no | none (file boundary) | none (file boundary) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="unanswerable_far-01"></a>
<details><summary><strong>unanswerable_far-01</strong> - How do I bake sourdough bread at high altitude?</summary>

**Category:** `unanswerable_far`\
**Question:** How do I bake sourdough bread at high altitude?
**Golden relevant label(s):** No labeled source (unanswerable question).\
**Automated must-mention screen (not a human verdict):** n/a

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |
| 100/20 experiment | 1 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |
| 60/10 baseline | 2 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |
| 100/20 experiment | 2 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `14680 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-1** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `24160 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**60/10 baseline - pass-2** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `18428 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-2** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `15822 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| n/a | *(no retrieved chunks)* | n/a | n/a | n/a | n/a | n/a | n/a |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| n/a | *(no retrieved chunks)* | n/a | n/a | n/a | n/a | n/a | n/a |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="unanswerable_far-02"></a>
<details><summary><strong>unanswerable_far-02</strong> - Which telescope can observe the rings of Saturn?</summary>

**Category:** `unanswerable_far`\
**Question:** Which telescope can observe the rings of Saturn?
**Golden relevant label(s):** No labeled source (unanswerable question).\
**Automated must-mention screen (not a human verdict):** n/a

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |
| 100/20 experiment | 1 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |
| 60/10 baseline | 2 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |
| 100/20 experiment | 2 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `17020 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-1** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `17457 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**60/10 baseline - pass-2** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `19359 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-2** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `16339 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| n/a | *(no retrieved chunks)* | n/a | n/a | n/a | n/a | n/a | n/a |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| n/a | *(no retrieved chunks)* | n/a | n/a | n/a | n/a | n/a | n/a |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="unanswerable_far-03"></a>
<details><summary><strong>unanswerable_far-03</strong> - How should a wooden canoe be repaired?</summary>

**Category:** `unanswerable_far`\
**Question:** How should a wooden canoe be repaired?
**Golden relevant label(s):** No labeled source (unanswerable question).\
**Automated must-mention screen (not a human verdict):** n/a

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |
| 100/20 experiment | 1 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |
| 60/10 baseline | 2 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |
| 100/20 experiment | 2 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `18719 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-1** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `17527 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**60/10 baseline - pass-2** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `19802 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-2** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `15471 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| n/a | *(no retrieved chunks)* | n/a | n/a | n/a | n/a | n/a | n/a |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| n/a | *(no retrieved chunks)* | n/a | n/a | n/a | n/a | n/a | n/a |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="unanswerable_far-04"></a>
<details><summary><strong>unanswerable_far-04</strong> - Why do coral reefs bleach during marine heatwaves?</summary>

**Category:** `unanswerable_far`\
**Question:** Why do coral reefs bleach during marine heatwaves?
**Golden relevant label(s):** No labeled source (unanswerable question).\
**Automated must-mention screen (not a human verdict):** n/a

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |
| 100/20 experiment | 1 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |
| 60/10 baseline | 2 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |
| 100/20 experiment | 2 | refused | guard_true_refusal | True | False | none | n/a | n/a | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `18331 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-1** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `19434 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**60/10 baseline - pass-2** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `20309 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-2** - confidence `low`; source `hybrid`; retry `True`; abstention `None`; answer screen `None`; finish `None`; wall `14958 ms`; generation `None ms`; throttle `0 ms`; tokens `None`.
Evidence check: sufficient `False`; best RRF `None`; best vector `None`; reason: No repository evidence was retrieved..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| n/a | *(no retrieved chunks)* | n/a | n/a | n/a | n/a | n/a | n/a |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| n/a | *(no retrieved chunks)* | n/a | n/a | n/a | n/a | n/a | n/a |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="unanswerable_near-01"></a>
<details><summary><strong>unanswerable_near-01</strong> - How is Redis configured for this application?</summary>

**Category:** `unanswerable_near`\
**Question:** How is Redis configured for this application?
**Golden relevant label(s):** No labeled source (unanswerable question).\
**Automated must-mention screen (not a human verdict):** n/a

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | falsely answered | model_abstained | False | True | 1439, 1506, 1507, 1440, 1492 | 1971 | 1409 | none |
| 100/20 experiment | 1 | falsely answered | model_abstained | False | True | none | 2498 | 2795 | none |
| 60/10 baseline | 2 | falsely answered | model_abstained | False | True | none | 1900 | 1213 | none |
| 100/20 experiment | 2 | falsely answered | model_abstained | False | True | none | 2498 | 1266 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1669 ms`; generation `1409 ms`; throttle `0 ms`; tokens `1971`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3890554043876535`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: `1439`, `1506`, `1507`, `1440`, `1492`. Citation relevance flags: [{'id': '1439', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1506', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1507', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1440', 'found_in_retrieval_results': True, 'relevant': False}, {'id': '1492', 'found_in_retrieval_results': True, 'relevant': False}].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-1** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `3029 ms`; generation `2795 ms`; throttle `0 ms`; tokens `2498`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3890554043876535`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**60/10 baseline - pass-2** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1539 ms`; generation `1213 ms`; throttle `0 ms`; tokens `1900`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3890554043876535`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-2** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1508 ms`; generation `1266 ms`; throttle `0 ms`; tokens `2498`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3890554043876535`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1439](#baseline-chunk-1439) | `app/config.py:1-20` | 0.3890554043876535 | None | 0.01639344262295082 | yes | no | none (file boundary) | none (file boundary) |
| 2 | [1506](#baseline-chunk-1506) | `tests/unit/test_investigation_persistence.py:51-110` | 0.4318074592245381 | None | 0.016129032258064516 | yes | no | [tests/unit/test_investigation_persistence.py:1-60](#baseline-context-91193a850a6b0918) | [retrieved chunk 1507](#baseline-chunk-1507) |
| 3 | [1507](#baseline-chunk-1507) | `tests/unit/test_investigation_persistence.py:101-120` | 0.4406065793695403 | None | 0.015873015873015872 | yes | no | [retrieved chunk 1506](#baseline-chunk-1506) | none (file boundary) |
| 4 | [1440](#baseline-chunk-1440) | `app/db/__init__.py:1-1` | 0.44230282920641895 | None | 0.015625 | yes | no | none (file boundary) | none (file boundary) |
| 5 | [1492](#baseline-chunk-1492) | `tests/unit/test_db_models.py:1-33` | 0.4502291742123362 | None | 0.015384615384615385 | yes | no | none (file boundary) | none (file boundary) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1542](#experiment-chunk-1542) | `app/config.py:1-20` | 0.3890554043876535 | None | 0.01639344262295082 | no | no | none (file boundary) | none (file boundary) |
| 2 | [1543](#experiment-chunk-1543) | `app/db/__init__.py:1-1` | 0.44230282920641895 | None | 0.016129032258064516 | no | no | none (file boundary) | none (file boundary) |
| 3 | [1581](#experiment-chunk-1581) | `tests/unit/test_db_models.py:1-33` | 0.4502291742123362 | None | 0.015873015873015872 | no | no | none (file boundary) | none (file boundary) |
| 4 | [1575](#experiment-chunk-1575) | `scripts/investigate.py:81-180` | 0.45046946150281586 | None | 0.015625 | no | no | [retrieved chunk 1574](#experiment-chunk-1574) | [scripts/investigate.py:161-186](#experiment-context-fbbc24cd3500764e) |
| 5 | [1592](#experiment-chunk-1592) | `tests/unit/test_investigation_persistence.py:81-120` | 0.45103925576977366 | None | 0.015384615384615385 | no | no | [retrieved chunk 1591](#experiment-chunk-1591) | none (file boundary) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="unanswerable_near-02"></a>
<details><summary><strong>unanswerable_near-02</strong> - How does the message queue retry failed jobs?</summary>

**Category:** `unanswerable_near`\
**Question:** How does the message queue retry failed jobs?
**Golden relevant label(s):** No labeled source (unanswerable question).\
**Automated must-mention screen (not a human verdict):** n/a

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | falsely answered | model_abstained | False | True | none | 3435 | 1170 | none |
| 100/20 experiment | 1 | falsely answered | model_abstained | False | True | none | 5039 | 1265 | none |
| 60/10 baseline | 2 | falsely answered | model_abstained | False | True | none | 3435 | 1111 | none |
| 100/20 experiment | 2 | falsely answered | model_abstained | False | True | none | 5039 | 2822 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1475 ms`; generation `1170 ms`; throttle `0 ms`; tokens `3435`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.4031933052665212`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-1** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1577 ms`; generation `1265 ms`; throttle `0 ms`; tokens `5039`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3841150746736245`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**60/10 baseline - pass-2** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1430 ms`; generation `1111 ms`; throttle `0 ms`; tokens `3435`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.4031933052665212`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-2** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `3092 ms`; generation `2822 ms`; throttle `0 ms`; tokens `5039`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.3841150746736245`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1497](#baseline-chunk-1497) | `tests/unit/test_investigation_graph.py:51-110` | 0.4031933052665212 | None | 0.01639344262295082 | no | no | [retrieved chunk 1496](#baseline-chunk-1496) | [retrieved chunk 1498](#baseline-chunk-1498) |
| 2 | [1453](#baseline-chunk-1453) | `app/investigation/graph.py:51-110` | 0.412718141815167 | None | 0.016129032258064516 | no | no | [retrieved chunk 1452](#baseline-chunk-1452) | [retrieved chunk 1454](#baseline-chunk-1454) |
| 3 | [1498](#baseline-chunk-1498) | `tests/unit/test_investigation_graph.py:101-155` | 0.4168331537438458 | None | 0.015873015873015872 | no | no | [retrieved chunk 1497](#baseline-chunk-1497) | none (file boundary) |
| 4 | [1455](#baseline-chunk-1455) | `app/investigation/graph.py:151-210` | 0.42768205946999827 | None | 0.015625 | no | no | [retrieved chunk 1454](#baseline-chunk-1454) | [app/investigation/graph.py:201-260](#baseline-context-d3469f915cc50c2d) |
| 5 | [1502](#baseline-chunk-1502) | `tests/unit/test_investigation_mcp_tools.py:151-206` | 0.4340658035003221 | None | 0.015384615384615385 | no | no | [retrieved chunk 1501](#baseline-chunk-1501) | none (file boundary) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1585](#experiment-chunk-1585) | `tests/unit/test_investigation_graph.py:1-100` | 0.3841150746736245 | None | 0.01639344262295082 | no | no | none (file boundary) | [retrieved chunk 1586](#experiment-chunk-1586) |
| 2 | [1555](#experiment-chunk-1555) | `app/investigation/graph.py:81-180` | 0.4027459638681431 | None | 0.016129032258064516 | no | no | [retrieved chunk 1554](#experiment-chunk-1554) | [retrieved chunk 1556](#experiment-chunk-1556) |
| 3 | [1586](#experiment-chunk-1586) | `tests/unit/test_investigation_graph.py:81-155` | 0.4064713259038074 | None | 0.015873015873015872 | no | no | [retrieved chunk 1585](#experiment-chunk-1585) | none (file boundary) |
| 4 | [1554](#experiment-chunk-1554) | `app/investigation/graph.py:1-100` | 0.4167288366750945 | None | 0.015625 | no | no | none (file boundary) | [retrieved chunk 1555](#experiment-chunk-1555) |
| 5 | [1556](#experiment-chunk-1556) | `app/investigation/graph.py:161-260` | 0.4400784922547819 | None | 0.015384615384615385 | no | no | [retrieved chunk 1555](#experiment-chunk-1555) | [app/investigation/graph.py:241-273](#experiment-context-6e7fbcc3f9f32261) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="unanswerable_near-03"></a>
<details><summary><strong>unanswerable_near-03</strong> - Where is user login and authentication implemented?</summary>

**Category:** `unanswerable_near`\
**Question:** Where is user login and authentication implemented?
**Golden relevant label(s):** No labeled source (unanswerable question).\
**Automated must-mention screen (not a human verdict):** n/a

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | falsely answered | model_abstained | False | True | none | 1602 | 1252 | none |
| 100/20 experiment | 1 | falsely answered | model_abstained | False | True | none | 2538 | 1090 | none |
| 60/10 baseline | 2 | falsely answered | model_abstained | False | True | none | 1602 | 931 | none |
| 100/20 experiment | 2 | falsely answered | model_abstained | False | True | none | 2518 | 1397 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1603 ms`; generation `1252 ms`; throttle `0 ms`; tokens `1602`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.46731259198489206`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-1** - confidence `medium`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1329 ms`; generation `1090 ms`; throttle `0 ms`; tokens `2538`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.46731259198489206`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**60/10 baseline - pass-2** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1252 ms`; generation `931 ms`; throttle `0 ms`; tokens `1602`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.46731259198489206`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-2** - confidence `medium`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1630 ms`; generation `1397 ms`; throttle `0 ms`; tokens `2518`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.46731259198489206`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1475](#baseline-chunk-1475) | `scripts/__init__.py:1-1` | 0.46731259198489206 | None | 0.01639344262295082 | no | no | none (file boundary) | none (file boundary) |
| 2 | [1440](#baseline-chunk-1440) | `app/db/__init__.py:1-1` | 0.4727672330395327 | None | 0.016129032258064516 | no | no | none (file boundary) | none (file boundary) |
| 3 | [1469](#baseline-chunk-1469) | `app/retrieval/__init__.py:1-7` | 0.48297343272328075 | None | 0.015873015873015872 | no | no | none (file boundary) | none (file boundary) |
| 4 | [1455](#baseline-chunk-1455) | `app/investigation/graph.py:151-210` | 0.5015593532669249 | None | 0.015625 | no | no | [retrieved chunk 1454](#baseline-chunk-1454) | [app/investigation/graph.py:201-260](#baseline-context-d3469f915cc50c2d) |
| 5 | [1507](#baseline-chunk-1507) | `tests/unit/test_investigation_persistence.py:101-120` | 0.5068296817421698 | None | 0.015384615384615385 | no | no | [retrieved chunk 1506](#baseline-chunk-1506) | none (file boundary) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1569](#experiment-chunk-1569) | `scripts/__init__.py:1-1` | 0.46731259198489206 | None | 0.01639344262295082 | no | no | none (file boundary) | none (file boundary) |
| 2 | [1543](#experiment-chunk-1543) | `app/db/__init__.py:1-1` | 0.4727672330395327 | None | 0.016129032258064516 | no | no | none (file boundary) | none (file boundary) |
| 3 | [1565](#experiment-chunk-1565) | `app/retrieval/__init__.py:1-7` | 0.48297343272328075 | None | 0.015873015873015872 | no | no | none (file boundary) | none (file boundary) |
| 4 | [1556](#experiment-chunk-1556) | `app/investigation/graph.py:161-260` | 0.5075824961489384 | None | 0.015625 | no | no | [retrieved chunk 1555](#experiment-chunk-1555) | [app/investigation/graph.py:241-273](#experiment-context-6e7fbcc3f9f32261) |
| 5 | [1562](#experiment-chunk-1562) | `app/investigation/persistence.py:1-93` | 0.5098096119079802 | None | 0.015384615384615385 | no | no | none (file boundary) | none (file boundary) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

<a id="unanswerable_near-04"></a>
<details><summary><strong>unanswerable_near-04</strong> - Which Kubernetes deployment target does this service use?</summary>

**Category:** `unanswerable_near`\
**Question:** Which Kubernetes deployment target does this service use?
**Golden relevant label(s):** No labeled source (unanswerable question).\
**Automated must-mention screen (not a human verdict):** n/a

### Saved answer and run facts

| Arm | Pass | Legacy outcome | outcome_v2 (automated) | Guard refused | Generation | Cited IDs | Tokens | Generation ms | Error |
|---|---:|---|---|---|---|---|---:|---:|---|
| 60/10 baseline | 1 | falsely answered | model_abstained | False | True | none | 2335 | 1259 | none |
| 100/20 experiment | 1 | falsely answered | model_abstained | False | True | none | 3213 | 1175 | none |
| 60/10 baseline | 2 | falsely answered | model_abstained | False | True | none | 2335 | 889 | none |
| 100/20 experiment | 2 | falsely answered | model_abstained | False | True | none | 3213 | 1107 | none |

#### Generated diagnoses (saved verbatim)

**60/10 baseline - pass-1** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1539 ms`; generation `1259 ms`; throttle `0 ms`; tokens `2335`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.46289446621226626`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-1** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1433 ms`; generation `1175 ms`; throttle `0 ms`; tokens `3213`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.47101313066292283`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**60/10 baseline - pass-2** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1345 ms`; generation `889 ms`; throttle `0 ms`; tokens `2335`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.46289446621226626`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

**100/20 experiment - pass-2** - confidence `low`; source `hybrid`; retry `False`; abstention `explicit`; answer screen `None`; finish `STOP`; wall `1344 ms`; generation `1107 ms`; throttle `0 ms`; tokens `3213`.
Evidence check: sufficient `True`; best RRF `0.01639344262295082`; best vector `0.47101313066292283`; reason: Evidence strength meets the RRF and vector-distance requirements..
Cited chunk IDs: none. Citation relevance flags: [].

> INSUFFICIENT_EVIDENCE

### Retrieved top-five context (same saved retrieval in both passes)

Each row links to its exact saved chunk text in the evidence library. Citation columns show whether each answer cited that chunk. The adjacent-window columns show the immediate preceding/following indexed chunks reconstructed from the run's pinned source commit; these are context only, not retrieval results for this question.

#### 60/10 baseline

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1506](#baseline-chunk-1506) | `tests/unit/test_investigation_persistence.py:51-110` | 0.46289446621226626 | None | 0.01639344262295082 | no | no | [tests/unit/test_investigation_persistence.py:1-60](#baseline-context-91193a850a6b0918) | [retrieved chunk 1507](#baseline-chunk-1507) |
| 2 | [1488](#baseline-chunk-1488) | `tests/conftest.py:1-11` | 0.4715337062833934 | None | 0.016129032258064516 | no | no | none (file boundary) | none (file boundary) |
| 3 | [1440](#baseline-chunk-1440) | `app/db/__init__.py:1-1` | 0.4743045842232415 | None | 0.015873015873015872 | no | no | none (file boundary) | none (file boundary) |
| 4 | [1454](#baseline-chunk-1454) | `app/investigation/graph.py:101-160` | 0.47986741564924884 | None | 0.015625 | no | no | [retrieved chunk 1453](#baseline-chunk-1453) | [retrieved chunk 1455](#baseline-chunk-1455) |
| 5 | [1450](#baseline-chunk-1450) | `app/investigation/generation.py:1-60` | 0.4809018363210532 | None | 0.015384615384615385 | no | no | none (file boundary) | [app/investigation/generation.py:51-71](#baseline-context-da287e9758a22061) |

#### 100/20 experiment

| Rank | Retrieved chunk | Source span | Vector | FTS | RRF | Cited pass 1 | Cited pass 2 | Previous indexed chunk | Next indexed chunk |
|---:|---|---|---:|---:|---:|---|---|---|---|
| 1 | [1575](#experiment-chunk-1575) | `scripts/investigate.py:81-180` | 0.47101313066292283 | None | 0.01639344262295082 | no | no | [retrieved chunk 1574](#experiment-chunk-1574) | [scripts/investigate.py:161-186](#experiment-context-fbbc24cd3500764e) |
| 2 | [1578](#experiment-chunk-1578) | `tests/conftest.py:1-11` | 0.4715337062833934 | None | 0.016129032258064516 | no | no | none (file boundary) | none (file boundary) |
| 3 | [1574](#experiment-chunk-1574) | `scripts/investigate.py:1-100` | 0.4725904923007155 | None | 0.015873015873015872 | no | no | none (file boundary) | [retrieved chunk 1575](#experiment-chunk-1575) |
| 4 | [1543](#experiment-chunk-1543) | `app/db/__init__.py:1-1` | 0.4743045842232415 | None | 0.015625 | no | no | none (file boundary) | none (file boundary) |
| 5 | [1553](#experiment-chunk-1553) | `app/investigation/generation.py:1-71` | 0.4757382739004399 | None | 0.015384615384615385 | no | no | none (file boundary) | none (file boundary) |

### Human review - do not treat automated labels as verdicts

| Pass | Baseline: correct / complete / grounded? | Experiment: correct / complete / grounded? | Comparison | Notes / source verification |
|---:|---|---|---|---|
| 1 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |
| 2 | ___ / ___ / ___ | ___ / ___ / ___ | Better / Same / Worse / Unsure |  |

</details>

## Full retrieved-chunk evidence library

Every chunk below is the exact saved `content` field from at least one top-five retrieval. Question-specific rank and scores are in the question tables. IDs are run-local and are not comparable across strategies.

### 60/10 baseline ? 45 unique retrieved chunks

<a id="baseline-chunk-1439"></a>
<details><summary><strong>60/10 baseline chunk 1439</strong> - app/config.py:1-20</summary>

```text
app/config.py:1-20
```

````text
"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the IncidentWeave application."""

    app_env: str = "development"
    database_url: str = "postgresql://incidentweave:incidentweave@localhost:5432/incidentweave"
    gemini_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
````

</details>

<a id="baseline-chunk-1440"></a>
<details><summary><strong>60/10 baseline chunk 1440</strong> - app/db/__init__.py:1-1</summary>

```text
app/db/__init__.py:1-1
```

````text
"""Database infrastructure for IncidentWeave."""
````

</details>

<a id="baseline-chunk-1444"></a>
<details><summary><strong>60/10 baseline chunk 1444</strong> - app/db/models/chunk.py:1-52</summary>

```text
app/db/models/chunk.py:1-52
```

````text
"""Chunk ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.repository import Repository

class Chunk(Base):
    """Persisted source/evidence chunk and structural metadata."""

    __tablename__ = "chunks"
    __table_args__ = (
        Index("ix_chunks_repository_id", "repository_id"),
        Index("ix_chunks_repository_file_path", "repository_id", "file_path"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(100))
    document_type: Mapped[str | None] = mapped_column(String(100))
    symbol: Mapped[str | None] = mapped_column(String(255))
    function_name: Mapped[str | None] = mapped_column(String(255))
    class_name: Mapped[str | None] = mapped_column(String(255))
    line_start: Mapped[int | None] = mapped_column(Integer)
    line_end: Mapped[int | None] = mapped_column(Integer)
    section: Mapped[str | None] = mapped_column(String(500))
    service: Mapped[str | None] = mapped_column(String(255))
    environment: Mapped[str | None] = mapped_column(String(100))
    incident_id: Mapped[str | None] = mapped_column(String(255))
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    embedding: Mapped[list[float] | None] = mapped_column(VECTOR(768))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    repository: Mapped[Repository] = relationship(back_populates="chunks")
````

</details>

<a id="baseline-chunk-1447"></a>
<details><summary><strong>60/10 baseline chunk 1447</strong> - app/db/session.py:1-46</summary>

```text
app/db/session.py:1-46
```

````text
"""SQLAlchemy engine and session management."""

from collections.abc import AsyncGenerator

from pgvector.psycopg import register_vector_async
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _async_database_url(database_url: str) -> str:
    """Convert the configured PostgreSQL URL to the psycopg async dialect."""

    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url


engine = create_async_engine(
    _async_database_url(settings.database_url),
    pool_pre_ping=True,
)


@event.listens_for(engine.sync_engine, "connect")
def _register_pgvector(dbapi_connection: object, connection_record: object) -> None:
    """Register pgvector types for each async psycopg connection."""

    del connection_record
    dbapi_connection.run_async(register_vector_async)  # type: ignore[attr-defined]


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an application database session."""

    async with AsyncSessionLocal() as session:
        yield session
````

</details>

<a id="baseline-chunk-1449"></a>
<details><summary><strong>60/10 baseline chunk 1449</strong> - app/investigation/confidence.py:1-38</summary>

```text
app/investigation/confidence.py:1-38
```

````text
"""Calibrate model confidence against retrieval strength."""

from __future__ import annotations

MIN_CLEAR_RRF_SCORE = 0.032
MAX_CLEAR_VECTOR_DISTANCE = 0.4


def calibrate_confidence(
    reported_confidence: str,
    best_rrf_score: float | None,
    best_vector_score: float | None,
) -> tuple[str, str]:
    """Downgrade a high model rating when accepted evidence is borderline."""

    normalized_confidence = reported_confidence.strip().lower()
    if normalized_confidence != "high":
        return normalized_confidence, "Model confidence retained; calibration only downgrades high."

    weak_rrf = best_rrf_score is not None and best_rrf_score < MIN_CLEAR_RRF_SCORE
    borderline_distance = (
        best_vector_score is not None
        and best_vector_score > MAX_CLEAR_VECTOR_DISTANCE
    )
    if weak_rrf or borderline_distance:
        reasons: list[str] = []
        if weak_rrf:
            reasons.append(
                f"best RRF {best_rrf_score:.6f} is below {MIN_CLEAR_RRF_SCORE:.3f}"
            )
        if borderline_distance:
            reasons.append(
                "best vector distance "
                f"{best_vector_score:.6f} is above {MAX_CLEAR_VECTOR_DISTANCE:.1f}"
            )
        return "medium", "High confidence downgraded: " + "; ".join(reasons) + "."

    return "high", "High confidence retained; retrieval scores clear both calibration margins."
````

</details>

<a id="baseline-chunk-1450"></a>
<details><summary><strong>60/10 baseline chunk 1450</strong> - app/investigation/generation.py:1-60</summary>

```text
app/investigation/generation.py:1-60
```

````text
"""Gemini text generation for grounded investigations."""

from __future__ import annotations

import json
import os
import time
from time import perf_counter
from urllib import error, request

GEMINI_GENERATION_MODEL = "gemini-3.5-flash-lite"
GEMINI_GENERATION_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_GENERATION_MODEL}:generateContent"
)
GENERATION_TIMEOUT_SECONDS = 60
MAX_GENERATION_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def get_gemini_api_key() -> str:
    """Read the Gemini API key from the process environment."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return api_key


def generate_investigation(prompt: str) -> tuple[dict[str, object], int]:
    """Send a grounded prompt to Gemini and return its payload and latency."""

    payload = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
        }
    ).encode("utf-8")
    url = f"{GEMINI_GENERATION_ENDPOINT}?key={get_gemini_api_key()}"
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    last_error: Exception | None = None
    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        try:
            started_at = perf_counter()
            with request.urlopen(req, timeout=GENERATION_TIMEOUT_SECONDS) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
            latency_ms = round((perf_counter() - started_at) * 1000)
            if not isinstance(response_payload, dict):
                raise RuntimeError("Unexpected Gemini generation response format")
            return response_payload, latency_ms
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(
                f"Gemini generation failed with HTTP {exc.code}: {detail}"
            )
````

</details>

<a id="baseline-chunk-1452"></a>
<details><summary><strong>60/10 baseline chunk 1452</strong> - app/investigation/graph.py:1-60</summary>

```text
app/investigation/graph.py:1-60
```

````text
"""LangGraph orchestration for evidence-grounded investigations."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.db.session import AsyncSessionLocal
from app.investigation.generation import GEMINI_GENERATION_MODEL, generate_investigation
from app.investigation.guard import evaluate_evidence_sufficiency
from app.investigation.parsing import parse_investigation_response
from app.investigation.prompt import build_grounded_prompt
from app.retrieval.hybrid_search import hybrid_search


class InvestigationState(TypedDict):
    repository_id: int
    repository_name: str
    repository_path: str
    query: str
    query_embedding: list[float]
    search_limit: int
    retry_limit: int
    retry_count: int
    retry_used: bool
    retrieval_results: list[dict[str, object]]
    evidence_check: dict[str, object]
    diagnosis: str
    confidence: str
    cited_chunk_ids: list[str]
    model: str
    latency_ms: int | None
    calibration_note: str
    confidence_calibrated: bool
    evidence_source: str
    tool_calls: list[dict[str, object]]
    prompt: NotRequired[str]
    response_payload: NotRequired[Mapping[str, object]]
    grep_error: NotRequired[str | None]


ConfidenceCalibrator = Callable[
    [str, float | None, float | None], tuple[str, str]
]


async def call_grep_search_mcp(
    repository_name: str,
    repository_path: str,
    keyword: str,
    limit: int,
) -> tuple[list[dict[str, object]], str | None]:
    """Call grep_search over a real local MCP stdio subprocess."""
````

</details>

<a id="baseline-chunk-1453"></a>
<details><summary><strong>60/10 baseline chunk 1453</strong> - app/investigation/graph.py:51-110</summary>

```text
app/investigation/graph.py:51-110
```

````text
]


async def call_grep_search_mcp(
    repository_name: str,
    repository_path: str,
    keyword: str,
    limit: int,
) -> tuple[list[dict[str, object]], str | None]:
    """Call grep_search over a real local MCP stdio subprocess."""

    repository_root = Path(__file__).resolve().parents[2]
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.investigation.mcp_server"],
        cwd=repository_root,
    )
    try:
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as client:
                await client.initialize()
                response = await client.call_tool(
                    "grep_search",
                    {
                        "repository_name": repository_name,
                        "repository_path": repository_path,
                        "keyword": keyword,
                        "limit": limit,
                    },
                )
        if response.isError:
            details = "; ".join(
                item.text for item in response.content if hasattr(item, "text")
            )
            return [], details or "MCP grep_search returned an error."
        text_parts = [item.text for item in response.content if hasattr(item, "text")]
        if not text_parts:
            return [], "MCP grep_search returned no text content."
        decoded = json.loads(text_parts[0])
        if not isinstance(decoded, list):
            return [], "MCP grep_search returned an unexpected result shape."
        return [item for item in decoded if isinstance(item, dict)], None
    except Exception as exc:
        return [], f"MCP grep_search failed: {type(exc).__name__}: {exc}"


def create_investigation_graph(calibrate_confidence: ConfidenceCalibrator):
    """Build the one-retry investigation graph around existing Phase 5 logic."""

    async def retrieve(state: InvestigationState) -> dict[str, object]:
        async with AsyncSessionLocal() as session:
            results = await hybrid_search(
                session,
                state["repository_id"],
                state["query"],
                state["query_embedding"],
                limit=state["search_limit"],
            )
        return {
            "retrieval_results": results,
````

</details>

<a id="baseline-chunk-1454"></a>
<details><summary><strong>60/10 baseline chunk 1454</strong> - app/investigation/graph.py:101-160</summary>

```text
app/investigation/graph.py:101-160
```

````text
        async with AsyncSessionLocal() as session:
            results = await hybrid_search(
                session,
                state["repository_id"],
                state["query"],
                state["query_embedding"],
                limit=state["search_limit"],
            )
        return {
            "retrieval_results": results,
            "evidence_source": "hybrid",
            "grep_error": None,
        }

    def guard(state: InvestigationState) -> dict[str, object]:
        evidence_source = state["evidence_source"]
        evidence_check = evaluate_evidence_sufficiency(
            state["retrieval_results"],
            evidence_source=evidence_source,
        )
        attempts = list(state["tool_calls"])
        if evidence_source == "literal":
            outcome: dict[str, object] = {
                "match_count": len(state["retrieval_results"]),
                "sufficient": evidence_check["is_sufficient"],
                "reason": evidence_check["reason"],
            }
            if state.get("grep_error"):
                outcome["error"] = state["grep_error"]
            attempts.append(
                {
                    "tool": "grep_search",
                    "stage": "literal_fallback",
                    "parameters": {
                        "repository_name": state["repository_name"],
                        "repository_path": state["repository_path"],
                        "keyword": state["query"],
                        "limit": 20,
                    },
                    "outcome": outcome,
                }
            )
        else:
            attempts.append(
                {
                    "tool": "hybrid_search",
                    "stage": "widened_retry" if state["retry_count"] else "initial",
                    "parameters": {
                        "repository_name": state["repository_name"],
                        "query": state["query"],
                        "limit": state["search_limit"],
                    },
                    "outcome": {
                        "result_count": len(state["retrieval_results"]),
                        "sufficient": evidence_check["is_sufficient"],
                        "reason": evidence_check["reason"],
                        "best_rrf_score": evidence_check["best_rrf_score"],
                        "best_vector_score": evidence_check["best_vector_score"],
                    },
                }
````

</details>

<a id="baseline-chunk-1455"></a>
<details><summary><strong>60/10 baseline chunk 1455</strong> - app/investigation/graph.py:151-210</summary>

```text
app/investigation/graph.py:151-210
```

````text
                        "limit": state["search_limit"],
                    },
                    "outcome": {
                        "result_count": len(state["retrieval_results"]),
                        "sufficient": evidence_check["is_sufficient"],
                        "reason": evidence_check["reason"],
                        "best_rrf_score": evidence_check["best_rrf_score"],
                        "best_vector_score": evidence_check["best_vector_score"],
                    },
                }
            )
        return {"evidence_check": evidence_check, "tool_calls": attempts}

    def route_after_guard(state: InvestigationState) -> str:
        if state["evidence_check"]["is_sufficient"]:
            return "continue"
        if state["evidence_source"] == "literal":
            return "stop"
        if state["retry_count"] == 0:
            return "retry"
        return "grep"

    def widen_search(state: InvestigationState) -> dict[str, object]:
        return {
            "search_limit": state["retry_limit"],
            "retry_count": state["retry_count"] + 1,
            "retry_used": True,
        }

    async def literal_search(state: InvestigationState) -> dict[str, object]:
        matches, error = await call_grep_search_mcp(
            state["repository_name"],
            state["repository_path"],
            state["query"],
            20,
        )
        return {
            "retrieval_results": matches,
            "evidence_source": "literal",
            "grep_error": error,
        }

    def return_insufficient(state: InvestigationState) -> dict[str, object]:
        return {
            "diagnosis": "INSUFFICIENT_EVIDENCE",
            "confidence": "low",
            "cited_chunk_ids": [],
            "model": GEMINI_GENERATION_MODEL,
            "latency_ms": None,
            "calibration_note": "Not calibrated because evidence remained insufficient.",
            "confidence_calibrated": False,
            "tool_calls": state["tool_calls"],
        }

    def build_prompt(state: InvestigationState) -> dict[str, object]:
        return {
            "prompt": build_grounded_prompt(
                state["query"], state["retrieval_results"]
            )
        }
````

</details>

<a id="baseline-chunk-1458"></a>
<details><summary><strong>60/10 baseline chunk 1458</strong> - app/investigation/guard.py:1-60</summary>

```text
app/investigation/guard.py:1-60
```

````text
"""Evidence quality guard for grounded investigation results."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

MIN_ACCEPTABLE_RRF_SCORE = 0.016
MAX_ACCEPTABLE_VECTOR_DISTANCE = 0.5


def evaluate_evidence_sufficiency(
    retrieval_results: Sequence[Mapping[str, object]],
    *,
    evidence_source: str = "hybrid",
) -> dict[str, object]:
    """Evaluate hybrid scores or explicit literal-source matches."""

    if not retrieval_results:
        return {
            "is_sufficient": False,
            "reason": "No repository evidence was retrieved.",
            "best_rrf_score": None,
            "best_vector_score": None,
        }

    mapping_results = [result for result in retrieval_results if isinstance(result, Mapping)]
    if not mapping_results:
        return {
            "is_sufficient": False,
            "reason": "No repository evidence was retrieved.",
            "best_rrf_score": None,
            "best_vector_score": None,
        }

    if evidence_source == "literal":
        return {
            "is_sufficient": True,
            "reason": "Literal source matches were found.",
            "best_rrf_score": None,
            "best_vector_score": None,
        }

    best_rrf_score = max(float(result.get("rrf_score", 0.0)) for result in mapping_results)
    vector_scores = [
        float(score)
        for result in mapping_results
        if isinstance((score := result.get("vector_score")), (int, float))
    ]
    best_vector_score = min(vector_scores) if vector_scores else None

    is_sufficient = (
        best_rrf_score >= MIN_ACCEPTABLE_RRF_SCORE
        and best_vector_score is not None
        and best_vector_score <= MAX_ACCEPTABLE_VECTOR_DISTANCE
    )
    if best_rrf_score < MIN_ACCEPTABLE_RRF_SCORE:
        reason = "Best retrieved evidence score is below the minimum threshold."
    elif best_vector_score is None:
        reason = "No vector similarity score was retrieved."
    elif best_vector_score > MAX_ACCEPTABLE_VECTOR_DISTANCE:
````

</details>

<a id="baseline-chunk-1459"></a>
<details><summary><strong>60/10 baseline chunk 1459</strong> - app/investigation/guard.py:51-70</summary>

```text
app/investigation/guard.py:51-70
```

````text
    is_sufficient = (
        best_rrf_score >= MIN_ACCEPTABLE_RRF_SCORE
        and best_vector_score is not None
        and best_vector_score <= MAX_ACCEPTABLE_VECTOR_DISTANCE
    )
    if best_rrf_score < MIN_ACCEPTABLE_RRF_SCORE:
        reason = "Best retrieved evidence score is below the minimum threshold."
    elif best_vector_score is None:
        reason = "No vector similarity score was retrieved."
    elif best_vector_score > MAX_ACCEPTABLE_VECTOR_DISTANCE:
        reason = "Best vector cosine distance is above the maximum threshold."
    else:
        reason = "Evidence strength meets the RRF and vector-distance requirements."

    return {
        "is_sufficient": is_sufficient,
        "reason": reason,
        "best_rrf_score": best_rrf_score,
        "best_vector_score": best_vector_score,
    }
````

</details>

<a id="baseline-chunk-1460"></a>
<details><summary><strong>60/10 baseline chunk 1460</strong> - app/investigation/mcp_server.py:1-60</summary>

```text
app/investigation/mcp_server.py:1-60
```

````text
"""Local MCP server exposing IncidentWeave retrieval tools."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select

from app.db.models import Repository
from app.db.session import AsyncSessionLocal
from app.retrieval.hybrid_search import hybrid_search
from scripts.ingest_repo import iter_python_files

server = FastMCP("IncidentWeave local investigation tools")


def grep_search(
    repository_path: str | Path,
    keyword: str,
    repository_id: int,
    limit: int = 20,
) -> list[dict[str, object]]:
    """Find case-insensitive literal matches in ingester-visible Python files."""

    if not keyword:
        raise ValueError("keyword must not be empty")
    if limit <= 0:
        return []

    root = Path(repository_path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Repository path is not a directory: {repository_path}")

    needle = keyword.casefold()
    matches: list[dict[str, object]] = []
    for file_path in sorted(iter_python_files(root)):
        relative_path = file_path.relative_to(root).as_posix()
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line_number, line in enumerate(lines, start=1):
            if needle not in line.casefold():
                continue
            matches.append(
                {
                    "id": f"grep-{len(matches) + 1}",
                    "repository_id": repository_id,
                    "file_path": relative_path,
                    "line_start": line_number,
                    "line_end": line_number,
                    "content": line,
                    "vector_score": None,
                    "fts_score": None,
                    "rrf_score": None,
                }
            )
            if len(matches) >= limit:
                return matches
````

</details>

<a id="baseline-chunk-1461"></a>
<details><summary><strong>60/10 baseline chunk 1461</strong> - app/investigation/mcp_server.py:51-110</summary>

```text
app/investigation/mcp_server.py:51-110
```

````text
                    "line_start": line_number,
                    "line_end": line_number,
                    "content": line,
                    "vector_score": None,
                    "fts_score": None,
                    "rrf_score": None,
                }
            )
            if len(matches) >= limit:
                return matches
    return matches


@server.tool(
    name="hybrid_search",
    description="Search one indexed repository with vector and PostgreSQL full-text retrieval.",
)
async def hybrid_search_tool(
    repository_name: str,
    query_text: str,
    query_embedding: list[float],
    limit: int = 10,
) -> str:
    """Call the existing hybrid search implementation for a repository."""

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repository_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repository_name}")
        results = await hybrid_search(
            session,
            repository.id,
            query_text,
            query_embedding,
            limit=limit,
        )
    return json.dumps(results)


@server.tool(
    name="grep_search",
    description=(
        "Find a literal keyword in Python source files under a local repository path; "
        "uses the same file and directory exclusions as ingestion."
    ),
)
async def grep_search_tool(
    repository_name: str,
    repository_path: str,
    keyword: str,
    limit: int = 20,
) -> str:
    """Resolve the repository ID and search its raw local Python sources."""

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repository_name)
        )
````

</details>

<a id="baseline-chunk-1462"></a>
<details><summary><strong>60/10 baseline chunk 1462</strong> - app/investigation/mcp_server.py:101-131</summary>

```text
app/investigation/mcp_server.py:101-131
```

````text
    repository_path: str,
    keyword: str,
    limit: int = 20,
) -> str:
    """Resolve the repository ID and search its raw local Python sources."""

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repository_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repository_name}")
        matches = grep_search(
            repository_path,
            keyword,
            repository.id,
            limit=limit,
        )
    return json.dumps(matches)


def main() -> None:
    """Run the MCP server over stdio."""

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
````

</details>

<a id="baseline-chunk-1463"></a>
<details><summary><strong>60/10 baseline chunk 1463</strong> - app/investigation/parsing.py:1-60</summary>

```text
app/investigation/parsing.py:1-60
```

````text
"""Parse grounded investigation responses from Gemini."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

_CONFIDENCE_PATTERN = re.compile(
    r"^\s*confidence\s*:\s*(high|medium|low)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_DIAGNOSIS_PATTERN = re.compile(
    r"^\s*diagnosis\s*:\s*(.+?)(?=\n\s*(?:confidence|evidence used)\s*:|\Z)",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)
_CHUNK_PATTERN = re.compile(r"chunk_id\s*[=:]\s*([A-Za-z0-9_-]+)", re.IGNORECASE)


def _response_text(response_payload: Mapping[str, object]) -> str:
    """Extract candidate text from the standard Gemini response shape."""

    candidates = response_payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return ""

    candidate = candidates[0]
    if not isinstance(candidate, Mapping):
        return ""
    content = candidate.get("content")
    if not isinstance(content, Mapping):
        return ""
    parts = content.get("parts")
    if not isinstance(parts, list):
        return ""

    return "\n".join(
        str(part.get("text"))
        for part in parts
        if isinstance(part, Mapping) and isinstance(part.get("text"), str)
    ).strip()


def _matches_retrieved_citation(response_text: str, result: Mapping[str, object]) -> bool:
    """Return whether the model cited the result by ID or exact file path."""

    if not isinstance(result, Mapping):
        return False

    chunk_id = str(result.get("id"))
    if _CHUNK_PATTERN.search(response_text) and any(
        matched == chunk_id for matched in _CHUNK_PATTERN.findall(response_text)
    ):
        return True

    file_path = str(result.get("file_path") or "").strip()
    if not file_path:
        return False
    if file_path in response_text:
        return True

````

</details>

<a id="baseline-chunk-1464"></a>
<details><summary><strong>60/10 baseline chunk 1464</strong> - app/investigation/parsing.py:51-97</summary>

```text
app/investigation/parsing.py:51-97
```

````text
        matched == chunk_id for matched in _CHUNK_PATTERN.findall(response_text)
    ):
        return True

    file_path = str(result.get("file_path") or "").strip()
    if not file_path:
        return False
    if file_path in response_text:
        return True

    line_start = result.get("line_start")
    line_end = result.get("line_end")
    if line_start is None or line_end is None:
        return False

    pattern = (
        rf"{re.escape(file_path)}.*?(?:lines?|line range)\s*[:=]?\s*"
        rf"{re.escape(str(line_start))}\s*[-–]\s*{re.escape(str(line_end))}"
    )
    return bool(re.search(pattern, response_text, re.IGNORECASE | re.DOTALL))


def parse_investigation_response(
    response_payload: Mapping[str, object],
    retrieved_results: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Extract diagnosis, categorical confidence, and cited retrieved chunk IDs."""

    response_text = _response_text(response_payload)
    cited_ids = [
        str(result.get("id"))
        for result in retrieved_results
        if _matches_retrieved_citation(response_text, result)
    ]

    confidence_match = _CONFIDENCE_PATTERN.search(response_text)
    confidence = confidence_match.group(1).lower() if confidence_match else "low"

    diagnosis_match = _DIAGNOSIS_PATTERN.search(response_text)
    diagnosis = diagnosis_match.group(1).strip() if diagnosis_match else "INSUFFICIENT_EVIDENCE"

    return {
        "diagnosis": diagnosis or "INSUFFICIENT_EVIDENCE",
        "confidence": confidence,
        "cited_chunk_ids": cited_ids,
        "raw_text": response_text,
    }
````

</details>

<a id="baseline-chunk-1469"></a>
<details><summary><strong>60/10 baseline chunk 1469</strong> - app/retrieval/__init__.py:1-7</summary>

```text
app/retrieval/__init__.py:1-7
```

````text
"""Retrieval helpers for vector, full-text, and hybrid search."""

from app.retrieval.fulltext_search import search_fulltext
from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.vector_search import search_vector

__all__ = ["hybrid_search", "search_fulltext", "search_vector"]
````

</details>

<a id="baseline-chunk-1472"></a>
<details><summary><strong>60/10 baseline chunk 1472</strong> - app/retrieval/hybrid_search.py:1-60</summary>

```text
app/retrieval/hybrid_search.py:1-60
```

````text
"""Hybrid vector + full-text retrieval using reciprocal rank fusion."""

from __future__ import annotations

from app.retrieval.fulltext_search import search_fulltext
from app.retrieval.vector_search import search_vector


async def hybrid_search(
    session,
    repository_id: int,
    query_text: str,
    query_embedding: list[float],
    limit: int = 10,
) -> list[dict[str, object]]:
    """Fuse vector and FTS results using reciprocal rank fusion (RRF)."""

    if limit <= 0:
        return []

    vector_results = await search_vector(session, repository_id, query_embedding, limit=limit)
    fts_results = await search_fulltext(session, repository_id, query_text, limit=limit)

    vector_rank_by_id = {result["id"]: index + 1 for index, result in enumerate(vector_results)}
    fts_rank_by_id = {result["id"]: index + 1 for index, result in enumerate(fts_results)}

    vector_result_by_id = {result["id"]: result for result in vector_results}
    fts_result_by_id = {result["id"]: result for result in fts_results}

    candidate_ids = set(vector_rank_by_id) | set(fts_rank_by_id)
    fused: list[dict[str, object]] = []

    for chunk_id in candidate_ids:
        vector_rank = vector_rank_by_id.get(chunk_id)
        fts_rank = fts_rank_by_id.get(chunk_id)

        rrf_score = 0.0
        if vector_rank is not None:
            rrf_score += 1 / (60 + vector_rank)
        if fts_rank is not None:
            rrf_score += 1 / (60 + fts_rank)

        fused.append(
            {
                "id": chunk_id,
                "repository_id": repository_id,
                "file_path": (
                    vector_result_by_id.get(chunk_id, {}).get("file_path")
                    or fts_result_by_id.get(chunk_id, {}).get("file_path")
                ),
                "line_start": (
                    vector_result_by_id.get(chunk_id, {}).get("line_start")
                    or fts_result_by_id.get(chunk_id, {}).get("line_start")
                ),
                "line_end": (
                    vector_result_by_id.get(chunk_id, {}).get("line_end")
                    or fts_result_by_id.get(chunk_id, {}).get("line_end")
                ),
                "content": (
                    vector_result_by_id.get(chunk_id, {}).get("content")
````

</details>

<a id="baseline-chunk-1473"></a>
<details><summary><strong>60/10 baseline chunk 1473</strong> - app/retrieval/hybrid_search.py:51-70</summary>

```text
app/retrieval/hybrid_search.py:51-70
```

````text
                "line_start": (
                    vector_result_by_id.get(chunk_id, {}).get("line_start")
                    or fts_result_by_id.get(chunk_id, {}).get("line_start")
                ),
                "line_end": (
                    vector_result_by_id.get(chunk_id, {}).get("line_end")
                    or fts_result_by_id.get(chunk_id, {}).get("line_end")
                ),
                "content": (
                    vector_result_by_id.get(chunk_id, {}).get("content")
                    or fts_result_by_id.get(chunk_id, {}).get("content")
                ),
                "vector_score": vector_result_by_id.get(chunk_id, {}).get("distance"),
                "fts_score": fts_result_by_id.get(chunk_id, {}).get("score"),
                "rrf_score": rrf_score,
            }
        )

    fused.sort(key=lambda item: item["rrf_score"], reverse=True)
    return fused[:limit]
````

</details>

<a id="baseline-chunk-1474"></a>
<details><summary><strong>60/10 baseline chunk 1474</strong> - app/retrieval/vector_search.py:1-56</summary>

```text
app/retrieval/vector_search.py:1-56
```

````text
"""Vector similarity search over repository chunks."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chunk


async def search_vector(
    session: AsyncSession,
    repository_id: int,
    query_embedding: list[float],
    limit: int = 10,
) -> list[dict[str, object]]:
    """Return the top-N chunks by pgvector cosine distance for a repository."""

    if limit <= 0:
        return []

    distance = Chunk.embedding.cosine_distance(query_embedding).label("distance")
    query = (
        select(
            Chunk.id,
            Chunk.repository_id,
            Chunk.file_path,
            Chunk.line_start,
            Chunk.line_end,
            Chunk.content,
            distance,
        )
        .where(
            Chunk.repository_id == repository_id,
            Chunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(limit)
    )

    rows = (
        await session.execute(query)
    ).mappings().all()

    return [
        {
            "id": row["id"],
            "repository_id": row["repository_id"],
            "file_path": row["file_path"],
            "line_start": row["line_start"],
            "line_end": row["line_end"],
            "content": row["content"],
            "distance": float(row["distance"]),
        }
        for row in rows
    ]
````

</details>

<a id="baseline-chunk-1475"></a>
<details><summary><strong>60/10 baseline chunk 1475</strong> - scripts/__init__.py:1-1</summary>

```text
scripts/__init__.py:1-1
```

````text
"""Command-line scripts and importable repository utilities."""
````

</details>

<a id="baseline-chunk-1476"></a>
<details><summary><strong>60/10 baseline chunk 1476</strong> - scripts/embed_chunks.py:1-60</summary>

```text
scripts/embed_chunks.py:1-60
```

````text
"""Embed all unembedded chunks for a repository using the Gemini embedding API."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from urllib import error, request

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Chunk, Repository  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402

GEMINI_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSION = 768


def get_gemini_api_key() -> str:
    """Read the Gemini API key from environment configuration."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return api_key


def embed_text(text: str) -> list[float]:
    """Call the Gemini embeddings API for a single text value."""

    api_key = get_gemini_api_key()
    payload = json.dumps(
        {
            "model": GEMINI_MODEL,
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": EMBEDDING_DIMENSION,
        }
    ).encode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/{GEMINI_MODEL}:embedContent?key={api_key}"
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=60) as response:
            payload_data = json.loads(response.read().decode("utf-8"))
````

</details>

<a id="baseline-chunk-1477"></a>
<details><summary><strong>60/10 baseline chunk 1477</strong> - scripts/embed_chunks.py:51-110</summary>

```text
scripts/embed_chunks.py:51-110
```

````text
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=60) as response:
            payload_data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API request failed: {detail}") from exc

    values = payload_data.get("embedding", {}).get("values")
    if not isinstance(values, list):
        raise ValueError("Unexpected Gemini embedding response format")

    if len(values) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Unexpected embedding dimension: expected {EMBEDDING_DIMENSION}, got {len(values)}"
        )

    return [float(value) for value in values]


async def embed_repository_chunks(repo_name: str) -> tuple[int, int, int]:
    """Embed all unembedded chunks for the given repository name."""

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repo_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repo_name}")

        all_chunks = (
            await session.execute(
                select(Chunk).where(Chunk.repository_id == repository.id)
            )
        ).scalars().all()

        chunks_to_embed = [chunk for chunk in all_chunks if chunk.embedding is None]
        skipped = len(all_chunks) - len(chunks_to_embed)
        embedded = 0
        failed = 0

        for chunk in chunks_to_embed:
            try:
                chunk.embedding = embed_text(chunk.content)
                session.add(chunk)
                embedded += 1
            except Exception as exc:  # pragma: no cover - runtime network/API behavior
                print(
                    f"Failed to embed chunk {chunk.id} ({chunk.file_path}): {exc}",
                    file=sys.stderr,
                )
                failed += 1
            finally:
                await asyncio.sleep(1.5)
````

</details>

<a id="baseline-chunk-1478"></a>
<details><summary><strong>60/10 baseline chunk 1478</strong> - scripts/embed_chunks.py:101-149</summary>

```text
scripts/embed_chunks.py:101-149
```

````text
                session.add(chunk)
                embedded += 1
            except Exception as exc:  # pragma: no cover - runtime network/API behavior
                print(
                    f"Failed to embed chunk {chunk.id} ({chunk.file_path}): {exc}",
                    file=sys.stderr,
                )
                failed += 1
            finally:
                await asyncio.sleep(1.5)

        await session.commit()

        return embedded, failed, skipped


def parse_args() -> argparse.Namespace:
    """Parse the repository name argument."""

    parser = argparse.ArgumentParser(
        description="Embed all unembedded repository chunks with Gemini gemini-embedding-001."
    )
    parser.add_argument("repo_name", help="Repository name as stored in the database")
    return parser.parse_args()


def main() -> None:
    """Run the chunk embedding CLI."""

    args = parse_args()

    try:
        embedded, failed, skipped = asyncio.run(
            embed_repository_chunks(args.repo_name)
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)

    print(f"Chunks embedded: {embedded}")
    print(f"Chunks failed: {failed}")
    print(f"Chunks skipped: {skipped}")


if __name__ == "__main__":
    main()
````

</details>

<a id="baseline-chunk-1479"></a>
<details><summary><strong>60/10 baseline chunk 1479</strong> - scripts/ingest_repo.py:1-60</summary>

```text
scripts/ingest_repo.py:1-60
```

````text
"""Ingest a local repository into the IncidentWeave chunk schema."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import delete, select

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Chunk, Repository  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402

CHUNK_SIZE = 60
OVERLAP_SIZE = 10
IGNORE_DIRS = {
    ".git",
    ".kilo",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "migrations",
}


def iter_python_files(repo_root: Path):
    """Yield Python files under the repo root while skipping excluded directories."""

    for file_path in repo_root.rglob("*.py"):
        if not file_path.is_file():
            continue

        relative_parts = file_path.relative_to(repo_root).parts
        if any(part in IGNORE_DIRS for part in relative_parts):
            continue

        yield file_path


def chunk_lines(lines: list[str], chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP_SIZE):
    """Yield windows only when they add at least one new line beyond the prior window."""

    if not lines:
        return

    step = chunk_size - overlap
    if step <= 0:
        raise ValueError("chunk_size must be greater than overlap_size")

    previous_end = 0
    for start_index in range(0, len(lines), step):
````

</details>

<a id="baseline-chunk-1480"></a>
<details><summary><strong>60/10 baseline chunk 1480</strong> - scripts/ingest_repo.py:51-110</summary>

```text
scripts/ingest_repo.py:51-110
```

````text

    if not lines:
        return

    step = chunk_size - overlap
    if step <= 0:
        raise ValueError("chunk_size must be greater than overlap_size")

    previous_end = 0
    for start_index in range(0, len(lines), step):
        end_index = min(start_index + chunk_size, len(lines))

        if end_index <= previous_end:
            continue

        yield start_index, end_index
        previous_end = end_index


async def ingest_repository(repo_path: str, repo_name: str) -> tuple[int, int]:
    """Ingest all Python files under a local repository into the chunk table."""

    root = Path(repo_path).resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Repository path not found or not a directory: {repo_path}")

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repo_name)
        )

        if repository is None:
            repository = Repository(name=repo_name)
            session.add(repository)
            await session.flush()

        await session.execute(
            delete(Chunk).where(Chunk.repository_id == repository.id)
        )

        files_processed = 0
        chunks_to_create: list[Chunk] = []

        for file_path in sorted(iter_python_files(root)):
            files_processed += 1
            relative_path = file_path.relative_to(root).as_posix()

            content = file_path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()

            for start_index, end_index in chunk_lines(lines):
                window_lines = lines[start_index:end_index]
                chunk_content = "\n".join(window_lines)

                if not chunk_content.strip():
                    continue

                chunks_to_create.append(
                    Chunk(
                        repository_id=repository.id,
````

</details>

<a id="baseline-chunk-1481"></a>
<details><summary><strong>60/10 baseline chunk 1481</strong> - scripts/ingest_repo.py:101-158</summary>

```text
scripts/ingest_repo.py:101-158
```

````text
            for start_index, end_index in chunk_lines(lines):
                window_lines = lines[start_index:end_index]
                chunk_content = "\n".join(window_lines)

                if not chunk_content.strip():
                    continue

                chunks_to_create.append(
                    Chunk(
                        repository_id=repository.id,
                        content=chunk_content,
                        file_path=relative_path,
                        file_type="python",
                        document_type="code",
                        line_start=start_index + 1,
                        line_end=end_index,
                        function_name=None,
                        class_name=None,
                        symbol=None,
                    )
                )

        session.add_all(chunks_to_create)
        await session.commit()

        return files_processed, len(chunks_to_create)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Ingest a local Python repository into the IncidentWeave chunk table."
    )
    parser.add_argument("repo_path", help="Path to the local repository to ingest")
    parser.add_argument("repo_name", help="Repository name to store in the database")
    return parser.parse_args()


def main() -> None:
    """Run the repository ingestion CLI."""

    args = parse_args()

    try:
        files_processed, chunks_created = asyncio.run(
            ingest_repository(args.repo_path, args.repo_name)
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)

    print(f"Files processed: {files_processed}")
    print(f"Chunks created: {chunks_created}")


if __name__ == "__main__":
    main()
````

</details>

<a id="baseline-chunk-1488"></a>
<details><summary><strong>60/10 baseline chunk 1488</strong> - tests/conftest.py:1-11</summary>

```text
tests/conftest.py:1-11
```

````text
import asyncio
import sys

import pytest


@pytest.fixture
def anyio_backend() -> str:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return "asyncio"
````

</details>

<a id="baseline-chunk-1489"></a>
<details><summary><strong>60/10 baseline chunk 1489</strong> - tests/integration/test_database.py:1-60</summary>

```text
tests/integration/test_database.py:1-60
```

````text
"""PostgreSQL integration tests for the Phase 2 database foundation."""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Chunk, Repository

pytestmark = pytest.mark.integration


def _database_url() -> str:
    """Return the PostgreSQL URL used by the integration tests."""

    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://incidentweave:incidentweave@localhost:5432/incidentweave",
    ).replace("postgresql://", "postgresql+psycopg://", 1)


@pytest.mark.anyio
async def test_pgvector_extension_and_vector_column() -> None:
    """Verify pgvector is enabled and the chunk embedding is VECTOR(768)."""

    engine = create_async_engine(_database_url())

    async with engine.connect() as connection:
        extension_result = await connection.execute(
            text(
                "SELECT 1 FROM pg_extension "
                "WHERE extname = 'vector'"
            )
        )
        assert extension_result.scalar_one_or_none() == 1

        column_result = await connection.execute(
            text(
                "SELECT format_type(a.atttypid, a.atttypmod) "
                "FROM pg_attribute a "
                "JOIN pg_class c ON c.oid = a.attrelid "
                "WHERE c.relname = 'chunks' AND a.attname = 'embedding'"
            )
        )
        assert column_result.scalar_one() == "vector(768)"

    await engine.dispose()


@pytest.mark.anyio
async def test_repository_and_chunk_persistence() -> None:
    """Verify SQLAlchemy can persist and read a repository and chunk."""

    engine = create_async_engine(_database_url())
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
````

</details>

<a id="baseline-chunk-1490"></a>
<details><summary><strong>60/10 baseline chunk 1490</strong> - tests/integration/test_database.py:51-87</summary>

```text
tests/integration/test_database.py:51-87
```

````text
@pytest.mark.anyio
async def test_repository_and_chunk_persistence() -> None:
    """Verify SQLAlchemy can persist and read a repository and chunk."""

    engine = create_async_engine(_database_url())
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        repository = Repository(name="phase2-test-repository")
        session.add(repository)
        await session.flush()

        chunk = Chunk(
            repository_id=repository.id,
            content="Phase 2 persistence test",
            file_path="tests/example.py",
            file_type="python",
            line_start=1,
            line_end=1,
            embedding=[0.0] * 768,
        )
        session.add(chunk)
        await session.commit()

        await session.refresh(chunk)

        assert chunk.id is not None
        assert chunk.repository_id == repository.id

        await session.delete(repository)
        await session.commit()

    await engine.dispose()
````

</details>

<a id="baseline-chunk-1492"></a>
<details><summary><strong>60/10 baseline chunk 1492</strong> - tests/unit/test_db_models.py:1-33</summary>

```text
tests/unit/test_db_models.py:1-33
```

````text
from pgvector.sqlalchemy import VECTOR

from app.db.base import Base
from app.db.models import Audit, Chunk, Investigation


def test_all_phase2_models_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "repositories",
        "chunks",
        "investigations",
        "audit_records",
    }


def test_chunk_embedding_is_768_dimensions() -> None:
    column = Chunk.__table__.c.embedding

    assert isinstance(column.type, VECTOR)
    assert column.type.dim == 768


def test_phase2_relationships_are_defined() -> None:
    assert Chunk.repository.property.back_populates == "chunks"
    assert Investigation.repository.property.back_populates == "investigations"
    assert Audit.investigation.property.back_populates == "audit_records"


def test_required_chunk_indexes_exist() -> None:
    index_names = {index.name for index in Chunk.__table__.indexes}

    assert "ix_chunks_repository_id" in index_names
    assert "ix_chunks_repository_file_path" in index_names
````

</details>

<a id="baseline-chunk-1494"></a>
<details><summary><strong>60/10 baseline chunk 1494</strong> - tests/unit/test_hybrid_search.py:1-49</summary>

```text
tests/unit/test_hybrid_search.py:1-49
```

````text
import importlib

import pytest

hybrid_search_module = importlib.import_module("app.retrieval.hybrid_search")


@pytest.mark.anyio
async def test_hybrid_search_fuses_ranks_with_reciprocal_rank_math(monkeypatch) -> None:
    vector_results = [
        {"id": 10, "file_path": "vector-first.py", "line_start": 1, "line_end": 5,
         "content": "vector only", "distance": 0.1},
        {"id": 20, "file_path": "shared.py", "line_start": 6, "line_end": 10,
         "content": "shared result", "distance": 0.2},
    ]
    fts_results = [
        {"id": 20, "file_path": "shared.py", "line_start": 6, "line_end": 10,
         "content": "shared result", "score": 0.8},
        {"id": 30, "file_path": "fts-only.py", "line_start": 11, "line_end": 15,
         "content": "fts only", "score": 0.7},
    ]

    async def fake_search_vector(session, repository_id, query_embedding, limit=10):
        return vector_results[:limit]

    async def fake_search_fulltext(session, repository_id, query_text, limit=10):
        return fts_results[:limit]

    monkeypatch.setattr(hybrid_search_module, "search_vector", fake_search_vector)
    monkeypatch.setattr(hybrid_search_module, "search_fulltext", fake_search_fulltext)

    results = await hybrid_search_module.hybrid_search(
        session=None,
        repository_id=1,
        query_text="test query",
        query_embedding=[0.0] * 768,
        limit=5,
    )
    results_by_id = {result["id"]: result for result in results}

    shared_expected = 1 / (60 + 2) + 1 / (60 + 1)
    vector_only_expected = 1 / (60 + 1)
    fts_only_expected = 1 / (60 + 2)

    assert results_by_id[20]["rrf_score"] == shared_expected
    assert results_by_id[10]["rrf_score"] == vector_only_expected
    assert results_by_id[30]["rrf_score"] == fts_only_expected
    assert results_by_id[20]["rrf_score"] > results_by_id[10]["rrf_score"]
    assert results[0]["id"] == 20
````

</details>

<a id="baseline-chunk-1495"></a>
<details><summary><strong>60/10 baseline chunk 1495</strong> - tests/unit/test_ingest_repo.py:1-20</summary>

```text
tests/unit/test_ingest_repo.py:1-20
```

````text
import pytest

from scripts.ingest_repo import chunk_lines


@pytest.mark.parametrize(
    ("line_count", "expected_windows"),
    [
        (0, []),
        (5, [(0, 5)]),
        (201, [(0, 60), (50, 110), (100, 160), (150, 201)]),
    ],
)
def test_chunk_lines_uses_non_redundant_overlapping_windows(
    line_count: int,
    expected_windows: list[tuple[int, int]],
) -> None:
    lines = [f"line {index}" for index in range(line_count)]

    assert list(chunk_lines(lines)) == expected_windows
````

</details>

<a id="baseline-chunk-1496"></a>
<details><summary><strong>60/10 baseline chunk 1496</strong> - tests/unit/test_investigation_graph.py:1-60</summary>

```text
tests/unit/test_investigation_graph.py:1-60
```

````text
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

import app.investigation.graph as graph_module
from app.investigation.confidence import calibrate_confidence
from app.investigation.graph import create_investigation_graph


class FakeSessionContext:
    async def __aenter__(self) -> FakeSessionContext:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


def initial_state() -> dict[str, Any]:
    return {
        "repository_id": 4,
        "repository_name": "incidentweave-local",
        "repository_path": ".",
        "query": "how are async sessions configured?",
        "query_embedding": [0.1, 0.2],
        "search_limit": 5,
        "retry_limit": 10,
        "retry_count": 0,
        "retry_used": False,
        "retrieval_results": [],
        "evidence_check": {},
        "diagnosis": "",
        "confidence": "",
        "cited_chunk_ids": [],
        "model": "",
        "latency_ms": None,
        "calibration_note": "",
        "confidence_calibrated": False,
        "evidence_source": "hybrid",
        "tool_calls": [],
    }


def sufficient_result() -> dict[str, object]:
    return {
        "id": 136,
        "file_path": "app/db/session.py",
        "line_start": 1,
        "line_end": 46,
        "vector_score": 0.3,
        "fts_score": 0.5,
        "rrf_score": 0.04,
        "content": "AsyncSessionLocal = async_sessionmaker(...) ",
    }


def response_payload() -> dict[str, object]:
    return {
````

</details>

<a id="baseline-chunk-1497"></a>
<details><summary><strong>60/10 baseline chunk 1497</strong> - tests/unit/test_investigation_graph.py:51-110</summary>

```text
tests/unit/test_investigation_graph.py:51-110
```

````text
        "line_end": 46,
        "vector_score": 0.3,
        "fts_score": 0.5,
        "rrf_score": 0.04,
        "content": "AsyncSessionLocal = async_sessionmaker(...) ",
    }


def response_payload() -> dict[str, object]:
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "Diagnosis: AsyncSessionLocal uses async_sessionmaker.\n"
                                "Confidence: high\n"
                                "Evidence used: app/db/session.py, lines 1-46"
                            )
                        }
                    ]
                }
            }
        ]
    }


@pytest.mark.anyio
async def test_graph_retries_once_with_wider_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    limits: list[int] = []

    async def fake_hybrid_search(
        session: object,
        repository_id: int,
        query_text: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict[str, object]]:
        limits.append(limit)
        if len(limits) == 1:
            return [{"id": 1, "rrf_score": 0.01, "vector_score": 0.3}]
        return [sufficient_result()]

    def fake_generation(prompt: str) -> tuple[Mapping[str, object], int]:
        return response_payload(), 12

    monkeypatch.setattr(graph_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(graph_module, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(graph_module, "generate_investigation", fake_generation)

    result = await create_investigation_graph(calibrate_confidence).ainvoke(initial_state())

    assert limits == [5, 10]
    assert result["retry_count"] == 1
    assert result["retry_used"] is True
    assert result["diagnosis"] == "AsyncSessionLocal uses async_sessionmaker."


@pytest.mark.anyio
````

</details>

<a id="baseline-chunk-1498"></a>
<details><summary><strong>60/10 baseline chunk 1498</strong> - tests/unit/test_investigation_graph.py:101-155</summary>

```text
tests/unit/test_investigation_graph.py:101-155
```

````text

    result = await create_investigation_graph(calibrate_confidence).ainvoke(initial_state())

    assert limits == [5, 10]
    assert result["retry_count"] == 1
    assert result["retry_used"] is True
    assert result["diagnosis"] == "AsyncSessionLocal uses async_sessionmaker."


@pytest.mark.anyio
async def test_graph_stops_after_one_insufficient_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limits: list[int] = []

    async def fake_hybrid_search(
        session: object,
        repository_id: int,
        query_text: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict[str, object]]:
        limits.append(limit)
        return [{"id": len(limits), "rrf_score": 0.01, "vector_score": 0.3}]

    def unexpected_generation(prompt: str) -> tuple[Mapping[str, object], int]:
        raise AssertionError("Generation must not run after insufficient evidence")

    async def fake_grep_search_mcp(
        repository_name: str,
        repository_path: str,
        keyword: str,
        limit: int,
    ) -> tuple[list[dict[str, object]], None]:
        return [], None

    monkeypatch.setattr(graph_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(graph_module, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(graph_module, "generate_investigation", unexpected_generation)
    monkeypatch.setattr(graph_module, "call_grep_search_mcp", fake_grep_search_mcp)

    result = await create_investigation_graph(calibrate_confidence).ainvoke(initial_state())

    assert limits == [5, 10]
    assert result["retry_count"] == 1
    assert result["retry_used"] is True
    assert result["diagnosis"] == "INSUFFICIENT_EVIDENCE"
    assert result["confidence"] == "low"


def test_confidence_calibration_downgrades_borderline_retrieval() -> None:
    confidence, note = calibrate_confidence("high", 0.021, 0.3)

    assert confidence == "medium"
    assert "best RRF 0.021000 is below 0.032" in note
````

</details>

<a id="baseline-chunk-1499"></a>
<details><summary><strong>60/10 baseline chunk 1499</strong> - tests/unit/test_investigation_mcp_tools.py:1-60</summary>

```text
tests/unit/test_investigation_mcp_tools.py:1-60
```

````text
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

import app.investigation.graph as graph_module
from app.investigation.confidence import calibrate_confidence
from app.investigation.graph import create_investigation_graph
from app.investigation.mcp_server import grep_search


class FakeSessionContext:
    async def __aenter__(self) -> FakeSessionContext:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


def graph_state() -> dict[str, Any]:
    return {
        "repository_id": 4,
        "repository_name": "incidentweave-local",
        "repository_path": ".",
        "query": "quasarLatchOmega",
        "query_embedding": [0.1, 0.2],
        "search_limit": 5,
        "retry_limit": 10,
        "retry_count": 0,
        "retry_used": False,
        "retrieval_results": [],
        "evidence_check": {},
        "diagnosis": "",
        "confidence": "",
        "cited_chunk_ids": [],
        "model": "",
        "latency_ms": None,
        "calibration_note": "",
        "confidence_calibrated": False,
        "evidence_source": "hybrid",
        "tool_calls": [],
    }


def grep_match() -> dict[str, object]:
    return {
        "id": "grep-1",
        "repository_id": 4,
        "file_path": "src/fixture.py",
        "line_start": 1,
        "line_end": 1,
        "content": "# operational marker: quasarLatchOmega",
        "vector_score": None,
        "fts_score": None,
        "rrf_score": None,
    }

````

</details>

<a id="baseline-chunk-1500"></a>
<details><summary><strong>60/10 baseline chunk 1500</strong> - tests/unit/test_investigation_mcp_tools.py:51-110</summary>

```text
tests/unit/test_investigation_mcp_tools.py:51-110
```

````text
        "repository_id": 4,
        "file_path": "src/fixture.py",
        "line_start": 1,
        "line_end": 1,
        "content": "# operational marker: quasarLatchOmega",
        "vector_score": None,
        "fts_score": None,
        "rrf_score": None,
    }


def response_payload() -> dict[str, object]:
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "Diagnosis: The source contains quasarLatchOmega.\n"
                                "Confidence: high\n"
                                "Evidence used: src/fixture.py, lines 1-1"
                            )
                        }
                    ]
                }
            }
        ]
    }


def test_grep_search_finds_literal_case_insensitively_and_uses_ingest_exclusions(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    (source_dir / "fixture.py").write_text(
        "# marker: QuasarLatchOmega\n", encoding="utf-8"
    )
    ignored_dir = tmp_path / ".venv"
    ignored_dir.mkdir()
    (ignored_dir / "ignored.py").write_text(
        "# marker: quasarLatchOmega\n", encoding="utf-8"
    )

    matches = grep_search(tmp_path, "quasarlatchomega", repository_id=4, limit=10)

    assert len(matches) == 1
    assert matches[0]["file_path"] == "src/fixture.py"
    assert matches[0]["line_start"] == matches[0]["line_end"] == 1
    assert matches[0]["content"] == "# marker: QuasarLatchOmega"
    assert matches[0]["vector_score"] is None
    assert matches[0]["fts_score"] is None
    assert matches[0]["rrf_score"] is None


@pytest.mark.anyio
async def test_graph_calls_grep_only_after_both_hybrid_attempts_and_traces_all_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
````

</details>

<a id="baseline-chunk-1501"></a>
<details><summary><strong>60/10 baseline chunk 1501</strong> - tests/unit/test_investigation_mcp_tools.py:101-160</summary>

```text
tests/unit/test_investigation_mcp_tools.py:101-160
```

````text
    assert matches[0]["content"] == "# marker: QuasarLatchOmega"
    assert matches[0]["vector_score"] is None
    assert matches[0]["fts_score"] is None
    assert matches[0]["rrf_score"] is None


@pytest.mark.anyio
async def test_graph_calls_grep_only_after_both_hybrid_attempts_and_traces_all_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[tuple[str, object]] = []

    async def fake_hybrid_search(
        session: object,
        repository_id: int,
        query_text: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict[str, object]]:
        events.append(("hybrid_search", limit))
        return [{"id": limit, "rrf_score": 0.02, "vector_score": 0.7}]

    async def fake_grep_search_mcp(
        repository_name: str,
        repository_path: str,
        keyword: str,
        limit: int,
    ) -> tuple[list[dict[str, object]], None]:
        events.append(("grep_search", keyword))
        return [grep_match()], None

    def fake_generation(prompt: str) -> tuple[Mapping[str, object], int]:
        return response_payload(), 25

    monkeypatch.setattr(graph_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(graph_module, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(graph_module, "call_grep_search_mcp", fake_grep_search_mcp)
    monkeypatch.setattr(graph_module, "generate_investigation", fake_generation)

    result = await create_investigation_graph(calibrate_confidence).ainvoke(graph_state())

    assert events == [
        ("hybrid_search", 5),
        ("hybrid_search", 10),
        ("grep_search", "quasarLatchOmega"),
    ]
    assert result["diagnosis"] == "The source contains quasarLatchOmega."
    assert result["retry_used"] is True
    assert result["evidence_source"] == "literal"
    assert [attempt["tool"] for attempt in result["tool_calls"]] == [
        "hybrid_search",
        "hybrid_search",
        "grep_search",
    ]
    assert [attempt["stage"] for attempt in result["tool_calls"]] == [
        "initial",
        "widened_retry",
        "literal_fallback",
    ]
    assert result["tool_calls"][2]["outcome"] == {
````

</details>

<a id="baseline-chunk-1502"></a>
<details><summary><strong>60/10 baseline chunk 1502</strong> - tests/unit/test_investigation_mcp_tools.py:151-206</summary>

```text
tests/unit/test_investigation_mcp_tools.py:151-206
```

````text
        "hybrid_search",
        "hybrid_search",
        "grep_search",
    ]
    assert [attempt["stage"] for attempt in result["tool_calls"]] == [
        "initial",
        "widened_retry",
        "literal_fallback",
    ]
    assert result["tool_calls"][2]["outcome"] == {
        "match_count": 1,
        "sufficient": True,
        "reason": "Literal source matches were found.",
    }


@pytest.mark.anyio
async def test_graph_returns_insufficient_when_grep_has_no_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    async def fake_hybrid_search(
        session: object,
        repository_id: int,
        query_text: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict[str, object]]:
        events.append(f"hybrid:{limit}")
        return [{"id": limit, "rrf_score": 0.02, "vector_score": 0.7}]

    async def fake_grep_search_mcp(
        repository_name: str,
        repository_path: str,
        keyword: str,
        limit: int,
    ) -> tuple[list[dict[str, object]], None]:
        events.append("grep")
        return [], None

    def unexpected_generation(prompt: str) -> tuple[Mapping[str, object], int]:
        raise AssertionError("Generation must not run without sufficient evidence")

    monkeypatch.setattr(graph_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(graph_module, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(graph_module, "call_grep_search_mcp", fake_grep_search_mcp)
    monkeypatch.setattr(graph_module, "generate_investigation", unexpected_generation)

    result = await create_investigation_graph(calibrate_confidence).ainvoke(graph_state())

    assert events == ["hybrid:5", "hybrid:10", "grep"]
    assert result["diagnosis"] == "INSUFFICIENT_EVIDENCE"
    assert result["retry_count"] == 1
    assert len(result["tool_calls"]) == 3
    assert result["tool_calls"][-1]["outcome"]["sufficient"] is False
````

</details>

<a id="baseline-chunk-1503"></a>
<details><summary><strong>60/10 baseline chunk 1503</strong> - tests/unit/test_investigation_parsing.py:1-60</summary>

```text
tests/unit/test_investigation_parsing.py:1-60
```

````text
from __future__ import annotations

from app.investigation.guard import evaluate_evidence_sufficiency
from app.investigation.parsing import parse_investigation_response


def test_parse_investigation_response_handles_nonmatching_header_casing() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "diagnosis: Async sessions use async_sessionmaker\n\n"
                                "confidence: high\n\n"
                                "evidence used:\n"
                                "- app/db/session.py, lines 1-46"
                            )
                        }
                    ]
                }
            }
        ]
    }
    results = [{
        "id": 105,
        "file_path": "app/db/session.py",
        "line_start": 1,
        "line_end": 46,
        "vector_score": 0.1,
        "fts_score": 0.5,
        "rrf_score": 0.9,
        "content": (
            "AsyncSessionLocal = async_sessionmaker(bind=engine, "
            "class_=AsyncSession, expire_on_commit=False)"
        ),
    }]

    parsed = parse_investigation_response(payload, results)

    assert parsed["diagnosis"] == "Async sessions use async_sessionmaker"
    assert parsed["confidence"] == "high"
    assert parsed["cited_chunk_ids"] == ["105"]


def test_parse_investigation_response_matches_exact_file_path_without_lines() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "Diagnosis: AsyncSessionLocal is configured in "
                                "app/db/session.py using async_sessionmaker.\n"
                                "Confidence: high"
                            )
                        }
                    ]
````

</details>

<a id="baseline-chunk-1504"></a>
<details><summary><strong>60/10 baseline chunk 1504</strong> - tests/unit/test_investigation_parsing.py:51-95</summary>

```text
tests/unit/test_investigation_parsing.py:51-95
```

````text
                "content": {
                    "parts": [
                        {
                            "text": (
                                "Diagnosis: AsyncSessionLocal is configured in "
                                "app/db/session.py using async_sessionmaker.\n"
                                "Confidence: high"
                            )
                        }
                    ]
                }
            }
        ]
    }
    retrieved_results = [
        {
            "id": 136,
            "file_path": "app/db/session.py",
            "line_start": 1,
            "line_end": 46,
        }
    ]

    parsed = parse_investigation_response(payload, retrieved_results)

    assert parsed["cited_chunk_ids"] == ["136"]


def test_evaluate_evidence_sufficiency_rejects_empty_and_weak_results() -> None:
    empty_result = evaluate_evidence_sufficiency([])
    assert empty_result["is_sufficient"] is False
    assert empty_result["best_vector_score"] is None
    assert evaluate_evidence_sufficiency([
        {"id": 1, "rrf_score": 0.01, "vector_score": 0.1},
        {"id": 2, "rrf_score": 0.005, "vector_score": 0.2},
    ])["is_sufficient"] is False
    assert evaluate_evidence_sufficiency([
        {"id": 3, "rrf_score": 0.021, "vector_score": 0.4},
    ])["is_sufficient"] is True
    assert evaluate_evidence_sufficiency([
        {"id": 4, "rrf_score": 0.021, "vector_score": 0.5001},
    ])["is_sufficient"] is False
    assert evaluate_evidence_sufficiency([
        {"id": 5, "rrf_score": 0.021},
    ])["is_sufficient"] is False
````

</details>

<a id="baseline-chunk-1506"></a>
<details><summary><strong>60/10 baseline chunk 1506</strong> - tests/unit/test_investigation_persistence.py:51-110</summary>

```text
tests/unit/test_investigation_persistence.py:51-110
```

````text
            "rrf_score": 0.016,
            "content": "asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())",
        },
    ]
    response_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                            "Diagnosis: Async sessions are configured using async_sessionmaker.\n\n"
                            "Confidence: high\n\n"
                            "Evidence used:\n- app/db/session.py, lines 1-46"
                            )
                        }
                    ]
                }
            }
        ]
    }
    tool_call_trace = [
        {
            "tool": "hybrid_search",
            "stage": "initial",
            "parameters": {"limit": 5},
            "outcome": {"result_count": 5, "sufficient": False},
        },
        {
            "tool": "hybrid_search",
            "stage": "widened_retry",
            "parameters": {"limit": 10},
            "outcome": {"result_count": 10, "sufficient": False},
        },
        {
            "tool": "grep_search",
            "stage": "literal_fallback",
            "parameters": {"keyword": "async_sessionmaker"},
            "outcome": {"match_count": 1, "sufficient": True},
        },
    ]

    investigation = await persist_investigation(
        session=session,
        repository_id=17,
        query="how are async sessions configured?",
        response_payload=response_payload,
        retrieval_results=retrieval_results,
        model="gemini-3.5-flash-lite",
        latency_ms=2400,
        token_usage=128,
        final_confidence="medium",
        tool_call_trace=tool_call_trace,
    )

    assert investigation.query == "how are async sessions configured?"
    assert investigation.response == "Async sessions are configured using async_sessionmaker."
    assert investigation.model == "gemini-3.5-flash-lite"
    assert investigation.latency_ms == 2400
    assert investigation.token_usage == 128
````

</details>

<a id="baseline-chunk-1507"></a>
<details><summary><strong>60/10 baseline chunk 1507</strong> - tests/unit/test_investigation_persistence.py:101-120</summary>

```text
tests/unit/test_investigation_persistence.py:101-120
```

````text
        token_usage=128,
        final_confidence="medium",
        tool_call_trace=tool_call_trace,
    )

    assert investigation.query == "how are async sessions configured?"
    assert investigation.response == "Async sessions are configured using async_sessionmaker."
    assert investigation.model == "gemini-3.5-flash-lite"
    assert investigation.latency_ms == 2400
    assert investigation.token_usage == 128
    assert investigation.confidence == "medium"
    audit_rows = [item for item in session.added if isinstance(item, Audit)]
    assert len(audit_rows) == 1
    assert audit_rows[0].retrieved_chunk_ids == [105, 106]
    assert audit_rows[0].vector_scores == [0.288488584, 0.4]
    assert audit_rows[0].fts_scores == [0.5]
    assert audit_rows[0].rrf_scores == [0.032786885, 0.016]
    assert audit_rows[0].tool_calls["cited_chunk_ids"] == ["105"]
    assert audit_rows[0].tool_calls["attempts"] == tool_call_trace
    assert audit_rows[0].confidence == "medium"
````

</details>

### 100/20 experiment ? 39 unique retrieved chunks

<a id="experiment-chunk-1541"></a>
<details><summary><strong>100/20 experiment chunk 1541</strong> - app/__init__.py:1-1</summary>

```text
app/__init__.py:1-1
```

````text
"""IncidentWeave application package."""
````

</details>

<a id="experiment-chunk-1542"></a>
<details><summary><strong>100/20 experiment chunk 1542</strong> - app/config.py:1-20</summary>

```text
app/config.py:1-20
```

````text
"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the IncidentWeave application."""

    app_env: str = "development"
    database_url: str = "postgresql://incidentweave:incidentweave@localhost:5432/incidentweave"
    gemini_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
````

</details>

<a id="experiment-chunk-1543"></a>
<details><summary><strong>100/20 experiment chunk 1543</strong> - app/db/__init__.py:1-1</summary>

```text
app/db/__init__.py:1-1
```

````text
"""Database infrastructure for IncidentWeave."""
````

</details>

<a id="experiment-chunk-1547"></a>
<details><summary><strong>100/20 experiment chunk 1547</strong> - app/db/models/chunk.py:1-52</summary>

```text
app/db/models/chunk.py:1-52
```

````text
"""Chunk ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.repository import Repository

class Chunk(Base):
    """Persisted source/evidence chunk and structural metadata."""

    __tablename__ = "chunks"
    __table_args__ = (
        Index("ix_chunks_repository_id", "repository_id"),
        Index("ix_chunks_repository_file_path", "repository_id", "file_path"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(100))
    document_type: Mapped[str | None] = mapped_column(String(100))
    symbol: Mapped[str | None] = mapped_column(String(255))
    function_name: Mapped[str | None] = mapped_column(String(255))
    class_name: Mapped[str | None] = mapped_column(String(255))
    line_start: Mapped[int | None] = mapped_column(Integer)
    line_end: Mapped[int | None] = mapped_column(Integer)
    section: Mapped[str | None] = mapped_column(String(500))
    service: Mapped[str | None] = mapped_column(String(255))
    environment: Mapped[str | None] = mapped_column(String(100))
    incident_id: Mapped[str | None] = mapped_column(String(255))
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    embedding: Mapped[list[float] | None] = mapped_column(VECTOR(768))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    repository: Mapped[Repository] = relationship(back_populates="chunks")
````

</details>

<a id="experiment-chunk-1550"></a>
<details><summary><strong>100/20 experiment chunk 1550</strong> - app/db/session.py:1-46</summary>

```text
app/db/session.py:1-46
```

````text
"""SQLAlchemy engine and session management."""

from collections.abc import AsyncGenerator

from pgvector.psycopg import register_vector_async
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def _async_database_url(database_url: str) -> str:
    """Convert the configured PostgreSQL URL to the psycopg async dialect."""

    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url


engine = create_async_engine(
    _async_database_url(settings.database_url),
    pool_pre_ping=True,
)


@event.listens_for(engine.sync_engine, "connect")
def _register_pgvector(dbapi_connection: object, connection_record: object) -> None:
    """Register pgvector types for each async psycopg connection."""

    del connection_record
    dbapi_connection.run_async(register_vector_async)  # type: ignore[attr-defined]


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an application database session."""

    async with AsyncSessionLocal() as session:
        yield session
````

</details>

<a id="experiment-chunk-1552"></a>
<details><summary><strong>100/20 experiment chunk 1552</strong> - app/investigation/confidence.py:1-38</summary>

```text
app/investigation/confidence.py:1-38
```

````text
"""Calibrate model confidence against retrieval strength."""

from __future__ import annotations

MIN_CLEAR_RRF_SCORE = 0.032
MAX_CLEAR_VECTOR_DISTANCE = 0.4


def calibrate_confidence(
    reported_confidence: str,
    best_rrf_score: float | None,
    best_vector_score: float | None,
) -> tuple[str, str]:
    """Downgrade a high model rating when accepted evidence is borderline."""

    normalized_confidence = reported_confidence.strip().lower()
    if normalized_confidence != "high":
        return normalized_confidence, "Model confidence retained; calibration only downgrades high."

    weak_rrf = best_rrf_score is not None and best_rrf_score < MIN_CLEAR_RRF_SCORE
    borderline_distance = (
        best_vector_score is not None
        and best_vector_score > MAX_CLEAR_VECTOR_DISTANCE
    )
    if weak_rrf or borderline_distance:
        reasons: list[str] = []
        if weak_rrf:
            reasons.append(
                f"best RRF {best_rrf_score:.6f} is below {MIN_CLEAR_RRF_SCORE:.3f}"
            )
        if borderline_distance:
            reasons.append(
                "best vector distance "
                f"{best_vector_score:.6f} is above {MAX_CLEAR_VECTOR_DISTANCE:.1f}"
            )
        return "medium", "High confidence downgraded: " + "; ".join(reasons) + "."

    return "high", "High confidence retained; retrieval scores clear both calibration margins."
````

</details>

<a id="experiment-chunk-1553"></a>
<details><summary><strong>100/20 experiment chunk 1553</strong> - app/investigation/generation.py:1-71</summary>

```text
app/investigation/generation.py:1-71
```

````text
"""Gemini text generation for grounded investigations."""

from __future__ import annotations

import json
import os
import time
from time import perf_counter
from urllib import error, request

GEMINI_GENERATION_MODEL = "gemini-3.5-flash-lite"
GEMINI_GENERATION_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_GENERATION_MODEL}:generateContent"
)
GENERATION_TIMEOUT_SECONDS = 60
MAX_GENERATION_ATTEMPTS = 3
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def get_gemini_api_key() -> str:
    """Read the Gemini API key from the process environment."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return api_key


def generate_investigation(prompt: str) -> tuple[dict[str, object], int]:
    """Send a grounded prompt to Gemini and return its payload and latency."""

    payload = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
        }
    ).encode("utf-8")
    url = f"{GEMINI_GENERATION_ENDPOINT}?key={get_gemini_api_key()}"
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    last_error: Exception | None = None
    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        try:
            started_at = perf_counter()
            with request.urlopen(req, timeout=GENERATION_TIMEOUT_SECONDS) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
            latency_ms = round((perf_counter() - started_at) * 1000)
            if not isinstance(response_payload, dict):
                raise RuntimeError("Unexpected Gemini generation response format")
            return response_payload, latency_ms
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(
                f"Gemini generation failed with HTTP {exc.code}: {detail}"
            )
            if exc.code not in RETRYABLE_STATUS_CODES:
                raise last_error from exc
        except (error.URLError, TimeoutError, OSError) as exc:
            last_error = RuntimeError(f"Gemini generation connection failed: {exc}")

        if attempt < MAX_GENERATION_ATTEMPTS:
            time.sleep(2 ** (attempt - 1))

    raise RuntimeError(
        f"Gemini generation failed after {MAX_GENERATION_ATTEMPTS} attempts: {last_error}"
    ) from last_error
````

</details>

<a id="experiment-chunk-1554"></a>
<details><summary><strong>100/20 experiment chunk 1554</strong> - app/investigation/graph.py:1-100</summary>

```text
app/investigation/graph.py:1-100
```

````text
"""LangGraph orchestration for evidence-grounded investigations."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.db.session import AsyncSessionLocal
from app.investigation.generation import GEMINI_GENERATION_MODEL, generate_investigation
from app.investigation.guard import evaluate_evidence_sufficiency
from app.investigation.parsing import parse_investigation_response
from app.investigation.prompt import build_grounded_prompt
from app.retrieval.hybrid_search import hybrid_search


class InvestigationState(TypedDict):
    repository_id: int
    repository_name: str
    repository_path: str
    query: str
    query_embedding: list[float]
    search_limit: int
    retry_limit: int
    retry_count: int
    retry_used: bool
    retrieval_results: list[dict[str, object]]
    evidence_check: dict[str, object]
    diagnosis: str
    confidence: str
    cited_chunk_ids: list[str]
    model: str
    latency_ms: int | None
    calibration_note: str
    confidence_calibrated: bool
    evidence_source: str
    tool_calls: list[dict[str, object]]
    prompt: NotRequired[str]
    response_payload: NotRequired[Mapping[str, object]]
    grep_error: NotRequired[str | None]


ConfidenceCalibrator = Callable[
    [str, float | None, float | None], tuple[str, str]
]


async def call_grep_search_mcp(
    repository_name: str,
    repository_path: str,
    keyword: str,
    limit: int,
) -> tuple[list[dict[str, object]], str | None]:
    """Call grep_search over a real local MCP stdio subprocess."""

    repository_root = Path(__file__).resolve().parents[2]
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.investigation.mcp_server"],
        cwd=repository_root,
    )
    try:
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as client:
                await client.initialize()
                response = await client.call_tool(
                    "grep_search",
                    {
                        "repository_name": repository_name,
                        "repository_path": repository_path,
                        "keyword": keyword,
                        "limit": limit,
                    },
                )
        if response.isError:
            details = "; ".join(
                item.text for item in response.content if hasattr(item, "text")
            )
            return [], details or "MCP grep_search returned an error."
        text_parts = [item.text for item in response.content if hasattr(item, "text")]
        if not text_parts:
            return [], "MCP grep_search returned no text content."
        decoded = json.loads(text_parts[0])
        if not isinstance(decoded, list):
            return [], "MCP grep_search returned an unexpected result shape."
        return [item for item in decoded if isinstance(item, dict)], None
    except Exception as exc:
        return [], f"MCP grep_search failed: {type(exc).__name__}: {exc}"


def create_investigation_graph(calibrate_confidence: ConfidenceCalibrator):
    """Build the one-retry investigation graph around existing Phase 5 logic."""

    async def retrieve(state: InvestigationState) -> dict[str, object]:
````

</details>

<a id="experiment-chunk-1555"></a>
<details><summary><strong>100/20 experiment chunk 1555</strong> - app/investigation/graph.py:81-180</summary>

```text
app/investigation/graph.py:81-180
```

````text
        if response.isError:
            details = "; ".join(
                item.text for item in response.content if hasattr(item, "text")
            )
            return [], details or "MCP grep_search returned an error."
        text_parts = [item.text for item in response.content if hasattr(item, "text")]
        if not text_parts:
            return [], "MCP grep_search returned no text content."
        decoded = json.loads(text_parts[0])
        if not isinstance(decoded, list):
            return [], "MCP grep_search returned an unexpected result shape."
        return [item for item in decoded if isinstance(item, dict)], None
    except Exception as exc:
        return [], f"MCP grep_search failed: {type(exc).__name__}: {exc}"


def create_investigation_graph(calibrate_confidence: ConfidenceCalibrator):
    """Build the one-retry investigation graph around existing Phase 5 logic."""

    async def retrieve(state: InvestigationState) -> dict[str, object]:
        async with AsyncSessionLocal() as session:
            results = await hybrid_search(
                session,
                state["repository_id"],
                state["query"],
                state["query_embedding"],
                limit=state["search_limit"],
            )
        return {
            "retrieval_results": results,
            "evidence_source": "hybrid",
            "grep_error": None,
        }

    def guard(state: InvestigationState) -> dict[str, object]:
        evidence_source = state["evidence_source"]
        evidence_check = evaluate_evidence_sufficiency(
            state["retrieval_results"],
            evidence_source=evidence_source,
        )
        attempts = list(state["tool_calls"])
        if evidence_source == "literal":
            outcome: dict[str, object] = {
                "match_count": len(state["retrieval_results"]),
                "sufficient": evidence_check["is_sufficient"],
                "reason": evidence_check["reason"],
            }
            if state.get("grep_error"):
                outcome["error"] = state["grep_error"]
            attempts.append(
                {
                    "tool": "grep_search",
                    "stage": "literal_fallback",
                    "parameters": {
                        "repository_name": state["repository_name"],
                        "repository_path": state["repository_path"],
                        "keyword": state["query"],
                        "limit": 20,
                    },
                    "outcome": outcome,
                }
            )
        else:
            attempts.append(
                {
                    "tool": "hybrid_search",
                    "stage": "widened_retry" if state["retry_count"] else "initial",
                    "parameters": {
                        "repository_name": state["repository_name"],
                        "query": state["query"],
                        "limit": state["search_limit"],
                    },
                    "outcome": {
                        "result_count": len(state["retrieval_results"]),
                        "sufficient": evidence_check["is_sufficient"],
                        "reason": evidence_check["reason"],
                        "best_rrf_score": evidence_check["best_rrf_score"],
                        "best_vector_score": evidence_check["best_vector_score"],
                    },
                }
            )
        return {"evidence_check": evidence_check, "tool_calls": attempts}

    def route_after_guard(state: InvestigationState) -> str:
        if state["evidence_check"]["is_sufficient"]:
            return "continue"
        if state["evidence_source"] == "literal":
            return "stop"
        if state["retry_count"] == 0:
            return "retry"
        return "grep"

    def widen_search(state: InvestigationState) -> dict[str, object]:
        return {
            "search_limit": state["retry_limit"],
            "retry_count": state["retry_count"] + 1,
            "retry_used": True,
        }

    async def literal_search(state: InvestigationState) -> dict[str, object]:
````

</details>

<a id="experiment-chunk-1556"></a>
<details><summary><strong>100/20 experiment chunk 1556</strong> - app/investigation/graph.py:161-260</summary>

```text
app/investigation/graph.py:161-260
```

````text
            )
        return {"evidence_check": evidence_check, "tool_calls": attempts}

    def route_after_guard(state: InvestigationState) -> str:
        if state["evidence_check"]["is_sufficient"]:
            return "continue"
        if state["evidence_source"] == "literal":
            return "stop"
        if state["retry_count"] == 0:
            return "retry"
        return "grep"

    def widen_search(state: InvestigationState) -> dict[str, object]:
        return {
            "search_limit": state["retry_limit"],
            "retry_count": state["retry_count"] + 1,
            "retry_used": True,
        }

    async def literal_search(state: InvestigationState) -> dict[str, object]:
        matches, error = await call_grep_search_mcp(
            state["repository_name"],
            state["repository_path"],
            state["query"],
            20,
        )
        return {
            "retrieval_results": matches,
            "evidence_source": "literal",
            "grep_error": error,
        }

    def return_insufficient(state: InvestigationState) -> dict[str, object]:
        return {
            "diagnosis": "INSUFFICIENT_EVIDENCE",
            "confidence": "low",
            "cited_chunk_ids": [],
            "model": GEMINI_GENERATION_MODEL,
            "latency_ms": None,
            "calibration_note": "Not calibrated because evidence remained insufficient.",
            "confidence_calibrated": False,
            "tool_calls": state["tool_calls"],
        }

    def build_prompt(state: InvestigationState) -> dict[str, object]:
        return {
            "prompt": build_grounded_prompt(
                state["query"], state["retrieval_results"]
            )
        }

    def generate(state: InvestigationState) -> dict[str, object]:
        response_payload, latency_ms = generate_investigation(state["prompt"])
        return {
            "response_payload": response_payload,
            "latency_ms": latency_ms,
            "model": GEMINI_GENERATION_MODEL,
        }

    def parse(state: InvestigationState) -> dict[str, object]:
        parsed = parse_investigation_response(
            state["response_payload"], state["retrieval_results"]
        )
        return {
            "diagnosis": str(parsed["diagnosis"]),
            "confidence": str(parsed["confidence"]),
            "cited_chunk_ids": list(parsed["cited_chunk_ids"]),
        }

    def calibrate(state: InvestigationState) -> dict[str, object]:
        evidence_check = state["evidence_check"]
        confidence, note = calibrate_confidence(
            state["confidence"],
            evidence_check.get("best_rrf_score"),
            evidence_check.get("best_vector_score"),
        )
        return {
            "confidence": confidence,
            "calibration_note": note,
            "confidence_calibrated": confidence != state["confidence"],
        }

    graph = StateGraph(InvestigationState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("guard", guard)
    graph.add_node("widen_search", widen_search)
    graph.add_node("grep_search", literal_search)
    graph.add_node("insufficient", return_insufficient)
    graph.add_node("build_prompt", build_prompt)
    graph.add_node("generate", generate)
    graph.add_node("parse", parse)
    graph.add_node("calibrate", calibrate)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "guard")
    graph.add_conditional_edges(
        "guard",
        route_after_guard,
        {
            "continue": "build_prompt",
````

</details>

<a id="experiment-chunk-1558"></a>
<details><summary><strong>100/20 experiment chunk 1558</strong> - app/investigation/guard.py:1-70</summary>

```text
app/investigation/guard.py:1-70
```

````text
"""Evidence quality guard for grounded investigation results."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

MIN_ACCEPTABLE_RRF_SCORE = 0.016
MAX_ACCEPTABLE_VECTOR_DISTANCE = 0.5


def evaluate_evidence_sufficiency(
    retrieval_results: Sequence[Mapping[str, object]],
    *,
    evidence_source: str = "hybrid",
) -> dict[str, object]:
    """Evaluate hybrid scores or explicit literal-source matches."""

    if not retrieval_results:
        return {
            "is_sufficient": False,
            "reason": "No repository evidence was retrieved.",
            "best_rrf_score": None,
            "best_vector_score": None,
        }

    mapping_results = [result for result in retrieval_results if isinstance(result, Mapping)]
    if not mapping_results:
        return {
            "is_sufficient": False,
            "reason": "No repository evidence was retrieved.",
            "best_rrf_score": None,
            "best_vector_score": None,
        }

    if evidence_source == "literal":
        return {
            "is_sufficient": True,
            "reason": "Literal source matches were found.",
            "best_rrf_score": None,
            "best_vector_score": None,
        }

    best_rrf_score = max(float(result.get("rrf_score", 0.0)) for result in mapping_results)
    vector_scores = [
        float(score)
        for result in mapping_results
        if isinstance((score := result.get("vector_score")), (int, float))
    ]
    best_vector_score = min(vector_scores) if vector_scores else None

    is_sufficient = (
        best_rrf_score >= MIN_ACCEPTABLE_RRF_SCORE
        and best_vector_score is not None
        and best_vector_score <= MAX_ACCEPTABLE_VECTOR_DISTANCE
    )
    if best_rrf_score < MIN_ACCEPTABLE_RRF_SCORE:
        reason = "Best retrieved evidence score is below the minimum threshold."
    elif best_vector_score is None:
        reason = "No vector similarity score was retrieved."
    elif best_vector_score > MAX_ACCEPTABLE_VECTOR_DISTANCE:
        reason = "Best vector cosine distance is above the maximum threshold."
    else:
        reason = "Evidence strength meets the RRF and vector-distance requirements."

    return {
        "is_sufficient": is_sufficient,
        "reason": reason,
        "best_rrf_score": best_rrf_score,
        "best_vector_score": best_vector_score,
    }
````

</details>

<a id="experiment-chunk-1559"></a>
<details><summary><strong>100/20 experiment chunk 1559</strong> - app/investigation/mcp_server.py:1-100</summary>

```text
app/investigation/mcp_server.py:1-100
```

````text
"""Local MCP server exposing IncidentWeave retrieval tools."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select

from app.db.models import Repository
from app.db.session import AsyncSessionLocal
from app.retrieval.hybrid_search import hybrid_search
from scripts.ingest_repo import iter_python_files

server = FastMCP("IncidentWeave local investigation tools")


def grep_search(
    repository_path: str | Path,
    keyword: str,
    repository_id: int,
    limit: int = 20,
) -> list[dict[str, object]]:
    """Find case-insensitive literal matches in ingester-visible Python files."""

    if not keyword:
        raise ValueError("keyword must not be empty")
    if limit <= 0:
        return []

    root = Path(repository_path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Repository path is not a directory: {repository_path}")

    needle = keyword.casefold()
    matches: list[dict[str, object]] = []
    for file_path in sorted(iter_python_files(root)):
        relative_path = file_path.relative_to(root).as_posix()
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line_number, line in enumerate(lines, start=1):
            if needle not in line.casefold():
                continue
            matches.append(
                {
                    "id": f"grep-{len(matches) + 1}",
                    "repository_id": repository_id,
                    "file_path": relative_path,
                    "line_start": line_number,
                    "line_end": line_number,
                    "content": line,
                    "vector_score": None,
                    "fts_score": None,
                    "rrf_score": None,
                }
            )
            if len(matches) >= limit:
                return matches
    return matches


@server.tool(
    name="hybrid_search",
    description="Search one indexed repository with vector and PostgreSQL full-text retrieval.",
)
async def hybrid_search_tool(
    repository_name: str,
    query_text: str,
    query_embedding: list[float],
    limit: int = 10,
) -> str:
    """Call the existing hybrid search implementation for a repository."""

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repository_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repository_name}")
        results = await hybrid_search(
            session,
            repository.id,
            query_text,
            query_embedding,
            limit=limit,
        )
    return json.dumps(results)


@server.tool(
    name="grep_search",
    description=(
        "Find a literal keyword in Python source files under a local repository path; "
        "uses the same file and directory exclusions as ingestion."
    ),
)
async def grep_search_tool(
    repository_name: str,
````

</details>

<a id="experiment-chunk-1560"></a>
<details><summary><strong>100/20 experiment chunk 1560</strong> - app/investigation/mcp_server.py:81-131</summary>

```text
app/investigation/mcp_server.py:81-131
```

````text
            raise ValueError(f"Repository not found: {repository_name}")
        results = await hybrid_search(
            session,
            repository.id,
            query_text,
            query_embedding,
            limit=limit,
        )
    return json.dumps(results)


@server.tool(
    name="grep_search",
    description=(
        "Find a literal keyword in Python source files under a local repository path; "
        "uses the same file and directory exclusions as ingestion."
    ),
)
async def grep_search_tool(
    repository_name: str,
    repository_path: str,
    keyword: str,
    limit: int = 20,
) -> str:
    """Resolve the repository ID and search its raw local Python sources."""

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repository_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repository_name}")
        matches = grep_search(
            repository_path,
            keyword,
            repository.id,
            limit=limit,
        )
    return json.dumps(matches)


def main() -> None:
    """Run the MCP server over stdio."""

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
````

</details>

<a id="experiment-chunk-1561"></a>
<details><summary><strong>100/20 experiment chunk 1561</strong> - app/investigation/parsing.py:1-97</summary>

```text
app/investigation/parsing.py:1-97
```

````text
"""Parse grounded investigation responses from Gemini."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

_CONFIDENCE_PATTERN = re.compile(
    r"^\s*confidence\s*:\s*(high|medium|low)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_DIAGNOSIS_PATTERN = re.compile(
    r"^\s*diagnosis\s*:\s*(.+?)(?=\n\s*(?:confidence|evidence used)\s*:|\Z)",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)
_CHUNK_PATTERN = re.compile(r"chunk_id\s*[=:]\s*([A-Za-z0-9_-]+)", re.IGNORECASE)


def _response_text(response_payload: Mapping[str, object]) -> str:
    """Extract candidate text from the standard Gemini response shape."""

    candidates = response_payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        return ""

    candidate = candidates[0]
    if not isinstance(candidate, Mapping):
        return ""
    content = candidate.get("content")
    if not isinstance(content, Mapping):
        return ""
    parts = content.get("parts")
    if not isinstance(parts, list):
        return ""

    return "\n".join(
        str(part.get("text"))
        for part in parts
        if isinstance(part, Mapping) and isinstance(part.get("text"), str)
    ).strip()


def _matches_retrieved_citation(response_text: str, result: Mapping[str, object]) -> bool:
    """Return whether the model cited the result by ID or exact file path."""

    if not isinstance(result, Mapping):
        return False

    chunk_id = str(result.get("id"))
    if _CHUNK_PATTERN.search(response_text) and any(
        matched == chunk_id for matched in _CHUNK_PATTERN.findall(response_text)
    ):
        return True

    file_path = str(result.get("file_path") or "").strip()
    if not file_path:
        return False
    if file_path in response_text:
        return True

    line_start = result.get("line_start")
    line_end = result.get("line_end")
    if line_start is None or line_end is None:
        return False

    pattern = (
        rf"{re.escape(file_path)}.*?(?:lines?|line range)\s*[:=]?\s*"
        rf"{re.escape(str(line_start))}\s*[-–]\s*{re.escape(str(line_end))}"
    )
    return bool(re.search(pattern, response_text, re.IGNORECASE | re.DOTALL))


def parse_investigation_response(
    response_payload: Mapping[str, object],
    retrieved_results: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Extract diagnosis, categorical confidence, and cited retrieved chunk IDs."""

    response_text = _response_text(response_payload)
    cited_ids = [
        str(result.get("id"))
        for result in retrieved_results
        if _matches_retrieved_citation(response_text, result)
    ]

    confidence_match = _CONFIDENCE_PATTERN.search(response_text)
    confidence = confidence_match.group(1).lower() if confidence_match else "low"

    diagnosis_match = _DIAGNOSIS_PATTERN.search(response_text)
    diagnosis = diagnosis_match.group(1).strip() if diagnosis_match else "INSUFFICIENT_EVIDENCE"

    return {
        "diagnosis": diagnosis or "INSUFFICIENT_EVIDENCE",
        "confidence": confidence,
        "cited_chunk_ids": cited_ids,
        "raw_text": response_text,
    }
````

</details>

<a id="experiment-chunk-1562"></a>
<details><summary><strong>100/20 experiment chunk 1562</strong> - app/investigation/persistence.py:1-93</summary>

```text
app/investigation/persistence.py:1-93
```

````text
"""Persist investigation results and retrieval audit rows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.db.models import Audit, Investigation
from app.investigation.parsing import parse_investigation_response


async def persist_investigation(
    session,
    repository_id: int,
    query: str,
    response_payload: Mapping[str, object],
    retrieval_results: Sequence[Mapping[str, object]],
    model: str,
    latency_ms: int,
    token_usage: int | None = None,
    final_confidence: str | None = None,
    tool_call_trace: Sequence[Mapping[str, object]] | None = None,
) -> Investigation:
    """Create one Investigation row and one Audit row from a Gemini response."""

    parsed = parse_investigation_response(response_payload, retrieval_results)
    diagnosis = str(parsed.get("diagnosis") or "INSUFFICIENT_EVIDENCE")
    confidence = final_confidence or parsed.get("confidence")
    retrieved_chunk_ids: list[int] = []
    for result in retrieval_results:
        chunk_id = result.get("id")
        if isinstance(chunk_id, int):
            retrieved_chunk_ids.append(chunk_id)
        elif isinstance(chunk_id, str) and chunk_id.isdigit():
            retrieved_chunk_ids.append(int(chunk_id))
    cited_chunk_ids = [str(chunk_id) for chunk_id in parsed.get("cited_chunk_ids", [])]

    investigation = Investigation(
        repository_id=repository_id,
        query=query,
        response=diagnosis,
        model=model,
        latency_ms=latency_ms,
        token_usage=token_usage,
        confidence=str(confidence) if confidence else None,
    )
    session.add(investigation)
    await session.flush()

    audit = Audit(
        investigation_id=investigation.id,
        query=query,
        repository_id=repository_id,
        retrieved_chunk_ids=retrieved_chunk_ids,
        vector_scores=[
            float(item["vector_score"])
            for item in retrieval_results
            if isinstance(item.get("vector_score"), (int, float))
        ],
        fts_scores=[
            float(item["fts_score"])
            for item in retrieval_results
            if isinstance(item.get("fts_score"), (int, float))
        ],
        rrf_scores=[
            float(item["rrf_score"])
            for item in retrieval_results
            if isinstance(item.get("rrf_score"), (int, float))
        ],
        tool_calls={
            "attempts": [dict(item) for item in (tool_call_trace or [])],
            "cited_chunk_ids": cited_chunk_ids,
            "retrieval_results": [
                {
                    "id": item.get("id"),
                    "file_path": item.get("file_path"),
                    "line_start": item.get("line_start"),
                    "line_end": item.get("line_end"),
                    "vector_score": item.get("vector_score"),
                    "fts_score": item.get("fts_score"),
                    "rrf_score": item.get("rrf_score"),
                }
                for item in retrieval_results
            ],
        },
        model=model,
        response=diagnosis,
        latency_ms=latency_ms,
        token_usage=token_usage,
        confidence=str(confidence) if confidence else None,
    )
    session.add(audit)
    await session.commit()
    return investigation
````

</details>

<a id="experiment-chunk-1565"></a>
<details><summary><strong>100/20 experiment chunk 1565</strong> - app/retrieval/__init__.py:1-7</summary>

```text
app/retrieval/__init__.py:1-7
```

````text
"""Retrieval helpers for vector, full-text, and hybrid search."""

from app.retrieval.fulltext_search import search_fulltext
from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.vector_search import search_vector

__all__ = ["hybrid_search", "search_fulltext", "search_vector"]
````

</details>

<a id="experiment-chunk-1567"></a>
<details><summary><strong>100/20 experiment chunk 1567</strong> - app/retrieval/hybrid_search.py:1-70</summary>

```text
app/retrieval/hybrid_search.py:1-70
```

````text
"""Hybrid vector + full-text retrieval using reciprocal rank fusion."""

from __future__ import annotations

from app.retrieval.fulltext_search import search_fulltext
from app.retrieval.vector_search import search_vector


async def hybrid_search(
    session,
    repository_id: int,
    query_text: str,
    query_embedding: list[float],
    limit: int = 10,
) -> list[dict[str, object]]:
    """Fuse vector and FTS results using reciprocal rank fusion (RRF)."""

    if limit <= 0:
        return []

    vector_results = await search_vector(session, repository_id, query_embedding, limit=limit)
    fts_results = await search_fulltext(session, repository_id, query_text, limit=limit)

    vector_rank_by_id = {result["id"]: index + 1 for index, result in enumerate(vector_results)}
    fts_rank_by_id = {result["id"]: index + 1 for index, result in enumerate(fts_results)}

    vector_result_by_id = {result["id"]: result for result in vector_results}
    fts_result_by_id = {result["id"]: result for result in fts_results}

    candidate_ids = set(vector_rank_by_id) | set(fts_rank_by_id)
    fused: list[dict[str, object]] = []

    for chunk_id in candidate_ids:
        vector_rank = vector_rank_by_id.get(chunk_id)
        fts_rank = fts_rank_by_id.get(chunk_id)

        rrf_score = 0.0
        if vector_rank is not None:
            rrf_score += 1 / (60 + vector_rank)
        if fts_rank is not None:
            rrf_score += 1 / (60 + fts_rank)

        fused.append(
            {
                "id": chunk_id,
                "repository_id": repository_id,
                "file_path": (
                    vector_result_by_id.get(chunk_id, {}).get("file_path")
                    or fts_result_by_id.get(chunk_id, {}).get("file_path")
                ),
                "line_start": (
                    vector_result_by_id.get(chunk_id, {}).get("line_start")
                    or fts_result_by_id.get(chunk_id, {}).get("line_start")
                ),
                "line_end": (
                    vector_result_by_id.get(chunk_id, {}).get("line_end")
                    or fts_result_by_id.get(chunk_id, {}).get("line_end")
                ),
                "content": (
                    vector_result_by_id.get(chunk_id, {}).get("content")
                    or fts_result_by_id.get(chunk_id, {}).get("content")
                ),
                "vector_score": vector_result_by_id.get(chunk_id, {}).get("distance"),
                "fts_score": fts_result_by_id.get(chunk_id, {}).get("score"),
                "rrf_score": rrf_score,
            }
        )

    fused.sort(key=lambda item: item["rrf_score"], reverse=True)
    return fused[:limit]
````

</details>

<a id="experiment-chunk-1568"></a>
<details><summary><strong>100/20 experiment chunk 1568</strong> - app/retrieval/vector_search.py:1-56</summary>

```text
app/retrieval/vector_search.py:1-56
```

````text
"""Vector similarity search over repository chunks."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chunk


async def search_vector(
    session: AsyncSession,
    repository_id: int,
    query_embedding: list[float],
    limit: int = 10,
) -> list[dict[str, object]]:
    """Return the top-N chunks by pgvector cosine distance for a repository."""

    if limit <= 0:
        return []

    distance = Chunk.embedding.cosine_distance(query_embedding).label("distance")
    query = (
        select(
            Chunk.id,
            Chunk.repository_id,
            Chunk.file_path,
            Chunk.line_start,
            Chunk.line_end,
            Chunk.content,
            distance,
        )
        .where(
            Chunk.repository_id == repository_id,
            Chunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(limit)
    )

    rows = (
        await session.execute(query)
    ).mappings().all()

    return [
        {
            "id": row["id"],
            "repository_id": row["repository_id"],
            "file_path": row["file_path"],
            "line_start": row["line_start"],
            "line_end": row["line_end"],
            "content": row["content"],
            "distance": float(row["distance"]),
        }
        for row in rows
    ]
````

</details>

<a id="experiment-chunk-1569"></a>
<details><summary><strong>100/20 experiment chunk 1569</strong> - scripts/__init__.py:1-1</summary>

```text
scripts/__init__.py:1-1
```

````text
"""Command-line scripts and importable repository utilities."""
````

</details>

<a id="experiment-chunk-1570"></a>
<details><summary><strong>100/20 experiment chunk 1570</strong> - scripts/embed_chunks.py:1-100</summary>

```text
scripts/embed_chunks.py:1-100
```

````text
"""Embed all unembedded chunks for a repository using the Gemini embedding API."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from urllib import error, request

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Chunk, Repository  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402

GEMINI_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSION = 768


def get_gemini_api_key() -> str:
    """Read the Gemini API key from environment configuration."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return api_key


def embed_text(text: str) -> list[float]:
    """Call the Gemini embeddings API for a single text value."""

    api_key = get_gemini_api_key()
    payload = json.dumps(
        {
            "model": GEMINI_MODEL,
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": EMBEDDING_DIMENSION,
        }
    ).encode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/{GEMINI_MODEL}:embedContent?key={api_key}"
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=60) as response:
            payload_data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API request failed: {detail}") from exc

    values = payload_data.get("embedding", {}).get("values")
    if not isinstance(values, list):
        raise ValueError("Unexpected Gemini embedding response format")

    if len(values) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Unexpected embedding dimension: expected {EMBEDDING_DIMENSION}, got {len(values)}"
        )

    return [float(value) for value in values]


async def embed_repository_chunks(repo_name: str) -> tuple[int, int, int]:
    """Embed all unembedded chunks for the given repository name."""

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repo_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repo_name}")

        all_chunks = (
            await session.execute(
                select(Chunk).where(Chunk.repository_id == repository.id)
            )
        ).scalars().all()

        chunks_to_embed = [chunk for chunk in all_chunks if chunk.embedding is None]
        skipped = len(all_chunks) - len(chunks_to_embed)
        embedded = 0
        failed = 0

        for chunk in chunks_to_embed:
            try:
                chunk.embedding = embed_text(chunk.content)
````

</details>

<a id="experiment-chunk-1571"></a>
<details><summary><strong>100/20 experiment chunk 1571</strong> - scripts/embed_chunks.py:81-149</summary>

```text
scripts/embed_chunks.py:81-149
```

````text
        repository = await session.scalar(
            select(Repository).where(Repository.name == repo_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repo_name}")

        all_chunks = (
            await session.execute(
                select(Chunk).where(Chunk.repository_id == repository.id)
            )
        ).scalars().all()

        chunks_to_embed = [chunk for chunk in all_chunks if chunk.embedding is None]
        skipped = len(all_chunks) - len(chunks_to_embed)
        embedded = 0
        failed = 0

        for chunk in chunks_to_embed:
            try:
                chunk.embedding = embed_text(chunk.content)
                session.add(chunk)
                embedded += 1
            except Exception as exc:  # pragma: no cover - runtime network/API behavior
                print(
                    f"Failed to embed chunk {chunk.id} ({chunk.file_path}): {exc}",
                    file=sys.stderr,
                )
                failed += 1
            finally:
                await asyncio.sleep(1.5)

        await session.commit()

        return embedded, failed, skipped


def parse_args() -> argparse.Namespace:
    """Parse the repository name argument."""

    parser = argparse.ArgumentParser(
        description="Embed all unembedded repository chunks with Gemini gemini-embedding-001."
    )
    parser.add_argument("repo_name", help="Repository name as stored in the database")
    return parser.parse_args()


def main() -> None:
    """Run the chunk embedding CLI."""

    args = parse_args()

    try:
        embedded, failed, skipped = asyncio.run(
            embed_repository_chunks(args.repo_name)
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)

    print(f"Chunks embedded: {embedded}")
    print(f"Chunks failed: {failed}")
    print(f"Chunks skipped: {skipped}")


if __name__ == "__main__":
    main()
````

</details>

<a id="experiment-chunk-1572"></a>
<details><summary><strong>100/20 experiment chunk 1572</strong> - scripts/ingest_repo.py:1-100</summary>

```text
scripts/ingest_repo.py:1-100
```

````text
"""Ingest a local repository into the IncidentWeave chunk schema."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import delete, select

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Chunk, Repository  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402

CHUNK_SIZE = 60
OVERLAP_SIZE = 10
IGNORE_DIRS = {
    ".git",
    ".kilo",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "migrations",
}


def iter_python_files(repo_root: Path):
    """Yield Python files under the repo root while skipping excluded directories."""

    for file_path in repo_root.rglob("*.py"):
        if not file_path.is_file():
            continue

        relative_parts = file_path.relative_to(repo_root).parts
        if any(part in IGNORE_DIRS for part in relative_parts):
            continue

        yield file_path


def chunk_lines(lines: list[str], chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP_SIZE):
    """Yield windows only when they add at least one new line beyond the prior window."""

    if not lines:
        return

    step = chunk_size - overlap
    if step <= 0:
        raise ValueError("chunk_size must be greater than overlap_size")

    previous_end = 0
    for start_index in range(0, len(lines), step):
        end_index = min(start_index + chunk_size, len(lines))

        if end_index <= previous_end:
            continue

        yield start_index, end_index
        previous_end = end_index


async def ingest_repository(repo_path: str, repo_name: str) -> tuple[int, int]:
    """Ingest all Python files under a local repository into the chunk table."""

    root = Path(repo_path).resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Repository path not found or not a directory: {repo_path}")

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repo_name)
        )

        if repository is None:
            repository = Repository(name=repo_name)
            session.add(repository)
            await session.flush()

        await session.execute(
            delete(Chunk).where(Chunk.repository_id == repository.id)
        )

        files_processed = 0
        chunks_to_create: list[Chunk] = []

        for file_path in sorted(iter_python_files(root)):
            files_processed += 1
            relative_path = file_path.relative_to(root).as_posix()

            content = file_path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()

````

</details>

<a id="experiment-chunk-1573"></a>
<details><summary><strong>100/20 experiment chunk 1573</strong> - scripts/ingest_repo.py:81-158</summary>

```text
scripts/ingest_repo.py:81-158
```

````text

        if repository is None:
            repository = Repository(name=repo_name)
            session.add(repository)
            await session.flush()

        await session.execute(
            delete(Chunk).where(Chunk.repository_id == repository.id)
        )

        files_processed = 0
        chunks_to_create: list[Chunk] = []

        for file_path in sorted(iter_python_files(root)):
            files_processed += 1
            relative_path = file_path.relative_to(root).as_posix()

            content = file_path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()

            for start_index, end_index in chunk_lines(lines):
                window_lines = lines[start_index:end_index]
                chunk_content = "\n".join(window_lines)

                if not chunk_content.strip():
                    continue

                chunks_to_create.append(
                    Chunk(
                        repository_id=repository.id,
                        content=chunk_content,
                        file_path=relative_path,
                        file_type="python",
                        document_type="code",
                        line_start=start_index + 1,
                        line_end=end_index,
                        function_name=None,
                        class_name=None,
                        symbol=None,
                    )
                )

        session.add_all(chunks_to_create)
        await session.commit()

        return files_processed, len(chunks_to_create)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Ingest a local Python repository into the IncidentWeave chunk table."
    )
    parser.add_argument("repo_path", help="Path to the local repository to ingest")
    parser.add_argument("repo_name", help="Repository name to store in the database")
    return parser.parse_args()


def main() -> None:
    """Run the repository ingestion CLI."""

    args = parse_args()

    try:
        files_processed, chunks_created = asyncio.run(
            ingest_repository(args.repo_path, args.repo_name)
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)

    print(f"Files processed: {files_processed}")
    print(f"Chunks created: {chunks_created}")


if __name__ == "__main__":
    main()
````

</details>

<a id="experiment-chunk-1574"></a>
<details><summary><strong>100/20 experiment chunk 1574</strong> - scripts/investigate.py:1-100</summary>

```text
scripts/investigate.py:1-100
```

````text
"""Run the full investigation pipeline for a repository query."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import select  # noqa: E402

from app.db.models import Repository  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.investigation.confidence import calibrate_confidence  # noqa: E402
from app.investigation.generation import GEMINI_GENERATION_MODEL  # noqa: E402
from app.investigation.graph import create_investigation_graph  # noqa: E402
from app.investigation.persistence import persist_investigation  # noqa: E402
from scripts.embed_chunks import embed_text  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse repository name and query from the CLI."""

    parser = argparse.ArgumentParser(
        description=(
            "Run retrieval, grounding, generation, parsing, and persistence "
            "for one repository query."
        )
    )
    parser.add_argument("repo_name", help="Repository name stored in the database")
    parser.add_argument("query", help="Natural-language question to investigate")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum hybrid-search results to consider",
    )
    parser.add_argument(
        "--repo-path",
        default=str(REPO_ROOT),
        help="Local repository root used by the literal grep fallback",
    )
    return parser.parse_args()


async def investigate_repository(
    repo_name: str,
    query_text: str,
    limit: int = 5,
    repo_path: str = str(REPO_ROOT),
) -> dict[str, object]:
    """Perform the end-to-end grounded investigation flow for one query."""

    if limit <= 0:
        raise ValueError("--limit must be greater than zero")

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repo_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repo_name}")
        repository_id = repository.id

    query_embedding = embed_text(query_text)
    graph = create_investigation_graph(calibrate_confidence)
    result = await graph.ainvoke(
        {
            "repository_id": repository_id,
            "repository_name": repo_name,
            "repository_path": str(Path(repo_path).resolve()),
            "query": query_text,
            "query_embedding": query_embedding,
            "search_limit": limit,
            "retry_limit": limit * 2,
            "retry_count": 0,
            "retry_used": False,
            "retrieval_results": [],
            "evidence_check": {},
            "diagnosis": "",
            "confidence": "",
            "cited_chunk_ids": [],
            "model": GEMINI_GENERATION_MODEL,
            "latency_ms": None,
            "calibration_note": "",
            "confidence_calibrated": False,
            "evidence_source": "hybrid",
            "tool_calls": [],
        }
    )

    if not result["evidence_check"]["is_sufficient"]:
        return {
````

</details>

<a id="experiment-chunk-1575"></a>
<details><summary><strong>100/20 experiment chunk 1575</strong> - scripts/investigate.py:81-180</summary>

```text
scripts/investigate.py:81-180
```

````text
            "search_limit": limit,
            "retry_limit": limit * 2,
            "retry_count": 0,
            "retry_used": False,
            "retrieval_results": [],
            "evidence_check": {},
            "diagnosis": "",
            "confidence": "",
            "cited_chunk_ids": [],
            "model": GEMINI_GENERATION_MODEL,
            "latency_ms": None,
            "calibration_note": "",
            "confidence_calibrated": False,
            "evidence_source": "hybrid",
            "tool_calls": [],
        }
    )

    if not result["evidence_check"]["is_sufficient"]:
        return {
            "repository": repo_name,
            "query": query_text,
            "diagnosis": result["diagnosis"],
            "confidence": result["confidence"],
            "cited_chunk_ids": result["cited_chunk_ids"],
            "retrieval_results": result["retrieval_results"],
            "evidence_check": result["evidence_check"],
            "model": result["model"],
            "latency_ms": result["latency_ms"],
            "retry_used": result["retry_used"],
            "confidence_calibrated": result["confidence_calibrated"],
            "calibration_note": result["calibration_note"],
            "tool_calls": result["tool_calls"],
        }

    response_payload = result["response_payload"]
    async with AsyncSessionLocal() as session:
        investigation = await persist_investigation(
            session=session,
            repository_id=repository_id,
            query=query_text,
            response_payload=response_payload,
            retrieval_results=result["retrieval_results"],
            model=GEMINI_GENERATION_MODEL,
            latency_ms=result["latency_ms"],
            final_confidence=result["confidence"],
            token_usage=(
                response_payload.get("usageMetadata", {}).get("totalTokenCount")
                if isinstance(response_payload.get("usageMetadata"), dict)
                else None
            ),
            tool_call_trace=result["tool_calls"],
        )

    return {
        "repository": repo_name,
        "query": query_text,
        "diagnosis": result["diagnosis"] or investigation.response,
        "confidence": result["confidence"] or investigation.confidence,
        "cited_chunk_ids": result["cited_chunk_ids"],
        "retrieval_results": result["retrieval_results"],
        "evidence_check": result["evidence_check"],
        "model": GEMINI_GENERATION_MODEL,
        "latency_ms": result["latency_ms"],
        "retry_used": result["retry_used"],
        "confidence_calibrated": result["confidence_calibrated"],
        "calibration_note": result["calibration_note"],
        "tool_calls": result["tool_calls"],
    }


def main() -> None:
    """Run the investigation CLI and print a concise result."""

    args = parse_args()

    try:
        result = asyncio.run(
            investigate_repository(
                args.repo_name,
                args.query,
                limit=args.limit,
                repo_path=args.repo_path,
            )
        )
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(f"Repository: {result['repository']}")
    print(f"Query: {result['query']}")
    print(f"Diagnosis: {result['diagnosis']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Cited chunks: {result['cited_chunk_ids']}")
    print(f"Model: {result['model']}")
    print(f"Latency ms: {result['latency_ms']}")
    print(
        "Retry used: "
        f"{result['retry_used']}; confidence calibrated: "
        f"{result['confidence_calibrated']}"
````

</details>

<a id="experiment-chunk-1577"></a>
<details><summary><strong>100/20 experiment chunk 1577</strong> - scripts/search_repo.py:1-95</summary>

```text
scripts/search_repo.py:1-95
```

````text
"""Search repository chunks with hybrid vector and full-text retrieval."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import select  # noqa: E402

from app.db.models import Repository  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.retrieval.hybrid_search import hybrid_search  # noqa: E402
from scripts.embed_chunks import embed_text  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse the repository name and natural-language query."""

    parser = argparse.ArgumentParser(
        description="Search repository chunks using Gemini embeddings and hybrid retrieval."
    )
    parser.add_argument("repo_name", help="Repository name stored in the database")
    parser.add_argument("query", help="Natural-language question about the repository code")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of results")
    return parser.parse_args()


async def search_repository(
    repo_name: str,
    query_text: str,
    query_embedding: list[float],
    limit: int,
) -> list[dict[str, object]]:
    """Run hybrid search against the named repository."""

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repo_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repo_name}")

        return await hybrid_search(
            session,
            repository.id,
            query_text,
            query_embedding,
            limit=limit,
        )


def main() -> None:
    """Embed the query and print its top hybrid-search results."""

    args = parse_args()
    if args.limit <= 0:
        raise SystemExit("--limit must be greater than zero")

    try:
        query_embedding = embed_text(args.query)
        results = asyncio.run(
            search_repository(args.repo_name, args.query, query_embedding, args.limit)
        )
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(f"Repository: {args.repo_name}")
    print(f"Query: {args.query}")
    if not results:
        print("No matching chunks found.")
        return

    for rank, result in enumerate(results, start=1):
        content = " ".join(str(result.get("content") or "").split())
        if len(content) > 220:
            content = f"{content[:217]}..."
        print(
            f"{rank}. {result.get('file_path')}:{result.get('line_start')}-"
            f"{result.get('line_end')} rrf={result.get('rrf_score'):.6f}"
        )
        print(f"   {content}")


if __name__ == "__main__":
    main()
````

</details>

<a id="experiment-chunk-1578"></a>
<details><summary><strong>100/20 experiment chunk 1578</strong> - tests/conftest.py:1-11</summary>

```text
tests/conftest.py:1-11
```

````text
import asyncio
import sys

import pytest


@pytest.fixture
def anyio_backend() -> str:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return "asyncio"
````

</details>

<a id="experiment-chunk-1579"></a>
<details><summary><strong>100/20 experiment chunk 1579</strong> - tests/integration/test_database.py:1-87</summary>

```text
tests/integration/test_database.py:1-87
```

````text
"""PostgreSQL integration tests for the Phase 2 database foundation."""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Chunk, Repository

pytestmark = pytest.mark.integration


def _database_url() -> str:
    """Return the PostgreSQL URL used by the integration tests."""

    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://incidentweave:incidentweave@localhost:5432/incidentweave",
    ).replace("postgresql://", "postgresql+psycopg://", 1)


@pytest.mark.anyio
async def test_pgvector_extension_and_vector_column() -> None:
    """Verify pgvector is enabled and the chunk embedding is VECTOR(768)."""

    engine = create_async_engine(_database_url())

    async with engine.connect() as connection:
        extension_result = await connection.execute(
            text(
                "SELECT 1 FROM pg_extension "
                "WHERE extname = 'vector'"
            )
        )
        assert extension_result.scalar_one_or_none() == 1

        column_result = await connection.execute(
            text(
                "SELECT format_type(a.atttypid, a.atttypmod) "
                "FROM pg_attribute a "
                "JOIN pg_class c ON c.oid = a.attrelid "
                "WHERE c.relname = 'chunks' AND a.attname = 'embedding'"
            )
        )
        assert column_result.scalar_one() == "vector(768)"

    await engine.dispose()


@pytest.mark.anyio
async def test_repository_and_chunk_persistence() -> None:
    """Verify SQLAlchemy can persist and read a repository and chunk."""

    engine = create_async_engine(_database_url())
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        repository = Repository(name="phase2-test-repository")
        session.add(repository)
        await session.flush()

        chunk = Chunk(
            repository_id=repository.id,
            content="Phase 2 persistence test",
            file_path="tests/example.py",
            file_type="python",
            line_start=1,
            line_end=1,
            embedding=[0.0] * 768,
        )
        session.add(chunk)
        await session.commit()

        await session.refresh(chunk)

        assert chunk.id is not None
        assert chunk.repository_id == repository.id

        await session.delete(repository)
        await session.commit()

    await engine.dispose()
````

</details>

<a id="experiment-chunk-1581"></a>
<details><summary><strong>100/20 experiment chunk 1581</strong> - tests/unit/test_db_models.py:1-33</summary>

```text
tests/unit/test_db_models.py:1-33
```

````text
from pgvector.sqlalchemy import VECTOR

from app.db.base import Base
from app.db.models import Audit, Chunk, Investigation


def test_all_phase2_models_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "repositories",
        "chunks",
        "investigations",
        "audit_records",
    }


def test_chunk_embedding_is_768_dimensions() -> None:
    column = Chunk.__table__.c.embedding

    assert isinstance(column.type, VECTOR)
    assert column.type.dim == 768


def test_phase2_relationships_are_defined() -> None:
    assert Chunk.repository.property.back_populates == "chunks"
    assert Investigation.repository.property.back_populates == "investigations"
    assert Audit.investigation.property.back_populates == "audit_records"


def test_required_chunk_indexes_exist() -> None:
    index_names = {index.name for index in Chunk.__table__.indexes}

    assert "ix_chunks_repository_id" in index_names
    assert "ix_chunks_repository_file_path" in index_names
````

</details>

<a id="experiment-chunk-1583"></a>
<details><summary><strong>100/20 experiment chunk 1583</strong> - tests/unit/test_hybrid_search.py:1-49</summary>

```text
tests/unit/test_hybrid_search.py:1-49
```

````text
import importlib

import pytest

hybrid_search_module = importlib.import_module("app.retrieval.hybrid_search")


@pytest.mark.anyio
async def test_hybrid_search_fuses_ranks_with_reciprocal_rank_math(monkeypatch) -> None:
    vector_results = [
        {"id": 10, "file_path": "vector-first.py", "line_start": 1, "line_end": 5,
         "content": "vector only", "distance": 0.1},
        {"id": 20, "file_path": "shared.py", "line_start": 6, "line_end": 10,
         "content": "shared result", "distance": 0.2},
    ]
    fts_results = [
        {"id": 20, "file_path": "shared.py", "line_start": 6, "line_end": 10,
         "content": "shared result", "score": 0.8},
        {"id": 30, "file_path": "fts-only.py", "line_start": 11, "line_end": 15,
         "content": "fts only", "score": 0.7},
    ]

    async def fake_search_vector(session, repository_id, query_embedding, limit=10):
        return vector_results[:limit]

    async def fake_search_fulltext(session, repository_id, query_text, limit=10):
        return fts_results[:limit]

    monkeypatch.setattr(hybrid_search_module, "search_vector", fake_search_vector)
    monkeypatch.setattr(hybrid_search_module, "search_fulltext", fake_search_fulltext)

    results = await hybrid_search_module.hybrid_search(
        session=None,
        repository_id=1,
        query_text="test query",
        query_embedding=[0.0] * 768,
        limit=5,
    )
    results_by_id = {result["id"]: result for result in results}

    shared_expected = 1 / (60 + 2) + 1 / (60 + 1)
    vector_only_expected = 1 / (60 + 1)
    fts_only_expected = 1 / (60 + 2)

    assert results_by_id[20]["rrf_score"] == shared_expected
    assert results_by_id[10]["rrf_score"] == vector_only_expected
    assert results_by_id[30]["rrf_score"] == fts_only_expected
    assert results_by_id[20]["rrf_score"] > results_by_id[10]["rrf_score"]
    assert results[0]["id"] == 20
````

</details>

<a id="experiment-chunk-1584"></a>
<details><summary><strong>100/20 experiment chunk 1584</strong> - tests/unit/test_ingest_repo.py:1-20</summary>

```text
tests/unit/test_ingest_repo.py:1-20
```

````text
import pytest

from scripts.ingest_repo import chunk_lines


@pytest.mark.parametrize(
    ("line_count", "expected_windows"),
    [
        (0, []),
        (5, [(0, 5)]),
        (201, [(0, 60), (50, 110), (100, 160), (150, 201)]),
    ],
)
def test_chunk_lines_uses_non_redundant_overlapping_windows(
    line_count: int,
    expected_windows: list[tuple[int, int]],
) -> None:
    lines = [f"line {index}" for index in range(line_count)]

    assert list(chunk_lines(lines)) == expected_windows
````

</details>

<a id="experiment-chunk-1585"></a>
<details><summary><strong>100/20 experiment chunk 1585</strong> - tests/unit/test_investigation_graph.py:1-100</summary>

```text
tests/unit/test_investigation_graph.py:1-100
```

````text
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

import app.investigation.graph as graph_module
from app.investigation.confidence import calibrate_confidence
from app.investigation.graph import create_investigation_graph


class FakeSessionContext:
    async def __aenter__(self) -> FakeSessionContext:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


def initial_state() -> dict[str, Any]:
    return {
        "repository_id": 4,
        "repository_name": "incidentweave-local",
        "repository_path": ".",
        "query": "how are async sessions configured?",
        "query_embedding": [0.1, 0.2],
        "search_limit": 5,
        "retry_limit": 10,
        "retry_count": 0,
        "retry_used": False,
        "retrieval_results": [],
        "evidence_check": {},
        "diagnosis": "",
        "confidence": "",
        "cited_chunk_ids": [],
        "model": "",
        "latency_ms": None,
        "calibration_note": "",
        "confidence_calibrated": False,
        "evidence_source": "hybrid",
        "tool_calls": [],
    }


def sufficient_result() -> dict[str, object]:
    return {
        "id": 136,
        "file_path": "app/db/session.py",
        "line_start": 1,
        "line_end": 46,
        "vector_score": 0.3,
        "fts_score": 0.5,
        "rrf_score": 0.04,
        "content": "AsyncSessionLocal = async_sessionmaker(...) ",
    }


def response_payload() -> dict[str, object]:
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "Diagnosis: AsyncSessionLocal uses async_sessionmaker.\n"
                                "Confidence: high\n"
                                "Evidence used: app/db/session.py, lines 1-46"
                            )
                        }
                    ]
                }
            }
        ]
    }


@pytest.mark.anyio
async def test_graph_retries_once_with_wider_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    limits: list[int] = []

    async def fake_hybrid_search(
        session: object,
        repository_id: int,
        query_text: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict[str, object]]:
        limits.append(limit)
        if len(limits) == 1:
            return [{"id": 1, "rrf_score": 0.01, "vector_score": 0.3}]
        return [sufficient_result()]

    def fake_generation(prompt: str) -> tuple[Mapping[str, object], int]:
        return response_payload(), 12

    monkeypatch.setattr(graph_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(graph_module, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(graph_module, "generate_investigation", fake_generation)
````

</details>

<a id="experiment-chunk-1586"></a>
<details><summary><strong>100/20 experiment chunk 1586</strong> - tests/unit/test_investigation_graph.py:81-155</summary>

```text
tests/unit/test_investigation_graph.py:81-155
```

````text
    limits: list[int] = []

    async def fake_hybrid_search(
        session: object,
        repository_id: int,
        query_text: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict[str, object]]:
        limits.append(limit)
        if len(limits) == 1:
            return [{"id": 1, "rrf_score": 0.01, "vector_score": 0.3}]
        return [sufficient_result()]

    def fake_generation(prompt: str) -> tuple[Mapping[str, object], int]:
        return response_payload(), 12

    monkeypatch.setattr(graph_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(graph_module, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(graph_module, "generate_investigation", fake_generation)

    result = await create_investigation_graph(calibrate_confidence).ainvoke(initial_state())

    assert limits == [5, 10]
    assert result["retry_count"] == 1
    assert result["retry_used"] is True
    assert result["diagnosis"] == "AsyncSessionLocal uses async_sessionmaker."


@pytest.mark.anyio
async def test_graph_stops_after_one_insufficient_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limits: list[int] = []

    async def fake_hybrid_search(
        session: object,
        repository_id: int,
        query_text: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict[str, object]]:
        limits.append(limit)
        return [{"id": len(limits), "rrf_score": 0.01, "vector_score": 0.3}]

    def unexpected_generation(prompt: str) -> tuple[Mapping[str, object], int]:
        raise AssertionError("Generation must not run after insufficient evidence")

    async def fake_grep_search_mcp(
        repository_name: str,
        repository_path: str,
        keyword: str,
        limit: int,
    ) -> tuple[list[dict[str, object]], None]:
        return [], None

    monkeypatch.setattr(graph_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(graph_module, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(graph_module, "generate_investigation", unexpected_generation)
    monkeypatch.setattr(graph_module, "call_grep_search_mcp", fake_grep_search_mcp)

    result = await create_investigation_graph(calibrate_confidence).ainvoke(initial_state())

    assert limits == [5, 10]
    assert result["retry_count"] == 1
    assert result["retry_used"] is True
    assert result["diagnosis"] == "INSUFFICIENT_EVIDENCE"
    assert result["confidence"] == "low"


def test_confidence_calibration_downgrades_borderline_retrieval() -> None:
    confidence, note = calibrate_confidence("high", 0.021, 0.3)

    assert confidence == "medium"
    assert "best RRF 0.021000 is below 0.032" in note
````

</details>

<a id="experiment-chunk-1587"></a>
<details><summary><strong>100/20 experiment chunk 1587</strong> - tests/unit/test_investigation_mcp_tools.py:1-100</summary>

```text
tests/unit/test_investigation_mcp_tools.py:1-100
```

````text
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

import app.investigation.graph as graph_module
from app.investigation.confidence import calibrate_confidence
from app.investigation.graph import create_investigation_graph
from app.investigation.mcp_server import grep_search


class FakeSessionContext:
    async def __aenter__(self) -> FakeSessionContext:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


def graph_state() -> dict[str, Any]:
    return {
        "repository_id": 4,
        "repository_name": "incidentweave-local",
        "repository_path": ".",
        "query": "quasarLatchOmega",
        "query_embedding": [0.1, 0.2],
        "search_limit": 5,
        "retry_limit": 10,
        "retry_count": 0,
        "retry_used": False,
        "retrieval_results": [],
        "evidence_check": {},
        "diagnosis": "",
        "confidence": "",
        "cited_chunk_ids": [],
        "model": "",
        "latency_ms": None,
        "calibration_note": "",
        "confidence_calibrated": False,
        "evidence_source": "hybrid",
        "tool_calls": [],
    }


def grep_match() -> dict[str, object]:
    return {
        "id": "grep-1",
        "repository_id": 4,
        "file_path": "src/fixture.py",
        "line_start": 1,
        "line_end": 1,
        "content": "# operational marker: quasarLatchOmega",
        "vector_score": None,
        "fts_score": None,
        "rrf_score": None,
    }


def response_payload() -> dict[str, object]:
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "Diagnosis: The source contains quasarLatchOmega.\n"
                                "Confidence: high\n"
                                "Evidence used: src/fixture.py, lines 1-1"
                            )
                        }
                    ]
                }
            }
        ]
    }


def test_grep_search_finds_literal_case_insensitively_and_uses_ingest_exclusions(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    (source_dir / "fixture.py").write_text(
        "# marker: QuasarLatchOmega\n", encoding="utf-8"
    )
    ignored_dir = tmp_path / ".venv"
    ignored_dir.mkdir()
    (ignored_dir / "ignored.py").write_text(
        "# marker: quasarLatchOmega\n", encoding="utf-8"
    )

    matches = grep_search(tmp_path, "quasarlatchomega", repository_id=4, limit=10)

    assert len(matches) == 1
    assert matches[0]["file_path"] == "src/fixture.py"
    assert matches[0]["line_start"] == matches[0]["line_end"] == 1
````

</details>

<a id="experiment-chunk-1588"></a>
<details><summary><strong>100/20 experiment chunk 1588</strong> - tests/unit/test_investigation_mcp_tools.py:81-180</summary>

```text
tests/unit/test_investigation_mcp_tools.py:81-180
```

````text

def test_grep_search_finds_literal_case_insensitively_and_uses_ingest_exclusions(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    (source_dir / "fixture.py").write_text(
        "# marker: QuasarLatchOmega\n", encoding="utf-8"
    )
    ignored_dir = tmp_path / ".venv"
    ignored_dir.mkdir()
    (ignored_dir / "ignored.py").write_text(
        "# marker: quasarLatchOmega\n", encoding="utf-8"
    )

    matches = grep_search(tmp_path, "quasarlatchomega", repository_id=4, limit=10)

    assert len(matches) == 1
    assert matches[0]["file_path"] == "src/fixture.py"
    assert matches[0]["line_start"] == matches[0]["line_end"] == 1
    assert matches[0]["content"] == "# marker: QuasarLatchOmega"
    assert matches[0]["vector_score"] is None
    assert matches[0]["fts_score"] is None
    assert matches[0]["rrf_score"] is None


@pytest.mark.anyio
async def test_graph_calls_grep_only_after_both_hybrid_attempts_and_traces_all_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[tuple[str, object]] = []

    async def fake_hybrid_search(
        session: object,
        repository_id: int,
        query_text: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict[str, object]]:
        events.append(("hybrid_search", limit))
        return [{"id": limit, "rrf_score": 0.02, "vector_score": 0.7}]

    async def fake_grep_search_mcp(
        repository_name: str,
        repository_path: str,
        keyword: str,
        limit: int,
    ) -> tuple[list[dict[str, object]], None]:
        events.append(("grep_search", keyword))
        return [grep_match()], None

    def fake_generation(prompt: str) -> tuple[Mapping[str, object], int]:
        return response_payload(), 25

    monkeypatch.setattr(graph_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(graph_module, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(graph_module, "call_grep_search_mcp", fake_grep_search_mcp)
    monkeypatch.setattr(graph_module, "generate_investigation", fake_generation)

    result = await create_investigation_graph(calibrate_confidence).ainvoke(graph_state())

    assert events == [
        ("hybrid_search", 5),
        ("hybrid_search", 10),
        ("grep_search", "quasarLatchOmega"),
    ]
    assert result["diagnosis"] == "The source contains quasarLatchOmega."
    assert result["retry_used"] is True
    assert result["evidence_source"] == "literal"
    assert [attempt["tool"] for attempt in result["tool_calls"]] == [
        "hybrid_search",
        "hybrid_search",
        "grep_search",
    ]
    assert [attempt["stage"] for attempt in result["tool_calls"]] == [
        "initial",
        "widened_retry",
        "literal_fallback",
    ]
    assert result["tool_calls"][2]["outcome"] == {
        "match_count": 1,
        "sufficient": True,
        "reason": "Literal source matches were found.",
    }


@pytest.mark.anyio
async def test_graph_returns_insufficient_when_grep_has_no_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    async def fake_hybrid_search(
        session: object,
        repository_id: int,
        query_text: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict[str, object]]:
        events.append(f"hybrid:{limit}")
````

</details>

<a id="experiment-chunk-1589"></a>
<details><summary><strong>100/20 experiment chunk 1589</strong> - tests/unit/test_investigation_mcp_tools.py:161-206</summary>

```text
tests/unit/test_investigation_mcp_tools.py:161-206
```

````text
        "match_count": 1,
        "sufficient": True,
        "reason": "Literal source matches were found.",
    }


@pytest.mark.anyio
async def test_graph_returns_insufficient_when_grep_has_no_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    async def fake_hybrid_search(
        session: object,
        repository_id: int,
        query_text: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict[str, object]]:
        events.append(f"hybrid:{limit}")
        return [{"id": limit, "rrf_score": 0.02, "vector_score": 0.7}]

    async def fake_grep_search_mcp(
        repository_name: str,
        repository_path: str,
        keyword: str,
        limit: int,
    ) -> tuple[list[dict[str, object]], None]:
        events.append("grep")
        return [], None

    def unexpected_generation(prompt: str) -> tuple[Mapping[str, object], int]:
        raise AssertionError("Generation must not run without sufficient evidence")

    monkeypatch.setattr(graph_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(graph_module, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(graph_module, "call_grep_search_mcp", fake_grep_search_mcp)
    monkeypatch.setattr(graph_module, "generate_investigation", unexpected_generation)

    result = await create_investigation_graph(calibrate_confidence).ainvoke(graph_state())

    assert events == ["hybrid:5", "hybrid:10", "grep"]
    assert result["diagnosis"] == "INSUFFICIENT_EVIDENCE"
    assert result["retry_count"] == 1
    assert len(result["tool_calls"]) == 3
    assert result["tool_calls"][-1]["outcome"]["sufficient"] is False
````

</details>

<a id="experiment-chunk-1590"></a>
<details><summary><strong>100/20 experiment chunk 1590</strong> - tests/unit/test_investigation_parsing.py:1-95</summary>

```text
tests/unit/test_investigation_parsing.py:1-95
```

````text
from __future__ import annotations

from app.investigation.guard import evaluate_evidence_sufficiency
from app.investigation.parsing import parse_investigation_response


def test_parse_investigation_response_handles_nonmatching_header_casing() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "diagnosis: Async sessions use async_sessionmaker\n\n"
                                "confidence: high\n\n"
                                "evidence used:\n"
                                "- app/db/session.py, lines 1-46"
                            )
                        }
                    ]
                }
            }
        ]
    }
    results = [{
        "id": 105,
        "file_path": "app/db/session.py",
        "line_start": 1,
        "line_end": 46,
        "vector_score": 0.1,
        "fts_score": 0.5,
        "rrf_score": 0.9,
        "content": (
            "AsyncSessionLocal = async_sessionmaker(bind=engine, "
            "class_=AsyncSession, expire_on_commit=False)"
        ),
    }]

    parsed = parse_investigation_response(payload, results)

    assert parsed["diagnosis"] == "Async sessions use async_sessionmaker"
    assert parsed["confidence"] == "high"
    assert parsed["cited_chunk_ids"] == ["105"]


def test_parse_investigation_response_matches_exact_file_path_without_lines() -> None:
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "Diagnosis: AsyncSessionLocal is configured in "
                                "app/db/session.py using async_sessionmaker.\n"
                                "Confidence: high"
                            )
                        }
                    ]
                }
            }
        ]
    }
    retrieved_results = [
        {
            "id": 136,
            "file_path": "app/db/session.py",
            "line_start": 1,
            "line_end": 46,
        }
    ]

    parsed = parse_investigation_response(payload, retrieved_results)

    assert parsed["cited_chunk_ids"] == ["136"]


def test_evaluate_evidence_sufficiency_rejects_empty_and_weak_results() -> None:
    empty_result = evaluate_evidence_sufficiency([])
    assert empty_result["is_sufficient"] is False
    assert empty_result["best_vector_score"] is None
    assert evaluate_evidence_sufficiency([
        {"id": 1, "rrf_score": 0.01, "vector_score": 0.1},
        {"id": 2, "rrf_score": 0.005, "vector_score": 0.2},
    ])["is_sufficient"] is False
    assert evaluate_evidence_sufficiency([
        {"id": 3, "rrf_score": 0.021, "vector_score": 0.4},
    ])["is_sufficient"] is True
    assert evaluate_evidence_sufficiency([
        {"id": 4, "rrf_score": 0.021, "vector_score": 0.5001},
    ])["is_sufficient"] is False
    assert evaluate_evidence_sufficiency([
        {"id": 5, "rrf_score": 0.021},
    ])["is_sufficient"] is False
````

</details>

<a id="experiment-chunk-1591"></a>
<details><summary><strong>100/20 experiment chunk 1591</strong> - tests/unit/test_investigation_persistence.py:1-100</summary>

```text
tests/unit/test_investigation_persistence.py:1-100
```

````text
from __future__ import annotations

import pytest

from app.db.models import Audit
from app.investigation.persistence import persist_investigation


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.committed = False

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def add_all(self, objs: list[object]) -> None:
        self.added.extend(objs)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True


@pytest.mark.anyio
async def test_persist_investigation_creates_investigation_and_audit_rows() -> None:
    session = FakeSession()
    retrieval_results = [
        {
            "id": 105,
            "file_path": "app/db/session.py",
            "line_start": 1,
            "line_end": 46,
            "vector_score": 0.288488584,
            "fts_score": 0.5,
            "rrf_score": 0.032786885,
            "content": (
                "AsyncSessionLocal = async_sessionmaker(bind=engine, "
                "class_=AsyncSession, expire_on_commit=False)"
            ),
        },
        {
            "id": 106,
            "file_path": "tests/conftest.py",
            "line_start": 1,
            "line_end": 11,
            "vector_score": 0.4,
            "fts_score": None,
            "rrf_score": 0.016,
            "content": "asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())",
        },
    ]
    response_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                            "Diagnosis: Async sessions are configured using async_sessionmaker.\n\n"
                            "Confidence: high\n\n"
                            "Evidence used:\n- app/db/session.py, lines 1-46"
                            )
                        }
                    ]
                }
            }
        ]
    }
    tool_call_trace = [
        {
            "tool": "hybrid_search",
            "stage": "initial",
            "parameters": {"limit": 5},
            "outcome": {"result_count": 5, "sufficient": False},
        },
        {
            "tool": "hybrid_search",
            "stage": "widened_retry",
            "parameters": {"limit": 10},
            "outcome": {"result_count": 10, "sufficient": False},
        },
        {
            "tool": "grep_search",
            "stage": "literal_fallback",
            "parameters": {"keyword": "async_sessionmaker"},
            "outcome": {"match_count": 1, "sufficient": True},
        },
    ]

    investigation = await persist_investigation(
        session=session,
        repository_id=17,
        query="how are async sessions configured?",
        response_payload=response_payload,
        retrieval_results=retrieval_results,
        model="gemini-3.5-flash-lite",
        latency_ms=2400,
````

</details>

<a id="experiment-chunk-1592"></a>
<details><summary><strong>100/20 experiment chunk 1592</strong> - tests/unit/test_investigation_persistence.py:81-120</summary>

```text
tests/unit/test_investigation_persistence.py:81-120
```

````text
            "stage": "widened_retry",
            "parameters": {"limit": 10},
            "outcome": {"result_count": 10, "sufficient": False},
        },
        {
            "tool": "grep_search",
            "stage": "literal_fallback",
            "parameters": {"keyword": "async_sessionmaker"},
            "outcome": {"match_count": 1, "sufficient": True},
        },
    ]

    investigation = await persist_investigation(
        session=session,
        repository_id=17,
        query="how are async sessions configured?",
        response_payload=response_payload,
        retrieval_results=retrieval_results,
        model="gemini-3.5-flash-lite",
        latency_ms=2400,
        token_usage=128,
        final_confidence="medium",
        tool_call_trace=tool_call_trace,
    )

    assert investigation.query == "how are async sessions configured?"
    assert investigation.response == "Async sessions are configured using async_sessionmaker."
    assert investigation.model == "gemini-3.5-flash-lite"
    assert investigation.latency_ms == 2400
    assert investigation.token_usage == 128
    assert investigation.confidence == "medium"
    audit_rows = [item for item in session.added if isinstance(item, Audit)]
    assert len(audit_rows) == 1
    assert audit_rows[0].retrieved_chunk_ids == [105, 106]
    assert audit_rows[0].vector_scores == [0.288488584, 0.4]
    assert audit_rows[0].fts_scores == [0.5]
    assert audit_rows[0].rrf_scores == [0.032786885, 0.016]
    assert audit_rows[0].tool_calls["cited_chunk_ids"] == ["105"]
    assert audit_rows[0].tool_calls["attempts"] == tool_call_trace
    assert audit_rows[0].confidence == "medium"
````

</details>

## Adjacent indexed chunks (source context, not retrieval results)

For every unique top-five retrieved chunk, the question tables link to the immediately preceding and following non-empty chunk windows in that strategy's indexed source order. A missing side means the retrieved chunk is at that file boundary. Retrieved chunk contents remain in the preceding evidence library; adjacent windows not themselves among the top-five retrieved chunks are reproduced below. These windows are reconstructed using the run's pinned source SHA and the recorded chunk size/overlap, and each retrieved chunk was verified byte-for-byte against that source. They are provided for context and must not be mistaken for retrieved evidence or cited evidence.

### 60/10 baseline ? 3 additional adjacent chunks

<a id="baseline-context-da287e9758a22061"></a>
<details><summary><strong>Adjacent context ? app/investigation/generation.py:51-71</strong> (60/10 baseline)</summary>

```text
                response_payload = json.loads(response.read().decode("utf-8"))
            latency_ms = round((perf_counter() - started_at) * 1000)
            if not isinstance(response_payload, dict):
                raise RuntimeError("Unexpected Gemini generation response format")
            return response_payload, latency_ms
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(
                f"Gemini generation failed with HTTP {exc.code}: {detail}"
            )
            if exc.code not in RETRYABLE_STATUS_CODES:
                raise last_error from exc
        except (error.URLError, TimeoutError, OSError) as exc:
            last_error = RuntimeError(f"Gemini generation connection failed: {exc}")

        if attempt < MAX_GENERATION_ATTEMPTS:
            time.sleep(2 ** (attempt - 1))

    raise RuntimeError(
        f"Gemini generation failed after {MAX_GENERATION_ATTEMPTS} attempts: {last_error}"
    ) from last_error
```

</details>

<a id="baseline-context-d3469f915cc50c2d"></a>
<details><summary><strong>Adjacent context ? app/investigation/graph.py:201-260</strong> (60/10 baseline)</summary>

```text
            "confidence_calibrated": False,
            "tool_calls": state["tool_calls"],
        }

    def build_prompt(state: InvestigationState) -> dict[str, object]:
        return {
            "prompt": build_grounded_prompt(
                state["query"], state["retrieval_results"]
            )
        }

    def generate(state: InvestigationState) -> dict[str, object]:
        response_payload, latency_ms = generate_investigation(state["prompt"])
        return {
            "response_payload": response_payload,
            "latency_ms": latency_ms,
            "model": GEMINI_GENERATION_MODEL,
        }

    def parse(state: InvestigationState) -> dict[str, object]:
        parsed = parse_investigation_response(
            state["response_payload"], state["retrieval_results"]
        )
        return {
            "diagnosis": str(parsed["diagnosis"]),
            "confidence": str(parsed["confidence"]),
            "cited_chunk_ids": list(parsed["cited_chunk_ids"]),
        }

    def calibrate(state: InvestigationState) -> dict[str, object]:
        evidence_check = state["evidence_check"]
        confidence, note = calibrate_confidence(
            state["confidence"],
            evidence_check.get("best_rrf_score"),
            evidence_check.get("best_vector_score"),
        )
        return {
            "confidence": confidence,
            "calibration_note": note,
            "confidence_calibrated": confidence != state["confidence"],
        }

    graph = StateGraph(InvestigationState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("guard", guard)
    graph.add_node("widen_search", widen_search)
    graph.add_node("grep_search", literal_search)
    graph.add_node("insufficient", return_insufficient)
    graph.add_node("build_prompt", build_prompt)
    graph.add_node("generate", generate)
    graph.add_node("parse", parse)
    graph.add_node("calibrate", calibrate)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "guard")
    graph.add_conditional_edges(
        "guard",
        route_after_guard,
        {
            "continue": "build_prompt",
```

</details>

<a id="baseline-context-91193a850a6b0918"></a>
<details><summary><strong>Adjacent context ? tests/unit/test_investigation_persistence.py:1-60</strong> (60/10 baseline)</summary>

```text
from __future__ import annotations

import pytest

from app.db.models import Audit
from app.investigation.persistence import persist_investigation


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.committed = False

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def add_all(self, objs: list[object]) -> None:
        self.added.extend(objs)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True


@pytest.mark.anyio
async def test_persist_investigation_creates_investigation_and_audit_rows() -> None:
    session = FakeSession()
    retrieval_results = [
        {
            "id": 105,
            "file_path": "app/db/session.py",
            "line_start": 1,
            "line_end": 46,
            "vector_score": 0.288488584,
            "fts_score": 0.5,
            "rrf_score": 0.032786885,
            "content": (
                "AsyncSessionLocal = async_sessionmaker(bind=engine, "
                "class_=AsyncSession, expire_on_commit=False)"
            ),
        },
        {
            "id": 106,
            "file_path": "tests/conftest.py",
            "line_start": 1,
            "line_end": 11,
            "vector_score": 0.4,
            "fts_score": None,
            "rrf_score": 0.016,
            "content": "asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())",
        },
    ]
    response_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
```

</details>

### 100/20 experiment ? 2 additional adjacent chunks

<a id="experiment-context-6e7fbcc3f9f32261"></a>
<details><summary><strong>Adjacent context ? app/investigation/graph.py:241-273</strong> (100/20 experiment)</summary>

```text
        }

    graph = StateGraph(InvestigationState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("guard", guard)
    graph.add_node("widen_search", widen_search)
    graph.add_node("grep_search", literal_search)
    graph.add_node("insufficient", return_insufficient)
    graph.add_node("build_prompt", build_prompt)
    graph.add_node("generate", generate)
    graph.add_node("parse", parse)
    graph.add_node("calibrate", calibrate)

    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "guard")
    graph.add_conditional_edges(
        "guard",
        route_after_guard,
        {
            "continue": "build_prompt",
            "retry": "widen_search",
            "grep": "grep_search",
            "stop": "insufficient",
        },
    )
    graph.add_edge("widen_search", "retrieve")
    graph.add_edge("grep_search", "guard")
    graph.add_edge("insufficient", END)
    graph.add_edge("build_prompt", "generate")
    graph.add_edge("generate", "parse")
    graph.add_edge("parse", "calibrate")
    graph.add_edge("calibrate", END)
    return graph.compile()
```

</details>

<a id="experiment-context-fbbc24cd3500764e"></a>
<details><summary><strong>Adjacent context ? scripts/investigate.py:161-186</strong> (100/20 experiment)</summary>

```text
                args.query,
                limit=args.limit,
                repo_path=args.repo_path,
            )
        )
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(f"Repository: {result['repository']}")
    print(f"Query: {result['query']}")
    print(f"Diagnosis: {result['diagnosis']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Cited chunks: {result['cited_chunk_ids']}")
    print(f"Model: {result['model']}")
    print(f"Latency ms: {result['latency_ms']}")
    print(
        "Retry used: "
        f"{result['retry_used']}; confidence calibrated: "
        f"{result['confidence_calibrated']}"
    )
    print(f"Tool attempts: {len(result['tool_calls'])}")


if __name__ == "__main__":
    main()
```

</details>

## Gate 5 reviewer conclusion

- Reviewer: ______________________________
- Review date: ___________________________
- Questions reviewed: ______ / 24; responses reviewed: ______ / 96
- Current human position: **Neutral; 55% lean toward 100/20 and 45% toward 60/10; further review pending.**
- Overall end-to-end comparison: **No clear winner; no final verdict recorded.**
- Material exceptions or unresolved questions: ____________________________________________
- Gate 5 verdict: **PENDING — the current position does not mark Gate 5 as passed.**
- Production strategy remains 60/10 unless the maintainer separately approves an adoption decision after all required gates.

## Source artifacts

- Baseline report: `../../evaluation/results/runs/20261018T123627Z-2274338-baseline/report.json`.
- Baseline responses: `../../evaluation/results/runs/20261018T123627Z-2274338-baseline/pass-1.json` and `pass-2.json`.
- Experimental report: `../../evaluation/results/runs/20261018T124223Z-2274338-w100_o20/report.json`.
- Experimental responses: `../../evaluation/results/runs/20261018T124223Z-2274338-w100_o20/pass-1.json` and `pass-2.json`.
- Paired retrieval/gate comparison: `../../evaluation/results/runs/20261018T124223Z-2274338-w100_o20/chunking-comparison.json`.
- Approved adoption criteria: `chunking-experiment.md`, entry [004].
- Prior risk-focused answer comparison: [`chunking-strategy-decision-report.md`](02-decision-report.md), sections 4–6.
