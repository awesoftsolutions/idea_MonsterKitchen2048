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
     src/core/score.py (score persistence) — Sprint 1 Task 2,
     src/core/history.py (undo stack) — Sprint 1 Task 5,
     src/core/rules.py (move legality, re-exports slide_merge),
     src/core/twist.py (contamination mechanic) — Sprint 2 Task 3.
     Phase 3 will add rendering layers.

Public API:
    Constants:
        GRID_SIZE: int = 4  — hardcoded grid dimension per ADR-011.

    Direction (enum.Enum):
        Enumeration of slide directions with string values.
        Members: UP, DOWN, LEFT, RIGHT.

    TileMove (dataclass):
        Movement record for a single tile during a slide-and-merge operation.
        Fields:
            source_row: int  — row index before the move.
            source_col: int  — column index before the move.
            dest_row: int    — row index after the move.
            dest_col: int    — column index after the move.
            value: int       — pre-merge value (source) or sum (merged destination).
            merged: bool     — True for merged destination; False for simple slides.

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
# CHANGELOG:
# - Sprint 1: Add Board.grid property for BoardProtocol compliance
# - Sprint 1: Fix has_rotten logic in is_game_over — game continues when rotten tiles present
# - Sprint 1: Add has_rotten awareness to is_game_over
# - Sprint 2: Add Board overlay API (get_rotten_overlay, add_rotten, remove_rotten, BoardState.rotten_overlay)
# - Sprint 3 Review: Type-annotation strictness fixes (typed dict generics, renamed local variable)

from __future__ import annotations

import copy
import enum
import random
from dataclasses import dataclass, field
from typing import Any


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
class TileMove:
    """Movement record for a single tile during a slide-and-merge operation.

    Attributes:
        source_row: Row index (0-based) of the tile before the move.
        source_col: Column index (0-based) of the tile before the move.
        dest_row: Row index (0-based) of the tile's destination after the move.
        dest_col: Column index (0-based) of the tile's destination after the move.
        value: Tile value (pre-merge value for the non-merged source; sum for the merged destination).
        merged: True only for the destination tile of a merge; False for simple slides and the non-merged source of a merge.
    """

    source_row: int
    source_col: int
    dest_row: int
    dest_col: int
    value: int
    merged: bool


@dataclass
class SlideResult:
    """Result of a slide-and-merge operation.

    Attributes:
        new_grid: The 4×4 grid state after slide-and-merge.
        score_delta: Sum of merged tile values (0 if no merges).
        moved: True if any tile changed position or merged.
        tile_moves: Per-tile movement records for animation (empty if no move).
    """

    new_grid: list[list[int]]
    score_delta: int = 0
    moved: bool = False
    tile_moves: list[TileMove] = field(default_factory=list)


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
    rotten_overlay: list[list[int]] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict.

        Returns:
            A dict with keys 'grid', 'score', 'moves', and optionally
            'rotten_overlay' when twist state is active.
        """
        result: dict[str, Any] = {
            "grid": copy.deepcopy(self.grid),
            "score": self.score,
            "moves": self.moves,
        }
        if self.rotten_overlay is not None:
            result["rotten_overlay"] = copy.deepcopy(self.rotten_overlay)
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BoardState:
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
        overlay = data.get("rotten_overlay", None)
        return cls(
            grid=copy.deepcopy(grid),
            score=score,
            moves=moves,
            rotten_overlay=copy.deepcopy(overlay) if overlay is not None else None,
        )


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
        self._rotten_overlay: list[list[int]] | None = None

    @property
    def grid(self) -> list[list[int]]:
        """The 4x4 grid of tile values. 0 = empty.

        Copy semantics match get_grid() — mutation does not affect Board internals.
        """
        return self.get_grid()

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
            SlideResult with new_grid, score_delta, moved, and tile_moves.
        """
        old_grid = [row[:] for row in self._grid]
        result = slide_merge(self._grid, direction)
        new_grid = result.new_grid

        if new_grid == old_grid:
            return SlideResult(
                new_grid=new_grid, score_delta=0, moved=False, tile_moves=[]
            )

        self._grid = new_grid
        self._score += result.score_delta
        self._moves += 1
        return SlideResult(
            new_grid=new_grid,
            score_delta=result.score_delta,
            moved=True,
            tile_moves=result.tile_moves,
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
        self._rotten_overlay = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the Board to a JSON-compatible dict.

        Returns:
            A dict with keys 'grid', 'score', 'moves'.
        """
        overlay_copy = None
        if self._rotten_overlay is not None:
            overlay_copy = [row[:] for row in self._rotten_overlay]
        state = BoardState(
            grid=self.get_grid(),
            score=self._score,
            moves=self._moves,
            rotten_overlay=overlay_copy,
        )
        return state.to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Board:
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
        if state.rotten_overlay is not None:
            board._rotten_overlay = copy.deepcopy(state.rotten_overlay)
        return board

    def spawn_tile(self) -> tuple[int, int]:
        """Place a new tile at a random empty cell.

        Tile value is 2 with 90% probability or 4 with 10% probability.

        Returns:
            The (row, col) position where the tile was placed.

        Raises:
            ValueError: If no empty cells exist on the board.
        """
        empty = self.get_empty_cells()
        if not empty:
            raise ValueError("No empty cells")
        row, col = self._rng.choice(empty)
        roll = self._rng.random()
        value = 2 if roll < 0.9 else 4
        self._grid[row][col] = value
        return (row, col)

    def get_empty_cells(self) -> list[tuple[int, int]]:
        """Return list of (row, col) positions where value is 0.

        Returns:
            A list of all empty cell coordinates.
        """
        empty: list[tuple[int, int]] = []
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if self._grid[row][col] == 0:
                    empty.append((row, col))
        return empty

    def is_empty(self, row: int, col: int) -> bool:
        """Check whether a cell is empty (value 0).

        Args:
            row: Row index (0-based).
            col: Column index (0-based).

        Returns:
            True if the cell value is 0.

        Raises:
            IndexError: If row or col is out of bounds.
        """
        if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
            raise IndexError(
                f"Cell ({row}, {col}) is out of bounds for {GRID_SIZE}x{GRID_SIZE} grid"
            )
        return self._grid[row][col] == 0

    def get_neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        """Return valid adjacent positions (UP, DOWN, LEFT, RIGHT) within grid bounds.

        Args:
            row: Row index (0-based).
            col: Column index (0-based).

        Returns:
            A list of valid neighbor coordinates (2-4 depending on position).

        Raises:
            IndexError: If row or col is out of bounds.
        """
        if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
            raise IndexError(
                f"Cell ({row}, {col}) is out of bounds for {GRID_SIZE}x{GRID_SIZE} grid"
            )
        neighbors: list[tuple[int, int]] = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr = row + dr
            nc = col + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                neighbors.append((nr, nc))
        return neighbors

    def get_rotten_overlay(self) -> list[list[int]]:
        """Return a defensive copy of the internal rotten overlay grid.

        The overlay uses 0 for healthy cells and 1-3 for countdown remaining.

        Returns:
            A deep copy of the 4x4 overlay grid.
        """
        if self._rotten_overlay is None:
            self._init_overlay()
        assert self._rotten_overlay is not None  # guaranteed by _init_overlay
        return [row[:] for row in self._rotten_overlay]

    def add_rotten(self, row: int, col: int, countdown: int) -> None:
        """Place a rotten marker on a cell.

        Args:
            row: Row index (0-based).
            col: Column index (0-based).
            countdown: Remaining turns before contamination (1-3).

        Raises:
            IndexError: If row or col is out of bounds.
            ValueError: If countdown is out of range or cell is empty.
        """
        if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
            raise IndexError(
                f"Cell ({row}, {col}) is out of bounds for {GRID_SIZE}x{GRID_SIZE} grid"
            )
        if countdown < 1 or countdown > 3:
            raise ValueError(f"Countdown must be between 1 and 3, got {countdown}")
        if self._grid[row][col] == 0:
            raise ValueError("Cannot add rotten to empty cell")
        if self._rotten_overlay is None:
            self._init_overlay()
        assert self._rotten_overlay is not None  # guaranteed by _init_overlay
        self._rotten_overlay[row][col] = countdown

    def remove_rotten(self, row: int, col: int) -> None:
        """Clear a rotten marker. Silent no-op if not rotten or out of bounds.

        Args:
            row: Row index (0-based).
            col: Column index (0-based).
        """
        if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
            return
        if self._rotten_overlay is None:
            return
        self._rotten_overlay[row][col] = 0

    def get_state(self) -> BoardState:
        """Return full state snapshot as a BoardState deep copy.

        Returns:
            A BoardState with copies of grid, score, moves, and overlay.
        """
        overlay_copy = None
        if self._rotten_overlay is not None:
            overlay_copy = [row[:] for row in self._rotten_overlay]
        return BoardState(
            grid=self.get_grid(),
            score=self._score,
            moves=self._moves,
            rotten_overlay=overlay_copy,
        )

    def set_state(self, state: BoardState) -> None:
        """Restore board from a snapshot.

        Restores both value grid and rotten overlay atomically.

        Args:
            state: A BoardState snapshot to restore from.
        """
        self._grid = copy.deepcopy(state.grid)
        self._score = state.score
        self._moves = state.moves
        if state.rotten_overlay is not None:
            self._rotten_overlay = copy.deepcopy(state.rotten_overlay)
        else:
            self._rotten_overlay = None

    def _init_overlay(self) -> None:
        """Initialize internal rotten overlay as a 4x4 grid of zeros."""
        self._rotten_overlay = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]


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


def _slide_row_left(
    row: list[int],
) -> tuple[list[int], int, list[tuple[int, int, int, bool]]]:
    """Slide a single row leftward with merging and tile journey tracking.

    Three-step pattern: compact, merge adjacent equal pairs left-to-right (each tile
    merges at most once), compact again. Tracks each non-zero tile's journey from its
    original position to its final position through the slide-and-merge cycle.

    Args:
        row: A list of tile values (0 = empty).

    Returns:
        (merged_row, row_score, tile_journeys) — the processed row, the score earned,
        and a list of (source_col, dest_col, value, merged) tuples for each tile that moved.
    """
    length = len(row)

    # Build source_positions: parallel list of original column indices for non-zero tiles
    source_positions: list[int] = []
    for i in range(length):
        if row[i] != 0:
            source_positions.append(i)

    slid = _compact_left(row)

    row_score = 0
    tile_journeys: list[tuple[int, int, int, bool]] = []
    merged_list: list[int] = [0] * length
    source_index = 0
    dest_index = 0
    while source_index < length:
        if (
            source_index < length - 1
            and slid[source_index] != 0
            and slid[source_index] == slid[source_index + 1]
        ):
            # Merge case: two tiles collide into one destination
            merged_value = slid[source_index] * 2
            merged_list[dest_index] = merged_value
            row_score += merged_value

            # Journey for first source tile (non-merged)
            tile_journeys.append(
                (source_positions[source_index], dest_index, slid[source_index], False)
            )
            # Journey for second source tile (merged destination)
            tile_journeys.append(
                (source_positions[source_index + 1], dest_index, merged_value, True)
            )

            source_index += 2
        else:
            # Simple slide case
            merged_list[dest_index] = slid[source_index]
            if slid[source_index] != 0:
                tile_journeys.append(
                    (
                        source_positions[source_index],
                        dest_index,
                        slid[source_index],
                        False,
                    )
                )
            source_index += 1
        dest_index += 1

    final = _compact_left(merged_list)
    return final, row_score, tile_journeys


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

    Public API — adopted from spikes/slide_merge.py with production SlideResult including tile_moves.

    Args:
        grid: NxN grid of tile values (0 = empty). Not mutated.
        direction: One of Direction.UP, DOWN, LEFT, RIGHT.

    Returns:
        SlideResult with new_grid, score_delta, moved, and tile_moves.

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
    all_tile_moves: list[TileMove] = []

    if direction == Direction.LEFT:
        for r, row in enumerate(working_grid):
            merged_row, row_score, journeys = _slide_row_left(row)
            result_grid.append(merged_row)
            total_score += row_score
            for src_col, dest_col, value, merged in journeys:
                all_tile_moves.append(
                    TileMove(
                        source_row=r,
                        source_col=src_col,
                        dest_row=r,
                        dest_col=dest_col,
                        value=value,
                        merged=merged,
                    )
                )

    elif direction == Direction.RIGHT:
        for r, row in enumerate(working_grid):
            reversed_row = row[::-1]
            merged_row_rev, row_score, journeys = _slide_row_left(reversed_row)
            result_grid.append(merged_row_rev[::-1])
            total_score += row_score
            for src_col_rev, dest_col_rev, value, merged in journeys:
                all_tile_moves.append(
                    TileMove(
                        source_row=r,
                        source_col=GRID_SIZE - 1 - src_col_rev,
                        dest_row=r,
                        dest_col=GRID_SIZE - 1 - dest_col_rev,
                        value=value,
                        merged=merged,
                    )
                )

    elif direction == Direction.UP:
        transposed = _transpose(working_grid)
        processed: list[list[int]] = []
        for c, col_as_row in enumerate(transposed):
            merged_col, col_score, journeys = _slide_row_left(col_as_row)
            processed.append(merged_col)
            total_score += col_score
            for src_idx, dest_idx, value, merged in journeys:
                all_tile_moves.append(
                    TileMove(
                        source_row=src_idx,
                        source_col=c,
                        dest_row=dest_idx,
                        dest_col=c,
                        value=value,
                        merged=merged,
                    )
                )
        result_grid = _transpose(processed)

    elif direction == Direction.DOWN:
        transposed = _transpose(working_grid)
        processed_down: list[list[int]] = []
        for c, col_as_row in enumerate(transposed):
            reversed_row = col_as_row[::-1]
            merged_col_rev, col_score, journeys = _slide_row_left(reversed_row)
            processed_down.append(merged_col_rev[::-1])
            total_score += col_score
            for src_idx_rev, dest_idx_rev, value, merged in journeys:
                all_tile_moves.append(
                    TileMove(
                        source_row=GRID_SIZE - 1 - src_idx_rev,
                        source_col=c,
                        dest_row=GRID_SIZE - 1 - dest_idx_rev,
                        dest_col=c,
                        value=value,
                        merged=merged,
                    )
                )
        result_grid = _transpose(processed_down)

    moved = result_grid != grid
    return SlideResult(
        new_grid=result_grid,
        score_delta=total_score,
        moved=moved,
        tile_moves=all_tile_moves if moved else [],
    )
