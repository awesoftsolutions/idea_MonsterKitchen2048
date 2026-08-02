# Contract: test_sprint_4_2_remediation.py
# Purpose:     Tests for Sprint 4-2 remediation fixes.
#              Fix 1 — celebration_effects wiring in GameWindow._handle_keydown and _render.
#              Fix 4 — SpriteCache with deferred pygame.smoothscale in src/render/animation.py.
# System:      pytest suite (tests/).  No pygame at import time.
# Dependencies: pytest, unittest.mock, src.main, src.render.merge_celebration,
#               src.render.animation
# Used-by:     CI pipeline, Sprint 4-2 remediation acceptance verification
# ---------------------------------------------------------------------------

"""Tests for Sprint 4-2 remediation fixes.

Fix 1 (celebration_effects wiring):
    Tests verify that GameWindow._handle_keydown creates MergeCelebrationEffect
    for merged TileMoves, passes them to renderer.render(), and clears them
    on new_game.  Each test exercises one lifecycle stage: creation,
    per-frame render pass-through, and clear-on-reset.

Fix 4 (SpriteCache):
    Tests verify that SpriteCache in src/render/animation.py provides a
    smooth_scale() method with caching, and uses deferred pygame imports.
    A source-level grep confirms no module-level pygame import.

Framework: pytest + unittest.mock. No pygame.init() or display required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock, patch

import pytest

# ---------------------------------------------------------------------------
# Module-level imports with graceful fallback (TDD red phase)
# ---------------------------------------------------------------------------

try:
    from src.main import GameState, GameWindow, InputHandler
except ImportError:
    GameState = None  # type: ignore[assignment,misc]
    GameWindow = None  # type: ignore[assignment,misc]
    InputHandler = None  # type: ignore[assignment,misc]

try:
    from src.core.board import Direction, TileMove
except ImportError:
    Direction = None  # type: ignore[assignment,misc]
    TileMove = None  # type: ignore[assignment,misc]

try:
    from src.render.merge_celebration import (
        MergeCelebrationEffect,
        create_effect,
        render_celebration_effects,
    )
except ImportError:
    MergeCelebrationEffect = None  # type: ignore[assignment,misc]
    create_effect = None  # type: ignore[assignment,misc]
    render_celebration_effects = None  # type: ignore[assignment,misc]

# Fix 4 — SpriteCache.  src/render/animation.py should NOT exist yet (TDD red).
try:
    from src.render.animation import SpriteCache
except (ImportError, ModuleNotFoundError):
    SpriteCache = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Helpers (matching test_main.py patterns)
# ---------------------------------------------------------------------------


def _make_mock_surface(width: int = 162, height: int = 162) -> MagicMock:
    """Build a mock pygame.Surface with configurable dimensions."""
    mock = MagicMock()
    mock.get_width.return_value = width
    mock.get_height.return_value = height
    return mock


def _make_mock_assets() -> MagicMock:
    """Build a mock AssetLoader."""
    assets = MagicMock()
    assets.get_tile_sprite.side_effect = lambda *_a, **_kw: _make_mock_surface()
    assets.get_ui_sprite.side_effect = lambda *_a, **_kw: _make_mock_surface()
    return assets


def _make_mock_session(
    board: list[list[int]] | None = None,
    score: int = 0,
    high_score: int = 0,
    can_undo: bool = False,
    game_over: bool = False,
) -> MagicMock:
    """Build a mock GameSession."""
    mock = MagicMock()
    mock.get_board_grid.return_value = board or [[0] * 4 for _ in range(4)]
    mock.get_score.return_value = score
    mock.get_high_score.return_value = high_score
    mock.can_undo.return_value = can_undo
    type(mock).game_over = PropertyMock(return_value=game_over)
    mock.undo.return_value = True
    return mock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def _patch_pygame(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch pygame for headless GameWindow instantiation."""
    monkeypatch.setattr("pygame.init", lambda: (1, 0))
    monkeypatch.setattr(
        "pygame.display.set_mode",
        lambda *a, **kw: _make_mock_surface(700, 800),
    )
    monkeypatch.setattr("pygame.display.set_caption", lambda *a, **kw: None)
    monkeypatch.setattr("pygame.display.flip", lambda: None)
    monkeypatch.setattr("pygame.quit", lambda: None)

    mock_clock = MagicMock()
    mock_clock.tick = MagicMock()
    monkeypatch.setattr("pygame.time.Clock", lambda: mock_clock)
    monkeypatch.setattr("pygame.event.get", lambda: [])


@pytest.fixture()
def window(_patch_pygame: None) -> GameWindow:
    """Create a GameWindow instance for testing (GameWindow | None)."""
    return GameWindow()  # type: ignore[misc]


# ===========================================================================
# Fix 1: Celebration effects wiring
# ===========================================================================


def test_celebration_effects_created_for_merged_moves(
    window: GameWindow,  # type: ignore[misc]
) -> None:
    """Fix 1 AC-1: _handle_keydown creates celebration effects for merged TileMoves.

    When session.move() returns tile_moves with merged=True, a
    MergeCelebrationEffect must be created for the merged destination.
    FAIL REASON: GameWindow has no _celebration_effects attribute and
    _handle_keydown does not import or call create_effect().
    """
    # Build a merged move and a non-merged slide
    merged_tile = MagicMock(spec=TileMove)
    merged_tile.source_row = 0
    merged_tile.source_col = 0
    merged_tile.dest_row = 1
    merged_tile.dest_col = 2
    merged_tile.value = 4
    merged_tile.merged = True

    slide_tile = MagicMock(spec=TileMove)
    slide_tile.source_row = 3
    slide_tile.source_col = 3
    slide_tile.dest_row = 3
    slide_tile.dest_col = 3
    slide_tile.value = 2
    slide_tile.merged = False

    session = _make_mock_session()
    session.move.return_value = MagicMock(
        moved=True,
        tile_moves=[merged_tile, slide_tile],
        new_achievements=[],
        state_transition=None,
    )

    window._session = session  # type: ignore[union-attr]
    window._state = GameState.PLAYING  # type: ignore[misc,union-attr]

    # Patch create_effect at the point-of-use in src.main (_merge_celebration module ref)
    with patch(
        "src.main._merge_celebration.create_effect",
    ) as mock_create_effect:
        mock_effect = MagicMock()
        mock_create_effect.return_value = mock_effect

        window._handle_keydown(Direction.LEFT.value)  # type: ignore[union-attr,misc,arg-type]

        # create_effect should be called once for the merged move only
        mock_create_effect.assert_called_once()
        call_kwargs = mock_create_effect.call_args
        # Support both positional and keyword arg patterns
        actual_row = call_kwargs.kwargs.get("dest_row") or call_kwargs.kwargs.get("row") or (
            call_kwargs.args[0] if call_kwargs.args else None
        )
        actual_col = call_kwargs.kwargs.get("dest_col") or call_kwargs.kwargs.get("col") or (
            call_kwargs.args[1] if len(call_kwargs.args) > 1 else None
        )
        actual_value = call_kwargs.kwargs.get("value") or (
            call_kwargs.args[2] if len(call_kwargs.args) > 2 else None
        )
        assert actual_row == 1
        assert actual_col == 2
        assert actual_value == 4

    # The celebration_effects list on the window should contain one effect
    assert hasattr(window, "_celebration_effects"), (
        "GameWindow must have a _celebration_effects attribute"
    )
    assert len(window._celebration_effects) == 1, (  # type: ignore[union-attr]
        f"Expected 1 celebration effect, got {len(window._celebration_effects)}"  # type: ignore[union-attr]
    )


def test_renderer_called_with_celebration_effects(
    window: GameWindow,  # type: ignore[misc]
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fix 1 AC-2: _render() passes celebration_effects to renderer.render().

    Sets _celebration_effects to a list containing a mock effect, then calls
    _render(). Verifies renderer.render() receives celebration_effects kwarg.
    FAIL REASON: GameWindow has no _celebration_effects and _render does not
    pass celebration_effects to renderer.render().
    """
    mock_effect = MagicMock()
    window._celebration_effects = [mock_effect]  # type: ignore[union-attr,attr-defined]
    window._screen = _make_mock_surface(700, 800)  # type: ignore[union-attr]
    window._assets = _make_mock_assets()  # type: ignore[union-attr]
    window._session = _make_mock_session()  # type: ignore[union-attr]
    window._state = GameState.PLAYING  # type: ignore[misc,union-attr]

    mock_renderer = MagicMock()
    window._renderer = mock_renderer  # type: ignore[union-attr]

    monkeypatch.setattr("pygame.display.flip", lambda: None)

    # Patch update_effects and cleanup_expired_effects at src.main level
    # (these are imported from src.render.merge_celebration into src.main)
    with (
        patch("src.main.update_effects") as mock_update,
        patch("src.main.cleanup_expired_effects") as mock_cleanup,
    ):
        window._render()  # type: ignore[union-attr]

        # renderer.render() must receive celebration_effects kwarg
        assert mock_renderer.render.called, "renderer.render() was not called"
        call_kwargs = mock_renderer.render.call_args.kwargs
        assert "celebration_effects" in call_kwargs, (
            "renderer.render() must receive celebration_effects keyword argument"
        )
        assert call_kwargs["celebration_effects"] == [mock_effect], (
            "celebration_effects must contain the effects passed to renderer"
        )

        # update_effects called once with (effects_list, dt_ms)
        mock_update.assert_called_once()
        update_args = mock_update.call_args[0]
        assert update_args[0] == [mock_effect], (
            "update_effects must receive the celebration effects list"
        )

        # cleanup_expired_effects called once with effects_list
        mock_cleanup.assert_called_once()
        cleanup_args = mock_cleanup.call_args[0]
        assert cleanup_args[0] == [mock_effect], (
            "cleanup_expired_effects must receive the celebration effects list"
        )


def test_celebration_effects_cleared_on_new_game(
    window: GameWindow,  # type: ignore[misc]
) -> None:
    """Fix 1 AC-3: When a new_game action is dispatched, _celebration_effects is cleared.

    Pre-populates _celebration_effects with a mock effect, then triggers the
    new_game action through _handle_keydown.
    FAIL REASON: GameWindow has no _celebration_effects attribute.
    """
    mock_effect = MagicMock()
    window._celebration_effects = [mock_effect]  # type: ignore[union-attr,attr-defined]
    window._session = _make_mock_session()  # type: ignore[union-attr]
    window._state = GameState.GAME_OVER  # type: ignore[misc,union-attr]

    # Trigger new_game action
    # InputHandler.handle_keydown returns {"action": "new_game", "new_state": GameState.IDLE}
    new_game_result = {"action": "new_game", "new_state": GameState.IDLE}
    with patch.object(InputHandler, "handle_keydown", return_value=new_game_result):
        window._handle_keydown(Direction.LEFT.value)  # type: ignore[union-attr,misc,arg-type]

    # _celebration_effects should now be an empty list
    assert window._celebration_effects == [], (  # type: ignore[union-attr,attr-defined]
        f"Expected empty list, got {window._celebration_effects}"  # type: ignore[union-attr,attr-defined]
    )


# ===========================================================================
# Fix 4: SpriteCache with deferred pygame.smoothscale
# ===========================================================================


def test_sprite_cache_smooth_scale() -> None:
    """Fix 4 AC-6: SpriteCache.smooth_scale() calls pygame.transform.smoothscale and caches.

    Creates a SpriteCache, calls smooth_scale(source, (100, 100)), results in
    pygame.transform.smoothscale being called, and returns the result.
    Second call with same args returns cached result without calling smoothscale again.
    FAIL REASON: src/render/animation.py does not exist (ImportError).
    """
    # SpriteCache MUST exist for this test to pass
    import importlib

    try:
        mod = importlib.import_module("src.render.animation")
        cache_cls = getattr(mod, "SpriteCache", None)
    except (ImportError, ModuleNotFoundError):
        pytest.fail(
            "src.render.animation does not exist yet — "
            "SpriteCache with smooth_scale() must be created"
        )

    assert cache_cls is not None, "SpriteCache class not found in src.render.animation"
    cache = cache_cls()

    mock_source = MagicMock()
    mock_scaled = MagicMock()
    with patch("pygame.transform.smoothscale", return_value=mock_scaled) as mock_ss:
        result = cache.smooth_scale(mock_source, (100, 100))
        mock_ss.assert_called_once_with(mock_source, (100, 100))
        assert result is mock_scaled, "smooth_scale should return the scaled surface"

        # Second call — cache hit
        result2 = cache.smooth_scale(mock_source, (100, 100))
        assert result2 is mock_scaled
        assert mock_ss.call_count == 1, (
            "smoothscale should not be called again (cache hit)"
        )

    # cache.clear() empties the cache — next call hits smoothscale again
    cache.clear()
    mock_scaled2 = MagicMock()
    with patch("pygame.transform.smoothscale", return_value=mock_scaled2) as mock_ss2:
        result3 = cache.smooth_scale(mock_source, (100, 100))
        assert result3 is mock_scaled2
        assert mock_ss2.call_count == 1, (
            "smoothscale must be called again after cache.clear()"
        )


def test_sprite_cache_no_pygame_at_import() -> None:
    """Fix 4 AC-7: Importing SpriteCache from src.render.animation does not load pygame at module level.

    Verifies deferred-import pattern: initializing SpriteCache should not
    import pygame at module level.
    FAIL REASON: src/render/animation.py does not exist (ImportError).
    """
    # In red phase, the module doesn't exist — this is the expected failure
    import importlib

    try:
        mod = importlib.import_module("src.render.animation")
    except (ImportError, ModuleNotFoundError):
        # Expected in TDD red phase — this is the actual FAIL
        pytest.fail(
            "src.render.animation does not exist yet — "
            "SpriteCache must be created with deferred pygame import pattern"
        )

    # If we have the module, verify no pygame at import time
    if mod is not None:
        import inspect

        source = inspect.getsource(mod)
        lines = source.split("\n")

        module_level_pygame_imports: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            if stripped.startswith("import pygame") or stripped.startswith(
                "from pygame"
            ):
                if not line[0].isspace():
                    module_level_pygame_imports.append(stripped)

        assert len(module_level_pygame_imports) == 0, (
            f"Found pygame import(s) at module level: {module_level_pygame_imports}. "
            "SpriteCache must use deferred imports to maintain headless test compatibility."
        )
