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
