# Offline Retrieval Evaluation

Run the retrieval-only evaluation and save its JSON report with:

```powershell
.\.venv\Scripts\python.exe -m scripts.run_retrieval_eval --out evaluation/results/offline-baseline.json
```

It uses the committed retrieval fixture and golden-set question embeddings; it makes no provider
calls and needs no API key. Rebuild the fixture with
`.\.venv\Scripts\python.exe -m evaluation.build_fixture` after the local evaluation repository
and every golden-question embedding are available. Fixture construction reads the database and
`evaluation/cache` only.

Substring labels remain in the golden set. Derived span labels record the first case-insensitive
occurrence as an inclusive, one-based source line range from the pinned commit. A retrieved chunk
matches a span when it overlaps the labeled range in the same file. This makes retrieval labels
less dependent on chunk boundaries.

Hit-rate intervals are Wilson 95% intervals. Paired report comparisons use the exact two-sided
sign test over per-question hits, excluding ties. The initial fixture and report are
`evaluation/fixtures/retrieval_fixture.json.gz` and
`evaluation/results/offline-baseline.json`; they represent the baseline 60/10 chunking at fixture
build time.

Limits: the golden set has 24 questions from one repository and remains marked “pending maintainer
review.” The offline result is a retrieval-only diagnostic, not answer-quality or general
throughput evidence. The committed baseline run produced substring and span Hit@1/3/5 of 8/16,
11/16, and 11/16, respectively, with MRR 0.573 for each label type.

## Manifest-driven retrieval gate

The retrieval fixture, questions, full baseline, and full gate are selected and hash-checked
through [the evaluation manifest](../../evaluation/manifest.json). For the fixed smoke subset,
run:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_retrieval_gate --split smoke
```

The gate evaluates every selected repository separately, then prints pooled Hit@1/3/5 and MRR
with denominators and Wilson intervals. Missing or invalid inputs fail the selected repository;
the overall gate fails if any selected repository fails or is absent, and pooled output is not
calculated from an incomplete selection. The fixed smoke subset has a separate baseline and
tolerance in its manifest-referenced smoke gate. The full gate compares Hit@5 successes and MRR
against each repository's full baseline. Retrieval on the committed fixture is deterministic, so
any drop is a real change; changing a tolerance or baseline requires a reviewed PR.

## Ordering ties and determinism

The hybrid search previously formed candidates from a set of database-generated chunk IDs, while
vector and full-text SQL left equal-score ordering unspecified. This allowed tied results to move
between runs. Item 13d orders SQL ties by file and line coordinates, then applies explicit RRF,
source-rank and coordinate tie-breaks without using chunk IDs.

Twenty S0 runs per repository and split were measured before and after the change. Every measured
repository/split had one distinct `(Hit@5, MRR)` outcome at each stage, and no question rank varied
within those 20-run batches.

| Repository | Split | Before: distinct outcome | After: distinct outcome | Question ranks varying within runs |
|---|---|---|---|---|
| incidentweave | development | 1 (7/11, 0.515152) | 1 (7/11, 0.515152) | none |
| incidentweave | smoke | 1 (4/5, 0.533333) | 1 (4/5, 0.533333) | none |
| batch-processing-service | development | 1 (9/11, 0.666667) | 1 (10/11, 0.684848) | none |
| batch-processing-service | smoke | 1 (4/5, 0.700000) | 1 (5/5, 0.740000) | none |
| lifeos | development | 1 (11/11, 0.821212) | 1 (11/11, 0.821212) | none |
| lifeos | smoke | 1 (5/5, 0.900000) | 1 (5/5, 0.900000) | none |

For batch-processing-service smoke, `direct-02` moved from a miss to rank 5; the other four
answerable question ranks did not change. Its full baseline also changed: substring Hit@5/MRR
went from 13/16 and 0.625000 to 14/16 and 0.637500; span Hit@5/MRR went from 14/16 and 0.640625
to 15/16 and 0.653125. The batch-processing-service full and smoke aggregate baselines, gates and
manifest pins were regenerated; all other baseline sets remain unchanged.

The full re-check used aggregates only. Item 3b's held-out independence is unchanged because the
committed baselines already contained these held-out outcomes; none were used for a design or
threshold decision. Results recorded before item 13d could vary slightly when scores tied; see
[item 13d in the fix checklist](../architecture-review/03-fix-checklist.md).

Use `--repo ID` to select one repository or `--split all` to run the full question sets. For the
split model, held-out protections, authoring protocol, and the limits of the small sample sizes,
see [the multi-repository evaluation note](./05-multi-repo-evaluation.md).

Evaluation generations now use temperature 0, and run metadata records
`temperature=0; responseMimeType=application/json; response schema + prompt version grounded-v3`.
Earlier recorded runs used the provider default, so they are not directly comparable. The gate
protects retrieval only, not generation or answer quality. The current manifest contains only
IncidentWeave, with 24 questions whose labels remain pending maintainer review; its fixture
reflects 60/10 chunking at build time.
