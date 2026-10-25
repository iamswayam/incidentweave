# Multi-Repository Evaluation

## Manifest and repository selection

[evaluation/manifest.json](../../evaluation/manifest.json) is the versioned source of truth for
evaluation repositories. Each entry records the repository URL and pinned commit, ownership and
licence note, indexed Python-line count, question/fixture/baseline/gate paths and SHA-256 hashes,
and the fixture-size ceiling. The loader rejects unknown schema versions, duplicate repository
IDs, missing or mismatched files, inconsistent pins, invalid split assignments, and fixtures
over their declared size limit. `--repo ID` selects one entry; by default, retrieval evaluation
and the gate select every manifest entry.

The manifest currently contains IncidentWeave only. Items 16b and 16c add reviewed question sets,
fixtures, baselines, and gates for the two approved repositories. The existing IncidentWeave
fixture, golden set, baseline, and gate stay at their existing paths.

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

The current committed manifest has one repository, so it does not yet establish cross-repository
generalisation. The planned three repositories are all by one author, and IncidentWeave's
held-out questions were previously exposed. Results are limited to pinned Python source and
committed embeddings; they do not establish language-generalisation, answer quality, or absence
of training-data contamination.
