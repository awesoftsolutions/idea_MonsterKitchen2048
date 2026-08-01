"""Test suite for src/render/animation_manager.py — AnimationManager class.

Purpose:
    Verifies correctness of the AnimationManager class — a pure-logic,
    zero-pygame-dependency component that computes per-tile pixel offsets
    and merge scale-pulse values for tile-slide animation. Covers all
    acceptance criteria from Sprint 1 Task 2 pseudocode (AC-1 through AC-6).

System:
    Headless pytest suite. No pygame, no conftest — each test constructs
    its own AnimationManager instance for full isolation. Imports only from
    src.core.board (TileMove) and src.render.animation_manager (AnimationManager).

Dependencies:
    pytest — third-party. src.core.board, src.render.animation_manager — production code.

Used-by:
    CI pipeline (pytest), Sprint 1 Task 2 acceptance verification.

Public API:
    Helper:
        _make_move(src_row, src_col, dest_row, dest_col, value,
                   merged=False) -> TileMove
            Create a TileMove dataclass for test setup.

    Test functions (10 standalone):
        test_animation_starts()                — AC-1: is_animating() True after start.
        test_interpolation_at_start()          — AC-1, AC-6: full delta at t=0.
        test_interpolation_at_midpoint()       — AC-2: 50% offset at 50% duration.
        test_animation_completes()             — AC-3: is_animating() False after duration.
        test_snap_to_end()                     — AC-4: snap mid-animation stops it.
        test_merge_scale_pulse()               — AC-5: scale >1.0 during pulse window.
        test_no_animation_before_start()       — AC-6: offset (0,0) before any start.
        test_merge_scale_for_non_merged_tile() — Non-merged tile gets no pulse.
        test_rapid_successive_animations()     — New animation replaces old cleanly.
        test_empty_tile_moves_no_op()          — Empty list does not clear running state.
"""

from __future__ import annotations

import pytest

from src.core.board import TileMove
from src.render.animation_manager import AnimationManager


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_move(
    src_row: int,
    src_col: int,
    dest_row: int,
    dest_col: int,
    value: int,
    merged: bool = False,
) -> TileMove:
    """Create a TileMove dataclass for test setup.

    Args:
        src_row: Source row index (0-based).
        src_col: Source column index (0-based).
        dest_row: Destination row index (0-based).
        dest_col: Destination column index (0-based).
        value: Tile value (pre-merge value or sum for merged destination).
        merged: True if this tile is the destination of a merge.

    Returns:
        A TileMove instance with the specified fields.
    """
    return TileMove(
        source_row=src_row,
        source_col=src_col,
        dest_row=dest_row,
        dest_col=dest_col,
        value=value,
        merged=merged,
    )


# ---------------------------------------------------------------------------
# Animation State Tests
# ---------------------------------------------------------------------------


def test_animation_starts() -> None:
    """AC-1: is_animating() returns True immediately after start_animation."""
    manager = AnimationManager(duration_ms=250, cell_size=162)
    move = _make_move(src_row=0, src_col=3, dest_row=0, dest_col=1, value=2)
    manager.start_animation([move])
    assert manager.is_animating() is True


def test_interpolation_at_start() -> None:
    """AC-1, AC-6: Full delta offset at t=0 (no update called yet).

    Move from (0,3) to (0,1): delta_x = (3-1)*162 = 324, delta_y = 0.
    At progress=0, offset equals delta.
    """
    manager = AnimationManager(duration_ms=250, cell_size=162)
    move = _make_move(src_row=0, src_col=3, dest_row=0, dest_col=1, value=2)
    manager.start_animation([move])
    offset = manager.get_pixel_offset(0, 3)
    assert offset == pytest.approx((324.0, 0.0))


def test_interpolation_at_midpoint() -> None:
    """AC-2: 50% of duration → 50% of total pixel distance.

    Update 125ms of 250ms (50%). Offset for move (0,3)→(0,1):
    324 * 0.5 = 162.0 in x, 0.0 in y.
    """
    manager = AnimationManager(duration_ms=250, cell_size=162)
    move = _make_move(src_row=0, src_col=3, dest_row=0, dest_col=1, value=2)
    manager.start_animation([move])
    manager.update(0.125)  # 125ms, half of 250ms
    assert manager.is_animating() is True
    offset = manager.get_pixel_offset(0, 3)
    assert offset[0] == pytest.approx(162.0, abs=0.5)
    assert offset[1] == pytest.approx(0.0, abs=0.5)


def test_animation_completes() -> None:
    """AC-3: update with dt >= duration marks animation complete.

    After 300ms update (exceeds 250ms), animation ends.
    All offsets become (0.0, 0.0).
    """
    manager = AnimationManager(duration_ms=250, cell_size=162)
    move = _make_move(src_row=0, src_col=3, dest_row=0, dest_col=1, value=2)
    manager.start_animation([move])
    manager.update(0.3)  # 300ms > 250ms
    assert manager.is_animating() is False
    assert manager.get_pixel_offset(0, 3) == (0.0, 0.0)
    assert manager.get_pixel_offset(0, 1) == (0.0, 0.0)


def test_snap_to_end() -> None:
    """AC-4: snap_to_end() mid-animation immediately stops animation.

    No update() called — animation is interrupted at t=0.
    """
    manager = AnimationManager(duration_ms=250, cell_size=162)
    move = _make_move(src_row=0, src_col=3, dest_row=0, dest_col=1, value=2)
    manager.start_animation([move])
    manager.snap_to_end()
    assert manager.is_animating() is False
    assert manager.get_pixel_offset(0, 3) == (0.0, 0.0)


# ---------------------------------------------------------------------------
# Merge Pulse Tests
# ---------------------------------------------------------------------------


def test_merge_scale_pulse() -> None:
    """AC-5: Merged tile gets scale >1.0 during 200ms pulse window.

    Pulse decays linearly: peak 1.3 at elapsed=0, 1.15 at 100ms, 1.0 after 200ms.
    PULSE_AMPLITUDE=0.3, MERGE_PULSE_MS=200.
    """
    manager = AnimationManager(duration_ms=250, cell_size=162)
    move = _make_move(
        src_row=0, src_col=3, dest_row=0, dest_col=1, value=4, merged=True
    )
    manager.start_animation([move])

    # Immediately after start (elapsed=0): peak scale
    assert manager.get_merge_scale(0, 1) == pytest.approx(1.3)

    # After 100ms: scale = 1.0 + 0.3 * (1.0 - 0.5) = 1.15
    manager.update(0.1)
    assert manager.get_merge_scale(0, 1) == pytest.approx(1.15)

    # After 250ms total >= 200ms MERGE_PULSE_MS: pulse expired
    manager.update(0.15)
    assert manager.get_merge_scale(0, 1) == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Edge Case / Additional Coverage Tests
# ---------------------------------------------------------------------------


def test_no_animation_before_start() -> None:
    """AC-6: No animation active → get_pixel_offset returns (0.0, 0.0) everywhere.

    Fresh manager with no start_animation call.
    """
    manager = AnimationManager(duration_ms=250, cell_size=162)
    assert manager.get_pixel_offset(0, 0) == (0.0, 0.0)
    assert manager.get_pixel_offset(3, 3) == (0.0, 0.0)
    assert manager.get_pixel_offset(1, 2) == (0.0, 0.0)
    assert manager.is_animating() is False


def test_merge_scale_for_non_merged_tile() -> None:
    """Non-merged tile gets no pulse — get_merge_scale returns 1.0 exactly."""
    manager = AnimationManager(duration_ms=250, cell_size=162)
    move = _make_move(src_row=0, src_col=3, dest_row=0, dest_col=1, value=2)
    manager.start_animation([move])
    # Non-merged tile at destination returns 1.0
    assert manager.get_merge_scale(0, 1) == 1.0
    # Position not in any TileMove also returns 1.0
    assert manager.get_merge_scale(0, 0) == 1.0


def test_rapid_successive_animations() -> None:
    """Starting a new animation mid-flight replaces all state cleanly.

    Start move_a, advance 100ms, then start move_b. Old source (0,3) is gone;
    new source (1,2) starts at t=0 with full delta.
    """
    manager = AnimationManager(duration_ms=250, cell_size=162)
    move_a = _make_move(src_row=0, src_col=3, dest_row=0, dest_col=1, value=2)
    move_b = _make_move(src_row=1, src_col=2, dest_row=1, dest_col=0, value=4)
    manager.start_animation([move_a])
    manager.update(0.1)  # 100ms advanced
    manager.start_animation([move_b])
    assert manager.is_animating() is True
    # Old position no longer tracked
    assert manager.get_pixel_offset(0, 3) == (0.0, 0.0)
    # New move at progress=0: delta_x = (2-0)*162 = 324, delta_y = 0
    assert manager.get_pixel_offset(1, 2) == pytest.approx((324.0, 0.0))


def test_empty_tile_moves_no_op() -> None:
    """Calling start_animation with empty list does not clear running animation.

    Start a real animation, advance time, then start again with [].
    Previous animation state is preserved.
    """
    manager = AnimationManager(duration_ms=250, cell_size=162)
    move = _make_move(src_row=0, src_col=3, dest_row=0, dest_col=1, value=2)
    manager.start_animation([move])
    manager.update(0.1)  # 100ms, still animating
    assert manager.is_animating() is True
    manager.start_animation([])  # empty list — should be a no-op
    assert manager.is_animating() is True
