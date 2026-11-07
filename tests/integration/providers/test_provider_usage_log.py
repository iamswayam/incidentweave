"""Integration tests for the provider usage log table."""

from uuid import uuid4

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.db.models import Audit, Investigation, ProviderUsageLog, Repository
from app.db.session import AsyncSessionLocal, engine
from app.providers.operational_metrics import summarize_operational_metrics
from app.providers.usage import DbUsageLogger, UsageEntry
from scripts.usage_report import _load_operational_rows, _load_rows

pytestmark = pytest.mark.integration

EXPECTED_COLUMNS = {
    "id",
    "provider",
    "model",
    "operation_tag",
    "status",
    "error_class",
    "attempt_count",
    "latency_ms",
    "input_tokens",
    "output_tokens",
    "correlation_id",
    "created_at",
}


@pytest.mark.anyio
async def test_usage_table_has_exact_columns_after_migrations() -> None:
    """Verify the migrated table exists and has no payload columns."""

    async with engine.connect() as connection:
        columns = await connection.run_sync(
            lambda sync_connection: {
                column["name"]
                for column in inspect(sync_connection).get_columns(ProviderUsageLog.__tablename__)
            }
        )

    assert columns == EXPECTED_COLUMNS


@pytest.mark.anyio
async def test_usage_table_rejects_invalid_status_and_success_error_class() -> None:
    """Verify database constraints enforce the status/error-class contract."""

    async with AsyncSessionLocal() as session:
        session.add(
            ProviderUsageLog(
                provider="gemini",
                model="test-model",
                operation_tag="generation",
                status="weird",
                error_class=None,
                attempt_count=1,
                correlation_id="integration-test",
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()

        session.add(
            ProviderUsageLog(
                provider="gemini",
                model="test-model",
                operation_tag="generation",
                status="success",
                error_class="server_error",
                attempt_count=1,
                correlation_id="integration-test",
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()


@pytest.mark.anyio
async def test_db_logger_records_rows_visible_to_report_query() -> None:
    """Verify logged usage is selected by the read-only report query."""

    model = f"usage-test-{uuid4().hex}"
    entry = UsageEntry(
        provider="gemini",
        model=model,
        operation_tag="generation",
        status="success",
        error_class=None,
        attempt_count=2,
        latency_ms=35,
        input_tokens=8,
        output_tokens=3,
        correlation_id=uuid4().hex,
    )
    await DbUsageLogger().record(entry)

    rows = await _load_rows(24)
    matching = [row for row in rows if row["model"] == model]

    assert matching == [
        {
            "provider": "gemini",
            "model": model,
            "operation_tag": "generation",
            "status": "success",
            "error_class": None,
            "attempt_count": 2,
            "latency_ms": 35,
            "input_tokens": 8,
            "output_tokens": 3,
        }
    ]


@pytest.mark.anyio
async def test_operational_metrics_load_persisted_usage_outcomes_and_cache_traces() -> None:
    """Verify the report aggregates synthetic telemetry from all persisted sources."""

    repository_name = f"usage-report-{uuid4().hex}"
    answered_correlation = uuid4().hex
    degraded_correlation = uuid4().hex
    async with AsyncSessionLocal() as session:
        repository = Repository(name=repository_name)
        session.add(repository)
        await session.flush()
        answered = Investigation(
            repository_id=repository.id,
            query="synthetic answered query",
            response="synthetic response",
            outcome="answered",
        )
        degraded = Investigation(
            repository_id=repository.id,
            query="synthetic degraded query",
            response="",
            outcome="generation_unavailable",
        )
        session.add_all((answered, degraded))
        await session.flush()
        session.add_all(
            (
                Audit(
                    investigation_id=answered.id,
                    repository_id=repository.id,
                    query=answered.query,
                    trace={
                        "correlation_id": answered_correlation,
                        "query_embedding_cache": {
                            "hit": True,
                            "miss": False,
                            "lookup_succeeded": True,
                        },
                    },
                ),
                Audit(
                    investigation_id=degraded.id,
                    repository_id=repository.id,
                    query=degraded.query,
                    trace={
                        "correlation_id": degraded_correlation,
                        "cache": {
                            "hit": False,
                            "miss": True,
                            "lookup_succeeded": True,
                        },
                    },
                ),
                ProviderUsageLog(
                    provider="gemini",
                    model="gemini-3.5-flash-lite",
                    operation_tag="generation",
                    status="success",
                    error_class=None,
                    attempt_count=1,
                    latency_ms=20,
                    input_tokens=100,
                    output_tokens=40,
                    correlation_id=answered_correlation,
                ),
                ProviderUsageLog(
                    provider="gemini",
                    model="gemini-3.5-flash-lite",
                    operation_tag="generation",
                    status="failure",
                    error_class="timeout",
                    attempt_count=2,
                    latency_ms=40,
                    input_tokens=None,
                    output_tokens=None,
                    correlation_id=degraded_correlation,
                ),
            )
        )
        await session.commit()

    usage_rows, investigation_rows = await _load_operational_rows(24)
    correlation_ids = {answered_correlation, degraded_correlation}
    usage_rows = [row for row in usage_rows if row["correlation_id"] in correlation_ids]
    investigation_rows = [
        row
        for row in investigation_rows
        if isinstance(row["trace"], dict) and row["trace"].get("correlation_id") in correlation_ids
    ]
    summary = summarize_operational_metrics(
        usage_rows,
        investigation_rows,
        since_hours=24,
    )

    operation = summary["operations"][0]
    assert operation["operation"] == "generation"
    assert operation["count"] == 2
    assert operation["errors"] == 1
    assert operation["attempts"] == 3
    assert summary["degraded_count"] == 1
    assert summary["cache"]["hits"] == 1
    assert summary["cache"]["misses"] == 1
