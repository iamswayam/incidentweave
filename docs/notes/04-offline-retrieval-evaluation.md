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

## CI retrieval gate

Run the gate locally with:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_retrieval_gate
```

It reruns offline retrieval on the committed fixture and compares Hit@5 successes and MRR for
substring labels and spans against [evaluation/gate.json](../../evaluation/gate.json). The
configured maximum drops are zero Hit@5 successes and 0.02 MRR. A failure means retrieval on this
fixture fell below its allowed baseline. Retrieval on the committed fixture is deterministic, so
any drop is a real change; changing the tolerance or baseline requires a reviewed PR.

Evaluation generations now use temperature 0, and run metadata records
`temperature=0; responseMimeType=application/json; response schema + prompt version grounded-v3`.
Earlier recorded runs used the provider default, so they are not directly comparable. The gate
protects retrieval only, not generation or answer quality. Its limits remain 24 questions, one
repository, labels pending maintainer review, and a fixture reflecting 60/10 chunking at build
time.
