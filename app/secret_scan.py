"""Pattern-based detection of possible secrets in repository text."""

from __future__ import annotations

import re

SECRET_PATTERNS = (
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    (
        "private_key",
        re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "generic_assignment",
        re.compile(
            r"""(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['"][^'"\s]{16,}['"]"""
        ),
    ),
)


def find_secret(text: str) -> str | None:
    """Return the first matching secret pattern name without returning the match."""

    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return name
    return None
