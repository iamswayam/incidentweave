"""Integration tests for the provider usage log table."""

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.db.models import ProviderUsageLog
from app.db.session import AsyncSessionLocal, engine

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
                for column in inspect(sync_connection).get_columns(
                    ProviderUsageLog.__tablename__
                )
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
