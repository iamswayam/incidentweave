# Architecture review

Independent engineering audits of IncidentWeave and the prioritized fix checklist that follows from them.

| # | File | Author | Type | Status |
|---|------|--------|------|--------|
| 01 | [01-audit-claude.md](01-audit-claude.md) | Claude | Audit report | Frozen |
| 02 | [02-audit-codex.md](02-audit-codex.md) | Codex | Audit report | Frozen |
| 03 | [03-fix-checklist.md](03-fix-checklist.md) | Claude, reviewed by Codex | Prioritized fix checklist with per-item status | Living |
| 04 | [04-fix-checklist-review-codex.md](04-fix-checklist-review-codex.md) | Codex | Independent review of 03 | Frozen |
| 05 | [05-implementation-workflow.md](05-implementation-workflow.md) | Maintainer | How every checklist item is implemented, reviewed and merged | Living |
| 06 | [06-multi-repo-evaluation-plan.md](06-multi-repo-evaluation-plan.md) | Claude, reviewed by Codex | Multi-repo evaluation plan and review | Living |
| 07 | [07-chunking-comparison-plan.md](07-chunking-comparison-plan.md) | Claude, reviewed by Codex | Chunking comparison plan and review | Living |
| 08 | [08-retrieval-ablation-protocol.md](08-retrieval-ablation-protocol.md) | Maintainer | Preregistered retrieval ablation protocol (item 14) | Living |
| 09 | [09-llm-gateway-decision.md](09-llm-gateway-decision.md) | Maintainer | LLM gateway decision revision and provider-layer direction for item 18 | Living |
| 10 | [10-llm-gateway-design.md](10-llm-gateway-design.md) | Maintainer | Provider-layer design and call-site inventory for 18a-1 | Living |
| 11 | [11-test-file-retrieval-protocol.md](11-test-file-retrieval-protocol.md) | Maintainer | Preregistered test-file retrieval comparison protocol (item 14b) | Living |
| 12 | [12-bm25-comparison-protocol.md](12-bm25-comparison-protocol.md) | Maintainer | Preregistered BM25 lexical retrieval comparison protocol (item 14d) | Living |
| 13 | [13-degraded-response-design.md](13-degraded-response-design.md) | Maintainer | Approved degraded-response contract and implementation record for item 18d | Implemented |
| 14 | [14-local-embedding-protocol.md](14-local-embedding-protocol.md) | Maintainer | Registered development-only local embedding comparison protocol for item 18c | Registered |

## Conventions
- Files are named `NN-kebab-case.md` in reading order. A new document takes the next number.
- Frozen documents are never edited apart from link maintenance. Corrections go into the living checklist.
- The living checklist is updated in the same commit as the fix it describes.
- Each fix uses one short-lived branch from `main` named `fix/NN-short-name` (NN = checklist item), merged into `main` and then deleted.
