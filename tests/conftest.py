"""Shared fixtures for Monster Kitchen test suite."""
# CHANGELOG:
# - Sprint 1: Add 4 shared test fixtures
# - Sprint 2: Add seeded_rng and empty_board fixtures for twist tests

from __future__ import annotations

import random

import pytest

from src.core.board import Board


@pytest.fixture()
def empty_4x4_grid() -> list[list[int]]:
    """A 4x4 grid of all zeros."""
    return [[0, 0, 0, 0] for _ in range(4)]


@pytest.fixture()
def board_with_two_tiles() -> Board:
    """A 4x4 Board with tiles at (0,0)=2 and (1,1)=4."""
    board = Board()
    board.set_cell(0, 0, 2)
    board.set_cell(1, 1, 4)
    return board


@pytest.fixture()
def board_near_full() -> Board:
    """A 4x4 Board with 15 of 16 cells filled — one empty at (3,3)."""
    board = Board()
    counter = 1
    for row in range(4):
        for col in range(4):
            if row == 3 and col == 3:
                continue
            board.set_cell(row, col, counter)
            counter += 1
    return board


@pytest.fixture()
def board_with_tiles_at_edges() -> Board:
    """A 4x4 Board with tiles only at the four corners."""
    board = Board()
    board.set_cell(0, 0, 2)
    board.set_cell(0, 3, 4)
    board.set_cell(3, 0, 8)
    board.set_cell(3, 3, 16)
    return board


@pytest.fixture()
def seeded_rng() -> random.Random:
    """A Random instance seeded with 42 for deterministic tests."""
    return random.Random(42)


@pytest.fixture()
def empty_board() -> Board:
    """An empty 4x4 Board with seeded RNG for deterministic tests."""
    return Board(random.Random(42))
