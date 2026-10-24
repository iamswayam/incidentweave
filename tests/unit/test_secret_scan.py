import pytest

from app.secret_scan import find_secret


@pytest.mark.parametrize(
    ("secret", "expected_name"),
    [
        ("AIza" + "A" * 35, "google_api_key"),
        ("AKIA" + "A" * 16, "aws_access_key"),
        ("ghp_" + "A" * 36, "github_token"),
        ("xoxb-" + "A" * 10, "slack_token"),
        ("-----BEGIN PRIVATE KEY-----", "private_key"),
        ("api_key='" + "A" * 16 + "'", "generic_assignment"),
    ],
)
def test_find_secret_returns_pattern_name_only(secret: str, expected_name: str) -> None:
    assert find_secret(f"example = '{secret}'") == expected_name


def test_find_secret_returns_none_for_normal_code() -> None:
    assert find_secret("def add(left, right):\n    return left + right") is None
