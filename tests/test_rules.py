"""Pytest test suite for the slide_merge algorithm — green phase.

Tests cover all 12 acceptance criteria for the slide_merge implementation
in src/core/rules.py. All tests pass against the fully implemented
slide_merge function and Direction enum.

Acceptance criteria coverage:
    AC-1  — test_direction_enum_members
    AC-2  — test_slide_merge_returns_slide_result
    AC-3  — test_simple_slide_left_no_merge
    AC-4  — test_simple_merge_left
    AC-5  — test_one_merge_per_tile
    AC-6  — test_edge_blocking_left
    AC-7  — test_full_row_no_movement
    AC-8  — test_score_sum_of_all_merges
    AC-9  — test_input_grid_not_mutated
    AC-10 — test_slide_merge_empty_grid_raises_value_error
          — test_slide_merge_empty_inner_rows_raises_value_error
    AC-11 — test_slide_merge_non_square_grid_raises_value_error
    AC-12 — test_slide_down_vertical_merge
          — test_slide_up_vertical_merge
          — test_slide_right_full
"""

from __future__ import annotations

import copy

import pytest

from src.core.rules import Direction, SlideResult, slide_merge


# ---------------------------------------------------------------------------
# Group 1: Direction Enum (AC-1)
# ---------------------------------------------------------------------------


def test_direction_enum_members() -> None:
    """Direction enum has exactly UP, DOWN, LEFT, RIGHT with string values."""
    assert Direction.UP.value == "UP"
    assert Direction.DOWN.value == "DOWN"
    assert Direction.LEFT.value == "LEFT"
    assert Direction.RIGHT.value == "RIGHT"
    assert len(Direction) == 4


# ---------------------------------------------------------------------------
# Group 2: Return Type (AC-2)
# ---------------------------------------------------------------------------


def test_slide_merge_returns_slide_result() -> None:
    """slide_merge returns a SlideResult with grid (list) and score (int)."""
    grid = [[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    result = slide_merge(grid, Direction.LEFT)

    assert isinstance(result, SlideResult)
    assert isinstance(result.grid, list)
    assert isinstance(result.score, int)


# ---------------------------------------------------------------------------
# Group 3: Simple Slide, No Merge (AC-3)
# ---------------------------------------------------------------------------


def test_simple_slide_left_no_merge() -> None:
    """Tiles slide left to fill gaps with no merges; score is 0."""
    grid = [[0, 0, 2, 4]]
    expected_grid = [[2, 4, 0, 0]]

    result = slide_merge(grid, Direction.LEFT)

    assert result.grid == expected_grid
    assert result.score == 0


# ---------------------------------------------------------------------------
# Group 4: Simple Merge (AC-4)
# ---------------------------------------------------------------------------


def test_simple_merge_left() -> None:
    """Two adjacent equal tiles merge; score equals merged value."""
    grid = [[2, 2, 0, 0]]
    expected_grid = [[4, 0, 0, 0]]

    result = slide_merge(grid, Direction.LEFT)

    assert result.grid == expected_grid
    assert result.score == 4


# ---------------------------------------------------------------------------
# Group 5: One-Merge-Per-Tile (AC-5)
# ---------------------------------------------------------------------------


def test_one_merge_per_tile() -> None:
    """Three consecutive equal tiles: only leftmost pair merges."""
    grid = [[2, 2, 2, 0]]
    expected_grid = [[4, 2, 0, 0]]

    result = slide_merge(grid, Direction.LEFT)

    assert result.grid == expected_grid
    assert result.grid != [[8, 0, 0, 0]], "Double merge must not occur"
    assert result.score == 4


# ---------------------------------------------------------------------------
# Group 6: Edge Blocking (AC-6)
# ---------------------------------------------------------------------------


def test_edge_blocking_left() -> None:
    """Two tiles from opposite sides slide and merge when meeting."""
    grid = [[2, 0, 0, 2]]
    expected_grid = [[4, 0, 0, 0]]

    result = slide_merge(grid, Direction.LEFT)

    assert result.grid == expected_grid
    assert result.score == 4


# ---------------------------------------------------------------------------
# Group 7: Full Row, No Movement (AC-7)
# ---------------------------------------------------------------------------


def test_full_row_no_movement() -> None:
    """Full row with no equal adjacent tiles — no change, score 0."""
    grid = [[2, 4, 8, 16]]
    expected_grid = [[2, 4, 8, 16]]

    result = slide_merge(grid, Direction.LEFT)

    assert result.grid == expected_grid
    assert result.score == 0


# ---------------------------------------------------------------------------
# Group 8: Vertical & Right Direction Tests (AC-12)
# ---------------------------------------------------------------------------


def test_slide_down_vertical_merge() -> None:
    """Two tiles slide DOWN and merge."""
    grid = [[2, 0], [2, 0]]
    expected_grid = [[0, 0], [4, 0]]

    result = slide_merge(grid, Direction.DOWN)

    assert result.grid == expected_grid
    assert result.score == 4


def test_slide_up_vertical_merge() -> None:
    """Tiles slide UP and merge in a 4x2 grid."""
    grid = [[0, 0], [0, 2], [0, 2], [4, 0]]
    # Column 0: [0, 0, 0, 4] → UP → [4, 0, 0, 0]
    # Column 1: [0, 2, 2, 0] → UP → [4, 0, 0, 0]
    expected_grid = [[4, 4], [0, 0], [0, 0], [0, 0]]

    result = slide_merge(grid, Direction.UP)

    assert result.grid == expected_grid
    assert result.score == 4


def test_slide_right_full() -> None:
    """Right direction on a 4x4 grid — verify reversal logic."""
    grid = [[0, 0, 2, 2], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    expected_grid = [[0, 0, 0, 4], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]

    result = slide_merge(grid, Direction.RIGHT)

    assert result.grid == expected_grid
    assert result.score == 4


# ---------------------------------------------------------------------------
# Group 9: Score Calculation (AC-8)
# ---------------------------------------------------------------------------


def test_score_sum_of_all_merges() -> None:
    """Multiple merges in one move: score is sum of all merged values."""
    grid = [[2, 2, 4, 4]]
    expected_grid = [[4, 8, 0, 0]]

    result = slide_merge(grid, Direction.LEFT)

    assert result.grid == expected_grid
    assert result.score == 12, "Score must be 4 (from 2+2) + 8 (from 4+4) = 12"


# ---------------------------------------------------------------------------
# Group 10: Immutability (AC-9)
# ---------------------------------------------------------------------------


def test_input_grid_not_mutated() -> None:
    """slide_merge must not modify the original grid."""
    grid = [[0, 2, 2, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    grid_snapshot = copy.deepcopy(grid)

    result = slide_merge(grid, Direction.LEFT)

    assert grid == grid_snapshot, "Original grid must not be mutated"
    assert result.grid is not grid, "Returned grid must be a new object"


# ---------------------------------------------------------------------------
# Group 11: Error Handling (AC-10, AC-11)
# ---------------------------------------------------------------------------


def test_slide_merge_empty_grid_raises_value_error() -> None:
    """Empty grid raises ValueError with 'empty' in the message."""
    with pytest.raises(ValueError, match="empty"):
        slide_merge([], Direction.LEFT)


def test_slide_merge_non_square_grid_raises_value_error() -> None:
    """Non-square grid raises ValueError with 'square' in the message."""
    with pytest.raises(ValueError, match="square"):
        slide_merge([[1, 2], [3]], Direction.LEFT)


def test_slide_merge_empty_inner_rows_raises_value_error() -> None:
    """Grid with empty inner rows raises ValueError."""
    with pytest.raises(ValueError, match="empty"):
        slide_merge([[], [], [], []], Direction.LEFT)


# ---------------------------------------------------------------------------
# Group 12: Edge Cases (HIGH-001)
# ---------------------------------------------------------------------------


def test_all_zeros_stays_zeros() -> None:
    """An all-zero grid remains identical after slide; score is 0."""
    grid: list[list[int]] = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]

    result = slide_merge(grid, Direction.LEFT)

    assert result.grid == grid
    assert result.score == 0
