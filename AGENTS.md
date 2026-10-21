# AGENTS.md

Standing rules for anyone working in this repository (maintainer, Copilot, Codex, or any other agent). Read this first. If a task conflicts with these rules, stop and ask the maintainer.

## Project in one paragraph

IncidentWeave is a repository-aware investigation assistant: it ingests a repository, retrieves evidence for a question, and returns a grounded, cited answer or an honest refusal. Scope is controlled by `docs/architecture/01-architecture-overview.md` (see its Maintenance Rule). Do not add features, dependencies or architecture beyond the approved plan.

## Sources of truth

- Work to do: `docs/architecture-review/03-fix-checklist.md` (one numbered item at a time, in the order given there).
- Design: `docs/architecture/`.
- History and results: `docs/phases/`, `docs/chunking-experiment/`, `docs/notes/`.
- Each docs folder has a `README.md` that indexes it.

## Change control

- The maintainer approves each implementation step before work starts. Do not start the next checklist item on your own.
- One checklist item = one branch = one pull request. Never mix items.
- Do not change behaviour that the checklist item does not name.
- Claims need evidence. Test counts, metrics and results come only from a command that was actually run; never from memory or from an old document.

## Git workflow

- `main` is the source of truth and must always be green (ruff and pytest).
- Code changes: create one short-lived branch from an up-to-date `main`, named `fix/NN-short-name` (NN = checklist item number, for example `fix/02-api-no-grep`). Open a pull request, merge with a merge commit, then delete that branch locally and on GitHub. Create no other branches.
- Docs-only changes (files under `docs/`, `README.md`, `AGENTS.md`) go directly to `main` as one small commit, unless the maintainer asks for a pull request.
- Before switching branches: `git status --short` must be empty. Never carry uncommitted work across branches.
- Stage by explicit path (`git add -- <path>`). Never `git add .` or `git add -A`.
- Never run reset, clean, stash, rebase, amend, force-push or `branch -D` without explicit maintainer approval for that exact command.
- Never delete a branch or a file that was not named in the task.
- Commit messages: `type: short imperative summary` with type one of `feat`, `fix`, `docs`, `test`, `chore`, `refactor`. One logical change per commit.
- Run git commands one at a time, never in parallel (parallel commands cause `index.lock` errors on Windows).

## Docs structure and naming

- Docs live only under `docs/<area>/`. No new top-level docs files and no new top-level folders.
- File names are `NN-kebab-case.md` with a two-digit sequence number inside their folder (`08b-` style suffixes only for a sub-document of an existing number). Do not invent other naming patterns.
- Adding, renaming or deleting a doc means updating that folder's `README.md` index and any links to it in the same commit. Use `git mv` for renames so history is kept.
- Images go in `docs/assets/`. Keep them small (the social preview is 1280x640 and under 1 MB).
- After any docs change, relative links must resolve (no broken links).

## Code checks

- Run from the repo root with the project interpreter: `.\.venv\Scripts\python.exe -m ruff check .` and `.\.venv\Scripts\python.exe -m pytest`.
- Add or update tests with every behaviour change. A checklist item is done only when its "Done when" line is met and demonstrated.
- Never commit `.env`, keys, tokens or run outputs. Check `git status --short` before every commit.
- Do not call live external APIs (for example Gemini) unless the task explicitly says so. Do not install packages unless the task explicitly says so.

## Working style

- Do exactly what the task says, in the order given. If a step's result differs from what the task expected, stop and report instead of improvising.
- Report at the end: commit SHAs, files changed, commands run with their results, and anything unverified.
