"""Database integration coverage for the committed offline retrieval fixture."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.db.models import Repository
from app.db.session import AsyncSessionLocal
from evaluation.retrieval_eval import FIXTURE_REPOSITORY, run_offline_retrieval

pytestmark = pytest.mark.integration


@pytest.mark.anyio
async def test_offline_retrieval_fixture_runs_and_cleans_up_repository() -> None:
    report = await run_offline_retrieval()

    assert report["metadata"]["fixture"]["chunk_count"] == 70
    assert report["metadata"]["fixture"]["question_count"] == 24
    assert report["metadata"]["limit"] == 5
    assert len(report["questions"]) == 24
    assert report["summary"]["substring_labels"]["count"] == 16
    assert report["summary"]["spans"]["count"] == 16
    hit_at_5 = report["summary"]["substring_labels"]["hit_at_5"]
    assert hit_at_5["successes"] / report["summary"]["substring_labels"]["count"] >= 0.5
    assert "wilson_95" in hit_at_5
    assert set(report["breakdown_by_category"]) == {"direct", "paraphrased"}

    async with AsyncSessionLocal() as session:
        leftover = await session.scalar(
            select(Repository).where(Repository.name == FIXTURE_REPOSITORY)
        )
    assert leftover is None
