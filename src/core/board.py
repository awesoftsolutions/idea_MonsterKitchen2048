"""Board module — grid state, slide/merge algorithm, and game-over detection.

Purpose:
    Provides the central Board class for Monster Kitchen 2048's core logic.
    Manages the 4x4 tile grid, executes slide-and-merge operations in four
    directions, tracks score and move counts, and serializes/deserializes
    board state for undo and persistence.

System:
    This module IS the core game-logic layer. It has zero rendering or UI
    dependencies. The slide-and-merge algorithm and helper functions are
    adopted from spikes/slide_merge.py per ADR-013 (Extract-and-Wrap
    strategy). All randomness is injectable via ADR-010.

Dependencies:
    copy, enum, random, dataclasses — stdlib only.

Used-by:
    Future sprints will add src/core/score.py (score persistence),
    src/core/history.py (undo stack), and Phase 3 rendering layers.

Public API:
    Constants:
        GRID_SIZE: int = 4  — hardcoded grid dimension per ADR-011.

    Direction (enum.Enum):
        Enumeration of slide directions with string values.
        Members: UP, DOWN, LEFT, RIGHT.

    SlideResult (dataclass):
        Result of a slide-and-merge operation.
        Fields:
            new_grid: list[list[int]]  — post-slide 4x4 grid (0 = empty).
            score_delta: int           — points earned from merges this move.
            moved: bool                — whether any tile changed position.

    BoardState (dataclass):
        Snapshot of board state for serialization.
        Fields:
            grid: list[list[int]]  — the 4x4 tile grid.
            score: int             — cumulative score.
            moves: int             — total move count.
        Methods:
            to_dict() -> dict                           — JSON-serializable snapshot.
            from_dict(data: dict) -> BoardState         — restore from dict.

    Board (class):
        Stateful 4x4 grid board manager.
        Constructor:
            __init__(rng: random.Random | None = None) -> None
        Methods:
            get_grid() -> list[list[int]]               — defensive copy of grid.
            get_cell(row: int, col: int) -> int         — read single cell.
            set_cell(row: int, col: int, value: int) -> None  — write single cell.
            move(direction: Direction) -> SlideResult   — slide-and-merge in direction.
            is_game_over() -> bool                      — True if no valid move exists.
            reset() -> None                             — restore to initial empty state.
            to_dict() -> dict                           — serialize via BoardState.
            from_dict(data: dict) -> Board (classmethod) — reconstruct from dict.

    Private functions (adopted from spike, ADR-013):
        _compact_left(values: list[int]) -> list[int]
        _slide_row_left(row: list[int]) -> tuple[list[int], int]
        _transpose(grid: list[list[int]]) -> list[list[int]]

    Public algorithm function:
        slide_merge(grid: list[list[int]], direction: Direction) -> SlideResult
"""

from __future__ import annotations

import copy
import enum
import random
from dataclasses import dataclass


# ADR-011: Grid size is hardcoded to 4×4 per operator directive DR-004.
GRID_SIZE: int = 4


# --- Types adopted from spikes/slide_merge.py (ADR-013) ---


class Direction(enum.Enum):
    """Enumeration of slide directions."""

    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


@dataclass
class SlideResult:
    """Result of a slide-and-merge operation.

    Attributes:
        new_grid: The 4×4 grid state after slide-and-merge.
        score_delta: Sum of merged tile values (0 if no merges).
        moved: True if any tile changed position or merged.
    """

    new_grid: list[list[int]]
    score_delta: int = 0
    moved: bool = False


@dataclass
class BoardState:
    """Snapshot of the complete board state for serialization.

    Attributes:
        grid: The 4×4 tile value grid.
        score: Current accumulated score.
        moves: Number of board-changing moves made.
    """

    grid: list[list[int]]
    score: int = 0
    moves: int = 0

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict.

        Returns:
            A dict with keys 'grid', 'score', 'moves'.
        """
        return {
            "grid": copy.deepcopy(self.grid),
            "score": self.score,
            "moves": self.moves,
        }

    @classmethod
    def from_dict(cls, data: dict) -> BoardState:
        """Reconstruct a BoardState from a serialized dict.

        Args:
            data: A dict with keys 'grid', 'score', 'moves'.

        Returns:
            A new BoardState instance.

        Raises:
            ValueError: If required keys are missing or grid dimensions are invalid.
        """
        grid = data.get("grid")
        score = data.get("score", 0)
        moves = data.get("moves", 0)
        if grid is None:
            raise ValueError("Missing 'grid' key")
        if not isinstance(grid, list) or len(grid) != GRID_SIZE:
            raise ValueError(f"Grid must have {GRID_SIZE} rows")
        for i, row in enumerate(grid):
            if not isinstance(row, list) or len(row) != GRID_SIZE:
                raise ValueError(f"Row {i} must have {GRID_SIZE} columns")
        return cls(grid=copy.deepcopy(grid), score=score, moves=moves)


class Board:
    """Stateful 4×4 grid board manager.

    Manages the tile value grid, score accumulation, move counting,
    and delegates slide-and-merge operations to slide_merge().
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        """Initialize a new Board with an empty 4×4 grid.

        Args:
            rng: Optional random.Random instance for deterministic testing.
                 If None, creates an unseeded random.Random() per ADR-010.
        """
        self._rng: random.Random = rng if rng is not None else random.Random()
        self._grid: list[list[int]] = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self._score: int = 0
        self._moves: int = 0

    def get_grid(self) -> list[list[int]]:
        """Return a defensive copy of the internal grid.

        Returns:
            A deep copy of the 4×4 grid. External mutation does not affect Board.
        """
        return [row[:] for row in self._grid]

    def get_cell(self, row: int, col: int) -> int:
        """Read a single cell value by row and column indices.

        Args:
            row: Row index (0-based).
            col: Column index (0-based).

        Returns:
            The tile value at the specified position.

        Raises:
            IndexError: If row or col is out of [0, GRID_SIZE).
        """
        if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
            raise IndexError(
                f"Cell ({row}, {col}) is out of bounds for {GRID_SIZE}x{GRID_SIZE} grid"
            )
        return self._grid[row][col]

    def set_cell(self, row: int, col: int, value: int) -> None:
        """Write a single cell value by row and column indices.

        Args:
            row: Row index (0-based).
            col: Column index (0-based).
            value: Tile value to set.

        Raises:
            IndexError: If row or col is out of [0, GRID_SIZE).
        """
        if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
            raise IndexError(
                f"Cell ({row}, {col}) is out of bounds for {GRID_SIZE}x{GRID_SIZE} grid"
            )
        self._grid[row][col] = value

    def move(self, direction: Direction) -> SlideResult:
        """Execute a slide-and-merge in the given direction.

        Args:
            direction: One of Direction.UP, DOWN, LEFT, RIGHT.

        Returns:
            SlideResult with new_grid, score_delta, and moved flag.
        """
        old_grid = [row[:] for row in self._grid]
        result = slide_merge(self._grid, direction)
        new_grid = result.new_grid

        if new_grid == old_grid:
            return SlideResult(new_grid=new_grid, score_delta=0, moved=False)

        self._grid = new_grid
        self._score += result.score_delta
        self._moves += 1
        return SlideResult(
            new_grid=new_grid,
            score_delta=result.score_delta,
            moved=True,
        )

    def is_game_over(self) -> bool:
        """Detect whether the game is over.

        Returns:
            True if no direction produces a grid change.
        """
        for direction in Direction:
            result = slide_merge(self._grid, direction)
            if result.new_grid != self._grid:
                return False
        return True

    def reset(self) -> None:
        """Reset the board to initial state — all zeros, score 0, moves 0."""
        self._grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self._score = 0
        self._moves = 0

    def to_dict(self) -> dict:
        """Serialize the Board to a JSON-compatible dict.

        Returns:
            A dict with keys 'grid', 'score', 'moves'.
        """
        state = BoardState(
            grid=self.get_grid(),
            score=self._score,
            moves=self._moves,
        )
        return state.to_dict()

    @classmethod
    def from_dict(cls, data: dict) -> Board:
        """Reconstruct a Board from a serialized dict.

        Args:
            data: A dict with keys 'grid', 'score', 'moves'.

        Returns:
            A new Board instance with restored state and unseeded default RNG.
        """
        state = BoardState.from_dict(data)
        board = cls()
        board._grid = copy.deepcopy(state.grid)
        board._score = state.score
        board._moves = state.moves
        return board


# --- Private algorithm functions adopted from spikes/slide_merge.py (ADR-013) ---


def _compact_left(items: list[int]) -> list[int]:
    """Compact non-zero tile values to the left, preserving order.

    Args:
        items: A list of tile values (0 = empty).

    Returns:
        A new list with non-zero tiles gathered left, trailing zeros filling remaining positions.
    """
    length = len(items)
    slid: list[int] = [0] * length
    write_index = 0
    for tile in items:
        if tile != 0:
            slid[write_index] = tile
            write_index += 1
    return slid


def _slide_row_left(row: list[int]) -> tuple[list[int], int]:
    """Slide a single row leftward with merging.

    Three-step pattern: compact, merge adjacent equal pairs left-to-right (each tile
    merges at most once), compact again.

    Args:
        row: A list of tile values (0 = empty).

    Returns:
        (merged_row, row_score) — the processed row and the score earned.
    """
    length = len(row)
    slid = _compact_left(row)

    row_score = 0
    merged: list[int] = [0] * length
    source_index = 0
    dest_index = 0
    while source_index < length:
        if (
            source_index < length - 1
            and slid[source_index] != 0
            and slid[source_index] == slid[source_index + 1]
        ):
            merged[dest_index] = slid[source_index] * 2
            row_score += merged[dest_index]
            source_index += 2
        else:
            merged[dest_index] = slid[source_index]
            source_index += 1
        dest_index += 1

    final = _compact_left(merged)
    return final, row_score


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    """Transpose a grid — rows become columns, columns become rows.

    Args:
        grid: An NxN grid of tile values.

    Returns:
        A new transposed grid. The input is not mutated.
    """
    num_rows = len(grid)
    num_cols = len(grid[0])
    return [[grid[r][c] for r in range(num_rows)] for c in range(num_cols)]


def slide_merge(grid: list[list[int]], direction: Direction) -> SlideResult:
    """Slide and merge tiles in the given direction.

    Public API — adopted from spikes/slide_merge.py with production SlideResult (3 fields).

    Args:
        grid: NxN grid of tile values (0 = empty). Not mutated.
        direction: One of Direction.UP, DOWN, LEFT, RIGHT.

    Returns:
        SlideResult with new_grid, score_delta, and moved computed by caller.

    Raises:
        ValueError: If grid is empty or not square.
    """
    if not grid or any(not row for row in grid):
        raise ValueError("Grid must not be empty")
    if len(set(len(row) for row in grid)) > 1:
        raise ValueError("Grid must be square")

    working_grid = copy.deepcopy(grid)
    total_score = 0
    result_grid: list[list[int]] = []

    if direction == Direction.LEFT:
        for row in working_grid:
            merged_row, row_score = _slide_row_left(row)
            result_grid.append(merged_row)
            total_score += row_score

    elif direction == Direction.RIGHT:
        for row in working_grid:
            reversed_row = row[::-1]
            merged_row, row_score = _slide_row_left(reversed_row)
            result_grid.append(merged_row[::-1])
            total_score += row_score

    elif direction == Direction.UP:
        transposed = _transpose(working_grid)
        processed: list[list[int]] = []
        for col_as_row in transposed:
            merged_row, row_score = _slide_row_left(col_as_row)
            processed.append(merged_row)
            total_score += row_score
        result_grid = _transpose(processed)

    elif direction == Direction.DOWN:
        transposed = _transpose(working_grid)
        processed: list[list[int]] = []
        for col_as_row in transposed:
            reversed_row = col_as_row[::-1]
            merged_row, row_score = _slide_row_left(reversed_row)
            processed.append(merged_row[::-1])
            total_score += row_score
        result_grid = _transpose(processed)

    moved = result_grid != grid
    return SlideResult(new_grid=result_grid, score_delta=total_score, moved=moved)
