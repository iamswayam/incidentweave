# Evaluation dataset v2 protocol (item 29)

## 1. Purpose and registration

Register how dataset v2 is built and frozen **before writing any question for a new
repository and before scoring any system on it**.

Version 2 supports retrieval and guard-quality claims on mid-size Python service/library
repositories, with 95% intervals and stated detectable effect sizes. It does not support
claims about other languages, large monorepos, non-code artifacts (item 20), real incident
data, or answer quality (items 34 and 17).

## 2. Current state (v1)

The manifest contains three maintainer-owned repositories. Their indexed Python line counts
range from 1,303 to 2,789. Across them, v1 has 33 answerable and 15 unanswerable development
questions, and 15 answerable and 9 unanswerable held-out questions. The IncidentWeave
held-out set is marked previously exposed; see the manifest and item 14b-1. Each committed
fixture is capped at 1.5 MiB.

With 33 answerable questions, only a pooled-MRR difference of about 0.14 is detectable at
the registered approximate power assumptions below.

## 3. Targets and power

Use the approximate minimum detectable effect:

`MDE = 2.8 × SD / sqrt(n)`

Here `SD = 0.28` for paired reciprocal-rank differences, derived from the item 14d BM25
comparison interval. This is approximate; re-estimate it from pilot data.

| Set | Answerable n | Approximate MDE |
|---|---:|---:|
| v1 development | 33 | 0.14 |
| v2 development | 153 | 0.063 |
| v2 held-out | 90 | 0.083 |

For unanswerable questions, a 40% false-accept rate at n=15 has an approximate 95% Wilson
interval of 20%–64%; at n=55 the interval is about ±12 percentage points.

| Split | Composition | Total |
|---|---|---:|
| v2 development | v1: 33 answerable + 15 unanswerable; four new repositories: 30 + 10 each | 153 answerable + 55 unanswerable |
| v2 held-out | Three new repositories: 30 answerable + 10 unanswerable each | 90 answerable + 30 unanswerable |

## 4. Repositories

### Selection criteria

| Criterion | Requirement |
|---|---|
| License | OSI-permissive: MIT, BSD, or Apache-2.0 |
| Language and size | Python-majority; 5k–30k source Python lines, excluding tests, docs, and examples |
| Activity | A commit within the last 12 months |
| Issue history | At least 40 closed issues with a merged linked PR touching non-test source |
| Snapshot | Pin a 40-character commit SHA |
| Content | No generated code or secrets; English documentation |
| Domain | Held-out repository domains differ from development repository domains |

### Candidate roles

Measurements below are candidates for item 30, not final pinned-SHA counts. Re-measure at
the pinned SHA. Confirm BSD license-clause counts for `rq/rq` and `encode/uvicorn`.

| Repository | License | Source / all Python lines | Role |
|---|---|---:|---|
| `rq/rq` | BSD; clause count to confirm | 13.3k / 29.6k | Development |
| `nolar/kopf` | MIT | 18.0k / 48.4k | Development |
| `agronholm/apscheduler` | MIT | 8.7k / 13.8k | Development |
| `prometheus/client_python` | Apache-2.0 | 5.4k / 11.6k | Development |
| `locustio/locust` | MIT | 12.7k / 35.9k | Held-out |
| `docker/docker-py` | Apache-2.0 | 14.2k / 31.5k | Held-out |
| `encode/uvicorn` | BSD; clause count to confirm | 7.5k / 16.8k | Held-out |

Backups, in order: `structlog`, `huey`, `flower`, `luigi`. At item 30, replace any candidate
that fails a selection criterion with the next backup and record the swap in the data card.
The three v1 repositories remain development data, unchanged. V1 held-out questions remain
flagged exposed and are excluded from blind claims.

## 5. Questions

Each new repository contributes 30 answerable and 10 unanswerable questions.

| Source | Construction and provenance |
|---|---|
| Mined | Issue rewritten as a question; retain issue and fixing-PR references |
| Drafted | Model-drafted from documentation and behavior, then human-verified; record the drafting model |
| Human | Written by the maintainer |

At least 8 answerable questions per repository are mined and at least 8 are drafted or human.
For mined questions, the issue must have been closed by a merged PR before the pinned SHA.
Gold labels are non-test source files changed by that PR and still present at the pinned SHA;
the reviewer selects line spans at that SHA. The question must omit the gold file path and
basename. Drafted questions must not copy gold-chunk text.

Answerable types: direct lookup, paraphrase, multi-file, config/env, error message, and
how-it-works. No type exceeds 40% of a repository's questions; no file receives more than
3 questions. Each repository also has 4 far, 3 near-miss, and 3 false-premise unanswerable
questions. Verify absence by exact search at the pinned SHA and record the search.

Human-review every question. Record provenance. Include no secrets or personal data.

## 6. Quality control and pilot gate

Pilot `rq` and `kopf` with full quotas before writing questions for any other repository.
Blindly re-label a random 20% sample, at least 16 pilot questions, at least 7 days later.
Use maintainer intra-rater review or a second-person inter-rater review when available.
Measure agreement separately for gold files and answerability.

| Gate | Requirement |
|---|---|
| Agreement | At least 90% for both gold-file and answerability labels |
| Median effort | At most 8 minutes per question, including review |
| Leakage | Report rejections; no numeric pass threshold |

If median effort exceeds 8 minutes, reduce targets to 20 answerable and 8 unanswerable per
repository, then recompute the power table in the pilot results note; do not edit this
protocol. If agreement is below 90%, revise labelling guidance in the data card, relabel the
pilot, and repeat the second pass once. If agreement remains below 90%, stop and ask the
maintainer.

## 7. Splits and held-out rules

Split by repository. Every question from a development repository is development data. Keep
the CI smoke gate on the three v1 repositories.

Held-out questions are written and frozen, but no system is run on them, no baseline is made,
and no held-out fixture is built before the single registered item 3b run. Never use held-out
data to choose methods or thresholds. Record any exposure with the existing
`previously_exposed` flag; exposure ends that repository's blind status.

Report every metric pooled and per repository with 95% intervals. A difference smaller than
the detectable effect is **not detectable**, not evidence of no difference.

## 8. Layout, schema and fixtures

```text
evaluation/
├── manifest.json                 # one registry; schema_version 2 at freeze
├── cache/                        # ignored candidate pools, mined issues, downloads
└── repos/
    ├── README.md                 # data card, composition, SPDX/license attribution,
    │                             # pinned SHAs, and changelog
    └── <repo-id>/
        ├── questions.json        # v2 questions committed first
        ├── retrieval_fixture.json.gz
        ├── gate.json
        ├── smoke-gate.json
        ├── offline-baseline.json # added later by item 32
        └── smoke-baseline.json   # added later by item 32
```

Keep v1 repository files unchanged. Add per-repository `role` (`development` or
`held_out`), `license` (SPDX ID), and `fixture.location` (`committed` or `release`) to the
manifest. Optional additive question fields are `type`, `source` (`mined`, `drafted`, or
`human`), `source_ref` (issue/PR number), and `reviewed`.

Commit a fixture only when it fits the existing 1.5 MiB cap. Otherwise publish it as an
immutable `dataset-v2.0` release asset, pin its SHA-256 in the manifest, and download it into
ignored `evaluation/cache/` with existing fixture tooling. Never regenerate it silently.
Do not add top-level folders or modules. Build tooling in later items only: extend manifest
validation for v2 rules, add one candidate-mining script writing to `evaluation/cache/`, and
reuse the fixture builder.

### Implementation notes

- Current manifest validation supports only `schema_version = 1`, with v1 default counts and
  split counts. It does not validate v2 `role`, SPDX `license`, or `fixture.location`.
- `golden.py` validates the four fixed v1 categories and their v1 counts. It does not yet
  validate the optional v2 provenance fields or the v2 question types and source quotas.
- Current `golden.py` and manifest validation default to at most 3 questions per file;
  the v1 manifest has a repository-specific override of 5 for batch-processing-service.
  V2 applies the registered limit of 3.
- The fixture validator checks each fixture against manifest `max_bytes`; the current
  builder uses the existing 1.5 MiB cap. Release-asset download and cache handling are not
  implemented in the current validator or fixture builder.
- `splits.py` assigns stratified splits within a repository; v2 instead assigns splits by
  repository role. Keep the requested v2 rule and implement the role-based behavior in
  item 30.

## 9. Freeze, versioning and changelog

At freeze, set manifest `dataset_version` to `2.0`. Freeze only after development and
held-out questions are committed, validation passes, the data card is complete, and all
section 6 gates pass.

After freeze, make no silent edits. A correction creates dataset version 2.x, adds a
changelog entry, and re-establishes baselines. Tie every result to the dataset version that
produced it.

## 10. Decision rules

| Area | Registered threshold or quota |
|---|---|
| Power | 80%; two-sided 5%; approximate `MDE = 2.8 × 0.28 / sqrt(n)`; re-estimate from pilot |
| Repository | OSI-permissive MIT/BSD/Apache-2.0; Python-majority; 5k–30k source Python lines; commit within 12 months; at least 40 qualifying closed issues; 40-character SHA |
| Dataset size | Development: 153 answerable + 55 unanswerable; held-out: 90 answerable + 30 unanswerable |
| Question quota | 30 answerable + 10 unanswerable per new repository |
| Answerable provenance | At least 8 mined and at least 8 drafted-or-human per repository |
| Answerable types | Six registered types; each at most 40% per repository |
| File concentration | At most 3 questions per file |
| Unanswerable composition | 4 far + 3 near-miss + 3 false-premise per repository |
| Review and privacy | 100% human-reviewed; provenance recorded; zero secrets or personal data |
| Pilot | `rq` and `kopf`, full quotas, before other new-repository questions |
| Second pass | Random 20%; at least 16 pilot questions; blind; at least 7 days later |
| Quality gate | At least 90% agreement for gold files and answerability; median effort at most 8 minutes/question |
| Low-effort fallback | If median effort exceeds 8 minutes: 20 answerable + 8 unanswerable per repository; recompute power in pilot note |
| Agreement recovery | Revise and repeat one second pass; if still below 90%, stop and ask maintainer |
| Held-out use | One registered run allowed; none before item 3b; never for method or threshold selection |
| Unanswerable uncertainty | At n=15, 40% false accepts gives about 20%–64% Wilson 95% interval; at n=55, about ±12 points |
| Fixture size | 1.5 MiB committed limit; larger fixture only as immutable `dataset-v2.0` release asset with SHA-256 pin |
| Reporting | Pooled and per-repository metrics with 95% intervals; below-MDE differences reported as “not detectable” |

## 11. Limits

The sample remains small. Labels may have only one maintainer annotator. Mined labels are
file-level and approximate. Well-known repositories may be memorized by models; generation
metrics need a closed-book baseline (item 34). The dataset is Python-only and uses static
snapshots.
