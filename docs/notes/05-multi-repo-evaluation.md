# Multi-Repository Evaluation

## Manifest and repository selection

[evaluation/manifest.json](../../evaluation/manifest.json) is the versioned source of truth for
evaluation repositories. Each entry records the repository URL and pinned commit, ownership and
licence note, indexed Python-line count, question/fixture/baseline/gate paths and SHA-256 hashes,
and the fixture-size ceiling. The loader rejects unknown schema versions, duplicate repository
IDs, missing or mismatched files, inconsistent pins, invalid split assignments, and fixtures
over their declared size limit. SHA-256 checks normalize CRLF to LF for JSON resources, while
binary fixtures are hashed as stored, so manifest validation is consistent across operating
systems. `--repo ID` selects one entry; by default, retrieval evaluation and the gate select every
manifest entry.

The manifest contains IncidentWeave and the pinned
`iamswayam/batch-processing-service` and `iamswayam/lifeos` snapshots. The existing IncidentWeave
fixture, golden set, baseline, and gate stay at their existing paths. All three repositories are
maintainer-owned and by one author, which limits the independence of this evaluation.

The per-file answerable-question cap defaults to three and is set per repository through
`max_questions_per_file`; batch-processing-service uses five. The supplied rationale cited 47%
concentration in `engine.py` and `routes.py`; the recorded measurement is 438/838 lines (52.3%)
within indexed `app/` Python files, or 438/1,527 (28.7%) across all indexed Python files,
including tests and `mock_vendor`. The minimum remains six distinct labeled files.

## Splits and running evaluations

The split assignment helper uses a fixed seed and stratifies by answerability and then question
category. Generated assignments are committed as explicit question ID lists in the manifest.
IncidentWeave is marked `previously_exposed` and its held-out split is retroactive, not independent
evidence. The eight-question smoke split is a fixed subset of the 16 development questions and
has a separate gate baseline.

Run the offline retrieval evaluation (no provider calls or API key) for all questions:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_retrieval_eval --split all
```

Select a repository or split with `--repo ID` and `--split development|held_out|smoke|all`.
Evaluation and chunking-experiment runs default to development. Selecting `held_out` or `all`
for those experiments requires `--confirm-frozen-heldout`, prints a warning, and records the
selection and confirmation in report metadata. Held-out results are for reporting after a
design is fixed, not for choosing a threshold or chunking strategy.

The CI retrieval gate runs the smoke split for all manifest repositories:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_retrieval_gate --split smoke
```

It prints a table for each repository, including gate checks and elapsed time, then a pooled
table with question denominators and Wilson intervals. Any failed, missing, or invalid selected
repository fails the command; pooled results are not presented as complete when a repository
fails. To run the full set locally, use `--split all`. A repository's full and smoke gates and
their baselines are individually hash-pinned in the manifest. Changing a baseline or tolerance
requires a reviewed pull request; CI does not rebuild either.

Each repository has 8 held-out questions (5 answerable and 3 unanswerable); smoke is an 8-question
subset of its 16-question development assignment. IncidentWeave's held-out assignment is
retroactive because those questions were previously exposed. Hit@5 intervals below are 95% Wilson
intervals. Unanswerable questions are excluded from retrieval-hit and MRR denominators.

| Repository / split | Label type | Answerable N | Hit@5 | Hit@5 95% Wilson interval | MRR |
|---|---|---:|---:|---:|---:|
| IncidentWeave full | Substring | 16 | 11/16 | 0.444–0.858 | 0.572917 |
| IncidentWeave full | Span | 16 | 11/16 | 0.444–0.858 | 0.572917 |
| IncidentWeave smoke | Substring and span | 5 | 4/5 | 0.376–0.964 | 0.533333 |
| batch-processing-service full | Substring | 16 | 13/16 | 0.570–0.934 | 0.625000 |
| batch-processing-service full | Span | 16 | 14/16 | 0.640–0.965 | 0.640625 |
| batch-processing-service smoke | Substring and span | 5 | 4/5 | 0.376–0.964 | 0.700000 |
| lifeos full | Substring | 16 | 16/16 | 0.806–1.000 | 0.804167 |
| lifeos full | Span | 16 | 16/16 | 0.806–1.000 | 0.804167 |
| lifeos smoke | Substring and span | 5 | 5/5 | 0.566–1.000 | 0.900000 |
| Pooled full | Substring | 48 | 40/48 | 0.700–0.910 | 0.667 |
| Pooled full | Span | 48 | 41/48 | 0.730–0.930 | 0.673 |
| Pooled smoke | Substring | 15 | 13/15 | 0.620–0.960 | 0.711 |
| Pooled smoke | Span | 15 | 13/15 | 0.620–0.960 | 0.711 |

All three repositories passed their smoke and full gates with observed results equal to their
committed baselines. The pooled rows combine answerable questions only; each repository's gate is
still checked independently.

## Question-authoring protocol

For each repository, maintain 24 questions: 8 direct and 8 paraphrased answerable questions, plus
4 far and 4 near unanswerable questions. Every answerable question must be grounded in ingested
Python files only. Paraphrases should avoid copying distinctive identifiers from the
implementation. Unanswerable questions should be plausible but refer to behavior absent from the
pinned Python source. Verify answer spans and absence against the complete pinned source snapshot,
then have a second reviewer approve question wording, labels/spans, and absence assertions. Freeze
wording before inspecting retrieval results; record revisions and review decisions with the
question set.
The span labels identify inclusive source line ranges, while the original substring labels remain
available for comparison.

Repository additions follow the same sequence: pin and review the source, record ownership and
licence evidence, measure indexed Python lines excluding migrations and generated/vendor code,
author and review the questions, commit explicit split IDs, build the offline fixture from local
embeddings, compute per-repository full and smoke baselines, then add their hashes and gates to
the manifest. Fixture creation reads the local evaluation database and embedding cache only; it
does not fetch embeddings or call a provider.

## Statistical and scope limits

Hit-rate intervals are 95% Wilson intervals. At the 16-answerable-question development or held-out
scale, 11/16 has an interval of 44.4%–85.8% and 15/16 has an interval of 72.0%–98.9%. At the
eight-question smoke scale, 4/8 has an interval of 21.5%–78.5% and 7/8 has an interval of
52.9%–97.8%. These small samples detect only large changes reliably; a smoke pass is a regression
signal, not evidence of broad generalisation. Paired comparisons use a two-sided exact sign test
on discordant question pairs, with ties excluded.

The committed manifest has three repositories, all by one author. This is a limited
multi-repository check, not independent replication across owners. IncidentWeave's held-out
questions were previously exposed. Results are limited to pinned Python source and committed
embeddings; they do not establish language-generalisation, answer quality, or absence of
training-data contamination.
