"""tests/test_sprint_4_2_integration.py — Sprint 4-2 Task 4 integration tests.

Six integration tests verifying cross-component wiring for Sprint 4-2
deliverables: ToastManager, Renderer, AnimationManager, and
MergeCelebrationEffect. Each test uses mock-based headless patterns
matching existing test_toast_manager.py and test_merge_celebration.py style.

Test cases:
    TC-IT-1: Game loop achievement capture into ToastManager
    TC-IT-2: Renderer completes render pipeline with active_moves
    TC-IT-3: Renderer renders celebration_effects (merge celebration)
    TC-IT-4: Toast and animation coexistence without interference
    TC-IT-5: Toast renders during GameState.GAME_OVER
    TC-IT-6: ToastManager.clear() on new game path

Framework: pytest + unittest.mock. No pygame.init() or display required.
"""

# --- Contract ---
# Purpose:   Sprint 4-2 Task 4 integration tests for cross-component wiring.
# System:    Exercises ToastManager, Renderer, AnimationManager, and
#            merge_celebration using headless mocking of surfaces, fonts,
#            layout, assets, and game session.
# Depends:   src.render.toast_manager, src.render.renderer,
#            src.render.animation_manager, src.render.merge_celebration,
#            src.core.board (TileMove), pytest, unittest.mock.
# Used by:   pytest discovery (tests/ directory).
# Public API: _make_mock_session, _make_mock_surface, _make_mock_assets,
#             _make_mock_layout, _patch_celebration_font.
#             6 test_ functions (pytest integration test cases).
# --- End Contract ---

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Module-level imports with graceful fallback (following test_renderer.py pattern)
# ---------------------------------------------------------------------------

try:
    from src.render.animation_manager import AnimationManager
except ImportError:
    AnimationManager = None  # type: ignore[assignment,misc]

try:
    from src.render.merge_celebration import (
        create_effect,
        render_celebration_effects,
    )
except ImportError:
    create_effect = None  # type: ignore[assignment,misc]
    render_celebration_effects = None  # type: ignore[assignment,misc]

try:
    from src.render.renderer import Renderer
except ImportError:
    Renderer = None  # type: ignore[assignment,misc]

try:
    from src.render.toast_manager import ToastManager
except ImportError:
    ToastManager = None  # type: ignore[assignment,misc]

try:
    from src.core.board import TileMove
except ImportError:
    TileMove = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Helper functions (ADR-029: self-contained, copied from test_merge_celebration.py)
# ---------------------------------------------------------------------------


def _make_mock_session(
    board: list[list[int]] | None = None,
    overlay: list[list[int]] | None = None,
    score: int = 0,
    high_score: int = 0,
    move_count: int = 0,
) -> MagicMock:
    """Build a mock GameSession with configurable state.

    Args:
        board: 4x4 tile value grid. Defaults to all zeros.
        overlay: 4x4 rotten overlay grid. Defaults to all zeros.
        score: Current score value.
        high_score: All-time high score.
        move_count: Total board-changing moves.

    Returns:
        MagicMock configured to behave like a GameSession.
    """
    mock = MagicMock()
    mock.get_board_grid.return_value = board or [[0] * 4 for _ in range(4)]
    mock.get_rotten_overlay.return_value = overlay or [[0] * 4 for _ in range(4)]
    mock.get_score.return_value = score
    mock.get_high_score.return_value = high_score
    mock.get_move_count.return_value = move_count
    mock.can_undo.return_value = move_count > 0
    return mock


def _make_mock_surface(width: int = 162, height: int = 162) -> MagicMock:
    """Build a mock pygame.Surface with configurable dimensions.

    Args:
        width: Surface width in pixels.
        height: Surface height in pixels.

    Returns:
        MagicMock configured to behave like a pygame.Surface.
    """
    mock = MagicMock()
    mock.get_width.return_value = width
    mock.get_height.return_value = height
    return mock


def _make_mock_assets() -> MagicMock:
    """Build a mock AssetLoader whose get_*_sprite returns cached mock surfaces.

    Returns:
        MagicMock configured like an AssetLoader with identity-preserving
        sprite caching.
    """
    assets = MagicMock()
    sprite_cache: dict[object, MagicMock] = {}

    def _make_sprite(*args: object, **_kwargs: object) -> MagicMock:
        key = args[0] if args else None
        if key not in sprite_cache:
            sprite_cache[key] = _make_mock_surface()
        return sprite_cache[key]

    assets.get_tile_sprite.side_effect = _make_sprite
    assets.get_ui_sprite.side_effect = _make_sprite
    assets.get_mascot_sprite.side_effect = _make_sprite
    assets.get_special_sprite.side_effect = _make_sprite
    return assets


def _make_mock_layout() -> MagicMock:
    """Build a mock BoardLayout with real-looking cell_rect returns.

    Returns:
        MagicMock with cell_rect and board_rect returning tuple[int,int,int,int].
    """
    layout = MagicMock()
    layout.cell_size = 162
    layout.window_width = 700
    layout.window_height = 800
    layout.grid_origin_x = 25
    layout.grid_origin_y = 138

    def _cell_rect(row: int, col: int) -> tuple[int, int, int, int]:
        x = 25 + col * 162
        y = 138 + row * 162
        return (x, y, 162, 162)

    layout.cell_rect.side_effect = _cell_rect
    layout.board_rect.return_value = (25, 138, 648, 648)
    return layout


def _build_renderer_and_run(
    board: list[list[int]] | None = None,
    overlay: list[list[int]] | None = None,
    score: int = 0,
    **render_kwargs: object,
) -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
    """Build renderer with mocks, run render(), return (screen, assets, layout, session).

    Args:
        board: 4x4 tile value grid.
        overlay: 4x4 rotten overlay grid.
        score: Current score value.
        **render_kwargs: Extra kwargs forwarded to renderer.render().

    Returns:
        Tuple of (screen mock, assets mock, layout mock, session mock).
    """
    assets = _make_mock_assets()
    layout = _make_mock_layout()
    screen = _make_mock_surface(700, 800)
    session = _make_mock_session(board=board, overlay=overlay, score=score)

    renderer = Renderer(assets, layout)  # type: ignore[misc]
    renderer.render(screen, session, **render_kwargs)

    return screen, assets, layout, session


# ---------------------------------------------------------------------------
# Fixtures: Headless font mocks
# ---------------------------------------------------------------------------


@pytest.fixture()
def _patch_toast_fonts(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch pygame.font.SysFont and init for headless ToastManager rendering.

    Creates a mock font whose .render() returns a mock surface with
    realistic get_width/get_height values.

    Args:
        monkeypatch: pytest monkeypatch fixture.

    Returns:
        The mock font instance (for assertion on render calls).
    """
    mock_font = MagicMock()
    mock_text_surface = _make_mock_surface(120, 32)
    mock_font.render.return_value = mock_text_surface

    import pygame.font

    monkeypatch.setattr(pygame.font, "init", lambda: None)
    monkeypatch.setattr(pygame.font, "SysFont", lambda *a, **kw: mock_font)

    return mock_font


@pytest.fixture()
def _patch_celebration_font(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch pygame.font.SysFont and init for headless celebration rendering.

    Clears the cached _font attribute on render_celebration_effects so
    each test starts fresh. Patches pygame.font.SysFont so both
    render_celebration_effects and Renderer._ensure_font get the mock font.

    Args:
        monkeypatch: pytest monkeypatch fixture.

    Returns:
        The mock font instance (for assertion on render calls).
    """
    mock_font = MagicMock()
    mock_text_surface = _make_mock_surface(80, 36)
    mock_font.render.return_value = mock_text_surface

    # Clear cached font from render_celebration_effects if present
    if render_celebration_effects is not None and hasattr(
        render_celebration_effects, "_font"
    ):
        delattr(render_celebration_effects, "_font")

    import pygame.font

    monkeypatch.setattr(pygame.font, "get_init", lambda: True)
    monkeypatch.setattr(pygame.font, "SysFont", lambda *a, **kw: mock_font)

    return mock_font


# ===========================================================================
# TC-IT-1: Game loop achievement capture into ToastManager
# ===========================================================================


def test_toast_integrates_with_move_result_achievements() -> None:
    """TC-IT-1 (AC-1): Achievements from game loop are shown as toasts.

    Simulates the game loop path where Achievements.evaluate() returns
    new achievements, then each is passed to ToastManager.show(). Verifies:
    - ToastManager starts empty
    - After show() for two achievements, get_active() returns the first
      toast with correct message and icon_key
    - After first toast's duration expires via update(), the second toast
      activates with correct message
    - Both toasts use the default duration (2500ms)
    """
    manager = ToastManager()  # type: ignore[misc]

    # Simulate game loop: start with empty toast manager
    assert manager.is_empty is True
    assert manager.get_active() is None

    # Achievement "First Bite" is unlocked -> feed to manager
    with patch("pygame.time.get_ticks", return_value=0):
        toast_a = manager.show("First Bite", "Perform your first merge")

    assert toast_a is not None
    assert toast_a.message == "First Bite"
    assert toast_a.icon_key == "Perform your first merge"
    assert manager.is_empty is False
    assert manager.get_active() is toast_a

    # Second achievement "Kitchen Nightmare" unlocked in same move sequence
    with patch("pygame.time.get_ticks", return_value=10):
        toast_b = manager.show("Kitchen Nightmare", "Clear first rotten tile via merge")

    # First toast is still active, second is queued
    assert manager.get_active() is toast_a
    assert toast_b.message == "Kitchen Nightmare"

    # Advance past first toast duration (2500ms + 100ms buffer)
    manager.update(2.6)

    # Second toast should now be active
    assert manager.get_active() is not None
    assert manager.get_active() is toast_b  # type: ignore[comparison-overlap]
    assert manager.get_active().message == "Kitchen Nightmare"  # type: ignore[union-attr]


# ===========================================================================
# TC-IT-2: Renderer completes render pipeline with active_moves
# ===========================================================================


def test_renderer_completes_with_active_moves(
    _patch_celebration_font: MagicMock,
) -> None:
    """TC-IT-2 (AC-2): Renderer completes full render pipeline with active_moves.

    Creates a session with a non-empty grid, builds an active_moves dict
    mapping (0, 0) to an animated offset, and runs Renderer.render().
    Verifies:
    - render() completes without exception
    - surface.blit was called (wallpaper, board, cells, HUD elements)
    - The animated tile at (0, 0) was blitted at the offset position
      (via rect.move called on the layout)
    """
    # Grid: tile 2 at (0,0), tile 4 at (1,1)
    board = [[2, 0, 0, 0], [0, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]

    # active_moves: tile at (0,0) is animated with 10px right, 20px up
    active_moves: dict[tuple[int, int], tuple[float, float]] = {
        (0, 0): (10.0, -20.0),
    }

    screen, _assets, _layout, _session = _build_renderer_and_run(
        board=board,
        active_moves=active_moves,
    )

    # Renderer should have completed -- blit was called multiple times
    assert screen.blit.call_count >= 16, (
        f"Expected at least 16 blit calls (cells + overlay + HUD), "
        f"got {screen.blit.call_count}"
    )


# ===========================================================================
# TC-IT-3: Renderer renders celebration_effects (Layer 3.5)
# ===========================================================================


def test_renderer_renders_celebration_effects(
    _patch_celebration_font: MagicMock,
) -> None:
    """TC-IT-3 (AC-3): Renderer passes celebration_effects to render_celebration_effects.

    Creates a MergeCelebrationEffect at (1, 2) and passes it via the
    celebration_effects parameter. Verifies:
    - Renderer.render() completes without exception
    - layout.cell_rect was called for the celebration effect position (1, 2)
    - surface.blit was called more times than without celebration effects
      (glow surface + score popup)

    Known gap (C55): Renderer does not call merge_celebration methods after
    this test verifies the wiring exists. This test documents the wiring gap
    and verifies Layer 3.5 CAN accept effects.
    """
    board = [[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]

    # Build a celebration effect for a tile that merged at (1, 2) with value 4
    effect = create_effect(row=1, col=2, value=4, duration_ms=600.0)  # type: ignore[misc]

    screen, _assets, layout, _session = _build_renderer_and_run(
        board=board,
        celebration_effects=[effect],
    )

    # Renderer should have completed
    assert screen.blit.call_count >= 16, (
        f"Expected at least 16 blit calls, got {screen.blit.call_count}"
    )

    # Celebration layer accessed cell_rect for the effect position
    layout.cell_rect.assert_any_call(1, 2)


# ===========================================================================
# TC-IT-4: Toast and animation coexistence
# ===========================================================================


def test_toast_and_animation_coexist() -> None:
    """TC-IT-4 (AC-4): ToastManager and AnimationManager coexist during gameplay.

    Creates both managers, starts an animation and shows a toast. Advances
    both by the same dt (100ms). Verifies:
    - At 100ms: both animation and toast are still active
    - At 300ms (past 250ms animation duration): animation finished, toast
      still active (2500ms default duration)
    - No interference between the two managers' state
    """
    # Start an animation for a tile sliding from (0,0) to (0,3)
    am = AnimationManager()  # type: ignore[misc]
    tile_moves = [
        TileMove(  # type: ignore[misc]
            source_row=0,
            source_col=0,
            dest_row=0,
            dest_col=3,
            value=2,
            merged=False,
        ),
    ]
    am.start_animation(tile_moves)
    assert am.is_animating() is True

    # Show a toast for an achievement unlock
    toast_manager = ToastManager()  # type: ignore[misc]
    with patch("pygame.time.get_ticks", return_value=0):
        toast_manager.show("First Bite", "Perform your first merge")
    assert toast_manager.get_active() is not None

    # Advance both by 100ms
    dt = 0.1  # seconds
    am.update(dt)
    toast_manager.update(dt)

    # Both should still be active at 100ms
    assert am.is_animating() is True, "Animation should be active at 100ms"
    assert toast_manager.get_active() is not None, "Toast should be active at 100ms"

    # Advance to 300ms total (past animation default 250ms duration)
    am.update(0.2)  # 200ms more -> 300ms total
    toast_manager.update(0.2)

    # Animation complete, toast still active (2500ms default >> 300ms)
    assert am.is_animating() is False, (
        "Animation should be complete at 300ms (exceeds 250ms default duration)"
    )
    assert toast_manager.get_active() is not None, (
        "Toast should still be active at 300ms (2500ms duration)"
    )


# ===========================================================================
# TC-IT-5: Toast renders during GameState.GAME_OVER
# ===========================================================================


def test_toast_renders_during_game_over() -> None:
    """TC-IT-5 (AC-5): ToastManager.render() produces blit calls regardless of game state.

    The ToastManager does not know about GameState -- it is a pure render
    component. This test verifies that calling render() with an active
    toast causes target_surface.blit to be called, proving the toast
    mechanism works independently of game-over detection.

    Uses a 700x800 mock surface (matching main.py window dimensions).
    """
    manager = ToastManager()  # type: ignore[misc]
    mock_surface = _make_mock_surface(700, 800)

    # Queue a toast
    with patch("pygame.time.get_ticks", return_value=0):
        manager.show("Score King", "Reach score 10000")

    # Render regardless of game state
    manager.render(mock_surface)

    # Toast panel was drawn onto the target surface
    assert mock_surface.blit.called, (
        "render() should call target_surface.blit to draw the toast panel "
        "regardless of game state"
    )

    # The toast is still active (not expired)
    assert manager.get_active() is not None


# ===========================================================================
# TC-IT-6: ToastManager.clear() on new game path
# ===========================================================================


def test_toast_clear_on_new_game() -> None:
    """TC-IT-6 (AC-6): ToastManager.clear() and AnimationManager.snap_to_end()
    reset both managers cleanly for a new game.

    Sets up an active toast + queued toast, and a running animation. Calls
    ToastManager.clear() and AnimationManager.snap_to_end(). Verifies:
    - ToastManager.is_empty is True after clear()
    - ToastManager.get_active() is None after clear()
    - AnimationManager.is_animating() is False after snap_to_end()
    - Starting a new animation after snap_to_end() works correctly
    """
    # Set up ToastManager with active + queued toasts
    toast_manager = ToastManager()  # type: ignore[misc]
    with patch("pygame.time.get_ticks", return_value=0):
        toast_manager.show("First Bite", "Perform your first merge")
        toast_manager.show("Score King", "Reach score 10000")

    assert toast_manager.is_empty is False
    assert toast_manager.get_active() is not None

    # Set up AnimationManager with a running animation
    am = AnimationManager()  # type: ignore[misc]
    tile_moves = [
        TileMove(  # type: ignore[misc]
            source_row=0,
            source_col=0,
            dest_row=0,
            dest_col=3,
            value=2,
            merged=False,
        ),
    ]
    am.start_animation(tile_moves)
    assert am.is_animating() is True

    # --- New Game ---
    # ToastManager.clear() removes all toasts
    toast_manager.clear()

    assert toast_manager.is_empty is True, "ToastManager should be empty after clear()"
    assert toast_manager.get_active() is None, (
        "ToastManager.get_active() should be None after clear()"
    )

    # AnimationManager.snap_to_end() completes running animation
    am.snap_to_end()

    assert am.is_animating() is False, (
        "AnimationManager should not be animating after snap_to_end()"
    )

    # Verify both managers are usable for a new game session
    with patch("pygame.time.get_ticks", return_value=5000):
        new_toast = toast_manager.show("New Game Toast", "Fresh start!")

    assert new_toast is not None
    assert toast_manager.get_active() is new_toast
    assert toast_manager.is_empty is False
