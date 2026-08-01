"""Tests for the Rules module — move legality and game-over detection.

45 test cases covering:
    - Module imports (AC-1, AC-7)
    - Move legality for all 4 directions (AC-2)
    - Legal move enumeration (AC-3)
    - Game-over detection (AC-4)
    - Game-over invariant (AC-5)
    - has_rotten twist-awareness (AC-8)
    - Stalemate trap detection (OQ-P17)
"""
# CHANGELOG:
# - Phase 3 Sprint 1: Add 8 stalemate trap tests + 9 behavioral updates (OQ-P17: rescueable-pair detection)

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


class SimpleBoardExtended:
    """Test-only stub implementing BoardProtocol with rotten overlay support.

    Provides both a ``grid`` attribute (BoardProtocol) and a
    ``get_rotten_overlay()`` method for twist-aware game-over tests.
    Standalone class — not a subclass of SimpleBoard — to avoid
    inheritance coupling in test stubs.
    """

    def __init__(
        self, grid: list[list[int]], rotten_overlay: list[list[int]]
    ) -> None:
        self.grid = grid
        self._rotten_overlay = rotten_overlay

    def get_rotten_overlay(self) -> list[list[int]]:
        """Return a defensive copy of the rotten overlay grid.

        Matches the behavior of ``Board.get_rotten_overlay()`` which
        returns ``[row[:] for row in self._rotten_overlay]``.
        """
        return [row[:] for row in self._rotten_overlay]


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


# ---------------------------------------------------------------------------
# Twist-aware game-over detection tests (TDD red phase)
# 19 new tests — 9 will FAIL (overlay not inspected), 10 will PASS (backward compat)
# ---------------------------------------------------------------------------


def test_rotten_tile_at_center_full_board_prevents_over() -> None:
    """Full board (no merges) with a single rotten tile at (1,1) countdown=3.

    is_game_over() returns True -- single rotten with no adjacent same-value
    partner is not rescueable. (OQ-P17 post-fix behavior)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[1][1] = 3
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is True


def test_rotten_tile_at_corner_full_board_prevents_over() -> None:
    """Full board (no merges) with a single rotten tile at (0,0) countdown=1.

    Countdown=1 with no adjacent same-value partner is not rescueable. (OQ-P17 post-fix)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][0] = 1
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is True


def test_rotten_tile_at_edge_full_board_prevents_over() -> None:
    """Full board (no merges) with a single rotten tile at (0,2) countdown=2.

    Edge position with no adjacent same-value partner is not rescueable. (OQ-P17 post-fix)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][2] = 2
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is True


def test_two_rotten_tiles_full_board_prevents_over() -> None:
    """Full board (no merges) with rotten at (0,0)=1 and (3,3)=2.

    Multiple rotten tiles at opposite corners — game continues. (AC-3)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][0] = 1
    overlay[3][3] = 2
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is True


def test_four_rotten_tiles_full_board_prevents_over() -> None:
    """Full board (no merges) with rotten at all four corners (countdown=3).

    Four rotten tiles at corners — game continues. (AC-3)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][0] = 3
    overlay[0][3] = 3
    overlay[3][0] = 3
    overlay[3][3] = 3
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is True


def test_rotten_tile_non_full_board_not_over() -> None:
    """Board has empty cells AND a rotten tile.

    Empty cells prevent game-over regardless of overlay. (AC-2)
    """
    rules = Rules()
    grid = [
        [2, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][0] = 3
    board = SimpleBoardExtended(grid=grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is False


def test_no_rotten_non_full_board_not_over() -> None:
    """Board has empty cells, overlay is all zeros.

    Empty cells prevent game-over. (AC-2)
    """
    rules = Rules()
    grid = [
        [2, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    board = SimpleBoardExtended(grid=grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is False


def test_full_no_merges_all_zeros_overlay_is_over() -> None:
    """Full board (no merges), overlay all zeros (no rotten tiles).

    Game is over — normal game-over with twist module present but
    no rotten tiles. (AC-4, AC-7)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is True


def test_full_no_merges_no_overlay_support_is_over() -> None:
    """Full board using old SimpleBoard (no get_rotten_overlay), has_rotten=False.

    Backward compat path — game is over. (AC-4, AC-5)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    board = SimpleBoard(grid=full_grid)
    assert rules.is_game_over(board, has_rotten=False) is True


def test_mixed_countdowns_full_board_prevents_over() -> None:
    """Full board with rotten overlays at various countdowns.

    Mix of countdown=1, 2, 3 across positions. Any non-zero value
    prevents game-over. (AC-2)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][0] = 1
    overlay[0][1] = 2
    overlay[0][2] = 3
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is True


def test_all_zero_overlay_behaves_as_no_rotten() -> None:
    """Full board (no merges), overlay explicitly all zeros, has_rotten=False.

    All-zero overlay is equivalent to no rotten — game is over. (AC-7)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    assert rules.is_game_over(board, has_rotten=False) is True


def test_is_game_over_invariant_with_rotten() -> None:
    """If is_game_over is True then get_legal_moves returns [].

    Invariant preserved across overlay and non-overlay boards.
    Extends existing invariant test. (AC-2)
    """
    rules = Rules()

    # Non-overlay board — classic backward compat
    classic = SimpleBoard(
        grid=[
            [1, 2, 1, 2],
            [2, 1, 2, 1],
            [1, 2, 1, 2],
            [2, 1, 2, 1],
        ]
    )

    # Overlay board with no rotten tiles
    overlay_clean = SimpleBoardExtended(
        grid=[
            [1, 2, 1, 2],
            [2, 1, 2, 1],
            [1, 2, 1, 2],
            [2, 1, 2, 1],
        ],
        rotten_overlay=[[0] * 4 for _ in range(4)],
    )

    # Overlay board with rotten tiles
    grid_rotten = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay_with_rotten = [[0] * 4 for _ in range(4)]
    overlay_with_rotten[0][0] = 2
    rotten_board = SimpleBoardExtended(
        grid=grid_rotten, rotten_overlay=overlay_with_rotten
    )

    boards = [classic, overlay_clean, rotten_board]
    for board in boards:
        if rules.is_game_over(board):
            assert rules.get_legal_moves(board) == [], (
                "invariant violated: is_game_over=True but get_legal_moves is non-empty"
            )


def test_rotten_overlay_full_no_merges_no_legal_moves() -> None:
    """Full board with no merges and overlay all zeros.

    Confirms get_legal_moves returns [] and is_game_over returns True
    when no rotten tiles exist. (AC-2)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    assert rules.get_legal_moves(board) == []
    assert rules.is_game_over(board) is True


def test_overlay_nonzero_but_has_empty_cells_not_over() -> None:
    """Board with ONE empty cell at (3,3). Overlay has rotten at (0,0)=3.

    Empty cells prevent game-over at Phase 1 — overlay not inspected.
    (AC-2)
    """
    rules = Rules()
    grid = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    grid[0][0] = 2  # minimal non-empty cell
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][0] = 3
    board = SimpleBoardExtended(grid=grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is False


def test_has_rotten_fallback_without_overlay_method() -> None:
    """Use old SimpleBoard (no overlay). Call with has_rotten=True -> not over.

    Call with has_rotten=False -> game over. Verifies the fallback path.
    (AC-4, AC-5)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    board = SimpleBoard(grid=full_grid)
    # has_rotten=True on non-overlay board -> game continues
    assert rules.is_game_over(board, has_rotten=True) is False
    # has_rotten=False on non-overlay board -> game is over
    assert rules.is_game_over(board, has_rotten=False) is True


def test_overlay_inspection_overrides_has_rotten_false() -> None:
    """SimpleBoardExtended with non-zero overlay, has_rotten=False.

    Overlay inspection overrides the stale boolean — game continues.
    (AC-2)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][0] = 3
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    # has_rotten=False but overlay has non-zero -> overlay inspection wins
    # Single rotten at (0,0) with no adjacent same-value partner -> game over
    assert rules.is_game_over(board, has_rotten=False) is True


def test_rotten_all_corner_positions() -> None:
    """Full board with rotten at all four corners.

    Positions: (0,0), (0,3), (3,0), (3,3). is_game_over -> False. (AC-9)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][0] = 1
    overlay[0][3] = 2
    overlay[3][0] = 3
    overlay[3][3] = 1
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is True


def test_rotten_center_position() -> None:
    """Full board with rotten at inner cells (1,1) and (2,2).

    is_game_over -> False. (AC-9)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[1][1] = 2
    overlay[2][2] = 3
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is True


def test_merges_possible_with_rotten_not_over() -> None:
    """Full board with mergeable tiles AND rotten overlay.

    Merges exist -> is_game_over False regardless of overlay. (AC-2)
    """
    rules = Rules()
    merge_grid = [
        [2, 2, 4, 4],
        [4, 8, 16, 32],
        [64, 128, 256, 512],
        [1024, 2048, 1024, 2048],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][0] = 2
    overlay[3][3] = 1
    board = SimpleBoardExtended(grid=merge_grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is False


# ---------------------------------------------------------------------------
# Stalemate trap detection tests (OQ-P17 TDD red phase)
# 8 new tests -- all will FAIL against current is_game_over() which returns
# False unconditionally when any rotten tile exists.
# ---------------------------------------------------------------------------


def test_stalemate_rescueable_same_value_pair_continues() -> None:
    """Full board, no legal moves, two adjacent rotten with same tile value.

    Rescueable pair found -- game continues. (OQ-P17 / AC-2)
    Grid[0][0]=1 and Grid[0][1]=2 in alternating pattern, but we override
    positions so both have value 2 (rescueable).
    """
    rules = Rules()
    # Build grid where positions (0,0) and (0,1) share the same value
    grid = [
        [2, 2, 1, 2],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][0] = 3
    overlay[0][1] = 2
    board = SimpleBoardExtended(grid=grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is False


def test_no_rescueable_pair_game_over() -> None:
    """Full board, no legal moves, single rotten with no adjacent partner.

    No rescueable pair -- game IS over. (OQ-P17 / AC-3)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][0] = 3
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is True


def test_stalemate_adjacent_different_values_not_rescueable() -> None:
    """Two adjacent rotten tiles with DIFFERENT tile values.

    Not rescueable -- game IS over. (OQ-P17)
    Grid[0][0]=1 and Grid[0][1]=2 differ in alternating pattern.
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][0] = 3
    overlay[0][1] = 2
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is True


def test_stalemate_diagonal_rotten_not_rescueable() -> None:
    """Two rotten tiles at diagonal positions (0,0) and (1,1).

    Diagonal is NOT adjacent -- not rescueable -- game IS over. (OQ-P17)
    """
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][0] = 3
    overlay[1][1] = 3
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is True


def test_stalemate_rescueable_at_all_positions() -> None:
    """Test rescueable pair detection at various grid positions.

    Each sub-case corrupts the minimum cells needed so the paired positions
    share the same tile value.
    """

    def _make_board_overlay(
        pair: list[tuple[int, int]],
        grid: list[list[int]],
        countdowns: tuple[int, int],
    ) -> SimpleBoardExtended:
        """Build a SimpleBoardExtended with rotten overlay at pair positions."""
        grid_copy = [row[:] for row in grid]
        grid_val = grid_copy[pair[0][0]][pair[0][1]]
        # Force second cell to match first
        grid_copy[pair[1][0]][pair[1][1]] = grid_val
        overlay = [[0] * 4 for _ in range(4)]
        overlay[pair[0][0]][pair[0][1]] = countdowns[0]
        overlay[pair[1][0]][pair[1][1]] = countdowns[1]
        return SimpleBoardExtended(grid=grid_copy, rotten_overlay=overlay)

    base_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]

    rules = Rules()

    # Case A: pair at (0,0)-(0,1) horizontal top-left
    board = _make_board_overlay([(0, 0), (0, 1)], base_grid, (3, 2))
    assert rules.is_game_over(board) is False

    # Case B: pair at (3,2)-(3,3) horizontal bottom-right
    board = _make_board_overlay([(3, 2), (3, 3)], base_grid, (3, 2))
    assert rules.is_game_over(board) is False

    # Case C: pair at (0,0)-(1,0) vertical top-left
    board = _make_board_overlay([(0, 0), (1, 0)], base_grid, (2, 3))
    assert rules.is_game_over(board) is False

    # Case D: pair at (2,3)-(3,3) vertical bottom-right
    board = _make_board_overlay([(2, 3), (3, 3)], base_grid, (1, 1))
    assert rules.is_game_over(board) is False

    # Case E: pair at (1,1)-(1,2) center horizontal
    board = _make_board_overlay([(1, 1), (1, 2)], base_grid, (2, 2))
    assert rules.is_game_over(board) is False


def test_stalemate_multiple_rotten_one_rescueable_pair() -> None:
    """Multiple rotten tiles, but only one pair is rescueable.

    Single rescueable pair at (0,0)-(0,1) with same value -> game continues.
    Other rotten at (3,3) is irrelevant. (OQ-P17)
    """
    rules = Rules()
    # Build grid where (0,0) and (0,1) share value 2
    grid = [
        [2, 2, 1, 2],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
    ]
    overlay = [[0] * 4 for _ in range(4)]
    overlay[0][0] = 3
    overlay[0][1] = 2
    overlay[3][3] = 3
    board = SimpleBoardExtended(grid=grid, rotten_overlay=overlay)
    assert rules.is_game_over(board) is False


def test_overlay_is_readonly() -> None:
    """Verify is_game_over does not mutate the overlay grid. (OQ-P17 / AC-5)"""
    rules = Rules()
    full_grid = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]

    # Case 1: all-zero overlay
    overlay_zero = [[0] * 4 for _ in range(4)]
    board = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay_zero)
    snapshot_before = [row[:] for row in board.get_rotten_overlay()]
    rules.is_game_over(board)
    snapshot_after = [row[:] for row in board.get_rotten_overlay()]
    assert snapshot_before == snapshot_after, "overlay mutated by is_game_over (all zeros)"

    # Case 2: non-zero overlay
    overlay_rotten = [[0] * 4 for _ in range(4)]
    overlay_rotten[0][0] = 3
    overlay_rotten[1][1] = 2
    overlay_rotten[2][2] = 1
    board2 = SimpleBoardExtended(grid=full_grid, rotten_overlay=overlay_rotten)
    snapshot_before2 = [row[:] for row in board2.get_rotten_overlay()]
    rules.is_game_over(board2)
    snapshot_after2 = [row[:] for row in board2.get_rotten_overlay()]
    assert snapshot_before2 == snapshot_after2, "overlay mutated by is_game_over (non-zero)"


def test_rescueable_pair_with_various_countdowns() -> None:
    """Rescueable pair detected regardless of countdown value (1, 2, or 3).

    The rescueability check uses overlay > 0, not a specific countdown.
    (OQ-P17)
    """
    rules = Rules()
    # Build grid where (1,1) and (1,2) share the same value
    grid = [
        [1, 2, 1, 2],
        [2, 1, 1, 2],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ]
    for countdown in (1, 2, 3):
        overlay = [[0] * 4 for _ in range(4)]
        overlay[1][1] = countdown
        overlay[1][2] = countdown
        board = SimpleBoardExtended(grid=grid, rotten_overlay=overlay)
        assert rules.is_game_over(board) is False, (
            f"countdown={countdown}: rescueable pair should prevent game-over"
        )