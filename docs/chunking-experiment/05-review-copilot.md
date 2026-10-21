# Gate 5 independent review — Copilot

- **Reviewer:** Copilot
- **Model:** ChatGPT via Copilot SDK in VS Code; exact backend model build is not exposed to me
- **Date:** 2026-10-19

**Independence statement:** I read the human-review workbook, the Gate 5 approval context in [`chunking-experiment.md`](01-experiment-log.md), and relevant source files at pinned commit `62d0e58593bb22d187ec7930274b0457afd3be74`. I did not read any other `docs/gate5-review-*.md` file, and did not use automated outcome labels, keyword screens, or decision-report verdicts as evidence. I had no prior opinion on this experiment before reviewing the saved answers and source.

**Inspected:** all 24 saved questions and their four responses, cited chunk IDs, retrieval-span tables and response text; the source ranges relevant to the claims at the pinned commit; and the cited chunk bodies for material priority claims. I checked the cited path/line spans against the pinned source. I did not read every full, uncited top-five chunk body; where a response has no citation, I say so and score its grounding accordingly. I also searched the pinned repository for the unanswerable topics.

**Not inspected or done:** raw ignored run JSONs, `outcome_v2`, keyword labels, another reviewer’s file, database contents, or any live API. I did not run the experiment, call an API, or touch the database. This is a review, not an adoption approval.

## Priority questions

### Question: direct-04
**Question:** What constant controls the minimum RRF score?
**Expected answer / authoritative reference:** `MIN_ACCEPTABLE_RRF_SCORE = 0.016` controls the evidence-sufficiency minimum in `app/investigation/guard.py:7,52-60`. `MIN_CLEAR_RRF_SCORE = 0.032` in `app/investigation/confidence.py:5,20-25` is a separate confidence-calibration threshold.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 4 | 8 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

- **60/10 — Pass 1:** Gist: names `MIN_ACCEPTABLE_RRF_SCORE`. Citations: 1458, 1459. Correct and complete; both cited guard spans support the identifier. All scores are 10.
- **100/20 — Pass 1:** Gist: names the minimum and its `0.016` value, distinguishing the `0.032` clear-confidence threshold. Citations: 1558, 1552. Both claims and the distinction are supported by guard and confidence source. All scores are 10.
- **60/10 — Pass 2:** Gist: names the minimum constant. Citations: none. The answer is correct and complete, but provides no cited evidence; Correctness/Completeness 10, Grounding 4, Overall 8.
- **100/20 — Pass 2:** Gist: names the minimum and `0.016`, and distinguishes `MIN_CLEAR_RRF_SCORE = 0.032`. Citations: 1558, 1552. Accurate, relevant, and supported. All scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Better (minor; +2 Overall) |

#### Question-level conclusion
Pass 1 is equivalent. Pass 2 is more grounded because the baseline answer has no citation; the experimental answer usefully distinguishes the two similarly named constants.

### Question: direct-05
**Question:** What constant controls the maximum vector distance?
**Expected answer / authoritative reference:** `MAX_ACCEPTABLE_VECTOR_DISTANCE = 0.5` in `app/investigation/guard.py:8,52-60`.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

- **60/10 — Pass 1:** Gist: names the constant and value `0.5`. Citations: 1458, 1459. Both point into the guard implementation and support the answer. All scores are 10.
- **100/20 — Pass 1:** Gist: names the maximum-distance constant. Citations: 1558. The cited guard chunk defines it; the asked-for constant is fully identified. All scores are 10.
- **60/10 — Pass 2:** Gist: names the constant and `0.5`. Citations: 1458, 1459. Correct and supported. All scores are 10.
- **100/20 — Pass 2:** Gist: names the constant and `0.5`. Citations: 1558. Correct, complete, and directly supported. All scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
All four answers are fully correct and grounded; neither strategy has a material advantage.

### Question: direct-08
**Question:** Where is the final confidence passed into persistence?
**Expected answer / authoritative reference:** The call in `scripts/investigate.py:118-126` passes `final_confidence=result["confidence"]` to `persist_investigation`; the parameter is declared in `app/investigation/persistence.py:11-23`. The unit test also supplies `final_confidence="medium"` at `tests/unit/test_investigation_persistence.py:93-103`.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | — | 0 | 0 | 2 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | — | 0 | 0 | 2 |
| 100/20 — Pass 2 | 10 | 10 | 9 | 9 |

- **60/10 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE` abstention. Citations: none. The question is answerable in source, so the response omits the answer; per convention Correctness is —, Completeness 0, Overall 2.
- **100/20 — Pass 1:** Gist: names `final_confidence=result["confidence"]` at the persistence call and the test’s explicit `"medium"` value. Citations: 1592, 1575. Both cited spans support the call/test detail. All scores are 10.
- **60/10 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE` abstention. Citations: none. Still fails to answer an answerable question; Correctness is —, Completeness 0, Overall 2.
- **100/20 — Pass 2:** Gist: identifies the `final_confidence` parameter, and mentions both the script call and a test example. Citations: 1575. The script span supports the main answer, but the test example is not separately cited; 10/10/9/9.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Better (clear; +8 Overall) |
| Pass 2 | 100/20 against 60/10 | Better (clear; +7 Overall) |

#### Question-level conclusion
The experiment answers this question correctly in both passes; the baseline abstains in both despite an authoritative source location.

### Question: paraphrased-03
**Question:** How does the project turn text into numeric vectors before storage?
**Expected answer / authoritative reference:** `scripts/embed_chunks.py:25-26,38-74,100` calls Gemini’s `models/gemini-embedding-001` endpoint, requests 768 dimensions, validates/converts the returned values, and assigns them to `chunk.embedding`. The `Chunk.embedding` vector column is in `app/db/models/chunk.py:45`.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

- **60/10 — Pass 1:** Gist: describes the API request, 768-value validation/conversion, and assignment to the chunk. Citations: 1477. The cited embedder span supports those details. All scores are 10.
- **100/20 — Pass 1:** Gist: identifies the Gemini embedding model, API request, and 768-dimensional float output. Citations: 1570. This supports the asked process; omitting the later assignment is not material. All scores are 10.
- **60/10 — Pass 2:** Gist: explains the API response parsing, validation/conversion, storage assignment, and vector column. Citations: 1477, 1444, 1492. The embedder and model spans support the claims; all scores are 10.
- **100/20 — Pass 2:** Gist: explains the model/API call and float vector assignment. Citations: 1570. Correct and adequately supported. All scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
All answers accurately describe vector creation. The baseline gives more implementation detail in pass 2, but no material answer-quality difference results.

### Question: paraphrased-05
**Question:** What stops a weak search result from reaching the language model?
**Expected answer / authoritative reference:** `evaluate_evidence_sufficiency` in `app/investigation/guard.py:11-63` checks retrieval thresholds; `route_after_guard` and the graph edges in `app/investigation/graph.py:164-171,254-269` route weak results through retry/grep or to `INSUFFICIENT_EVIDENCE`, rather than prompt generation. A sufficient result alone routes to prompt building.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

- **60/10 — Pass 1:** Gist: guard checks sufficiency; weak evidence retries/falls back and ultimately returns insufficient without generation. Citations: 1454, 1455, 1498, 1502, 1504. Graph and test/tool spans support the flow. All scores are 10.
- **100/20 — Pass 1:** Gist: gives both thresholds and explains retry/grep/insufficient routing. Citations: 1586, 1554, 1585, 1558, 1556. The thresholds and routing match source. All scores are 10.
- **60/10 — Pass 2:** Gist: explains guard routing, retry, literal fallback and stopping before generation. Citations: 1454, 1455, 1498, 1502, 1504. Correct and adequately cited. All scores are 10.
- **100/20 — Pass 2:** Gist: gives the thresholds and same retry/grep/stop behavior. Citations: 1586, 1554, 1585, 1558, 1556. Supported by guard and graph. All scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
Both strategies answer the control-flow question correctly and with relevant citations. The additional thresholds in the experimental answers are supported but do not make the baseline incomplete.

### Question: paraphrased-08
**Question:** What record keeps the retrieved evidence and response metadata together?
**Expected answer / authoritative reference:** The `Audit` row/model stores retrieval IDs/scores, tool calls/retrieval details, and query/response metadata: `app/db/models/audit.py:18-52` and `app/investigation/persistence.py:49-80`. The persistence test verifies these fields at `tests/unit/test_investigation_persistence.py:112-120`.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | — | 0 | 0 | 2 |
| 100/20 — Pass 1 | 10 | 10 | 4 | 8 |
| 60/10 — Pass 2 | 4 | 4 | 3 | 4 |
| 100/20 — Pass 2 | 10 | 10 | 4 | 8 |

- **60/10 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE` abstention. Citations: none. This is answerable and the response does not name the record; Correctness is —, Completeness 0, Overall 2.
- **100/20 — Pass 1:** Gist: identifies `Audit` and lists its retrieval and response metadata. Citations: none. Correct and complete, but unsupported by a citation; Correctness/Completeness 10, Grounding 4, Overall 8.
- **60/10 — Pass 2:** Gist: says `persist_investigation` stores an “investigation record” with retrieval and response data. Citations: 1506. It does not identify `Audit`; cited test span ends before the Audit assertions, and the Investigation row itself is not the record storing retrieval details. Partly wrong and poorly supported: 4/4/3/4.
- **100/20 — Pass 2:** Gist: correctly names the `Audit` record and its retrieval/response fields. Citations: none. Complete and factually correct, but uncited; Correctness/Completeness 10, Grounding 4, Overall 8.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Better (clear; +6 Overall) |
| Pass 2 | 100/20 against 60/10 | Better (clear; +4 Overall) |

#### Question-level conclusion
The experiment supplies the right record in both passes, improving substantially over an abstention and a misleading baseline pass-2 answer. Its own answers are uncited, so the correctness gain does not remove the grounding weakness.

### Question: paraphrased-07
**Question:** How can the application find an exact phrase in its local source tree?
**Expected answer / authoritative reference:** The `grep_search` MCP tool searches local Python files using case-insensitive literal substring matching (`app/investigation/mcp_server.py:16,21-61,92-119`); ingestion file selection/exclusions are in `scripts/ingest_repo.py:35-46`.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 4 | 8 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

- **60/10 — Pass 1:** Gist: use `grep_search`/`call_grep_search_mcp` for literal matching in local Python files with ingestion exclusions. Citations: 1500, 1461, 1501, 1453, 1499. Relevant tool/graph spans support it. All scores are 10.
- **100/20 — Pass 1:** Gist: same local literal search behavior. Citations: none. Correct and complete, but the uncited answer has a grounding weakness; 10/10/4/8.
- **60/10 — Pass 2:** Gist: use `grep_search` for a literal keyword in local Python files. Citations: 1461, 1453. These point to MCP/graph implementation and support the answer. All scores are 10.
- **100/20 — Pass 2:** Gist: identifies the `grep_search` function/tool and local source/exclusion behavior. Citations: 1588, 1587, 1560. Relevant test and tool spans support it. All scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Worse (minor; −2 Overall) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
The answer content is equivalent; pass 1 loses grounding because the experiment supplies no citations. Pass 2 is equivalent and cited in both arms.

## Remaining questions

### Question: direct-01
**Question:** How is AsyncSessionLocal configured?
**Expected answer / authoritative reference:** `async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)` in `app/db/session.py:35-39`; engine setup and `get_db_session` are at lines 12-32 and 42-46.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

- **60/10 — Pass 1:** Gist: gives the sessionmaker, engine binding, session class, and expiration setting. Citations: 1447. The cited `session.py:1-46` span supports all claims. All scores are 10.
- **100/20 — Pass 1:** Gist: same configuration plus async URL conversion, pre-ping, and pgvector event registration. Citations: 1550. These additional details also match the cited source. All scores are 10.
- **60/10 — Pass 2:** Gist: gives the same configuration. Citations: 1447. Accurate, complete, directly supported. All scores are 10.
- **100/20 — Pass 2:** Gist: gives the configuration and related engine setup. Citations: 1550. All details are supported and relevant. All scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
Both strategies answer correctly with relevant evidence. The experiment adds valid configuration context, not a material quality improvement.

### Question: direct-02
**Question:** What chunk size does ingest_repo.py use?
**Expected answer / authoritative reference:** `CHUNK_SIZE = 60` in `scripts/ingest_repo.py:22`; the default parameter and overlap logic are at lines 49-67.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 4 | 8 |
| 100/20 — Pass 1 | 10 | 10 | 4 | 8 |
| 60/10 — Pass 2 | 10 | 10 | 8 | 9 |
| 100/20 — Pass 2 | 10 | 10 | 8 | 9 |

- **60/10 — Pass 1:** Gist: gives `CHUNK_SIZE = 60` and overlap 10. Citations: none. Both values are correct, but neither is cited; 10/10/4/8.
- **100/20 — Pass 1:** Gist: gives `CHUNK_SIZE = 60`. Citations: none. Correct and sufficient for the question, but uncited; 10/10/4/8.
- **60/10 — Pass 2:** Gist: gives `CHUNK_SIZE = 60`. Citations: 1479, 1480, 1481. Chunk 1479 supports the constant; the other cited windows are extra and do not improve support. 10/10/8/9.
- **100/20 — Pass 2:** Gist: gives `CHUNK_SIZE = 60` and overlap 10. Citations: 1572, 1573. The first span supports the constant; the second is extra context. 10/10/8/9.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
The fact is correct in all four answers. Pass 2 gains a relevant citation in both arms; pass 1 remains uncited in both.

### Question: direct-03
**Question:** Which Gemini embedding model is configured?
**Expected answer / authoritative reference:** `GEMINI_MODEL = "models/gemini-embedding-001"` in `scripts/embed_chunks.py:25`; the CLI description is at line 121.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 8 | 9 | 4 | 7 |

- **60/10 — Pass 1:** Gist: identifies `models/gemini-embedding-001` and `GEMINI_MODEL`. Citations: 1476, 1477, 1478. These embedder spans support the answer. All scores are 10.
- **100/20 — Pass 1:** Gist: names the configured model. Citations: 1570, 1571. Correct, complete, and supported. All scores are 10.
- **60/10 — Pass 2:** Gist: names the configured model and constant. Citations: 1476, 1477, 1478. Supported and precise. All scores are 10.
- **100/20 — Pass 2:** Gist: gives the correct model, then says the CLI description refers to `gemini-gemini-embedding-001`. Citations: none. That extra string is not the source description, and the answer is uncited; 8/9/4/7.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Worse (clear; −3 Overall) |

#### Question-level conclusion
Pass 1 is equivalent. In pass 2 the core model is right, but the experiment adds an incorrect CLI-description claim (`gemini-gemini-embedding-001`) and has no citation.

### Question: direct-06
**Question:** What is the high-confidence RRF calibration margin?
**Expected answer / authoritative reference:** `MIN_CLEAR_RRF_SCORE = 0.032` in `app/investigation/confidence.py:5,20-29`.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

- **60/10 — Pass 1:** Gist: names the high-confidence margin as `MIN_CLEAR_RRF_SCORE = 0.032`. Citations: 1449. The confidence source supports it. All scores are 10.
- **100/20 — Pass 1:** Gist: same constant and value. Citations: 1552. Correct and directly supported. All scores are 10.
- **60/10 — Pass 2:** Gist: same constant and value. Citations: 1449. Accurate and grounded. All scores are 10.
- **100/20 — Pass 2:** Gist: same constant and value. Citations: 1552. Accurate and grounded. All scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
All answers are fully correct and cited; no strategy difference.

### Question: direct-07
**Question:** Which MCP server class is instantiated?
**Expected answer / authoritative reference:** `FastMCP` is imported and instantiated as `server` in `app/investigation/mcp_server.py:10,18`.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 4 | 8 |

- **60/10 — Pass 1:** Gist: identifies `FastMCP` and gives its constructor use. Citations: 1460, 1462. The MCP source span supports it. All scores are 10.
- **100/20 — Pass 1:** Gist: names `FastMCP`. Citations: 1559, 1560. Relevant server spans support the answer. All scores are 10.
- **60/10 — Pass 2:** Gist: identifies `FastMCP` and its instance. Citations: 1460, 1462. Accurate and supported. All scores are 10.
- **100/20 — Pass 2:** Gist: correctly names `FastMCP` and its construction. Citations: none. Correct and complete but uncited; 10/10/4/8.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Worse (minor; −2 Overall) |

#### Question-level conclusion
The answer is right in all cases. The pass-2 experimental response loses grounding solely because it omits citations.

### Question: paraphrased-01
**Question:** How does the database layer establish non-blocking connections and create request-scoped objects?
**Expected answer / authoritative reference:** `app/db/session.py:12-32` creates the async engine, converts PostgreSQL to the psycopg async URL, enables `pool_pre_ping`, and registers pgvector asynchronously. Lines 35-46 configure `AsyncSessionLocal` and yield sessions through `get_db_session`.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

- **60/10 — Pass 1:** Gist: explains async engine setup, URL conversion, pgvector registration, sessionmaker, and yielded sessions. Citations: 1447. The cited session file span supports these details. All scores are 10.
- **100/20 — Pass 1:** Gist: same, explicitly describes `run_async` and request-scoped session yielding. Citations: 1550. Accurate and supported. All scores are 10.
- **60/10 — Pass 2:** Gist: explains URL conversion, pre-ping, `AsyncSessionLocal`, and `get_db_session`. Citations: 1447. Correct and complete. All scores are 10.
- **100/20 — Pass 2:** Gist: same configuration, including async pgvector registration and the context manager. Citations: 1550. All claims are supported. All scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
Both arms correctly cover connection setup and session creation. Additional detail in the experiment is supported but not material to the comparison.

### Question: paraphrased-02
**Question:** How are source files divided into overlapping pieces for indexing?
**Expected answer / authoritative reference:** `scripts/ingest_repo.py:22-23,35-46,49-67,94-106` sets 60-line windows with 10-line overlap, steps by `chunk_size - overlap`, emits advancing windows, ingests Python files, and skips whitespace-only chunk content.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

- **60/10 — Pass 1:** Gist: explains `chunk_lines`, 60/10 defaults, 50-line step, and non-redundant windows. Citations: 1480, 1479, 1481. These spans cover the function and constants. All scores are 10.
- **100/20 — Pass 1:** Gist: gives the same splitting mechanism and default values. Citations: 1572, 1573. The cited ingestion spans support it. All scores are 10.
- **60/10 — Pass 2:** Gist: explains the 60/10 defaults and advancing overlapping windows. Citations: 1480, 1479, 1481. Correct and supported. All scores are 10.
- **100/20 — Pass 2:** Gist: additionally notes Python files and skipping empty content. Citations: 1572, 1584, 1573. Both details are supported by ingestion code/test spans. All scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
All descriptions match the pinned implementation. Extra process detail in the experiment is supported but does not materially change correctness or completeness.

### Question: paraphrased-04
**Question:** How are two independent search rankings combined into one ordered result?
**Expected answer / authoritative reference:** `app/retrieval/hybrid_search.py:9-70` obtains vector and full-text results, assigns one-based ranks, sums `1 / (60 + rank)` for each result list containing a chunk, sorts descending by fused score, and applies the result limit.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 4 | 8 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 4 | 8 |

- **60/10 — Pass 1:** Gist: describes both rankings, rank fusion formula, descending sort, and limit. Citations: 1473, 1494, 1472. Implementation and test spans support it. All scores are 10.
- **100/20 — Pass 1:** Gist: accurately describes rank calculation, union, RRF formula, sort, and limit. Citations: none. No factual weakness, but no citation; 10/10/4/8.
- **60/10 — Pass 2:** Gist: explains the same RRF sequence. Citations: 1473, 1494, 1472. Correct and well-supported. All scores are 10.
- **100/20 — Pass 2:** Gist: accurately describes the same RRF calculation and truncation. Citations: none. Correct but uncited; 10/10/4/8.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Worse (minor; −2 Overall) |
| Pass 2 | 100/20 against 60/10 | Worse (minor; −2 Overall) |

#### Question-level conclusion
The content is equally correct, but both experimental answers lack citations while the baseline answers cite the implementation and test.

### Question: paraphrased-06
**Question:** How is a model's certainty adjusted when the supporting search evidence is borderline?
**Expected answer / authoritative reference:** `calibrate_confidence` in `app/investigation/confidence.py:9-38` normalizes the reported confidence, downgrades only `"high"` to `"medium"` when RRF is below `0.032` or vector distance exceeds `0.4`, and otherwise retains the rating.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 1 | 10 | 10 | 10 | 10 |
| 60/10 — Pass 2 | 10 | 10 | 10 | 10 |
| 100/20 — Pass 2 | 10 | 10 | 10 | 10 |

- **60/10 — Pass 1:** Gist: states both calibration margins and the high-to-medium downgrade. Citations: 1449, 1498. Confidence and graph spans support the behavior. All scores are 10.
- **100/20 — Pass 1:** Gist: same thresholds and conditional downgrade. Citations: 1552. Correct and directly supported. All scores are 10.
- **60/10 — Pass 2:** Gist: adds that the downgrade note records the violated threshold and non-high values are retained. Citations: 1449. Both details are in the cited source. All scores are 10.
- **100/20 — Pass 2:** Gist: gives the threshold checks and retention of non-high confidence. Citations: 1552. Correct and supported. All scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
Both arms fully answer the question with supporting citations in both passes.

### Question: unanswerable_far-01
**Question:** How do I bake sourdough bread at high altitude?
**Expected answer / authoritative reference:** No sourdough or baking guidance appears in the pinned repository search. Correct behavior is to abstain; this domain is unrelated to the project.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

- **60/10 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention on a source-absent topic; all applicable scores are 10.
- **100/20 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **60/10 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
Both strategies abstain appropriately in both passes. The topic is absent from the pinned repository.

### Question: unanswerable_far-02
**Question:** Which telescope can observe the rings of Saturn?
**Expected answer / authoritative reference:** No telescope or Saturn guidance appears in the pinned repository search. Correct behavior is to abstain.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

- **60/10 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **60/10 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
All four responses abstain appropriately; the pinned repository contains no relevant astronomy content.

### Question: unanswerable_far-03
**Question:** How should a wooden canoe be repaired?
**Expected answer / authoritative reference:** No canoe or repair guidance appears in the pinned repository search. Correct behavior is to abstain.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

- **60/10 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **60/10 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
Both arms correctly abstain in both passes; no canoe-repair information is present in the pinned repository.

### Question: unanswerable_far-04
**Question:** Why do coral reefs bleach during marine heatwaves?
**Expected answer / authoritative reference:** No coral-reef or marine-heatwave guidance appears in the pinned repository search. Correct behavior is to abstain.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

- **60/10 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **60/10 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
The four responses abstain correctly. The pinned repository has no marine-science material.

### Question: unanswerable_near-01
**Question:** How is Redis configured for this application?
**Expected answer / authoritative reference:** Redis is explicitly listed among technologies excluded from V1 in `README.md:318`; no Redis configuration is present in the pinned repository. Correct behavior is to abstain.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

- **60/10 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. IDs listed: 1439, 1506, 1507, 1440, 1492; the abstention makes no factual claim for them to support. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **60/10 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
All arms abstain appropriately. The explicit V1 exclusion and absence of implementation confirm the topic is not answerable from this source.

### Question: unanswerable_near-02
**Question:** How does the message queue retry failed jobs?
**Expected answer / authoritative reference:** No message-queue retry implementation appears in the pinned repository. The repository search finds only unrelated queue/worker probe text in `tests/fixtures/phase7_grep_probe.py:22`, not an application queue or retry mechanism. Correct behavior is to abstain.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

- **60/10 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **60/10 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
Both strategies abstain. The sole queue-related search hit is fixture prose, not evidence of a queue or retry implementation.

### Question: unanswerable_near-03
**Question:** Where is user login and authentication implemented?
**Expected answer / authoritative reference:** Authentication is explicitly excluded from V1 in `README.md:318`; repository search found no login/authentication implementation. Correct behavior is to abstain.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

- **60/10 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **60/10 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
All four responses abstain appropriately; the source explicitly excludes authentication and contains no implementation.

### Question: unanswerable_near-04
**Question:** Which Kubernetes deployment target does this service use?
**Expected answer / authoritative reference:** Kubernetes is explicitly excluded from V1 in `README.md:318`; repository search found no deployment-target configuration. Correct behavior is to abstain.

#### Response assessments
| Response | Correctness /10 | Completeness /10 | Grounding /10 | Overall /10 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 1 | 10 | n/a | 10 | 10 |
| 60/10 — Pass 2 | 10 | n/a | 10 | 10 |
| 100/20 — Pass 2 | 10 | n/a | 10 | 10 |

- **60/10 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 1:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **60/10 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.
- **100/20 — Pass 2:** Gist: `INSUFFICIENT_EVIDENCE`. Citations: none. Correct abstention; all applicable scores are 10.

#### Comparative verdict
| Pass | Comparison | Verdict |
| Pass 1 | 100/20 against 60/10 | Same (equivalent) |
| Pass 2 | 100/20 against 60/10 | Same (equivalent) |

#### Question-level conclusion
Both strategies abstain correctly; the source explicitly excludes Kubernetes and contains no target configuration.

## Final report

### Summary by question
| Question ID | Pass-1 verdict | Pass-2 verdict | Main reason |
|---|---|---|---|
| direct-01 | Same | Same | Both accurate and cited. |
| direct-02 | Same | Same | Correct values; both uncited in pass 1, both cited in pass 2. |
| direct-03 | Same | Worse (clear) | Experimental pass 2 adds a false CLI-description string and has no citation. |
| direct-04 | Same | Better (minor) | Experimental pass 2 cites both relevant thresholds; baseline pass 2 is uncited. |
| direct-05 | Same | Same | All answers identify the correct constant and value with evidence. |
| direct-06 | Same | Same | All answers correctly identify the confidence margin with citations. |
| direct-07 | Same | Worse (minor) | Experimental pass 2 is correct but uncited. |
| direct-08 | Better (clear) | Better (clear) | Experiment answers correctly; baseline abstains. |
| paraphrased-01 | Same | Same | Both accurately explain async engine and session setup. |
| paraphrased-02 | Same | Same | Both accurately explain overlapping windows and chunk defaults. |
| paraphrased-03 | Same | Same | Both correctly describe embedding; citations support the claims. |
| paraphrased-04 | Worse (minor) | Worse (minor) | Experimental answers are correct but uncited; baseline cites implementation. |
| paraphrased-05 | Same | Same | Both explain guard and routing with relevant citations. |
| paraphrased-06 | Same | Same | Both correctly describe confidence calibration and cite it. |
| paraphrased-07 | Worse (minor) | Same | Experimental pass 1 is correct but uncited; pass 2 is cited. |
| paraphrased-08 | Better (clear) | Better (clear) | Experiment names Audit; baseline abstains in pass 1 and misidentifies the record in pass 2. |
| unanswerable_far-01 | Same | Same | Both arms correctly abstain. |
| unanswerable_far-02 | Same | Same | Both arms correctly abstain. |
| unanswerable_far-03 | Same | Same | Both arms correctly abstain. |
| unanswerable_far-04 | Same | Same | Both arms correctly abstain. |
| unanswerable_near-01 | Same | Same | Both arms correctly abstain; Redis is excluded/absent. |
| unanswerable_near-02 | Same | Same | Both arms correctly abstain; no queue retry implementation exists. |
| unanswerable_near-03 | Same | Same | Both arms correctly abstain; authentication is excluded/absent. |
| unanswerable_near-04 | Same | Same | Both arms correctly abstain; Kubernetes is excluded/absent. |

### Verdict counts
| Comparison set | Pass | Better | Same | Worse | Uncertain |
|---|---:|---:|---:|---:|---:|
| All 24 questions | Pass 1 | 2 | 20 | 2 | 0 |
| 16 answerable questions | Pass 1 | 2 | 12 | 2 | 0 |
| All 24 questions | Pass 2 | 3 | 18 | 3 | 0 |
| 16 answerable questions | Pass 2 | 3 | 10 | 3 | 0 |

All verdicts follow the specified Overall-score comparison. In pass 1, both improvements are clear and both regressions minor. In pass 2, one improvement is minor and two clear; one regression is clear and two minor.

### Mean scores on answerable questions
Descriptive means over the 16 answerable questions; not an adoption test. Correctness averages include only numeric correctness scores (an answerable abstention is `—`, not zero); all other columns include all 16 responses.

| Response set | Correctness mean (n) | Completeness mean /16 | Grounding mean /16 | Overall mean /16 |
|---|---:|---:|---:|---:|
| 60/10 — Pass 1 | 10.00 (14) | 8.75 | 8.38 | 8.88 |
| 100/20 — Pass 1 | 10.00 (16) | 10.00 | 8.50 | 9.50 |
| 60/10 — Pass 2 | 9.60 (15) | 9.00 | 8.44 | 8.94 |
| 100/20 — Pass 2 | 9.88 (16) | 9.94 | 8.31 | 9.31 |

### Important correctness, grounding, and completeness observations
- **Correctness regression:** direct-03, experimental pass 2, incorrectly says the CLI description uses `gemini-gemini-embedding-001`; the configured model is `models/gemini-embedding-001`, and the CLI description at the pinned source does not contain that doubled prefix. The answer’s main model value remains correct.
- **Other material factual issue:** paraphrased-08, baseline pass 2, does not name `Audit` and attributes retrieved evidence to an “investigation record.” The cited test chunk ends before the Audit assertions; `Audit` is the record that holds retrieval evidence and response metadata.
- **Grounding weakness:** on answerable questions, the 100/20 responses without citations are direct-03 pass 2, direct-07 pass 2, paraphrased-04 both passes, paraphrased-07 pass 1, and paraphrased-08 both passes, plus direct-02 pass 1. The baseline also omits citations on direct-02 pass 1 and direct-04 pass 2. Correct prose is not treated as fully grounded merely because the source can establish it.
- **Completeness gains:** both direct-08 experimental passes answer where both baseline passes abstain. Paraphrased-08 improves from an abstention to the correct Audit answer in pass 1, and from a misleading answer to the correct record in pass 2. Experimental paraphrased-08 remains uncited.
- **No general verbosity reward:** detailed experimental responses were scored on relevance and support, not length or the presence of additional numbers.

### Citation behavior
For answerable questions only, I counted `Cited chunk IDs: none` as uncited and excluded answerable abstentions from the no-citation-answer numerator:

| Arm | Answerable responses | No-citation answers | Answerable abstentions |
|---|---:|---:|---:|
| 60/10 | 29 | 2 | 3 |
| 100/20 | 32 | 8 | 0 |

The experimental arm has more uncited answers (8/32 versus 2/29), despite answering more answerable prompts. This is a grounding pattern, not proof that the uncited facts are false. Correct abstentions on the eight unanswerable questions are counted separately and are not included above.

### Questions where the two passes disagree
- **direct-03:** pass 1 is Same; pass 2 is Worse (clear), due to the extra false CLI-description detail and missing citation.
- **direct-04:** pass 1 is Same; pass 2 is Better (minor), because only the pass-2 baseline answer is uncited.
- **direct-07:** pass 1 is Same; pass 2 is Worse (minor), because only the pass-2 experimental answer is uncited.
- **paraphrased-07:** pass 1 is Worse (minor) for the uncited experiment answer; pass 2 is Same with citations in both arms.

### Limitations
- The raw ignored run JSONs and database were not inspected; I relied on the saved workbook. No experiment/API/database operation was performed.
- I did not read every full body among all top-five retrieved chunks. I checked workbook source-span mappings and verified claim-bearing source ranges at the pinned commit; cited support that was not materially relevant to a claim was not credited.
- This is one reviewer’s rubric application. Scores are judgment-based; no inter-rater agreement or statistical inference is claimed.
- The runs provide two saved generations per strategy and 16 answerable questions. This is evidence about these responses, not a guarantee of repeat-run quality.

### Gate 5 assessment
**Mixed, with a modest descriptive Overall-score advantage for 100/20 in these saved responses, but not an unqualified quality improvement.** The experiment improves answers on direct-08 and paraphrased-08, and pass-1 aggregate Overall is higher. However, pass 2 also has a clear correctness regression on direct-03, more uncited answerable responses, and more question-level losses than pass 1. Retrieval effectiveness is deliberately kept separate: this is an answer-quality review and does not infer a retrieval win from ranks or hit measures. The human Gate 5 requirement in [`chunking-experiment.md`](01-experiment-log.md), entry [004], is not an adoption authorization. Production remains 60/10 unless the maintainer separately approves a change.

### Unresolved issues
- Whether the higher uncited-answer rate for 100/20 recurs beyond these two saved passes.
- Whether reviewers applying the rubric independently would agree on borderline Overall scores and whether uncited-but-accurate answers should carry the grounding penalty used here.
- The pass-2 direct-03 false aside should be treated as a genuine response defect even though it does not change the requested model identifier.

## Methodology critique

The method is auditable and substantially reproducible: it freezes two run identities and a pinned source, requires four response assessments per question, distinguishes answerability/abstention, and gives a mechanical pass-by-pass Overall comparison. The source-linked workbook is a strong improvement over automated labels as a substitute for judgment. It is not fully objective: the 0–10 rubric leaves substantial room for different scores, “Overall” is intentionally not an average, and evaluators may interpret “supported and cited correctly” differently.

### Essential proposals (approval required)
1. **Add anchored examples for each dimension and the main edge cases.** Include examples for a correct uncited answer, a partly irrelevant citation set, a false extra detail, a correct abstention on an answerable question, and a correct abstention on an unanswerable question. **Benefit:** reduces score drift and makes the stated bands reproducible. **Cost:** calibration effort and a longer rubric; do not retroactively change this review’s scores without approval.
2. **Require blinded first-pass scoring.** Randomize response order and hide strategy/pass labels until correctness, completeness, and grounding notes are recorded. **Benefit:** reduces expectation, length, and strategy-label bias. **Cost:** a small workbook-preparation step and delayed side-by-side comparison.
3. **Make the evidence protocol explicit per response.** Preserve the exact answer and cited IDs, show the cited chunk bodies and source spans, distinguish cited evidence from merely retrieved top-five evidence, and require a pinned-source check for each material claim. **Benefit:** makes grounding judgments independently checkable and avoids treating a citation as proof by itself. **Cost:** more workbook space and reviewer time.
4. **Predefine how score differences aggregate into Gate 5.** The existing per-question comparison is clear, but the gate criterion (“must not be lower”) does not state how many regressions, a severity-weighted regression, or differing pass outcomes affect an aggregate conclusion. Specify the aggregation and tie/disagreement treatment before the next review. **Benefit:** prevents a mean improvement from obscuring a serious isolated regression. **Cost:** requires maintainer approval because it refines the decision criterion; it should not silently replace entry [004].

### Optional proposals (approval required)
1. **Report citation coverage and citation precision separately from grounding.** For example, coverage could count claims with at least one supporting citation, while precision assesses whether each citation actually supports its attached claim. **Benefit:** diagnoses whether low grounding comes from missing citations or irrelevant citations. **Cost:** adds annotation and another reported measure.
2. **Use a second independent reviewer on disputed or low-scoring items, with adjudication notes.** **Benefit:** exposes inter-reviewer variation and resolves subjective cases such as paraphrased-08 pass 2. **Cost:** review time; full double-scoring is more expensive than targeted adjudication.
3. **Keep per-question results alongside any aggregate, and summarize pass disagreement explicitly.** This report does so; making the presentation a fixed workbook requirement would help future comparisons. **Benefit:** makes reversals and regressions visible. **Cost:** modest reporting overhead.

These are proposals for approval only. They do not change the agreed scoring rules or expand the experiment’s scope.
