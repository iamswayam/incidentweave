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

Use `--repo ID` to select one repository or `--split all` to run the full question sets. For the
split model, held-out protections, authoring protocol, and the limits of the small sample sizes,
see [the multi-repository evaluation note](./05-multi-repo-evaluation.md).

Evaluation generations now use temperature 0, and run metadata records
`temperature=0; responseMimeType=application/json; response schema + prompt version grounded-v3`.
Earlier recorded runs used the provider default, so they are not directly comparable. The gate
protects retrieval only, not generation or answer quality. The current manifest contains only
IncidentWeave, with 24 questions whose labels remain pending maintainer review; its fixture
reflects 60/10 chunking at build time.
