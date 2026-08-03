# Contract: test_sprint_4_2_rem.py
# Purpose:     Validation tests for Sprint 4-2 MergeCelebrationEffect game loop wiring.
#              5 integration tests covering create, update, render pass-through,
#              keyboard new_game clear, and mouse new_game clear.
# System:      pytest suite (tests/).  No pygame at import time.
# Dependencies: pytest, unittest.mock, src.main, src.render.merge_celebration
# Used-by:     CI pipeline, Sprint 4-2 validation acceptance
# ---------------------------------------------------------------------------

"""Tests for Sprint 4-2 MergeCelebrationEffect game loop wiring (validation).

Five integration tests verify the complete lifecycle of celebration effects:

1. test_celebration_effects_created_on_merge (AC-1):
   When a move produces TileMoves with merged=True,
   create_effect(dest_row, dest_col, value) is called.
   Only merged moves trigger effect creation; slides are skipped.

2. test_celebration_effects_updated_each_frame (AC-2):
   When _render() is called each frame,
   update_effects(effects, dt_ms) and cleanup_expired_effects(effects) are called.

3. test_celebration_effects_passed_to_renderer (AC-3):
   When Renderer.render() is called from _render(),
   celebration_effects=self._celebration_effects is passed as a keyword argument.

4. test_celebration_effects_cleared_on_new_game (AC-4):
   When new_game is triggered via keyboard (action=="new_game"),
   self._celebration_effects is cleared to an empty list.

5. test_celebration_effects_cleared_on_mouse_new_game (AC-5):
   When new_game is triggered via mouse click (should_start_new_game=True),
   self._celebration_effects is cleared to an empty list.

Framework: pytest + unittest.mock. No pygame.init() or display required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock, patch

import pytest

# ---------------------------------------------------------------------------
# Module-level imports with graceful fallback
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


# ---------------------------------------------------------------------------
# Helpers (matching test_sprint_4_2_remediation.py patterns)
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
    mock.move.return_value = MagicMock(
        moved=True,
        tile_moves=[],
        new_achievements=[],
        state_transition=None,
    )
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
    """Create a GameWindow instance for testing."""
    return GameWindow()  # type: ignore[misc]


# ===========================================================================
# Validation tests for MergeCelebrationEffect game loop wiring
# ===========================================================================


def test_celebration_effects_created_on_merge(
    window: GameWindow,  # type: ignore[misc]
) -> None:
    """AC-1: _handle_keydown creates celebration effects for merged TileMoves.

    When session.move() returns tile_moves with merged=True, a
    MergeCelebrationEffect must be created for the merged destination.
    The non-merged slide_tile must NOT trigger create_effect.
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
        call_args = mock_create_effect.call_args
        # Production code passes positional args: create_effect(dest_row, dest_col, value)
        assert call_args.args[0] == 1, f"Expected dest_row=1, got {call_args.args[0]}"
        assert call_args.args[1] == 2, f"Expected dest_col=2, got {call_args.args[1]}"
        assert call_args.args[2] == 4, f"Expected value=4, got {call_args.args[2]}"

    # The celebration_effects list on the window should contain one effect
    assert hasattr(window, "_celebration_effects"), (
        "GameWindow must have a _celebration_effects attribute"
    )
    assert len(window._celebration_effects) == 1, (  # type: ignore[union-attr]
        f"Expected 1 celebration effect, got {len(window._celebration_effects)}"  # type: ignore[union-attr]
    )


def test_celebration_effects_updated_each_frame(
    window: GameWindow,  # type: ignore[misc]
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-2: _render() calls update_effects and cleanup_expired_effects each frame.

    Places a mock effect on the window, calls _render(), and verifies that
    update_effects and cleanup_expired_effects are each called once with the
    effects list as the first positional argument.
    """
    mock_effect = MagicMock()
    window._celebration_effects = [mock_effect]  # type: ignore[union-attr,attr-defined]
    window._screen = _make_mock_surface(700, 800)  # type: ignore[union-attr,attr-defined]
    window._assets = _make_mock_assets()  # type: ignore[union-attr,attr-defined]
    window._session = _make_mock_session()  # type: ignore[union-attr,attr-defined]
    window._state = GameState.PLAYING  # type: ignore[misc,union-attr]
    window._renderer = MagicMock()  # type: ignore[union-attr,attr-defined]

    monkeypatch.setattr("pygame.display.flip", lambda: None)

    # Patch update_effects and cleanup_expired_effects at src.main level
    # (these are imported from src.render.merge_celebration into src.main)
    with (
        patch("src.main.update_effects") as mock_update,
        patch("src.main.cleanup_expired_effects") as mock_cleanup,
    ):
        window._render()  # type: ignore[union-attr]

        # update_effects called once with (effects_list, dt_ms)
        mock_update.assert_called_once()
        update_args = mock_update.call_args[0]
        assert update_args[0] == [mock_effect], (
            "update_effects must receive the celebration effects list"
        )
        assert isinstance(update_args[1], float), (
            "update_effects second arg must be dt_ms (float)"
        )

        # cleanup_expired_effects called once with effects_list
        mock_cleanup.assert_called_once()
        cleanup_args = mock_cleanup.call_args[0]
        assert cleanup_args[0] == [mock_effect], (
            "cleanup_expired_effects must receive the celebration effects list"
        )


def test_celebration_effects_passed_to_renderer(
    window: GameWindow,  # type: ignore[misc]
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-3: _render() passes celebration_effects to renderer.render().

    Sets _celebration_effects to a list containing a mock effect, calls
    _render(), and verifies renderer.render() receives celebration_effects
    as a keyword argument matching the same list object.
    """
    mock_effect = MagicMock()
    window._celebration_effects = [mock_effect]  # type: ignore[union-attr,attr-defined]
    window._screen = _make_mock_surface(700, 800)  # type: ignore[union-attr,attr-defined]
    window._assets = _make_mock_assets()  # type: ignore[union-attr,attr-defined]
    window._session = _make_mock_session()  # type: ignore[union-attr,attr-defined]
    window._state = GameState.PLAYING  # type: ignore[misc,union-attr]

    mock_renderer = MagicMock()
    window._renderer = mock_renderer  # type: ignore[union-attr,attr-defined]

    monkeypatch.setattr("pygame.display.flip", lambda: None)

    # Patch update/cleanup at src.main level so they don't call real code
    with (
        patch("src.main.update_effects"),
        patch("src.main.cleanup_expired_effects"),
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


def test_celebration_effects_cleared_on_new_game(
    window: GameWindow,  # type: ignore[misc]
) -> None:
    """AC-4: When a new_game action is dispatched via keyboard, effects are cleared.

    Pre-populates _celebration_effects with a mock effect, then triggers the
    new_game action through _handle_keydown. Verifies the list is now empty.
    """
    mock_effect = MagicMock()
    window._celebration_effects = [mock_effect]  # type: ignore[union-attr,attr-defined]
    window._session = _make_mock_session()  # type: ignore[union-attr,attr-defined]
    window._state = GameState.GAME_OVER  # type: ignore[misc,union-attr]

    # Trigger new_game action via InputHandler return
    new_game_result = {"action": "new_game", "new_state": GameState.IDLE}
    with patch.object(InputHandler, "handle_keydown", return_value=new_game_result):
        window._handle_keydown(Direction.LEFT.value)  # type: ignore[union-attr,misc,arg-type]

    # _celebration_effects should now be an empty list
    assert window._celebration_effects == [], (  # type: ignore[union-attr]
        f"Expected empty list, got {window._celebration_effects}"  # type: ignore[union-attr]
    )


def test_celebration_effects_cleared_on_mouse_new_game(
    window: GameWindow,  # type: ignore[misc]
) -> None:
    """AC-5: When a new_game is triggered via mouse click, effects are cleared.

    Pre-populates _celebration_effects with two mock effects, then triggers
    a mouse click that starts a new game. Verifies:
    - _celebration_effects is empty
    - session.new_game() was called
    - state transitioned to IDLE
    """
    window._celebration_effects = [MagicMock(), MagicMock()]  # type: ignore[union-attr,attr-defined]
    window._session = _make_mock_session()  # type: ignore[union-attr,attr-defined]
    window._state = GameState.GAME_OVER  # type: ignore[misc,union-attr]
    window._renderer = MagicMock()  # type: ignore[union-attr,attr-defined]

    # InputHandler.handle_mouse_click returns True -> triggers new game
    with patch.object(InputHandler, "handle_mouse_click", return_value=True):
        window._handle_mouse_click(pos=(350, 750))  # type: ignore[union-attr]

    # _celebration_effects should now be an empty list
    assert window._celebration_effects == [], (  # type: ignore[union-attr]
        f"Expected empty list, got {window._celebration_effects}"  # type: ignore[union-attr]
    )
    # session.new_game() should have been called
    window._session.new_game.assert_called_once()  # type: ignore[union-attr]
    # State should have transitioned to IDLE
    assert window._state == GameState.IDLE  # type: ignore[misc,union-attr]
