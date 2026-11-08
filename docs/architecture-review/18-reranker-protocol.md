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

Also report the scorecard's guard metrics and the item 34 citation and refusal checks:
citation quote validity, retrieval-grounded citation rate, false-answer and
false-refusal rates, overall correctness, and the `answered`, `refused_guard`, and
`abstained_model` outcomes. The item 32 scorecard defines no citation or abstention
metrics and no non-inferiority margins; use item 34's definitions for those checks and
the proposed margins below.
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

## 5. Proposed decision rule

Every numeric gate below is **proposed and must be confirmed by the maintainer before the
run**. Keep the candidate only if all conditions hold:

1. The lower bound of the paired 95% interval for MRR@5 improvement is above zero, and
   the pooled point improvement is at least **0.02 absolute**.
2. No secondary safety metric is worse than baseline beyond its margin: **zero absolute**
   for citation validity and retrieval-grounded citation rates; **zero absolute** for
   guard false-accept rate; and **0.02 absolute** for refusal and abstention rates and
   refusal correctness rate. The scorecard defines no such margins; the zero false-accept
   margin is an additional conservative proposal.
3. Added median latency per query is at most **500 ms**, and added p95 latency is at most
   **1,500 ms**.
4. Cost per 1,000 queries is recorded and reported. There is no cost cap; the maintainer
   judges the reported cost.

Otherwise reject the candidate and record the result. There are no second chances and
the rule cannot change after results are seen. Record any deviation in the results
document without adding a date.

## 6. Run procedure and records

Before any run, pin the model identifier, API version, run settings, and data hashes.
Require the Docker database to be available for the retrieval and operational path. Keep
`VOYAGE_API_KEY` only in the local git-ignored `.env`; never commit or print it. No key
or live request is used to register this protocol.

Run in this order:

1. Validate the selected development split and freeze each question's top 20 candidates.
2. Save the baseline ordering and the pinned model/API/settings record.
3. Rerank those same candidates; record every response and failure.
4. Compute paired per-question metrics, intervals, latency deltas, and cost.
5. Write the aggregate report and apply the registered decision rule without changing it.

Later-run files, not created by this registration:

- `evaluation/experiments/reranker/development-rankings.json`
- `evaluation/experiments/reranker/development-report.json`
- `evaluation/experiments/reranker/report-development.md`
- `scripts/run_reranker_experiment.py`

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
