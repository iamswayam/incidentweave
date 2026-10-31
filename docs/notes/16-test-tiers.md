# Test tiers and CI speed

## Purpose and structure

Item 28 separates fast logic checks from PostgreSQL-backed behavior and deterministic evaluation
checks. All tests remain in the suite; the directory determines each test's pytest marker:

| Folder | Marker | What belongs here | Database/network |
|---|---|---|---|
| `tests/unit/` | `unit` | Pure logic, mocked provider calls, and tests with fake sessions | No database or external provider calls |
| `tests/integration/` | `integration` | Behavior requiring PostgreSQL or pgvector | PostgreSQL required; serial because tests share one database |
| `tests/evaluation/` | `evaluation` | Evaluation harness, fixtures, metrics, and deterministic offline gates | No live provider calls |

`tests/conftest.py` applies the folder marker during collection. The `slow` marker is registered
for tests that intentionally exercise longer-running behavior; it does not replace the folder's
single tier marker. Strict marker validation rejects unregistered marks.

## Commands

The tier runner keeps local and CI commands aligned:

| Purpose | Command | Notes |
|---|---|---|
| Fast | `.\.venv\Scripts\python.exe -m scripts.test_tiers fast` | Unit only, serial |
| Integration | `.\.venv\Scripts\python.exe -m scripts.test_tiers integration` | Serial; start PostgreSQL and apply Alembic migrations first |
| Evaluation | `.\.venv\Scripts\python.exe -m scripts.test_tiers evaluation` | Evaluation tests followed by the offline smoke gate |
| Full | `.\.venv\Scripts\python.exe -m scripts.test_tiers full` | All test folders, serial |
| Lint | `.\.venv\Scripts\python.exe -m ruff check .` | Repository-wide Ruff check |

The tier runner does not start services or migrate the database. Use the repository's normal
Docker Compose and Alembic setup before the integration command. These tests use synthetic data,
mocked HTTP transports, and cached evaluation fixtures; no command here requires a provider key.

## Adding a test

Place a pure test in `tests/unit/`, a database-dependent test in `tests/integration/`, or an
offline evaluation-harness test in `tests/evaluation/`. Do not add manual tier decorators; the
folder marker is automatic. Keep provider calls mocked and avoid real waits: use injected fake
clocks/sleeps or `asyncio.Event` coordination. Add a `slow` marker only when the test intentionally
measures or waits for a long-running behavior.

## CI

GitHub Actions runs independent jobs in parallel:

- `lint`: Ruff and Docker image build.
- `unit`: `pytest tests/unit -q`; it has no PostgreSQL service.
- `integration`: PostgreSQL/pgvector health check, Alembic migrations, then serial integration tests.
- `evaluation`: evaluation harness tests and the offline retrieval smoke gate.

The unit job is the everyday fast gate. CI still covers every test file and the previous migration,
database, retrieval-gate, lint, and Docker-build checks. The original full-suite `pytest` step is
also preserved in the PostgreSQL job, after the tier-specific integration command.

## Timings and limits

The pre-change baseline reported **424 passed and 1 failed (425 total) in about 156 seconds**.
The slow unit-provider tests waited on environment-configured request limits and cooldowns. Unit
tests now reset provider settings and adapter state before each test, and concurrency/timeout tests
use events rather than real sleeps or wall-clock responsiveness assertions.

Final measured timings and per-tier counts are recorded after the tier commands are run:

| Tier | Tests | Baseline | Final |
|---|---:|---:|---:|
| Unit | pending final run | not separately tiered | pending |
| Integration | pending final run | not separately tiered | pending |
| Evaluation | pending final run | not separately tiered | pending |
| Full | 425 | about 156 s | pending |

Serial unit testing took 136.03 seconds wall-clock for 249 tests; pytest-xdist `-n auto` took
136.41 seconds for the same set, so parallel execution was not retained. These measurements include
the current Windows machine's process-startup and scheduling overhead. The evaluation tier is
offline and deterministic; it does not validate live provider behavior.
