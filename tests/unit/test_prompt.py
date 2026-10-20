from app.investigation.prompt import (
    SYSTEM_INSTRUCTION,
    build_grounded_prompt,
    select_evidence_within_budget,
)


def test_build_grounded_prompt_under_budget_is_unchanged() -> None:
    prompt = build_grounded_prompt(
        "What is configured?",
        [
            {
                "id": 7,
                "file_path": "app/config.py",
                "line_start": 1,
                "line_end": 2,
                "vector_score": 0.3,
                "fts_score": 0.5,
                "rrf_score": 0.04,
                "content": "ANSWER = 42",
            }
        ],
    )

    assert prompt == (
        f"{SYSTEM_INSTRUCTION}\n"
        "Investigation query:\nWhat is configured?\n\n"
        "Retrieved repository evidence:\n"
        "Evidence 1 (chunk_id=7):\n"
        "File: app/config.py\n"
        "Lines: 1-2\n"
        "Vector distance: 0.3\n"
        "FTS score: 0.5\n"
        "RRF score: 0.04\n"
        "Content:\n"
        "ANSWER = 42\n\n"
        "Grounding requirement: base every statement on the evidence above. "
        "If it does not establish a diagnosis, return INSUFFICIENT_EVIDENCE "
        "and do not present a speculative explanation as fact."
    )


def test_build_grounded_prompt_drops_results_after_budget() -> None:
    prompt = build_grounded_prompt(
        "query",
        [
            {"id": 1, "file_path": "first.py", "content": "kept"},
            {"id": 2, "file_path": "second.py", "content": "dropped-second"},
            {"id": 3, "file_path": "third.py", "content": "dropped-third"},
        ],
        max_evidence_chars=4,
    )

    assert "kept" in prompt
    assert "dropped-second" not in prompt
    assert "dropped-third" not in prompt


def test_select_evidence_drops_lowest_ranked_results_in_order() -> None:
    results = [
        {"id": 1, "content": "a" * 4},
        {"id": 2, "content": "b" * 3},
        {"id": 3, "content": "c" * 2},
    ]

    kept, dropped = select_evidence_within_budget(results, max_chars=7)

    assert kept == results[:2]
    assert [result["id"] for result in kept] == [1, 2]
    assert dropped == 1


def test_select_evidence_truncates_oversized_first_result_without_mutation() -> None:
    original = {"id": 1, "content": "abcdefgh"}

    kept, dropped = select_evidence_within_budget([original], max_chars=4)

    assert kept == [{"id": 1, "content": "abcd\n[truncated]"}]
    assert kept[0] is not original
    assert original == {"id": 1, "content": "abcdefgh"}
    assert dropped == 0


def test_select_evidence_dropped_count_includes_every_result_after_overflow() -> None:
    results = [
        {"id": 1, "content": "a" * 4},
        {"id": 2, "content": "b" * 4},
        {"id": 3, "content": "c"},
        {"id": 4, "content": "d"},
    ]

    kept, dropped = select_evidence_within_budget(results, max_chars=5)

    assert kept == results[:1]
    assert dropped == 3


def test_build_grounded_prompt_respects_budget_and_truncates_first_result() -> None:
    prompt = build_grounded_prompt(
        "query",
        [
            {"id": 1, "file_path": "first.py", "content": "abcdefgh"},
            {"id": 2, "file_path": "second.py", "content": "dropped-evidence"},
            {"id": 3, "file_path": "third.py", "content": "also-dropped"},
        ],
        max_evidence_chars=4,
    )

    assert "abcd\n[truncated]" in prompt
    assert "efgh" not in prompt
    assert "dropped-evidence" not in prompt
    assert "also-dropped" not in prompt
