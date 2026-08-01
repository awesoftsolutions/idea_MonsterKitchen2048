"""tests/test_renderer.py — TDD Red Phase tests for the unified Renderer class.

Tests the Renderer class from src/render/renderer.py using headless mocking
of pygame surfaces, fonts, BoardLayout, AssetLoader, and GameSession.

All 18 test cases (TC-1 through TC-18) are collected by pytest even when
src/render/renderer.py does not exist yet. Tests naturally call Renderer()
which is None when the module is missing, producing a TypeError.

Framework: pytest + unittest.mock. No pygame.init() or display required.
"""

# --- Contract ---
# Purpose:   TDD Red Phase tests for the unified Renderer class.
# System:    Exercises Renderer from src/render/renderer.py using headless
#            mocking of pygame surfaces, fonts, BoardLayout, AssetLoader,
#            and GameSession.  18 test cases (TC-1 through TC-18).
# Depends:   src.render.renderer.Renderer (graceful fallback if missing),
#            pytest, unittest.mock.
# Used by:   pytest discovery (tests/ directory).
# Public API: _make_mock_session, _make_mock_surface, _make_mock_assets,
#             _make_sprite, _make_mock_layout, _cell_rect (test helpers).
#             18 test_ functions (pytest test cases).
# --- End Contract ---

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

# ---------------------------------------------------------------------------
# Module-level Renderer import with graceful fallback
# ---------------------------------------------------------------------------

try:
    from src.render.renderer import Renderer
except ImportError:
    Renderer = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Helper functions
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

    Each sprite method returns the same mock object for the same first positional
    argument, matching real AssetLoader caching behavior.  This preserves mock
    identity (``is``) checks in tests that blit-followed-by-query.

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


# ===========================================================================
# TC-1 and TC-2: Constructor tests
# ===========================================================================


def test_constructor_stores_asset_loader() -> None:
    """TC-1 (AC-1): Renderer stores the AssetLoader reference."""
    assets = MagicMock()
    layout = MagicMock()
    renderer = Renderer(assets, layout)  # type: ignore[misc]
    assert renderer._assets is assets


def test_constructor_stores_layout() -> None:
    """TC-2 (AC-1): Renderer stores the BoardLayout reference."""
    assets = MagicMock()
    layout = MagicMock()
    renderer = Renderer(assets, layout)  # type: ignore[misc]
    assert renderer._layout is layout


# ===========================================================================
# Fixtures shared by TC-3 through TC-18
# ===========================================================================


@pytest.fixture()
def _patch_font(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch pygame.font.SysFont and get_init so _ensure_font works headless.

    This fixture patches the pygame.font module so Renderer._ensure_font()
    can create a font object without requiring pygame.font.init().
    """
    mock_font = MagicMock()
    mock_text_surface = _make_mock_surface(80, 36)
    mock_font.render.return_value = mock_text_surface

    import pygame.font

    monkeypatch.setattr(pygame.font, "get_init", lambda: True)
    monkeypatch.setattr(pygame.font, "SysFont", lambda *a, **kw: mock_font)

    return mock_font


def _build_renderer_and_run(
    board: list[list[int]] | None = None,
    overlay: list[list[int]] | None = None,
    score: int = 0,
) -> tuple[MagicMock, MagicMock, MagicMock]:
    """Build renderer with mocks, run render(), return (screen, assets, layout).

    Args:
        board: 4x4 tile value grid.
        overlay: 4x4 rotten overlay grid.
        score: Current score value.

    Returns:
        Tuple of (screen mock, assets mock, layout mock).
    """
    assets = _make_mock_assets()
    layout = _make_mock_layout()
    screen = _make_mock_surface(700, 800)
    session = _make_mock_session(board=board, overlay=overlay, score=score)

    renderer = Renderer(assets, layout)  # type: ignore[misc]
    renderer.render(screen, session)

    return screen, assets, layout


# ===========================================================================
# TC-3: Background wallpaper is the first blit
# ===========================================================================


def test_render_blits_background_wallpaper_first(_patch_font: MagicMock) -> None:
    """TC-3 (AC-13): background_wallpaper is the first blit call."""
    screen, assets, _layout = _build_renderer_and_run()

    assert screen.blit.call_count >= 2
    first_blit_pos = screen.blit.call_args_list[0][0][1]
    assets.get_ui_sprite.assert_any_call("background_wallpaper")
    assert first_blit_pos == (0, 0), (
        f"Wallpaper expected at (0,0), got {first_blit_pos}"
    )


# ===========================================================================
# TC-4: Board background is the second blit
# ===========================================================================


def test_render_blits_board_background_second(_patch_font: MagicMock) -> None:
    """TC-4 (AC-13): board_background is the second blit call."""
    screen, assets, layout = _build_renderer_and_run()

    assert screen.blit.call_count >= 2
    second_blit_pos = screen.blit.call_args_list[1][0][1]
    assets.get_ui_sprite.assert_any_call("board_background")
    layout.board_rect.assert_called()

    import pygame

    expected_rect = pygame.Rect(layout.board_rect())
    assert second_blit_pos == expected_rect, (
        f"Expected {expected_rect}, got {second_blit_pos}"
    )


# ===========================================================================
# TC-5: Empty cells get cell_empty sprite
# ===========================================================================


def test_render_empty_cell_blits_cell_empty_sprite(_patch_font: MagicMock) -> None:
    """TC-5 (AC-7): Cells with value 0 render the cell_empty sprite."""
    _screen, assets, _layout = _build_renderer_and_run(
        board=[[0] * 4 for _ in range(4)],
    )

    assets.get_ui_sprite.assert_any_call("cell_empty")


# ===========================================================================
# TC-6: Tile at correct grid position
# ===========================================================================


def test_render_tile_sprite_at_correct_position(_patch_font: MagicMock) -> None:
    """TC-6 (AC-2): Tile value 2 blits at the correct grid cell position (0,0)."""
    board = [[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    screen, assets, layout = _build_renderer_and_run(board=board)

    assets.get_tile_sprite.assert_any_call(2)
    layout.cell_rect.assert_any_call(0, 0)

    import pygame

    expected_pos = pygame.Rect(layout.cell_rect(0, 0))
    tile_sprite = assets.get_tile_sprite(2)
    found = any(
        blit_call[0][0] is tile_sprite and blit_call[0][1] == expected_pos
        for blit_call in screen.blit.call_args_list
    )
    assert found, f"Tile sprite not blitted at {expected_pos}"


# ===========================================================================
# TC-7: Overlay >= 2 uses rotten_normal
# ===========================================================================


def test_render_rotten_overlay_normal_for_countdown_ge_2(
    _patch_font: MagicMock,
) -> None:
    """TC-7 (AC-8): Overlay value >= 2 renders rotten_normal sprite."""
    board = [[4, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    overlay = [[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    _screen, assets, _layout = _build_renderer_and_run(board=board, overlay=overlay)

    assets.get_special_sprite.assert_any_call("rotten_normal")


# ===========================================================================
# TC-8: Overlay == 1 uses rotten_warning
# ===========================================================================


def test_render_rotten_overlay_warning_for_countdown_eq_1(
    _patch_font: MagicMock,
) -> None:
    """TC-8 (AC-9): Overlay value == 1 renders rotten_warning sprite."""
    board = [[4, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    overlay = [[1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    _screen, assets, _layout = _build_renderer_and_run(board=board, overlay=overlay)

    assets.get_special_sprite.assert_any_call("rotten_warning")


# ===========================================================================
# TC-9: Overlay == 0 means no overlay sprite
# ===========================================================================


def test_render_no_rotten_overlay_for_value_0(_patch_font: MagicMock) -> None:
    """TC-9 (AC-10): Overlay value==0 does NOT call get_special_sprite."""
    overlay = [[0] * 4 for _ in range(4)]
    _screen, assets, _layout = _build_renderer_and_run(overlay=overlay)

    assets.get_special_sprite.assert_not_called()


# ===========================================================================
# TC-10: Score text via font.render
# ===========================================================================


def test_render_score_text_via_font(_patch_font: MagicMock) -> None:
    """TC-10 (AC-3): Score text is rendered via font.render with correct value."""
    _screen, _assets, _layout = _build_renderer_and_run(score=42)

    _patch_font.render.assert_any_call("42", True, (255, 255, 255))


# ===========================================================================
# TC-11: Uses AssetLoader for images
# ===========================================================================


def test_render_uses_asset_loader_for_images(_patch_font: MagicMock) -> None:
    """TC-11 (AC-4): All sprite retrieval goes through AssetLoader methods."""
    board = [[2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    _screen, assets, _layout = _build_renderer_and_run(board=board)

    assets.get_ui_sprite.assert_called()
    assets.get_tile_sprite.assert_called()
    assets.get_mascot_sprite.assert_called()


# ===========================================================================
# TC-12: Uses BoardLayout for positioning
# ===========================================================================


def test_render_uses_board_layout_for_positioning(_patch_font: MagicMock) -> None:
    """TC-12 (AC-5): BoardLayout.cell_rect() called 16 times for 4x4 grid."""
    _screen, _assets, layout = _build_renderer_and_run()

    assert layout.cell_rect.call_count == 16, (
        f"Expected 16 cell_rect calls, got {layout.cell_rect.call_count}"
    )
    layout.board_rect.assert_called()


# ===========================================================================
# TC-13: Title logo at top
# ===========================================================================


def test_render_title_logo_at_top(_patch_font: MagicMock) -> None:
    """TC-13 (AC-11): title_logo is blitted at (10, 10)."""
    screen, assets, _layout = _build_renderer_and_run()

    assets.get_ui_sprite.assert_any_call("title_logo")
    title_sprite = assets.get_ui_sprite("title_logo")
    title_blit = None
    for blit_call in screen.blit.call_args_list:
        if blit_call[0][0] is title_sprite:
            title_blit = blit_call
            break
    assert title_blit is not None, "title_logo sprite not blitted"
    assert title_blit[0][1] == (10, 10), f"Expected (10,10), got {title_blit[0][1]}"


# ===========================================================================
# TC-14: Mascot beside title
# ===========================================================================


def test_render_mascot_beside_title(_patch_font: MagicMock) -> None:
    """TC-14 (AC-12): mascot_idle is blitted beside the title."""
    screen, assets, _layout = _build_renderer_and_run()

    assets.get_mascot_sprite.assert_any_call("idle")
    mascot_sprite = assets.get_mascot_sprite("idle")
    mascot_blit = None
    for blit_call in screen.blit.call_args_list:
        if blit_call[0][0] is mascot_sprite:
            mascot_blit = blit_call
            break
    assert mascot_blit is not None, "mascot sprite not blitted"
    mascot_x = mascot_blit[0][1][0]
    assert mascot_x > 10, f"Mascot should be right of title, got x={mascot_x}"


# ===========================================================================
# TC-15: Session integration calls all methods
# ===========================================================================


def test_render_session_integration_calls_all_methods(_patch_font: MagicMock) -> None:
    """TC-15 (AC-4, AC-5): render() reads all state from session."""
    assets = _make_mock_assets()
    layout = _make_mock_layout()
    screen = _make_mock_surface(700, 800)
    session = _make_mock_session()

    renderer = Renderer(assets, layout)  # type: ignore[misc]
    renderer.render(screen, session)

    session.get_board_grid.assert_called()
    session.get_rotten_overlay.assert_called()
    session.get_score.assert_called()
    session.get_high_score.assert_called()
    session.get_move_count.assert_called()


# ===========================================================================
# TC-16: Empty board renders without error
# ===========================================================================


def test_render_handles_empty_board_no_errors(_patch_font: MagicMock) -> None:
    """TC-16 (AC-15): All-zero board renders without error, at least 16 blit calls."""
    board = [[0] * 4 for _ in range(4)]
    assets = _make_mock_assets()
    layout = _make_mock_layout()
    screen = _make_mock_surface(700, 800)
    session = _make_mock_session(board=board)

    renderer = Renderer(assets, layout)  # type: ignore[misc]
    renderer.render(screen, session)  # Should not raise

    assert screen.blit.call_count >= 16, (
        f"Expected at least 16 blit calls, got {screen.blit.call_count}"
    )


# ===========================================================================
# TC-17: Overlay value 3 uses rotten_normal (not warning)
# ===========================================================================


def test_render_rotten_overlay_3_uses_normal(_patch_font: MagicMock) -> None:
    """TC-17 (AC-8): Overlay value 3 uses rotten_normal, NOT rotten_warning."""
    board = [[4, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    overlay = [[3, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    _screen, assets, _layout = _build_renderer_and_run(board=board, overlay=overlay)

    assets.get_special_sprite.assert_any_call("rotten_normal")
    for special_call in assets.get_special_sprite.call_args_list:
        assert special_call != call("rotten_warning"), (
            "rotten_warning should NOT be called for overlay value 3"
        )


# ===========================================================================
# TC-18: Mixed board correct sprite per cell
# ===========================================================================


def test_render_mixed_board_correct_sprite_per_cell(_patch_font: MagicMock) -> None:
    """TC-18 (AC-2, AC-7, AC-8): Mixed board with tiles, empty cells, and overlays."""
    board = [
        [2, 4, 0, 8],
        [0, 16, 32, 0],
        [64, 0, 0, 128],
        [0, 0, 256, 0],
    ]
    overlay = [
        [0, 0, 0, 0],
        [0, 0, 2, 0],
        [0, 0, 0, 1],
        [0, 0, 0, 0],
    ]
    _screen, assets, _layout = _build_renderer_and_run(board=board, overlay=overlay)

    # All 8 non-empty tile values should be fetched
    for value in [2, 4, 8, 16, 32, 64, 128, 256]:
        assets.get_tile_sprite.assert_any_call(value)

    # Empty cells should use cell_empty sprite
    assets.get_ui_sprite.assert_any_call("cell_empty")

    # Overlay value 2 at (1,2) => rotten_normal
    assets.get_special_sprite.assert_any_call("rotten_normal")

    # Overlay value 1 at (2,3) => rotten_warning
    assets.get_special_sprite.assert_any_call("rotten_warning")
