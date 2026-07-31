"""Test suite for src/core/twist.py — Twist module and Board enhancement methods.

Purpose:
    Verifies correctness of the Rotten Food contamination mechanic (Twist),
    the TwistEffect result dataclass, and the Board enhancement methods
    (spawn_tile, get_empty_cells, is_empty, get_neighbors, get_rotten_overlay,
    add_rotten, remove_rotten, get_state, set_state). Covers all acceptance
    criteria from Sprint 2 Task 3 pseudocode.

System:
    Headless pytest suite. Each test constructs its own seeded RNG and Board
    instance for full isolation. Imports only from src.core.twist
    (Twist, TwistEffect) and src.core.board (Board, BoardState, GRID_SIZE).

Dependencies:
    pytest, random — third-party and stdlib. src.core.twist, src.core.board.

Used-by:
    CI pipeline (pytest), Sprint 2 Task 3 acceptance verification.

Public API:
    Helpers:
        _make_board_with_cells(rng, cells) -> Board
            Create a Board with specific cells set; cells is a list of
            (row, col, value) tuples.

    Test functions (22 standalone):
        Category 1 — Import and Construction:
            test_twist_import                          — import succeeds (AC-1)
            test_twist_constructor_defaults            — default spawn_interval, zero overlay

        Category 2 — Overlay Accessors:
            test_overlay_initial_state                 — all zeros (AC-7)
            test_get_overlay_returns_copy              — defensive copy
            test_is_rotten_and_get_countdown           — accessor correctness

        Category 3 — Countdown Decrement:
            test_countdown_decrements_each_move        — 3→2→1 lifecycle
            test_countdown_does_not_go_below_zero      — no negative values

        Category 4 — Contamination on Expiry:
            test_expired_countdown_contaminates_adjacent    — AC-2
            test_contamination_picks_one_adjacent           — one-of-many
            test_contamination_skips_when_no_valid_target   — AC-6

        Category 5 — Spawn on Interval:
            test_spawn_new_rotten_on_interval          — AC-3
            test_spawn_skips_when_board_full            — AC-5
            test_tunable_spawn_interval                — interval=2

        Category 6 — Rotten-Merges-Rotten Removal:
            test_rotten_merges_rotten_removes_both     — AC-4
            test_rotten_does_not_merge_with_healthy    — healthy adjacency
            test_rotten_merges_different_value_no_removal — value mismatch

        Category 7 — Board Enhancement Methods:
            test_board_spawn_tile                      — spawn at seeded position
            test_board_get_empty_cells                 — 3 known empties
            test_board_get_neighbors_corner            — 2 neighbors
            test_board_get_state_set_state_roundtrip   — snapshot/restore

        Category 8 — Integration / Edge Cases:
            test_multiple_expirations_in_same_move     — 3 independent expirations
            test_contamination_avoids_empty_cells      — only occupied targeted
"""
# CHANGELOG:
# - Sprint 2: Create 22 deterministic test cases for Twist module (TDD red phase)

from __future__ import annotations

import random

from src.core.board import Board, GRID_SIZE
from src.core.twist import Twist, TwistEffect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_board_with_cells(
    rng: random.Random, cells: list[tuple[int, int, int]]
) -> Board:
    """Create a Board with specific cells populated.

    Args:
        rng: Seeded RNG for deterministic construction.
        cells: List of (row, col, value) tuples to place on the board.

    Returns:
        A Board with cells set as specified.
    """
    board = Board(rng)
    for row, col, value in cells:
        board.set_cell(row, col, value)
    return board


# ---------------------------------------------------------------------------
# Category 1: Import and Construction
# ---------------------------------------------------------------------------


def test_twist_import() -> None:
    """AC-1: from src.core.twist import Twist, TwistEffect succeeds."""
    assert Twist is not None
    assert TwistEffect is not None


def test_twist_constructor_defaults() -> None:
    """Twist(rng) creates instance with default spawn_interval=4 and 4x4 zero overlay."""
    rng = random.Random(42)
    twist = Twist(rng)
    assert twist._spawn_interval == 4
    overlay = twist.get_overlay()
    assert len(overlay) == GRID_SIZE
    assert all(len(row) == GRID_SIZE for row in overlay)
    assert all(cell == 0 for row in overlay for cell in row)


# ---------------------------------------------------------------------------
# Category 2: Overlay Accessors
# ---------------------------------------------------------------------------


def test_overlay_initial_state() -> None:
    """AC-7: New Twist has all-zero overlay (4x4 grid of 0)."""
    rng = random.Random(42)
    twist = Twist(rng)
    overlay = twist.get_overlay()
    assert len(overlay) == GRID_SIZE
    assert all(len(row) == GRID_SIZE for row in overlay)
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            assert overlay[row][col] == 0, (
                f"Expected 0 at ({row}, {col}), got {overlay[row][col]}"
            )


def test_get_overlay_returns_copy() -> None:
    """Mutating the returned list does not affect Twist internal state."""
    rng = random.Random(42)
    twist = Twist(rng)
    overlay1 = twist.get_overlay()
    overlay1[0][0] = 99
    overlay2 = twist.get_overlay()
    assert overlay2[0][0] == 0, "External mutation must not affect Twist state"


def test_is_rotten_and_get_countdown() -> None:
    """After placing a rotten tile, is_rotten returns True and get_countdown returns value."""
    rng = random.Random(42)
    board = _make_board_with_cells(rng, [(1, 1, 2), (0, 1, 4)])
    board.add_rotten(1, 1, 3)
    rng2 = random.Random(42)
    twist = Twist(rng2)
    # Process a move so Twist syncs overlay from board
    twist.process_move(board, 0)
    # After sync, (1,1) should still be rotten (just decremented since no spawn)
    # Actually with countdown=3, after one decrement it's 2
    assert twist.is_rotten(1, 1) is True
    assert twist.get_countdown(1, 1) == 2
    # (0,1) is healthy
    assert twist.is_rotten(0, 1) is False
    assert twist.get_countdown(0, 1) == 0


# ---------------------------------------------------------------------------
# Category 3: Countdown Decrement
# ---------------------------------------------------------------------------


def test_countdown_decrements_each_move() -> None:
    """Place rotten tile with countdown=3; verify 3→2→1 countdown decrement cycle."""
    rng = random.Random(42)
    # Board with a tile at (2,2) and some healthy neighbors for contamination
    board = _make_board_with_cells(rng, [(2, 2, 2), (1, 2, 4), (3, 2, 8)])
    board.add_rotten(2, 2, 3)

    rng2 = random.Random(42)
    twist = Twist(rng2)

    # Move 1: countdown 3 → 2
    twist.process_move(board, 1)
    assert twist.get_countdown(2, 2) == 2

    # Move 2: countdown 2 → 1
    twist.process_move(board, 2)
    assert twist.get_countdown(2, 2) == 1

    # Move 3: countdown 1 → 0 (expired, contaminate neighbor)
    twist.process_move(board, 3)
    assert twist.get_countdown(2, 2) == 0
    assert twist.is_rotten(2, 2) is False


def test_countdown_does_not_go_below_zero() -> None:
    """After countdown reaches 0 (expired), next process_move produces no negative values."""
    rng = random.Random(42)
    board = _make_board_with_cells(rng, [(2, 2, 2)])
    board.add_rotten(2, 2, 1)

    rng2 = random.Random(42)
    twist = Twist(rng2)

    # Move 1: countdown 1 → 0 (expires, no valid neighbor to contaminate)
    twist.process_move(board, 1)
    assert twist.get_countdown(2, 2) == 0

    # Move 2: already expired, verify no negative
    twist.process_move(board, 2)
    assert twist.get_countdown(2, 2) == 0, "Countdown must not go below zero"


# ---------------------------------------------------------------------------
# Category 4: Contamination on Expiry
# ---------------------------------------------------------------------------


def test_expired_countdown_contaminates_adjacent() -> None:
    """AC-2: Rotten tile at countdown 1 contaminates one adjacent cell."""
    rng = random.Random(42)
    # (1,1)=rotten countdown=1, (1,2)=healthy tile
    board = _make_board_with_cells(rng, [(1, 1, 2), (1, 2, 4)])
    board.add_rotten(1, 1, 1)

    rng2 = random.Random(42)
    twist = Twist(rng2)
    effect = twist.process_move(board, 2)

    # (1,1) expired → contaminates (1,2) (the only healthy occupied neighbor)
    assert (1, 2) in effect.contaminated, (
        f"Expected (1,2) contaminated, got {effect.contaminated}"
    )
    assert twist.is_rotten(1, 2) is True
    assert twist.get_countdown(1, 2) == 3


def test_contamination_picks_one_adjacent() -> None:
    """When multiple healthy neighbors exist, exactly ONE is contaminated."""
    rng = random.Random(42)
    # (1,1) with countdown=1; all 4 neighbors have healthy tiles
    board = _make_board_with_cells(
        rng,
        [
            (1, 1, 2),  # rotten target
            (0, 1, 4),  # neighbor up
            (2, 1, 4),  # neighbor down
            (1, 0, 4),  # neighbor left
            (1, 2, 4),  # neighbor right
        ],
    )
    board.add_rotten(1, 1, 1)

    rng2 = random.Random(42)
    twist = Twist(rng2)
    effect = twist.process_move(board, 2)

    # Exactly one neighbor contaminated
    assert len(effect.contaminated) == 1, (
        f"Expected 1 contaminated, got {len(effect.contaminated)}: {effect.contaminated}"
    )
    contaminated_pos = effect.contaminated[0]
    assert contaminated_pos in [(0, 1), (2, 1), (1, 0), (1, 2)]


def test_contamination_skips_when_no_valid_target() -> None:
    """AC-6: Expired rotten with no adjacent healthy occupied cell → skip contamination."""
    rng = random.Random(42)
    # (0,0) with countdown=1; neighbors (0,1) and (1,0) are both empty (value=0)
    board = _make_board_with_cells(rng, [(0, 0, 2)])
    board.add_rotten(0, 0, 1)

    rng2 = random.Random(42)
    twist = Twist(rng2)
    effect = twist.process_move(board, 2)

    # No valid contamination target (corners have only 2 neighbors, both empty)
    assert effect.contaminated == [], (
        f"Expected no contamination, got {effect.contaminated}"
    )


# ---------------------------------------------------------------------------
# Category 5: Spawn on Interval
# ---------------------------------------------------------------------------


def test_spawn_new_rotten_on_interval() -> None:
    """AC-3: spawn_interval=4 triggers spawn at move 4."""
    rng = random.Random(42)
    board = _make_board_with_cells(
        rng,
        [
            (0, 0, 2),
            (0, 1, 4),
            (0, 2, 8),
            (0, 3, 16),
            (1, 0, 2),
            (1, 1, 4),
            (1, 2, 8),
            (1, 3, 16),
        ],
    )

    rng2 = random.Random(42)
    twist = Twist(rng2, spawn_interval=4)

    # Moves 1-3: no spawn
    for move_count in [1, 2, 3]:
        effect = twist.process_move(board, move_count)
        assert effect.rotten_spawned is False, f"Expected no spawn at move {move_count}"

    # Move 4: spawn triggered
    effect = twist.process_move(board, 4)
    assert effect.rotten_spawned is True, "Expected spawn at move 4"

    # Verify at least one cell has overlay=3 (freshly spawned)
    overlay = twist.get_overlay()
    rotten_count = sum(
        1 for r in range(GRID_SIZE) for c in range(GRID_SIZE) if overlay[r][c] > 0
    )
    assert rotten_count >= 1, "Expected at least 1 rotten cell after spawn"


def test_spawn_skips_when_board_full() -> None:
    """AC-5: Full board → spawn gracefully skipped, no exception."""
    rng = random.Random(42)
    # Fill all 16 cells
    cells = []
    counter = 1
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            cells.append((row, col, counter))
            counter += 1
    board = _make_board_with_cells(rng, cells)

    rng2 = random.Random(42)
    twist = Twist(rng2, spawn_interval=4)

    # Process moves 1-5, verifying no exception on full board at move 4
    for move_count in range(1, 6):
        twist.process_move(board, move_count)
    # The spawn at move 4 should have been skipped
    # Final check: no exception was raised (test passes if we reach here)


def test_tunable_spawn_interval() -> None:
    """spawn_interval=2 → spawn at move 2 and move 4."""
    rng = random.Random(42)
    board = _make_board_with_cells(
        rng,
        [
            (0, 0, 2),
            (0, 1, 4),
            (0, 2, 8),
            (0, 3, 16),
            (1, 0, 2),
            (1, 1, 4),
            (1, 2, 8),
            (1, 3, 16),
        ],
    )

    rng2 = random.Random(42)
    twist = Twist(rng2, spawn_interval=2)

    # Move 1: no spawn (1 % 2 != 0)
    effect = twist.process_move(board, 1)
    assert effect.rotten_spawned is False

    # Move 2: spawn (2 % 2 == 0)
    effect = twist.process_move(board, 2)
    assert effect.rotten_spawned is True, "Expected spawn at move 2"

    # Move 3: no spawn
    effect = twist.process_move(board, 3)
    assert effect.rotten_spawned is False

    # Move 4: spawn again
    effect = twist.process_move(board, 4)
    assert effect.rotten_spawned is True, "Expected spawn at move 4"


# ---------------------------------------------------------------------------
# Category 6: Rotten-Merges-Rotten Removal
# ---------------------------------------------------------------------------


def test_rotten_merges_rotten_removes_both() -> None:
    """AC-4: Two adjacent same-value rotten tiles → both removed."""
    rng = random.Random(42)
    # Two adjacent rotten tiles with same value 4
    board = _make_board_with_cells(rng, [(0, 0, 4), (0, 1, 4), (1, 0, 2)])
    board.add_rotten(0, 0, 3)
    board.add_rotten(0, 1, 3)

    rng2 = random.Random(42)
    twist = Twist(rng2)
    effect = twist.process_move(board, 1)

    # Both should be removed
    assert (0, 0) in effect.removed, f"Expected (0,0) in removed, got {effect.removed}"
    assert (0, 1) in effect.removed, f"Expected (0,1) in removed, got {effect.removed}"
    # Overlays should be cleared (countdown decremented then removed → 0)
    assert twist.is_rotten(0, 0) is False
    assert twist.is_rotten(0, 1) is False


def test_rotten_does_not_merge_with_healthy() -> None:
    """Rotten tile adjacent to same-value healthy tile → no removal."""
    rng = random.Random(42)
    # (0,0) rotten value=4, (0,1) healthy value=4
    board = _make_board_with_cells(rng, [(0, 0, 4), (0, 1, 4), (1, 0, 2)])
    board.add_rotten(0, 0, 3)

    rng2 = random.Random(42)
    twist = Twist(rng2)
    effect = twist.process_move(board, 1)

    # No removal (neighbor is healthy, not rotten)
    assert effect.removed == [], f"Expected no removal, got {effect.removed}"
    # (0,0) still rotten (countdown decremented from 3 to 2)
    assert twist.is_rotten(0, 0) is True
    assert twist.get_countdown(0, 0) == 2


def test_rotten_merges_different_value_no_removal() -> None:
    """Two adjacent rotten tiles with different values → no removal."""
    rng = random.Random(42)
    # (0,0) value=2, (0,1) value=4, both rotten
    board = _make_board_with_cells(rng, [(0, 0, 2), (0, 1, 4), (1, 0, 8)])
    board.add_rotten(0, 0, 3)
    board.add_rotten(0, 1, 3)

    rng2 = random.Random(42)
    twist = Twist(rng2)
    effect = twist.process_move(board, 1)

    # Values differ (2 != 4), so no removal
    assert effect.removed == [], f"Expected no removal, got {effect.removed}"
    # Both still rotten (countdowns decremented)
    assert twist.is_rotten(0, 0) is True
    assert twist.is_rotten(0, 1) is True
    assert twist.get_countdown(0, 0) == 2
    assert twist.get_countdown(0, 1) == 2


# ---------------------------------------------------------------------------
# Category 7: Board Enhancement Methods
# ---------------------------------------------------------------------------


def test_board_spawn_tile() -> None:
    """Board.spawn_tile() places a tile at a seeded random empty cell."""
    rng = random.Random(42)
    board = Board(rng)
    # Seed RNG a few times to position the sequence
    rng = random.Random(42)
    board = Board(rng)

    # Get one spawn: board is empty, spawn_tile should pick from 16 empty cells
    row, col = board.spawn_tile()
    assert 0 <= row < GRID_SIZE
    assert 0 <= col < GRID_SIZE
    value = board.get_cell(row, col)
    assert value in (2, 4), f"Expected tile value 2 or 4, got {value}"


def test_board_get_empty_cells() -> None:
    """Board with 3 known positions filled → get_empty_cells returns exactly 13."""
    rng = random.Random(42)
    board = _make_board_with_cells(rng, [(0, 0, 2), (1, 1, 4), (2, 3, 8)])
    empty = board.get_empty_cells()
    assert len(empty) == 13, f"Expected 13 empty cells, got {len(empty)}"
    assert (0, 0) not in empty
    assert (1, 1) not in empty
    assert (2, 3) not in empty
    assert (0, 1) in empty
    assert (3, 3) in empty


def test_board_get_neighbors_corner() -> None:
    """get_neighbors(0, 0) returns exactly [(0,1), (1,0)]."""
    rng = random.Random(42)
    board = Board(rng)
    neighbors = board.get_neighbors(0, 0)
    assert sorted(neighbors) == sorted([(0, 1), (1, 0)]), (
        f"Expected [(0,1), (1,0)], got {neighbors}"
    )
    assert len(neighbors) == 2


def test_board_get_state_set_state_roundtrip() -> None:
    """Set cells + rotten markers, get_state(), modify board, set_state() restores."""
    rng = random.Random(42)
    board = Board(rng)
    board.set_cell(0, 0, 2)
    board.set_cell(1, 1, 4)
    board.set_cell(2, 2, 8)
    board.add_rotten(0, 0, 3)
    board.add_rotten(1, 1, 2)
    board._score = 100
    board._moves = 5

    state = board.get_state()
    assert state.grid[0][0] == 2
    assert state.grid[1][1] == 4
    assert state.rotten_overlay is not None
    assert state.rotten_overlay[0][0] == 3
    assert state.score == 100
    assert state.moves == 5

    # Modify board
    board.set_cell(0, 0, 99)
    board.set_cell(3, 3, 16)

    # Restore
    board.set_state(state)
    assert board.get_cell(0, 0) == 2
    assert board.get_cell(1, 1) == 4
    assert board.get_cell(3, 3) == 0
    overlay = board.get_rotten_overlay()
    assert overlay[0][0] == 3
    assert overlay[1][1] == 2


# ---------------------------------------------------------------------------
# Category 8: Integration / Edge Cases
# ---------------------------------------------------------------------------


def test_multiple_expirations_in_same_move() -> None:
    """3 rotten tiles at countdown=1 expire in same move → all 3 contaminate independently."""
    rng = random.Random(42)
    # Three isolated rotten tiles at countdown=1, each with at least 1 healthy neighbor
    board = _make_board_with_cells(
        rng,
        [
            (0, 0, 2),
            (0, 1, 4),  # neighbor of (0,0)
            (2, 2, 2),
            (2, 3, 4),  # neighbor of (2,2)
            (3, 0, 2),
            (3, 1, 4),  # neighbor of (3,0)
        ],
    )
    board.add_rotten(0, 0, 1)
    board.add_rotten(2, 2, 1)
    board.add_rotten(3, 0, 1)

    rng2 = random.Random(42)
    twist = Twist(rng2)
    effect = twist.process_move(board, 2)

    # All 3 expire independently → 3 contaminations
    assert len(effect.contaminated) == 3, (
        f"Expected 3 contaminated, got {len(effect.contaminated)}: {effect.contaminated}"
    )


def test_contamination_avoids_empty_cells() -> None:
    """Rotting tile at (1,1) countdown=1: only occupied neighbor contaminated, not empty."""
    rng = random.Random(42)
    # (1,1) rotten countdown=1
    # (0,1) healthy value=2 (valid target)
    # (1,0) empty (value=0, should NOT be targeted)
    # (2,1) empty (value=0, should NOT be targeted)
    # (1,2) empty (value=0, should NOT be targeted)
    board = _make_board_with_cells(rng, [(1, 1, 4), (0, 1, 2)])
    board.add_rotten(1, 1, 1)

    rng2 = random.Random(42)
    twist = Twist(rng2)
    effect = twist.process_move(board, 2)

    # Only (0,1) is a valid contamination target
    assert (1, 0) not in effect.contaminated
    assert (2, 1) not in effect.contaminated
    assert (1, 2) not in effect.contaminated
    # (0,1) should be the contaminated cell
    assert (0, 1) in effect.contaminated, (
        f"Expected (0,1) contaminated, got {effect.contaminated}"
    )
