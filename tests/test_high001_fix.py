"""Regression tests for HIGH-001 — verifies spike's SlideResult
attribute access works correctly (no TypeError from tuple unpacking).
"""

from __future__ import annotations

from spikes.slide_merge import Direction, slide_merge
from src.core.board import Board
from src.core.rules import BoardProtocol


def test_high001_attribute_access_grid() -> None:
    """HIGH-001 regression: slide_merge returns SlideResult with .grid attribute.

    Verifies AC-1 — the spike's slide_merge returns a SlideResult dataclass,
    not a tuple. Accessing .grid must not raise TypeError.
    """
    grid = [[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    result = slide_merge(grid, Direction.LEFT)
    assert result.grid is not None
    assert isinstance(result.grid, list)
    assert len(result.grid) == 4
    assert result.grid[0] == [4, 0, 0, 0]


def test_high001_attribute_access_score() -> None:
    """HIGH-001 regression: slide_merge returns SlideResult with .score attribute.

    Verifies AC-1 — accessing .score must not raise TypeError.
    """
    grid = [[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    result = slide_merge(grid, Direction.LEFT)
    assert result.score == 4


def test_high001_all_directions_attribute_access() -> None:
    """HIGH-001 regression: attribute access works for all four directions."""
    grid = [[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    for direction in [Direction.LEFT, Direction.RIGHT, Direction.UP, Direction.DOWN]:
        result = slide_merge(grid, direction)
        assert result.grid is not None
        assert result.score is not None
        assert isinstance(result.score, int)


def test_board_grid_property_exists() -> None:
    """Board class must have a grid property for BoardProtocol compliance.

    Verifies AC-5 — Board instances must expose a grid attribute.
    """
    board = Board()
    assert hasattr(board, "grid"), "Board must have a 'grid' attribute"


def test_board_grid_satisfies_protocol() -> None:
    """Board must satisfy BoardProtocol structural typing.

    Verifies AC-5 — isinstance check with runtime_checkable protocol.
    """
    board = Board()
    assert isinstance(board, BoardProtocol), (
        "Board must satisfy BoardProtocol (requires @property grid)"
    )
