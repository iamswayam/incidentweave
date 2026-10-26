"""Pure candidate chunk specifications for offline chunking comparisons."""

import ast
from dataclasses import dataclass, replace

LINE_WINDOW_SIZE = 60
LINE_WINDOW_OVERLAP = 10
AST_CHUNKER_VERSION = "ast-v1"
AST_MAX_LINES = 80
AST_MIN_LINES = 8
EMBEDDING_TEXT_VERSION = "embed-path-symbol-v1"


@dataclass(frozen=True)
class ChunkSpec:
    line_start: int
    line_end: int
    content: str
    kind: str
    symbol: str | None
    function_name: str | None
    class_name: str | None
    fallback: bool = False


@dataclass(frozen=True)
class _Unit:
    line_start: int
    line_end: int
    kind: str
    symbol: str | None
    function_name: str | None
    class_name: str | None
    split: bool = False


def _window_ranges(
    line_start: int,
    line_end: int,
    size: int,
    overlap: int,
) -> list[tuple[int, int]]:
    step = size - overlap
    if step <= 0:
        raise ValueError("chunk size must be greater than overlap_size")
    ranges = []
    previous_end = line_start - 1
    for start in range(line_start, line_end + 1, step):
        end = min(start + size - 1, line_end)
        if end <= previous_end:
            continue
        ranges.append((start, end))
        previous_end = end
    return ranges


def line_window_specs(
    source: str,
    size: int = LINE_WINDOW_SIZE,
    overlap: int = LINE_WINDOW_OVERLAP,
) -> list[ChunkSpec]:
    lines = source.splitlines()
    specs = []
    if not lines:
        return specs
    for start, end in _window_ranges(1, len(lines), size, overlap):
        content = "\n".join(lines[start - 1 : end])
        if content.strip():
            specs.append(
                ChunkSpec(
                    line_start=start,
                    line_end=end,
                    content=content,
                    kind="lines",
                    symbol=None,
                    function_name=None,
                    class_name=None,
                )
            )
    return specs


def _definition_start(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    if node.decorator_list:
        return min(decorator.lineno for decorator in node.decorator_list)
    return node.lineno


def _definition_unit(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    class_name: str | None = None,
) -> _Unit:
    name = node.name
    symbol = f"{class_name}.{name}" if class_name else name
    return _Unit(
        line_start=_definition_start(node),
        line_end=node.end_lineno or node.lineno,
        kind="method" if class_name else "function",
        symbol=symbol,
        function_name=name,
        class_name=class_name,
    )


def _unit_content(lines: list[str], unit: _Unit) -> str:
    return "\n".join(lines[unit.line_start - 1 : unit.line_end])


def _split_unit(unit: _Unit) -> list[_Unit]:
    if unit.line_end - unit.line_start + 1 <= AST_MAX_LINES:
        return [unit]
    return [
        _Unit(
            line_start=start,
            line_end=end,
            kind=unit.kind,
            symbol=unit.symbol,
            function_name=unit.function_name,
            class_name=unit.class_name,
            split=True,
        )
        for start, end in _window_ranges(
            unit.line_start,
            unit.line_end,
            LINE_WINDOW_SIZE,
            LINE_WINDOW_OVERLAP,
        )
    ]


def _merge_units(first: _Unit, second: _Unit) -> _Unit:
    first_length = first.line_end - first.line_start + 1
    second_length = second.line_end - second.line_start + 1
    metadata = first if first_length >= second_length else second
    return _Unit(
        line_start=first.line_start,
        line_end=second.line_end,
        kind="merged",
        symbol=metadata.symbol,
        function_name=metadata.function_name,
        class_name=metadata.class_name,
    )


def ast_chunk_specs(source: str) -> list[ChunkSpec]:
    lines = source.splitlines()
    if not any(line.strip() for line in lines):
        return []
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return [
            replace(spec, fallback=True)
            for spec in line_window_specs(source)
        ]

    classes = [
        node for node in tree.body if isinstance(node, ast.ClassDef)
    ]
    definitions: list[_Unit] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.append(_definition_unit(node))
        elif isinstance(node, ast.ClassDef):
            definitions.extend(
                _definition_unit(child, node.name)
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            )

    definition_by_line: dict[int, _Unit] = {}
    for unit in definitions:
        for line_number in range(unit.line_start, unit.line_end + 1):
            definition_by_line[line_number] = unit

    class_ranges = [
        (
            min(
                (decorator.lineno for decorator in node.decorator_list),
                default=node.lineno,
            ),
            node.end_lineno or node.lineno,
            node.name,
        )
        for node in classes
    ]

    raw_units: list[_Unit] = []
    line_number = 1
    while line_number <= len(lines):
        definition = definition_by_line.get(line_number)
        if definition is not None:
            raw_units.append(definition)
            line_number = definition.line_end + 1
            continue

        class_name = next(
            (
                name
                for start, end, name in class_ranges
                if start <= line_number <= end
            ),
            None,
        )
        kind = "class_body" if class_name else "module"
        end_line = line_number
        while end_line + 1 <= len(lines):
            if end_line + 1 in definition_by_line:
                break
            next_class_name = next(
                (
                    name
                    for start, end, name in class_ranges
                    if start <= end_line + 1 <= end
                ),
                None,
            )
            if next_class_name != class_name:
                break
            end_line += 1
        raw_units.append(
            _Unit(
                line_start=line_number,
                line_end=end_line,
                kind=kind,
                symbol=class_name,
                function_name=None,
                class_name=class_name,
            )
        )
        line_number = end_line + 1

    split_units = [
        piece for unit in raw_units for piece in _split_unit(unit)
    ]
    merged_units: list[_Unit] = []
    current = split_units[0]
    for next_unit in split_units[1:]:
        current_length = current.line_end - current.line_start + 1
        next_length = next_unit.line_end - next_unit.line_start + 1
        if (
            not current.split
            and not next_unit.split
            and (current_length < AST_MIN_LINES or next_length < AST_MIN_LINES)
            and current_length + next_length <= AST_MAX_LINES
        ):
            current = _merge_units(current, next_unit)
        else:
            merged_units.append(current)
            current = next_unit
    merged_units.append(current)

    return [
        ChunkSpec(
            line_start=unit.line_start,
            line_end=unit.line_end,
            content=_unit_content(lines, unit),
            kind=unit.kind,
            symbol=unit.symbol,
            function_name=unit.function_name,
            class_name=unit.class_name,
        )
        for unit in merged_units
        if _unit_content(lines, unit).strip()
    ]


def embedding_text(spec: ChunkSpec, file_path: str) -> str:
    symbol = f"symbol: {spec.symbol}\n" if spec.symbol else ""
    return f"path: {file_path}\n{symbol}\n{spec.content}"


def describe_chunker(name: str) -> dict[str, str | int]:
    if name == "lines":
        return {
            "chunker": "lines",
            "size": LINE_WINDOW_SIZE,
            "overlap": LINE_WINDOW_OVERLAP,
        }
    if name == "ast":
        return {
            "chunker": "ast",
            "version": AST_CHUNKER_VERSION,
            "max_lines": AST_MAX_LINES,
            "min_lines": AST_MIN_LINES,
            "window_size": LINE_WINDOW_SIZE,
            "window_overlap": LINE_WINDOW_OVERLAP,
        }
    raise ValueError(f"Unknown chunker {name!r}; choose from: lines, ast")
