"""Review-pack workflows for v2 evaluation questions."""

from __future__ import annotations

import json
import math
import random
import re
from collections import defaultdict
from datetime import date
from pathlib import Path, PurePosixPath
from statistics import median
from typing import Any

from evaluation.candidates import _cached_clone, mine_candidate_issues
from evaluation.manifest import MANIFEST_PATH
from evaluation.question_set import (
    build_question_set,
    derive_relevant_labels,
    legacy_category,
    validate_question_set,
)
from evaluation.stats import wilson_interval

ROOT = Path(__file__).resolve().parents[1]
QUESTION_CACHE_ROOT = ROOT / "evaluation" / "cache" / "questions"
QUALIFY_CACHE_ROOT = ROOT / "evaluation" / "cache" / "qualify"
GUIDELINES_LINK = "../../../repos/README.md#labelling-guidelines"
PACK_HEADING = re.compile(
    r"^## (Q-\d{3}) \| (answerable|unanswerable) \| "
    r"(mined|drafted|human)(?: \(issue #(\d+), PR #(\d+)\))?$"
)
GOLD_LINE = re.compile(r"^- (.+?) : (\d+)-(\d+)$")
ABSENCE_LINE = re.compile(r"^(.+?) -> (\d+) hits at ([0-9a-fA-F]{40})$")
SECOND_PASS_HEADING = re.compile(r"^## Item (\d+)$")


def _one_line(value: object) -> str:
    return " ".join(str(value or "").splitlines()).strip()


def _read_manifest_candidates(path: Path) -> dict[str, dict[str, Any]]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read candidate manifest {path}: {exc}") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("candidates"), list):
        raise ValueError(f"{path}: manifest must contain a candidates list")
    candidates: dict[str, dict[str, Any]] = {}
    for candidate in manifest["candidates"]:
        if not isinstance(candidate, dict) or not isinstance(candidate.get("id"), str):
            continue
        repo_id = candidate["id"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", repo_id):
            raise ValueError(f"{path}: unsafe candidate id {repo_id!r}")
        if repo_id in candidates:
            raise ValueError(f"{path}: duplicate candidate id {repo_id!r}")
        candidates[repo_id] = candidate
    return candidates


def mine_issues(
    repo_id: str,
    *,
    manifest_path: Path = MANIFEST_PATH,
    qualify_cache_root: Path = QUALIFY_CACHE_ROOT,
    question_cache_root: Path = QUESTION_CACHE_ROOT,
) -> Path:
    """Mine linked issues for one candidate using its cached pinned clone."""

    candidate = _read_manifest_candidates(manifest_path).get(repo_id)
    if candidate is None:
        raise ValueError(f"{repo_id!r} is not a candidate in the manifest")
    return mine_candidate_issues(
        candidate,
        cache_root=qualify_cache_root,
        question_cache_root=question_cache_root,
    )


def render_pack(
    repo_id: str,
    pinned_sha: str,
    items: list[dict[str, Any]],
) -> tuple[str, dict[str, Any], int]:
    """Render a review pack, its original-item metadata, and skipped count."""

    lines = [
        f"# Question review pack: {repo_id}",
        "",
        f"Pinned SHA: `{pinned_sha}`",
        "",
        "Fill Question, Type or Kind, Gold or Absence check, Evidence, Decision, Minutes, "
        "and Notes.",
        "Set Decision to `accept` or `reject`; record whole minutes including review.",
        f"Guidelines: [Labelling guidelines]({GUIDELINES_LINK})",
        "",
    ]
    metadata: dict[str, Any] = {
        "repo_id": repo_id,
        "pinned_sha": pinned_sha,
        "items": {},
    }
    skipped = 0
    number = 0
    for item in items:
        question = _one_line(item.get("question"))
        if not question:
            skipped += 1
            continue
        number += 1
        block_id = f"Q-{number:03d}"
        source = item["source"]
        mined = item.get("mined")
        answerable = bool(item.get("answerable"))
        source_label = source
        if source == "mined":
            if not isinstance(mined, dict):
                raise ValueError(f"{item.get('candidate_id')}: mined record is missing")
            source_label = (
                f"mined (issue #{mined['issue_number']}, PR #{mined['pr_number']})"
            )
        lines.append(
            f"## {block_id} | {'answerable' if answerable else 'unanswerable'} | "
            f"{source_label}"
        )
        if isinstance(mined, dict):
            lines.extend(
                [
                    f"Issue title: {_one_line(mined.get('issue_title'))}",
                    f"Issue quote: > {_one_line(mined.get('issue_body'))[:280]}",
                ]
            )
        lines.append(f"Question: {question}")
        if answerable:
            lines.append(f"Type: {_one_line(item.get('type'))}")
            lines.append("Gold:")
            for gold in item.get("gold", []):
                lines.append(
                    f"- {_one_line(gold.get('path'))} : {gold.get('start')}-{gold.get('end')}"
                )
        else:
            absence = item.get("absence_check", {})
            lines.extend(
                [
                    f"Kind: {_one_line(item.get('kind'))}",
                    "Absence check: "
                    f"{', '.join(map(str, absence.get('terms', [])))} -> "
                    f"{absence.get('hits')} hits at {pinned_sha}",
                ]
            )
        lines.append(f"Evidence: {_one_line(item.get('evidence'))}")
        if answerable:
            for gold in item.get("gold", []):
                path = _one_line(gold.get("path"))
                start = gold.get("start")
                end = gold.get("end")
                lines.append(
                    f"Link: https://github.com/{item['owner']}/{item['repo']}/blob/"
                    f"{pinned_sha}/{path}#L{start}-L{end}"
                )
        lines.extend(["Decision:", "Minutes:", "Notes:", ""])
        metadata["items"][block_id] = {
            "candidate_id": item.get("candidate_id"),
            "original": item,
            "mined": mined,
        }
    return "\n".join(lines), metadata, skipped


def parse_pack(text: str, *, require_decisions: bool = False) -> list[dict[str, Any]]:
    """Parse review blocks; every malformed field includes its source line."""

    lines = text.splitlines()
    headings = [
        (line_number, PACK_HEADING.fullmatch(line))
        for line_number, line in enumerate(lines, start=1)
        if line.startswith("## ")
    ]
    errors = [
        f"line {line_number}: malformed question block heading"
        for line_number, match in headings
        if match is None
    ]
    if errors:
        raise ValueError("; ".join(errors))
    expected = {
        "answerable": {
            "Question",
            "Type",
            "Gold",
            "Evidence",
            "Decision",
            "Minutes",
            "Notes",
        },
        "unanswerable": {
            "Question",
            "Kind",
            "Absence check",
            "Evidence",
            "Decision",
            "Minutes",
            "Notes",
        },
    }
    known_fields = {
        "Question",
        "Type",
        "Gold",
        "Evidence",
        "Decision",
        "Minutes",
        "Notes",
        "Kind",
        "Absence check",
    }
    blocks: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for block_index, (start_line, match) in enumerate(headings):
        assert match is not None
        end_line = (
            headings[block_index + 1][0] - 1
            if block_index + 1 < len(headings)
            else len(lines)
        )
        block_id, status, source, issue, pr = match.groups()
        if block_id in seen_ids:
            errors.append(f"line {start_line}: duplicate question block {block_id}")
        seen_ids.add(block_id)
        fields: dict[str, tuple[str, int]] = {}
        gold: list[dict[str, Any]] = []
        current_field: str | None = None
        for line_number in range(start_line + 1, end_line + 1):
            line = lines[line_number - 1]
            if not line.strip():
                continue
            if line.startswith(("Link: ", "Issue title: ", "Issue quote: ")):
                continue
            if line.startswith("- "):
                if current_field != "Gold":
                    errors.append(f"line {line_number}: gold path outside Gold field")
                    continue
                span_match = GOLD_LINE.fullmatch(line)
                if span_match is None:
                    errors.append(
                        f"line {line_number}: malformed gold span; "
                        "expected '- path : start-end'"
                    )
                    continue
                path, span_start, span_end = span_match.groups()
                start, end = int(span_start), int(span_end)
                if start < 1 or end < start:
                    errors.append(f"line {line_number}: gold span range is invalid")
                gold.append({"path": path, "start": start, "end": end})
                continue
            field_match = re.match(r"^([A-Za-z ]+):(?:\s*(.*))?$", line)
            if field_match is None:
                errors.append(f"line {line_number}: malformed review field")
                continue
            name, value = field_match.groups()
            name = name.strip()
            if name not in known_fields:
                errors.append(f"line {line_number}: unknown review field {name!r}")
                continue
            if name in fields:
                errors.append(f"line {line_number}: duplicate {name} field")
                continue
            fields[name] = (value or "", line_number)
            current_field = name
        for field, (_, field_line) in fields.items():
            if field not in expected[status]:
                errors.append(
                    f"line {field_line}: {field} field is invalid for {status} questions"
                )
        for field in expected[status]:
            if field not in fields:
                errors.append(f"line {start_line}: missing {field} field in {block_id}")
        question = fields.get("Question", ("", start_line))[0]
        question_type = fields.get("Type", ("", start_line))[0] or None
        kind = fields.get("Kind", ("", start_line))[0] or None
        if not question.strip():
            errors.append(
                f"line {fields.get('Question', ('', start_line))[1]}: Question is required"
            )
        if status == "answerable" and not question_type:
            errors.append(f"line {start_line}: Type is required")
        if status == "answerable" and not gold:
            errors.append(f"line {start_line}: Gold needs a span")
        if status == "unanswerable" and not kind:
            errors.append(f"line {start_line}: Kind is required")
        decision = fields.get("Decision", ("", start_line))[0].casefold()
        minutes_text, minutes_line = fields.get("Minutes", ("", start_line))
        minutes = int(minutes_text) if re.fullmatch(r"\d+", minutes_text) else None
        if require_decisions and decision not in {"accept", "reject"}:
            errors.append(
                f"line {fields.get('Decision', ('', start_line))[1]}: "
                "Decision must be accept or reject"
            )
        if require_decisions and minutes is None:
            errors.append(f"line {minutes_line}: Minutes must be a non-negative integer")
        absence_terms: list[str] = []
        absence_hits: int | None = None
        absence_sha: str | None = None
        if status == "unanswerable" and "Absence check" in fields:
            absence_text, absence_line = fields["Absence check"]
            absence_match = ABSENCE_LINE.fullmatch(absence_text)
            if absence_match is None:
                errors.append(f"line {absence_line}: malformed Absence check")
            else:
                term_text, hits_text, absence_sha = absence_match.groups()
                absence_terms = [term.strip() for term in term_text.split(",") if term.strip()]
                absence_hits = int(hits_text)
        blocks.append(
            {
                "block_id": block_id,
                "answerable": status == "answerable",
                "source": source,
                "issue_number": int(issue) if issue else None,
                "pr_number": int(pr) if pr else None,
                "question": question,
                "type": question_type,
                "kind": kind,
                "gold": gold,
                "evidence": fields.get("Evidence", ("", start_line))[0],
                "absence_terms": absence_terms,
                "absence_hits": absence_hits,
                "absence_sha": absence_sha,
                "decision": decision,
                "minutes": minutes,
                "line": start_line,
            }
        )
    if errors:
        raise ValueError("; ".join(errors))
    return blocks


def create_review_pack(
    repo_id: str,
    *,
    manifest_path: Path = MANIFEST_PATH,
    question_cache_root: Path = QUESTION_CACHE_ROOT,
) -> tuple[Path, int]:
    candidate = _read_manifest_candidates(manifest_path).get(repo_id)
    if candidate is None:
        raise ValueError(f"{repo_id!r} is not a candidate in the manifest")
    if not isinstance(candidate.get("url"), str) or not isinstance(
        candidate.get("pinned_sha"), str
    ):
        raise ValueError(f"{repo_id}: candidate URL and pinned_sha are required")
    cache_dir = question_cache_root / repo_id
    drafts_path = cache_dir / "drafts.json"
    if not drafts_path.is_file():
        raise FileNotFoundError(f"{drafts_path} is missing; prepare drafts.json first")
    drafts = json.loads(drafts_path.read_text(encoding="utf-8"))
    if not isinstance(drafts, list) or any(not isinstance(item, dict) for item in drafts):
        raise ValueError("drafts.json must be a list of question draft objects")
    mined_path = cache_dir / "mined.json"
    if mined_path.exists():
        mined_data = json.loads(mined_path.read_text(encoding="utf-8"))
        if not isinstance(mined_data, list):
            raise ValueError(f"{mined_path}: mined issue data must be a list")
    else:
        mined_data = []
    mined = {
        item["candidate_id"]: item
        for item in mined_data
        if isinstance(item, dict) and isinstance(item.get("candidate_id"), str)
    }
    repository_parts = PurePosixPath(
        candidate["url"].removeprefix("https://github.com/")
    ).parts
    if len(repository_parts) != 2:
        raise ValueError("candidate URL must identify owner/repository")
    drafts_by_id: dict[str, dict[str, Any]] = {}
    for draft in drafts:
        candidate_id = draft.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            raise ValueError("every draft needs a candidate_id")
        source = draft.get("source")
        expected_prefix = "M-" if source == "mined" else "D-"
        if source not in {"mined", "drafted", "human"} or not candidate_id.startswith(
            expected_prefix
        ):
            raise ValueError(f"{candidate_id}: candidate_id prefix does not match source")
        if candidate_id in drafts_by_id:
            raise ValueError(f"duplicate draft candidate_id {candidate_id!r}")
        drafts_by_id[candidate_id] = draft

    items: list[dict[str, Any]] = []
    for candidate_id, mined_record in mined.items():
        draft = drafts_by_id.pop(candidate_id, {"candidate_id": candidate_id, "source": "mined"})
        items.append(
            {
                **draft,
                "answerable": "kind" not in draft,
                "mined": mined_record,
                "owner": repository_parts[0],
                "repo": repository_parts[1],
            }
        )
    for candidate_id, draft in drafts_by_id.items():
        if draft.get("source") == "mined":
            raise ValueError(f"{candidate_id}: mined draft has no matching mined issue")
        items.append(
            {
                **draft,
                "answerable": "kind" not in draft,
                "owner": repository_parts[0],
                "repo": repository_parts[1],
            }
        )
    text, metadata, skipped = render_pack(repo_id, candidate.get("pinned_sha", ""), items)
    cache_dir.mkdir(parents=True, exist_ok=True)
    pack_path = cache_dir / "pack.md"
    pack_path.write_text(text, encoding="utf-8")
    (cache_dir / "pack-meta.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return pack_path, skipped


def _pre_review_leakage(drafts: list[dict[str, Any]]) -> int:
    from app.secret_scan import find_secret

    violations = 0
    for draft in drafts:
        question = _one_line(draft.get("question"))
        evidence = _one_line(draft.get("evidence"))
        if find_secret(question) or find_secret(evidence):
            violations += 1
        else:
            lowered = question.casefold()
            for span in draft.get("gold", []):
                path = str(span.get("path") or "")
                basename = PurePosixPath(path).name
                if path and (
                    path.casefold() in lowered or basename.casefold() in lowered
                ):
                    violations += 1
                    break
    return violations


def ingest_review_pack(
    repo_id: str,
    *,
    targets: str,
    manifest_path: Path = MANIFEST_PATH,
    question_cache_root: Path = QUESTION_CACHE_ROOT,
    output_root: Path = ROOT,
    snapshot_root: Path | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """Validate a completed pack, then write the accepted v2 question set."""

    if targets not in {"full", "reduced"}:
        raise ValueError("targets must be full or reduced")
    candidate = _read_manifest_candidates(manifest_path).get(repo_id)
    if candidate is None:
        raise ValueError(f"{repo_id!r} is not a candidate in the manifest")
    pinned_sha = candidate.get("pinned_sha")
    if not isinstance(pinned_sha, str):
        raise ValueError(f"{repo_id}: candidate pinned_sha is required")
    cache_dir = question_cache_root / repo_id
    pack_path = cache_dir / "pack.md"
    meta_path = cache_dir / "pack-meta.json"
    drafts_path = cache_dir / "drafts.json"
    for path in (pack_path, meta_path, drafts_path):
        if not path.is_file():
            raise FileNotFoundError(f"required review input is missing: {path}")
    blocks = parse_pack(pack_path.read_text(encoding="utf-8"), require_decisions=True)
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    item_meta = metadata.get("items")
    if not isinstance(item_meta, dict):
        raise ValueError("pack metadata must contain item mapping")
    drafts = json.loads(drafts_path.read_text(encoding="utf-8"))
    if not isinstance(drafts, list) or any(not isinstance(item, dict) for item in drafts):
        raise ValueError("drafts.json must be a list of question draft objects")
    if snapshot_root is None:
        clone = _cached_clone(
            ROOT / "evaluation" / "cache" / "qualify",
            repo_id,
            pinned_sha,
        )
        snapshot_root = clone.parent / "python-snapshot"

    accepted = rejected = edited = 0
    minutes_by_item: dict[str, int] = {}
    questions: list[dict[str, Any]] = []
    for block in blocks:
        block_id = block["block_id"]
        minutes = block["minutes"]
        if minutes is None:
            raise ValueError(f"line {block['line']}: Minutes must be a non-negative integer")
        minutes_by_item[block_id] = minutes
        entry = item_meta.get(block_id)
        if not isinstance(entry, dict) or not isinstance(entry.get("original"), dict):
            raise ValueError(f"line {block['line']}: original metadata missing for {block_id}")
        original = entry["original"]
        if block["source"] != original.get("source") or block["answerable"] != (
            "kind" not in original
        ):
            raise ValueError(f"line {block['line']}: source and answerability must not change")
        mined = entry.get("mined")
        if block["source"] == "mined" and (
            not isinstance(mined, dict)
            or block["issue_number"] != mined.get("issue_number")
            or block["pr_number"] != mined.get("pr_number")
        ):
            raise ValueError(f"line {block['line']}: mined issue and PR must not change")
        original_gold = [
            {"path": span.get("path"), "start": span.get("start"), "end": span.get("end")}
            for span in original.get("gold", [])
        ]
        original_absence = original.get("absence_check", {})
        edited += int(
            block["question"] != _one_line(original.get("question"))
            or block["type"] != original.get("type")
            or block["kind"] != original.get("kind")
            or block["gold"] != original_gold
            or block["evidence"] != _one_line(original.get("evidence"))
            or block["absence_terms"] != original_absence.get("terms", [])
            or block["absence_hits"] != original_absence.get("hits")
        )
        if block["decision"] == "reject":
            rejected += 1
            continue
        accepted += 1
        question: dict[str, Any] = {
            "id": block_id,
            "question": block["question"],
            "answerable": block["answerable"],
            "source": block["source"],
            "reviewed": True,
            "review_minutes": minutes,
            "evidence": block["evidence"],
        }
        if block["answerable"]:
            if not block["type"]:
                raise ValueError(f"line {block['line']}: Type is required")
            spans = [
                {"file_path": span["path"], "start": span["start"], "end": span["end"]}
                for span in block["gold"]
            ]
            question.update(
                {
                    "type": block["type"],
                    "relevant": derive_relevant_labels(spans, snapshot_root),
                    "relevant_spans": [
                        {
                            "file_path": span["path"],
                            "line_start": span["start"],
                            "line_end": span["end"],
                        }
                        for span in block["gold"]
                    ],
                }
            )
        else:
            if not block["kind"]:
                raise ValueError(f"line {block['line']}: Kind is required")
            question.update(
                {
                    "kind": block["kind"],
                    "relevant": [],
                    "relevant_spans": [],
                    "absence_check": {
                        "terms": block["absence_terms"],
                        "hits": block["absence_hits"],
                        "pinned_sha": block["absence_sha"],
                    },
                }
            )
        if block["source"] == "mined":
            question["source_ref"] = {
                "issue": block["issue_number"],
                "pr": block["pr_number"],
            }
        if block["source"] == "drafted":
            question["drafting_model"] = original.get("drafting_model")
        question["category"] = legacy_category(question)
        questions.append(question)

    question_set = build_question_set(
        repo_id,
        pinned_sha,
        questions,
        reviewed_on=today or date.today(),
        targets=targets,
    )
    errors = validate_question_set(
        question_set,
        repo_id=repo_id,
        pinned_sha=pinned_sha,
        snapshot_root=snapshot_root,
        targets=targets,
    )
    if errors:
        raise ValueError("v2 question validation failed: " + "; ".join(errors))
    output_path = output_root / "evaluation" / "repos" / repo_id / "questions.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(question_set, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    minute_values = list(minutes_by_item.values())
    report = {
        "repo_id": repo_id,
        "accepted": accepted,
        "rejected": rejected,
        "edited": edited,
        "leakage_violations_before_edits": _pre_review_leakage(drafts),
        "minutes_by_item": minutes_by_item,
        "median_minutes": median(minute_values) if minute_values else None,
    }
    (cache_dir / "ingest-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def _largest_remainder_allocation(
    strata: dict[tuple[str, bool], list[dict[str, Any]]],
    sample_size: int,
) -> dict[tuple[str, bool], int]:
    population = sum(len(items) for items in strata.values())
    if sample_size < 0 or sample_size > population:
        raise ValueError("sample size must be within the population")
    exact = {key: sample_size * len(items) / population for key, items in strata.items()}
    allocation = {
        key: min(len(strata[key]), math.floor(count))
        for key, count in exact.items()
    }
    remaining = sample_size - sum(allocation.values())
    order = sorted(
        strata,
        key=lambda key: (-(exact[key] - math.floor(exact[key])), key),
    )
    while remaining:
        progressed = False
        for key in order:
            if allocation[key] < len(strata[key]):
                allocation[key] += 1
                remaining -= 1
                progressed = True
                if remaining == 0:
                    break
        if not progressed:
            raise ValueError("cannot allocate sample across strata")
    return allocation


def stratified_sample(
    repository_questions: dict[str, list[dict[str, Any]]],
    *,
    seed: int = 20261102,
) -> list[dict[str, Any]]:
    """Sample max(16, 20%) with largest-remainder repository/answerability strata."""

    rows = [
        {"repo_id": repo_id, "question": question}
        for repo_id, questions in repository_questions.items()
        for question in questions
    ]
    if not rows:
        raise ValueError("second pass needs at least one question")
    size = min(len(rows), max(16, math.ceil(0.2 * len(rows))))
    strata: dict[tuple[str, bool], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        answerable = row["question"].get("answerable")
        if not isinstance(answerable, bool):
            raise ValueError(f"{row['repo_id']}: question answerable must be boolean")
        strata[(row["repo_id"], answerable)].append(row)
    allocation = _largest_remainder_allocation(strata, size)
    rng = random.Random(seed)
    selected = [
        row
        for key in sorted(strata)
        for row in rng.sample(strata[key], allocation[key])
    ]
    rng.shuffle(selected)
    return selected


def render_second_pass(sampled: list[dict[str, Any]]) -> str:
    lines = [
        "# Blind second pass",
        "",
        "Relabel each item independently. Do not consult first-pass labels. "
        "Answer yes or no; list each gold file as `- path`; use whole minutes.",
        "",
    ]
    for index, row in enumerate(sampled, start=1):
        lines.extend(
            [
                f"## Item {index}",
                "",
                _one_line(row["question"].get("question")),
                "",
                "Answerable:",
                "Gold files:",
                "Minutes:",
                "",
            ]
        )
    return "\n".join(lines)


def create_second_pass(
    repo_ids: list[str],
    *,
    output_root: Path = ROOT,
    question_cache_root: Path = QUESTION_CACHE_ROOT,
    today: date | None = None,
) -> tuple[Path, int]:
    if not repo_ids or len(repo_ids) != len(set(repo_ids)):
        raise ValueError("second pass requires unique repository ids")
    repository_questions: dict[str, list[dict[str, Any]]] = {}
    for repo_id in repo_ids:
        path = output_root / "evaluation" / "repos" / repo_id / "questions.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("repo_id") != repo_id or not isinstance(data.get("questions"), list):
            raise ValueError(f"{path}: invalid v2 question set")
        repository_questions[repo_id] = data["questions"]
    sampled = stratified_sample(repository_questions)
    created_on = today or date.today()
    metadata = {
        "created_on": created_on.isoformat(),
        "seed": 20261102,
        "sample_size": len(sampled),
        "sample": [
            {
                "repo_id": row["repo_id"],
                "question_id": row["question"]["id"],
                "answerable": row["question"]["answerable"],
                "gold_files": sorted(
                    {
                        span["file_path"]
                        for span in row["question"].get("relevant_spans", [])
                    }
                ),
            }
            for row in sampled
        ],
    }
    output_dir = question_cache_root / "second-pass"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "second-pass.md"
    output_path.write_text(render_second_pass(sampled), encoding="utf-8")
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_path, len(sampled)


def parse_second_pass(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    headings = [
        (line_number, SECOND_PASS_HEADING.fullmatch(line))
        for line_number, line in enumerate(lines, start=1)
        if line.startswith("## ")
    ]
    errors = [
        f"line {line_number}: malformed second-pass heading"
        for line_number, match in headings
        if match is None
    ]
    if errors:
        raise ValueError("; ".join(errors))
    results: list[dict[str, Any]] = []
    for index, (start_line, match) in enumerate(headings):
        assert match is not None
        end_line = headings[index + 1][0] - 1 if index + 1 < len(headings) else len(lines)
        fields: dict[str, tuple[str, int]] = {}
        question_lines: list[str] = []
        in_gold = False
        for line_number in range(start_line + 1, end_line + 1):
            line = lines[line_number - 1]
            if not line.strip():
                continue
            field_match = re.match(r"^(Answerable|Gold files|Minutes):\s*(.*)$", line)
            if field_match:
                field, value = field_match.groups()
                fields[field] = (value, line_number)
                in_gold = field == "Gold files"
                continue
            if in_gold and line.startswith("- "):
                value, source_line = fields["Gold files"]
                fields["Gold files"] = (f"{value}\n{line[2:]}", source_line)
                continue
            if not fields:
                question_lines.append(line)
        for field in ("Answerable", "Gold files", "Minutes"):
            if field not in fields:
                errors.append(f"line {start_line}: missing {field} in Item {match.group(1)}")
        answer_text, answer_line = fields.get("Answerable", ("", start_line))
        answer_text = answer_text.casefold()
        if answer_text not in {"yes", "no"}:
            errors.append(f"line {answer_line}: Answerable must be yes or no")
        gold_text, gold_line = fields.get("Gold files", ("", start_line))
        gold_files = sorted(
            {
                item.strip().removeprefix("- ").strip()
                for item in gold_text.splitlines()
                if item.strip()
            }
        )
        minutes_text, minutes_line = fields.get("Minutes", ("", start_line))
        valid_minutes = re.fullmatch(r"\d+", minutes_text) is not None
        if not valid_minutes:
            errors.append(f"line {minutes_line}: Minutes must be a non-negative integer")
        if answer_text == "yes" and not gold_files:
            errors.append(f"line {gold_line}: answerable item needs at least one gold file")
        if answer_text == "no" and gold_files:
            errors.append(f"line {gold_line}: unanswerable item must have no gold files")
        results.append(
            {
                "item": int(match.group(1)),
                "question": "\n".join(question_lines),
                "answerable": answer_text == "yes",
                "gold_files": gold_files,
                "minutes": int(minutes_text) if valid_minutes else None,
            }
        )
    if errors:
        raise ValueError("; ".join(errors))
    return results


def _agreement_record(successes: int, total: int) -> dict[str, Any]:
    low, high = wilson_interval(successes, total)
    rate = successes / total if total else 0.0
    return {
        "agreement": successes,
        "total": total,
        "rate": rate,
        "wilson_95": [low, high],
        "passed": bool(total and rate >= 0.9),
    }


def calculate_agreement(
    sample_metadata: list[dict[str, Any]],
    second_pass: list[dict[str, Any]],
) -> dict[str, Any]:
    if len(sample_metadata) != len(second_pass):
        raise ValueError("second-pass answers do not match sampled item count")
    answer_matches = gold_matches = exact_matches = answerable_total = 0
    for index, (original, reviewed) in enumerate(
        zip(sample_metadata, second_pass), start=1
    ):
        if reviewed["item"] != index:
            raise ValueError("second-pass item numbering does not match metadata")
        answerable = bool(original["answerable"])
        answer_matches += answerable == reviewed["answerable"]
        if answerable:
            answerable_total += 1
            original_files = set(original["gold_files"])
            reviewed_files = set(reviewed["gold_files"])
            if not original_files or not reviewed_files:
                raise ValueError(f"second-pass Item {index} needs at least one gold file")
            gold_matches += bool(original_files & reviewed_files)
            exact_matches += original_files == reviewed_files
        elif reviewed["gold_files"]:
            raise ValueError(f"second-pass Item {index} is unanswerable but has gold files")
    return {
        "answerability": _agreement_record(answer_matches, len(sample_metadata)),
        "gold_files": _agreement_record(gold_matches, answerable_total),
        "gold_files_exact_descriptive": {
            "agreement": exact_matches,
            "total": answerable_total,
            "rate": exact_matches / answerable_total if answerable_total else 0.0,
        },
    }


def run_agreement(
    repo_ids: list[str],
    *,
    output_root: Path = ROOT,
    question_cache_root: Path = QUESTION_CACHE_ROOT,
    today: date | None = None,
) -> dict[str, Any]:
    """Check review delay, calculate agreements, and save aggregate cache results."""

    if not repo_ids or len(repo_ids) != len(set(repo_ids)):
        raise ValueError("agreement requires unique repository ids")
    current_date = today or date.today()
    second_pass_dir = question_cache_root / "second-pass"
    metadata = json.loads((second_pass_dir / "metadata.json").read_text(encoding="utf-8"))
    answers = parse_second_pass(
        (second_pass_dir / "second-pass.md").read_text(encoding="utf-8")
    )
    sample = metadata.get("sample")
    if not isinstance(sample, list) or len(sample) != len(answers):
        raise ValueError("second-pass metadata is missing or does not match review items")
    if {item["repo_id"] for item in sample} != set(repo_ids):
        raise ValueError("agreement repository arguments must match the second-pass sample")
    first_pass_minutes: list[int] = []
    for repo_id in repo_ids:
        question_path = output_root / "evaluation" / "repos" / repo_id / "questions.json"
        question_set = json.loads(question_path.read_text(encoding="utf-8"))
        reviewed_on = date.fromisoformat(question_set["reviewed_on"])
        if (current_date - reviewed_on).days < 7:
            raise ValueError(
                f"{repo_id}: second pass requires at least 7 days after {reviewed_on}"
            )
        report_path = question_cache_root / repo_id / "ingest-report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        first_pass_minutes.extend(report.get("minutes_by_item", {}).values())
    result = calculate_agreement(sample, answers)
    effort = median(first_pass_minutes) if first_pass_minutes else None
    result.update(
        {
            "median_first_pass_minutes": effort,
            "median_effort_passed": effort is not None and effort <= 8,
            "created_on": metadata.get("created_on"),
            "repositories": repo_ids,
        }
    )
    (second_pass_dir / "agreement-results.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return result
