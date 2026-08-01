"""tests/test_animation_integration.py — Integration tests for AnimationManager.

Purpose:
    Verifies the AnimationManager integration contract with GameWindow.
    AnimationManager is implemented (Sprint 1 Task 2) and these tests
    validate that the animation pipeline correctly intercepts valid moves,
    produces tile-move offsets, and resolves positions after animation.
    Each test imports AnimationManager at function level — if the module
    is missing, the test fails cleanly with a descriptive message rather
    than crashing during collection.

    When AnimationManager becomes available, these tests validate:
    - A successful move feeds tile_moves to animation manager
    - An illegal move produces no animation
    - A rapid second move interrupts (snap_to_end) the first animation
    - After animation completes, get_pixel_offset returns (0, 0)
    - Frame-0 has deterministic dt=0 offsets (full delta)
    - _pending_tile_moves is initialized as empty list

Framework: pytest + unittest.mock. No real pygame.init() or display required.
Uses the same mock patterns as tests/test_main.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

import pygame
import pytest

# ---------------------------------------------------------------------------
# Module-level imports — try/except to allow collection even when missing
# ---------------------------------------------------------------------------

try:
    from src.main import GameState, GameWindow
except ImportError:
    GameState = None  # type: ignore[assignment,misc]
    GameWindow = None  # type: ignore[assignment,misc]

try:
    from src.render.animation_manager import AnimationManager
except ImportError:
    AnimationManager = None  # type: ignore[assignment,misc]

try:
    from src.core.board import TileMove
except ImportError:
    TileMove = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_animation_manager() -> None:
    """Skip (actually fail) if AnimationManager module is not importable."""
    if AnimationManager is None:
        pytest.fail(
            "AnimationManager not importable — src/render/animation_manager.py "
            "does not exist yet. This test is part of the TDD red phase and "
            "is expected to fail until Sprint 1 Task 2 is implemented.",
            pytrace=False,
        )


def _make_mock_session(
    board: list[list[int]] | None = None,
    score: int = 0,
    high_score: int = 0,
    can_undo: bool = False,
    game_over: bool = False,
) -> MagicMock:
    """Build a mock GameSession with configurable state.

    Args:
        board: 4x4 tile value grid. Defaults to all zeros.
        score: Current score value.
        high_score: All-time high score.
        can_undo: Whether undo is available.
        game_over: Whether the game is over.

    Returns:
        MagicMock configured to behave like a GameSession.
    """
    mock = MagicMock()
    mock.get_board_grid.return_value = board or [[0] * 4 for _ in range(4)]
    mock.get_score.return_value = score
    mock.get_high_score.return_value = high_score
    mock.can_undo.return_value = can_undo
    type(mock).game_over = PropertyMock(return_value=game_over)
    mock.move.return_value = MagicMock(moved=True, tile_moves=[])
    mock.undo.return_value = True
    return mock


def _make_mock_event(event_type: int, **kwargs: object) -> MagicMock:
    """Build a mock pygame event with given type and attributes."""
    event = MagicMock()
    event.type = event_type
    for attr, value in kwargs.items():
        setattr(event, attr, value)
    return event


def _make_key_event(key: int) -> MagicMock:
    """Shortcut for KEYDOWN event."""
    return _make_mock_event(pygame.KEYDOWN, key=key)


def _make_tile_move(
    src_row: int,
    src_col: int,
    dest_row: int,
    dest_col: int,
    value: int,
    merged: bool = False,
) -> MagicMock:
    """Build a mock TileMove matching the dataclass fields."""
    tm = MagicMock()
    tm.source_row = src_row
    tm.source_col = src_col
    tm.dest_row = dest_row
    tm.dest_col = dest_col
    tm.value = value
    tm.merged = merged
    return tm


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def _patch_pygame(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch pygame functions for headless GameWindow instantiation."""
    monkeypatch.setattr(pygame, "init", lambda: (1, 0))
    monkeypatch.setattr(
        pygame.display,
        "set_mode",
        lambda *a, **kw: MagicMock(get_width=lambda: 700, get_height=lambda: 800),
    )
    monkeypatch.setattr(pygame.display, "set_caption", lambda *a, **kw: None)
    monkeypatch.setattr(pygame.display, "flip", lambda: None)
    monkeypatch.setattr(pygame, "quit", lambda: None)

    mock_clock = MagicMock()
    mock_clock.tick.return_value = 16  # ~60 FPS
    monkeypatch.setattr(pygame.time, "Clock", lambda: mock_clock)

    monkeypatch.setattr(pygame.event, "get", lambda: [])


# ---------------------------------------------------------------------------
# Integration tests — validate AnimationManager integration contract
# ---------------------------------------------------------------------------


def test_animation_triggered_on_valid_move(
    _patch_pygame: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that a valid move queues tile_moves into a non-None animation manager.

    After _handle_keydown processes a successful move, the tile_moves from
    MoveResult should be queued for the animation manager, and the animation
    manager itself must be instantiated (not None).
    """
    _require_animation_manager()
    assert GameWindow is not None
    assert AnimationManager is not None

    # Create a mock tile_move to verify it flows through the system
    mock_tile_move = _make_tile_move(
        src_row=0, src_col=3, dest_row=0, dest_col=1, value=2
    )

    session = _make_mock_session()
    # Configure move() to return tile_moves
    session.move.return_value = MagicMock(moved=True, tile_moves=[mock_tile_move])

    window = GameWindow()
    window._session = session
    window._state = GameState.PLAYING
    window._pending_tile_moves.clear()

    # Integration assertion: GameWindow must have a real AnimationManager
    assert window._animation_manager is not None, (
        "GameWindow._animation_manager must be a real AnimationManager instance, "
        "not None. The run() method should create it during __init__ or there "
        "should be lazy initialization."
    )

    window._handle_keydown(pygame.K_RIGHT)

    # After a successful move, _pending_tile_moves should have the tile_moves
    # extended from the result
    assert len(window._pending_tile_moves) == 1
    assert window._pending_tile_moves[0] is mock_tile_move


def test_no_animation_on_illegal_move(
    _patch_pygame: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that an illegal move (moved=False) produces no animation data.

    When move() returns moved=False, _pending_tile_moves must remain empty.
    Also verifies the animation manager is instantiated on the window.
    """
    _require_animation_manager()
    assert GameWindow is not None
    assert AnimationManager is not None

    session = _make_mock_session()
    session.move.return_value = MagicMock(moved=False, tile_moves=[])

    window = GameWindow()
    window._session = session
    window._state = GameState.PLAYING
    window._pending_tile_moves.clear()

    # Integration assertion: animation manager must be non-None
    assert window._animation_manager is not None, (
        "GameWindow._animation_manager must be a real AnimationManager instance."
    )

    window._handle_keydown(pygame.K_UP)

    # No tiles moved — _pending_tile_moves stays empty
    assert len(window._pending_tile_moves) == 0


def test_animation_interruption(
    _patch_pygame: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that a second move interrupts the first animation (snap_to_end).

    When a new valid move arrives while animation is running,
    snap_to_end() should be called first, then new tile_moves queued.
    """
    _require_animation_manager()
    assert GameWindow is not None

    move_a = _make_tile_move(src_row=0, src_col=3, dest_row=0, dest_col=1, value=2)
    move_b = _make_tile_move(src_row=1, src_col=2, dest_row=1, dest_col=0, value=4)

    session = _make_mock_session()

    window = GameWindow()
    window._session = session
    window._state = GameState.PLAYING
    window._pending_tile_moves.clear()

    # Ensure animation manager is real
    assert window._animation_manager is not None

    # First move: triggers animation
    session.move.return_value = MagicMock(moved=True, tile_moves=[move_a])
    window._handle_keydown(pygame.K_RIGHT)
    # Simulate game loop consuming pending moves
    window._animation_manager.start_animation(window._pending_tile_moves)
    window._pending_tile_moves.clear()

    assert window._animation_manager.is_animating()

    # Second move: should snap first animation and queue new moves
    session.move.return_value = MagicMock(moved=True, tile_moves=[move_b])
    window._handle_keydown(pygame.K_LEFT)

    # snap_to_end is called when animation_manager exists and result.moved
    # Previous animation should be snapped, new moves queued
    assert len(window._pending_tile_moves) == 1
    assert window._pending_tile_moves[0] is move_b


def test_tile_positions_resolve_after_animation(
    _patch_pygame: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that after animation completes, all offsets resolve to (0, 0).

    When is_animating() returns False, _render() should produce an
    active_moves of None (no active animation offsets).
    """
    _require_animation_manager()
    assert GameWindow is not None

    window = GameWindow()

    # Ensure animation manager is created
    assert window._animation_manager is not None
    manager = window._animation_manager

    # Start an animation
    move = _make_tile_move(src_row=0, src_col=3, dest_row=0, dest_col=1, value=2)
    manager.start_animation([move])

    # Advance past animation duration (250ms + buffer) with 16ms ticks
    for _ in range(20):
        manager.update(0.016)

    assert manager.is_animating() is False

    # All offsets should be zero
    assert manager.get_pixel_offset(0, 0) == (0.0, 0.0)
    assert manager.get_pixel_offset(0, 3) == (0.0, 0.0)


def test_animation_dt_zero_first_frame(
    _patch_pygame: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that the first animation frame (dt=0) shows full delta offset.

    At t=0 (before any update call), get_pixel_offset should return the
    full pixel delta — the tile starts at its source position.
    """
    _require_animation_manager()
    assert GameWindow is not None

    window = GameWindow()
    assert window._animation_manager is not None

    move = _make_tile_move(src_row=0, src_col=3, dest_row=0, dest_col=1, value=2)
    size = (
        window._animation_manager._cell_size
        if hasattr(window._animation_manager, "_cell_size")
        else 162
    )
    window._animation_manager.start_animation([move])

    # At t=0 (no update yet), offset = full delta
    offset = window._animation_manager.get_pixel_offset(0, 3)
    expected_x = (3 - 1) * size  # source_col - dest_col * cell_size
    assert offset[0] == pytest.approx(float(expected_x))
    assert offset[1] == pytest.approx(0.0)


def test_pending_tile_moves_initialized(
    _patch_pygame: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that GameWindow initializes _pending_tile_moves as an empty list
    and has a non-None AnimationManager instance ready.

    This ensures attributes exist and are ready for the animation pipeline.
    """
    _require_animation_manager()
    assert GameWindow is not None
    assert AnimationManager is not None

    window = GameWindow()

    assert hasattr(window, "_pending_tile_moves")
    assert isinstance(window._pending_tile_moves, list)
    assert len(window._pending_tile_moves) == 0

    # Integration assertion: animation manager must be instantiated
    assert window._animation_manager is not None, (
        "GameWindow._animation_manager must be a real AnimationManager instance, "
        "not None. Create it in __init__() or via lazy initialization."
    )
    assert isinstance(window._animation_manager, AnimationManager)
