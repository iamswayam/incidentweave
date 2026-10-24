"""Small, dependency-free statistics for retrieval evaluation."""

from __future__ import annotations

from math import comb, sqrt


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Return the Wilson score interval for a binomial proportion."""

    if n == 0:
        return 0.0, 1.0
    if n < 0 or successes < 0 or successes > n:
        raise ValueError("successes and n must satisfy 0 <= successes <= n")
    proportion = successes / n
    z_squared = z * z
    denominator = 1 + z_squared / n
    center = (proportion + z_squared / (2 * n)) / denominator
    margin = (
        z
        * sqrt(proportion * (1 - proportion) / n + z_squared / (4 * n * n))
        / denominator
    )
    return center - margin, center + margin


def exact_sign_test(wins: int, losses: int) -> float:
    """Return the two-sided exact binomial sign-test p-value."""

    if wins < 0 or losses < 0:
        raise ValueError("wins and losses must be non-negative")
    trials = wins + losses
    if trials == 0:
        return 1.0
    tail = min(wins, losses)
    probability = sum(comb(trials, index) for index in range(tail + 1)) / (2**trials)
    return min(1.0, 2 * probability)


def paired_comparison(
    a_hits: list[bool],
    b_hits: list[bool],
) -> dict[str, int | float]:
    """Compare paired boolean hits, counting ties separately."""

    if len(a_hits) != len(b_hits):
        raise ValueError("paired hit lists must have the same length")
    wins = sum(not a and b for a, b in zip(a_hits, b_hits))
    losses = sum(a and not b for a, b in zip(a_hits, b_hits))
    ties = len(a_hits) - wins - losses
    return {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "p_value": exact_sign_test(wins, losses),
    }
