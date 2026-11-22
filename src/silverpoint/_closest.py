"""The library's "did you mean" helper (``packages/embed/src/util/closest.ts``), the same rule."""

from __future__ import annotations

from collections.abc import Sequence


def _distance(a: str, b: str) -> int:
    previous = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        current = [i]
        for j in range(1, len(b) + 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (a[i - 1] != b[j - 1])))
        previous = current
    return previous[len(b)]


def closest(word: str, candidates: Sequence[str], limit: int = 3) -> list[str]:
    """Up to ``limit`` candidates within a third of the word's length (at least 2 edits), nearest first."""
    top = max(2, len(word) // 3)
    scored = [(_distance(word.lower(), c.lower()), order, c) for order, c in enumerate(candidates)]
    return [c for d, _, c in sorted(s for s in scored if s[0] <= top)][:limit]


def did_you_mean(word: str, candidates: Sequence[str]) -> str:
    near = closest(word, candidates)
    quoted = " or ".join('"' + n + '"' for n in near)
    return f" Did you mean {quoted}?" if near else ""
