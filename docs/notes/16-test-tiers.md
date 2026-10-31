# Test tiers and scaling

## Purpose and layout

Tests are grouped first by execution tier, then by the application area they exercise. A test's
first directory under `tests/` supplies its single tier marker automatically; nested area folders
do not change that tier.

| Tier | Location | Marker | Contents |
|---|---|---|---|
| Unit | `tests/unit/<area>/` | `unit` | Deterministic logic with fake sessions and mocked provider transports |
| Integration | `tests/integration/<area>/` | `integration` | Behavior requiring PostgreSQL/pgvector or real local service boundaries |
| Evaluation | `tests/evaluation/<topic>/` | `evaluation` | Offline retrieval metrics, manifest/split protections, and experiment harnesses |

Unit areas mirror the application and script boundaries:

| Area | Purpose |
|---|---|
| `api` | HTTP route behavior and health response |
| `db` | ORM model definitions and constraints without a live database |
| `evaluation` | Pure embedding-task-type decision logic and test-path classification |
| `investigation` | Prompting, parsing, graph orchestration, replay, and input limits |
| `providers` | Gemini/Groq adapters, retries, cooldowns, usage metadata, and reporting |
| `retrieval` | Chunking, full-text query construction, and hybrid-search composition |
| `scripts` | Ingestion and embedding CLI/helper behavior |

Integration areas are `db`, `ingestion`, `providers`, and `retrieval`. Evaluation topics are
`chunking`, `embedding_task_type`, `fulltext`, `manifest_and_splits`, `retrieval_eval`, and
`test_files`. `tests/evaluation/test_evaluation.py` remains at the tier root because its fixtures
resolve the repository root relative to that exact location.

`tests/conftest.py` applies exactly one tier marker based on the first folder under `tests/`.
Pytest runs with strict marker validation and importlib import mode. `slow` is reserved for tests
whose real-world behavior is intentionally long; no current test is excluded from the fast tier.
The former one-off timeout/concurrency tests use events and short bounded deadlines, not wall-clock
speed assertions.

## Commands

Run commands from the repository root:

| Purpose | Command | Requirements |
|---|---|---|
| Fast | `.\.venv\Scripts\python.exe -m scripts.test_tiers fast` | Unit tests only |
| One area | `.\.venv\Scripts\python.exe -m scripts.test_tiers fast --area providers` | Any existing direct unit area |
| Integration | `.\.venv\Scripts\python.exe -m scripts.test_tiers integration` | Start Compose PostgreSQL and apply Alembic migrations |
| Evaluation | `.\.venv\Scripts\python.exe -m scripts.test_tiers evaluation` | Offline evaluation tests plus smoke retrieval gate |
| Full | `.\.venv\Scripts\python.exe -m scripts.test_tiers full` | Integration prerequisites still apply |
| Lint | `.\.venv\Scripts\python.exe -m ruff check .` | No service required |

The runner does not start services or migrate the database. It forwards the pytest exit status and
stops if an evaluation test fails before running the smoke gate.

## Network and shared state

`pytest-socket` is a development dependency. Global pytest options deny socket creation and permit
Unix-domain sockets only. Thus unit and evaluation tests cannot reach Gemini, Groq, or other
network services. Integration tests receive an automatic `allow_hosts` restriction for
`localhost`, `127.0.0.1`, and `::1`; they cannot connect to external hosts.

Unit tests set provider configuration to documented defaults once per test session, construct the
default adapters once, and clear limiter/cooldown/API-rate-limiter state before each test. Tests
that need retries inject fake sleepers and clocks. Provider tests use fake HTTP transports or
injected helpers. Integration tests remain serial because they share one database.

## Adding a test

1. Choose the tier by the boundary the test actually needs: pure logic in `unit`, PostgreSQL or
   service integration in `integration`, and offline evaluation/harness behavior in `evaluation`.
2. Put it under the relevant area/topic folder. Do not add a tier decorator; collection applies
   it. Keep filenames unique where practical, and do not import test helpers from another test
   module; put shared fixtures in the appropriate `conftest.py` or a small `tests/helpers/` module.
3. Keep provider calls mocked, use fake clocks/sleep functions for retry tests, and do not use
   external network access. Only mark a test `slow` when long duration is essential to the behavior.
4. Run its tier or area command, then the full suite when the change affects shared setup.

## CI

GitHub Actions runs the checks as independent jobs:

- `lint`: Ruff and Docker image build.
- `unit`: one network-blocked unit run with `--durations=15`; no database service.
- `integration`: one PostgreSQL service, health check, migrations, and serial integration run.
- `evaluation`: evaluation tests once, followed by the offline retrieval gate.

The full suite is run locally by the `full` command; CI does not repeat the same tests after the
three tier jobs.

## Diagnosis and timings

Before the test-tier work, the full suite was reported as **424 passed, 1 failed, 425 total in
about 156 seconds**. After the first tier split, the 249-test unit tier measured **103.62 seconds
inside pytest and 136.03 seconds wall-clock**; `-n auto` measured **106.32 seconds inside pytest
and 136.41 seconds wall-clock**, so xdist did not help on this Windows machine.

For this follow-up, the no-cache duration run reported **249 passed in 110.71 seconds**. Summed
reported setup and teardown was **1.27 seconds**; almost all test-reported time was in call phases.
The slowest calls included:

| Test | Setup | Call | Teardown |
|---|---:|---:|---:|
| `providers/test_provider_usage.py::test_non_integer_usage_metadata_is_logged_as_none` | 0.00s | 5.85s | 0.00s |
| `providers/test_provider_usage.py::test_usage_logger_failure_does_not_change_success_or_provider_exception` | 0.01s | 4.25s | 0.00s |
| `providers/test_provider_layer.py::test_value_error_releases_half_open_probe` | 0.00s | 4.20s | 0.00s |
| `providers/test_provider_layer.py::test_non_retryable_error_closes_cooldown_and_timeout_counts_as_retryable` | 0.00s | 4.19s | 0.01s |
| `providers/test_provider_usage.py::test_value_error_from_provider_helper_is_not_logged` | 0.05s | 4.14s | 0.00s |
| `providers/test_provider_usage.py::test_usage_timeout_does_not_delay_success_or_log_payload` | 0.02s | 3.71s | 0.00s |
| `providers/test_provider_layer.py::test_cancelled_half_open_probe_is_released` | 0.01s | 3.62s | 0.00s |
| `providers/test_provider_layer.py::test_estimated_tokens_trigger_tpm_wait` | 0.00s | 3.21s | 0.00s |
| `providers/test_groq_fallback.py::test_one_groq_sequence_uses_only_bounded_internal_retries` | 0.00s | 2.59s | 0.00s |
| `providers/test_groq_fallback.py::test_generation_falls_back_once_for_retryable_gemini_errors[gemini_error0]` | 0.01s | 2.44s | 0.00s |
| `providers/test_provider_usage.py::test_usage_latency_excludes_rate_limiter_wait` | 0.00s | 2.05s | 0.00s |
| `providers/test_provider_layer.py::test_estimated_tokens_are_passed_to_limiter_and_tpm_is_enforced` | 0.00s | 2.03s | 0.00s |
| `providers/test_groq_fallback.py::test_generation_falls_back_once_for_retryable_gemini_errors[gemini_error3]` | 0.00s | 1.95s | 0.00s |
| `providers/test_groq_fallback.py::test_missing_or_disabled_groq_configuration_does_not_fallback[True-None-qwen/qwen3.8-27b]` | 0.01s | 1.90s | 0.00s |
| `providers/test_provider_layer.py::test_rate_limiter_error_releases_half_open_probe` | 0.00s | 1.88s | 0.00s |

Collection took **65.90 seconds as reported by pytest and 134.30 seconds wall-clock** before the
layout/import changes, then **21.84 seconds** after them. The `python -X importtime` profile showed
**26.41 seconds cumulative** for importing
`app.investigation.graph`; `langgraph.graph` accounted for 21.47 seconds cumulative, and
`langchain_core`/`langsmith` tracing imports were also prominent. These are startup/import costs,
not per-test fixture setup.

The prior unit autouse fixture patched 17 settings/environment variables and rebuilt Gemini and
Groq adapters before every test. Profiling showed that setup and teardown contributed only 1.27
seconds in total, so it was a correctness/isolation problem rather than the dominant runtime cause.
It now establishes defaults and adapters once, then clears mutable state per test. No repeated
large fixture loads or real DNS/provider requests were found. Retry/rate-limit tests inject fake
sleepers; explicit timeout tests await events and exercise bounded timeout behavior. The DB engine
is module-level, not constructed per test. The import change substantially reduced collection
time, but the measured call-phase time remains high and was not fully explained by the inspected
fixtures, waits, or provider retry code. The fast-tier target has not been met; further profiling of
the slow call-phase tests is still needed rather than claiming the remaining time is fixed.

The final run collected and passed **428 tests**: 251 unit, 10 integration, and 167 evaluation.
The baseline had 425 tests (424 passed and 1 failed), so three tests were added and none were lost.
The measured final tier timings were:

| Tier | Tests | Before timing | Final timing |
|---|---:|---:|---:|
| Unit / fast | 251 | 249: 103.62s pytest / 136.03s wall | 251: 108.35s pytest / 135.19s wall |
| Integration | 10 | not separately timed | 21.32s pytest in full run; 38.61s wall standalone |
| Evaluation tests | 167 | not separately timed | 39.09s in full run; 44.85s standalone |
| Evaluation command, including smoke gate | 167 | not separately timed | 82.90s wall standalone |
| Full tests only | 425 | about 156s | 428 passed; 163.70s summed pytest time |
| Full runner, including smoke gate | 425 | not applicable | 428 tests passed; 234.09s wall |

The full-run pytest-reported times were 103.29 seconds for unit, 21.32 seconds for integration,
and 39.09 seconds for evaluation (163.70 seconds summed). The standalone command timings include
process startup; the evaluation command also runs the retrieval smoke gate. The full command runs
the smoke gate once after all three test tiers. On this machine the `fast` command remains over
the 30-second target and over the 60-second threshold in the scaling plan. `-n auto` did not
improve the measured wall-clock time (141.61 seconds versus 135.19 seconds for the final serial
run), so xdist remains disabled.

Final collected counts by area:

| Tier | Area/topic | Tests |
|---|---|---:|
| Unit | `api` | 16 |
| Unit | `db` | 6 |
| Unit | `evaluation` | 29 |
| Unit | `investigation` | 47 |
| Unit | `providers` | 101 |
| Unit | `retrieval` | 35 |
| Unit | `scripts` | 17 |
| Integration | `db` | 3 |
| Integration | `ingestion` | 1 |
| Integration | `providers` | 3 |
| Integration | `retrieval` | 3 |
| Evaluation | tier root | 46 |
| Evaluation | `chunking` | 27 |
| Evaluation | `embedding_task_type` | 14 |
| Evaluation | `fulltext` | 3 |
| Evaluation | `manifest_and_splits` | 25 |
| Evaluation | `retrieval_eval` | 31 |
| Evaluation | `test_files` | 21 |

## Scaling plan and limits

The measured fast tier is currently over 60 seconds, so the next performance work should profile
the slow call-phase tests and collection imports before adding parallelism. When the test count or
fast-tier runtime continues to grow, evaluate:

- pytest-xdist only after a same-machine benchmark demonstrates a wall-clock win without shared
  state leaks;
- pytest-split to divide deterministic CI runs into balanced, stable shards;
- testmon only as an optional local changed-test accelerator, never as the sole CI gate.

None of these sharding/selection plugins is added here. The documented `--area` runner is useful
for focused local debugging but does not replace full-tier CI coverage. Measurements are from one
Windows machine and should not be generalized to CI or other developer hardware.
