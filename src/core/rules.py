"""Rules module for Monster Kitchen 2048.

Provides move legality checking and game-over detection for a 4x4
slide-and-merge board. This module is stateless -- the Rules class has
no instance state and all methods accept a board parameter.

Direction, SlideResult, and slide_merge are imported from src.core.board
as the single source of truth per the Tech Debt Reconciliation (ADR-013).

Public API:
    BoardProtocol: Minimal board interface with a ``grid`` property
        and an optional ``get_rotten_overlay()`` method for
        twist-aware game-over detection.
    Rules: Stateless class for move legality and game-over detection.

Dependencies: typing -- Python stdlib only.
Zero rendering or framework imports.
"""
# CHANGELOG:
# - Sprint 1: Fix has_rotten logic in is_game_over — game continues when rotten tiles present

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.core.board import Direction, GRID_SIZE, SlideResult, slide_merge  # noqa: F401 — re-exported for typing


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

    def get_rotten_overlay(self) -> list[list[int]]:
        """Return a 4x4 grid where 0=healthy, 1-3=countdown remaining.

        This is an OPTIONAL protocol method -- Rules checks for its
        existence via getattr duck-typing, not Protocol conformance.
        Boards that implement this method get twist-aware game-over
        detection; boards that lack it fall back to the ``has_rotten``
        boolean parameter.
        """
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

    def _has_rescueable_rotten_pair(self, board: BoardProtocol) -> bool:
        """Check if any adjacent rotten tiles share the same value.

        Scans the overlay grid for adjacent cells where both are rotten
        (overlay > 0) AND share the same tile value on the board grid.
        Adjacent means sharing an edge (up/down/left/right), not diagonal.
        Only checks right and down neighbors to avoid counting pairs twice.

        Args:
            board: An object satisfying BoardProtocol (must have grid and
                get_rotten_overlay).

        Returns:
            True if at least one rescueable adjacent pair exists.
        """
        grid = board.grid
        overlay = board.get_rotten_overlay()

        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if overlay[row][col] == 0:
                    continue

                # Check right neighbor
                if col + 1 < GRID_SIZE:
                    if overlay[row][col + 1] > 0 and grid[row][col] == grid[row][col + 1]:
                        return True

                # Check down neighbor
                if row + 1 < GRID_SIZE:
                    if overlay[row + 1][col] > 0 and grid[row][col] == grid[row + 1][col]:
                        return True

        return False

    def is_game_over(self, board: BoardProtocol, has_rotten: bool = False) -> bool:
        """Determine whether the game is over for the given board.

        The game is over when:
        1. There are no empty cells (all tiles non-zero), AND
        2. There are no active rotten tiles in the overlay, AND
        3. No legal move exists in any direction.

        When the board provides ``get_rotten_overlay()``, Phase 2 inspects
        the actual overlay grid for non-zero values (any countdown > 0).
        If rescueable adjacent same-value rotten pairs exist, the game
        continues because rotten-merges-rotten could clear tiles.  If no
        rescueable pair exists, the game falls through to the legal-move
        check.  When the board does NOT provide ``get_rotten_overlay()``,
        the ``has_rotten`` boolean parameter is used as a backward-
        compatible fallback (game continues if has_rotten is True).

        Invariant: if any direction is legal, returns False.

        Args:
            board: An object satisfying BoardProtocol.
            has_rotten: Backward-compatible fallback for boards without
                ``get_rotten_overlay()``.  Ignored when the board provides
                the overlay method (overlay inspection takes precedence).

        Returns:
            True if the game is over, False otherwise.
        """
        grid = board.grid

        # Phase 1: Check for empty cells.
        for row in grid:
            for value in row:
                if value == 0:
                    return False

        # Phase 2: Twist-awareness via overlay inspection.
        # Use getattr duck-typing to check if board supports overlay access.
        # This preserves backward compatibility with stubs that lack the method.
        actual_has_rotten = False

        overlay_method = getattr(board, "get_rotten_overlay", None)
        if overlay_method is not None:
            # Board supports overlay access -- inspect the actual grid.
            overlay = overlay_method()
            for row in overlay:
                for value in row:
                    if value > 0:
                        actual_has_rotten = True
                        break
                if actual_has_rotten:
                    break
        else:
            # Board does NOT support overlay -- fall back to the boolean parameter.
            actual_has_rotten = has_rotten

        # If rotten tiles exist, check whether rescue is possible.
        # When overlay is available, only continue game if a rescueable
        # adjacent same-value pair exists (rotten-merges-rotten can clear it).
        # Without overlay, fall back to has_rotten boolean (backward compat).
        if actual_has_rotten:
            if overlay_method is not None:
                if self._has_rescueable_rotten_pair(board):
                    return False  # Rescue possible — game continues
                # No rescueable pair — fall through to legal-move check
            else:
                return False  # has_rotten fallback — preserve existing behavior

        # Phase 3: Check all directions for legal moves.
        legal = self.get_legal_moves(board)
        if legal:
            return False

        return True