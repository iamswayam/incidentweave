# Reranker experiment protocol (item 21)

## 1. Registration and scope

Register this protocol before any reranker run. No experiment has been run.

Question: does reranking the current top 20 candidates into a top 5 improve retrieval on
the development split at acceptable latency and cost, without making guard, citation, or
abstention behavior worse?

Use the development split only. The held-out split remains untouched and is part of item
3b. This experiment makes no production-default changes. If the reranker is kept, it ships
off by default behind a setting.

## 2. Data and comparison

Use the item 32 scorecard's committed questions, manifest-selected fixtures, and cached
retrieval outputs. Its v1 scorecard uses the development split for exactly the three
manifest repositories `incidentweave`, `batch-processing-service`, and `lifeos`. Follow
the scorecard's fail-closed split and repository checks; do not read held-out data. If
item 32b has frozen dataset v2.0 before this run, include its manifest-selected
development repositories as a separate cohort; report versions separately and never
pool them.

Freeze the selected scorecard dataset version, manifest, fixtures, retrieval commit, and
per-question candidate-set hashes before the run. For each question, retrieve the current
production ordering's top 20 candidates using the scorecard's deep view. The baseline is
that unchanged ordering truncated to five. The treatment reranks the identical 20
candidates and truncates to five. The reranker may only reorder candidates; it cannot add,
remove, or modify candidate text. Keep chunking, retrieval, labels, and guard settings
fixed.

## 3. Candidate

Test exactly one candidate: a hosted reranking model served through the existing Voyage
provider.

- Model identifier: to be pinned and recorded before the run.
- API version: to be pinned and recorded before the run.
- Run settings: to be pinned and recorded before the run.

Record the request limits, truncation behavior, timeout, retry policy, and model settings.
No other candidate is tested under this protocol. A second candidate requires its own
protocol.

## 4. Metrics and paired analysis

The primary metric is **MRR@5**, using the item 32 scorecard's metric name and formula.
The scorecard does not designate a primary metric; this protocol designates MRR@5.
Secondary retrieval metrics are Hit@1, Hit@3, Hit@5, Hit@10, Hit@20, nDCG@5, nDCG@10,
Recall@20, and context precision@5, using the scorecard definitions and cutoffs.

The current item 32 scorecard computes `guard.false_accept_rate`,
`guard.correct_refusal_rate`, `guard.false_refusal_rate`, `guard.refusal_precision`,
and `guard.refusal_recall`. The current item 34 end-to-end runner computes
`citation_quote_validity`, `retrieval_grounded_citation_rate`,
`answered_with_citations`, `false_answer_rate`, `false_refusal_rate`,
`overall_correctness`, `outcome_counts`, `stable_outcome_questions`,
`mean_cited_chunk_jaccard`, and `flip_questions`; `outcome_counts` includes the
`answered`, `refused_guard`, and `abstained_model` outcomes.

This experiment reranks retrieval results only; it does not run the application with
the treatment ordering. Therefore `citation_quote_validity`,
`retrieval_grounded_citation_rate`, `answered_with_citations`, `false_answer_rate`,
`false_refusal_rate`, `overall_correctness`, `outcome_counts`,
`stable_outcome_questions`, `mean_cited_chunk_jaccard`, and `flip_questions` are
**not measured in this experiment; not a gate**. There is no computed
`abstention_rate`: the end-to-end runner reports `outcome_counts` rather than an
abstention rate, so an abstention-rate gate is **not measured in this experiment; not a
gate**. The unchanged retrieval guard can be measured by the existing scorecard;
report its exact metrics and apply only the gates specified in section 5.
Use the item 14b `evaluation/test_files.py` classifier to report test-file share as a
noise diagnostic, not as a decision gate.

For every metric, report per-question treatment-minus-baseline differences, per-repository
and pooled summaries, and sample counts. Use `evaluation.stats.stratified_bootstrap_interval`
on per-question paired differences, resampling within repository strata with seed
`20261031`, 10,000 resamples, and a 95% percentile interval with linear interpolation,
as in item 32. For paired binary Hit@k outcomes, also report
`evaluation.stats.paired_comparison` wins, losses, ties, and its exact two-sided sign-test
p-value; it is descriptive, not an additional decision gate.

Report added per-query latency and cost using item 33's operational-report conventions.
Report median/p50 and p95 latency deltas per query, using nearest-rank percentiles, and
cost per 1,000 queries. Record token counts, errors, and the estimated list-price cost
per operation/query; report any observed free-tier amount separately, never as the
estimated cost.

## 5. Confirmed decision rule

The numeric gates below were confirmed by the maintainer before the run. Keep the
candidate only if all conditions hold:

1. The lower bound of the paired 95% interval for MRR@5 improvement is above zero, and
   the pooled point improvement is at least **0.02 absolute**.
2. No measured safety metric is worse than baseline beyond its margin:
   **zero absolute** for `guard.false_accept_rate`; and **0.02 absolute** for
   `guard.false_refusal_rate` and `guard.correct_refusal_rate`. Citation validity,
   retrieval-grounded citation rate, and abstention rate are **not measured in this
   experiment; not a gate** (section 4). Do not substitute other metrics or derive
   unregistered rates.
3. Added median latency per query is at most **500 ms**, and added p95 latency is at most
   **1,500 ms**.
4. Cost per 1,000 queries is recorded and reported. There is no cost cap; the maintainer
   judges the reported cost.

Otherwise reject the candidate and record the result. There are no second chances and
the rule cannot change after results are seen. Record any deviation in the results
document without adding a date.

**Pre-run amendment:** The numeric gates are confirmed before any run. Sections 4 and 5
name the guard and end-to-end metrics present in the current scorecard and runner, and
exclude citation and abstention gates because this retrieval-only experiment cannot
measure treatment answer behavior. The protocol previously described item 34 as not
built; the current code contains its checks, but they are not wired to the reranked
ordering.

## 6. Run procedure and records

Before any run, pin the model identifier, API version, run settings, and data hashes.
The harness has three separate commands:

1. `python -m scripts.run_reranker_experiment export` requires the Docker evaluation
   database and no provider key. It uses the scorecard's development-only validation,
   freezes the top-20 candidate text and baseline order, and records the dataset, fixture,
   and per-question candidate-set hashes.
2. `python -m scripts.run_reranker_experiment rerank [--min-interval-seconds N]` accepts an
   optional minimum spacing between request start times (default `0`). It requires the evaluation database for
   the existing metadata-only provider usage log, plus `VOYAGE_API_KEY` in the local
   git-ignored `.env`. The key is never accepted as an argument or written to experiment
   data, logs, or reports. It refuses to run without `pin.json`.
3. `python -m scripts.run_reranker_experiment analyze` reads only saved development data
   and manifest-selected fixtures. It needs no database, key, or network access.

Create `evaluation/experiments/reranker/pin.json` locally before reranking. It records
`model_identifier`, `api_version` (`v1`), `model_settings` (an empty object; the registered
rerank endpoint has no additional model-specific settings), `request_limits`
(`max_candidates` and `top_k` both 20, `truncation`, positive `timeout_seconds`, and
`max_attempts` from 1 through 5), `retry_policy` (exponential strategy, positive initial
and maximum delays, and whether to respect the provider's `Retry-After` header), and
`pricing` (`usd_per_million_tokens` and `source_url`). Do not include credentials. No key
or live request is used to register this protocol.

Run in this order:

1. Validate the selected development split and freeze each question's top 20 candidates.
2. Save the baseline ordering and the pinned model/API/settings record.
3. Rerank those same candidates; record every response and failure.
4. Compute paired per-question metrics, intervals, latency deltas, and cost.
5. Write the aggregate report and apply the registered decision rule without changing it.

Harness files:

- `app/providers/reranker.py`
- `evaluation/studies/reranker/reranker_experiment.py`
- `scripts/run_reranker_experiment.py`

Run-time files:

- `evaluation/experiments/reranker/development-rankings.json`
- `evaluation/experiments/reranker/development-report.json`
- `evaluation/experiments/reranker/report-development.md`
- `evaluation/experiments/reranker/pin.json` (local run-time settings; not a credential file)

Store dataset and fixture hashes, baseline and treatment rankings, per-question metric
values and differences, guard/citation/refusal outcomes, model and API settings, latencies,
token counts, cost estimates, errors, fallback counts, and the decision. A rerank API
failure uses the baseline ordering for that question and is reported; never silently drop
the question or failure.

## 7. Risks and exclusions

The development sample is small, so paired intervals may be wide and results may not
generalize. Test-file noise can affect rankings; the registered classifier diagnostic
does not establish test-file evidence quality. Keep development and held-out data
separate to prevent leakage. The hosted calls incur run cost, which must be recorded.

Held-out evaluation is out of scope and remains in item 3b. Local cross-encoders,
chunking changes, and guard-threshold changes are out of scope.
