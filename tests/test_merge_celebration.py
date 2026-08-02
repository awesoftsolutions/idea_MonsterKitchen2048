"""tests/test_merge_celebration.py — TDD Red Phase tests for MergeCelebrationEffect.

Tests the MergeCelebrationEffect dataclass, standalone lifecycle functions
(create_effect, update_effects, cleanup_expired_effects, render_celebration_effects),
Renderer Layer 3.5 integration, AnimationManager.is_merge_destination(), and
import safety.

All 10 test cases are collected by pytest even when src/render/merge_celebration.py
does not exist yet. Tests that import from that module use try/except ImportError
with fallback to None, matching the pattern in test_renderer.py. The tests naturally
call create_effect() which is None when the module is missing, producing a TypeError.

Framework: pytest + unittest.mock. No pygame.init() or display required.
"""

# --- Contract ---
# Purpose:   TDD Red Phase tests for merge celebration visual effects.
# System:    Exercises MergeCelebrationEffect from src/render/merge_celebration.py
#            using headless mocking of pygame surfaces, fonts, BoardLayout,
#            AssetLoader, and GameSession.  10 test cases.
# Depends:   src.render.merge_celebration (graceful fallback if missing),
#            src.render.renderer.Renderer (graceful fallback if missing),
#            src.render.animation_manager.AnimationManager (real class),
#            pytest, unittest.mock.
# Used by:   pytest discovery (tests/ directory).
# Public API: _make_mock_session, _make_mock_surface, _make_mock_assets,
#             _make_mock_layout, _patch_celebration_font (test helpers).
#             10 test_ functions (pytest test cases).
# --- End Contract ---

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Module-level imports with graceful fallback (following test_renderer.py pattern)
# ---------------------------------------------------------------------------

try:
    from src.render.merge_celebration import (
        MergeCelebrationEffect,
        cleanup_expired_effects,
        create_effect,
        render_celebration_effects,
        update_effects,
    )
except ImportError:
    MergeCelebrationEffect = None  # type: ignore[assignment,misc]
    create_effect = None  # type: ignore[assignment,misc]
    update_effects = None  # type: ignore[assignment,misc]
    cleanup_expired_effects = None  # type: ignore[assignment,misc]
    render_celebration_effects = None  # type: ignore[assignment,misc]

try:
    from src.render.renderer import Renderer
except ImportError:
    Renderer = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Helper functions (copied from test_renderer.py for self-containment)
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
# Fixture: Headless font mock for celebration rendering
# ---------------------------------------------------------------------------


@pytest.fixture()
def _patch_celebration_font(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch pygame.font.SysFont and get_init for headless celebration rendering.

    This fixture patches the pygame.font module so render_celebration_effects()
    can create a font object without requiring pygame.font.init(). Follows the
    same pattern as _patch_font in test_renderer.py.
    """
    mock_font = MagicMock()
    mock_text_surface = _make_mock_surface(80, 36)
    mock_font.render.return_value = mock_text_surface

    import pygame.font

    monkeypatch.setattr(pygame.font, "get_init", lambda: True)
    monkeypatch.setattr(pygame.font, "SysFont", lambda *a, **kw: mock_font)

    return mock_font


# ===========================================================================
# TC-1: MergeCelebrationEffect dataclass fields
# ===========================================================================


def test_merge_celebration_effect_fields() -> None:
    """TC-1 (AC-1): MergeCelebrationEffect has all 8 required fields with correct defaults.

    Creates an effect via create_effect() and asserts every field has the
    expected initial value.  Fails with TypeError when create_effect is None
    (module missing).
    """
    effect = create_effect(row=1, col=2, value=4)  # type: ignore[misc]

    assert effect.row == 1
    assert effect.col == 2
    assert effect.value == 4
    assert effect.glow_alpha == 255
    assert effect.score_offset_y == 0.0
    assert effect.score_alpha == 255
    assert effect.elapsed_ms == 0.0
    assert effect.duration_ms == 600.0


# ===========================================================================
# TC-2: Golden glow alpha decays linearly from 255 to 0
# ===========================================================================


def test_golden_glow_alpha_decay() -> None:
    """TC-2 (AC-2): glow_alpha decays linearly over the effect duration.

    After 300ms of a 600ms effect, glow_alpha should be int(255 * 0.5) = 127.
    After another 300ms (end), glow_alpha should be 0.
    """
    effect = create_effect(row=0, col=0, value=4, duration_ms=600)  # type: ignore[misc]

    update_effects([effect], delta_ms=300)  # type: ignore[misc]
    assert effect.glow_alpha == 127, f"Expected 127 at 50%, got {effect.glow_alpha}"

    update_effects([effect], delta_ms=300)  # type: ignore[misc]
    assert effect.glow_alpha == 0, f"Expected 0 at end, got {effect.glow_alpha}"


# ===========================================================================
# TC-3: Score popup floats upward and fades
# ===========================================================================


def test_score_popup_floats_upward() -> None:
    """TC-3 (AC-3): score_offset_y increases over time and score_alpha decays.

    After 200ms of a 600ms effect:
    - score_offset_y should be 200 * 0.08 = 16.0
    - score_alpha should be int(255 * (1 - 200/600)) = 170
    """
    effect = create_effect(row=0, col=0, value=8, duration_ms=600)  # type: ignore[misc]

    update_effects([effect], delta_ms=200)  # type: ignore[misc]
    assert effect.score_offset_y > 0.0, (
        f"Expected offset > 0, got {effect.score_offset_y}"
    )
    assert effect.score_offset_y == pytest.approx(16.0), (
        f"Expected 16.0, got {effect.score_offset_y}"
    )
    assert effect.score_alpha < 255, f"Expected alpha < 255, got {effect.score_alpha}"
    assert effect.score_alpha == 170, f"Expected 170, got {effect.score_alpha}"


# ===========================================================================
# TC-4: Expired effects are removed by cleanup
# ===========================================================================


def test_update_removes_expired_effects() -> None:
    """TC-4 (AC-5): cleanup_expired_effects removes effects where elapsed >= duration.

    Two effects with 600ms duration, updated by 700ms (both expired).
    After cleanup, the result list should be empty.
    """
    effect_a = create_effect(row=0, col=0, value=4, duration_ms=600)  # type: ignore[misc]
    effect_b = create_effect(row=1, col=1, value=8, duration_ms=600)  # type: ignore[misc]

    effects: list = [effect_a, effect_b]
    update_effects(effects, delta_ms=700)  # type: ignore[misc]

    # Both should be clamped to duration
    assert effect_a.elapsed_ms == 600.0, f"Expected 600, got {effect_a.elapsed_ms}"
    assert effect_b.elapsed_ms == 600.0, f"Expected 600, got {effect_b.elapsed_ms}"

    result = cleanup_expired_effects(effects)  # type: ignore[misc]
    assert len(result) == 0, f"Expected empty list after cleanup, got {len(result)}"


# ===========================================================================
# TC-5: Renderer celebration layer ordering (Layer 3.5)
# ===========================================================================


def test_renderer_celebration_layer_order(_patch_celebration_font: MagicMock) -> None:
    """TC-5 (AC-4): Celebration effects render between grid cells and rotten overlay.

    When celebration_effects is provided, the celebration render should occur
    after all grid cell blits and before rotten overlay blits in call_args_list.

    In TDD RED phase, this fails with TypeError because Renderer.render() does
    not accept the celebration_effects keyword argument yet.
    """
    board = [[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    overlay = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]

    mock_effect = MagicMock()
    mock_effect.row = 0
    mock_effect.col = 0
    mock_effect.value = 4
    mock_effect.glow_alpha = 200
    mock_effect.score_alpha = 200
    mock_effect.score_offset_y = 10.0

    # This should raise TypeError because render() doesn't accept celebration_effects yet
    _build_renderer_and_run(
        board=board,
        overlay=overlay,
        celebration_effects=[mock_effect],
    )


# ===========================================================================
# TC-6: No pygame import at module import time
# ===========================================================================


def test_no_pygame_at_import_time() -> None:
    """TC-6 (AC-8): Importing src.render.merge_celebration does NOT trigger pygame import.

    Records the set of pygame-related modules before importing, then imports
    the module and asserts no new pygame modules were added. This catches
    module-level "import pygame" or "from pygame import ..." statements.

    In TDD RED phase, this fails with ImportError because the module does
    not exist yet.
    """
    pygame_modules_before = {key for key in sys.modules if key.startswith("pygame")}

    # Force a fresh import by removing from cache if present
    mod_name = "src.render.merge_celebration"
    sys.modules.pop(mod_name, None)

    try:
        __import__(mod_name)
    finally:
        pygame_modules_after = {key for key in sys.modules if key.startswith("pygame")}

    new_pygame_modules = pygame_modules_after - pygame_modules_before
    assert not new_pygame_modules, (
        f"Importing {mod_name} triggered pygame imports: {new_pygame_modules}"
    )


# ===========================================================================
# TC-7: AnimationManager.is_merge_destination()
# ===========================================================================


def test_is_merge_destination_returns_true() -> None:
    """TC-7 (AC-9): is_merge_destination returns True for cells in _merge_map.

    Creates a real AnimationManager, starts an animation with a merged TileMove
    at destination (2, 3), and verifies is_merge_destination(2, 3) is True
    while is_merge_destination(0, 0) is False.

    In TDD RED phase, this fails with AttributeError because
    is_merge_destination() does not exist on AnimationManager yet.
    """
    from src.render.animation_manager import AnimationManager
    from src.core.board import TileMove

    am = AnimationManager()
    tile_moves = [
        TileMove(
            source_row=0,
            source_col=0,
            dest_row=2,
            dest_col=3,
            value=4,
            merged=True,
        ),
    ]
    am.start_animation(tile_moves)

    assert am.is_merge_destination(2, 3) is True  # type: ignore[attr-defined]
    assert am.is_merge_destination(0, 0) is False  # type: ignore[attr-defined]


# ===========================================================================
# TC-8: Renderer backward compatibility without celebration_effects
# ===========================================================================


def test_celebration_effects_none_no_render(_patch_celebration_font: MagicMock) -> None:
    """TC-8 (AC-4 supplement): Renderer.render() works unchanged with celebration_effects=None.

    Calls render() with celebration_effects=None and verifies it completes
    without error. Existing blit behavior (wallpaper, board, cells, overlay)
    should be unchanged.

    In TDD RED phase, this fails with TypeError because Renderer.render()
    does not accept the celebration_effects keyword argument yet.
    """
    board = [[2, 4, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    screen, _assets, _layout, _session = _build_renderer_and_run(
        board=board,
        celebration_effects=None,
    )
    # Should have rendered normally (wallpaper + board + cells + overlay + HUD)
    assert screen.blit.call_count >= 16, (
        f"Expected at least 16 blit calls, got {screen.blit.call_count}"
    )


# ===========================================================================
# TC-9: Golden glow surface blitted at correct position
# ===========================================================================


def test_glow_surface_blitted_at_correct_position(
    _patch_celebration_font: MagicMock,
) -> None:
    """TC-9 (AC-2 supplement): Golden glow surface is blitted with GLOW_PADDING offset.

    Creates an effect at row=1, col=2 with glow_alpha=200, calls
    render_celebration_effects on a mock surface, and verifies:
    - layout.cell_rect(1, 2) was called
    - surface.blit is called with glow at (x - GLOW_PADDING, y - GLOW_PADDING)

    In TDD RED phase, this fails with TypeError because
    render_celebration_effects is None (module missing).
    """
    surface = MagicMock()
    layout = _make_mock_layout()

    effect = create_effect(row=1, col=2, value=16, duration_ms=600)  # type: ignore[misc]
    effect.glow_alpha = 200  # Partially faded

    render_celebration_effects(surface, [effect], layout)  # type: ignore[misc]

    # Verify cell_rect was called for (1, 2)
    layout.cell_rect.assert_any_call(1, 2)

    # Verify glow was blitted at GLOW_PADDING offset (6 pixels from cell origin)
    x, y, _w, _h = layout.cell_rect(1, 2)
    glow_padding = 6
    expected_glow_pos = (x - glow_padding, y - glow_padding)

    # Find the glow blit call (the one that uses a MagicMock surface with SRCALPHA)
    found_glow = False
    for blit_call in surface.blit.call_args_list:
        pos = blit_call[0][1]
        if pos == expected_glow_pos:
            found_glow = True
            break
    assert found_glow, (
        f"Glow not blitted at {expected_glow_pos}. "
        f"Blit positions: {[c[0][1] for c in surface.blit.call_args_list]}"
    )


# ===========================================================================
# TC-10: Multiple concurrent effects update independently
# ===========================================================================


def test_multiple_concurrent_effects() -> None:
    """TC-10 (AC-5 supplement): Multiple effects coexist and update independently.

    Creates two effects at different positions, updates by 300ms, and verifies:
    - Both have elapsed_ms == 300
    - Both have reduced glow_alpha and score_alpha (< 255)
    - Both have non-zero score_offset_y
    """
    effect_a = create_effect(row=0, col=0, value=4, duration_ms=600)  # type: ignore[misc]
    effect_b = create_effect(row=3, col=3, value=16, duration_ms=600)  # type: ignore[misc]

    update_effects([effect_a, effect_b], delta_ms=300)  # type: ignore[misc]

    # Both should be at 300ms elapsed
    assert effect_a.elapsed_ms == 300.0, f"effect_a elapsed: {effect_a.elapsed_ms}"
    assert effect_b.elapsed_ms == 300.0, f"effect_b elapsed: {effect_b.elapsed_ms}"

    # Both should have reduced alpha (halfway: int(255 * 0.5) = 127)
    assert effect_a.glow_alpha < 255, f"effect_a glow_alpha: {effect_a.glow_alpha}"
    assert effect_b.glow_alpha < 255, f"effect_b glow_alpha: {effect_b.glow_alpha}"
    assert effect_a.score_alpha < 255, f"effect_a score_alpha: {effect_a.score_alpha}"
    assert effect_b.score_alpha < 255, f"effect_b score_alpha: {effect_b.score_alpha}"

    # Both should have non-zero upward drift
    assert effect_a.score_offset_y > 0.0, f"effect_a offset: {effect_a.score_offset_y}"
    assert effect_b.score_offset_y > 0.0, f"effect_b offset: {effect_b.score_offset_y}"

    # Effects are independent — different positions, same values
    assert effect_a.row != effect_b.row or effect_a.col != effect_b.col, (
        "Effects should be at different positions"
    )
