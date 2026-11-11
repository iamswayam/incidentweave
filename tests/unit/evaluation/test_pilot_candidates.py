from __future__ import annotations

from datetime import date
from typing import Any

from evaluation.mine_pilot_candidates import collect_pilot_candidates


def test_mining_keeps_only_closed_linked_prs_with_extant_non_test_files() -> None:
    issues: list[dict[str, Any]] = [
        {
            "number": 10,
            "title": "Handle queue shutdown",
            "body": "A report with contact user@example.com",
            "closedAt": "2026-10-20T12:00:00Z",
            "url": "https://github.com/rq/rq/issues/10",
        },
        {
            "number": 11,
            "title": "Too new",
            "body": "",
            "closedAt": "2026-11-01T12:00:00Z",
        },
    ]
    pull_requests: list[dict[str, Any]] = [
        {
            "number": 20,
            "mergedAt": "2026-10-22T12:00:00Z",
            "closingIssuesReferences": [{"number": 10}],
            "files": [{"path": "src/rq/worker.py"}],
            "url": "https://github.com/rq/rq/pull/20",
        },
        {
            "number": 21,
            "mergedAt": "2026-10-22T12:00:00Z",
            "closingIssuesReferences": [{"number": 10}],
            "files": [{"path": "src/rq/worker.py"}, {"path": "tests/test_worker.py"}],
        },
        {
            "number": 22,
            "mergedAt": "2026-10-22T12:00:00Z",
            "closingIssuesReferences": [{"number": 10}],
            "files": [{"path": "src/rq/deleted.py"}],
        },
        {
            "number": 23,
            "mergedAt": "2026-11-01T12:00:00Z",
            "closingIssuesReferences": [{"number": 10}],
            "files": [{"path": "src/rq/worker.py"}],
        },
        {
            "number": 24,
            "mergedAt": "2026-10-22T12:00:00Z",
            "closingIssuesReferences": [{"number": 11}],
            "files": [{"path": "src/rq/worker.py"}],
        },
    ]

    result = collect_pilot_candidates(
        "rq",
        "rq/rq",
        "a" * 40,
        date(2026, 10, 30),
        issues,
        pull_requests,
        {"src/rq/worker.py", "tests/test_worker.py"},
    )

    assert len(result) == 1
    assert result[0]["issue_number"] == 10
    assert result[0]["pr_number"] == 20
    assert result[0]["changed_source_files"] == ["src/rq/worker.py"]
    assert result[0]["issue_body"] == "A report with contact [redacted email]"
    assert result[0]["diff_command"] == "gh pr diff 20 --repo rq/rq"
