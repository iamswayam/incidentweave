# IncidentWeave: Prioritized Fix Checklist (merged from the Claude and Codex audits)

*Written 2026-10-21 by Claude (Sonnet 5.5). Source reports: `docs/audit_report_claude.md` and `docs/audit_report_codex.md`. Code reference: `main` @ `e98da82`; experiment branch `experiment/chunking-evaluation-harness` @ `12edf8e`.*

**How to use this file**
1. Work **top to bottom**. The order is: cheap safety and honesty fixes → audit trail → answer contract → measurement foundation → retrieval/chunking gains → scale and breadth.
2. One item at a time. Each item has a **Done when** test. Do not start the next until the test passes.
3. After any change that affects retrieval or the guard, re-run the evaluation and record the result.
4. Effort: **S** = under half a day, **M** = 1–3 days, **L** = a week or more.
5. Item 1 is implemented; remaining entries are recommendations to be verified (Codex is asked to do that in section 6).

**Evidence tags** (same as in my audit): **[SRC]** read from code, **[EXEC]** I ran it, **[ART]** author-reported in repo docs/artifacts, **[INF]** my inference.

---

## 1. Fix-order checklist (summary)

| # | ✔ | Fix | Priority | Effort | Raised by |
|---|---|---|---|---|---|
| 1 | ☑ | Cap `limit`, query length and prompt size | High | S | Both |
| 2 | ☐ | Stop the API's grep fallback searching the wrong repository | High | S | Claude (Codex partial) |
| 3 | ☐ | Fix the evidence guard (per-chunk check, drop the vacuous RRF gate) | High | S | Both |
| 4 | ☐ | Make abstention consistent (low confidence, no citations; literal-evidence rule) | High | S | Claude |
| 5 | ☐ | Hardening bundle: API key in header, grep timeout, Docker non-root and env, healthcheck | Medium | S | Both |
| 6 | ☐ | Make README/docs claims match the code (RRF, audit, raw response, test counts) | Medium | S | Both |
| 7 | ☐ | Persist every outcome (answered, refused, abstained, error) | High | S–M | Both |
| 8 | ☐ | Store a replayable audit (raw output, raw confidence, prompt, versions, thresholds) | High | M | Both |
| 9 | ☐ | Source versioning and upsert ingestion (commit SHA, content hashes, stable chunk IDs) | High | M | Both |
| 10 | ☐ | Async, batched provider client with deadlines and retries | High | M | Both |
| 11 | ☐ | Structured output and server-side citation validation | High | M | Both (Codex stronger) |
| 12 | ☐ | Prompt-injection and secret-leak controls | Medium | M | Codex (Claude minor) |
| 13 | ☐ | **Evaluation foundation** (do before any retrieval tuning) | High | M | Both |
| 14 | ☐ | Cheap retrieval ablations: embedding task type, test-file policy, full-text fix | High | S–M each | Both |
| 15 | ☐ | Chunking upgrade: function-aware chunks, enriched embedding text, parent expansion | High | M | New (data-driven, see Part A) |
| 16 | ☐ | Held-out evaluation set: second repository, 60+ independent questions | High | M–L | Both |
| 17 | ☐ | LLM judge, claim-level citation scoring, larger abstention set | Medium | M | Both |
| 18 | ☐ | Tracing, cost and latency telemetry | Medium | M | Both |
| 19 | ☐ | Rename or truly calibrate "confidence" | Medium | S–M | Codex (Claude data) |
| 20 | ☐ | Multi-artifact ingestion (docs, configs, logs) with metadata | Medium | L | Both |
| 21 | ☐ | Reranker experiment | Low | M | Both |
| 22 | ☐ | Incident-replay evaluation and hypothesis loop (flagship feature) | Medium | L | Claude |
| 23 | ☐ | Security and operability layer (auth scopes, distributed limits, load test, threat model) | Medium | L | Codex |
| 24 | ☐ | Provider adapter and model comparison, version pinning | Low | M | Codex |
| 25 | ☐ | Decide on MCP and LangGraph; deploy a hosted demo | Low | M | Both |

---

## 2. Item details (Why / Fix / Done when)

### Phase 1: quick safety and honesty fixes

**1. Cap `limit`, query length and prompt size.**
- *Why:* `limit: int = Field(default=5, gt=0)` has no maximum, `query` has no max length, and `build_grounded_prompt` inserts every chunk with no ceiling [SRC: `app/api.py`, `app/investigation/prompt.py`]. An authenticated caller can create outsized cost and latency.
- *Fix:* `limit` `ge=1, le=20`; `query` `max_length=2000`; in the prompt builder enforce a total evidence budget (for example 24,000 characters), drop the lowest-ranked chunks first, and record what was dropped in the audit.
- *Done when:* `limit=1000` and an oversized query return 422, and a test proves the prompt never exceeds the budget.
- **Status:** 2026-10-21; branch `fix/01-input-caps`; changed `app/investigation/limits.py`, `app/api.py`, `scripts/investigate.py`, `app/investigation/prompt.py`, `app/investigation/graph.py`, `tests/unit/test_api.py`, `tests/unit/test_prompt.py`, `tests/unit/test_investigation_graph.py`, `tests/unit/test_investigate_limits.py`, `docs/fix_checklist.md`; `ruff check .`: All checks passed!; `pytest tests/unit -q`: 84 passed in 45.42s; `pytest -q`: 87 passed in 44.83s.

**2. Stop the wrong-tree grep fallback.**
- *Why:* `POST /investigations` calls `investigate_repository(...)` without `repo_path`, so the default is IncidentWeave's own checkout (`REPO_ROOT`). For any other repository the literal fallback can return IncidentWeave source as evidence [SRC]. In the final evaluation run grep recovered 0 of 8 attempts [ART], so removing it loses nothing measured.
- *Fix:* add a nullable `source_path` to `Repository` (migration), set at ingest. The API passes it. If it is null, skip the grep fallback and refuse. Short-term option: pass `repo_path=None` and have the graph skip grep.
- *Done when:* a test with a repository other than IncidentWeave, and a query matching IncidentWeave's source, shows grep is not run or returns nothing.

**3. Fix the evidence guard.**
- *Why:* (a) `MIN_ACCEPTABLE_RRF_SCORE = 0.016` is below `1/61 = 0.016393`, so any rank-1 vector hit passes; I executed this [EXEC]. (b) The guard takes the best RRF and best vector distance from *different* chunks independently (`max` and `min` over all results), so no single chunk has to satisfy both [SRC; found by Codex]. Result: 4 of 8 unanswerable questions pass the guard [ART].
- *Fix:* decide sufficiency per chunk. Use RRF for ranking only. Example rule: the top chunk's own vector distance ≤ T, or it has a lexical match and distance ≤ T2. Pick T from the sweep as a provisional value and re-validate on the held-out set (item 16). Update the README sentence about "both an RRF threshold and a vector-distance threshold".
- *Done when:* unit tests show the guard accepts only if one chunk passes; the evaluation is re-run and false accepts are recorded; the README matches the code.

**4. Make abstention consistent.**
- *Why:* a response with `Diagnosis: INSUFFICIENT_EVIDENCE` and `Confidence: high` is stored as `high` [EXEC]. For literal-grep evidence, calibration retains `high` with the note "retrieval scores clear both calibration margins", which is false because there are no scores [EXEC].
- *Fix:* after parsing, if the diagnosis equals `INSUFFICIENT_EVIDENCE` then confidence = `low` and cited chunks = `[]`. For literal-only evidence cap confidence at `medium` with an honest note.
- *Done when:* parser and calibration tests cover both cases.

**5. Hardening bundle.**
- *Why:* the Gemini key is in the URL query string [SRC] (it can leak into logs); the grep subprocess call has no deadline [SRC; Codex]; the Dockerfile runs as root and Compose passes neither `GEMINI_API_KEY` nor `API_PROTECTION_SECRET`, so the container cannot generate or authenticate [SRC].
- *Fix:* send the key in the `x-goog-api-key` header (generation and embedding); wrap the MCP call in `asyncio.wait_for(..., 10)`; add `USER` (non-root) to the Dockerfile; pass env via `env_file`; add a healthcheck on `/health`.
- *Done when:* each is covered by a test or a `docker compose up` smoke check.

**6. Make docs match code.**
- *Why:* the README says retrieval must clear both thresholds (not true, item 3); "one Audit row per query" (not true for refusals); the raw model response is persisted (not true: only the parsed diagnosis is stored); the test count is stated as both 41 and 53, and `main` contains both phases [SRC].
- *Fix:* run `pytest -q` on the current `main`, then update the counts and rewrite each claim to say exactly what the code does.
- *Done when:* every README claim maps to a code location or a test.

### Phase 2: audit and provenance

**7. Persist every outcome.**
- *Why:* when the guard fails, `investigate_repository` returns before persistence, so there is no row, `investigation_id` is `None`, and refusals cannot be reviewed [SRC].
- *Fix:* add an `outcome` column (`answered`, `refused_guard`, `abstained_model`, `error`) via Alembic migration `0002`. Store a row for refusals with the evidence check and a retrieval summary. The API returns an ID for refusals.
- *Done when:* a refused POST returns an ID and `GET /investigations/{id}` returns the refusal reason.

**8. Store a replayable audit.**
- *Why:* only the parsed diagnosis is stored. Missing: raw model text, raw confidence, prompt, model and embedding versions, generation settings, thresholds [SRC].
- *Fix:* add `raw_response`, `raw_confidence`, `prompt_text` (or `prompt_sha256` plus `prompt_template_version`), `embedding_model`, `generation_config` (JSONB), `thresholds` (JSONB), and a content hash per retrieved chunk. Note the prompt contains source code, so restrict who can read it.
- *Done when:* an old investigation can be explained from its stored data alone.

**9. Source versioning and upsert ingestion.**
- *Why:* `ingest_repository` deletes all chunks and reinserts them, so chunk IDs change and embeddings are lost. `Audit.retrieved_chunk_ids` has no foreign key and no content snapshot. No commit SHA is stored [SRC].
- *Fix:* an `ingest_runs` table (`repository_id`, `source_path`, `git_remote`, `commit_sha`, `dirty`, `started_at`, `chunker_version`, `embedding_model`); `chunks.ingest_run_id` and `chunks.content_hash`; upsert by (repository, file, range, content hash) so unchanged chunks keep their ID and embedding; audit rows reference the `ingest_run_id`.
- *Done when:* re-ingesting an unchanged repository leaves chunk IDs and embeddings intact, and an audit row shows which commit it described.

### Phase 3: answer contract

**10. Async, batched provider client.**
- *Why:* `embed_text` and `generate_investigation` use blocking `urllib` calls on async paths (up to 60 s per attempt plus `time.sleep` backoff). Embedding is one chunk per request with a 1.5 s sleep, about 4.2 hours of sleep for 10,000 chunks [SRC]. A batch embedding endpoint exists [per Google docs].
- *Fix:* use `httpx.AsyncClient` or the `google-genai` async client; batch embeddings with a bounded-concurrency semaphore; retries with jitter on 429 and 5xx; one end-to-end deadline per request.
- *Done when:* a test with a slow fake provider shows other requests stay responsive, and 500 chunks embed in minutes.

**11. Structured output and server-side citation validation.**
- *Why:* citations are string mentions. A response calling `app/config.py` "unrelated" still cites it, and a nonexistent line range still cites every chunk from that file [EXEC]. In the final run only 9 of 22 and 9 of 31 cited chunks matched a labeled-relevant substring [ART].
- *Fix:* use the provider's JSON-schema output: `{outcome, diagnosis, claims:[{text, evidence:[{chunk_id, quote}]}], uncertainty_note}`. The server checks that every `chunk_id` was retrieved and every `quote` is a substring of that chunk (whitespace-normalized). Invalid claims are dropped or flagged. `cited_chunk_ids` is derived from validated claims. If no claim is valid, refuse. This replaces the regex parser.
- *Done when:* tests cover a hallucinated chunk ID, a quote not in the chunk, and a valid case; the evaluation reports a citation-validity rate.

**12. Prompt-injection and secret controls.**
- *Why:* repository text is concatenated into the prompt with no trust boundary, and code sent to an external model may contain secrets [SRC; Codex].
- *Fix:* wrap each chunk in explicit tags (`<evidence id=… path=…>…</evidence>`) and instruct the model that evidence is untrusted data. Scan for secrets at ingestion (regex for keys and tokens) and redact or skip with a warning. Document the data policy.
- *Done when:* a fixture file containing "ignore previous instructions" does not change the diagnosis, and a fixture secret never reaches the prompt.

### Phase 4: measurement foundation, then retrieval gains

**13. Evaluation foundation (before tuning anything).** Why and design are in Part B. Minimum set:
- Chunk-agnostic labels: the evidence is a file plus line range, and a retrieved chunk is a hit if it overlaps or contains it.
- A retrieval-only mode (no LLM call) that uses cached query and chunk embeddings committed as a small fixture, so CI can run it offline.
- Generation settings recorded and `temperature=0`.
- Confidence intervals and a paired comparison in every report.
- *Done when:* a CI job runs the retrieval evaluation offline and fails if Hit@5 or MRR drops beyond a stored tolerance.

**14. Cheap retrieval ablations (each is one row in an ablation table).**
- *Why:* full-text returned nothing for 14 of 16 answerable questions [ART] because `websearch_to_tsquery` ANDs all words [PostgreSQL docs]; no `task_type` is sent to the embedding API although `RETRIEVAL_DOCUMENT` and `CODE_RETRIEVAL_QUERY` exist [Google docs]; 44% of top-5 results come from `tests/` [EXEC on the committed `baseline.json`].
- *Fix, as three separate experiments:*
  - (a) Add `task_type` (documents `RETRIEVAL_DOCUMENT`, queries `CODE_RETRIEVAL_QUERY`) and re-embed.
  - (b) Tag tests `document_type="test"`, then compare keep / downweight / exclude.
  - (c) Build an OR query from extracted identifiers and keywords, split `snake_case` and `camelCase` into extra searchable text, and add a generated `tsvector` column with a GIN index.
- *Done when:* a committed ablation table with confidence intervals; keep only changes that help without hurting.

**15. Chunking upgrade.** See Part A. *Done when:* the four-way chunker comparison runs on the item 13 metrics and the winner is chosen by a rule fixed in advance.

### Phase 5: scale and breadth

**16. Held-out evaluation set.**
- *Fix:* add a second repository (a small open-source Python service; your other repository only once non-Python ingestion exists) and at least 60 questions written independently of the system's own retrieval output. Include multi-file, config, error-message and stack-trace style questions. Split into a dev set and a frozen test set. Record a human review before the label status changes from "pending maintainer review".
- *Done when:* the frozen test set is used only for final reporting.

**17. LLM judge and a larger abstention set.**
- *Fix:* judge prompts for faithfulness (is each claim supported by its quote?), correctness against a reference answer, and completeness against a required-facts list. Prefer a different model from the generator. Validate the judge on at least 30 human-labeled answers and report agreement. Keep the keyword screen as a cheap smoke test. Grow unanswerable questions to at least 20 (far, near-miss, false-premise).
- *Done when:* the report shows judge agreement with humans.

**18. Tracing, cost, latency.**
- *Fix:* OpenTelemetry spans per graph node, tokens and estimated cost per request, p50/p95 per stage; self-hosted Langfuse or Grafana.
- *Done when:* one request shows every stage with timings and cost.

**19. "Confidence".**
- *Why:* in the committed baseline the model said `high` on 15 of 16 answers, and calibration moved 13 to `medium` [EXEC]. It has not been checked against correctness.
- *Fix:* rename the API field to `evidence_score` and `model_self_rating`, or, with at least 100 labeled answers, publish a reliability table (bucket → accuracy).
- *Done when:* wording matches the evidence.

**20. Multi-artifact ingestion.**
- *Fix:* Markdown by heading; YAML/TOML/JSON by top-level key; Dockerfile and CI files whole; logs by time window or request ID with stack traces kept intact. Fill `document_type`, `service`, `environment`, `timestamp`, `incident_id` (the columns already exist but are unused) and filter on them.
- *Done when:* questions over a README, a runbook and a config are answered with valid citations.

**21. Reranker experiment.** Re-rank the top 20 into the top 5. Keep it only if held-out Hit@5 or nDCG improves beyond the confidence interval at acceptable latency and cost.

**22. Incident-replay evaluation and hypothesis loop.**
- *Why:* this is the biggest gap versus the AI-SRE product category [market research in my report].
- *Fix:* a small containerized sample service with injected faults; capture its logs, alerts and deploy diff; 10–20 labeled incidents with root cause and evidence; the system proposes ranked hypotheses, tests each with read-only queries, and may end "inconclusive"; score root-cause accuracy, evidence validity, time and cost.
- *Done when:* a report across all incidents exists.

**23. Security and operability.**
- *Fix:* per-user API keys (hashed) with scopes; distributed rate limiting; a per-request cost budget; structured logs with request IDs; a load test (20 concurrent requests); a threat-model document (prompt injection, data exfiltration, secrets, tenant isolation); CI type checking, `pip-audit` and secret scanning.
- *Done when:* the threat model and load-test report are committed.

**24. Provider adapter and model comparison.** Add an `LLMClient` interface, pin model versions in config and audit, and run the harness on `gemini-3.5-flash-lite`, `gemini-3.8-flash` and one other provider.

**25. MCP, LangGraph, deployment.** Either remove the per-call stdio MCP grep (use in-process exact search) or expose IncidentWeave as a read-only MCP server. Keep LangGraph only if the hypothesis loop genuinely needs branching or checkpoints. Deploy a hosted demo.

---

## 3. Part A: Can the chunking strategy be better? **Yes.**

**What chunking is (plain language).** The system cannot give the whole repository to the model, so it cuts files into pieces ("chunks"), turns each piece into a vector of numbers (an "embedding") that captures its meaning, and later finds the pieces whose vectors are closest to the question's vector. If a chunk is too big, its vector blends many topics and the prompt gets expensive. If it is too small or cut in the wrong place, the model sees a fragment, such as half a function without its start.

**What the project does now** [SRC: `scripts/ingest_repo.py`]: every Python file is cut into fixed windows of 60 lines with 10 lines of overlap. The cut ignores code structure. `function_name`, `class_name` and `symbol` are left empty.

**What the data says** (my analysis [EXEC] on the pinned snapshot used by the evaluation; script in the appendix):

| Measure | Result |
|---|---|
| Chunks at 60/10 and 100/20 | 70 and 52. These match the repo's own report, so my reproduction is faithful. |
| Median file length | 50.5 lines |
| Non-test function length | median 21.5, 90th percentile 60, max 177 lines |
| Functions/methods cut across chunk boundaries at 60/10 | **16 of 48 (33%)** non-test |
| Same at 100/20 | **5 of 48 (10%)** non-test |
| Test files in the top 5 results | 44% (35 of 80), 15 of 16 answerable questions [EXEC on `baseline.json`] |

**What this means.**
- The 100/20 gain (Hit@5 11/16 → 15/16 [ART]) has a concrete explanation: far fewer functions are cut in half. This is stronger evidence than the sample size alone suggests.
- It also says the real problem is **cutting without regard to structure**, so bigger windows are a blunt fix. A function-aware chunker should help further.
- I have not measured the retrieval effect of function-aware chunking. That needs embeddings and a model, which I could not run [INF].
- Test files add noise to the top results regardless of chunk size.

**Options compared**

| Strategy | How it works | Good | Bad | Verdict |
|---|---|---|---|---|
| Fixed windows (current) | N lines, overlap | Simple | Cuts functions; ignores structure | Baseline |
| Bigger windows (100/20) | Fewer, larger pieces | Fewer cut functions; fewer chunks | +40% tokens; blends topics; near whole-file on small files | Interim only |
| **Function-aware (`ast`)** | One chunk per function/class; split very long functions | Matches how people ask questions; fills the empty metadata columns; stdlib only | Needs fallbacks (syntax errors, non-Python) | **Recommended** |
| **Function-aware + header in embedding text** | Prepend path, class, function name and docstring to the text that is embedded | Questions that name a file or function match better | Slightly more code | **Recommended with the above** |
| **Parent-child ("retrieve small, answer big")** | Search small chunks, expand to the enclosing class or neighbours before prompting | Precise search, full context for the answer | Needs a token budget | **Recommended** |
| LLM or semantic chunking | A model decides the cuts | Flexible | Slow, costly, non-deterministic | Not now |
| Non-code (Markdown, config, logs) | Headings, keys, time windows/request IDs with stack traces whole | Needed for real incidents | New parsers | Item 20 |

**Recommended design**
1. Python: one chunk per top-level function or class; methods separately if a class is longer than about 80 lines; merge tiny neighbours (imports, constants) into a "module header" chunk; split functions longer than about 100 lines at blank-line boundaries with a 10-line overlap. Fill `symbol`, `function_name`, `class_name` and the line range.
2. Embed `File: … / Symbol: … / Docstring: … / <code>` but keep `content` raw for display and citations.
3. Tag tests with `document_type="test"` and decide the policy (keep, downweight, exclude) by ablation.
4. Record `chunker_version` in `ingest_runs` (item 9) so audits stay reproducible.
5. Decide by experiment: four chunkers × the test-file policy, scored with the item 13 metrics, with the decision rule written down before running. A quick throwaway prototype of mine produced 88 chunks with median 27 lines (max 177, a very long function). It is not in the appendix; treat the numbers as indicative.

**Caveats.** The corpus is small (40 files; the top 5 of 70 chunks is 7% of everything), so Hit@5 is easy here and will drop on real repositories. Do not treat conclusions as general.

---

## 4. Part B: Can the evaluation stage be better? **Yes.**

**What evaluation means for a RAG system (plain language).** There are two separate things to test. **Retrieval:** did the search put the right evidence in front of the model? **Generation:** given that evidence, was the answer correct, complete and supported? Test them separately, otherwise you cannot tell which part broke. Add two more: **citations** (do they point at real support?) and **abstention** (does it refuse when it should?).

**Glossary**

| Term | Meaning |
|---|---|
| Hit@k / Recall@k | Share of questions where the right evidence is in the top k results |
| MRR | Average of 1/rank of the first right result; rewards putting it first |
| nDCG@k | Like MRR but handles several relevant results and graded relevance |
| Context precision | Share of the top k results that are actually relevant (catches noise such as test files) |
| Faithfulness | Is every claim in the answer supported by the cited evidence? |
| Citation precision/recall | Of the citations given, how many truly support the claim; of the needed support, how much was cited |
| Abstention precision/recall | When it refuses, was it right to; when it should refuse, did it |
| Confidence interval | The range the true value plausibly lies in given the sample size |
| Ablation | Change one thing at a time and measure |
| Held-out set | Questions never used to tune anything |

**What is good already** [ART/SRC]: pinned corpus, run metadata (hashes, dirty flag), a validator that stops paraphrased questions leaking source identifiers, near/far unanswerable categories, and a distance-cutoff sweep.

**Problems, ranked**
1. **The sample is too small to settle anything.** 16 answerable questions. Wilson 95% intervals [EXEC]: Hit@5 60/10 is 11/16 [44%, 86%]; 100/20 is 15/16 [72%, 99%]. They overlap. Guard false accepts are 4/8 [22%, 78%]. Answer screen correct is 12/16 [51%, 90%]. A paired sign test on the 4-wins-0-losses Hit@5 gain gives p≈0.125.
2. **Self-referential, author-drafted, unreviewed.** The system is judged on its own source, the questions were drafted from the indexed content, and the status is "pending maintainer review" [ART].
3. **Labels depend on chunk text** (file + substring). I checked whether this favors big chunks: each label matches exactly one chunk at every size (two at 60/10 for one question) [EXEC]. So this bias is small here. The real limits are that substring labels cannot say "this answer needs two pieces of evidence" and do not penalize noisy results.
4. **Answer scoring is keyword groups.** It can accept a wrong answer or reject a correct paraphrase. `direct-05` shows an answer that omitted the required value yet ranked better [ART].
5. **Non-determinism and weak replication.** Generation uses "provider default" settings. Retrieval is deterministic, so a second pass adds no retrieval information [ART/INF].
6. **Not usable as a regression gate.** The harness calls a live provider; CI has no offline retrieval check [SRC].
7. **Confidence is never checked against correctness** [SRC: no such metric in `evaluation/metrics.py`].
8. **Process weight.** Docs are about 4,450 lines and the experiment comparator is 761 lines for a two-arm comparison [EXEC]. Simplify once the basics work.

**Recommended design: three layers**

| Layer | Runs | What it measures | Cost |
|---|---|---|---|
| 1. Retrieval | Every pull request (offline, cached embeddings) | Hit@k, MRR, nDCG@10, context precision@5, by question type and file type | Free |
| 2. Generation | Nightly or manual | Faithfulness, correctness, completeness (LLM judge validated on human labels), claim-level citation precision/recall, at `temperature=0`, at least 3 runs, with intervals | Tokens |
| 3. Abstention and safety | Nightly or manual | At least 20 unanswerable (far, near-miss, false-premise), injection and secret fixtures; refusal precision/recall | Tokens |
| 4. Incident replay (later) | Manual | Root-cause accuracy over labeled incidents (item 22) | Tokens |

**Dataset:** 60 or more questions across two or more repositories, split into dev and a frozen test set; types: direct, paraphrased, multi-file, config, error-message/stack-trace, unanswerable; written independently and human-reviewed; version-controlled with a changelog.

**Experiment discipline:** write the hypothesis and decision rule first; change one thing at a time; report the effect with an interval and a paired test; never tune thresholds on the frozen test set.

**Scorecard to report each run**

| Metric | Value | 95% interval | Change vs baseline |
|---|---|---|---|
| Hit@5, MRR, nDCG@10, context precision@5 | | | |
| Faithfulness, correctness, completeness | | | |
| Citation precision / recall | | | |
| Abstention precision / recall | | | |
| Median and p95 latency, tokens, cost per correct answer | | | |

**A practical learning path (tied to the checklist)**
1. Implement nDCG and context precision in `metrics.py` with unit tests (item 13).
2. Write the function-aware chunker and print how the chunk boundaries change for two files (item 15).
3. Run the ablation and read the table (item 14).
4. Write the judge prompt, label 30 answers yourself, compare (item 17).
5. Learn just enough statistics to read an interval and a paired test.

---

## 5. Corrections to my own earlier audit

- I said label matching "favors larger chunks". The label-reachability check shows the count effect is small here (Part B problem 3). The better explanation for 100/20's gain is fewer cut functions (33% → 10%).
- I said AST-aware chunking was a "later" item. Both audits said later. The function-splitting data justifies moving it earlier (item 15), but only after the evaluation foundation (item 13) so the gain can be measured.

---

## 6. Prompt to hand to Codex

Place these three files in the repository first: `docs/audit_report_claude.md` (my audit), `docs/audit_report_codex.md` (your earlier audit), and `docs/fix_checklist.md` (this file). Then give Codex the block below.

````text
You are the independent reviewer of a prioritized fix checklist for the IncidentWeave repository.

Inputs (read all three fully before answering):
- docs/audit_report_claude.md  : Claude's engineering + market audit
- docs/audit_report_codex.md   : your own earlier audit
- docs/fix_checklist.md        : Claude's merged, ordered checklist (25 items), plus Part A (chunking), Part B (evaluation) and an appendix script
If a file is not found under docs/, search the repo for the name without the extension; if still missing, stop and tell me.

Ground rules:
- Treat every claim in the checklist as a hypothesis. Verify it against the code. If Claude misread something, say so plainly.
- State which branch/commit you inspected (main e98da82 vs experiment/chunking-evaluation-harness 12edf8e) and use the same one throughout. Your report counted 64 test functions; Claude counted 51 on main and 64 on the experiment branch, so confirm which tree you used.
- Do NOT modify product code. You may run read-only commands, the test suite, and the appendix script.
- Label evidence: Verified (code/official docs), Executed (you ran it), Artifact-observed, Inferred, Unverified. Cite file and line for code claims. Say what you could not run.
- Be concrete and concise. No generic advice.

Tasks:
1. Item-by-item review of checklist items 1-25. For each: verify the premise in code; give AGREE / AGREE-WITH-CHANGES / DISAGREE; correct priority or effort if wrong; flag ordering or dependency problems and regression risks; strengthen weak "Done when" tests.
2. Missing items: list anything in your own audit that the checklist omits, and anything you now think is wrong or low value in the checklist.
3. Where your audit's recommendation is better than Claude's, say so and why (for example structured output, threat model, provenance). Where Claude's is better, say that too.
4. Independently verify Part A and Part B numbers by running the appendix script (functions cut at 60/10 vs 100/20, chunk counts 70/52, label reachability, Wilson intervals). Challenge the interpretation. In particular: (a) is function-aware chunking the right next chunking step, or is a different choice better for this repo? (b) are the three-layer evaluation design and the 60+ question target realistic for one developer? (c) any statistical or methodological errors?
5. Check the ordering principle: quick safety/honesty -> audit trail -> answer contract -> evaluation foundation -> retrieval/chunking gains -> scale/breadth. Propose a different order if you disagree, with reasons.
6. Check Claude's claims that you may dispute: guard severity (High vs your Critical), API grep fallback using IncidentWeave's own tree (api.py does not pass repo_path), refusals not persisted, raw response not persisted, no GIN/HNSW index, full-text empty for 14 of 16 questions because websearch_to_tsquery ANDs terms.

Output: write docs/fix_checklist_review_codex.md containing:
(a) one-paragraph verdict;
(b) a table: item # | verdict | corrections | extra tests;
(c) missing or removable items;
(d) ranked list of disagreements with Claude, each with evidence;
(e) your final recommended fix order as a list of item numbers;
(f) what you could not verify.
````

---

## Appendix: analysis script (stdlib only)

Run it on the pinned evaluation snapshot, **outside** the snapshot directory, with `python3 -I`. It reads files with `ast.parse` and never executes repository code.

```python
"""Stdlib-only chunking/evaluation analysis for IncidentWeave's pinned snapshot.

Usage (from any directory, NOT inside the untrusted snapshot):
    git -C <repo> archive 62d0e58593bb22d187ec7930274b0457afd3be74 | tar -x -C /tmp/snap
    rm -rf /tmp/snap/tests/fixtures
    git -C <repo> show origin/main:evaluation/golden_set.json > /tmp/golden.json
    python3 -I chunk_eval_analysis.py /tmp/snap /tmp/golden.json
"""
import ast
import json
import statistics
import sys
from math import sqrt
from pathlib import Path

ROOT, GOLDEN = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text())
IGNORE = {".git", ".kilo", ".pytest_cache", ".ruff_cache", ".venv", "__pycache__", "migrations"}
STRATEGIES = {"60/10": (60, 10), "100/20": (100, 20)}


def load_files():
    out = {}
    for p in sorted(ROOT.rglob("*.py")):
        rel = p.relative_to(ROOT)
        if not any(part in IGNORE for part in rel.parts):
            out[rel.as_posix()] = p.read_text(encoding="utf-8", errors="replace")
    return out


def windows(n, size, overlap):  # mirrors scripts/ingest_repo.py::chunk_lines
    step, prev = size - overlap, 0
    for s in range(0, n, step):
        e = min(s + size, n)
        if e > prev:
            yield s, e  # half-open, 0-based
            prev = e


files = load_files()
print(f"files={len(files)}  median file length={statistics.median(len(s.splitlines()) for s in files.values())} lines")

# 1) chunk counts (should equal the repo's reported 70 and 52) and function splitting
funcs = []
for name, src in files.items():
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.append((name, node.lineno, node.end_lineno))
for label, (size, ov) in STRATEGIES.items():
    n_chunks = sum(len(list(windows(len(s.splitlines()), size, ov))) for s in files.values())
    for scope, keep in (("non-test", lambda n: not n.startswith("tests/")), ("all", lambda n: True)):
        total = split = 0
        for name, s, e in funcs:
            if not keep(name):
                continue
            ws = list(windows(len(files[name].splitlines()), size, ov))
            total += 1
            split += not any(a + 1 <= s and e <= b for a, b in ws)
        print(f"[{label}] chunks={n_chunks}  {scope} functions/methods={total} split across chunks={split} ({split/total:.0%})")
lens = sorted(e - s + 1 for n, s, e in funcs if not n.startswith("tests/"))
print(f"non-test function length: median={statistics.median(lens)}  p90={lens[int(len(lens)*.9)]}  max={lens[-1]}")

# 2) label reachability: how many chunks match each question's file+substring label
chunks = {}
for label, (size, ov) in STRATEGIES.items():
    chunks[label] = [(n, "\n".join(s.splitlines()[a:b])) for n, s in files.items()
                     for a, b in windows(len(s.splitlines()), size, ov)]
chunks["whole-file"] = list(files.items())
print("\nlabeled chunks per answerable question (60/10, 100/20, whole-file):")
for q in GOLDEN["questions"]:
    if q["category"] in ("direct", "paraphrased"):
        row = [sum(1 for n, c in chunks[k] if any(l["file_path"] == n and l["substring"].casefold() in c.casefold()
                                                   for l in q["relevant"])) for k in ("60/10", "100/20", "whole-file")]
        print(f"  {q['id']:15s} {row}")


# 3) uncertainty on the headline numbers
def wilson(k, n, z=1.96):
    p, d = k / n, 1 + z * z / n
    c, m = p + z * z / (2 * n), z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - m) / d, (c + m) / d


print("\nWilson 95% intervals:")
for name, k, n in [("Hit@5 60/10", 11, 16), ("Hit@5 100/20", 15, 16),
                   ("guard false accepts on unanswerable", 4, 8), ("answer screen correct", 12, 16)]:
    lo, hi = wilson(k, n)
    print(f"  {name}: {k}/{n}  [{lo:.0%}, {hi:.0%}]")
```

**Expected output when I ran it** [EXEC]: 40 files, median 50.5 lines; 70 chunks at 60/10 and 52 at 100/20; non-test functions cut across chunks 16 of 48 (33%) at 60/10 and 5 of 48 (10%) at 100/20; non-test function length median 21.5, p90 60, max 177; one labeled chunk per question at every size except `paraphrased-05` at 60/10 (two); Wilson intervals as in Part B.
