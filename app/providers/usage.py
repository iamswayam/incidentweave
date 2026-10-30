"""Provider usage logging without retaining request or response content."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Iterator, Protocol

OPERATION_TAGS = (
    "query_embedding",
    "document_embedding",
    "generation",
    "experiment_embedding",
    "evaluation",
)

operation_override_var: ContextVar[str | None] = ContextVar(
    "operation_override",
    default=None,
)
correlation_id_var: ContextVar[str | None] = ContextVar(
    "correlation_id",
    default=None,
)

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UsageEntry:
    provider: str
    model: str
    operation_tag: str
    status: str
    error_class: str | None
    attempt_count: int
    latency_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    correlation_id: str


def validate_operation_tag(tag: str) -> None:
    if tag not in OPERATION_TAGS:
        raise ValueError(f"Unsupported provider usage operation tag: {tag}")


@contextmanager
def usage_operation(tag: str) -> Iterator[None]:
    validate_operation_tag(tag)
    token: Token[str | None] = operation_override_var.set(tag)
    try:
        yield
    finally:
        operation_override_var.reset(token)


class UsageLogger(Protocol):
    async def record(self, entry: UsageEntry) -> None: ...


class NullUsageLogger:
    """No-op logger used when provider usage logging is disabled."""

    async def record(self, entry: UsageEntry) -> None:
        del entry


class DbUsageLogger:
    """Persist provider usage metadata in a short independent transaction."""

    async def record(self, entry: UsageEntry) -> None:
        try:
            from app.db.models import ProviderUsageLog
            from app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                session.add(
                    ProviderUsageLog(
                        provider=entry.provider,
                        model=entry.model,
                        operation_tag=entry.operation_tag,
                        status=entry.status,
                        error_class=entry.error_class,
                        attempt_count=entry.attempt_count,
                        latency_ms=entry.latency_ms,
                        input_tokens=entry.input_tokens,
                        output_tokens=entry.output_tokens,
                        correlation_id=entry.correlation_id,
                    )
                )
                await session.commit()
        except Exception as exc:
            _logger.warning(
                "Provider usage log write failed (%s)",
                type(exc).__name__,
            )
