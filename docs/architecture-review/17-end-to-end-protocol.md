# Citation and end-to-end protocol (item 34)

## 1. Registration and scope

**Status:** Registered before any item 34 run. **Registered on:** 2026-11-08.

This protocol applies only to questions explicitly assigned to the development split.
No held-out questions or artifacts are read before the one authorized held-out run in
item 3b. No thresholds are set because no item 34 baseline exists. Results are
descriptive and will be compared in item 3b using these same definitions.

Each question record carries its question ID and answerability. The question file's
`answerable` boolean is authoritative; answerable questions have relevant/gold spans,
and unanswerable questions have unanswerable labels and no answer gold spans. For
legacy question files without that boolean, the manifest's answerability convention
is used: categories beginning with `unanswerable` are unanswerable.

## 2. Check A — quote in cited chunk

For every submitted citation in a recorded answer, normalize whitespace by splitting
on whitespace and joining with one ASCII space, matching
`app/investigation/parsing.py`. A normalized quote is valid only if it is at least
10 characters and occurs in the normalized text of the chunk it cites.

Report citation quote validity as valid citations / submitted citations; it is
undefined when no citations were submitted. Also report the share of answered
investigations with at least one submitted citation, with its numerator and
denominator.

## 3. Check B — cited chunk in retrieved set

For every submitted citation, check whether its chunk ID is among the ranked chunk
IDs retrieved for that same run and supplied to the prompt. Report retrieval-grounded
citation rate as citations whose chunk ID is in that set / submitted citations; it is
undefined when no citations were submitted.

## 4. Check C — refusal correctness

Use the question file's answerability label. Expected outcomes are:

- Answerable: `answered`.
- Unanswerable/refused: `refused_guard` or `abstained_model`. The latter is the
  model's `INSUFFICIENT_EVIDENCE` outcome.

`generation_unavailable` and `embedding_unavailable` are degraded outcomes. Exclude
them from correctness-rate denominators and report each count separately. An `error`
or other non-degraded outcome is not silently excluded: it is incorrect for overall
correctness. False-answer counts only `answered` outcomes on unanswerable questions;
false-refusal counts only `refused_guard` or `abstained_model` outcomes on answerable
questions. Report false-answer rate, false-refusal rate, and overall correctness with
numerators, denominators, and Wilson 95% intervals. A rate and interval are undefined
when their denominator is zero.

## 5. Check D — stability

Run each question three times with identical inputs and temperature 0. Keep all three
raw run records. Temperature 0 does not guarantee identical outputs.

For a question with three recorded runs:

- Outcome is stable if all three outcome strings are equal.
- A flip occurs if the three runs include both an `answered` outcome and a refused
  outcome (`refused_guard` or `abstained_model`).
- For each pair, cited-chunk-set Jaccard is intersection / union; a pair with two
  empty citation sets scores 1.0. A question's stability is the mean of its three
  pair scores, defined only when at least two of the three runs have citations.

Report stable outcomes / complete three-run question sets, mean defined Jaccard with
the number of questions contributing, and flip count / complete question sets.
Report incomplete run sets separately; they do not enter these denominators.

## 6. Run procedure and records

Run only the manifest-assigned development questions. Store one JSON file per run set
under `evaluation/experiments/end-to-end/`. Each record includes the questions file
path and SHA-256, repository identifier, repository-code commit, model names,
generation parameters, question ID and answerability, repeat index (1, 2, or 3),
outcome, submitted citations, retrieved chunk IDs and text, and the raw service result.
The raw result preserves provider retry/error details when supplied by the service.
Provider exceptions are recorded as `error` outcomes with their error class. Questions
not run (including those omitted by a trial limit) are listed with a reason.

Generate the report deterministically from the saved records; do not add the current
time unless it is explicitly supplied. Every report states record and question-set
counts, skipped questions, incomplete sets, and provider/degraded errors. No retry,
skipped question, or provider error may be silently dropped.

## 7. Deviations

As in protocol 16, any later change to this protocol is a disclosed amendment. Do not
silently change definitions after observing results.
