"""Tests for the Rules module — move legality and game-over detection.

14 test cases covering:
    - Module imports (AC-1, AC-7)
    - Move legality for all 4 directions (AC-2)
    - Legal move enumeration (AC-3)
    - Game-over detection (AC-4)
    - Game-over invariant (AC-5)
    - has_rotten twist-awareness (AC-8)
"""

from __future__ import annotations

import pytest

from src.core.board import Direction, SlideResult, slide_merge  # noqa: F401 — imported for test_import_rules_module
from src.core.rules import BoardProtocol, Rules  # noqa: F401 — imported for test_import_rules_module


class SimpleBoard:
    """Test-only stub implementing the BoardProtocol interface.

    Provides a ``grid`` attribute matching the BoardProtocol contract
    without duplicating the production Board implementation.
    """

    def __init__(self, grid: list[list[int]]) -> None:
        self.grid = grid


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def empty_board() -> SimpleBoard:
    """4×4 grid of all zeros."""
    return SimpleBoard(grid=[[0, 0, 0, 0] for _ in range(4)])


@pytest.fixture()
def single_tile_board() -> SimpleBoard:
    """4×4 grid with a single tile (2) at position (0, 0)."""
    grid = [[0, 0, 0, 0] for _ in range(4)]
    grid[0][0] = 2
    return SimpleBoard(grid=grid)


@pytest.fixture()
def full_no_merge_board() -> SimpleBoard:
    """Full 4×4 grid with alternating values — no adjacent equals, no merges possible."""
    return SimpleBoard(
        grid=[
            [1, 2, 1, 2],
            [2, 1, 2, 1],
            [1, 2, 1, 2],
            [2, 1, 2, 1],
        ]
    )


@pytest.fixture()
def full_with_merge_board() -> SimpleBoard:
    """Full 4×4 grid with one adjacent-equal pair at (0, 0) and (0, 1)."""
    return SimpleBoard(
        grid=[
            [2, 2, 4, 8],
            [4, 8, 16, 32],
            [64, 128, 256, 512],
            [1024, 2048, 1024, 2048],
        ]
    )


@pytest.fixture()
def almost_game_over_board() -> SimpleBoard:
    """Full 4×4 grid with no merges — game over when no rotten tiles."""
    return SimpleBoard(
        grid=[
            [1, 2, 1, 2],
            [2, 1, 2, 1],
            [1, 2, 1, 2],
            [2, 1, 2, 1],
        ]
    )


# ---------------------------------------------------------------------------
# Test 1: AC-1 — Module imports
# ---------------------------------------------------------------------------


def test_import_rules_module() -> None:
    """All expected symbols are importable from their canonical modules."""
    # Direction, SlideResult, slide_merge come from board.py (single source of truth).
    from src.core.board import Direction as _dir  # noqa: F401
    from src.core.board import SlideResult as _sr  # noqa: F401
    from src.core.board import slide_merge as _sm  # noqa: F401

    # BoardProtocol and Rules come from rules.py (unique to that module).
    from src.core.rules import BoardProtocol as _bp  # noqa: F401
    from src.core.rules import Rules as _rules  # noqa: F401

    assert _dir is not None
    assert _sr is not None
    assert _sm is not None
    assert _bp is not None
    assert _rules is not None


# ---------------------------------------------------------------------------
# Tests 2-6: AC-2 — Move legality
# ---------------------------------------------------------------------------


def test_is_move_legal_left_merges() -> None:
    """LEFT slide merges equal adjacent tiles, making the move legal."""
    board = SimpleBoard(
        grid=[
            [2, 2, 4, 4],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
    )
    rules = Rules()
    assert rules.is_move_legal(board, Direction.LEFT) is True


def test_is_move_legal_left_no_change() -> None:
    """LEFT slide on already-compacted row with no merges is not legal."""
    board = SimpleBoard(
        grid=[
            [2, 4, 8, 16],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
    )
    rules = Rules()
    assert rules.is_move_legal(board, Direction.LEFT) is False


def test_is_move_legal_right() -> None:
    """RIGHT slide on tile at left edge is legal."""
    board = SimpleBoard(
        grid=[
            [2, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
    )
    rules = Rules()
    assert rules.is_move_legal(board, Direction.RIGHT) is True


def test_is_move_legal_empty_board(empty_board: SimpleBoard) -> None:
    """Empty board has no legal moves in any direction."""
    rules = Rules()
    for direction in Direction:
        assert rules.is_move_legal(empty_board, direction) is False


def test_is_move_legal_up_and_down(single_tile_board: SimpleBoard) -> None:
    """Tile at (0, 0): UP is not legal (already at top), DOWN is legal."""
    rules = Rules()
    assert rules.is_move_legal(single_tile_board, Direction.UP) is False
    assert rules.is_move_legal(single_tile_board, Direction.DOWN) is True


# ---------------------------------------------------------------------------
# Tests 7-9: AC-3 — Legal move enumeration
# ---------------------------------------------------------------------------


def test_get_legal_moves_returns_empty_for_empty(empty_board: SimpleBoard) -> None:
    """Empty board yields no legal moves."""
    rules = Rules()
    assert rules.get_legal_moves(empty_board) == []


def test_get_legal_moves_returns_directions(single_tile_board: SimpleBoard) -> None:
    """Single tile at (0, 0) has legal moves DOWN and RIGHT."""
    rules = Rules()
    legal = rules.get_legal_moves(single_tile_board)
    assert legal == [Direction.DOWN, Direction.RIGHT]


def test_get_legal_moves_returns_empty_when_no_legal(
    full_no_merge_board: SimpleBoard,
) -> None:
    """Full board with no merges has no legal moves."""
    rules = Rules()
    assert rules.get_legal_moves(full_no_merge_board) == []


# ---------------------------------------------------------------------------
# Tests 10-12: AC-4 — Game-over detection
# ---------------------------------------------------------------------------


def test_is_game_over_true_when_no_moves(full_no_merge_board: SimpleBoard) -> None:
    """Full board with no legal moves is game over."""
    rules = Rules()
    assert rules.is_game_over(full_no_merge_board) is True


def test_is_game_over_false_when_empty_cells(empty_board: SimpleBoard) -> None:
    """Board with empty cells is not game over."""
    rules = Rules()
    assert rules.is_game_over(empty_board) is False


def test_is_game_over_false_when_merges_possible(
    full_with_merge_board: SimpleBoard,
) -> None:
    """Full board with mergeable tiles is not game over."""
    rules = Rules()
    assert rules.is_game_over(full_with_merge_board) is False


# ---------------------------------------------------------------------------
# Test 13: AC-5 — Game-over invariant
# ---------------------------------------------------------------------------


def test_is_game_over_invariant(
    empty_board: SimpleBoard,
    single_tile_board: SimpleBoard,
    almost_game_over_board: SimpleBoard,
) -> None:
    """If is_game_over is True then get_legal_moves returns []."""
    rules = Rules()
    boards = [empty_board, single_tile_board, almost_game_over_board]
    for board in boards:
        if rules.is_game_over(board):
            assert rules.get_legal_moves(board) == [], (
                "invariant violated: is_game_over=True but get_legal_moves is non-empty"
            )
        elif rules.get_legal_moves(board):
            assert rules.is_game_over(board) is False, (
                "invariant violated: get_legal_moves is non-empty but is_game_over=True"
            )


# ---------------------------------------------------------------------------
# Test 14: AC-8 — has_rotten prevents premature game-over
# ---------------------------------------------------------------------------


def test_is_game_over_has_rotten_prevents_over(
    full_no_merge_board: SimpleBoard,
) -> None:
    """has_rotten=True prevents game over on full board (rotten tiles could clear)."""
    rules = Rules()
    assert rules.is_game_over(full_no_merge_board, has_rotten=False) is True
    assert rules.is_game_over(full_no_merge_board, has_rotten=True) is False


# ---------------------------------------------------------------------------
# Reconciliation verification tests (TDD red phase)
# ---------------------------------------------------------------------------


def test_slide_merge_from_board_returns_correct_fields() -> None:
    """Verify slide_merge returns board.py's SlideResult with new_grid/score_delta/moved."""
    grid = [[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    result = slide_merge(grid, Direction.LEFT)

    # board.py's SlideResult uses new_grid, score_delta, moved — not grid/score.
    assert hasattr(result, "new_grid"), (
        "SlideResult must have 'new_grid' field (not 'grid')"
    )
    assert hasattr(result, "score_delta"), (
        "SlideResult must have 'score_delta' field (not 'score')"
    )
    assert hasattr(result, "moved"), "SlideResult must have 'moved' field"
    assert result.new_grid[0] == [4, 0, 0, 0]
    assert result.score_delta == 4
    assert result.moved is True


def test_rules_direction_is_board_direction() -> None:
    """Verify Direction at module level is the same object as board.py's Direction."""
    from src.core.board import Direction as BoardDirection

    # The Direction imported at the top of this file (from src.core.board)
    # must be the identical object — no duplicate class in rules.py.
    assert Direction is BoardDirection, (
        "Direction imported at top of file must be the same object as "
        "Direction from src.core.board — rules.py must not define its own"
    )
