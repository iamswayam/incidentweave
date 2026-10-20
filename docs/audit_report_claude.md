# Independent Engineering Audit & AI Market Assessment: IncidentWeave

*Audit date: 2026-10-20 · `main` @ `e98da82` · `experiment/chunking-evaluation-harness` @ `12edf8e`*

## 0. Evidence legend and limits

| Tag | Meaning |
|---|---|
| **[SRC]** | Verified by reading source code on the named branch. |
| **[EXEC]** | I executed it: stdlib-only functions (`guard`, `confidence`, `parsing`), arithmetic, and analysis of the committed `evaluation/results/baseline.json`. |
| **[ART]** | Taken from repo docs or reports. These are the author's reported results and I did not re-run them. |
| **[MKT]** | External source, dated, listed in the Sources section. |
| **[INF]** | My engineering inference or hypothesis. |

**Not done:**
- I did not run the full pytest suite (PyPI blocked), the PostgreSQL integration tests, live Gemini calls, or `scripts/run_eval.py`.
- I observed nothing at runtime.
- I did not read every test file line by line. I read the graph tests and the API and parsing test names.
- The experiment's per-run JSON artifacts (`evaluation/results/runs/*`) are gitignored, so they are not in either branch. I could not verify the experiment's raw numbers.

---

## 1. Executive Summary

**Engineering quality:** This is a disciplined, honestly documented solo project that is well above tutorial-level RAG. Its strengths are its measurement and its candor. It is not production-grade, and the "incident investigation" name outruns what it does. Today it is grounded Q&A over one Python repository.

**Market relevance:** The stack is relevant but generic. What distinguishes it (evaluation, audit trail, abstention) is what the 2026 market rewards. Its gaps are the things the AI-SRE category is built on: operational data (logs, alerts, traces, deploys), hypothesis-driven investigation, tracing and deployment.

**Most important conclusions:**

1. **The RRF half of the evidence guard can never reject anything** [SRC][EXEC]. The author's own diagnostic confirms it [ART]. The guard is effectively one vector-distance cutoff, which overstates what the README claims.
2. **"Hybrid" retrieval is nominal.** Hybrid tied vector-only on every metric, because full-text returned nothing for 14 of 16 answerable questions [ART]. The cause is query construction, not Postgres FTS itself.
3. **Citations are mentions, not verification** [SRC][EXEC]. Mentioning a file path as "unrelated" counts as citing every retrieved chunk from that file. In the final run only 9 of 22 and 9 of 31 cited chunks matched a labeled-relevant substring [ART].
4. **Two undocumented correctness and audit gaps** [SRC]:
   - `POST /investigations` runs the literal grep fallback against IncidentWeave's own source tree, not the requested repository.
   - Refused queries are never persisted, so the audit trail omits them.
5. **The chunking experiment is promising but not established.** Hit@5 went from 11/16 to 15/16 (a paired sign test gives p≈0.125) on one self-referential, author-drafted, unreviewed 24-question set. Token use rose about 40%, and the harness's label-matching rule favors larger chunks (the author acknowledges this). The decision report's own conclusion is to keep 60/10 until human review is done, which is correct.
6. **It is worth continuing, but change direction.** Stop micro-tuning chunk sizes and fix the retrieval and grounding defects below. Then give the project real incident data and an incident-replay evaluation. That is what would make it stand out.

---

## 2. Engineering Audit

### 2.1 Strengths [SRC] unless noted

- **Fail-closed defaults.** An unset API secret means 401 on every route. A response that fails parsing becomes `INSUFFICIENT_EVIDENCE` with `low` confidence. Generation is skipped when evidence is weak. Errors return sanitized bodies.
- **Bounded, deterministic orchestration.** The graph has one widened retry, then a grep fallback, then a stop. The model never chooses tools, which suits a safety-sensitive domain.
- **Real infrastructure in tests and CI.** CI runs a `pgvector/pgvector:pg17` service, `alembic upgrade head`, pytest, ruff and a Docker build. Tests use a real PostgreSQL instance rather than a mocked database layer.
- **Evaluation hygiene that is unusually good** (`evaluation/golden.py`, `runner.py`):
  - The corpus is pinned to a commit SHA.
  - The golden-set validator checks that paraphrased questions don't contain source identifiers.
  - "Unanswerable-near" and "unanswerable-far" categories separate easy and hard abstention cases.
  - Runs record config, prompt and golden-set hashes and a `code_dirty` flag.
  - The harness can only write to allowlisted evaluation repositories.
  - There is an outcome taxonomy (`outcome_v2`) and a distance-cutoff sweep.
- **The author surfaces weaknesses.** `docs/later-optimizations.md` and the API's `evaluation_note` document several issues I would otherwise flag: whole-query literal grep, a new MCP process per call, citation matching not being claim verification, and widening not fixing vector rejection.

### 2.2 Confirmed findings (ranked)

| # | Finding | Evidence | Impact |
|---|---|---|---|
| **F1** | **RRF guard gate is vacuous.** `MIN_ACCEPTABLE_RRF_SCORE = 0.016` is below `1/61 = 0.016393`, the score of any rank-1 vector hit. I ran the guard: with a non-empty vector result the RRF check always passes, and sufficiency reduces to `best_vector ≤ 0.5`. The README claim that retrieval must clear "both an RRF threshold *and* a raw vector-distance threshold" is overstated. | [SRC][EXEC]; author's own diagnostic `rrf_gate_can_reject_nonempty_vector_results: false` [ART] | The guard is a single distance cutoff, not a combined signal. |
| **F2** | **Wrong-tree grep fallback in the API.** `api.py` calls `investigate_repository(...)` without `repo_path`. The default is `REPO_ROOT`, the IncidentWeave checkout. For any repository other than itself, a literal-fallback hit is IncidentWeave's own source presented as evidence for the requested repo. Literal matches also bypass the guard thresholds (always "sufficient"). | [SRC]. I found no mention in the Phase 9 docs, whose `repo_path` references are CLI help only. | Cross-repository evidence contamination. Probability is low because the whole query must match one line verbatim. In the final run grep recovered 0 of 8 attempts [ART]. |
| **F3** | **Refusals aren't audited.** When the guard fails, `investigate_repository` returns before `persist_investigation`. There is no Investigation or Audit row and `investigation_id` is `None`. README says "one `Audit` row per query." | [SRC]; Phase 9 doc example 1 states "refusal before persistence" [ART] | False-refusal and refusal rates can't be audited, and no refused query can be retrieved via `GET /investigations/{id}`. |
| **F4** | **Citation = string mention.** A chunk counts as cited if its chunk ID, its file path anywhere in the response, or a path with a line range appears. I ran it: a response calling `app/config.py` "unrelated" cites it. `app/db/session.py lines 900-950 (does not exist)` still cites every retrieved chunk from that file. A response with `Diagnosis: INSUFFICIENT_EVIDENCE` and `Confidence: high` persists as `high`. | [EXEC] | Citations don't prove grounding, and the stored record can contradict itself. |
| **F5** | **Audit not reproducible after re-ingest.** `ingest_repository` deletes all chunks for the repository and reinserts them, so chunk IDs change and embeddings are lost. `Audit.retrieved_chunk_ids` has no foreign key and no content snapshot. No commit SHA is stored anywhere, since `Repository` has only a name. | [SRC] | You can't show which version of the code supported a past diagnosis. For incident work this is serious. |
| **F6** | **Raw model output and prompt aren't persisted.** `Investigation.response` and `Audit.response` both store only the parsed diagnosis. The prompt is hashed in the CLI trace, not stored. README says the raw model response is persisted. Raw confidence isn't stored either (the author discloses this). | [SRC] | The audit can't replay or explain a model's full output. |
| **F7** | **Retrieval quality defects.** (a) `websearch_to_tsquery` ANDs unquoted words, so natural-language questions return no rows [MKT: PostgreSQL docs]. This matches full-text being empty for 14 of 16 answerable questions [ART]. (b) The `'english'` config stems and strips stopwords, which is poor for code identifiers. (c) `embed_text` sends no `task_type`, although `gemini-embedding-001` supports `RETRIEVAL_DOCUMENT` and `CODE_RETRIEVAL_QUERY` [MKT]. (d) Test files are indexed alongside source. In `baseline.json`, 35 of 80 top-5 results (44%) come from `tests/`, and 15 of 16 answerable questions have at least one test chunk in the top 5 [EXEC on the committed artifact]. (e) The migration has no HNSW index and no GIN index on `to_tsvector`. | [SRC] for a–c and e; [EXEC] for d | Hybrid adds no measured lift, and ranking is noisy. (e) is irrelevant at 70 chunks and disqualifying at scale. |
| **F8** | **Async and cost-safety gaps.** `embed_text` is a blocking `urllib` call inside an async path (up to a 60s timeout, no retry). The generation call uses blocking `urllib` with `time.sleep` backoff; LangGraph probably offloads this node to a thread, but that is unverified [INF]. The API key travels in the URL query string. `limit` has no upper bound and `query` no max length. The rate limiter is in-memory and per-IP (disclosed by the author). `app/api.py` imports `scripts.investigate`, which inverts the layering. Docker Compose passes neither `GEMINI_API_KEY` nor `API_PROTECTION_SECRET`, so the containerized app can't generate or authenticate. The Dockerfile runs as root. | [SRC] | Event-loop stalls under concurrency, key-leak risk via logs, and a cost-abuse vector. A fully working container path is not demonstrated. |
| **F9** | **Embedding throughput.** One chunk per request with `asyncio.sleep(1.5)`. A batch endpoint exists [MKT]. For 10,000 chunks, the sleeps alone take about 4.2 hours. | [SRC] | Doesn't scale to real repositories. |
| **F10** | **Scope gap.** Only `*.py` files are ingested. The schema has `service`, `environment`, `incident_id`, `timestamp`, `symbol`, `function_name`, `class_name`, but ingestion sets only path, lines and type. There are no logs, alerts, metrics, traces or deploy history, and no hypothesis loop. | [SRC] | It is repo Q&A, not incident investigation. |

### 2.3 Design trade-offs (not defects)

- **LangGraph for a nine-node, mostly linear graph.** It adds a dependency without checkpointing, human approval or parallel branches. It earns its place only if you add real branching.
- **MCP over stdio for a deterministic internal call.** It demonstrates the protocol, but spawning a Python subprocess per grep adds latency with no measured benefit. The `hybrid_search` MCP tool is exposed but unused.
- **Confidence calibration carries little information.** In the committed `baseline.json`, the model's raw confidence was `high` for 15 of 16 answerable questions, and 13 of those were downgraded to `medium` [EXEC]. The thresholds (0.032, 0.4) are hand-set. I found no metric in `evaluation/metrics.py` that relates confidence to correctness.
- **Process weight exceeds product weight.** `app/` is 1,738 lines, `evaluation/` 1,596, `tests/` 2,030, and `docs/` about 4,450 [EXEC]. The experiment adds a 761-line comparator for a two-arm comparison.

### 2.4 Verification gaps

- The full pipeline is **not** verified by me. Its stages were verified individually by reading code. The Phase 8b run's reported results (40 generation calls, 0 errors, 0 HTTP 429s) are [ART].
- The README test count is inconsistent: 41 passing in the header and Phase 9 section, and 53 passing in the Phase 8 section. `main` now contains both phases, and I could not run the suite. Treat both numbers as stale.
- I did not test prompt injection (retrieved code is concatenated into the prompt with no delimiting or defense) or concurrency behavior.

---

## 3. End-to-End and Evaluation Assessment

### 3.1 Data-flow trace (source-verified; not executed end to end)

| Stage | What survives | Status |
|---|---|---|
| Ingest (`scripts/ingest_repo.py`) | `file_path`, `line_start/end`, content. Fixed 60-line windows with 10-line overlap, Python only. | No symbol metadata, no commit SHA. Delete-and-reinsert (F5). |
| Embed | 768-dim `gemini-embedding-001`, one request per chunk. | No task type (F7c). |
| Retrieve (`hybrid_search`) | ID, path, lines, content, vector distance, FTS score, RRF score. | FTS usually empty (F7a). |
| Guard | `best_rrf`, `best_vector`. | RRF gate vacuous (F1). |
| Prompt | Chunk ID, path, line range, raw scores, content. | No in-content line numbers, so line citations are approximate. No injection defense. |
| Generate | Single-turn free text. | No structured output schema. |
| Parse (`parsing.py`) | Regex for diagnosis, confidence and citations. | Fails safe to `INSUFFICIENT_EVIDENCE`/`low`, but citations are lenient (F4). |
| Calibrate | Downgrades `high` to `medium` on borderline scores. | Literal-source evidence has no scores, so `high` is retained with the note "retrieval scores clear both calibration margins," which is wrong for literal evidence [EXEC]. |
| Persist | Parsed diagnosis, scores, retrieved IDs, per-chunk path/lines in JSONB, tool-call trace. | No raw text or prompt (F6). Refusals not stored (F3). |

### 3.2 What the evaluation measures well and badly [ART unless noted]

**Final Phase 8b run on the 70-chunk pinned snapshot (24 questions: 16 answerable, 8 unanswerable):**

| Measure | Result |
|---|---|
| Retrieval (16 answerable) | Vector-only and hybrid: Hit@1 8/16, Hit@3 11/16, Hit@5 11/16, MRR 0.573. Full-text: Hit@5 2/16. |
| Guard | 16 true accepts, 0 false refusals, 4 true refusals, 4 false accepts. |
| Guard distance distributions | Answerable best-vector 0.274–0.413 (median 0.349). Unanswerable 0.389–0.544 (median 0.486). |
| Cutoff sweep | Cutoffs from 0.42 to 0.46 give 0 false refusals and 2 false accepts. 0.50 gives 4 false accepts. Tuning on the same 24 questions would be overfitting. |
| End to end (each pass) | 10 correct with labeled context, 2 correct with unlabeled context, 2 retrieval-miss abstentions, 2 incomplete or wrong, 4 guard true refusals, 4 model abstentions. |
| Abstention | All 4 near-unanswerable questions passed the guard (distances 0.389–0.467) and the model abstained on all 4 [EXEC on `baseline.json`]. So safety here rests on the LLM, not the guard. n=4. |
| Citations (answerable) | 9 of 22 and 9 of 31 cited chunks matched a labeled-relevant substring. "Relevant" means labeled only, so this is a lower bound on citation quality. |
| Latency and tokens | Median wall time 3.8–5.4 s per question, max about 18 s. Median total tokens about 2.8–2.9k. No cost accounting. |

**Does the evidence support the project's claims?**
- **Supported:** "Evaluation exists and is reproducible-by-design"; "the guard blocks far-off-topic queries"; "hybrid did not beat vector-only on this set."
- **Not supported:** any general claim about retrieval or grounding quality. The corpus is the project's own source, the 24 questions were drafted from the indexed source, and the label review status is "pending maintainer review." Checks use keyword screens (no LLM judge). Per-category n is 4–8, and there is no confidence interval.
- **Missing metrics:** confidence-versus-correctness, claim-level citation precision, and answer completeness beyond keywords. Neither the end-to-end latency distribution nor token cost is tied to a budget.

---

## 4. Branch Comparison (`main` vs `experiment/chunking-evaluation-harness`)

**What the branch changes [SRC]:** +3,116 / −50 lines across 9 files. It changes only evaluation code, docs and tests: `evaluation/chunk_experiments.py`, `compare_chunking_runs.py`, `runner.py`, `scripts/run_eval.py`, `tests/unit/*`, `docs/architecture.md`, `docs/chunking-experiment.md`, and a decision report. **No production code changes.** The experiment reimplements chunk ranges in the harness, with parity tests against production `chunk_lines` (good practice).

**Reported results (60/10 → 100/20), same pinned corpus, same golden set [ART, not re-run]:**

| Measure | 60/10 | 100/20 |
|---|---|---|
| Hit@5 | 11/16 | 15/16 |
| MRR | 0.573 | 0.700 |
| Hit-by-function@5 | 1/7 | 5/7 |
| Chunks | 70 | 52 |
| Median top-5 context | 7,730 chars | 11,072 chars (+43%) |
| Median tokens per question | ~2,840 | ~3,980 (+40%) |
| Guard false accepts | 4 | 4 |

**My assessment:**

- **Improved (reported):** more labeled chunks in the top 5, no lost Hit@3 or Hit@5 questions, gains concentrated in paraphrased questions (4/8 → 7/8).
- **Regressed or uncertain:**
  - `direct-05` pass 1 omitted the required value `0.5` despite a better rank.
  - `paraphrased-08` was answered "correctly" with zero citations.
  - Human correctness review (Gate 5) is pending.
  - `paraphrased-07` stays a miss.
- **Why the evidence is weaker than it looks:**
  - **Small, unreviewed sample.** The Hit@5 gain is 4 wins and 0 losses out of 16. My exact paired sign test gives p ≈ 0.125 (two-sided) [EXEC].
  - **Retrieval is deterministic.** The two passes are one retrieval sample plus two generation samples, not two replications.
  - **Label bias favors larger chunks.** Labels are file plus substring, so bigger chunks match more easily. The author acknowledges this and added hit-by-file and hit-by-function, which is the most credible signal, but its n is 7.
  - **100/20 is near file-level here.** In the current checkout, 70% of Python files are 100 lines or fewer (median 66.5) [EXEC]. The comparison is nearly "windows vs. whole files," which says little about other repositories.
  - **Narrow search.** Only two arms were tried. AST or function-aware chunking, other window sizes, and the larger defects in F7 were not.
  - **Artifacts not shipped.** Run artifacts are gitignored, so the numbers can't be audited from the repository.
- **Verdict:** The decision report's conclusion (keep 60/10, treat 100/20 as the retrieval-favored candidate until Gate 5) is the right call. The experiment is not convincing evidence for changing production. Chunk size is likely a second-order lever next to F7. Cheaper ablations on the same harness should come first.

---

## 5. October 2026 AI Market Assessment

### 5.1 Hiring signals

| Signal | Source and date | Reliability |
|---|---|---|
| AI engineering is the top fastest-growing skill; postings requiring AI literacy rose more than 70% year over year. | LinkedIn *Skills on the Rise 2026*, via CIO Dive/Yahoo Finance, **Mar 3, 2026** | High (named report, secondary relay). |
| AI engineering is the largest AI hiring category: 43,480 US postings since Jan 2026, about 1,550 per week. Python in 62% of postings, cloud 55%, foundation models 51%; observability and RAG are also mentioned. Employers favor breadth over single-tool depth, and a portfolio of shipped systems matters more than credentials. | Axial Search (recruiter), published **Apr 28, 2026**, updated **Oct 13, 2026** | Medium. Recruiter content, and the data window ends July 6 despite the October update date. |
| Skill-frequency sample (Glassdoor, 903 US postings): Python 71%, LangChain 10.7%, RAG 13.6%, agents 10.6%, model evaluation 5.5%, Docker 15.4%, Kubernetes 17.6%, vector databases 4.5%, GCP 4%. | 365 Data Science, first published Apr 2025, modified **Apr 23, 2026** | Low to medium. Mixed with classical ML roles, an older sample, and internal inconsistencies. |
| Forward-deployed engineer postings: India up about 19× year over year in June 2026, about 16× in July and over 6× in August (momentum from March). | Indeed via Deccan Chronicle, **Oct 14, 2026** | Medium. Regional and a news relay. |
| RAG is commoditizing in platforms. Premium skills are evaluation and observability, governance and access control, and agentic workflow design. | yage.ai, **May 2, 2026** | Low. It self-labels as AI-generated, so I use it only as an opinion. |

**What this shows, versus hype:**
- Demand for applied LLM and backend AI engineers is demonstrated.
- RAG shows up as a baseline skill, not a niche. In the Glassdoor sample "model evaluation" appears in only 5.5% of postings, and observability is only "mentioned" in Axial's data.
- Evaluation and reliability skills are probably a hiring-manager differentiator rather than a keyword filter [INF]. Keyword evidence alone does not make them a hard requirement.
- Forward-deployed work (customer-facing, deployment-heavy) is surging but regionally measured.

### 5.2 The product category your project names

- AI-SRE is an active product category. Vendors include Resolve AI, Traversal, Cleric and Neubird (closed agents), plus Datadog Bits AI, Dynatrace, New Relic and AWS DevOps Agent, and OSS options such as HolmesGPT, K8sGPT and OpenSRE (Mezmo market map, **Jun 22, 2026**; a vendor blog).
- Datadog's engineering post (**Jan 12, 2026**) describes the pattern:
  - Hypothesis trees tested with telemetry queries, with tool calls scoped to a hypothesis.
  - A benchmark built from labeled real incidents.
  - An LLM judge aligned to human judgments.
  - Its docs say an investigation can end "inconclusive" when the data doesn't support a conclusion.
- Your abstention behavior matches that principle. Your lack of telemetry, hypotheses and incident-based evaluation is the gap.

### 5.3 Protocols and tooling

- **MCP** moved to the Linux Foundation's Agentic AI Foundation on **Dec 9, 2025** (co-founded by Anthropic, Block and OpenAI; Google, Microsoft, AWS and others as supporters). Anthropic reports 10,000+ public servers and 97M+ monthly SDK downloads. These are vendor-stated figures. Adoption is real, so MCP skills are worth demonstrating, but your current use is thin.
- **Observability and evals:** Langfuse (MIT, self-hostable) joined ClickHouse on **Jan 19, 2026** alongside a $400M Series D, and reportedly has 23.1M monthly SDK installs (secondary source). Tracing and eval platforms are consolidating into the data infrastructure layer.
- **Gemini lifecycle (Google deprecations page, updated Oct 12, 2026):** `gemini-3.5-flash-lite` (released Jul 21, 2026) has no shutdown date, and `gemini-3.8-flash` was released Sep 2, 2026. `gemini-embedding-001` runs until at least May 14, 2028, and `gemini-embedding-2` (Apr 22, 2026) is the recommended replacement.

---

## 6. Technology-by-Technology Assessment

| Area | Currently used [SRC] | Still relevant in Oct 2026? | Alternatives | Would changing help? |
|---|---|---|---|---|
| Language and API | Python 3.12, FastAPI, Pydantic, Uvicorn | Yes. Python is 62–71% of postings [MKT]. | Go, TypeScript | No. Keep. |
| LLM provider | Gemini `3.5-flash-lite` and `embedding-001` via raw `urllib` | The models are current. Raw HTTP is the weak part. | Official SDK or async `httpx`; OpenAI or Anthropic adapters | **Yes, the client.** Use an SDK or async client with header auth, structured output and retries. Adding a second provider behind an interface has modest portfolio value and low priority. |
| Embeddings | `gemini-embedding-001`, 768-dim, no task type | Fine until 2028 [MKT]. | `gemini-embedding-2` (no `task_type`; uses a prompt prefix such as `task: code retrieval \| query:`), code-specific embedders | **Fix usage first** (task type, batching). Test `embedding-2` as a cheap A/B on your harness. |
| Storage and vector search | PostgreSQL, pgvector, SQLAlchemy async, Alembic | Yes. Postgres is a defensible default at this scale [INF]. | Dedicated vector databases | **No swap.** Add HNSW and GIN indexes. A dedicated vector database adds operations and no demonstrated benefit. |
| Lexical search | `ts_rank_cd` over `websearch_to_tsquery('english')`, no index | The idea is right; the construction is broken (F7a). | OR-based or identifier-aware query construction; BM25 via `pg_search` (ParadeDB, vendor-sourced argument that `ts_rank` lacks corpus statistics, Oct 2025) | **Yes.** Fix the query first and measure. Consider BM25 only if that fix shows a lift. |
| Chunking | Fixed line windows | Fixed windows are a baseline. cAST (AST-based) reports modest gains: Recall +1.8–4.3 points on RepoEval and +0.7–1.1 on SWE-bench [MKT]. | tree-sitter or function-level chunks; contextual headers | **Later.** The gain is real but modest, and F7 comes first. |
| Reranking | None | Commonly used to fix top-k ordering [INF]. | Cross-encoder or hosted rerankers | **Consider later**, after F7, for 44% test-file noise and paraphrase misses. |
| Orchestration | LangGraph 1.x | Visible in hiring (LangChain 10.7% in one sample [MKT]), but your graph is nearly linear. | Plain async code; Pydantic AI; OpenAI Agents SDK; Claude Agent SDK | **No rewrite.** Keep LangGraph only if you add branching: hypothesis loop, human approval, checkpoints. |
| Tool use | MCP stdio, `grep_search` only | MCP adoption is strong [MKT]. The current use adds latency for little value. | In-process function; MCP server for others to call | **Change the shape.** Expose IncidentWeave as a read-only MCP server and/or consume a real MCP server (for example logs). |
| Evaluation | Custom harness (pinned corpus, golden set, outcomes) | The approach matches Datadog's incident-benchmark pattern [MKT]. | Ragas, DeepEval, Braintrust | **Keep custom.** Add an LLM judge validated against human review, and a second repository. |
| Observability | `Audit` table, latency, tokens | Tracing platforms are consolidating [MKT]. Your docs recorded a Langfuse "no-go for now." | OpenTelemetry; self-hosted Langfuse; Phoenix | **Yes, soon.** Tracing and cost dashboards are cheap and highly visible. |
| Deployment and CI | Docker, Compose, GitHub Actions | Standard | Cloud Run or AWS deployment | Add a hosted demo. Cloud Run pairs well with Gemini. AWS and Azure appear in about 26–33% of Glassdoor postings versus 4% for GCP, though that sample is noisy [MKT]. |
| Auth and rate limiting | Shared secret, in-memory limiter | Disclosed as non-production | OAuth, Redis or edge limiter | Fine for a portfolio project. Add `limit` caps now. |

---

## 7. Recommended Stack

**Keep:**
- Python 3.12, FastAPI, Pydantic, SQLAlchemy async, Alembic, PostgreSQL and pgvector (add indexes).
- RRF-based hybrid retrieval as a concept.
- The custom evaluation harness and its hygiene.
- Docker and GitHub Actions with a real database.
- The bounded, deterministic orchestration principle.
- Gemini as a provider. The models are current.

**Change (justified by evidence above):**
1. Full-text query construction (F7a, 14 of 16 empty).
2. Embedding calls: task type, batching, async, header-based key (F7c, F8, F9).
3. Generation client: SDK or async `httpx`, structured output, citations as verifiable spans (F4, F8).
4. Ingestion: upsert by content hash, record commit SHA, tag tests as `document_type="test"` and downweight or filter them (F5, F7d).
5. Guard: drop or replace the vacuous RRF gate. Document it honestly (F1).
6. Audit: persist refusals, raw output, prompt and raw confidence (F3, F6).
7. API: carry the repository's root path in the repository record and cap `limit` and `query` length (F2, F8).

**Consider later:**
- A reranker, after the retrieval fixes.
- AST or function-aware chunking.
- BM25 via `pg_search`, only if the query fix shows a lift.
- Outward-facing MCP server and a second LLM provider.
- Tracing and dashboards (soon, but not blocking).
- Log, alert and trace ingestion (the largest product step).

**Do not do:** a framework rewrite, a vector-database swap, or more chunk-size-only experiments.

---

## 8. Portfolio and Interview Assessment

**Strengths a hiring manager would credit:**
- An evaluation-first, evidence-before-generation mindset, with documented measurement of what failed.
- Abstention and an audit design.
- Migrations, CI against a real database, and a typed async stack.
- Honest limits stated in the API response itself.

**Weaknesses and likely questions:**

| Likely question | Honest answer today |
|---|---|
| "Hybrid beats vector. Show me." | Your data shows a tie, and full-text was empty for 14 of 16. |
| "Does the guard use RRF and distance?" | Only distance. RRF can't reject (F1). |
| "What does your confidence mean?" | The model says `high` on 15 of 16 answers, and calibration moves most to `medium`. It is not validated against correctness. |
| "Why LangGraph? Why an MCP subprocess?" | Neither is currently necessary for the logic. |
| "How does this scale to a large repository?" | No vector or full-text index, sequential 1.5 s embeddings, delete-and-reinsert ingestion. |
| "Where are the logs, metrics and deploys?" | Not ingested. It's Python source only. |
| "Can I trust a citation?" | Citations are substring matches, not claim verification (F4). |
| "What about prompt injection or cost abuse?" | No injection defense. `limit` is unbounded. |
| "How do you know the evaluation generalizes?" | One self-referential repo, 24 unreviewed questions. |

**Versus a tutorial RAG project:** you are clearly ahead on evaluation discipline, traceability and honesty. You are not yet at the level of "built or evaluated an incident investigator on real operational data." That is where the market signal (the AI-SRE category) points.

---

## 9. Prioritized Action Plan

1. **Fix retrieval and grounding defects, measured in your existing harness** (effort S–M, highest ROI).
   - Make the full-text query OR/identifier-aware.
   - Add embedding `task_type` and batching.
   - Downweight or filter test files.
   - Replace the vacuous RRF gate.
   - Require verifiable citation spans.
   - Report each change as an ablation with the old numbers kept.
2. **Make the audit trustworthy** (effort S). Persist refusals, raw output, prompt, raw confidence and commit SHA. Switch ingestion to upsert-by-hash. Fix the `repo_path` and `limit` issues (F2, F8).
3. **Give it real incident data and an incident-replay evaluation** (effort M–L, highest differentiation). Build a small containerized sample service with injected faults. Ingest its logs, alerts and recent diffs. Create 10–20 labeled incidents with root causes. Score with an LLM judge validated on human labels, and allow "inconclusive." This mirrors what Datadog describes publicly and is what separates you from RAG demos.
4. **Strengthen evaluation rigor** (effort M). Add a second, held-out repository. Add confidence intervals and a confidence-versus-correctness metric. Run an offline retrieval regression in CI using cached embeddings.
5. **Add visible production signals** (effort S–M). OpenTelemetry or self-hosted Langfuse traces, a cost and latency view, and a hosted demo. Optionally expose a read-only MCP server.

Do these in order. Only revisit chunking, rerankers or AST after step 1.

---

## 10. Final Verdict

- **Maturity:** a well-engineered, unusually honest prototype. Its strengths are measurement and safe failure behavior. Its core claims (hybrid retrieval, a two-signal guard, grounded citations, full audit) are each weaker than the README implies, and I verified why in the source.
- **Market competitiveness:** relevant stack, genuinely relevant philosophy, but generic. It competes well against tutorial RAG. It does not yet demonstrate the operational-data, hypothesis-driven, deployed system that the 2026 AI-SRE category is built around.
- **Worth more effort?** Yes, but redirect it. The most valuable next move is step 1 followed by step 3: fix the measured retrieval and grounding defects, then run the system on real (or realistically simulated) incident data with an incident-replay evaluation. Further chunk-size tuning is the wrong next move, because the experiment's evidence is thin and bigger defects sit upstream of it.

---

## Sources

- LinkedIn *Skills on the Rise 2026*, via [CIO Dive / Yahoo Finance, Mar 3, 2026](https://finance.yahoo.com/news/ai-engineering-tops-list-demand-160600138.html)
- [Axial Search, AI Engineering Jobs in 2026 (published Apr 28, updated Oct 13, 2026)](https://axialsearch.com/insights/ai-engineering-jobs)
- [365 Data Science, AI Engineer Job Outlook (modified Apr 23, 2026)](https://365datascience.com/career-advice/career-guides/ai-engineer-job-outlook-2025/)
- [Indeed FDE data via Deccan Chronicle, Oct 14, 2026](https://www.deccanchronicle.com/amp/nation/in-other-news/demand-for-forward-deployed-engineers-jumps-19-fold-in-india-report-1995773)
- [yage.ai, "Is RAG Worth Betting On?", May 2, 2026](https://yage.ai/share/rag-career-direction-en-20260502.html) (self-described AI-generated; opinion only)
- [Mezmo, The 2026 AI SRE Market Map, Jun 22, 2026](https://www.mezmo.com/learn/the-2026-ai-sre-market-map-agents-harnesses-and-the-data-layer) (vendor blog)
- [Datadog, Building Bits AI SRE, Jan 12, 2026](https://www.datadoghq.com/blog/building-bits-ai-sre.md) and [Bits AI SRE docs](https://docs.datadoghq.com/ko/bits_ai/bits_ai_sre/investigate_alerts)
- [Anthropic, Donating MCP and establishing the Agentic AI Foundation, Dec 9, 2025](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation)
- [Langfuse joins ClickHouse, Jan 19, 2026](https://invest-in.berlin/n/berlins-langfuse-joins-clickhouse/) (secondary)
- [Google, Gemini API deprecations (updated Oct 12, 2026)](https://ai.google.dev/gemini-api/docs/deprecations?hl=en) and [Gemini embeddings docs](https://ai.google.dev/gemini-api/docs/embeddings)
- [PostgreSQL 18 docs, text search controls](https://www.postgresql.org/docs/current/textsearch-controls.html)
- [ParadeDB, Hybrid Search in PostgreSQL, Oct 22, 2025](https://paradedb.com/blog/hybrid-search-in-postgresql-the-missing-manual) (vendor)
- [cAST: structural chunking via AST (arXiv 2506.15655, v2 Oct 2, 2025)](https://arxiv.org/abs/2506.15655)
- Repository: [iamswayam/incidentweave](https://github.com/iamswayam/incidentweave) (`main` @ `e98da82`; `experiment/chunking-evaluation-harness` @ `12edf8e`)
