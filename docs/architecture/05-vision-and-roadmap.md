# IncidentWeave: vision and roadmap

**Status:** adopted 2026-11-08. This document sets direction. It is not a checklist: work items live in `../architecture-review/03-fix-checklist.md`.

## Vision

Evidence-first incident investigation for engineers: every claim cites verifiable evidence, or the system says it does not know.

The goal is to be the most trustworthy answer for evidence-based questions about software incidents, not the first choice for every question.

## Principles

1. **Evidence or silence.** An answer cites evidence that can be checked, or it refuses. It never states a root cause without cited evidence.
2. **Measured, not claimed.** Methods are registered before results, development and held-out data stay separate, and every number has a source and an interval.
3. **Auditable.** Each answer can be replayed: prompt, evidence, versions and settings are stored.
4. **Private by direction.** Private code and logs should be able to stay under the user's control. A self-hosted path with open-source local models is a goal, not a current capability.
5. **Focus before breadth.** A new evidence source or feature starts only when the quality of the existing ones is measured and good enough.

## Where we are

Retrieval finds the relevant chunk within the top 20 almost every time. The main weaknesses are the order of the results and the refusal of questions that are close to, but not covered by, the indexed evidence. Current numbers are in `../reference/metrics.md`.

## Roadmap

A horizon starts only when the previous horizon's exit condition is met. An exception needs a written reason in the pull request.

| Horizon | Focus | Checklist items | Exit condition |
|---|---|---|---|
| 1. Prove quality | Larger and harder datasets, reranker, better refusal of near-miss questions, answer-quality measurement | 31, 32b, 21, 3b, 34, 17 | The registered held-out run (3b) is done and the near-miss refusal rate has improved on development data |
| 2. Widen evidence | Git history and pull requests ("what changed before this broke"), then docs, runbooks and configs, then logs and alerts, then issue trackers | 20 and new items | Each new source has its own questions and a measured result before the next is added |
| 3. Reasoning | Ranked hypotheses tested with read-only queries, where "inconclusive" is a valid result; incident-replay benchmark | 22, 12b | A report over labelled incidents with root-cause accuracy, evidence validity, time and cost |
| 4. Delivery and scale | GitHub App, chat and alert integrations, editor access through MCP, access scopes, self-hosted deployment with local models, per-repository evaluation reports | 23, 24 and new items | A deployment that another team can run on its own repositories |

## Open-source and local models

Gemini stays the default for now. Open-source models are evaluated through registered comparisons (item 24), using the existing yardsticks: citation validity, refusal correctness and stability (item 34), retrieval metrics, and cost and latency (item 33). Local embedding models were tested and the control was kept; they are revisited when stronger candidates appear. The aim is a self-hosted configuration whose measured quality is published next to the hosted one.

## Scope fence

Not before horizon 4: multi-tenant hosting, job queues, container orchestration, a hosted public demo. Not at any time: unsupported root-cause claims, or results without a registered method.

## Checkpoint

After the held-out run (3b) and the first incident-replay results (22), review feedback and any real use, then decide how much further to invest.

## Changing this document

Changes go through a pull request that states the reason. Work items belong in the checklist, not here.
