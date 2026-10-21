# Manual Verification and Improvements

This log records behavior manually tested against IncidentWeave and improvement scope grounded in those observations. A single spot check is not a measure of overall accuracy; keep observed output, independent verification, and proposed work distinct.

## Manual Verification

### 2026-09-30 — Chunk-size investigation (Investigation 25)

- **Verified by:** Swayam (manual source check).
- **Environment:** Local API, repository `incidentweave-local`.
- **Input:** `What chunk size does repository ingestion use?`
- **Observed result:** HTTP `200`; diagnosis: “Repository ingestion uses a default chunk size of 60 lines (defined by `CHUNK_SIZE = 60` in `scripts/ingest_repo.py`).” The response reported confidence `medium`, raw confidence `high`, RRF score `0.01639344262295082`, vector score `0.319359047097336`, and cited chunks `1334`, `1333`, and `1335`.
- **Independent check:** The cited chunks were verified in the local database as rows from `scripts/ingest_repo.py`. The source defines `CHUNK_SIZE = 60` and `OVERLAP_SIZE = 10`.
- **Assessment:** The 60-line chunk-size claim was correct, but the answer omitted the related 10-line overlap setting. The `medium` confidence resulted from calibration thresholds; it did not mean the checked chunk-size claim was wrong.
- **Limits:** This is one manually reviewed answer, not a measurement of overall answer accuracy.

### 2026-09-30 — Overlap-size investigation (Investigation 26)

- **Run:** Live authenticated `POST /investigations` against `incidentweave-local` with query `What is the default overlap size for repository chunking?` and limit `5`.
- **Observed result:** HTTP `200`; diagnosis: “The default overlap size for repository chunking is 10 lines (defined by `OVERLAP_SIZE = 10` in `scripts/ingest_repo.py`).” The response reported confidence `medium`, raw confidence `high`, RRF score `0.01639344262295082`, vector score `0.3105875108084195`, latency `1587 ms`, and cited chunks `1334`, `1333`, and `1335`. It used one initial hybrid-search attempt with no retry.
- **Persistence check:** `GET /investigations/26` returned HTTP `200` with the same diagnosis, citations, and evidence scores.
- **Independent check:** A database query confirmed all three cited rows point to `scripts/ingest_repo.py`; chunk `1333` (lines 1–60) contains `OVERLAP_SIZE = 10` and the default `chunk_lines` argument.
- **Human review:** Not yet independently reviewed by Swayam.
- **Assessment:** The answer correctly reported the requested overlap size and cited source chunks containing its definition.
- **Limits:** This is one assistant-run live check and does not establish overall answer accuracy.

### 2026-09-30 — Chunk-step investigation (Investigation 27)

- **Run:** Swayam's live Swagger test against `incidentweave-local` with query `How many lines does ingestion advance between chunks, and how is that step calculated?` and limit `5`.
- **Observed result:** The supplied response stated `step = chunk_size - overlap`, with defaults `60` and `10`, and said the step increments `range(0, len(lines), step)`. It reported confidence `medium`, raw confidence `high`, RRF score `0.01639344262295082`, vector score `0.3347928364539068`, latency `1901 ms`, and cited chunks `1334`, `1333`, and `1335`. The trace showed one initial hybrid-search attempt and no retry.
- **Independent check:** The cited database rows point to `scripts/ingest_repo.py`. Chunk `1333` contains the `60` and `10` defaults; chunks `1333` and `1334` contain `step = chunk_size - overlap` and `range(0, len(lines), step)`. The default advance is therefore `60 - 10 = 50` lines.
- **Assessment:** The formula and default values are correct, so the answer implies a 50-line advance. It would be clearer to state `50 lines` explicitly.
- **Limits:** This is one manually run and reviewed question, not a measure of overall answer accuracy.

## Improvement Scope

### Include closely related settings in answers

- **Evidence:** Investigation 25 correctly reported `CHUNK_SIZE = 60` but omitted `OVERLAP_SIZE = 10`, even though both configure chunking in the same source file.
- **Observed gap:** A narrow question received a correct but incomplete answer about the behavior.
- **Proposed improvement:** Evaluate whether answers to configuration questions include closely related settings needed to describe that behavior accurately.
- **Acceptance check:** Use human-reviewed cases that specify expected related settings; verify each required setting appears in the answer and is supported by cited source evidence.
- **Status:** Proposed; no code or prompt changes have been made for this observation.