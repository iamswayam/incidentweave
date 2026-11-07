"""Shared text normalization helpers."""

from __future__ import annotations


def normalize_whitespace(text: str) -> str:
    """Collapse all whitespace runs to one ASCII space."""

    return " ".join(text.split())
