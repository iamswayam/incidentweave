# IncidentWeave Architecture

**Canonical repository:** [github.com/iamswayam/incidentweave](https://github.com/iamswayam/incidentweave)

IncidentWeave is a repository-aware AI incident investigation platform. Its purpose is to help an engineer investigate questions about a software repository by retrieving source evidence, presenting that evidence to a language model, and returning a diagnosis with references to retrieved chunks. The implemented workflow starts by ingesting Python source into PostgreSQL/pgvector, then accepts a query, searches the selected repository, applies a numeric evidence gate, widens retrieval once if needed, and either abstains or generates and optionally persists a response.

**Implemented capability:** local Python repository ingestion, fixed-window chunking, Gemini embeddings, PostgreSQL vector and full-text retrieval, RRF fusion, a score-based evidence guard, one widened retrieval retry, Gemini response parsing, categorical confidence downgrading, and Investigation/Audit persistence. The HTTP API exposes synchronous investigation and repository-read endpoints; ingestion and embedding remain CLI operations.

**Intended goal versus guarantee:** the prompt and citations are intended to keep investigations evidence-oriented. The implementation does not verify that every answer claim is entailed by cited content, and the evidence guard does not check semantic relevance. Evaluation results are small-sample diagnostics, not evidence of general accuracy or reliability. This document makes no claim that the system is production-ready or eliminates unsupported model output.

This is a source-grounded reference, not authorization to change the architecture. It distinguishes implemented code, test coverage, saved measurements, inference, and behavior not verified at runtime.

**Evidence labels:** **Source-verified** means explicit in current source. **Tested** means an automated test covers the behavior (test execution is separately stated). **Artifact-observed** means present in a saved evaluation artifact. **Inferred** means follows from code wiring but was not directly exercised. **Unknown** means the repository or available runtime evidence does not establish the behavior.

**Inspected revision:** `e104005848bdee38d603d3703f93a5ff9bce79e1`, branch `phase-8/evaluation`, inspected 2026-10-17. At inspection, the local branch and stored `origin/phase-8/evaluation` ref matched. The working tree had an existing untracked `evaluation/results/run-2.json`; ignored evaluation artifacts were also present. No remote fetch was performed. The source permalinks below target this inspected commit; their public availability depends on that commit being present on GitHub. This architecture document was created after that revision check.

## How to Verify This Architecture

1. Check the checkout you are actually using with `git status --short --branch` and `git rev-parse HEAD`; do not assume the local branch matches GitHub. The revision above is the revision inspected for this document, not a promise about a later checkout.
2. Follow the local relative source links to inspect the implementation. The absolute GitHub links in section 14 point to the recorded commit SHA; they resolve publicly only if that commit has been pushed and is accessible.
3. A test's presence establishes test coverage, not that the test passed in your environment. Run the relevant test command and record its output before calling behavior tested. No test suite was run for this documentation update.
4. For an evaluation report, compare its `code_sha` to the evaluated source revision and its `pinned_sha` to the corpus commit. Also inspect `code_dirty`, `code_untracked_files`, `golden_set_sha256`, model, thresholds, prompt hash, pass files, and configuration metadata. Matching a report's code SHA alone does not reproduce provider behavior.
5. Evaluation caches, run reports, snapshots, and other local or ignored artifacts may not be included in the public repository. Their local presence is not evidence that another checkout or GitHub has them. Use only artifacts available in the checkout being reviewed, and mark missing evidence as unknown.

## 1. System Overview

The two principal paths connect indexed repository content to a user investigation. Ingestion stores Python source chunks and their embeddings in PostgreSQL/pgvector. A query is embedded and searched against one named repository using vector and PostgreSQL full-text retrieval; RRF combines their rankings before the evidence guard decides whether to proceed, retry once, or abstain. Guard-accepted content is placed in a prompt for Gemini. A generated result can be persisted with an audit record; an insufficient-evidence result is returned without persistence.

**Source-verified:** The application uses Python 3.12+, FastAPI, SQLAlchemy async sessions, PostgreSQL, pgvector, LangGraph, and MCP. Gemini is called using synchronous `urllib` requests. Evaluation code is outside `app/` and calls the investigation pipeline with persistence disabled.

**Observed scope:** The ingestion CLI handles `*.py` only. The API exposes investigation and repository-read endpoints, not ingestion or embedding endpoints. Markdown, runbooks, SOPs, logs, background jobs, and other document ingestion are not implemented by the inspected ingestion path.

**Verification status:** Source behavior is described from the inspected code. Test coverage is identified separately; this document update did not execute tests. Saved evaluation values are labeled artifact-observed. Database, deployed-service, and provider behavior remains unverified unless a cited saved artifact records it.

## 2. Component and Module Responsibilities

| Component | Responsibility and key implementation |
|---|---|
| `scripts/ingest_repo.py` | Selects a local root and repository name, traverses Python files, creates line-window chunks, and replaces that repository's chunk rows. [`iter_python_files`](../../scripts/ingest_repo.py#L35), [`chunk_lines`](../../scripts/ingest_repo.py#L49), [`ingest_repository`](../../scripts/ingest_repo.py#L70). |
| `scripts/embed_chunks.py` | Embeds chunks that have no vector through Gemini `embedContent`; handles each chunk independently and commits after iteration. [`embed_text`](../../scripts/embed_chunks.py#L38), [`embed_repository_chunks`](../../scripts/embed_chunks.py#L77). |
| `app/db/models/` and `migrations/` | Define Repository, Chunk, Investigation, and Audit storage and the initial schema. [Models](../../app/db/models/), [initial migration](../../migrations/versions/20260819_0001_initial_schema.py#L16). |
| `app/retrieval/vector_search.py` | Top-K pgvector cosine-distance query scoped by repository ID. [`search_vector`](../../app/retrieval/vector_search.py#L11). |
| `app/retrieval/fulltext_search.py` | Query-time PostgreSQL full-text filtering and ranking. [`search_fulltext`](../../app/retrieval/fulltext_search.py#L9). |
| `app/retrieval/hybrid_search.py` | Runs both retrievers, combines rankings with reciprocal-rank fusion (RRF), and returns fused top-K. [`hybrid_search`](../../app/retrieval/hybrid_search.py#L9). |
| `app/investigation/graph.py` | LangGraph orchestration: retrieval, guard, one widening retry, insufficient-evidence return, prompt, generation, parse, and calibration. [`create_investigation_graph`](../../app/investigation/graph.py#L94). |
| `app/investigation/guard.py` | Score-based evidence gate; it does not inspect golden labels or prove semantic relevance. [`evaluate_evidence_sufficiency`](../../app/investigation/guard.py#L11). |
| `app/investigation/mcp_server.py` | Exposes `hybrid_search` and `grep_search` MCP tools; the investigation graph does not invoke this server. [`grep_search_tool`](../../app/investigation/mcp_server.py#L99). |
| `app/investigation/prompt.py`, `generation.py`, `parsing.py`, `confidence.py` | Build evidence prompt, call Gemini, parse response/citations, and downgrade confidence where score margins are weak. [`build_grounded_prompt`](../../app/investigation/prompt.py#L20), [`generate_investigation`](../../app/investigation/generation.py#L30), [`parse_investigation_response`](../../app/investigation/parsing.py#L118), [`calibrate_confidence`](../../app/investigation/confidence.py#L9). |
| `app/investigation/persistence.py` | Stores parsed diagnosis and audit metadata when the pipeline's `persist` flag permits it. [`persist_investigation`](../../app/investigation/persistence.py#L11). |
| `scripts/investigate.py`, `app/api.py`, `app/main.py` | CLI/pipeline entry and synchronous HTTP API. [`investigate_repository`](../../scripts/investigate.py#L42), [API routes](../../app/api.py#L68), [FastAPI app and error handlers](../../app/main.py#L1). |
| `evaluation/`, `scripts/run_eval.py` | Pinned-corpus validation, retrieval and end-to-end measurement, per-question traces, reports, and run comparison. [`run_evaluation`](../../evaluation/runner.py#L715), [`compare_reports`](../../evaluation/compare.py#L77). |

**MCP distinction:** The server exposes both `hybrid_search` and `grep_search`, but the investigation graph does not call either MCP tool. Hybrid search is imported and called directly ([graph retrieval](../../app/investigation/graph.py#L100)); the future of the MCP module is deferred to checklist item 25.

## 3. Ingestion and Indexing Flow

1. **Repository selection — Source-verified.** `python -m scripts.ingest_repo <repo_path> <repo_name>` takes a filesystem path and a separate database identity. It resolves the path and requires an existing directory. It looks up or creates a `Repository` by exact name; there is no stored source-root association ([argument parsing](../../scripts/ingest_repo.py#L129), [`ingest_repository`](../../scripts/ingest_repo.py#L70)).
2. **Traversal and formats — Source-verified.** Traversal is sorted `rglob("*.py")`. Excluded path components are `.git`, `.kilo`, `.pytest_cache`, `.ruff_cache`, `.venv`, `__pycache__`, and `migrations` ([`IGNORE_DIRS`](../../scripts/ingest_repo.py#L24), [`iter_python_files`](../../scripts/ingest_repo.py#L35)). No Markdown, log, PDF, or other format parser is present in this path. Files are decoded as UTF-8 with replacement.
3. **Parsing and chunking — Source-verified.** No AST or syntax parser is used. `chunk_lines` creates 60-line windows with 10-line overlap (step 50), skips windows that add no new lines, and discards blank-only content ([`chunk_lines`](../../scripts/ingest_repo.py#L49), chunk construction at [line 101](../../scripts/ingest_repo.py#L101)). Python slices use an exclusive end index; the code stores that index as `line_end`, which is the inclusive, one-based number of the final included source line.
4. **Metadata and provenance — Source-verified.** Each Chunk receives repository ID, exact content, relative POSIX file path, `file_type="python"`, `document_type="code"`, and line start/end. `function_name`, `class_name`, and `symbol` are explicitly `None`; additional schema fields such as section/service/environment/incident ID/timestamp are nullable and not populated by this ingester ([Chunk model](../../app/db/models/chunk.py#L17), chunk construction [line 101](../../scripts/ingest_repo.py#L101)).
5. **Replacement behavior — Source-verified.** Ingestion deletes all existing chunks for the selected repository ID, inserts the newly generated set, and commits once ([`ingest_repository`](../../scripts/ingest_repo.py#L88)). This is clean replacement rather than append-only accumulation. There is no chunk content/path uniqueness constraint or incremental diff. **Inferred:** chunk IDs can change on re-ingestion, while audit rows hold integer ID arrays without chunk foreign keys, so historical IDs can become stale.
6. **Embedding generation — Source-verified.** Run separately with `python -m scripts.embed_chunks <repo_name>`. It selects rows with null embeddings, calls Gemini `models/gemini-embedding-001` one chunk at a time, requests `outputDimensionality=768`, validates the response length, casts values to float, and assigns the vector ([model and dimension](../../scripts/embed_chunks.py#L25), [`embed_text`](../../scripts/embed_chunks.py#L38), [`embed_repository_chunks`](../../scripts/embed_chunks.py#L77)). Requests use `urllib`, a 60-second timeout, and a 1.5-second sleep after every chunk attempt. There is no batch API or automatic retry. Per-chunk exceptions are printed/counted; iteration continues and the session commits at the end. A failed chunk remains without an embedding and can be retried by rerunning the script.
7. **FTS preparation — Source-verified.** No FTS column/vector is created during ingestion. Search computes `to_tsvector('english', content)` and `websearch_to_tsquery(query)` at request time and orders by `ts_rank_cd` ([`search_fulltext`](../../app/retrieval/fulltext_search.py#L9)).

**Evaluation-specific exception:** `evaluation/runner.py::setup_eval_corpus` inserts pinned-snapshot chunks into one strategy-specific allowlisted evaluation repository using ranges from `evaluation/chunk_experiments.py`. If that repository already exists, its path/range/content tuples must exactly match the selected snapshot and strategy or setup fails without replacing rows. Matching rows are reused; only missing embeddings are submitted for embedding. The production `scripts.ingest_repo.chunk_lines` function is not patched or called by this evaluation setup. The inventory guard permits count changes only in the selected evaluation repository and rejects changes, creation, or disappearance elsewhere ([`setup_eval_corpus`](../../evaluation/runner.py#L274), [`ensure_non_eval_inventory_unchanged`](../../evaluation/runner.py#L241), [strategy definitions](../../evaluation/chunk_experiments.py)).

**Tests:** `tests/unit/test_ingest_repo.py` covers chunk window boundaries; `tests/unit/test_evaluation.py` checks pinned snapshot counts. These tests were inspected but not run while writing this document. Path containment for symlinks, live DB replacement, and provider failure behavior are not established by those tests.

## 4. User-Query Investigation Flow

1. **Entry points — Source-verified.** The investigation CLI is `python -m scripts.investigate <repo_name> <query> [--limit N]`; `scripts/search_repo.py` is a separate hybrid-search-only CLI. HTTP routes are `POST /investigations`, `GET /investigations/{id}`, `GET /repositories`; `/health` is open ([routes](../../app/api.py#L26), [health and error handlers](../../app/main.py#L1)).
2. **Validation and authentication — Source-verified.** The Pydantic request requires repository name length 1-255, query length at least one character, and positive limit default 5, with no maximum limit. Protected routes require `X-API-Secret`, compare against configured secret with `secrets.compare_digest`, then apply a 10-request/60-second per-client-IP in-memory sliding window ([request model](../../app/api.py#L26), [`require_api_access`](../../app/api_security.py#L57)).
3. **Repository and query embedding — Source-verified.** `investigate_repository` finds the exact repository row, obtains its ID, synchronously embeds the query using the embedding script, and starts the graph with initial limit `limit` and retry limit `2 * limit` ([`investigate_repository`](../../scripts/investigate.py#L42)).
4. **Retrieval and guard — Source-verified.** Graph retrieval calls `hybrid_search` for the selected database repository. Guard checks scores and appends an attempt record. If sufficient, the graph builds a prompt; if insufficient on first search it widens; if insufficient after widening it returns `INSUFFICIENT_EVIDENCE` without generation ([graph routing](../../app/investigation/graph.py#L164)).
5. **Prompt and generation — Source-verified.** The prompt includes the query plus each hybrid result's ID, path, line range, scores, and content. It tells Gemini to use only supplied repository evidence and to return `INSUFFICIENT_EVIDENCE` if unsupported ([`SYSTEM_INSTRUCTION`](../../app/investigation/prompt.py#L7), [`build_grounded_prompt`](../../app/investigation/prompt.py#L20)). The graph calls Gemini synchronously after guard acceptance.
6. **Parsing, calibration, response — Source-verified.** The parser extracts diagnosis, the model's self-rating, and cited IDs; retrieval calibration may lower a `high` self-rating to `medium`. The CLI labels the value `Model self-rating`; the API exposes it as `model_self_rating` with a note that it is not a measured probability of correctness ([response model](../../app/api.py#L34)).
7. **Persistence — Source-verified.** API POST passes `persist=True`; the investigation CLI defaults to `True`. Evaluation passes `False`. Guard-level insufficient evidence returns before persistence. A generated path that reaches persistence stores an Investigation and an Audit row ([pipeline persistence branch](../../scripts/investigate.py#L90), [`persist_investigation`](../../app/investigation/persistence.py#L11)).

## 5. Mermaid Diagram: Ingestion

```mermaid
flowchart TD
    A[repo_path and repo_name] --> B[Resolve and validate directory]
    B --> C[Traverse sorted Python files]
    C --> D[Apply directory exclusions]
    D --> E[Read UTF-8 with replacement]
    E --> F[60-line windows, 10-line overlap]
    F --> G[Delete existing chunks for repository]
    G --> H[Insert chunk content, path, line range, metadata]
    H --> I[Commit chunk rows]
    I --> J[Select chunks with null embeddings]
    J --> K[Gemini embedContent, 768 dimensions, one request per chunk]
    K --> L[Commit successful embeddings]
    L --> M[Query-time vector search]
    L --> N[Query-time full-text search over content]
```

## 6. Mermaid Diagram: Investigation

```mermaid
flowchart TD
    A[API POST or investigate CLI] --> B[Validate request; API secret and rate limit]
    B --> C[Look up repository by exact name]
    C --> D[Embed query with Gemini]
    D --> E[Vector top K and FTS top K]
    E --> F[RRF merge and truncate to K]
    F --> G{Any chunk vector distance <= provisional 0.5?}
    G -->|Yes| J[Build prompt from fused chunks]
    G -->|No, first pass| H[Widen limit once to 2K]
    H --> E
    G -->|No, after retry| Z[Return INSUFFICIENT_EVIDENCE; do not persist]
    J --> K[Gemini generateContent; up to 3 attempts]
    K --> L[Parse diagnosis, confidence, citation IDs]
    L --> M[Downgrade high confidence if score margins fail]
    M --> N{persist enabled?}
    N -->|Yes| O[Write Investigation and Audit]
    N -->|No| P[Return without persistence]
    O --> Q[API response or CLI output]
    P --> Q
```

## 7. Database Schema and Data Lifecycle

| Entity | Important fields and relationships |
|---|---|
| `repositories` | Integer ID, unique non-null name (255 chars), created/updated timestamps. One repository has chunks and investigations. [Model](../../app/db/models/repository.py#L17). |
| `chunks` | Repository FK with `ON DELETE CASCADE`; content, file path, line bounds, nullable file/document/symbol/function/class/section/service/environment/incident/timestamp metadata, nullable `VECTOR(768)`. B-tree indexes on repository ID and `(repository_id, file_path)`; no declared uniqueness, pgvector, or FTS index. [Model](../../app/db/models/chunk.py#L17), [migration](../../migrations/versions/20260819_0001_initial_schema.py#L38). |
| `investigations` | Repository FK, query, parsed diagnosis in `response`, model, latency, token usage, final model self-rating, outcome, optional error class, timestamp; index on repository ID. [Model](../../app/db/models/investigation.py#L17). |
| `audit_records` | Investigation and repository FKs; integer array of retrieved chunk IDs; parallel score arrays; JSONB tool trace; model, parsed diagnosis, latency, token count, confidence, feedback. No chunk FK for elements of `retrieved_chunk_ids`. [Model](../../app/db/models/audit.py#L17). |

Migration `20260819_0001_initial_schema` creates the vector extension and initial tables/indexes; `20261024_0002_investigation_outcome` adds outcome and error-class fields. Migration execution was not performed. SQLAlchemy sessions are configured through `AsyncSessionLocal` in [app/db/session.py](../../app/db/session.py#L1). PostgreSQL full-text indexes are not declared in these migrations.

## 8. Retrieval, RRF, Evidence Guard, Retry and Abstention

- **Vector — Source-verified:** pgvector cosine distance, ascending, repository-scoped, excludes null embeddings; top K from `search_vector` ([implementation](../../app/retrieval/vector_search.py#L11)).
- **Full text — Source-verified:** `websearch_to_tsquery` filters English `to_tsvector` content and ranks by `ts_rank_cd`; top K ([implementation](../../app/retrieval/fulltext_search.py#L9)). Query lexemes are not guaranteed to match code tokens; the Phase 8 log observed many empty results.
- **RRF — Source-verified:** for each chunk, sum `1 / (60 + rank)` over the vector and FTS lists where the chunk appears. Shared chunks get both contributions. Sort descending and return K ([fusion](../../app/retrieval/hybrid_search.py#L21)). Numeric source scores are not averaged.
- **Guard — Source-verified:** evidence is sufficient when at least one retrieved chunk has a vector distance `<= 0.5`. RRF is used for ranking and reporting, not as a gate; a result without a vector distance cannot make evidence sufficient ([guard](../../app/investigation/guard.py)). The cutoff is provisional and will be re-validated on the held-out split in checklist item 3b.
- **Widening — Source-verified:** if the initial result is insufficient, one retry doubles requested K. A vector-only closest distance will not improve merely because K grows; RRF membership can change. This is an implication of the ranking query, not a separate live measurement.
- **Retry and abstention — Source-verified:** after an insufficient widened result, the graph returns `INSUFFICIENT_EVIDENCE` without generation. The MCP server separately exposes literal `grep_search`; the investigation graph does not call it.
- **MCP — Source-verified:** `app.investigation.mcp_server` exposes `hybrid_search` and `grep_search` tools over stdio, but neither is invoked by the investigation graph. The graph calls `hybrid_search` in-process.

## 9. LLM Integration, Prompting, Parsing and Confidence

- **Provider/model — Source-verified:** generation endpoint is Gemini `generateContent`, model `gemini-3.5-flash-lite`, request body contains prompt text, timeout is 60 seconds, maximum is three attempts. HTTP 429/500/502/503/504, URL errors, timeouts, and OS errors retry with 1- and 2-second sleeps; other HTTP errors fail immediately ([generation constants and function](../../app/investigation/generation.py#L11)). No explicit generation config/sampling parameters are sent. Generation latency is measured around a successful HTTP attempt, not all retry time.
- **Prompt — Source-verified:** retrieved hybrid chunks are included with ID, file path, line bounds, vector/FTS/RRF scores, and content. Instructions constrain statements to supplied evidence and request the exact abstention marker when evidence is insufficient ([prompt](../../app/investigation/prompt.py#L7)). No explicit context token budget or truncation is implemented there.
- **Parsing — Source-verified:** first candidate text is used. Diagnosis is extracted by a section regex; missing/empty diagnosis becomes `INSUFFICIENT_EVIDENCE`. An `INSUFFICIENT_EVIDENCE` diagnosis forces confidence to `low`, while citation matches are kept. Missing confidence becomes `low` ([parser](../../app/investigation/parsing.py#L118)).
- **Citation matching — Source-verified:** a returned chunk is marked cited if response text contains its chunk ID, exact file path, or a file path plus line range ([matcher](../../app/investigation/parsing.py#L44)). This detects reference format, not whether a claim is supported by that chunk.
- **Confidence — Source-verified:** only `high` may be downgraded, to `medium`, when RRF is below `0.032` or best vector distance exceeds `0.4`; there is no upgrade path ([calibrator](../../app/investigation/confidence.py#L9)).
- **Secrets and errors — Source-verified:** provider keys are read from `GEMINI_API_KEY`; the permanent launcher copies the Settings value into the process environment. API errors avoid returning raw internal messages. API maps some pipeline `ValueError`s to 422, repository-not-found to 404, generation `RuntimeError` to 502, and unexpected errors to generic 500 ([route](../../app/api.py#L68), [exception handlers](../../app/main.py#L15)). **Inferred:** embedding `ValueError`s may be indistinguishable from input validation failures at the route.

## 10. Audit, Citations, Abstention and Persistence

- **Generated result:** `persist_investigation` reparses the provider response and stores the parsed diagnosis, model, latency, token count and final self-rating in Investigation and Audit rows; the Investigation stores either `answered` or `abstained_model` as its outcome. Audit JSON stores tool attempts, cited IDs, and retrieval metadata; it does not store full retrieved chunk text or the original Gemini response payload ([persistence](../../app/investigation/persistence.py#L11)).
- **Guard refusal:** if the graph remains insufficient after the widened retry, it returns `INSUFFICIENT_EVIDENCE`; with `persist=True`, one Investigation (`refused_guard`) and Audit row preserve the refusal reason and retrieval summary without generation latency. Evaluation uses `persist=False` and does not write these rows ([graph return](../../app/investigation/graph.py#L193), [outcome taxonomy](../../evaluation/metrics.py#L193)).
- **Investigation error:** exceptions during embedding or graph execution are re-raised after an `error` outcome and an Audit row are attempted when `persist=True`. Only the exception class name is stored, never its message.
- **Evaluation persistence:** `run_pipeline_once` calls the same investigation function with `persist=False` and captures compact generation metadata for measurement; it does not request Investigation/Audit writes ([runner](../../evaluation/runner.py#L320)).
- **API response:** POST returns investigation ID, diagnosis, outcome, `model_self_rating`, a `rating_note`, citations, evidence check, retry flag, tool calls, model, latency, and a static note summarizing Phase 8 ([response model](../../app/api.py#L34)). The rating note identifies the value as the model's own label, explains retrieval-based downgrades, and says it is not a measured probability of correctness. GET returns the stored outcome, final model self-rating and the same note; error class is not exposed. `/repositories` returns total and embedded chunk counts.
- **Documentation mismatch:** README says raw model response is persisted; current persistence code stores parsed diagnosis, not the raw provider response ([README](../../README.md#L170), [implementation](../../app/investigation/persistence.py#L25)).

## 11. Evaluation Architecture and Available Results

**Evaluation flow — Source-verified:** `evaluation/golden_set.json` pins a corpus SHA and 24 labeled questions (8 direct, 8 paraphrased, 4 far-unanswerable, 4 near-unanswerable). `run_evaluation` exports that commit, validates source labels and index reachability, selects an explicitly allowlisted evaluation repository, computes independent vector/FTS/hybrid retrieval metrics, then runs two pipeline passes with `persist=False`. The evaluation-only strategies are `baseline` (60/10, `incidentweave-eval`, default) and `w100_o20` (100/20, `incidentweave-eval-w100_20`). Expected chunk ranges are computed from the selected strategy. New evaluation repositories receive evaluation-owned chunk rows; existing repositories are reused only when all path/range/content tuples match, otherwise setup fails closed without deleting or replacing data. It writes `pass-1.json`, `pass-2.json`, and `report.json` under a strategy-specific run ID. Report metadata records code/corpus SHAs, tracked dirty state, untracked file count, models, thresholds, prompt hash, strategy, chunk size, overlap, evaluation repository, and config hash ([golden set](../../evaluation/golden_set.json#L1), [`run_evaluation`](../../evaluation/runner.py#L715), [strategy definitions](../../evaluation/chunk_experiments.py), [corpus export](../../evaluation/corpus.py#L25)). The `w100_o20` harness is implemented in the current working tree but remains uncommitted; no experiment run is authorized by this implementation task.

**Metrics — Source-verified:** Retrieval hit@1/3/5 and MRR use file-path plus case-insensitive label substring. Guard confusion counts answerability vs guard sufficiency. The keyword answer screen requires one term from each `must_mention` group; it is not human correctness or claim grounding. V2 outcomes add guard refusal, model abstention, retrieval miss, labeled/unlabeled context pass, incomplete/wrong, and error. Citation summary checks cited chunks against the same labels. Generation traces capture raw text, prompt hash/length, finish reason, usage, latency, throttle wait, and HTTP call counts ([metrics](../../evaluation/metrics.py), [runner records](../../evaluation/runner.py#L451)).

**Available artifacts — Artifact-observed:** Legacy [baseline.json](../../evaluation/results/baseline.json), [run-2.json](../../evaluation/results/run-2.json), and [evaluation_report.json](../../evaluation/results/evaluation_report.json), plus six timestamped run bundles, each with report and two pass files:

| Run ID | Reported code SHA | `code_dirty` / untracked count |
|---|---|---|
| `20261005T143011Z-abe7796` | `abe77967b5ae9635bff486303cdddd44b0b28e2c` | true |
| `20261005T150844Z-fea9d8d` | `fea9d8d2b2eb2e31ac9f6e674b566766ed4748ae` | true |
| `20261005T151632Z-fea9d8d` | `fea9d8d2b2eb2e31ac9f6e674b566766ed4748ae` | true |
| `20261005T152746Z-2a6c658` | `2a6c658636e9f0e8d77933f3d899cff1b37e3d03` | true |
| `20261014T160330Z-305200f` | `305200f223f4c0bdea61519e5ff5c7bfd2903e7c` | false; 1 untracked |
| `20261015T151657Z-c203e0e` | `c203e0e3fac87340addfe905ce3bd17eacfbe35f` | false; 1 untracked |

All six timestamped runs report corpus SHA `62d0e58593bb22d187ec7930274b0457afd3be74`, 40 files/70 chunks, embedding model `models/gemini-embedding-001`, generation model `gemini-3.5-flash-lite`, limit 5, and provider-default generation settings. The golden set is still marked `pending maintainer review`. Historical runs do not all use the same code revision or clean tracked tree.

**Latest saved run, 2026-10-15 — Artifact-observed:** On 16 answerable questions, vector and hybrid both have hit@1/3/5 `8/11/11`, MRR `0.5729167`; full-text has `1/1/2`, MRR `0.078125`, and is empty for 14/16. Guard counts are 16 true accepts, 0 false refusals, 4 true refusals, 4 false accepts. Per pass, V2 counts are 10 `correct_labeled_context`, 2 `correct_unlabeled_context`, 2 `retrieval_miss_abstained`, 2 `incomplete_or_wrong`, 4 `guard_true_refusal`, and 4 `model_abstained`. Reported calls: 40, with 0 HTTP 429s and 0 generation errors. Citation label-match summaries are 9/22 cited chunks in pass 1 and 9/31 in pass 2 ([latest report](../../evaluation/results/runs/20261015T151657Z-c203e0e/report.json)). These are diagnostic measurements on this small, pending-review set, not a general benchmark.

**Interpretation and limitations:** Vector and hybrid metrics tie in these reports; this does not show a retrieval gain from fusion. Legacy `outcome` counts are not comparable to V2 because legacy labels generated responses to unanswerable questions as “falsely answered,” including model abstentions. Model outcomes vary across passes/runs. The saved reports omit explicit generation parameters/provider version. Per-question pass records preserve fused hybrid results, not standalone vector and full-text rankings, limiting exact retrieval replay. `outcome_changes` uses the legacy field, and `compare_reports` question-level flips inspect pass 1 only ([runner comparison generation](../../evaluation/runner.py#L850), [compare code](../../evaluation/compare.py#L18)). Config fingerprints have no explicit schema version.

**Reproduction status:** The report includes useful provenance, but full reproduction from saved artifacts alone is **not established**: standalone per-question retrieval lists, provider-version/config details, and a checked-in materialized snapshot are absent. Evaluation tests and historical run outputs are documented in [Phase 8](../phases/08-evaluation.md) and [Phase 8b](../phases/08b-evaluation-improvements.md); tests were not run while updating this document. Run folders and caches are ignored locally, so they may not be available in a public checkout.

## 12. Configuration, Deployment and External Dependencies

- **Configuration — Source-verified:** `app/config.py` uses Pydantic Settings with `.env` and environment variables for app environment, database URL, Gemini key, and API protection secret ([Settings](../../app/config.py#L1)). Do not put secret values in this document. Generation and embedding functions read `GEMINI_API_KEY` from the process environment.
- **Database/deployment — Source-verified:** Compose defines PostgreSQL `pgvector/pgvector:pg17` and an app service on port 8000, with a DB health dependency ([compose](../../docker-compose.yml#L1)). The Dockerfile copies `app/`, `scripts/`, `alembic.ini`, and `migrations/` ([Dockerfile](../../docker/Dockerfile#L1)). No migration was run as part of this documentation task.
- **Launch — Source-verified:** `scripts/serve.py` starts Uvicorn and configures a selector event loop on Windows; `app/main.py` also sets the Windows selector policy before app import ([launcher](../../scripts/serve.py#L1), [app entry](../../app/main.py#L1)).
- **Dependencies — Source-verified:** FastAPI, Pydantic Settings, Uvicorn, SQLAlchemy async, psycopg, pgvector, Alembic, LangGraph, and MCP are runtime dependencies ([dependency list](../../pyproject.toml#L1)). Gemini access uses standard-library `urllib`; evaluation uses standard-library JSON/hash/process functions and existing application packages.
- **API protection — Source-verified:** Shared-secret header plus per-process IP limiter; source comments explicitly state this is not production-grade authentication and limiter state is not shared across workers ([security module](../../app/api_security.py#L1)).
- **Documentation drift:** `docs/notes/02-deferred-optimizations.md` still says the Docker image omits `scripts/`, while the current Dockerfile copies it ([note](../notes/02-deferred-optimizations.md#L130), [Dockerfile](../../docker/Dockerfile#L12)).

## 13. Known Limitations and Failure Modes

- Ingestion accepts Python files only; fixed line windows can split semantic units. No AST-aware or document-format parsing is implemented.
- Re-ingestion replaces all chunks for a repository and can change chunk IDs; there is no incremental update or chunk uniqueness key.
- Embedding is synchronous and per-chunk, has a fixed delay but no internal retry, and can leave null vectors after failures.
- FTS query-time parsing may return no rows for natural-language questions; there is no FTS index in the declared migration.
- Hybrid RRF treats list ranks equally and has no explicit deterministic tie-break. The evidence guard does not require relevant source content; its vector-distance cutoff is provisional and does not establish semantic relevance.
- The MCP server still exposes a local literal grep tool, but the investigation graph does not invoke it. Checklist item 25 addresses whether the MCP module should remain.
- Gemini calls are synchronous in async flow. Provider-default generation settings are not pinned in the report; retry latency is not the same as total request duration.
- Citation matching is a reference detector, not claim verification. Confidence is a categorical model label subject only to a one-way threshold downgrade.
- API limiter is in-memory and per worker; no user accounts, key rotation, or per-user quota. API has no ingestion/embedding endpoint or background queue.
- README overstates both grounding protection and raw-response persistence ([README](../../README.md#L169), [persistence](../../app/investigation/persistence.py#L25)).
- Phase 8b status text is inconsistent: the header and reviewer blocks indicate approval while its evidence bundle contains “awaiting reviewer” wording ([Phase 8b](../phases/08b-evaluation-improvements.md#L3)).
- No live database, deployed-container, provider, or current remote behavior was verified for this document. Automated tests were not run.

## 14. Source-Code Reference Index

| Area | Primary source references |
|---|---|
| Configuration and session | [app/config.py](../../app/config.py), [app/db/session.py](../../app/db/session.py) |
| Schema and migration | [app/db/models/repository.py](../../app/db/models/repository.py), [chunk.py](../../app/db/models/chunk.py), [investigation.py](../../app/db/models/investigation.py), [audit.py](../../app/db/models/audit.py), [initial migration](../../migrations/versions/20260819_0001_initial_schema.py) |
| Ingestion and embeddings | [scripts/ingest_repo.py](../../scripts/ingest_repo.py), [scripts/embed_chunks.py](../../scripts/embed_chunks.py) |
| Retrieval | [vector_search.py](../../app/retrieval/vector_search.py), [fulltext_search.py](../../app/retrieval/fulltext_search.py), [hybrid_search.py](../../app/retrieval/hybrid_search.py) |
| Investigation and grounding | [graph.py](../../app/investigation/graph.py), [guard.py](../../app/investigation/guard.py), [prompt.py](../../app/investigation/prompt.py), [generation.py](../../app/investigation/generation.py), [parsing.py](../../app/investigation/parsing.py), [confidence.py](../../app/investigation/confidence.py), [mcp_server.py](../../app/investigation/mcp_server.py), [persistence.py](../../app/investigation/persistence.py) |
| Entry points and security | [scripts/investigate.py](../../scripts/investigate.py), [scripts/search_repo.py](../../scripts/search_repo.py), [scripts/serve.py](../../scripts/serve.py), [app/api.py](../../app/api.py), [app/api_security.py](../../app/api_security.py), [app/main.py](../../app/main.py) |
| Evaluation | [golden_set.json](../../evaluation/golden_set.json), [chunk_experiments.py](../../evaluation/chunk_experiments.py), [runner.py](../../evaluation/runner.py), [metrics.py](../../evaluation/metrics.py), [golden.py](../../evaluation/golden.py), [corpus.py](../../evaluation/corpus.py), [compare.py](../../evaluation/compare.py), [run_eval.py](../../scripts/run_eval.py), [compare_runs.py](../../scripts/compare_runs.py) |
| Tests inspected | [unit tests](../../tests/unit/), [integration tests](../../tests/integration/) |
| Project configuration/deployment | [pyproject.toml](../../pyproject.toml), [docker-compose.yml](../../docker-compose.yml), [Dockerfile](../../docker/Dockerfile), [alembic.ini](../../alembic.ini) |

### GitHub Source Permalinks

These links use the inspected commit SHA. They point to source files, not local evaluation artifacts. GitHub can resolve them only if the commit is available in the remote repository.

- [Repository ingestion](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/scripts/ingest_repo.py) and [embedding](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/scripts/embed_chunks.py)
- [Vector retrieval](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/app/retrieval/vector_search.py), [full-text retrieval](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/app/retrieval/fulltext_search.py), and [RRF fusion](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/app/retrieval/hybrid_search.py)
- [Investigation graph](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/app/investigation/graph.py), [evidence guard](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/app/investigation/guard.py), and [prompt](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/app/investigation/prompt.py)
- [Gemini generation](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/app/investigation/generation.py), [parsing and citations](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/app/investigation/parsing.py), [confidence](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/app/investigation/confidence.py), and [persistence](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/app/investigation/persistence.py)
- [HTTP API](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/app/api.py), [evaluation runner](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/evaluation/runner.py), and [evaluation metrics](https://github.com/iamswayam/incidentweave/blob/e104005848bdee38d603d3703f93a5ff9bce79e1/evaluation/metrics.py)

## 15. Architecture Change History

This history is assembled from the checked-in phase logs and current repository evidence. Entries without a commit are phase-level provenance, not claims about exact commit boundaries.

| Date / revision | Change represented in current architecture | Evidence and rationale recorded |
|---|---|---|
| Phase 2; migration `20260819_0001` | Added PostgreSQL entities for repositories, chunks, investigations, and audit records, including pgvector storage. | [Initial migration](../../migrations/versions/20260819_0001_initial_schema.py); phase log [database persistence](../phases/02-database-persistence.md). |
| Phase 3 | Added Python repository traversal, 60/10 line chunking, and replace-on-reingest behavior. | [Ingest implementation](../../scripts/ingest_repo.py); [Phase 3 log](../phases/03-ingestion-chunking.md). |
| Phase 4 | Added Gemini 768-dimensional embeddings, vector search, PostgreSQL FTS, and RRF fusion. | [Embedding](../../scripts/embed_chunks.py), [retrieval](../../app/retrieval/), [Phase 4 log](../phases/04-embeddings-retrieval.md). The phase log records per-chunk processing and no automatic retries. |
| Phases 5-7 | Added investigation graph, score guard/confidence calibration, controlled tools/MCP, and audit persistence. | [Graph](../../app/investigation/graph.py), [Phase 5-7 logs](../phases/05-investigation-engine.md). Phase logs describe intent and verification at their time; current source is authoritative for behavior today. |
| Phase 8 | Added a 24-question evaluation against a pinned 40-file/70-chunk corpus and recorded diagnostic retrieval/guard outcomes. | [Phase 8 log](../phases/08-evaluation.md), [golden set](../../evaluation/golden_set.json). Its own scope states results are small-sample diagnostics, not a general benchmark. |
| Phase 8b; commits recorded in work log include `fea9d8d`, `2a6c658`, `b51894a`, `4b688a1` | Added generation traces, additive V2 outcomes, run metadata/registry/comparison, and report diagnostics while preserving legacy labels and evaluation `persist=False`. | [Phase 8b log](../phases/08b-evaluation-improvements.md). The document contains conflicting status wording noted above. |
| Phase 9 | Added synchronous FastAPI investigation/read endpoints, shared-secret protection, in-memory rate limit, and Docker runtime files. Ingestion and embedding remain CLI-only; job queue was explicitly deferred. | [API](../../app/api.py), [security](../../app/api_security.py), [Dockerfile](../../docker/Dockerfile), [Phase 9 log](../phases/09-production-api.md). |
| 2026-10-17; uncommitted evaluation harness on `experiment/chunking-evaluation-harness` | Added evaluation-only baseline 60/10 and experimental 100/20 strategies, separate allowlisted repositories, strategy-aware metadata/run IDs, evaluation-owned insertion for new corpora, exact-match reuse, fail-closed stale-data handling, and a selected-repository inventory guard. | D3/D4/D6 were approved in [the chunking experiment log](../chunking-experiment/01-experiment-log.md). This documents harness behavior only; the experiment has not been run or authorized. Production ingestion and golden-set data are unchanged. |
| 2026-10-17; source revision `e104005848bdee38d603d3703f93a5ff9bce79e1` | Created this implementation reference. No application, schema, dependency, test, or deployment behavior changed. | Current source and locally available evaluation artifacts inspected; runtime checks and test execution were not performed for the documentation update. |

### Maintenance Rule

When an approved change affects application code, component responsibilities, execution flow, data models, APIs, configuration, dependencies, tests, evaluation, or deployment, update the relevant architecture sections in the same change. Update affected diagrams and source references, and add a dated change-history entry with the commit or pull request when available. Do not rewrite unrelated sections or change implementation merely to match this document. If a proposed change conflicts with a documented architectural decision, report the conflict and obtain an explicit decision before implementation. Distinguish test coverage from tests actually executed, and record runtime verification only when it was actually performed.