# Later Optimizations and Follow-up Notes

This file tracks issues and improvements that are valid, useful, and worth doing later, but are not required for the current phase to function correctly.

## 1) Noisy repository ingestion filtering

### Summary
This is a general follow-up for ingestion of arbitrary repositories, including non-Python repositories. Generated, vendored, or third-party source can dilute retrieval quality, but the specific directories to exclude depend on the repository's languages and tooling.

### Scope and provenance
This note was added after testing broad investigation questions against the separately ingested `dexterai` repository, where retrieval produced weak or insufficient project-level evidence. The observed results did not establish that any particular directory caused the retrieval behavior. IncidentWeave's current ingester only indexes `*.py` files, so these JavaScript-oriented examples are not claims about noise in IncidentWeave's own indexed corpus.

### Observed pattern
When a repository has weak retrieval quality, the system correctly refuses to guess. The failure mode is usually:
- `Cited chunks: []`
- `Diagnosis: INSUFFICIENT_EVIDENCE`
- low confidence

This does not indicate a bug in the core investigation pipeline; it indicates the indexed repo content is noisy or not well filtered.

### Recommended later work
- When ingestion is broadened beyond Python files, consider filtering generated or dependency directories appropriate to each repository's ecosystem. Examples for JavaScript/Node.js repositories include:
  - `node_modules`
  - `dist`
  - `build`
  - `vendor`
  - `.next`
  - `.cache`
  - `coverage`
- For Python repositories, evaluate relevant generated, vendored, or dependency directories based on actual corpus and retrieval evidence rather than applying the JavaScript list.
- Consider a repository-specific allowlist/denylist policy for large external dependencies.
- Re-ingest noisy repos after filtering and re-test project-level questions.

## 2) Repo-level question quality improvements

### Summary
Broad questions like “what does this project do?” are often too high-level for a repository that does not contain a clear README, entrypoint, or app structure in the indexed evidence.

### Recommended later work
- Prefer queries about concrete evidence sources:
  - main entry point
  - startup files
  - root config files
  - build scripts
  - package manifests
  - module structure
- Improve retrieval by excluding generated and dependency-heavy folders before indexing.

## 3) Citation matching robustness

### Summary
The parser currently matches citations by file path + line range when the model emits prose references, which prevents false negatives from natural-language evidence references.

### Status
This is already implemented in the current parser and validated with a live Gemini response.

## 4) Phase discipline

### Summary
This project explicitly separates core functionality from later optimization work. If a branch or issue is not required to complete the current phase, it should be documented here rather than mixed into the implementation work itself.

### Rule
When a problem is caused by noisy data, generated dependencies, or repo quality rather than a bug in the investigation engine, log it here and continue the phase work without widening scope.

---

This file is intentionally a holding area for improvement work that should be revisited later once the core implementation is complete and verified.
