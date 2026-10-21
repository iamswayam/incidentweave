# IncidentWeave: Independent Engineering Audit and October 2026 Market Assessment

**Audit date:** 20 October 2026  
**Scope:** source tree, migration, tests, CI, committed evaluation artifacts, existing technical documentation, and current external documentation. This is an audit and recommendation document; no product code was changed.

## 1. Executive Summary

**Verdict: a thoughtful, well-documented prototype with several real engineering strengths, but not yet a reliable or production-ready incident-investigation system.** It is stronger than a tutorial RAG app because it has a real database schema and migration, repository-scoped retrieval, an explicit no-generation guard, a bounded graph, persisted successful investigations, an evaluation harness, and CI. The code is legible and the project records limitations more honestly than most portfolio projects.

However, its principal claim--trustworthy, evidence-grounded incident investigation--is not established. The current guard has a demonstrated false-accept rate of 4/24 on its own small set; its RRF threshold effectively admits any rank-one vector result; citations only show that a path or ID was mentioned, not that claims are entailed; and guard refusals are returned without persistence. Ingestion is Python-only fixed line windows, despite a broader operational-evidence framing. The HTTP API runs synchronous provider I/O inside async request handling and has no input/context limit. The database has neither a vector ANN index nor an indexed FTS vector.

The most important conclusion is not “replace the stack.” **Keep Python, FastAPI, PostgreSQL/pgvector, direct provider integration, and a deliberately bounded workflow. Change the reliability contract around provenance, evaluation, and request execution.** That produces far more portfolio and product value than adding a fashionable agent framework or a separate vector database.

Confidence labels used below:

| Label | Meaning |
|---|---|
| **Verified** | Directly established by inspected code or a current official source. |
| **Artifact-observed** | Present in a saved run/report, but not rerun in this audit. |
| **Inferred** | Logical consequence of verified facts; stated as such. |
| **Unverified** | Not established because the necessary live dependency, workload, or evidence was unavailable. |

## 2. Project Architecture and End-to-End Audit

### Actual flow

1. **Ingestion -- verified.** `scripts/ingest_repo.py` resolves a local directory, finds only `*.py` files, excludes selected directories, deletes all existing chunks for the supplied repository name, then writes 60-line windows with 10-line overlap. It preserves relative file path and line range, but writes `function_name`, `class_name`, and `symbol` as `None` ([`scripts/ingest_repo.py`](../../scripts/ingest_repo.py#L22)).
2. **Embedding -- verified.** `scripts/embed_chunks.py` selects null embeddings and calls Gemini one chunk at a time for a 768-dimensional vector, sleeping 1.5 seconds after every attempt. It commits successful assignments at the end ([`scripts/embed_chunks.py`](../../scripts/embed_chunks.py#L25)).
3. **Retrieval -- verified.** `search_vector` uses pgvector cosine distance; `search_fulltext` constructs `to_tsvector('english', content)` at query time. `hybrid_search` fuses independently truncated top-K lists with RRF, then re-truncates ([`app/retrieval/vector_search.py`](../../app/retrieval/vector_search.py#L11), [`app/retrieval/fulltext_search.py`](../../app/retrieval/fulltext_search.py#L9), [`app/retrieval/hybrid_search.py`](../../app/retrieval/hybrid_search.py#L9)).
4. **Investigation -- verified.** A query is embedded, then a LangGraph retrieves, applies a score guard, retries once at 2K, and finally starts a local MCP stdio subprocess for literal grep. If any literal match exists, it sends the match to Gemini; otherwise it returns `INSUFFICIENT_EVIDENCE` ([`scripts/investigate.py`](../../scripts/investigate.py#L54), [`app/investigation/graph.py`](../../app/investigation/graph.py#L97)).
5. **Generation, parsing, and confidence -- verified.** The prompt includes raw retrieved contents and asks Gemini for three text sections. Regex parsing derives diagnosis/confidence; citation recognition accepts a cited chunk ID or exact file path. Calibration only downgrades `high` to `medium` ([`prompt.py`](../../app/investigation/prompt.py#L7), [`parsing.py`](../../app/investigation/parsing.py#L44), [`confidence.py`](../../app/investigation/confidence.py#L9)).
6. **Persistence/API -- verified.** Sufficient-evidence generated answers receive one `investigations` row and one `audit_records` row in one database commit. Guard abstentions return before this branch and are not stored. The API wraps it synchronously behind a shared secret and process-local IP limiter ([`persistence.py`](../../app/investigation/persistence.py#L11), [`api.py`](../../app/api.py#L67), [`api_security.py`](../../app/api_security.py#L1)).

Metadata mostly survives the happy path: file path, ranges, chunk IDs and scores reach prompt/audit; model, latency, token count and final confidence are stored. Important losses remain: source root/commit is not a repository attribute, the raw model response and raw confidence are not stored, abstentions are not audited, and audit score arrays are parallel rather than per-chunk records.

### Checks performed in this audit

- **Verified:** 64 test functions are present; unit tests cover RRF arithmetic, graph routing, parser behavior, persistence, API response shaping, and evaluation metric arithmetic. CI provisions PostgreSQL, applies Alembic, runs pytest and builds the container ([CI workflow](../../.github/workflows/ci.yml)). Ruff was run locally and reported `All checks passed!`.
- **Not established:** local pytest and Docker/database execution did not yield a completed usable result in this environment, so this audit does **not** claim a fresh test pass, migration, API run, or live Gemini call. Historical live checks in project documentation are artifact-observed, not repeated evidence.
- **Artifact-observed:** the baseline/experiment artifacts describe pinned snapshots and live provider runs. They do not substitute for a clean, current end-to-end verification.

## 3. Strengths

- **Clear separations and bounded control flow -- verified.** Retrieval, guard, prompt, parsing, confidence and persistence are small modules. The graph has explicit terminal paths rather than open-ended model-directed tool use.
- **Useful provenance foundation -- verified.** Chunks retain file paths/line ranges; successful requests retain ranked chunk IDs, scores, tool attempts, model, latency, token count and result. Foreign keys and a version-controlled Alembic schema are sound foundations ([migration](../../migrations/versions/20260819_0001_initial_schema.py#L16)).
- **A real abstention attempt -- verified.** The system does not always call the model: it retries once and can return `INSUFFICIENT_EVIDENCE`. That is materially better than unconditional RAG generation.
- **Good documentation/evaluation hygiene for a portfolio project -- artifact-observed.** The golden set records corpus SHA, prompt hash, model identifiers, thresholds, strategy and dirty-tree metadata. The project documents limitations instead of presenting a single cherry-picked answer as proof.
- **Sensible baseline technology choices -- verified.** Python 3.12, FastAPI, SQLAlchemy/Alembic, PostgreSQL, pgvector, Docker, pytest and Ruff are mainstream, maintainable choices for a service of this size.

## 4. Engineering Findings

| Severity | Finding and evidence | Impact |
|---|---|---|
| **Critical** | **The evidence guard is empirically unsafe.** It accepts when the maximum RRF and minimum vector distance across *any* results independently clear thresholds; they need not be the same chunk. `0.016` is below a single rank-1 RRF contribution of `1/61 = 0.01639`, so RRF does not filter a nonempty vector top result ([`guard.py`](../../app/investigation/guard.py#L7), [`hybrid_search.py`](../../app/retrieval/hybrid_search.py#L37)). Latest saved results show 4 false accepts out of 24 questions and no tested vector cutoff separated answerable from unanswerable cases. | Unsupported generation can occur despite a “sufficient” label. Confidence calibration cannot repair a guard that selected unrelated evidence. |
| **High** | **“Every investigation is auditable” is false for abstentions.** `investigate_repository` returns early at the insufficient-evidence branch; persistence happens only after accepted generation ([`scripts/investigate.py`](../../scripts/investigate.py#L103)). | The most safety-critical decisions lack a durable audit trail, user feedback, and later analysis. This compromises incident review and guard calibration. |
| **High** | **Citation validation is format recognition, not grounding.** A result is “cited” merely when its path/ID occurs anywhere in model text; exact line ranges are optional and no claim-to-evidence entailment is checked ([`parsing.py`](../../app/investigation/parsing.py#L44)). The chunk experiment records a result marked correct with zero citations for `paraphrased-08` ([chunking decision report](../gate-5-chunking-review/chunking-strategy-decision-report.md)). | The UI/API can signal provenance without proving support. A plausible answer can cite an irrelevant range or leave claims uncited. |
| **High** | **Blocking provider I/O runs on async paths.** `embed_text()` and `generate_investigation()` use synchronous `urllib.request.urlopen`; `investigate_repository()` is awaited by FastAPI ([`embed_chunks.py`](../../scripts/embed_chunks.py#L38), [`generation.py`](../../app/investigation/generation.py#L30), [`api.py`](../../app/api.py#L72)). The retry backoff also calls `time.sleep`. | A slow embedding/generation blocks the event loop handling concurrent requests. Under timeout/retry it can monopolize a worker for roughly three 60-second attempts plus sleeps. |
| **High** | **Request and context budgets are unbounded.** API query has no maximum length and `limit` has no upper bound ([`api.py`](../../app/api.py#L26)); prompt construction inserts every selected chunk without a token/character ceiling ([`prompt.py`](../../app/investigation/prompt.py#L18)). | Authenticated callers can create outsized database work, prompt cost, latency and provider failure. A 10/minute IP limiter does not constrain per-request spend. |
| **High** | **Repository identity is not source identity.** `Repository` stores only a unique name, not source root, Git remote, commit, content manifest, branch, or ingest timestamp ([`repository.py`](../../app/db/models/repository.py#L17)). Re-ingestion deletes chunks by name. Grep accepts a path supplied outside stored repository identity ([`mcp_server.py`](../../app/investigation/mcp_server.py#L21)). | A database result and fallback evidence can originate from different source states or directories. This breaks the provenance claim and makes investigations irreproducible. |
| **Medium** | **Retrieval will not scale as implemented.** The migration declares only B-tree repository/path indexes--no HNSW/IVFFlat pgvector index and no materialized/generated `tsvector` plus GIN index. FTS recomputes vectors per row ([migration](../../migrations/versions/20260819_0001_initial_schema.py#L71), [`fulltext_search.py`](../../app/retrieval/fulltext_search.py#L20)). | Full scans/recalculation are acceptable only for small corpora. Latency and cost will degrade with repository size. |
| **Medium** | **The corpus is narrower than the product story.** Ingestion visits only Python, excludes migrations, and uses fixed line windows; it ignores Markdown/runbooks/configuration, CI definitions, logs, traces and incident records. Structural metadata is deliberately blank ([`ingest_repo.py`](../../scripts/ingest_repo.py#L35)). | It cannot reliably investigate most cross-language or operational incidents, and line windows split functions/classes unpredictably. |
| **Medium** | **Literal grep is an unsafe evidence promotion.** It receives the full natural-language question as one literal substring and treats any match as sufficient ([`graph.py`](../../app/investigation/graph.py#L180), [`guard.py`](../../app/investigation/guard.py#L35)). The caller has no explicit subprocess deadline ([`graph.py`](../../app/investigation/graph.py#L54)). | It usually has poor recall for natural-language questions; a comment/string can cause a false acceptance; hung local tooling can hang a request. |
| **Medium** | **Prompt injection and sensitive-source controls are absent.** Raw repository text is interpolated with no trust boundary, source policy, secret redaction, content tagging or output DLP ([`prompt.py`](../../app/investigation/prompt.py#L24)). | Untrusted code/comments can attempt instruction override; code sent to an external model may contain secrets or proprietary information. This matters substantially for an incident tool. |
| **Medium** | **Audit reproducibility is incomplete.** The stored audit omits raw provider payload, raw confidence, provider/model version/configuration, exact prompt, embedding model/version, source commit and chunk content; GET exposes `raw_confidence: null` for persisted records ([`persistence.py`](../../app/investigation/persistence.py#L25), [`api.py`](../../app/api.py#L181)). | A later investigator cannot faithfully explain or replay an answer after source/model drift. Storing only a prompt hash is useful but insufficient. |
| **Low** | **Security is explicitly development-grade.** The project correctly documents a single shared secret and process-local per-IP rate limiter; it lacks user identity, authorization scopes, rotation, durable/distributed quotas and ingress-aware client-IP handling ([`api_security.py`](../../app/api_security.py#L1)). | Fine for a local demo, unsafe for multi-user or multi-instance production deployment. |

These are confirmed source findings, not claims that exploitation occurred. No live security test was performed.

## 5. Retrieval, Grounding, and Evaluation Assessment

### What the evidence actually shows

The pinned golden set has 24 questions: 16 answerable (8 direct, 8 paraphrased) and 8 unanswerable. Its own metadata says **“pending maintainer review”** ([`evaluation/golden_set.json`](../../evaluation/golden_set.json#L1)). In the 15 October baseline artifact, vector and hybrid tie at hit@1/3/5 of 8/16, 11/16 and 11/16; full text achieves 1/16, 1/16 and 2/16. That does **not** substantiate a hybrid retrieval improvement. It does substantiate that current FTS is weak for this code corpus.

The saved 100/20 experiment improves hit@5 from 11/16 to 15/16 and MRR from 0.573 to 0.700 for the same 16 questions, but increases median top-five context by 43.24% and tokens by about 40%. It still reports four guard false accepts, has only two generation passes, one corpus, a pending human gate, and at least one answer regression (`direct-05`) despite better retrieval rank ([chunking decision report](../gate-5-chunking-review/chunking-strategy-decision-report.md)). **Inference:** it is promising evidence to run a larger controlled trial, not proof that 100/20 should replace 60/10.

The test/evaluation suite positively covers retrieval ranking, RRF arithmetic, guard confusion, declared labels, response keyword screens, latency/tokens, and some citation-label summaries. Its gaps are decisive:

- No independently authored/maintainer-approved test set or unseen repositories.
- No codebase diversity (languages, monorepos, generated files, docs/runbooks/configs, incidents).
- Answer scoring uses required keyword groups, not claim-level correctness/completeness or entailment; no human adjudication or calibrated LLM judge.
- Citation precision is label overlap, not citation range validity or whether every material claim is supported.
- No regression gates in CI for a fixed offline/replayable retrieval set; evaluations call a moving provider.
- No load, concurrency, tail-latency, cost-per-successful-answer, data leakage, prompt-injection, authorization, or restart/failure tests.

### Grounding and confidence conclusion

Prompt instructions, explicit abstention, and a downgrade-only confidence calibrator are useful guardrails. They are not a grounding guarantee. Confidence is a categorical model self-report plus hand-set retrieval margins; it has not been calibrated against observed accuracy. The correct product vocabulary is **“heuristic evidence score,” not “confidence,”** until reliability diagrams, calibration curves and per-category error rates support the term.

## 6. October 2026 AI Market Assessment

This section separates market evidence from judgement. Market claims are dated **20 October 2026** and should be refreshed before using them in an application or proposal.

### Signals with practical relevance

- Google’s current model page lists both `gemini-3.5-flash-lite` and `gemini-3.8-flash`; it directs new Gemini 2.5 projects toward the newer 3.5 Flash-Lite or 3.8 Flash. `gemini-embedding-001` remains listed, while Google also lists Gemini Embedding 2 ([Google model catalogue, accessed 20 Oct 2026](https://ai.google.dev/gemini-api/docs/models.md); [deprecation schedule, accessed 20 Oct 2026](https://ai.google.dev/gemini-api/docs/deprecations/)). The project’s provider choices are therefore viable, but a hard-coded provider/model pair is weak operational practice.
- Structured output and tool calling are now first-class API capabilities: Google documents JSON-Schema-constrained structured output for final formatting and function calling for application actions ([Structured Output docs, accessed 20 Oct 2026](https://ai.google.dev/gemini-api/docs/structured-output); [Function Calling docs, accessed 20 Oct 2026](https://ai.google.dev/gemini-api/docs/function-calling)). This makes text regex parsing a portfolio liability when the provider can return a schema-constrained result.
- A 2026 survey of 400 engineering leaders reports a large prototype-to-production gap and associates automated evaluation sets with production deployment; this is a vendor survey, not a universal statistic, but its direction matches the project’s main weakness ([Solidslate, 2026](https://www.solidslategroups.com/insights/state-of-ai-engineering)).
- Recurrent 2026 job-market signals and engineering reports emphasize backend delivery, Python/FastAPI, APIs, retrieval/vector stores, evaluation, observability, cost and operations. Individual job listings are too volatile and self-selected to quantify reliably; the enduring hiring value is the ability to demonstrate these production behaviors, not possession of any one agent framework.

### Market judgement

RAG, hybrid retrieval, reranking, vector search, API integration and agent/tool workflows remain relevant, but **basic RAG is commoditized.** Hiring differentiation now comes from evaluating retrieval and answer quality, handling failure modes, securing data/tool boundaries, managing cost/latency, and shipping observable backend services. IncidentWeave can demonstrate those skills only after the reliability gaps are closed and measured. Its bounded graph is more credible than a multi-agent novelty demo, but the present MCP use adds subprocess complexity without delivering model-directed or multi-system tool value.

## 7. Technology-by-Technology Assessment

| Current choice | Assessment | Credible alternatives and decision |
|---|---|---|
| Python 3.12 + FastAPI + Pydantic | Strong, market-relevant choice. Async DB support is sound; provider calls currently negate async benefits. | Keep. Use an async HTTP client/official SDK, deadlines, bounded concurrency and a job model for long investigations. Node/Go only win for existing organizational constraints or extreme service needs. |
| PostgreSQL + SQLAlchemy + Alembic | Excellent single-service baseline with transactional metadata/audit storage. | Keep. Add source-version schema and retrieval indexes before considering a separate search database. Elasticsearch/OpenSearch becomes justified for very large lexical/code-search needs; dedicated vector stores only after measured scale/operational need. |
| pgvector cosine search | Suitable for a modest, tenant-scoped corpus; currently exact/unindexed. | Keep initially; add HNSW or IVFFlat only after measuring corpus size/recall/latency. HNSW generally favors low-latency recall but has build/write memory cost; IVFFlat needs tuning/training. |
| PostgreSQL FTS + RRF | FTS is sensible in principle, but English lexical analysis over code and unindexed expression scans perform poorly here. The artifact’s weak FTS validates the concern. | Change implementation, not necessarily database: persist/index `tsvector`, use code-aware tokenization/query expansion, and test a stronger lexical baseline (e.g., trigram/exact-symbol search) before adding a search cluster. Add a reranker only if offline evaluation shows material lift. |
| Gemini embedding/generation via raw REST | Current model identifiers are supported as of audit date. Raw `urllib` is brittle and blocks the event loop; hard-coding ties the system to one model/version. | Keep Gemini if its quality/cost/data terms suit the deployment, but create a narrow provider interface and evaluate Gemini, OpenAI, Anthropic or self-hosted choices on the actual test set. Switch model only on quality/cost/latency or governance evidence. |
| Text prompt + regex parser | The least reliable part of a structured investigation contract. | Change to provider structured output with a schema containing diagnosis, claim list, citations referencing exact chunk/range, abstention reason, and uncertainty. Validate every reference server-side. |
| LangGraph | A bounded retry/fallback state machine is a reasonable learning artifact, but this graph is small and deterministic. | Keep only if it continues to earn its dependency through tracing/checkpointing or expected branching growth. A plain tested async state function is simpler if not. Do not add LangChain merely for résumé keywords. |
| MCP local stdio grep | Demonstrates protocol familiarity but is not a good production fallback: it starts a subprocess and accepts any literal match. | Consider later. Use an in-process, repository-version-bound exact/symbol search first. Use MCP when tools are independently hosted, permissioned, and genuinely interoperable. |
| Docker Compose / single container | Appropriate development baseline. | Keep for local reproducibility. Change deployment practice before production: secrets manager, non-root image, health/readiness, migration job, structured telemetry, worker scaling and managed database backups. |
| pytest, Ruff, GitHub Actions | Strong quality baseline, including a real PostgreSQL CI service. | Keep. Add type checking, dependency/security scanning, integration contract tests, offline retrieval/eval regression gates, and load/security tests. |

## 8. Recommended Stack

### Keep

- Python/FastAPI, SQLAlchemy/Alembic, PostgreSQL/pgvector, Docker, pytest/Ruff, CI.
- Repository-scoped chunks with line-range provenance.
- Explicit abstention design, bounded retry, and audit intent.
- Direct integration behind a small provider adapter; direct APIs are preferable to an orchestration framework for this narrowly defined workflow.

### Change

- Make source version (remote/path policy, commit/content hash, ingested timestamp and embedding/model version) a first-class, immutable ingestion record; bind every query and fallback to it.
- Replace score heuristics with per-chunk sufficiency features, deterministic citation validation and calibrated abstention using an independently reviewed set.
- Use structured generation output; retain raw response/prompt/version/config safely with access controls; persist all outcomes, including refusals/errors.
- Replace synchronous network calls with async/delegated work, apply end-to-end deadlines, cap query/context/limit, and introduce cost/latency telemetry.
- Add generated `tsvector` + GIN and selected pgvector ANN indexes only with benchmarked recall/latency targets; make lexical search code-aware.

### Consider Later

- A reranker after a labelled retrieval experiment establishes a gain.
- Tree-sitter/AST plus semantic document/config/log chunkers after requirements define supported languages/document types.
- Durable workflow/background execution and Redis/cache when concurrency or async job UX makes them necessary.
- OpenTelemetry-compatible tracing/evaluation tooling if in-house structured traces stop being sufficient.
- A separate search/vector service only after PostgreSQL measurements show the real bottleneck.

## 9. Portfolio and Interview Assessment

### What it genuinely demonstrates now

It demonstrates competent backend foundations, relational modelling/migrations, async database usage, provider integration, simple hybrid ranking, bounded workflow orchestration, testable modular code, CI and unusually detailed engineering documentation. An interviewer should see it as a serious learning/build project rather than a copied chatbot.

### What would be challenged

An experienced interviewer is likely to ask: “Why does hybrid not beat vector in your result?” “What does your confidence mean mathematically?” “How do you prove a citation supports the claim?” “What happens under 20 concurrent requests?” “Which commit did this answer describe?” “How do you prevent secret leakage/prompt injection?” “Why MCP for a local grep?” “What data supports the 60/10 or 100/20 choice?” Current code and artifacts make these fair challenges.

The highest-value career improvements are: (1) an independently authored benchmark/evaluation report with failure slices and regression gate; (2) immutable provenance and validated citation/claim schema; (3) async/cost/latency/observability work with measured load behavior; (4) code-aware multi-artifact ingestion; and (5) a concise deployment/security threat model. These demonstrate engineering judgement more effectively than adding another model provider or agent library.

## 10. Prioritized Action Plan

| Priority | Action | Expected value / effort |
|---|---|---|
| 1 | Define and test a trustworthy answer contract: immutable source version, per-claim exact chunk/range citations, server validation, durable records for success/refusal/error, and a correction path. | **Highest impact; medium effort.** Directly repairs the product’s central trust claim. |
| 2 | Build a reviewed, held-out evaluation set across at least several repositories and artifact types; measure retrieval recall/NDCG, citation precision/recall, answer correctness/completeness, abstention, cost and tail latency. Gate regressions in CI with replayable provider fixtures or approved stable runs. | **Highest hiring value; medium-high effort.** Turns assertions into evidence. |
| 3 | Replace blocking provider calls and unbounded input/context with async HTTP/worker execution, cancellation/deadlines, concurrency controls, maximum query/K/context budgets and request cost accounting. | **High reliability value; medium effort.** Makes FastAPI honest under concurrent use. |
| 4 | Redesign ingestion/search around supported artifact types and source versions; introduce code-aware structural chunks and improve lexical retrieval. Benchmark FTS/vector/hybrid/rerank alternatives before adopting the winner. | **High quality value; high effort.** Expands beyond a Python source Q&A demo. |
| 5 | Add a minimal production-operability/security layer: proper identity/scopes, secret and source-data policy, input/output controls, structured logs/traces/alerts, backup/migration/runbook, load/failure tests. | **High portfolio value; medium effort.** Addresses the gap between local demo and service. |

## 11. Verification Gaps

- A fresh local database/migration/API/Gemini end-to-end run was not established in this audit; the available runtime checks did not complete with usable output. Historical documentation and JSON are not a substitute.
- No repository contents external to IncidentWeave were inspected or evaluated; no conclusion is possible about language/doc/log breadth or real incident usefulness.
- No deployment configuration, cloud account, secrets manager, monitoring backend, production traffic, SLO, cost invoice, access-control policy or threat-model artefact was available.
- No independent maintainer review of the golden labels, answer grades or chunking experiment was found. The golden set explicitly remains pending review.
- No live provider test verified current model behavior, rate limits, cost, data residency or retention terms. Current official model documentation verifies model availability, not this application’s account entitlements.
- No load/penetration testing or source-data leak test was performed. Security observations are code-based risks, not confirmed incidents.

## 12. Final Verdict

**Maturity:** well above a tutorial in engineering intent and documentation; below production-ready in reliability, security and operational design.  
**Market competitiveness:** a credible junior-to-mid AI/backend portfolio foundation today, but not yet evidence of production-grade AI reliability.  
**Best next step:** do not rewrite it or add more agents. Deliver one rigorous “trustworthy investigation” increment: versioned source provenance, structured claim/citation output, auditable abstentions, and a reviewed evaluation proving the revised guard improves false-accept and citation metrics. That is the shortest route to both a better system and a more compelling portfolio narrative.
