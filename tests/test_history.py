"""Test suite for src/core/history.py — History class (bounded undo stack).

11 test functions covering all acceptance criteria from Sprint 1 Task 5
(History Module). Tests are designed to FAIL until src/core/history.py
is implemented (TDD red phase).
"""

from __future__ import annotations

import pytest  # noqa: F401 — required for fixtures

from src.core.board import BoardState
from src.core.history import History


# ---------------------------------------------------------------------------
# Initial State
# ---------------------------------------------------------------------------


def test_history_initial_state_can_undo_false() -> None:
    """AC-3: A freshly constructed History reports no undo capability."""
    history = History()
    assert history.can_undo() is False


def test_history_initial_state_pop_returns_none() -> None:
    """E-H01: Popping from an empty History returns None (no exception)."""
    history = History()
    assert history.pop() is None


# ---------------------------------------------------------------------------
# Push / Pop
# ---------------------------------------------------------------------------


def test_history_push_one_then_pop_returns_it() -> None:
    """AC-2: Push a single snapshot, then pop returns the same grid and score."""
    grid = [
        [2, 4, 8, 16],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    board_state = BoardState(grid=grid, score=50, moves=3)
    history = History()
    history.push((board_state, 100))
    assert history.can_undo() is True
    result = history.pop()
    assert result is not None
    assert result[0].grid == grid
    assert result[1] == 100


def test_history_push_two_then_pop_returns_lifo_order() -> None:
    """AC-2: Last pushed is first popped (LIFO ordering)."""
    grid_a = [
        [2, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    grid_b = [
        [4, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    state_a = BoardState(grid=grid_a, score=10, moves=1)
    state_b = BoardState(grid=grid_b, score=20, moves=2)
    history = History()
    history.push((state_a, 100))
    history.push((state_b, 200))
    result_b = history.pop()
    assert result_b is not None
    assert result_b[0].grid == grid_b
    assert result_b[1] == 200
    result_a = history.pop()
    assert result_a is not None
    assert result_a[0].grid == grid_a
    assert result_a[1] == 100


# ---------------------------------------------------------------------------
# Max Depth
# ---------------------------------------------------------------------------


def test_history_max_depth_1_keeps_only_last() -> None:
    """AC-4: max_depth=1 retains only the most recent snapshot."""
    grid_a = [
        [2, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    grid_b = [
        [4, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    state_a = BoardState(grid=grid_a, score=10, moves=1)
    state_b = BoardState(grid=grid_b, score=20, moves=2)
    history = History(max_depth=1)
    history.push((state_a, 100))
    history.push((state_b, 200))
    assert history.can_undo() is True
    result = history.pop()
    assert result is not None
    assert result[0].grid == grid_b
    assert history.pop() is None  # BoardState_A was discarded


def test_history_max_depth_3_with_5_pushes_keeps_last_3() -> None:
    """AC-4: max_depth=3 with 5 pushes retains only the 3 most recent."""
    grids = []
    for i in range(5):
        grid = [[0] * 4 for _ in range(4)]
        grid[0][0] = i + 1
        grids.append(grid)
    history = History(max_depth=3)
    for i in range(5):
        state = BoardState(grid=grids[i], score=i * 10, moves=i)
        history.push((state, (i + 1) * 10))
    result = history.pop()
    assert result is not None
    assert result[0].grid == grids[4]
    assert result[1] == 50
    result = history.pop()
    assert result is not None
    assert result[0].grid == grids[3]
    assert result[1] == 40
    result = history.pop()
    assert result is not None
    assert result[0].grid == grids[2]
    assert result[1] == 30
    assert history.pop() is None  # S1 and S2 were discarded


def test_history_max_depth_0_allows_unlimited_pushes() -> None:
    """AC-4: max_depth=0 (default) allows unlimited snapshots."""
    history = History()
    grids = []
    for i in range(100):
        grid = [[0] * 4 for _ in range(4)]
        grid[0][0] = i + 1
        grids.append(grid)
        state = BoardState(grid=grid, score=i * 10, moves=i)
        history.push((state, i))
    assert history.can_undo() is True
    for i in range(99, -1, -1):
        result = history.pop()
        assert result is not None
        assert result[0].grid == grids[i]
        assert result[1] == i


# ---------------------------------------------------------------------------
# Depth Enforcement
# ---------------------------------------------------------------------------


def test_history_pop_after_push_to_limit_discards_oldest() -> None:
    """AC-4 / ADR-H3: Pushing beyond max_depth discards the oldest snapshot."""
    grid_1 = [[1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    grid_2 = [[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    grid_3 = [[3, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    state_1 = BoardState(grid=grid_1, score=10, moves=1)
    state_2 = BoardState(grid=grid_2, score=20, moves=2)
    state_3 = BoardState(grid=grid_3, score=30, moves=3)
    history = History(max_depth=2)
    history.push((state_1, 10))
    history.push((state_2, 20))
    history.push((state_3, 30))  # S1 should be discarded
    result = history.pop()
    assert result is not None
    assert result[0].grid == grid_3
    result = history.pop()
    assert result is not None
    assert result[0].grid == grid_2
    assert history.pop() is None  # S1 was discarded, not S2 or S3


# ---------------------------------------------------------------------------
# Defensive Copy Isolation
# ---------------------------------------------------------------------------


def test_history_deep_copy_isolation() -> None:
    """ADR-H4: Pop returns a defensive copy — mutation does not affect the stack."""
    grid = [
        [2, 4, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    board_state = BoardState(grid=grid, score=50, moves=3)
    history = History()
    history.push((board_state, 100))
    popped_state, popped_score = history.pop()
    popped_state.grid[0][0] = 9999
    history.push((board_state, 100))
    popped_again, _ = history.pop()
    assert popped_again.grid[0][0] != 9999  # original value preserved


# ---------------------------------------------------------------------------
# Error Handling
# ---------------------------------------------------------------------------


def test_history_push_none_raises_type_error() -> None:
    """E-H02: push(None) raises TypeError."""
    history = History()
    with pytest.raises(TypeError):
        history.push(None)


def test_history_negative_max_depth_raises_value_error() -> None:
    """ADR-H6: History(max_depth=-1) raises ValueError."""
    with pytest.raises(ValueError):
        History(max_depth=-1)
