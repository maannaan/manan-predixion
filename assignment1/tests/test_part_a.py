import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "part_a"))

import pytest

from A1_partA_manan import flag_excess_attempts, merge_windows


# ----------------------------- A1 -----------------------------------------
def test_merge_example_from_brief():
    assert merge_windows([[5, 8], [1, 3], [2, 4], [10, 12], [12, 13]]) == [[1, 4], [5, 8], [10, 13]]


def test_merge_touching_endpoints():
    assert merge_windows([[3, 5], [1, 3]]) == [[1, 5]]


def test_merge_adjacent_days_stay_separate():
    assert merge_windows([[1, 4], [5, 8]]) == [[1, 4], [5, 8]]


def test_merge_contained_window():
    assert merge_windows([[1, 10], [2, 3], [4, 5]]) == [[1, 10]]


def test_merge_empty_and_single_day():
    assert merge_windows([]) == []
    assert merge_windows([[7, 7]]) == [[7, 7]]


def test_merge_does_not_mutate_input():
    data = [[5, 8], [1, 3]]
    merge_windows(data)
    assert data == [[5, 8], [1, 3]]


def test_merge_rejects_inverted_window():
    with pytest.raises(ValueError):
        merge_windows([[5, 1]])


# ----------------------------- A2 -----------------------------------------
def test_flags_three_calls_within_an_hour():
    attempts = [("b1", 0), ("b1", 1000), ("b1", 3599)]
    assert flag_excess_attempts(attempts) == {"b1"}


def test_window_boundary_is_strict():
    # last - first == 3600 is NOT less than the window
    attempts = [("b1", 0), ("b1", 1000), ("b1", 3600)]
    assert flag_excess_attempts(attempts) == set()


def test_unsorted_and_mixed_borrowers():
    attempts = [
        ("b2", 9000), ("b1", 7200), ("b2", 100),
        ("b1", 0), ("b2", 8000), ("b1", 3600), ("b2", 7000),
    ]
    # b1: gaps of exactly 3600 -> never 3 within <3600
    # b2: 7000, 8000, 9000 -> span 2000
    assert flag_excess_attempts(attempts) == {"b2"}


def test_violation_not_at_start_of_history():
    attempts = [("b1", t) for t in (0, 5000, 10000, 10010, 10020)]
    assert flag_excess_attempts(attempts) == {"b1"}


def test_duplicate_timestamps_count():
    assert flag_excess_attempts([("b1", 50)] * 3) == {"b1"}


def test_custom_limit_and_window():
    attempts = [("b1", 0), ("b1", 59)]
    assert flag_excess_attempts(attempts, limit=2, window=60) == {"b1"}
    assert flag_excess_attempts(attempts, limit=2, window=59) == set()


def test_empty_input():
    assert flag_excess_attempts([]) == set()