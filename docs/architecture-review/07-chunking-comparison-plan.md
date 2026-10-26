# 07 Chunking comparison plan

## 1. Proposed plan (author: Claude)

Context: the evaluation harness now has three repositories (incidentweave, batch-processing-service, lifeos) with 24 questions each, explicit development / held-out / smoke splits, span labels that are independent of chunk boundaries, and per-repository offline fixtures. Held-out questions are frozen. Retrieval Hit@5 is near its ceiling on these small corpora (lifeos 16/16).
P1 Candidates fixed in advance: S0 current 60/10 line windows; S1 100/20 line windows; S2 function-aware chunks built with Python's ast module (one chunk per function or method; class header and docstring as their own chunk; module-level statements grouped; functions longer than a fixed limit split by line windows inside; tiny neighbouring chunks merged up to a minimum size; fallback to line windows if the file fails to parse); S3 = S2 plus an enriched embedding text (file path and symbol name prepended to the text that is embedded; the stored chunk text is unchanged so evidence-quote validation is unaffected).
P2 Parent expansion (adding a method's class header to the prompt context) is moved to a later item, because it changes prompt context, not retrieval ranking, and can only be judged with the answer-quality evaluation of item 17.
P3 Primary metric: pooled MRR on span labels over the development answerable questions of all three repositories (33 questions). Secondary: Hit@1, Hit@3, Hit@5.
P4 Cost metric: mean amount of text in the top-5 retrieved chunks, because larger chunks hit spans more easily.
P5 Selection rule, written before any run: a candidate qualifies only if (a) no repository loses more than one Hit@5 question versus S0, (b) pooled development MRR improves by at least 0.03 absolute over S0, and (c) mean top-5 text is at most 1.5 times S0's. The qualifying candidate with the highest MRR wins; ties go to the simpler strategy; if none qualifies, S0 stays (a valid outcome).
P6 A paired exact sign test on per-question rank changes is reported but does not gate.
P7 Held-out questions are run once, after the choice is frozen, for confirmation only (15 answerable held-out questions in total; only large effects are visible).
P8 Reported but not gated: chunk counts, chunk-size distribution, and the distance gap between answerable and unanswerable questions; the guard threshold (0.5) is re-checked afterwards in item 3b.
P9 Steps: 15a-1 code only (chunker interface, AST chunker, strategy registry made repository-independent, unit tests, no provider calls); 15a-2 the experiment (per-strategy fixtures built with embedding calls only, comparison, rule applied, result recorded); 15b adopt the winner in production ingestion (bump chunker version, re-ingest); parent expansion becomes item 15c after item 17.
P10 Tests stay indexed as today with no downweighting; that is item 14's job.

## 2. Codex review

### Review basis

The reviewed checkout has a three-entry, hash-validated manifest and explicit development/held-out/smoke assignments. Its committed baseline fixtures report 70 IncidentWeave chunks and support 24 cached question vectors; each manifest entry limits its compressed fixture to 1.5 MiB. This is source/artifact evidence only; no provider call or new experiment was run for this review.

| Item | Verdict | Review and exact amendment where needed |
|---|---|---|
| P1 | AMEND | Replace the S2/S3 definition with: “S2 uses a deterministic AST chunk specification with committed `max_function_lines`, `min_chunk_lines`, overlap, merge order, handling for decorated/async methods, class headers, module headers and parse failure. S3 uses the same stored chunks and boundaries as S2, but a separately versioned deterministic `embedding_text` formed from path and available structural names plus raw content.” The current registry has only `baseline` and `w100_o20`, and its strategy object embeds an IncidentWeave database name. |
| P2 | AGREE | Parent expansion changes answer context rather than retrieval ranking; defer it until item 17 can assess answer quality and citation faithfulness. |
| P3 | AMEND | Replace P3 with: “Primary metric: pooled, question-weighted span-label MRR over 33 development answerable questions. Report its per-question delta and every repository’s MRR and Hit@1/3/5, plus direct/paraphrased breakdowns; mark IncidentWeave as previously exposed.” Equal 11-question denominators make the pooled mean interpretable, but it must not hide a per-repository regression. |
| P4 | AMEND | Replace P4 with: “Cost metrics are mean and p95 unique raw source characters in the top five retrieved chunks, per repository and pooled, after de-duplicating overlapping line ranges. Report fixture compressed size and chunk count too.” Mean text alone can hide a high-tail context cost and overlap double-counts line windows. |
| P5 | AMEND | Replace P5 with: “Before embeddings, commit one comparison matrix, one run budget and the baseline/candidate artifact hashes. A candidate qualifies if no repository loses more than one development Hit@5 result, no repository loses more than 0.03 MRR, pooled development delta-MRR is at least 0.03, and its mean and p95 unique top-five source characters are each at most 1.5 times S0. Among qualifiers, select highest pooled MRR, then simpler strategy; otherwise retain S0. Report a paired delta-MRR interval and the full per-repository table; this is a practical selection rule, not a claim of statistical significance.” |
| P6 | AMEND | Replace P6 with: “Report a two-sided exact sign test on the sign of each non-zero per-question reciprocal-rank change, including wins, losses, ties and effective N. Also report a seeded paired-bootstrap percentile interval for pooled delta-MRR. Neither result gates selection.” A sign test on raw ranks is ambiguous and discards magnitude. |
| P7 | AMEND | Replace P7 with: “After the selected strategy, artifact hashes and report are committed, run each held-out question once through deterministic offline retrieval and report the 15 answerable results separately by repository. Treat only the 10 answerable questions from the two new repositories as external-replication evidence; IncidentWeave is retrospective.” |
| P8 | AMEND | Replace P8 with: “Report, but do not gate on, chunk count, chunk-size distribution, answerable/unanswerable distance distributions, and the span-coverage and evidence-density diagnostics defined below. Re-check the guard threshold in item 3b using the chosen production strategy and frozen evidence; do not tune it during 15a-2.” |
| P9 | AMEND | Replace P9 with: “15a-1 is code only: strategy-independent chunk descriptors, deterministic AST/S3 embedding-text builders, manifest-independent strategy registry, fixture/report schema support and unit tests, with no provider calls. 15a-2 builds strategy-specific chunks and document embeddings for every manifest repository, reuses the unchanged cached query embeddings, produces immutable comparison artifacts, applies the precommitted rule and records the result. 15b adopts the committed winner in production only after held-out reporting. 15c is parent expansion after item 17.” Current fixture building reads one default strategy from one evaluation database, so per-strategy artifacts need an explicit lifecycle. |
| P10 | AMEND | Replace P10 with: “Keep test files indexed and unweighted for every candidate. Report their share of top-five retrieval and preserve the identical policy across strategies; test downweighting/exclusion remains item 14.” Current ingestion labels all chunks `document_type=code`, so the experiment must not imply a test policy that does not exist. |

### a) Selection rule at 33 development questions

The precommitted rule is much better than choosing after inspection, but it is a practical decision rule rather than a statistically decisive test. A pooled delta-MRR of 0.03 is a total reciprocal-rank increase of 0.99 across 33 questions: two rank-2 to rank-1 moves contribute 1.0, or six rank-3 to rank-2 moves contribute 1.0. Thus it is observable but can be caused by very few changed questions and cannot reliably be separated from evaluation-set variation at this n. The proposed sign test will have even less sensitivity when many ranks tie.

The 1.5x raw-context ceiling is a reasonable safety limit if it applies to both mean and p95 de-duplicated source characters. “No repository loses more than one Hit@5” is useful but insufficient alone: with 11 development answerables it permits a 9% loss in one repository and says nothing about a larger rank-quality loss. The amended rule adds a per-repository MRR floor and interval reporting rather than pretending the 0.03 threshold proves a general effect.

### b) Metric bias

Span overlap is less boundary-dependent than a substring label, but a one-line overlap still credits a huge chunk. The proposed text-cost mean is necessary but not sufficient. Add two non-gating diagnostics: span coverage@5, the fraction of labeled source lines covered by the union of retrieved ranges, and evidence density@5, relevant labeled lines divided by unique retrieved source lines. Calculate both from de-duplicated line ranges per file. Coverage prevents a strategy from winning by touching a label token; density penalizes a whole-file-sized context. Report top-1 density separately for the retrieved first result. These diagnostics complement MRR rather than replacing it.

### c) S3 separation

S3 is correctly a distinct candidate because document vectors change while S2 boundaries do not. The current `Chunk` model stores raw `content`, path and structural-name fields; it has no `embedding_text` column. S3 therefore needs a deterministic builder used only when embedding. It must leave `content` and `content_hash` unchanged, so evidence quotes and citation validation remain valid. It also leaves FTS unchanged because the offline fixture rehydrates FTS-searchable `content`, not a separate embedding string. Vector distances, and consequently guard inputs, can change; that is why item 3b must re-check rather than tune the 0.5 threshold after adoption.

### d) Concrete 15a-1 code scope

- `evaluation/chunk_experiments.py` hard-codes only `baseline` and `w100_o20`, and couples each to an `incidentweave-eval` database repository. The strategy descriptor needs chunk/build parameters without a repository name.
- `evaluation/build_fixture.py` always selects `DEFAULT_STRATEGY`, finds one database repository, writes one manifest fixture path and records the global ingestion `CHUNKER_VERSION`; it needs strategy-specific chunk inputs, fixture paths and metadata.
- `evaluation/retrieval_eval.py` is manifest-selectable for the current fixture but assumes one fixture per repository and rehydrates only raw content/vectors. It needs strategy artifact selection while retaining its isolated temporary repository naming.
- `evaluation/runner.py` still allowlists `EVALUATION_REPOSITORIES`, resolves strategy-owned repository names, reads/writes the shared cache and exports a snapshot from this checkout through `evaluation/corpus.py`. It cannot yet run the two external manifest repositories as independent source roots or strategy databases.
- `evaluation/corpus.py` explicitly describes itself as restricted to `incidentweave-eval` and exports only commits available in this checkout. A repository-aware source/snapshot contract is needed before live experiment runs.
- `evaluation/manifest.json` has one `database_repository`, fixture, baseline and gate per repository; it needs a separate experiment-artifact namespace or manifest schema that cannot replace the S0 CI gate by accident.
- `scripts/ingest_repo.py` only creates 60/10 windows and writes empty structural metadata. It needs the selected chunker/version and deterministic descriptor persistence. `scripts/embed_chunks.py` sends `chunk.content` directly and needs an S3 embedding-text builder/version without changing stored content.

The existing chunks table can store `symbol`, `function_name`, `class_name`, `file_type` and `document_type` without a migration. `class_name` can represent a method’s class parent, but there is no general parent field and no persisted `embedding_text`; do not claim otherwise.

### e) Fixtures and cost

Existing manifest fixtures are each capped at 1.5 MiB. S0 already has one fixture per repository; S1/S2/S3 require nine additional strategy/repository document-vector artifacts if all candidates are evaluated. Query vectors do not change across these document strategies and can be reused from the current 24-question cache per repository, but every chunk in every new strategy needs one document embedding. Fixture construction itself is offline once vectors exist; provider calls belong only to the explicit 15a-2 embedding phase. Normal CI must continue to run the locked S0 smoke gate only. It must neither build candidate fixtures nor run them, while a missing selected experiment artifact must fail that experiment rather than silently fall back to S0.

### f) Overfitting, leakage, and omissions

- Four predeclared candidates reduce, but do not eliminate, selection bias. Do not add candidates, revise cutoffs or retry embeddings/runs after seeing development results without recording a new protocol.
- The 33 development questions are clustered in three repositories; treat per-repository rows as primary safeguards, not 33 independent codebases.
- LifeOS has 11/11 development Hit@5 at the current strategy if its full 16/16 result carries into the split. It can contribute rank improvements but no Hit@5 gains, so pooled MRR and per-repository reporting matter more than a ceilinged hit rate.
- Preserve strategy code, source pin, fixture, query-cache/model, chunker/embedding-text version and comparison hashes together. Otherwise a result cannot be reproduced or attributed to a single change.
- Specify handling for empty module headers, nested definitions, syntax errors, generated files, duplicate/overlapping source ranges, and secrets before embedding. The current secret scanner must remain on every raw chunk.

## 3. Resolved plan

1. Compare fixed candidates S0 (60/10), S1 (100/20), S2 (deterministic AST chunks) and S3 (S2 with separately versioned embedding text). Commit all AST thresholds, merge order and fallback semantics before embeddings. (amended by Codex review)
2. Defer parent expansion to 15c after item 17, where answer quality and citations can be evaluated.
3. Select on pooled, question-weighted span-label MRR over 33 development answerables, with per-repository MRR/Hit@1/3/5 and direct/paraphrased reports. Mark IncidentWeave previously exposed. (amended by Codex review)
4. Measure mean and p95 unique raw source characters in top-five context, de-duplicated by file/line range, per repository and pooled. Also report fixture size and chunk count. (amended by Codex review)
5. Commit one run matrix and artifact hashes before embeddings. A candidate must meet the amended per-repository Hit@5/MRR floors, pooled delta-MRR of at least 0.03, and mean/p95 context ceilings. Use highest pooled MRR then simpler strategy, or retain S0. Report the paired delta-MRR interval without claiming significance. (amended by Codex review)
6. Report the exact sign test on non-zero reciprocal-rank changes and a seeded paired-bootstrap delta-MRR interval; neither gates adoption. (amended by Codex review)
7. Commit the chosen strategy and its development report, then run held-out offline retrieval once. Report all 15 answerables by repository, but treat only the two new repositories’ 10 answerables as external replication. (amended by Codex review)
8. Report non-gating chunk/count/distance diagnostics plus de-duplicated span coverage and evidence density; defer threshold selection to 3b after adoption. (amended by Codex review)
9. Implement 15a-1 as provider-free strategy/descriptor/artifact support and tests; run 15a-2 as the explicit embedding/artifact/comparison phase; perform 15b production adoption only after held-out reporting; reserve 15c for parent expansion after 17. (amended by Codex review)
10. Keep test files indexed and unweighted for every candidate, and report their top-five share; leave policy changes to item 14. (amended by Codex review)

### Open decisions for the maintainer

None.

## 4. Checklist impact

Changed `03-fix-checklist.md` entries are: line 40 (Progress log row); lines 64-67 (summary-table 15a-1, 15a-2, 15b and 15c rows); line 88 (recommended order); line 94 (15/3b dependency wording); and lines 199-217 (the replacement 15a-1, 15a-2, 15b and 15c details, Done-when and Status lines).

## 5. Result of the development comparison (item 15a-2)

Decision: S0 retained. The precommitted rule (protocol.json, committed before any embedding) was applied unchanged. The held-out questions were not run, because the plan runs them only to confirm a selected candidate; they remain unobserved.

Table (development split, 33 answerable questions, span labels):

| Strategy | Pooled MRR | Pooled Hit@5 | Mean top-5 context (chars) | p95 context (chars) | Qualifies |
|---|---:|---:|---:|---:|---|
| S0 60/10 | 0.668 | 27/33 | 7,608 | 10,592 | reference |
| S1 100/20 | 0.723 | 31/33 | 11,000 (x1.45) | 16,632 (x1.57) | No: p95 context above the 1.5 limit |
| S2 AST | 0.664 | 28/33 | 4,434 (x0.58) | 6,620 (x0.63) | No: pooled MRR gain below 0.03; batch-processing-service MRR lost 0.091 (limit 0.03) |
| S3 AST + path/symbol text | 0.630 | 28/33 | 4,194 (x0.55) | 6,620 (x0.63) | No: same two conditions as S2 |

Paired statistics versus S0 (reported, not gating): S1 11 wins, 2 losses, 20 ties, exact sign-test p=0.022, delta-MRR +0.056, bootstrap 95% interval [-0.022, 0.129]; S2 6 wins, 4 losses, 23 ties, p=0.754, delta-MRR -0.004, interval [-0.121, 0.114]; S3 4 wins, 8 losses, 21 ties, p=0.388, delta-MRR -0.038, interval [-0.169, 0.101].

Interpretation, with limits: S1 met four of the five conditions and failed only the p95 context limit; its gain came with about 45% more context on average and its interval includes zero, which is the size effect the cost limit exists to catch. The sign test is one of three comparisons and does not gate. AST chunking (S2) matched S0 on Hit@5 and MRR using about 40% less context, but lost 0.091 MRR on batch-processing-service while gaining 0.073 on lifeos; adding path and symbol text (S3) lowered MRR further. These results do not show that AST chunking is better or worse in general: there are only 33 development questions, three repositories by one author, IncidentWeave was previously exposed, and lifeos is at its Hit@5 ceiling. The rule and thresholds were not changed after seeing the results.

What follows: 15b is closed with no change (S0 stays in production ingestion). Any new comparison (for example at an equal context budget, or with more questions) would need a new, separately registered protocol and fresh data; it must not reuse these development results to choose thresholds. Item 3b will use the held-out questions with the S0 chunker.
