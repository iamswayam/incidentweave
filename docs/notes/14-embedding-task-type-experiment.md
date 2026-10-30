# Embedding task-type comparison (item 14a)

## Purpose and status

Compare one Gemini embedding configuration against the selected retrieval control before
changing production defaults or rebuilding stored vectors. This note registers the control,
candidate, metrics, and decision rule before any candidate embedding or result exists.

The required provider calls were not made in this offline preparation. The development
comparison and retention decision are pending a maintainer-run `embed` command followed by
the offline `evaluate` command. Production embeddings, the vector column, chunking, lexical
retrieval, test-file handling, baselines, gates, and manifest remain unchanged.

## Control and candidate

The control is current production hybrid retrieval using S0 60/10 chunks and the unchanged
14c full-text behavior. The registered 14c comparison adopted no lexical variant. The
registered 14b comparison retained neither V1 nor V2, so the control has no test-file
downweighting or exclusion. V1 was descriptive only; test-file policy is not varied here.

The single candidate changes only the Gemini embedding task metadata:

| Input | Task type | Endpoint shape |
|---|---|---|
| Repository chunk/document | `RETRIEVAL_DOCUMENT` | `batchEmbedContents`, applied to each request |
| Development question/query | `CODE_RETRIEVAL_QUERY` | `embedContent` |

Both settings use `models/gemini-embedding-001` and 768 dimensions. The task type is sent
as REST JSON `taskType`; the Python helper accepts the keyword `task_type`. This item does
not activate task types in production. Existing helper calls omit the optional task type,
preserving their current request bodies until the registered comparison and a later
maintainer adoption decision.

The protocol's most conservative readings are:

- The two task types are one paired embedding configuration; there is no separate search
  over task-type combinations.
- All 16 development questions per repository are embedded for each candidate, so the
  15 unanswerable development questions remain available for guard checks. No held-out
  question or vector is embedded or evaluated.
- The selected 14c and 14b controls stay fixed. No retrieval setting changes alongside
  the embedding configuration.
- Item 14a does not specify numeric safeguards. To avoid weakening the registered 14b
  decision, apply its R1-R5 criteria unchanged; when test-source recall has a zero
  denominator, R5 is not evaluable and cannot authorize retention.
- The task-type candidate remains experimental even if it meets the numeric rule; no
  production embedding rewrite or adoption is performed by the comparison command.

## Metrics and decision

Only the 33 answerable development questions contribute to reciprocal-rank statistics.
Report pooled substring MRR (primary), per-repository answerable Hit@5 successes, Hit@1,
Hit@3, span MRR, test-file share of top five, test-source recall and test precision.
Evaluate the unchanged production evidence guard on all 15 unanswerable development
questions. Report changes by repository and development ordinal only.

Use paired bootstrap resampling of the 33 question-level reciprocal-rank differences,
seed `20261031`, 10,000 resamples, 95% percentile interval with linear interpolation.
The exact two-sided sign test is descriptive only.

| Rule | Retention condition |
|---|---|
| R1 | Pooled MRR gain is at least `0.03`. |
| R2 | Lower bound of the paired-bootstrap 95% interval is above zero. |
| R3 | No repository loses an answerable Hit@5 success (tolerance: 0 questions). |
| R4 | No unanswerable guard decision regresses in any repository (tolerance: 0 questions); sufficient-to-insufficient is an improvement. |
| R5 | Pooled test-source recall loses at most one question. A zero denominator is not evaluable and is not a pass. |

Retain only if every rule passes. Otherwise keep the current control and do not adopt the
task-type candidate. On the registered 14b development set, test-source recall's denominator
was zero; that value is not reinterpreted after seeing the task-type results.

## Versioning, quota, and artifacts

Candidate cache identity includes the experiment version, model, dimension, task type, and
input text hash. It cannot reuse legacy vectors or mix document and query vectors. Candidate
fixtures and reports are written under ignored `evaluation/cache/embedding_task_type_v1/`;
the committed control fixture, baseline, gate, manifest, and production database embeddings
are not overwritten.

The plan is fail-closed at 200 unique document texts, 48 unique development query texts,
and four document batches of at most 50 texts. Each physical request is limited to one
attempt, bounding the initial plan to at most 52 HTTP requests. Defaults pace document
batches 70 seconds apart and query requests 1.5 seconds apart. The `plan` command prints
the exact uncached text and request counts before any provider call. If interrupted,
successful vectors are cached separately; re-run `plan` before resuming so only uncached
inputs are counted. No API key or request content is written to the report.

The safe plan on the empty task-type cache reported 156 unique document texts and 47
distinct development query texts: four batched document requests plus 47 single-query
requests, 51 HTTP requests total. These are input/request counts, not a retrieval result.
Re-run `plan` before any later call because completed cached vectors reduce the remaining
request count.

Provider usage is tagged `document_embedding` for document batches and `query_embedding`
for query requests. The operator must confirm their current provider quota before running;
the caps limit this experiment but are not a promise about current account limits.

## Reproduction

From the repository root, first inspect the safe command interface and request plan:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_embedding_task_type_experiment --help
.\.venv\Scripts\python.exe -m scripts.run_embedding_task_type_experiment plan
```

Only after reviewing the printed development-only counts and explicitly deciding to spend
the bounded quota, set `GEMINI_API_KEY` in the process environment and run:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_embedding_task_type_experiment embed --confirm-provider-calls
```

This command requires a provider key, sends no generation requests, and uses the one-attempt
budget and pacing above. It stores task-versioned vectors in the ignored cache. With the
local PostgreSQL service available, evaluate those cached vectors without provider calls:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_embedding_task_type_experiment evaluate
```

The evaluation selects `development` with the diagnostic's `_development_question_records`
loader, passes those rows to an evaluator that rejects explicit non-development records,
applies the current retrieval path and production guard, and writes aggregate-only reports
to the ignored cache directory. It does not write a committed baseline or make a held-out
decision.
The report must be reviewed and copied into the documentation only in a later result-recording
step; this offline preparation does not claim a winner.

The Google API documentation was not fetched in this offline task. Verify the current REST
`taskType` contract and account quota before the maintainer authorizes the provider calls.

## Limits

The comparison uses 33 answerable and 15 unanswerable development questions across three
small repositories. Results may not generalize to other repositories or query distributions.
If R5 remains not evaluable because no test-evidence question exists, the conservative rule
cannot retain the candidate. A successful retrieval metric does not establish answer quality.
The held-out split remains untouched.
