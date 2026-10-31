from __future__ import annotations

from collections import defaultdict
from typing import Iterable


# A1. Merge promise windows
def merge_windows(windows: list[list[int]]) -> list[list[int]]:
    """Merge overlapping or touching inclusive day ranges.

    Two windows merge when they share at least one day, so [1, 3] and [3, 5]
    become [1, 5]. Windows that are merely adjacent ([1, 4] and [5, 8]) stay
    separate, which matches the expected output in the brief.

    Time:  O(n log n) for the sort; the merge pass itself is O(n).
    Space: O(n) for the sorted copy and the output (input is not mutated).
    """
    for w in windows:
        if len(w) != 2 or w[0] > w[1]:
            raise ValueError(f"invalid window {w!r}: expected [start, end] with start <= end")

    merged: list[list[int]] = []
    for start, end in sorted(windows):  # sorted() copies; caller's list untouched
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


# A2. Excess call attempts
def flag_excess_attempts(
    attempts: Iterable[tuple[str, int]],
    limit: int = 3,
    window: int = 3600,
) -> set[str]:
    """Return borrowers with `limit` or more attempts where last - first < window.

    Approach: group timestamps per borrower, sort them, then slide a window of
    exactly `limit` consecutive attempts. If any group of `limit` attempts fits
    inside the window, the tightest such group is always `limit` *consecutive*
    sorted timestamps, so checking times[i + limit - 1] - times[i] < window for
    each i is sufficient.

    Time:  O(n log n) overall (O(k log k) per borrower with k attempts, the
           scan is O(k)), versus O(k^2) for comparing all pairs.
    Space: O(n) for the per-borrower grouping.
    """
    if limit < 1:
        raise ValueError("limit must be >= 1")
    if window <= 0:
        raise ValueError("window must be > 0")

    by_borrower: dict[str, list[int]] = defaultdict(list)
    for borrower_id, ts in attempts:
        by_borrower[borrower_id].append(ts)

    flagged: set[str] = set()
    for borrower_id, times in by_borrower.items():
        if len(times) < limit:
            continue
        times.sort()
        for i in range(len(times) - limit + 1):
            if times[i + limit - 1] - times[i] < window:
                flagged.add(borrower_id)
                break  # one violation is enough for this borrower
    return flagged