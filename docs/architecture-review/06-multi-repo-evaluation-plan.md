# 06 Multi-repo evaluation plan

## 1. Proposed plan (author: Claude)

Context: the evaluation set today is 24 questions on one repo (incidentweave). We want to measure generalisation across codebases and make chunking and guard experiments trustworthy.
D1 Three Python repos: incidentweave plus two more, chosen from the maintainer's public repos (or third-party if none qualifies; selection pending maintainer input). A non-Python repo is a later, separate language-generalisation step (tree-sitter).
D2 One manifest lists, per repo: URL, pinned commit SHA, licence, questions file, offline fixture, baseline.
D3 24 questions per repo, 72 in total; 16 answerable and 8 unanswerable per repo.
D4 Per repo: 16 development questions (11 answerable, 5 unanswerable) and 8 held-out questions (5 answerable, 3 unanswerable). The held-out split is frozen before any chunking or threshold experiment and is never tuned on. The incidentweave split is retroactive, because those questions were already seen during development, and is flagged as such.
D5 A fixed smoke subset of 8 questions per repo (24 in total; 5 answerable, 3 unanswerable each), drawn from the development questions only so the held-out split stays untouched. The full 72 run before merging retrieval or answer changes.
D6 Unanswerable questions must be plausible but absent from the repo. The maintainer writes or approves every question; questions are written before looking at retrieval results.
D7 Reports show each repo separately and pooled, with Wilson intervals; before/after comparisons use the pooled exact sign test. The headline generalisation claim uses only held-out questions from the two new repos (16 questions) and states n. At n=16 only large effects are detectable; reports must say so.
D8 The CI gate keeps one baseline per repo; a drop on any repo fails it.
D9 Item 16 is split into 16a (generalise the harness: manifest, tags, per-repo and pooled reports, smoke and held-out selection, per-repo gate; code only), 16b (repo 2: questions, fixture, baseline), 16c (repo 3). Afterwards 17, 3b, 14.
D10 Item 15a (AST function-aware chunking) starts after 16a and 16b are merged and is evaluated on both repos; 16c may run in parallel.
Repo selection criteria: public GitHub; Python; different domain from the other repos; at least about 1,500 lines of source plus a README; no secrets in files or history (the secret scanner still runs because content is sent to the embedding API); pinned SHA. Maintainer-owned repos are acceptable and give label authority and low training-data contamination, but three repos by one author is a weaker independence claim than third-party repos; reports must say so. If no owned repo qualifies, a lesser-known third-party repo with an MIT/Apache/BSD licence is used.
Order: 16a, 16b, 15a (16c in parallel), 17, 3b, 14.

## 2. Codex review

### Review basis

This review inspected `main` after merge commit `c1faddb`. The offline path is currently single-repository: `evaluation/golden.py` requires exactly 8 direct, 8 paraphrased, 4 far-unanswerable and 4 near-unanswerable questions; `evaluation/build_fixture.py`, `evaluation/retrieval_eval.py`, and `scripts/check_retrieval_gate.py` use one fixed golden set, fixture, fixture repository and gate; and `evaluation/chunk_experiments.py` allowlists only two IncidentWeave evaluation repositories. The fixture writer already rejects compressed fixtures of 1.5 MiB or more. These are source observations, not a live multi-repo run.

| Item | Verdict | Review and exact amendment where needed |
|---|---|---|
| D1 | AGREE | Three Python repositories are a coherent first external-replication step. Language generalisation must wait for separate parser support and evaluation. |
| D2 | AMEND | Replace D2 with: “One versioned manifest lists, per repository: stable ID, URL, pinned commit SHA, licence and licence check date, source-size measurement, question file and SHA-256, split assignments, fixture and its SHA-256/size, baseline and its SHA-256, embedding/chunker versions, and the gate command. The harness rejects a missing or mismatched manifest entry.” |
| D3 | AGREE | 24 questions per repository is feasible and balanced for a first replication, if results retain per-repository denominators and are not presented as precise estimates. |
| D4 | AMEND | Replace its split sentence with: “The held-out split is stratified by answerability and question type, assigned and committed before any retrieval, threshold, chunking, or generation experiment is examined, and is never used to choose a design or threshold. The IncidentWeave split is retroactive and is reported separately as previously exposed, not as independent held-out evidence.” Current validation has categories but no split field. |
| D5 | AMEND | Replace D5 with: “A fixed, stratified smoke subset of 8 questions per repository (24 total; 5 answerable, 3 unanswerable each) is selected from development questions only. It has its own reviewed baseline and is used only for regression detection, never to select a threshold, chunker, or retrieval policy. The full 72-question run is required before merging any retrieval or answer change; held-out results are reported but not used for selection.” |
| D6 | AMEND | Append: “A second maintainer reviewer approves wording, answer labels/spans, and the absent-term check against the full pinned tree. Question wording is frozen before retrieval results are viewed; source inspection needed to create labels is recorded separately from retrieval-result inspection.” The current validator scans absence only in `*.py`. |
| D7 | AMEND | Replace D7 with: “Reports show each repository separately and pooled, with Wilson intervals and denominators. A preregistered paired binary endpoint may use a two-sided exact sign test over discordant pairs; reports state wins, losses, ties, and the number of discordant pairs. The headline is an external-replication result for the two named new repositories’ 16 held-out questions, not a general claim about arbitrary codebases or languages; it states both 16 question-level observations and two repository-level observations.” |
| D8 | AMEND | Replace D8 with: “CI runs one fixed smoke fixture and reviewed baseline per manifest repository and fails closed if any required fixture, baseline, manifest hash, or result is missing or mismatched; a drop on any repository fails the gate. Rebuilding a fixture or baseline is a reviewed full-evaluation operation, not a CI side effect.” The current committed fixture cannot itself expose a changed chunker. |
| D9 | AMEND | Replace its end with: “16a is code and synthetic/unit-test fixtures only; it must add manifest validation, split validation, explicit repository selection, per-repository and pooled reporting, smoke/held-out selection, and a fail-closed per-repository gate. 16b adds the first new repository’s approved questions, pinned source snapshot, offline fixture and baseline; 16c adds the second. Item 17, threshold re-validation 3b, and item 14 follow completion of 16b and 16c.” |
| D10 | AMEND | Replace D10 with: “Item 15a starts after 16a and 16b are merged. Its design choices are selected using development results on IncidentWeave and repository 2; the frozen held-out split is evaluated only after a choice is fixed. Item 16c may run in parallel, but its results are not used to revise the selected 15a design.” |
| Selection criteria | AMEND | Replace the secret/licence clause with: “At the pinned commit, record the licence file and source-size method; exclude vendored/generated code from the 1,500-source-line threshold. Before embedding, the maintainer records authority to submit the repository to the provider, and checks current files with the project secret scanner plus GitHub secret-scanning/maintainer history review where available. These checks reduce risk; they do not prove that no secret ever existed in history.” |

### a) Size, split, smoke, and statistical limits

The allocation is a sound small regression suite, not confirmatory evidence of broad generalisation. It preserves answerable and unanswerable coverage and bounds CI work. It cannot precisely estimate per-repository performance, establish a small effect, calibrate a threshold safely from repeated smoke results, or support a language-generalisation claim.

Wilson examples show the uncertainty: 11/16 has a 95% interval of 44.4% to 85.8%; 15/16 is 72.0% to 98.9%. At the eight-question smoke scale, 4/8 is 21.5% to 78.5% and even 7/8 is 52.9% to 97.8%.

For a two-sided exact sign test at alpha 0.05 with 72 independent discordant pairs, at least 45 wins (or losses) are required; the exact two-sided null probability at that boundary is about 0.044. With probabilities of winning a discordant pair of 0.55, 0.60, 0.65, and 0.70, approximate power is 12%, 38%, 72%, and 93%. This assumes all pairs are discordant and independent. Ties and within-repository correlation reduce effective evidence; pooled question statistics do not create 72 independent codebases.

### b) Leakage and contamination risks

- A development smoke subset run repeatedly leaks if used for design selection; lock it to regression detection.
- Repeated tuning on remaining development questions can overfit. Record candidates, selection rule and number of looks, then freeze a choice before held-out reporting.
- A writer who sees source or earlier output can make retrieval-friendly wording or labels. Separate wording review, source/label review and retrieval-result inspection.
- IncidentWeave questions were already exposed; never put their retroactive held-out split in an independent-held-out headline.
- Same-author repositories share habits and documentation style. They support replication across selected repositories, not independence from author style or model training contamination.
- Public source may be in training data. Record this residual risk; the plan cannot measure it directly.
- Cached embeddings, fixtures and baselines are inputs too: hash them and reject a mismatched pin/fixture/question combination.

### c) Item split, order, and concrete 16a code scope

The amended 16a/16b/16c split is correct. It establishes a data contract before a second corpus, makes 15a meaningful on two repositories, and permits 16c to proceed independently. Item 15a selects on development data only; 3b waits for both new repositories.

16a must generalise:

- `evaluation/golden.py`: exact category counts, one review-status value, prior-question markers, file-distribution caps and validation need manifest-driven, split-aware rules.
- `evaluation/chunk_experiments.py` and `evaluation/runner.py`: strategies are tied to allowlisted IncidentWeave repositories; the runner reads one `golden_set.json`, has one cache namespace and exports one snapshot.
- `evaluation/build_fixture.py`: golden/cache/fixture paths, default strategy/repository, and one global 1.5 MiB limit are fixed; metadata needs repository ID and manifest hashes.
- `evaluation/retrieval_eval.py`: default golden/fixture paths and `incidentweave-fixture` are fixed; it needs selected manifest input and isolated fixture names.
- `evaluation/gate.json`, `evaluation/gate.py`, and `scripts/check_retrieval_gate.py`: one baseline/gate/fixture is loaded; there is no manifest iteration or missing-input failure report.
- `scripts/run_eval.py`: only passes and strategy are selectable; it needs manifest/repository/split selection and per-repository plus pooled reports.

### d) Missing operational controls

- Keep the existing fixture-size ceiling as a per-repository manifest limit, measure it in CI, and require review to change it.
- Record CI elapsed time and a maximum total budget before enabling three database-backed gates; keep the full 72 out of normal PR CI if necessary.
- Version a question-authoring protocol: task taxonomy, forbidden identifiers in paraphrases, unanswerable construction, source/absence verification, label spans, reviewer roles and changelog.
- Require second-review approval of answerable spans and unanswerable absence assertions before a dataset becomes approved; current `review_status` is only global.
- Missing fixture, baseline, cache embedding or manifest entry must fail the selected repository and overall gate; it must never skip or silently re-pool available repositories.

## 3. Resolved plan

1. Use IncidentWeave and two additional Python repositories for a first external-replication evaluation; defer language generalisation to a separate tree-sitter step.
2. Maintain a versioned manifest per repository with stable ID, URL, pinned SHA, licence/check date, source-size measurement, question file/hash, split assignments, fixture/hash/size, baseline/hash, versions and gate command; reject missing or mismatched entries. (amended by Codex review)
3. Use 24 questions per repository: 16 answerable and 8 unanswerable, 72 total.
4. Use 16 development questions (11 answerable, 5 unanswerable) and 8 held-out questions (5 answerable, 3 unanswerable) per repository. Stratify and commit the held-out split before relevant experiments; never select on it. Flag IncidentWeave as previously exposed. (amended by Codex review)
5. Select a fixed 5-answerable/3-unanswerable development smoke subset per repository, with its own baseline, for regression detection only. Run all 72 before merging retrieval/answer changes. (amended by Codex review)
6. Freeze question wording before retrieval results are viewed and require a second reviewer for wording, labels/spans and full-tree absence checks. (amended by Codex review)
7. Report per-repository and pooled intervals/denominators; use a preregistered two-sided exact sign test only for a paired binary endpoint and report discordant pairs. Describe the 16 held-out questions from two named new repositories as external replication for those repositories, not broad generalisation. (amended by Codex review)
8. Run one fixed smoke fixture/baseline per manifest repository in CI and fail closed on missing, mismatched or dropping inputs/results. Rebuild fixtures/baselines only through reviewed full evaluation. (amended by Codex review)
9. 16a provides the manifest-driven harness, validation, reporting and fail-closed gates using only code/synthetic fixtures; 16b and 16c each add one approved repository’s data. Run 17, 3b and 14 after 16b and 16c. (amended by Codex review)
10. Start 15a after 16a/16b, select it on the two repositories’ development data, and evaluate frozen held-out data only after selection. Let 16c run in parallel without using it to revise 15a. (amended by Codex review)
11. Record licence/source-size evidence, exclude vendored/generated code from the size threshold, record authority to embed the source, and use available project/GitHub secret checks as risk reduction rather than proof of a secret-free history. (amended by Codex review)

### Open decisions for the maintainer

- Which two repositories meet the amended selection criteria. Record whether each is maintainer-owned or third-party and the resulting independence/training-contamination limitation before selection.

### Order

16a, 16b, 15a (16c in parallel), 17, 3b, 14.

## 4. Checklist impact

Changed `03-fix-checklist.md` entries are: line 36 (Progress log row); lines 60-63 (summary-table 15a and 16a/16b/16c rows); lines 81-82 (recommended-order rows); line 87 (15a and 3b dependency wording); line 107 (3b dependency wording); line 192 (15a detail); and lines 196-206 (the replacement 16a, 16b and 16c details and Done-when lines).
