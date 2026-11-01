# Documentation status index

**As of 2026-11-02.**

This is the single cross-folder status index for tracked Markdown under `docs/`. Folder
README files remain navigation indexes. The [scripts catalog](../scripts/README.md) covers
operational and evaluation commands.

## Status rules

- **Frozen** documents are immutable; record corrections in a living reference rather than
  editing the original.
- A new registered experiment adds its protocol and results note and one row in the
  [Experiments table](#experiments).
- **Living** documents carry an as-of date. Their last-verified date below records the latest
  source or command check made for this index.
- **Draft** marks work in progress. **Superseded** means the named replacement is now the
  navigation or behavioral source of truth.

## Documents

| Path | Title | Kind | Status | Superseded-by | Last verified |
|---|---|---|---|---|---|
| [README.md](README.md) | Documentation status index | living reference | Living | — | 2026-11-02 |
| [architecture/README.md](architecture/README.md) | Architecture | living reference | Living | — | 2026-11-01 |
| [architecture/01-architecture-overview.md](architecture/01-architecture-overview.md) | IncidentWeave Architecture | living reference | Living | — | 2026-11-01 |
| [architecture/02-high-level-design.md](architecture/02-high-level-design.md) | IncidentWeave High-Level Design | living reference | Living | — | 2026-11-01 |
| [architecture/03-low-level-design.md](architecture/03-low-level-design.md) | IncidentWeave Low-Level Design | living reference | Living | — | 2026-11-01 |
| [architecture/04-threat-model.md](architecture/04-threat-model.md) | Threat Model | living reference | Living | — | 2026-11-01 |
| [architecture-review/README.md](architecture-review/README.md) | Architecture review | living reference | Living | — | 2026-11-01 |
| [architecture-review/01-audit-claude.md](architecture-review/01-audit-claude.md) | Independent Engineering Audit & AI Market Assessment: IncidentWeave | audit or review | Frozen | — | — |
| [architecture-review/02-audit-codex.md](architecture-review/02-audit-codex.md) | IncidentWeave: Independent Engineering Audit and October 2026 Market Assessment | audit or review | Frozen | — | — |
| [architecture-review/03-fix-checklist.md](architecture-review/03-fix-checklist.md) | IncidentWeave: Prioritized Fix Checklist | living reference | Living | — | 2026-11-02 |
| [architecture-review/04-fix-checklist-review-codex.md](architecture-review/04-fix-checklist-review-codex.md) | Independent review: fix checklist | audit or review | Frozen | — | — |
| [architecture-review/05-implementation-workflow.md](architecture-review/05-implementation-workflow.md) | Implementation workflow | how-to | Living | — | 2026-11-01 |
| [architecture-review/06-multi-repo-evaluation-plan.md](architecture-review/06-multi-repo-evaluation-plan.md) | Multi-repo evaluation plan | protocol | Living | — | 2026-11-01 |
| [architecture-review/07-chunking-comparison-plan.md](architecture-review/07-chunking-comparison-plan.md) | Chunking comparison plan | protocol | Living | — | 2026-11-01 |
| [architecture-review/08-retrieval-ablation-protocol.md](architecture-review/08-retrieval-ablation-protocol.md) | Retrieval ablation protocol (item 14) | protocol | Frozen | — | — |
| [architecture-review/09-llm-gateway-decision.md](architecture-review/09-llm-gateway-decision.md) | LLM gateway decision (item 18) | decision record | Living | — | 2026-11-01 |
| [architecture-review/10-llm-gateway-design.md](architecture-review/10-llm-gateway-design.md) | Provider layer design (item 18a-1) | decision record | Living | — | 2026-11-01 |
| [architecture-review/11-test-file-retrieval-protocol.md](architecture-review/11-test-file-retrieval-protocol.md) | Test-file retrieval protocol (item 14b) | protocol | Frozen | — | — |
| [architecture-review/12-bm25-comparison-protocol.md](architecture-review/12-bm25-comparison-protocol.md) | BM25 comparison protocol (item 14d) | protocol | Frozen | — | — |
| [architecture-review/13-degraded-response-design.md](architecture-review/13-degraded-response-design.md) | Degraded response design (item 18d-1) | decision record | Frozen | — | — |
| [architecture-review/14-local-embedding-protocol.md](architecture-review/14-local-embedding-protocol.md) | Local embedding-model comparison protocol (item 18c) | protocol | Frozen | — | — |
| [chunking-experiment/README.md](chunking-experiment/README.md) | Chunking experiment | living reference | Living | — | 2026-11-01 |
| [chunking-experiment/01-experiment-log.md](chunking-experiment/01-experiment-log.md) | IncidentWeave: Chunking Strategy Discussion Log | results | Frozen | — | — |
| [chunking-experiment/02-decision-report.md](chunking-experiment/02-decision-report.md) | Chunking Strategy Experiment: Decision Report | results | Frozen | — | — |
| [chunking-experiment/03-human-review-workbook.md](chunking-experiment/03-human-review-workbook.md) | Chunking Experiment: Human Review Workbook | audit or review | Frozen | — | — |
| [chunking-experiment/04-review-claude.md](chunking-experiment/04-review-claude.md) | Gate 5 Review — Claude | audit or review | Frozen | — | — |
| [chunking-experiment/05-review-copilot.md](chunking-experiment/05-review-copilot.md) | Gate 5 independent review — Copilot | audit or review | Frozen | — | — |
| [chunking-experiment/06-review-chatgpt.md](chunking-experiment/06-review-chatgpt.md) | Gate 5 Independent Review — ChatGPT | audit or review | Frozen | — | — |
| [learning/README.md](learning/README.md) | IncidentWeave — Learning Log | living reference | Living | — | 2026-11-01 |
| [learning/00-template.md](learning/00-template.md) | \<Topic Name> | how-to | Draft | — | — |
| [learning/01-project-setup.md](learning/01-project-setup.md) | Project Setup (Phase 1) | learning guide | Frozen | — | — |
| [learning/02-database-persistence.md](learning/02-database-persistence.md) | Database & Persistence (Phase 2) | learning guide | Frozen | — | — |
| [learning/03-ingestion-chunking.md](learning/03-ingestion-chunking.md) | Ingestion & Chunking (Phase 3) | learning guide | Frozen | — | — |
| [learning/04-embeddings-retrieval.md](learning/04-embeddings-retrieval.md) | Embeddings & Hybrid Retrieval (Phase 4) | learning guide | Frozen | — | — |
| [learning/05-investigation-engine.md](learning/05-investigation-engine.md) | Investigation Engine (Phase 5) | learning guide | Frozen | — | — |
| [learning/06-langgraph-agent.md](learning/06-langgraph-agent.md) | Grounding & Confidence with LangGraph (Phase 6) | learning guide | Frozen | — | — |
| [learning/07-mcp-integration.md](learning/07-mcp-integration.md) | Controlled Tools & Audit (Phase 7) | learning guide | Frozen | — | — |
| [learning/08-evaluation.md](learning/08-evaluation.md) | Evaluation (Phase 8) | learning guide | Frozen | — | — |
| [learning/09-production-api.md](learning/09-production-api.md) | Production CLI / API (Phase 9) | learning guide | Frozen | — | — |
| [notes/README.md](notes/README.md) | Notes | living reference | Living | — | 2026-11-01 |
| [notes/01-manual-verification.md](notes/01-manual-verification.md) | Manual Verification and Improvements | note | Frozen | — | — |
| [notes/02-deferred-optimizations.md](notes/02-deferred-optimizations.md) | Later Optimizations and Follow-up Notes | note | Living | — | 2026-11-01 |
| [notes/03-embedding-benchmark.md](notes/03-embedding-benchmark.md) | Embedding Benchmark | results | Frozen | — | — |
| [notes/04-offline-retrieval-evaluation.md](notes/04-offline-retrieval-evaluation.md) | Offline Retrieval Evaluation | results | Frozen | — | — |
| [notes/05-multi-repo-evaluation.md](notes/05-multi-repo-evaluation.md) | Multi-Repository Evaluation | results | Frozen | — | — |
| [notes/06-chunking-strategies.md](notes/06-chunking-strategies.md) | Chunking strategies | living reference | Living | — | 2026-11-01 |
| [notes/07-retrieval-inspection-report.md](notes/07-retrieval-inspection-report.md) | Retrieval inspection report | results | Frozen | — | — |
| [notes/08-fulltext-diagnostic.md](notes/08-fulltext-diagnostic.md) | Full-text diagnostic (item 14c-1) | audit or review | Frozen | — | — |
| [notes/09-fulltext-ablation-results.md](notes/09-fulltext-ablation-results.md) | Full-text ablation results (item 14c-2) | results | Frozen | — | — |
| [notes/10-provider-usage-log.md](notes/10-provider-usage-log.md) | Provider Usage Log | living reference | Living | — | 2026-11-01 |
| [notes/11-test-file-diagnostic.md](notes/11-test-file-diagnostic.md) | Test-file retrieval diagnostic | audit or review | Frozen | — | — |
| [notes/12-test-file-comparison-results.md](notes/12-test-file-comparison-results.md) | Test-file retrieval comparison results | results | Frozen | — | — |
| [notes/13-groq-generation-fallback.md](notes/13-groq-generation-fallback.md) | Optional Groq Generation Fallback | how-to | Living | — | 2026-11-01 |
| [notes/14-embedding-task-type-experiment.md](notes/14-embedding-task-type-experiment.md) | Embedding task-type comparison (item 14a) | protocol | Frozen | — | — |
| [notes/15-embedding-task-type-results.md](notes/15-embedding-task-type-results.md) | Embedding task-type comparison: development | results | Frozen | — | — |
| [notes/16-test-tiers.md](notes/16-test-tiers.md) | Test tiers and scaling | how-to | Living | — | 2026-11-01 |
| [notes/17-bm25-comparison-results.md](notes/17-bm25-comparison-results.md) | BM25 comparison results (item 14d) | results | Frozen | — | — |
| [notes/18-local-embedding-results.md](notes/18-local-embedding-results.md) | Local embedding-model comparison results | results | Frozen | — | — |
| [notes/19-repository-inventory.md](notes/19-repository-inventory.md) | Repository inventory | note | Superseded | docs/README.md | — |
| [phases/README.md](phases/README.md) | Phase build logs | living reference | Living | — | 2026-11-01 |
| [phases/01-project-setup.md](phases/01-project-setup.md) | Phase 1 — Project Setup | phase log | Frozen | — | — |
| [phases/02-database-persistence.md](phases/02-database-persistence.md) | Phase 2 — Database & Persistence | phase log | Frozen | — | — |
| [phases/03-ingestion-chunking.md](phases/03-ingestion-chunking.md) | Phase 3 — Repository Ingestion & Chunking | phase log | Frozen | — | — |
| [phases/04-embeddings-retrieval.md](phases/04-embeddings-retrieval.md) | Phase 4 — Embeddings & Retrieval | phase log | Frozen | — | — |
| [phases/05-investigation-engine.md](phases/05-investigation-engine.md) | Phase 5 — Investigation Engine | phase log | Frozen | — | — |
| [phases/06-grounding-confidence.md](phases/06-grounding-confidence.md) | Phase 6 — Grounding & Confidence | phase log | Frozen | — | — |
| [phases/07-controlled-tools-audit.md](phases/07-controlled-tools-audit.md) | Phase 7 — Controlled Tools & Audit | phase log | Frozen | — | — |
| [phases/08-evaluation.md](phases/08-evaluation.md) | Phase 8 — Evaluation | phase log | Frozen | — | — |
| [phases/08b-evaluation-improvements.md](phases/08b-evaluation-improvements.md) | Phase 8b — Evaluation Improvements | phase log | Frozen | — | — |
| [phases/09-production-api.md](phases/09-production-api.md) | Phase 9 — Production CLI / API | phase log | Frozen | — | — |
| [runbooks/README.md](runbooks/README.md) | Runbooks | living reference | Living | — | 2026-11-01 |
| [runbooks/degraded-modes-and-cache.md](runbooks/degraded-modes-and-cache.md) | Degraded modes and query-embedding cache | how-to | Living | — | 2026-11-01 |
| [reference/README.md](reference/README.md) | Generated API reference | living reference | Living | — | 2026-11-01 |

## Experiments

| Experiment | Protocol | Results note | Aggregate JSON | Runner | Outcome |
|---|---|---|---|---|---|
| Chunking 15a/15b | [07-chunking-comparison-plan.md](architecture-review/07-chunking-comparison-plan.md) | [02-decision-report.md](chunking-experiment/02-decision-report.md) | `evaluation/experiments/chunking/report-development.json` | `scripts/run_chunking_experiment.py` | S0 control retained; no candidate adopted |
| Full-text 14c | [08-retrieval-ablation-protocol.md](architecture-review/08-retrieval-ablation-protocol.md) | [09-fulltext-ablation-results.md](notes/09-fulltext-ablation-results.md) | `evaluation/experiments/fulltext/results.json` | `scripts/run_fulltext_ablation.py` | Current lexical behavior retained; c1/c2 failed, c3 equivalent |
| Test-file 14b | [11-test-file-retrieval-protocol.md](architecture-review/11-test-file-retrieval-protocol.md) | [12-test-file-comparison-results.md](notes/12-test-file-comparison-results.md) | `docs/notes/12-test-file-comparison-results.json` | `scripts/compare_test_file_variants.py` | Keep control; V1 descriptively improved but did not meet retention rules |
| Embedding task type 14a | [14-embedding-task-type-experiment.md](notes/14-embedding-task-type-experiment.md) | [15-embedding-task-type-results.md](notes/15-embedding-task-type-results.md) | `evaluation/cache/embedding_task_type_v1/report-development.json` (ignored) | `scripts/run_embedding_task_type_experiment.py` | Keep control |
| BM25 14d | [12-bm25-comparison-protocol.md](architecture-review/12-bm25-comparison-protocol.md) | [17-bm25-comparison-results.md](notes/17-bm25-comparison-results.md) | `evaluation/experiments/bm25/results.json` | `scripts/compare_bm25.py` | Keep control; B1 failed R1 and R2 |
| Local embeddings 18c | [14-local-embedding-protocol.md](architecture-review/14-local-embedding-protocol.md) | [18-local-embedding-results.md](notes/18-local-embedding-results.md) | `evaluation/cache/local_embedding_v1/results-development.json` (ignored) | `scripts/run_local_embedding_experiment.py` | Keep control; both candidates failed R1–R3 |

## Where to look

- **Current behavior:** [architecture overview](architecture/01-architecture-overview.md) and
  [low-level design](architecture/03-low-level-design.md).
- **How to run tests:** [test tiers](notes/16-test-tiers.md).
- **How to run experiments:** [the paired experiment table](#experiments) and
  [evaluation guide](../evaluation/README.md).
- **Decisions:** [LLM gateway direction](architecture-review/09-llm-gateway-decision.md),
  [degraded-response contract](architecture-review/13-degraded-response-design.md), and
  the decisions linked from each experiment row.
- **Runbooks:** [degraded modes and cache](runbooks/degraded-modes-and-cache.md).

## Folder navigation

- [Architecture](architecture/README.md)
- [Architecture review](architecture-review/README.md)
- [Chunking experiment](chunking-experiment/README.md)
- [Learning guides](learning/README.md)
- [Notes](notes/README.md)
- [Phases](phases/README.md)
- [Evaluation](../evaluation/README.md)
- [Runbooks](runbooks/README.md)
- [API reference](reference/README.md)
