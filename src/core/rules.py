"""Rules module for Monster Kitchen 2048.

Provides move legality checking and game-over detection for a 4×4
slide-and-merge board. This module is stateless — the Rules class has
no instance state and all methods accept a board parameter.

The module also contains the core slide-and-merge algorithm adopted from
``spikes/slide_merge.py`` so that Rules has zero cross-module dependencies.

Public API:
    BoardProtocol: Minimal board interface with a ``grid`` property.
    Direction: Enum of slide directions (UP, DOWN, LEFT, RIGHT).
    SlideResult: Dataclass holding the resulting grid and earned score.
    slide_merge: Slide-and-merge a 4×4 grid in a given direction.
    Rules: Stateless class for move legality and game-over detection.

Dependencies: typing, enum, dataclasses, copy — Python stdlib only.
Zero rendering or framework imports.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# BoardProtocol — minimal interface Rules depends on
# ---------------------------------------------------------------------------


@runtime_checkable
class BoardProtocol(Protocol):
    """Minimal board interface for Rules.

    Uses structural typing so the production Board class does not need
    to explicitly inherit from this protocol.
    """

    @property
    def grid(self) -> list[list[int]]:
        """The 4×4 grid of tile values. 0 = empty."""
        ...


# ---------------------------------------------------------------------------
# Direction — four slide directions (adopted from spike lines 52-58)
# ---------------------------------------------------------------------------


class Direction(str, Enum):
    """Enumeration of slide directions."""

    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


# ---------------------------------------------------------------------------
# SlideResult — result container (adopted from spike lines 62-71)
# ---------------------------------------------------------------------------


@dataclass
class SlideResult:
    """Result of a slide-and-merge operation.

    Attributes:
        grid: The 4×4 grid state after slide-and-merge.
        score: Sum of all merged tile values (0 if no merges occurred).
    """

    grid: list[list[int]]
    score: int = 0


# ---------------------------------------------------------------------------
# Internal helpers (adopted from spike lines 74-151)
# ---------------------------------------------------------------------------


def _compact_left(row: list[int]) -> list[int]:
    """Remove zeros from row, shifting non-zero values to the left.

    Preserves the relative order of non-zero elements and pads the
    right side with zeros to maintain the original row length.

    Args:
        row: A list of tile values (0 = empty).

    Returns:
        A new list of the same length with non-zero tiles gathered
        from the left, and trailing zeros filling remaining positions.
    """
    length = len(row)
    slid: list[int] = [0] * length
    write_index = 0
    for tile in row:
        if tile != 0:
            slid[write_index] = tile
            write_index += 1
    return slid


def _slide_row_left(row: list[int]) -> tuple[list[int], int]:
    """Slide a single row leftward with merging.

    Three-step pattern following the 2048 slide-and-merge rules:
    1. Slide all non-zero tiles to the left, closing gaps.
    2. Merge adjacent equal pairs left-to-right (each tile merges at most once).
    3. Slide left again to close gaps created by merges.

    Args:
        row: A list of tile values (0 = empty).

    Returns:
        A tuple of (merged_row, row_score) — the processed row and points earned.
    """
    length = len(row)

    # Step 1: Slide non-zero tiles left — close all gaps.
    slid = _compact_left(row)

    # Step 2: Merge adjacent equal pairs left-to-right with skip.
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

    # Step 3: Slide left again to close gaps created by merges.
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


# ---------------------------------------------------------------------------
# slide_merge — main algorithm (adopted from spike lines 154-216)
# ---------------------------------------------------------------------------


def slide_merge(grid: list[list[int]], direction: Direction) -> SlideResult:
    """Slide and merge tiles in the given direction on a 4×4 grid.

    The input grid is deep-copied and never mutated. The result is a
    new grid reflecting the slide-and-merge operation and the score
    earned from any merges.

    Args:
        grid: 4×4 grid of tile values (0 = empty). Not mutated.
        direction: One of Direction.UP, DOWN, LEFT, RIGHT.

    Returns:
        SlideResult with grid (new grid state) and score (sum of merged values).

    Raises:
        ValueError: If grid is empty or not square.
    """
    # Validate grid.
    if not grid or any(not row for row in grid):
        raise ValueError("Grid must not be empty")
    if len(set(len(row) for row in grid)) > 1:
        raise ValueError("Grid must be square")

    # Deep copy — the caller's grid must not be mutated.
    working_grid = copy.deepcopy(grid)

    # Direction-specific processing.
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

    return SlideResult(grid=result_grid, score=total_score)


# ---------------------------------------------------------------------------
# Rules — move legality and game-over detection
# ---------------------------------------------------------------------------


class Rules:
    """Stateless rules engine for Monster Kitchen 2048.

    Provides move legality checking and game-over detection.
    All methods accept a board parameter — no instance state is stored.
    """

    def is_move_legal(self, board: BoardProtocol, direction: Direction) -> bool:
        """Check whether sliding in the given direction changes the grid.

        Deep-copies the board grid, applies slide_merge, and compares
        the result to the original. If any cell differs, the move is legal.

        Args:
            board: An object satisfying BoardProtocol (must have a grid property).
            direction: The slide direction to test.

        Returns:
            True if the grid would change after sliding, False otherwise.
        """
        original = board.grid
        result = slide_merge(original, direction)
        return result.grid != original

    def get_legal_moves(self, board: BoardProtocol) -> list[Direction]:
        """Return all directions where a legal move exists.

        Iterates UP, DOWN, LEFT, RIGHT in that order and collects
        directions where ``is_move_legal`` returns True.

        Args:
            board: An object satisfying BoardProtocol.

        Returns:
            List of legal Direction values in deterministic order.
        """
        legal: list[Direction] = []
        for direction in Direction:
            if self.is_move_legal(board, direction):
                legal.append(direction)
        return legal

    def is_game_over(self, board: BoardProtocol, has_rotten: bool = False) -> bool:
        """Determine whether the game is over for the given board.

        The game is over when:
        1. There are no empty cells (all tiles non-zero), AND
        2. No legal move exists in any direction.

        The ``has_rotten`` flag provides twist-awareness: when True on a
        full board with non-zero tiles, the game is NOT over because
        rotten tiles could still be cleared via rotten-merges-rotten.

        Invariant: if any direction is legal, returns False.

        Args:
            board: An object satisfying BoardProtocol.
            has_rotten: If True, prevents premature game-over on full boards
                with non-zero tiles (rotten tiles may still be cleared).

        Returns:
            True if the game is over, False otherwise.
        """
        grid = board.grid

        # Phase 1: Check for empty cells.
        for row in grid:
            for value in row:
                if value == 0:
                    return False

        # Phase 2: has_rotten twist-awareness.
        if has_rotten:
            for row in grid:
                for value in row:
                    if value != 0:
                        return False

        # Phase 3: Check all directions for legal moves.
        legal = self.get_legal_moves(board)
        if legal:
            return False

        return True
