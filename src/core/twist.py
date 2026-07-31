"""Twist module — Rotten Food contamination mechanic for Monster Kitchen 2048.

Purpose:
    Implements the "Rotten Food" twist mechanic that forces defensive gameplay
    on top of the standard 2048 slide-and-merge. Rotten tiles spawn periodically,
    count down, and contaminate adjacent healthy tiles when they expire. Adjacent
    same-value rotten tiles remove each other.

System:
    Twist owns the contamination LOGIC. Board owns the overlay STORAGE (ADR-007).
    Twist reads Board state through public methods (get_empty_cells,
    get_neighbors, get_rotten_overlay) and writes through add_rotten/
    remove_rotten. All randomness is injectable via random.Random (ADR-010).

Dependencies:
    copy, random, dataclasses — stdlib only. src.core.board — Board, GRID_SIZE.

Used-by:
    src/core/game.py (move orchestration) — Sprint 2 Task 4,
    src/core/history.py (undo integration) — Sprint 2 Task 5.

Public API:
    Constants:
        ROTTEN_COUNTDOWN: int = 3 — fresh rotten tiles start with this countdown.

    TwistEffect (dataclass):
        Result of process_move().
        Fields:
            rotten_spawned: bool   — True if a new rotten tile was placed.
            contaminated: list[tuple[int, int]] — Positions contaminated by expiry.
            removed: list[tuple[int, int]] — Positions cleared by rotten-merges-rotten.

    Twist (class):
        Rotten Food contamination manager.
        Constructor:
            __init__(rng: random.Random, spawn_interval: int = 4)
        Methods:
            process_move(board, move_count) -> TwistEffect
            get_overlay() -> list[list[int]]
            is_rotten(row, col) -> bool
            get_countdown(row, col) -> int
"""
# CHANGELOG:
# - Sprint 2: Create Twist module with full contamination algorithm

from __future__ import annotations

import random
from dataclasses import dataclass, field

from src.core.board import Board, GRID_SIZE


# ROTTEN_COUNTDOWN defines the starting value for freshly spawned rotten tiles.
ROTTEN_COUNTDOWN: int = 3


@dataclass
class TwistEffect:
    """Result of Twist.process_move() — describes what the twist system did.

    Attributes:
        rotten_spawned: True if a new rotten tile was placed this move.
        contaminated: Positions of cells that became rotten from countdown expiry.
        removed: Positions of rotten tiles removed by rotten-merges-rotten.
    """

    rotten_spawned: bool = False
    contaminated: list[tuple[int, int]] = field(default_factory=list)
    removed: list[tuple[int, int]] = field(default_factory=list)


class Twist:
    """Rotten Food contamination mechanic — the Monster Kitchen twist.

    Manages the lifecycle of rotten tiles: spawn on interval, decrement
    countdowns, contaminate adjacent cells on expiry, and remove adjacent
    same-value rotten pairs. Twists are stateless with respect to Board —
    the Board instance is passed to process_move each time.
    """

    def __init__(self, rng: random.Random, spawn_interval: int = 4) -> None:
        """Initialize the Twist with injected RNG and configurable spawn interval.

        Args:
            rng: Injected random.Random for deterministic testing (ADR-010).
            spawn_interval: Moves between rotten spawns (default 4).
        """
        self._rng: random.Random = rng
        self._spawn_interval: int = spawn_interval
        self._overlay: list[list[int]] = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

    def process_move(self, board: Board, move_count: int) -> TwistEffect:
        """Run the contamination algorithm for one move.

         Five-phase algorithm:
             Phase 1: Decrement all active countdowns.
             Phase 2: Contaminate one random adjacent healthy cell per expired tile.
             Phase 3: Spawn new rotten tile on interval (if empty cells exist).
             Phase 4: Remove adjacent same-value rotten pairs.
             Phase 5: Write working overlay back to Board.

        Args:
            board: The Board instance to operate on.
            move_count: Current move number (1-based).

        Returns:
            A TwistEffect describing what the twist system did.
        """
        # Read current overlay from board and work on a deep copy
        current_overlay = board.get_rotten_overlay()
        working_overlay = [row[:] for row in current_overlay]
        effect = TwistEffect()

        # --- Phase 1: Decrement all countdowns ---
        expired_cells: list[tuple[int, int]] = []
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if working_overlay[row][col] > 0:
                    working_overlay[row][col] -= 1
                    if working_overlay[row][col] == 0:
                        expired_cells.append((row, col))

        # --- Phase 2: Contaminate from expired cells ---
        for expired_row, expired_col in expired_cells:
            neighbors = board.get_neighbors(expired_row, expired_col)
            healthy = [
                (nr, nc)
                for nr, nc in neighbors
                if not board.is_empty(nr, nc) and working_overlay[nr][nc] == 0
            ]
            if healthy:
                cr, cc = self._rng.choice(healthy)
                working_overlay[cr][cc] = ROTTEN_COUNTDOWN
                effect.contaminated.append((cr, cc))

        # --- Phase 3: Spawn new rotten on interval ---
        if move_count > 0 and move_count % self._spawn_interval == 0:
            empty = board.get_empty_cells()
            if empty:
                sr, sc = self._rng.choice(empty)
                # Place a tile value at the empty cell so add_rotten validation passes
                board.set_cell(sr, sc, 2)
                working_overlay[sr][sc] = ROTTEN_COUNTDOWN
                effect.rotten_spawned = True

        # --- Phase 4: Rotten-merges-rotten removal ---
        removed_set: set[tuple[int, int]] = set()
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if working_overlay[row][col] == 0:
                    continue
                if (row, col) in removed_set:
                    continue
                this_val = board.get_cell(row, col)
                for nr, nc in board.get_neighbors(row, col):
                    if (nr, nc) in removed_set:
                        continue
                    if (
                        working_overlay[nr][nc] > 0
                        and board.get_cell(nr, nc) == this_val
                    ):
                        # ADR-012: adjacent same-value rotten → remove BOTH
                        working_overlay[row][col] = 0
                        working_overlay[nr][nc] = 0
                        removed_set.update([(row, col), (nr, nc)])
                        effect.removed.extend([(row, col), (nr, nc)])
                        break

        # --- Phase 5: Write working overlay back to Board ---
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                new_val = working_overlay[row][col]
                old_val = current_overlay[row][col]
                if old_val > 0 and new_val == 0:
                    board.remove_rotten(row, col)
                elif old_val == 0 and new_val > 0:
                    board.add_rotten(row, col, new_val)
                elif old_val > 0 and new_val > 0 and old_val != new_val:
                    # Countdown was decremented — update via remove + add
                    board.remove_rotten(row, col)
                    board.add_rotten(row, col, new_val)

        # Update Twist's cached overlay copy
        self._overlay = [row[:] for row in working_overlay]

        return effect

    def get_overlay(self) -> list[list[int]]:
        """Return a 4x4 list where 0=healthy and 1-3=countdown remaining.

        Returns:
            A defensive copy of the current overlay.
        """
        return [row[:] for row in self._overlay]

    def is_rotten(self, row: int, col: int) -> bool:
        """Check whether a cell has a non-zero countdown.

        Args:
            row: Row index (0-based).
            col: Column index (0-based).

        Returns:
            True if the cell has a non-zero countdown in the overlay.

        Raises:
            IndexError: If row or col is out of bounds.
        """
        if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
            raise IndexError(
                f"Cell ({row}, {col}) is out of bounds for {GRID_SIZE}x{GRID_SIZE} grid"
            )
        return self._overlay[row][col] > 0

    def get_countdown(self, row: int, col: int) -> int:
        """Return the countdown value for a cell.

        Args:
            row: Row index (0-based).
            col: Column index (0-based).

        Returns:
            The countdown value (0 = not rotten, 1-3 = rotten).

        Raises:
            IndexError: If row or col is out of bounds.
        """
        if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
            raise IndexError(
                f"Cell ({row}, {col}) is out of bounds for {GRID_SIZE}x{GRID_SIZE} grid"
            )
        return self._overlay[row][col]
