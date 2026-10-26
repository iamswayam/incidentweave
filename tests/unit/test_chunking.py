from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from app.retrieval.chunking import (
    AST_CHUNKER_VERSION,
    AST_MAX_LINES,
    AST_MIN_LINES,
    EMBEDDING_TEXT_VERSION,
    ChunkSpec,
    ast_chunk_specs,
    describe_chunker,
    embedding_text,
    line_window_specs,
)
from evaluation import chunk_experiments
from evaluation.chunk_experiments import (
    CANDIDATE_STRATEGIES,
    candidate_chunk_specs,
    candidate_embedding_text,
    get_candidate_strategy,
)
from scripts.ingest_repo import chunk_lines


@pytest.mark.parametrize("line_count", [0, 5, 60, 61, 201])
def test_line_windows_match_ingestion_ranges(line_count: int) -> None:
    source = "\n".join(f"line {index}" for index in range(line_count))
    expected = [
        (start + 1, end)
        for start, end in chunk_lines(source.splitlines(), 60, 10)
    ]
    observed = [
        (spec.line_start, spec.line_end)
        for spec in line_window_specs(source)
    ]

    assert observed == expected


def test_line_windows_reject_non_positive_step() -> None:
    with pytest.raises(ValueError, match="greater than overlap"):
        line_window_specs("a\nb", size=10, overlap=10)


def test_blank_only_source_has_no_chunks() -> None:
    source = " \n\t\n"

    assert line_window_specs(source) == []
    assert ast_chunk_specs(source) == []


def test_ast_collects_top_level_sync_async_and_decorated_functions() -> None:
    source = (
        "@decorate\n"
        "def sync():\n"
        + "".join(f"    value_{index} = {index}\n" for index in range(8))
        + "\nasync def async_fn():\n"
        + "".join(f"    value_{index} = {index}\n" for index in range(8))
        + "\n@first\n@second\ndef decorated():\n"
        + "".join(f"    value_{index} = {index}\n" for index in range(8))
    )

    specs = ast_chunk_specs(source)
    by_name = {spec.function_name: spec for spec in specs if spec.function_name}

    assert by_name["sync"].symbol == "sync"
    assert by_name["async_fn"].symbol == "async_fn"
    assert by_name["decorated"].kind == "function"
    assert by_name["decorated"].line_start == 22
    assert by_name["decorated"].content.startswith("@first\n@second")


def test_class_body_and_direct_methods_have_structural_metadata() -> None:
    source = (
        "class Sample:\n"
        '    \"\"\"Class documentation.\"\"\"\n'
        "    value = 1\n"
        "    # retained class-body line 1\n"
        "    # retained class-body line 2\n"
        "    # retained class-body line 3\n"
        "    # retained class-body line 4\n"
        "    # retained class-body line 5\n"
        "    # retained class-body line 6\n"
        "    # retained class-body line 7\n"
        "    def first(self):\n"
        "        value = 1\n"
        "        value += 1\n"
        "        value += 1\n"
        "        value += 1\n"
        "        value += 1\n"
        "        value += 1\n"
        "        return value\n"
        "    def second(self):\n"
        "        value = 2\n"
        "        value += 1\n"
        "        value += 1\n"
        "        value += 1\n"
        "        value += 1\n"
        "        value += 1\n"
        "        return value\n"
    )

    specs = ast_chunk_specs(source)
    class_body = next(spec for spec in specs if spec.kind == "class_body")
    methods = {spec.symbol: spec for spec in specs if spec.kind == "method"}

    assert class_body.class_name == "Sample"
    assert class_body.symbol == "Sample"
    assert class_body.function_name is None
    assert set(methods) == {"Sample.first", "Sample.second"}
    assert all(spec.class_name == "Sample" for spec in methods.values())


def test_nested_function_remains_inside_its_enclosing_function() -> None:
    source = (
        "def outer():\n"
        "    def inner():\n"
        "        return 1\n"
        "    return inner()\n"
    )

    specs = ast_chunk_specs(source)

    assert len(specs) == 1
    assert specs[0].symbol == "outer"
    assert "def inner" in specs[0].content
    assert all(spec.symbol != "outer.inner" for spec in specs)


def test_ast_specs_cover_each_nonblank_line_once_in_order() -> None:
    source = (
        "MODULE = 1\n"
        "\n"
        "def first():\n"
        "    return MODULE\n"
        "\n"
        "class Container:\n"
        "    value = 2\n"
        "\n"
        "    def method(self):\n"
        "        return self.value\n"
        "\n"
        "def final():\n"
        "    return 3\n"
    )

    specs = ast_chunk_specs(source)
    assert [(spec.line_start, spec.line_end) for spec in specs] == sorted(
        (spec.line_start, spec.line_end) for spec in specs
    )
    covered: dict[int, int] = {}
    for spec in specs:
        assert spec.line_start <= spec.line_end
        for line_number in range(spec.line_start, spec.line_end + 1):
            if source.splitlines()[line_number - 1].strip():
                covered[line_number] = covered.get(line_number, 0) + 1
    expected = {
        index
        for index, line in enumerate(source.splitlines(), start=1)
        if line.strip()
    }
    assert set(covered) == expected
    assert set(covered.values()) == {1}


def test_long_function_splits_into_overlapping_windows_with_same_symbol() -> None:
    source = "def large():\n" + "".join(
        f"    value_{index} = {index}\n" for index in range(100)
    )

    specs = ast_chunk_specs(source)

    assert len(specs) == 2
    assert all(spec.symbol == "large" for spec in specs)
    assert specs[0].line_start == 1
    assert specs[0].line_end == 60
    assert specs[1].line_start == 51
    assert specs[1].line_end == 101
    assert specs[0].line_end - specs[1].line_start + 1 == 10


def test_adjacent_tiny_functions_merge_and_oversized_split_is_not_merged() -> None:
    tiny_source = "def first():\n    return 1\n\ndef second():\n    return 2\n"
    tiny_specs = ast_chunk_specs(tiny_source)
    assert len(tiny_specs) == 1
    assert tiny_specs[0].kind == "merged"
    assert tiny_specs[0].symbol == "first"

    large_source = "def large():\n" + "".join(
        f"    value_{index} = {index}\n" for index in range(100)
    )
    specs = ast_chunk_specs(large_source + "\ndef tiny():\n    return 1\n")
    assert all(spec.kind != "merged" for spec in specs if spec.symbol == "large")
    assert any(spec.symbol == "tiny" for spec in specs)


def test_small_function_does_not_merge_with_unit_over_maximum_size() -> None:
    large = "def large():\n" + "".join(
        f"    value_{index} = {index}\n" for index in range(74)
    )
    tiny = "def tiny():\n" + "".join(
        f"    value_{index} = {index}\n" for index in range(6)
    )
    specs = ast_chunk_specs(large + "\n" + tiny)

    assert any(spec.kind == "merged" and spec.symbol == "large" for spec in specs)
    assert all(spec.kind != "merged" for spec in specs if spec.symbol == "tiny")
    assert any(spec.symbol == "tiny" for spec in specs)


def test_syntax_error_falls_back_to_line_windows() -> None:
    source = "def broken(:\n    pass\n" + "value = 1\n" * 65

    specs = ast_chunk_specs(source)

    assert specs
    assert all(spec.fallback for spec in specs)
    assert [
        (spec.line_start, spec.line_end) for spec in specs
    ] == [
        (spec.line_start, spec.line_end)
        for spec in line_window_specs(source)
    ]


@pytest.mark.parametrize(
    "source",
    [
        "import os\n# page\x0c break\n\n\ndef a():\n    return 1\n",
        'X = "a\u2028b"\n\n\ndef a():\n    return 1\n',
    ],
)
def test_parser_and_splitlines_break_mismatch_falls_back(source: str) -> None:
    specs = ast_chunk_specs(source)

    assert specs
    assert all(spec.fallback for spec in specs)
    assert [
        (spec.line_start, spec.line_end) for spec in specs
    ] == [
        (spec.line_start, spec.line_end)
        for spec in line_window_specs(source)
    ]


def test_ast_source_without_trailing_newline_does_not_fall_back() -> None:
    specs = ast_chunk_specs("def a():\n    return 1")

    assert len(specs) == 1
    assert specs[0].fallback is False
    assert specs[0].symbol == "a"


def test_ast_crlf_source_does_not_fall_back() -> None:
    specs = ast_chunk_specs("def a():\r\n    return 1\r\n")

    assert len(specs) == 1
    assert specs[0].fallback is False
    assert specs[0].symbol == "a"


def test_ast_chunking_is_deterministic() -> None:
    source = "def one():\n    return 1\n\nclass Two:\n    def method(self):\n        return 2\n"

    assert ast_chunk_specs(source) == ast_chunk_specs(source)


def test_embedding_text_preserves_spec_and_adds_path_and_optional_symbol() -> None:
    spec = ChunkSpec(3, 4, "def run():\n    return 1", "function", "run", "run", None)
    original = (
        spec.content,
        spec.line_start,
        spec.line_end,
        hashlib.sha256(spec.content.encode()).hexdigest(),
    )
    enriched = embedding_text(spec, "src/example.py")

    assert enriched.startswith("path: src/example.py\nsymbol: run\n\n")
    assert enriched.endswith(spec.content)
    assert original == (
        spec.content,
        spec.line_start,
        spec.line_end,
        hashlib.sha256(spec.content.encode()).hexdigest(),
    )
    with pytest.raises(FrozenInstanceError):
        spec.content = "changed"  # type: ignore[misc]

    no_symbol = ChunkSpec(1, 1, "value = 1", "module", None, None, None)
    assert embedding_text(no_symbol, "module.py") == "path: module.py\n\nvalue = 1"


def test_candidate_registry_and_embedding_text_are_isolated() -> None:
    assert set(CANDIDATE_STRATEGIES) == {
        "s0_lines_60_10",
        "s1_lines_100_20",
        "s2_ast_v1",
        "s3_ast_v1_embed_text",
    }
    with pytest.raises(ValueError, match="s0_lines_60_10"):
        get_candidate_strategy("unknown")

    source = "def run():\n    return 1\n"
    s2_specs = candidate_chunk_specs("s2_ast_v1", source)
    s3_specs = candidate_chunk_specs("s3_ast_v1_embed_text", source)
    assert s2_specs == s3_specs
    assert candidate_embedding_text("s2_ast_v1", s2_specs[0], "src/run.py") == (
        s2_specs[0].content
    )
    assert candidate_embedding_text(
        "s3_ast_v1_embed_text", s3_specs[0], "src/run.py"
    ) == embedding_text(s3_specs[0], "src/run.py")
    assert "s2_ast_v1" not in chunk_experiments.STRATEGIES
    assert chunk_experiments.EVALUATION_REPOSITORIES == {
        "incidentweave-eval",
        "incidentweave-eval-w100_20",
    }


def test_candidate_line_strategies_use_requested_windows() -> None:
    source = "\n".join(f"line {index}" for index in range(121))
    s0 = candidate_chunk_specs("s0_lines_60_10", source)
    s1 = candidate_chunk_specs("s1_lines_100_20", source)

    assert (s0[0].line_start, s0[0].line_end) == (1, 60)
    assert (s1[0].line_start, s1[0].line_end) == (1, 100)
    assert candidate_embedding_text("s0_lines_60_10", s0[0], "x.py") == s0[0].content


def test_chunker_descriptors_are_frozen_and_candidate_module_is_pure() -> None:
    assert describe_chunker("lines") == {
        "chunker": "lines",
        "size": 60,
        "overlap": 10,
    }
    assert describe_chunker("ast") == {
        "chunker": "ast",
        "version": AST_CHUNKER_VERSION,
        "max_lines": AST_MAX_LINES,
        "min_lines": AST_MIN_LINES,
        "window_size": 60,
        "window_overlap": 10,
    }
    with pytest.raises(ValueError, match="Unknown chunker"):
        describe_chunker("other")
    assert AST_MIN_LINES == 8
    assert EMBEDDING_TEXT_VERSION == "embed-path-symbol-v1"
    source = Path("app/retrieval/chunking.py").read_text(encoding="utf-8").lower()
    assert "sqlalchemy" not in source
    assert "google" not in source
    assert "httpx" not in source


def test_nested_class_methods_are_not_separate_units() -> None:
    source = (
        "class Outer:\n"
        "    class Inner:\n"
        "        def method(self):\n"
        "            return 1\n"
    )

    specs = ast_chunk_specs(source)

    assert all(spec.symbol != "Inner.method" for spec in specs)
    assert all(spec.kind != "method" for spec in specs)
