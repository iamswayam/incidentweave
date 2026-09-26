import pytest

from scripts.ingest_repo import chunk_lines


@pytest.mark.parametrize(
    ("line_count", "expected_windows"),
    [
        (0, []),
        (5, [(0, 5)]),
        (201, [(0, 60), (50, 110), (100, 160), (150, 201)]),
    ],
)
def test_chunk_lines_uses_non_redundant_overlapping_windows(
    line_count: int,
    expected_windows: list[tuple[int, int]],
) -> None:
    lines = [f"line {index}" for index in range(line_count)]

    assert list(chunk_lines(lines)) == expected_windows
