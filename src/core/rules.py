"""Slide-and-merge algorithm for the 2048 game.

This module provides the core game logic for sliding and merging tiles
on a 4×4 grid in four directions (UP, DOWN, LEFT, RIGHT). The algorithm
uses a row-based approach with direction normalization: LEFT/RIGHT process
rows directly; UP/DOWN transpose the grid, process rows as LEFT, then
transpose back.

System: Core game logic module for slide-and-merge operations. Pure
    algorithm with no rendering, I/O, or framework dependencies. Consumed
    by board.py (Phase 2) and test_rules.py.

Dependencies: copy, enum — Python stdlib only. Zero pygame or display
    dependencies, fulfilling the logic-rendering separation principle.

Used-by: board.py (Phase 2 production integration), test_rules.py
    (pytest validation suite).

Public API:
    Direction — enumeration of the four slide directions
    slide_merge — performs a complete slide-and-merge operation
"""

from __future__ import annotations

import copy
import enum


class Direction(enum.Enum):
    """Enumeration of slide directions."""

    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


def _slide_row_left(row: list[int]) -> tuple[list[int], int]:
    """Slide a single row leftward with merging.

    Three-step pattern following the 2048 slide-and-merge rules:
    1. Slide all non-zero tiles to the left, closing gaps.
    2. Merge adjacent equal pairs left-to-right (each tile merges at most once).
    3. Slide left again to close gaps created by merges.

    Args:
        row: A list of tile values (0 = empty).

    Returns:
        (merged_row, row_score) — the processed row and the score earned.
    """
    length = len(row)

    # Step 1: Slide non-zero tiles left — close all gaps.
    slided: list[int] = [0] * length
    write_index = 0
    for tile in row:
        if tile != 0:
            slided[write_index] = tile
            write_index += 1

    # Step 2: Merge adjacent equal pairs left-to-right with skip.
    # Each tile participates in at most one merge per pass.
    row_score = 0
    merged: list[int] = [0] * length
    source_index = 0
    dest_index = 0
    while source_index < length:
        if (
            source_index < length - 1
            and slided[source_index] != 0
            and slided[source_index] == slided[source_index + 1]
        ):
            # Pair found: merge and skip the partner tile.
            merged[dest_index] = slided[source_index] * 2
            row_score += merged[dest_index]
            source_index += 2
        else:
            merged[dest_index] = slided[source_index]
            source_index += 1
        dest_index += 1

    # Step 3: Slide left again to close gaps created by merges.
    final: list[int] = [0] * length
    write_index = 0
    for tile in merged:
        if tile != 0:
            final[write_index] = tile
            write_index += 1

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


def slide_merge(
    grid: list[list[int]], direction: Direction
) -> tuple[list[list[int]], int]:
    """Slide and merge tiles in the given direction.

    Args:
        grid: NxN grid of tile values (0 = empty). Not mutated.
        direction: One of Direction.UP, DOWN, LEFT, RIGHT.

    Returns:
        (new_grid, score_delta) — new grid state, sum of merged tile values.

    Raises:
        ValueError: If grid is empty or not square.
    """
    # Step 1: Validate grid.
    if not grid or any(not row for row in grid):
        raise ValueError("Grid must not be empty")
    if len(set(len(row) for row in grid)) > 1:
        raise ValueError("Grid must be square")

    # Step 2: Deep copy — the caller's grid must not be mutated.
    working_grid = copy.deepcopy(grid)

    # Step 3: Direction-specific processing.
    total_score = 0
    result_grid: list[list[int]] = []

    if direction == Direction.LEFT:
        for row in working_grid:
            merged_row, row_score = _slide_row_left(row)
            result_grid.append(merged_row)
            total_score += row_score

    elif direction == Direction.RIGHT:
        # Reverse each row, slide left, reverse back.
        for row in working_grid:
            reversed_row = row[::-1]
            merged_row, row_score = _slide_row_left(reversed_row)
            result_grid.append(merged_row[::-1])
            total_score += row_score

    elif direction == Direction.UP:
        # Transpose so columns become rows, slide each left, transpose back.
        transposed = _transpose(working_grid)
        processed: list[list[int]] = []
        for col_as_row in transposed:
            merged_row, row_score = _slide_row_left(col_as_row)
            processed.append(merged_row)
            total_score += row_score
        result_grid = _transpose(processed)

    elif direction == Direction.DOWN:
        # Transpose, reverse each row (so bottom→top becomes left→right),
        # slide left, reverse back, transpose back.
        transposed = _transpose(working_grid)
        processed = []
        for col_as_row in transposed:
            reversed_row = col_as_row[::-1]
            merged_row, row_score = _slide_row_left(reversed_row)
            processed.append(merged_row[::-1])
            total_score += row_score
        result_grid = _transpose(processed)

    return result_grid, total_score
