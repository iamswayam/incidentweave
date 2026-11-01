# Contributing

**As of 2026-11-01.**

## Windows setup

From the repository root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
```

Set `DATABASE_URL` for the local Compose PostgreSQL service and put provider credentials in
the ignored `.env` file. Never commit `.env`, keys, tokens, or generated run output. Pydantic
Settings reads `.env`; `scripts/serve.py` copies `GEMINI_API_KEY` from settings into the
process environment. The shared Gemini request helper reads `GEMINI_API_KEY` from the process
environment, so direct provider CLI commands must receive it through the local environment.
Do not put secrets in command arguments, source files, tests, or logs.

Start the local database with `docker compose up -d db`, apply migrations with
`alembic upgrade head`, and stop it with `docker compose down` when finished. Do not use
`docker compose down -v` unless you explicitly intend to remove the local database volume.

## Test tiers

The tier runner is `scripts/test_tiers.py`; it does not start services or apply migrations.

```powershell
.\.venv\Scripts\python.exe -m scripts.test_tiers fast
.\.venv\Scripts\python.exe -m scripts.test_tiers fast --area providers
.\.venv\Scripts\python.exe -m scripts.test_tiers integration
.\.venv\Scripts\python.exe -m scripts.test_tiers evaluation
.\.venv\Scripts\python.exe -m scripts.test_tiers full
.\.venv\Scripts\python.exe -m ruff check .
```

`fast` runs the unit tier; `--area` narrows it to a unit-area directory. Integration requires
local PostgreSQL + pgvector and current migrations. Evaluation runs offline harness tests and
the retrieval smoke gate. `full` runs all three tiers serially. Network access is blocked in
unit and evaluation tests; tests replace provider calls with fakes or mocks. CI needs neither
a gateway nor a provider key.

## Branches, issues, and pull requests

- Work on one checklist item per branch and one pull request. Use the `fix/<item-id>-short-name`
  convention unless the maintainer assigns another branch name.
- Keep each pull request scoped to its checklist item. Follow the
  [checklist issue template](.github/ISSUE_TEMPLATE/checklist-item.md) and
  [pull request template](.github/pull_request_template.md).
- Merge with a merge commit. The maintainer handles branch creation/switching, PR creation,
  merge, and branch deletion.
- Use a plain commit subject such as `docs: add degraded-mode runbook`; do not add trailers.
- Stage explicit paths, never stage the whole worktree, and never rewrite history.

## Registered experiments

- Commit the protocol before generating candidate vectors or results.
- Use the development split for development comparisons. Held-out data is accessed only by
  the single explicitly registered held-out run; never inspect question, baseline, or result
  files directly. Use the approved split helpers.
- Define tolerances in whole questions before the run. Do not tune rules after observing
  results. Report descriptive measures separately from decisions.
- Keep aggregate artifacts separate from per-question or held-out material. Add each new
  protocol/results-note pair to the [documentation status index](docs/README.md).

## Documentation lifecycle

[docs/README.md](docs/README.md) is the single cross-folder status index; folder READMEs
remain navigation. Frozen documents are never edited. New experiments add a protocol, a
results note, and one row in the index. Living documents carry an as-of date. Put corrections
to frozen records in a living reference rather than changing the record. Keep relative links
valid and run the documented docs link check after documentation changes.

## Providers, keys, and fallback

Provider keys belong only in the ignored `.env`/local environment; never commit or paste them.
The application has no automatic key rotation. Groq generation fallback is off by default.
Before enabling any fallback, verify the provider's current data terms and limitations, and
validate its output on the registered golden set. There is no cross-model embedding fallback:
embedding spaces are not interchangeable. Do not add a silent direct-provider bypass around a
configured provider path.

## Decisions

Record architecture and provider decisions under
[docs/architecture-review/](docs/architecture-review/), registered experiment rules in their
protocols, and completed measurements in paired results notes. The checklist tracks work and
status; it is not a substitute for the decision record.
