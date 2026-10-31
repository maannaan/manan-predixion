from __future__ import annotations

from collections import defaultdict
from typing import Iterable


# A1. Merge promise windows
def merge_windows(windows: list[list[int]]) -> list[list[int]]:
    
    for w in windows:
        if len(w) != 2 or w[0] > w[1]:
            raise ValueError(f"invalid window {w!r}: expected [start, end] with start <= end")

    merged: list[list[int]] = []
    for start, end in sorted(windows): 
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
                break 
    return flagged