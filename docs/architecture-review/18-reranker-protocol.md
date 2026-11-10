# Reranker experiment protocol (item 21)

## 1. Registration and scope

Register this protocol before any reranker run. No valid experiment has been analyzed.

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
per-question candidate-set hashes before the run. For each question, use the scorecard's
development deep view to freeze its top 20 candidates. The baseline is that same deep-view
ordering truncated to five. The treatment reranks the identical 20 candidates and truncates
to five. The reranker may only reorder candidates; it cannot add, remove, or modify
candidate text. Keep chunking, retrieval, labels, and guard settings fixed.

## 3. Candidate

The original registered candidate was a hosted reranking model served through the existing
Voyage provider. That path is retained below for auditability but was discarded after the
free account returned HTTP 429 on three runs; none was analyzed and no metric was computed.
The amendment below replaces it, before any valid result exists, with exactly one open-weight
candidate. No second candidate is tested under this protocol.

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

## Amendment: open-weight candidate on a free GPU notebook

The registered hosted candidate could not be run on a free account: three Voyage runs were
rejected by HTTP 429 (36/48, 23/48, and 20/48 questions fell back to baseline). None was
analyzed and no metric was computed. Before any valid result exists, the single candidate is
replaced with Qwen/Qwen3-Reranker-0.6B (Apache-2.0). The number of candidates remains one.
No gate or decision rule changes.

The task is unchanged: rerank the same frozen top-20 development candidates. The baseline
is the current top-20 order truncated to five; treatment reranks the identical 20 candidates
and truncates to five. Primary metric remains MRR@5. Use the same paired bootstrap (seed
20261031, 10,000 resamples, 95% percentile interval), the same MRR@5 gain gate (at least
0.02 with interval lower bound above zero), the same guard gates, and the same added latency
gates (median at most 500 ms and p95 at most 1,500 ms per query). Latency is measured on the
stated GPU with a warm model and 20 query-document pairs scored in one batch.

Local inference is fixed in advance: use the exact instruction in
`scripts/kaggle_rerank_qwen3.py`, the model card prompt format, max_length 8192, float16,
and batch size 20. Do not tune the instruction, prompt, or settings after seeing results.
Record the model revision from the run, GPU hardware, and torch and transformers versions.

There is no per-token fee. The pin price is zero, the experiment reports zero API cost, and
compute uses a free notebook GPU. GPU latency does not establish production CPU latency;
measure latency separately on the target CPU before any adoption. That CPU measurement is
not a gate for this experiment. Candidate Recall@20 is 33/33; the pool is not the limit.
The perfect-order ceiling is an upper bound, not a forecast. Guard metrics are unchanged by
construction because the guard uses vector distance before reranking. End-to-end citation
metrics are not measured here.

The request file contains development repository code chunks. Upload it only as a private
notebook dataset. It is not committed; it lives under `evaluation/cache/`, which is
git-ignored.

## 6. Run procedure and records

For the open-weight candidate, pin the model identifier, local inference settings, and data
hashes before scoring. The workflow is:

1. `python -m scripts.run_reranker_experiment export` requires the Docker evaluation
database and no provider key. It uses scorecard development-only validation, freezes the
top-20 candidate text and baseline order, and records the dataset, fixture, and per-question
candidate-set hashes.
2. `python -m scripts.run_reranker_experiment export-requests` validates the frozen
rankings against the development source split and writes
`evaluation/cache/reranker_requests_v1/reranker_requests.json`. The ignored request file
contains the query and candidate code text in baseline order.
3. Run `scripts/kaggle_rerank_qwen3.py` in Kaggle or Colab with a GPU, using the request file
as a private notebook dataset. The script records scores, per-question latency and token
count, model revision, GPU, and library versions in `reranker_results.json`. No provider
API is called.
4. `python -m scripts.run_reranker_experiment import-results --requests
<reranker_requests.json> --results <reranker_results.json>` validates the request-set hash,
model settings, complete question keys, score arrays, latency, and token counts. It imports
scores into the frozen rankings file and applies stable descending score order (ties retain
baseline order).
5. `python -m scripts.run_reranker_experiment analyze` reads saved development data and
manifest-selected fixtures only. It needs no database, key, or network access.

The discarded hosted path remains documented for the record:
`python -m scripts.run_reranker_experiment rerank [--min-interval-seconds N]` used the
existing metadata-only provider usage log and `VOYAGE_API_KEY` from local git-ignored
`.env`. The three failed runs returned HTTP 429 as described in the amendment. Do not use
that path for this candidate or treat those attempts as results.

The local pin records `model_identifier`, `api_version` (`v1`), empty `model_settings`,
request limits, retry policy, zero pricing, and `local_inference` fields: model identifier,
fixed instruction, max_length, and dtype. The imported results record the model revision,
hardware, batch size, and torch and transformers versions. No credentials are included.

Run-time files:

- `evaluation/experiments/reranker/development-rankings.json`
- `evaluation/experiments/reranker/development-report.json`
- `evaluation/experiments/reranker/report-development.md`
- `evaluation/experiments/reranker/pin.json` (local run-time settings; not a credential file)
- `evaluation/cache/reranker_requests_v1/reranker_requests.json` (ignored; contains development code)
- `reranker_results.json` (not committed; notebook output)

Store dataset and fixture hashes, baseline and treatment rankings, per-question metric
values and differences, guard/citation/refusal outcomes, model settings and revision,
hardware and library versions, latencies, token counts, cost estimates, errors, fallback
counts, and the decision. Notebook output import rejects incomplete or mismatched results;
no question is silently dropped.

## 7. Risks and exclusions

The development sample is small, so paired intervals may be wide and results may not
generalize. Test-file noise can affect rankings; the registered classifier diagnostic
does not establish test-file evidence quality. Keep development and held-out data
separate to prevent leakage. Free notebook GPU availability is not guaranteed.

Held-out evaluation is out of scope and remains in item 3b. Changing chunking or the
guard threshold is out of scope. GPU notebook results do not establish production CPU
latency; measure the target CPU separately before adoption.
