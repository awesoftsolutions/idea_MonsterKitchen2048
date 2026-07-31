"""Rules module for Monster Kitchen 2048.

Provides move legality checking and game-over detection for a 4x4
slide-and-merge board. This module is stateless -- the Rules class has
no instance state and all methods accept a board parameter.

Direction, SlideResult, and slide_merge are imported from src.core.board
as the single source of truth per the Tech Debt Reconciliation (ADR-013).

Public API:
    BoardProtocol: Minimal board interface with a ``grid`` property.
    Rules: Stateless class for move legality and game-over detection.

Dependencies: typing -- Python stdlib only.
Zero rendering or framework imports.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.core.board import Direction, SlideResult, slide_merge  # noqa: F401 — re-exported for typing


# ---------------------------------------------------------------------------
# BoardProtocol -- minimal interface Rules depends on
# ---------------------------------------------------------------------------


@runtime_checkable
class BoardProtocol(Protocol):
    """Minimal board interface for Rules.

    Uses structural typing so the production Board class does not need
    to explicitly inherit from this protocol.
    """

    @property
    def grid(self) -> list[list[int]]:
        """The 4x4 grid of tile values. 0 = empty."""
        ...


# ---------------------------------------------------------------------------
# Rules -- move legality and game-over detection
# ---------------------------------------------------------------------------


class Rules:
    """Stateless rules engine for Monster Kitchen 2048.

    Provides move legality checking and game-over detection.
    All methods accept a board parameter -- no instance state is stored.
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
        return result.new_grid != original

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
