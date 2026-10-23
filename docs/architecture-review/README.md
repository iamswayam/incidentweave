# Architecture review

Independent engineering audits of IncidentWeave and the prioritized fix checklist that follows from them.

| # | File | Author | Type | Status |
|---|------|--------|------|--------|
| 01 | [01-audit-claude.md](01-audit-claude.md) | Claude | Audit report | Frozen |
| 02 | [02-audit-codex.md](02-audit-codex.md) | Codex | Audit report | Frozen |
| 03 | [03-fix-checklist.md](03-fix-checklist.md) | Claude, reviewed by Codex | Prioritized fix checklist with per-item status | Living |
| 04 | [04-fix-checklist-review-codex.md](04-fix-checklist-review-codex.md) | Codex | Independent review of 03 | Frozen |
| 05 | [05-implementation-workflow.md](05-implementation-workflow.md) | Maintainer | How every checklist item is implemented, reviewed and merged | Living |

## Conventions
- Files are named `NN-kebab-case.md` in reading order. A new document takes the next number.
- Frozen documents are never edited apart from link maintenance. Corrections go into the living checklist.
- The living checklist is updated in the same commit as the fix it describes.
- Each fix uses one short-lived branch from `main` named `fix/NN-short-name` (NN = checklist item), merged into `main` and then deleted.
