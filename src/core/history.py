"""History module — bounded undo/redo stack for game state snapshots.

Stores (BoardState, int) snapshots with configurable depth limiting via
max_depth parameter. Provides push/pop semantics for undo functionality.

Public API:
    History.__init__(max_depth: int = 0) -> None
    History.push(state: tuple[BoardState, int]) -> None
    History.pop() -> Optional[tuple[BoardState, int]]
    History.can_undo() -> bool
"""
# CHANGELOG:
# - Sprint 1: Bounded undo/redo History stack with max_depth

from __future__ import annotations

import copy
from typing import Optional

from src.core.board import BoardState


class History:
    """Bounded undo/redo stack storing (BoardState, int) snapshots.

    Snapshots are stored oldest-first (index 0 = oldest, index -1 = newest).
    The depth limit is configurable via max_depth: 0 means unlimited, any
    positive value enforces a hard cap — oldest snapshots are discarded when
    the limit is exceeded.
    """

    def __init__(self, max_depth: int = 0) -> None:
        """Initialize History with an empty snapshot stack and depth limit.

        Args:
            max_depth: Maximum snapshots to retain. 0 means unlimited.

        Raises:
            ValueError: If max_depth is negative.
        """
        if max_depth < 0:
            raise ValueError(f"max_depth must be non-negative, got {max_depth}")
        self._max_depth = max_depth
        self._stack: list[tuple[BoardState, int]] = []

    def push(self, state: tuple[BoardState, int]) -> None:
        """Push a board state snapshot onto the stack.

        Validates the state parameter and enforces the depth limit by removing
        the oldest snapshot when the stack exceeds max_depth.

        Args:
            state: A (BoardState, int) tuple representing the board snapshot
                and game score.

        Raises:
            TypeError: If state is None, not a tuple, wrong length, or contains
                invalid element types.
        """
        if state is None:
            raise TypeError("state must be a tuple of (BoardState, int), got None")
        if not isinstance(state, tuple):
            raise TypeError(f"state must be a tuple, got {type(state).__name__}")
        if len(state) != 2:
            raise TypeError(f"state must be a 2-tuple, got {len(state)} elements")
        if not isinstance(state[0], BoardState):
            raise TypeError(f"state[0] must be a BoardState, got {type(state[0]).__name__}")
        if not isinstance(state[1], int):
            raise TypeError(f"state[1] must be an int, got {type(state[1]).__name__}")

        self._stack.append(state)

        # Enforce depth limit — remove oldest snapshot when exceeded
        if self._max_depth > 0 and len(self._stack) > self._max_depth:
            self._stack.pop(0)

    def pop(self) -> Optional[tuple[BoardState, int]]:
        """Pop and return the most recent snapshot from the stack.

        Returns a defensive deep copy to prevent aliasing between the history
        stack and the caller's mutable state.

        Returns:
            A (BoardState, int) tuple of the most recent snapshot, or None if
            the stack is empty.
        """
        if len(self._stack) == 0:
            return None

        board_state, score = self._stack.pop()
        copied_state = copy.deepcopy(board_state)
        return (copied_state, score)

    def can_undo(self) -> bool:
        """Check whether at least one snapshot exists on the stack.

        Returns:
            True if the stack has at least one snapshot, False otherwise.
        """
        return len(self._stack) > 0
