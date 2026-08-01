"""Test suite for src/core/board.py — Board class, types, and algorithm.

Purpose:
    Verifies correctness of the Board class, Direction enum, SlideResult,
    BoardState dataclasses, and the slide-and-merge algorithm. Covers all
    acceptance criteria from Sprint 1 Task 1 pseudocode.

System:
    Headless pytest suite. No fixtures, no conftest — each test constructs
    its own Board instance for full isolation. Imports only from
    src.core.board (Board, BoardState, Direction, SlideResult).

Dependencies:
    pytest, random — third-party and stdlib. src.core.board — production code.

Used-by:
    CI pipeline (pytest), Sprint 1 Task 1 acceptance verification.

Public API:
    Helper:
        _make_board_from_grid(grid: list[list[int]], score: int = 0,
                              moves: int = 0) -> Board
            Create a Board pre-populated with a specific grid, score, and
            move count for test setup. Uses private _grid, _score, _moves
            attributes (acceptable in test code).

    Test functions (28 standalone):
        test_direction_enum_members()          — Direction has 4 string members.
        test_slide_result_dataclass()          — SlideResult fields, types, defaults.
        test_boardstate_dataclass()            — BoardState fields and types.
        test_board_initial_state()             — Board() creates 4×4 zeros, score 0.
        test_board_get_set_cell()              — get_cell / set_cell roundtrip.
        test_board_out_of_bounds_raises()      — IndexError for invalid row/col.
        test_board_slide_left_merges()         — LEFT merges [2,2,0,0] -> [4,0,0,0].
        test_board_slide_right_merges()        — RIGHT merges [0,0,2,2] -> [0,0,0,4].
        test_board_slide_up_merges()           — UP merges columns correctly.
        test_board_slide_down_merges()         — DOWN merges columns correctly.
        test_board_slide_no_change_returns_false() — No move when grid unchanged.
        test_board_slide_updates_score()       — Score increments from merges.
        test_board_is_game_over_true()         — Dead board detected.
        test_board_is_game_over_false()        — Board with valid move not dead.
        test_board_reset()                     — reset() restores initial state.
        test_board_get_grid_defensive_copy()   — get_grid() returns independent copy.
        test_board_full_slide_cycle()          — All 4 directions on complex grid.
        test_board_move_count_only_increments_on_change() — moves +1 iff changed.
        test_board_rng_injection()             — Board accepts rng parameter.
        test_boardstate_to_dict_roundtrip()    — BoardState to_dict/from_dict.
        test_board_to_dict_from_dict_roundtrip() — Board to_dict/from_dict.
        test_tile_moves_left_slide()          — LEFT slide produces correct TileMove coords.
        test_tile_moves_right_slide()         — RIGHT slide maps reversed-column coords.
        test_tile_moves_up_slide()            — UP slide maps transposed coords.
        test_tile_moves_down_slide()          — DOWN slide maps reversed-transposed coords.
        test_tile_moves_merge_detection()     — merged=True + value=sum on merge.
        test_tile_moves_no_move()             — Illegal move returns empty tile_moves.
        test_tile_moves_backward_compatibility() — MoveResult/SlideResult tile_moves default.
"""

from __future__ import annotations

import random

import pytest

from src.core.board import Board, BoardState, Direction, SlideResult, slide_merge


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_board_from_grid(
    grid: list[list[int]], score: int = 0, moves: int = 0
) -> Board:
    """Create a Board pre-populated with a specific grid, score, and move count.

    Args:
        grid: A 4×4 nested list of tile values.
        score: Initial score to set.
        moves: Initial move count to set.

    Returns:
        A Board with the specified internal state.
    """
    board = Board()
    board._grid = [row[:] for row in grid]
    board._score = score
    board._moves = moves
    return board


# ---------------------------------------------------------------------------
# Type Tests
# ---------------------------------------------------------------------------


def test_direction_enum_members() -> None:
    """AC2: Direction enum has 4 members with correct string values."""
    assert len(Direction) == 4
    assert Direction.UP.value == "UP"
    assert Direction.DOWN.value == "DOWN"
    assert Direction.LEFT.value == "LEFT"
    assert Direction.RIGHT.value == "RIGHT"


def test_slide_result_dataclass() -> None:
    """AC5: SlideResult has new_grid, score_delta, and moved fields."""
    grid = [[0] * 4 for _ in range(4)]
    result = SlideResult(new_grid=grid, score_delta=0, moved=False)
    assert result.new_grid is grid
    assert result.score_delta == 0
    assert result.moved is False


def test_boardstate_dataclass() -> None:
    """AC3: BoardState has grid, score, moves fields with correct defaults."""
    grid = [[0] * 4 for _ in range(4)]
    bs = BoardState(grid=grid)
    assert bs.grid is grid
    assert bs.score == 0
    assert bs.moves == 0


# ---------------------------------------------------------------------------
# Initial State
# ---------------------------------------------------------------------------


def test_board_initial_state() -> None:
    """AC1: Fresh Board has 4×4 zeros, score 0, moves 0."""
    board = Board()
    grid = board.get_grid()
    assert len(grid) == 4
    for row in grid:
        assert len(row) == 4
        assert all(cell == 0 for cell in row)


# ---------------------------------------------------------------------------
# Cell Access
# ---------------------------------------------------------------------------


def test_board_get_set_cell() -> None:
    """AC1: get_cell and set_cell work within bounds."""
    board = Board()
    board.set_cell(0, 0, 2)
    assert board.get_cell(0, 0) == 2
    board.set_cell(3, 3, 4)
    assert board.get_cell(3, 3) == 4
    board.set_cell(1, 2, 16)
    assert board.get_cell(1, 2) == 16


def test_board_out_of_bounds_raises() -> None:
    """AC1: get_cell and set_cell raise IndexError for invalid indices."""
    board = Board()
    with pytest.raises(IndexError):
        board.get_cell(-1, 0)
    with pytest.raises(IndexError):
        board.get_cell(4, 0)
    with pytest.raises(IndexError):
        board.set_cell(0, 4, 2)
    with pytest.raises(IndexError):
        board.set_cell(0, -1, 2)


# ---------------------------------------------------------------------------
# Slide & Merge — Directional
# ---------------------------------------------------------------------------


def test_board_slide_left_merges() -> None:
    """AC5: Left slide merges adjacent equal tiles."""
    grid = [
        [2, 2, 4, 4],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    board = _make_board_from_grid(grid)
    result = board.move(Direction.LEFT)
    assert result.moved is True
    assert result.new_grid[0] == [4, 8, 0, 0]


def test_board_slide_right_merges() -> None:
    """AC5: Right slide merges adjacent equal tiles."""
    grid = [
        [2, 2, 4, 4],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    board = _make_board_from_grid(grid)
    result = board.move(Direction.RIGHT)
    assert result.moved is True
    assert result.new_grid[0] == [0, 0, 4, 8]


def test_board_slide_up_merges() -> None:
    """AC5: Up slide merges column-wise."""
    grid = [
        [2, 0, 0, 0],
        [2, 0, 0, 0],
        [4, 0, 0, 0],
        [4, 0, 0, 0],
    ]
    board = _make_board_from_grid(grid)
    result = board.move(Direction.UP)
    assert result.moved is True
    assert result.new_grid[0][0] == 4
    assert result.new_grid[1][0] == 8
    assert result.new_grid[2][0] == 0
    assert result.new_grid[3][0] == 0


def test_board_slide_down_merges() -> None:
    """AC5: Down slide merges column-wise."""
    grid = [
        [2, 0, 0, 0],
        [2, 0, 0, 0],
        [4, 0, 0, 0],
        [4, 0, 0, 0],
    ]
    board = _make_board_from_grid(grid)
    result = board.move(Direction.DOWN)
    assert result.moved is True
    assert result.new_grid[0][0] == 0
    assert result.new_grid[1][0] == 0
    assert result.new_grid[2][0] == 4
    assert result.new_grid[3][0] == 8


# ---------------------------------------------------------------------------
# Slide — No-Change and Score
# ---------------------------------------------------------------------------


def test_board_slide_no_change_returns_false() -> None:
    """AC5: SlideResult.moved=False when no tiles move or merge."""
    grid = [
        [0, 0, 0, 0],
        [0, 0, 0, 2],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    board = _make_board_from_grid(grid)
    result = board.move(Direction.RIGHT)
    assert result.moved is False
    assert result.score_delta == 0
    assert result.new_grid == grid


def test_board_slide_updates_score() -> None:
    """AC5: Score accumulates correctly after merges."""
    grid = [
        [2, 2, 4, 4],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    board = _make_board_from_grid(grid)
    result = board.move(Direction.LEFT)
    # [2,2,4,4] LEFT → [4,8,0,0]: score = 4 + 8 = 12
    assert result.score_delta == 12
    assert board._score == 12

    # Set up second merge
    board.set_cell(1, 0, 8)
    board.set_cell(1, 1, 8)
    result2 = board.move(Direction.LEFT)
    # [8,8,0,0] LEFT → [16,0,0,0]: score_delta = 16
    assert result2.score_delta == 16
    assert board._score == 28


# ---------------------------------------------------------------------------
# Game Over
# ---------------------------------------------------------------------------


def test_board_is_game_over_true() -> None:
    """AC6: is_game_over returns True on a dead board (no merges, no gaps)."""
    grid = [
        [2, 4, 2, 4],
        [4, 2, 4, 2],
        [2, 4, 2, 4],
        [4, 2, 4, 2],
    ]
    board = _make_board_from_grid(grid)
    assert board.is_game_over() is True


def test_board_is_game_over_false() -> None:
    """AC6: is_game_over returns False when at least one empty cell exists."""
    grid = [
        [2, 4, 2, 4],
        [4, 2, 4, 2],
        [2, 4, 2, 4],
        [4, 2, 4, 0],
    ]
    board = _make_board_from_grid(grid)
    assert board.is_game_over() is False


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


def test_board_reset() -> None:
    """AC1: Reset clears grid, score, and moves to initial state."""
    grid = [
        [2, 2, 4, 4],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    board = _make_board_from_grid(grid, score=10, moves=3)
    board.reset()
    assert board.get_grid() == [[0] * 4 for _ in range(4)]
    assert board._score == 0
    assert board._moves == 0


# ---------------------------------------------------------------------------
# Defensive Copy
# ---------------------------------------------------------------------------


def test_board_get_grid_defensive_copy() -> None:
    """AC1: get_grid returns a defensive copy — external mutation is isolated."""
    board = Board()
    board.set_cell(0, 0, 2)
    grid = board.get_grid()
    grid[0][0] = 999
    assert board.get_cell(0, 0) == 2


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


def test_board_full_slide_cycle() -> None:
    """AC1, AC5: Multi-slide integration — sequential moves accumulate correctly."""
    grid = [
        [2, 2, 4, 4],
        [2, 2, 4, 4],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    board = _make_board_from_grid(grid)
    total_score = 0

    # LEFT: [2,2,4,4] per row → [4,8,0,0], score=12 per row
    r1 = board.move(Direction.LEFT)
    assert r1.moved is True
    assert r1.new_grid[0] == [4, 8, 0, 0]
    assert r1.new_grid[1] == [4, 8, 0, 0]
    assert r1.score_delta == 24
    total_score += r1.score_delta

    # UP: col0=[4,4,0,0]→[8,0,0,0], col1=[8,8,0,0]→[16,0,0,0]
    r2 = board.move(Direction.UP)
    assert r2.moved is True
    assert r2.new_grid[0] == [8, 16, 0, 0]
    assert r2.score_delta == 24
    total_score += r2.score_delta

    # RIGHT: [8,16,0,0]→[0,0,8,16] (slide only, no merge)
    r3 = board.move(Direction.RIGHT)
    assert r3.moved is True
    assert r3.new_grid[0] == [0, 0, 8, 16]
    assert r3.score_delta == 0
    total_score += r3.score_delta

    # DOWN: slides 8 and 16 to bottom row
    r4 = board.move(Direction.DOWN)
    assert r4.moved is True
    assert r4.new_grid[3] == [0, 0, 8, 16]
    assert r4.score_delta == 0
    total_score += r4.score_delta

    assert board._score == total_score
    assert board._moves == 4


# ---------------------------------------------------------------------------
# Move Count
# ---------------------------------------------------------------------------


def test_board_move_count_only_increments_on_change() -> None:
    """AC5: Move counter does not increment for no-op slides."""
    board = Board()
    board.set_cell(0, 0, 2)
    result = board.move(Direction.LEFT)
    assert result.moved is False
    assert board._moves == 0


# ---------------------------------------------------------------------------
# RNG Injection
# ---------------------------------------------------------------------------


def test_board_rng_injection() -> None:
    """AC4: Board accepts rng parameter per ADR-010 without error."""
    board_default = Board()
    grid_default = board_default.get_grid()
    assert len(grid_default) == 4
    assert all(len(row) == 4 for row in grid_default)

    board_seeded = Board(rng=random.Random(42))
    grid_seeded = board_seeded.get_grid()
    assert len(grid_seeded) == 4
    assert all(len(row) == 4 for row in grid_seeded)


# ---------------------------------------------------------------------------
# Serialization Roundtrip
# ---------------------------------------------------------------------------


def test_boardstate_to_dict_roundtrip() -> None:
    """AC3, AC7: BoardState serialization roundtrip preserves all fields."""
    grid = [
        [2, 4, 8, 16],
        [32, 64, 128, 256],
        [512, 1024, 2048, 0],
        [0, 0, 0, 0],
    ]
    original = BoardState(grid=grid, score=1000, moves=42)
    data = original.to_dict()
    restored = BoardState.from_dict(data)
    assert restored.grid == original.grid
    assert restored.score == original.score
    assert restored.moves == original.moves


def test_board_to_dict_from_dict_roundtrip() -> None:
    """AC7: Board serialization roundtrip preserves grid, score, and moves."""
    grid = [
        [2, 4, 8, 16],
        [32, 64, 128, 256],
        [512, 1024, 2048, 0],
        [0, 0, 0, 0],
    ]
    board = _make_board_from_grid(grid, score=1000, moves=42)
    data = board.to_dict()
    restored = Board.from_dict(data)
    assert restored.get_grid() == board.get_grid()
    assert restored._score == board._score
    assert restored._moves == board._moves

# ---------------------------------------------------------------------------
# TileMove Tests (TDD Red Phase — TileMove does NOT exist yet, tests will FAIL)
# ---------------------------------------------------------------------------


def test_tile_moves_left_slide() -> None:
  """AC-1: LEFT slide produces correct TileMove coordinate mapping."""
  from src.core.board import TileMove

  grid = [
    [0, 0, 2, 2],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ]
  result = slide_merge(grid, Direction.LEFT)
  assert result.tile_moves is not None
  assert len(result.tile_moves) == 2

  assert all(isinstance(m, TileMove) for m in result.tile_moves)
  move_by_src = {(m.source_row, m.source_col): m for m in result.tile_moves}
  m1 = move_by_src[(0, 2)]
  assert m1.dest_row == 0
  assert m1.dest_col == 0
  assert m1.value == 2
  assert m1.merged is False

  m2 = move_by_src[(0, 3)]
  assert m2.dest_row == 0
  assert m2.dest_col == 0
  assert m2.value == 4
  assert m2.merged is True


def test_tile_moves_right_slide() -> None:
  """AC-7: RIGHT slide maps reversed-column coordinates correctly."""
  from src.core.board import TileMove

  grid = [
    [2, 4, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ]
  result = slide_merge(grid, Direction.RIGHT)
  assert len(result.tile_moves) == 2

  assert all(isinstance(m, TileMove) for m in result.tile_moves)
  move_by_src = {(m.source_row, m.source_col): m for m in result.tile_moves}
  m1 = move_by_src[(0, 0)]
  assert m1.dest_row == 0
  assert m1.dest_col == 2
  assert m1.value == 2
  assert m1.merged is False

  m2 = move_by_src[(0, 1)]
  assert m2.dest_row == 0
  assert m2.dest_col == 3
  assert m2.value == 4
  assert m2.merged is False


def test_tile_moves_up_slide() -> None:
  """AC-5: UP slide maps transposed grid coordinates correctly."""
  from src.core.board import TileMove

  grid = [
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [2, 0, 0, 0],
    [4, 0, 0, 0],
  ]
  result = slide_merge(grid, Direction.UP)
  assert len(result.tile_moves) == 2

  assert all(isinstance(m, TileMove) for m in result.tile_moves)
  move_by_src = {(m.source_row, m.source_col): m for m in result.tile_moves}
  m1 = move_by_src[(2, 0)]
  assert m1.dest_row == 0
  assert m1.dest_col == 0
  assert m1.value == 2
  assert m1.merged is False

  m2 = move_by_src[(3, 0)]
  assert m2.dest_row == 1
  assert m2.dest_col == 0
  assert m2.value == 4
  assert m2.merged is False


def test_tile_moves_down_slide() -> None:
  """AC-8: DOWN slide maps reversed-transposed coordinates correctly."""
  from src.core.board import TileMove

  grid = [
    [2, 0, 0, 0],
    [4, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ]
  result = slide_merge(grid, Direction.DOWN)
  assert len(result.tile_moves) == 2

  assert all(isinstance(m, TileMove) for m in result.tile_moves)
  move_by_src = {(m.source_row, m.source_col): m for m in result.tile_moves}
  m1 = move_by_src[(0, 0)]
  assert m1.dest_row == 2
  assert m1.dest_col == 0
  assert m1.value == 2
  assert m1.merged is False

  m2 = move_by_src[(1, 0)]
  assert m2.dest_row == 3
  assert m2.dest_col == 0
  assert m2.value == 4
  assert m2.merged is False


def test_tile_moves_merge_detection() -> None:
  """AC-2: merged=True is set on the destination tile of a merge; value equals sum."""
  from src.core.board import TileMove

  # Simple merge: [0,0,2,2] LEFT -> [4,0,0,0]
  grid = [
    [0, 0, 2, 2],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ]
  result = slide_merge(grid, Direction.LEFT)
  assert len(result.tile_moves) == 2
  assert all(isinstance(m, TileMove) for m in result.tile_moves)

  merged_flags = [m.merged for m in result.tile_moves]
  assert merged_flags.count(False) == 1, "Exactly one non-merged tile expected"
  assert merged_flags.count(True) == 1, "Exactly one merged tile expected"

  non_merged = next(m for m in result.tile_moves if not m.merged)
  merged = next(m for m in result.tile_moves if m.merged)
  assert non_merged.value == 2
  assert merged.value == 4  # sum: 2 + 2
  assert (non_merged.dest_row, non_merged.dest_col) == (
    merged.dest_row, merged.dest_col
  ), "Both tiles merge into the same destination"

  # Compound merge: [2,2,4,4] LEFT -> [4,8,0,0], score_delta = 12
  grid2 = [
    [2, 2, 4, 4],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ]
  result2 = slide_merge(grid2, Direction.LEFT)
  assert len(result2.tile_moves) == 4
  assert result2.score_delta == 12

  merged_values = sorted(
    m.value for m in result2.tile_moves if m.merged
  )
  assert merged_values == [4, 8], (
    f"Expected merged values [4, 8], got {merged_values}"
  )


def test_tile_moves_no_move() -> None:
  """AC-3: Illegal move (no grid change) returns empty tile_moves."""
  grid = [
    [0, 0, 0, 2],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ]
  result = slide_merge(grid, Direction.RIGHT)
  assert result.moved is False
  assert result.tile_moves == []

  # Also verify via Board.move() short-circuit path
  board = _make_board_from_grid([
    [2, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ])
  result2 = board.move(Direction.LEFT)
  assert result2.moved is False
  assert result2.tile_moves == []


def test_tile_moves_backward_compatibility() -> None:
  """AC-4: Constructing SlideResult without tile_moves defaults to empty list."""
  grid = [[0] * 4 for _ in range(4)]
  result = SlideResult(new_grid=grid, score_delta=0, moved=False)
  assert result.tile_moves == []
  assert isinstance(result.tile_moves, list)
  assert len(result.tile_moves) == 0

  # Also move=True path
  result2 = SlideResult(new_grid=grid, score_delta=4, moved=True)
  assert result2.tile_moves == []
  assert len(result2.tile_moves) == 0