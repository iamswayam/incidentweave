# Implementation workflow

How every item of the [fix checklist](03-fix-checklist.md) is implemented, reviewed and merged. The same steps apply to every item, so the history of the repository reads the same from the first fix to the last.

## 1. Unit of work

One checklist item = one branch = one pull request (PR). Items are never mixed, and an item is not started until the previous one is merged. The order comes from the **Recommended order** table in the checklist.

| Rule | Why (production equivalent) |
|---|---|
| Small, single-purpose PRs | Easy to review and easy to revert. Standard practice on any team. |
| `main` always passes lint and tests | Everyone can branch from a known-good state; releases can be cut at any time. |
| No direct code pushes to `main` | Code changes are reviewed through a PR. Documentation-only changes may go straight to `main`. |

## 2. Lifecycle of one item

1. **Read the item** in the checklist: Why, Fix, Done when. The *Done when* line is the acceptance test.
2. **Branch** from an up-to-date `main`: `fix/NN-short-name` (NN is the checklist item number, for example `fix/02-remove-literal-grep`).
3. **Baseline**: run `ruff check .` and `pytest -q` on the fresh branch and note the test count.
4. **Implement** only what the item names. Add or update tests in the same change (see section 4).
5. **Check**: `ruff check .` and `pytest -q` must pass. Record the new test count.
6. **Update the docs** that describe the changed behaviour (README, architecture documents). A behaviour change and its documentation ship together.
7. **Update the checklist**: tick the item in the summary table and add one **Status** line (date, branch, files changed, real ruff and pytest results).
8. **Commit** in small logical steps (section 3) and push the branch.
9. **Open a PR** (section 5) that says `Closes #N` for the item's issue. CI must be green.
10. **Review the diff** against the item's *Done when* line, then **merge with a merge commit**.
11. **Clean up**: delete the branch on GitHub and locally, then update local `main`.

## 3. Commits

- Format: `type: short imperative summary`. Types: `feat`, `fix`, `docs`, `test`, `chore`, `refactor`.
- One logical change per commit. Code with its tests; documentation separately.
- Stage files by explicit path so unrelated files never slip in.
- Never commit secrets, `.env` files or run outputs.

## 4. Definition of done

- The *Done when* line of the item is demonstrated by a test or a recorded command, not by assertion.
- `ruff check .` and `pytest -q` pass; numbers in the docs come from a command that was actually run.
- No behaviour changed beyond what the item names.
- README and architecture documents match the code.
- The checklist shows the item ticked with a Status line.

## 5. Pull request description

Every PR description answers three questions in plain language:

1. **What changed?** The files and behaviour, briefly.
2. **How does it affect the project?** What is different for a user, the data or the next items.
3. **What is the real-world equivalent?** The industry practice the change follows (for example: input validation, dead-code removal, an audit trail).

Also include the checklist item number and the evidence for *Done when* (test names and results).

## 6. Documentation-only changes

Changes under `docs/` or to `README.md` go directly to `main` as one small commit. Files follow the `NN-kebab-case.md` naming inside their folder, each folder's `README.md` index is updated in the same commit, and every relative link must resolve.

## 7. Where progress is recorded

- Per-item progress: the **Progress log** and the **Status** lines in [03-fix-checklist.md](03-fix-checklist.md).
- History of decisions and corrections: the checklist's corrections section and the [independent review](04-fix-checklist-review-codex.md).
- What was merged and when: the merge commits on `main`.

## 8. Recommended repository setting

Protect `main` on GitHub (Settings → Branches): require a pull request and a passing CI check before merging. This enforces the rules above mechanically instead of by convention.

## 9. Blocked items

If an item cannot be finished (a failing check, a conflict, an unclear design), stop work on it, do not force it, and record `Blocked (reason)` in the Progress log. Continue with the next item only if that item does not depend on the blocked one (see the Recommended order table). A blocked item is revisited as soon as the reason is resolved.
