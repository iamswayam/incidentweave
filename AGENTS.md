# AGENTS.md

Standing rules for anyone working in this repository (maintainer, Copilot, Codex, or any other agent). Read this first.

## Precedence and when to stop

Order of authority, highest first:

1. **Safety rules** (the section below). Only the maintainer can lift one, and only by naming the exact action.
2. **The maintainer's task prompt.** A task may override the workflow defaults in this file (branching, who opens the PR, when to commit, how docs changes flow). Follow the task and mention the difference in the final report. A difference between the task and a workflow default is **not** a reason to stop.
3. **The defaults in this file.**

Stop and ask the maintainer only when:

- an action would break a Safety rule;
- the task contradicts itself, or is ambiguous in a way that changes the outcome;
- a result differs from what the task said to expect;
- a step needs a human decision (the task says so, or the choice cannot be undone);
- something is beyond what you can do or verify.

Do not stop for a failing test, a lint error or a broken link caused by your own change. Fix it and report it.

## Project in one paragraph

IncidentWeave is a repository-aware investigation assistant: it ingests a repository, retrieves evidence for a question, and returns a grounded, cited answer or an honest refusal. Scope is controlled by `docs/architecture/01-architecture-overview.md` (see its Maintenance Rule). Do not add features, dependencies or architecture beyond the approved plan.

## Sources of truth

- Work to do: `docs/architecture-review/03-fix-checklist.md` (one numbered item at a time, in the order given there).
- Design: `docs/architecture/`.
- History and results: `docs/phases/`, `docs/chunking-experiment/`, `docs/notes/`.
- Each docs folder has a `README.md` that indexes it.

## Safety rules

- Never commit `.env`, keys, tokens or run outputs. Check `git status --short` before every commit.
- Do not call live external APIs (for example Gemini) unless the task explicitly says so. Do not install packages unless the task explicitly says so.
- Never run reset, clean, stash, rebase, amend, force-push or `branch -D` without explicit maintainer approval for that exact command.
- Never delete a branch or a file that was not named in the task.
- Never `git add .` or `git add -A`. Stage by explicit path (`git add -- <path>`).
- The frozen held-out evaluation split is not run, inspected or used for any decision unless the task explicitly says so.
- Claims need evidence. Test counts, metrics and results come only from a command that was actually run; never from memory or from an old document.

## Change control

- The maintainer approves each implementation step before work starts. Do not start the next checklist item on your own.
- One checklist item (or sub-item, for example `14c-2`) = one branch = one pull request. Never mix items. Housekeeping that records or closes an item belongs to that item's branch.
- Do not change behaviour that the checklist item does not name.
- A checklist item is done only when its "Done when" line is met and demonstrated.

## Git workflow

- `main` is the source of truth and must always be green (ruff and pytest).
- **Every change goes through a branch and a pull request, including docs-only changes.** Branch names are `fix/<item-id>-short-name`, for example `fix/02-api-no-grep` or `fix/14c-2-fulltext-variants`.
- **The maintainer does the git setup**: creates the branch from an up-to-date `main` and switches to it before giving the task, opens the pull request, merges with a merge commit, and deletes the branch locally and on GitHub.
- **The agent's git work**:
  - First action: confirm the current branch is the one the task names and that `git status --short` is clean (see the exception below). If not, stop and report.
  - Do not create, switch, merge or delete branches unless the task says so.
  - Make the changes and run the checks. Then, **at the end only**: stage by explicit path, commit in small logical commits, and push the branch (`git push --set-upstream origin <branch>` if it has no upstream).
  - Do not open the pull request unless the task says so.
- Exception to the clean-tree check: a task may say that a named file was already changed by the maintainer. Only that file may be uncommitted at the start.
- Before switching branches: `git status --short` must be empty. Never carry uncommitted work across branches.
- Commit messages: `type: short imperative summary` with type one of `feat`, `fix`, `docs`, `test`, `chore`, `refactor`. One logical change per commit.
- Run git commands one at a time, never in parallel (parallel commands cause `index.lock` errors on Windows).

## Docs structure and naming

- Docs live only under `docs/<area>/`. No new top-level docs files and no new top-level folders.
- File names are `NN-kebab-case.md` with a two-digit sequence number inside their folder (`08b-` style suffixes only for a sub-document of an existing number). Do not invent other naming patterns.
- Adding, renaming or deleting a doc means updating that folder's `README.md` index and any links to it in the same commit. Use `git mv` for renames so history is kept.
- Images go in `docs/assets/`. Keep them small (the social preview is 1280x640 and under 1 MB).
- After any docs change, relative links must resolve (no broken links). Run the docs link check the task names.

## Code checks

- Run from the repo root with the project interpreter: `.\.venv\Scripts\python.exe -m ruff check .` and `.\.venv\Scripts\python.exe -m pytest`.
- Add or update tests with every behaviour change.

## Working style

- Do exactly what the task says, in the order given. If a step's result differs from what the task expected, stop and report instead of improvising.
- Read-only diagnostics are not stop conditions.
- Report at the end: commit SHAs, files changed, commands run with their results, and anything unverified.