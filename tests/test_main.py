"""tests/test_main.py — TDD Red Phase tests for GameWindow, GameState, _check_win, and Renderer.get_new_game_button_rect.

Tests the main module (src/main.py) using headless mocking of pygame
surfaces, event queue, display, and the GameSession. Follows the exact
mock pattern established in tests/test_renderer.py.

src/main.py is expected to define:
  - GameState enum: IDLE, PLAYING, GAME_OVER, WIN
  - GameWindow class: __init__, run, _process_events, _handle_keydown,
    _handle_mouse_click, _check_win_condition, _render
  - _check_win(grid) helper function
  - main() entry point

The test also verifies Renderer.get_new_game_button_rect() which is
added to src/render/renderer.py in the same task.

All 23 test cases are collected by pytest even when src/main.py does
not exist yet. Tests naturally reference GameState/GameWindow/_check_win
which are None from the failed import, producing TypeError.

Framework: pytest + unittest.mock. No real pygame.init() or display required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

import pygame
import pytest

# ---------------------------------------------------------------------------
# Module-level imports with graceful fallback
# ---------------------------------------------------------------------------

try:
    from src.main import GameState, GameWindow, InputHandler, _check_win, main
except ImportError:
    GameState = None  # type: ignore[assignment,misc]
    GameWindow = None  # type: ignore[assignment,misc]
    InputHandler = None  # type: ignore[assignment,misc]
    _check_win = None  # type: ignore[assignment,misc]
    main = None  # type: ignore[assignment,misc]

try:
    from src.render.renderer import Renderer
except ImportError:
    Renderer = None  # type: ignore[assignment,misc]

try:
    from src.core.board import Direction
except ImportError:
    Direction = None  # type: ignore[assignment,misc]

try:
    from src.render.toast_manager import ToastManager
except ImportError:
    ToastManager = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


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
    """Build a mock AssetLoader whose get_*_sprite returns distinct mock surfaces.

    Returns:
        MagicMock configured like an AssetLoader with unique return surfaces
        per sprite name/value.
    """
    assets = MagicMock()
    sprite_counter = {"n": 0}

    def _make_sprite(*_args: object, **_kwargs: object) -> MagicMock:
        sprite_counter["n"] += 1
        return _make_mock_surface()

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
    # game_over is a @property — configure it via type(mock)
    type(mock).game_over = PropertyMock(return_value=game_over)
    # move() returns a mock MoveResult with moved=True and empty tile_moves
    mock.move.return_value = MagicMock(moved=True, tile_moves=[], new_achievements=[])
    mock.undo.return_value = True
    return mock


def _make_mock_event(event_type: int, **kwargs: object) -> MagicMock:
    """Build a mock pygame event with given type and attributes.

    Args:
        event_type: pygame event type constant (e.g. pygame.KEYDOWN).
        **kwargs: Attributes to set on the event (key, pos, etc.).

    Returns:
        MagicMock configured to behave like a pygame event.
    """
    event = MagicMock()
    event.type = event_type
    for attr, value in kwargs.items():
        setattr(event, attr, value)
    return event


def _make_key_event(key: int) -> MagicMock:
    """Shortcut for creating a KEYDOWN event.

    Args:
        key: pygame key constant (e.g. pygame.K_UP).

    Returns:
        MagicMock for a KEYDOWN event with the given key.
    """
    return _make_mock_event(pygame.KEYDOWN, key=key)


def _make_click_event(pos: tuple[int, int]) -> MagicMock:
    """Shortcut for creating a MOUSEBUTTONDOWN event.

    Args:
        pos: Click position as (x, y).

    Returns:
        MagicMock for a MOUSEBUTTONDOWN event with the given pos.
    """
    return _make_mock_event(pygame.MOUSEBUTTONDOWN, pos=pos)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def _patch_pygame(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch pygame functions for headless GameWindow instantiation.

    Patches pygame.init, display, clock, and font functions so that
    GameWindow can be created without a real display.
    """
    monkeypatch.setattr(pygame, "init", lambda: (1, 0))
    monkeypatch.setattr(
        pygame.display, "set_mode", lambda *a, **kw: _make_mock_surface(700, 800)
    )
    monkeypatch.setattr(pygame.display, "set_caption", lambda *a, **kw: None)
    monkeypatch.setattr(pygame.display, "flip", lambda: None)
    monkeypatch.setattr(pygame, "quit", lambda: None)

    mock_clock = MagicMock()
    mock_clock.tick = MagicMock()
    monkeypatch.setattr(pygame.time, "Clock", lambda: mock_clock)

    monkeypatch.setattr(pygame.event, "get", lambda: [])


@pytest.fixture()
def window(_patch_pygame: None) -> object:
    """Create a GameWindow instance for testing.

    Returns:
        GameWindow instance with mocked pygame internals.
    """
    return GameWindow()  # type: ignore[misc]


# ===========================================================================
# TC-unit-1: GameState enum has exactly 4 values (AC-8)
# ===========================================================================


def test_game_state_enum_has_exactly_four_values() -> None:
    """TC-unit-1 (AC-8): GameState enum has IDLE, PLAYING, GAME_OVER, WIN."""
    members = list(GameState)  # type: ignore[misc]
    assert len(members) == 4, f"Expected 4 GameState members, got {len(members)}"
    names = {m.name for m in members}
    assert names == {"IDLE", "PLAYING", "GAME_OVER", "WIN"}, (
        f"Unexpected members: {names}"
    )


# ===========================================================================
# TC-unit-2: get_new_game_button_rect returns valid tuple (AC-9)
# ===========================================================================


def test_get_new_game_button_rect_returns_positive_tuple() -> None:
    """TC-unit-2 (AC-9): get_new_game_button_rect() returns (x, y, w, h) of positive ints within window."""
    assets = MagicMock()
    mock_button_sprite = _make_mock_surface(150, 50)
    assets.get_ui_sprite.return_value = mock_button_sprite

    layout = _make_mock_layout()
    layout.board_rect.return_value = (25, 138, 648, 648)
    layout.window_width = 700
    layout.window_height = 800

    renderer = Renderer(assets, layout)  # type: ignore[misc]

    try:
        result = renderer.get_new_game_button_rect()
    except AttributeError:
        pytest.skip("get_new_game_button_rect() not yet implemented on Renderer")

    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    assert len(result) == 4, f"Expected 4 elements, got {len(result)}"
    x, y, w, h = result
    assert all(isinstance(v, int) and v > 0 for v in result), (
        f"All values must be positive ints, got {result}"
    )
    assert x + w <= 700, f"Button right edge {x + w} exceeds window width 700"
    assert y + h <= 800, f"Button bottom edge {y + h} exceeds window height 800"


# ===========================================================================
# TC-functional-1: Arrow key dispatches correct Direction (AC-2)
# ===========================================================================


def test_arrow_key_dispatches_direction_to_move(window: object) -> None:
    """TC-functional-1 (AC-2): Arrow keys call session.move() with correct Direction."""
    session = _make_mock_session()
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.PLAYING  # type: ignore[misc,union-attr]

    key_direction_pairs = [
        (pygame.K_UP, Direction.UP),  # type: ignore[union-attr]
        (pygame.K_DOWN, Direction.DOWN),  # type: ignore[union-attr]
        (pygame.K_LEFT, Direction.LEFT),  # type: ignore[union-attr]
        (pygame.K_RIGHT, Direction.RIGHT),  # type: ignore[union-attr]
    ]

    for key, expected_direction in key_direction_pairs:
        session.move.reset_mock()
        window._handle_keydown(key)  # type: ignore[union-attr]
        session.move.assert_called_once_with(expected_direction)


# ===========================================================================
# TC-functional-2: Escape quits in all states (AC-3)
# ===========================================================================


def test_escape_quits_in_all_states(window: object) -> None:
    """TC-functional-2 (AC-3): Escape key returns True (quit) in all states."""
    for state in [
        GameState.IDLE,
        GameState.PLAYING,
        GameState.GAME_OVER,
        GameState.WIN,
    ]:  # type: ignore[misc]
        window._state = state  # type: ignore[union-attr]
        pygame.event.get = lambda: [_make_key_event(pygame.K_ESCAPE)]  # type: ignore[assignment]
        result = window._process_events()  # type: ignore[union-attr]
        assert result is True, f"Escape should quit in state {state}, got {result}"


# ===========================================================================
# TC-functional-3: Z key calls undo when can_undo is true (AC-4)
# ===========================================================================


def test_z_key_calls_undo_when_can_undo_true(window: object) -> None:
    """TC-functional-3a (AC-4): Z key calls session.undo() when can_undo is True."""
    session = _make_mock_session(can_undo=True)
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.PLAYING  # type: ignore[misc,union-attr]

    window._handle_keydown(pygame.K_z)  # type: ignore[union-attr]
    session.undo.assert_called_once()


def test_z_key_does_not_call_undo_when_can_undo_false(window: object) -> None:
    """TC-functional-3b (AC-4): Z key does NOT call session.undo() when can_undo is False."""
    session = _make_mock_session(can_undo=False)
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.PLAYING  # type: ignore[misc,union-attr]

    window._handle_keydown(pygame.K_z)  # type: ignore[union-attr]
    session.undo.assert_not_called()


# ===========================================================================
# TC-functional-4: New game button click calls session.new_game() (AC-5)
# ===========================================================================


def test_new_game_button_click_calls_new_game(window: object) -> None:
    """TC-functional-4a (AC-5): Click inside button rect calls session.new_game() in GAME_OVER."""
    session = _make_mock_session()
    mock_renderer = MagicMock()
    mock_renderer.get_new_game_button_rect.return_value = (275, 388, 150, 50)

    window._session = session  # type: ignore[union-attr]
    window._renderer = mock_renderer  # type: ignore[union-attr]
    window._state = GameState.GAME_OVER  # type: ignore[misc,union-attr]

    window._handle_mouse_click((350, 410))  # type: ignore[union-attr]
    session.new_game.assert_called_once()
    assert window._state == GameState.IDLE  # type: ignore[misc,union-attr]


def test_click_outside_button_does_nothing(window: object) -> None:
    """TC-functional-4b (AC-5): Click outside button rect does NOT call session.new_game()."""
    session = _make_mock_session()
    mock_renderer = MagicMock()
    mock_renderer.get_new_game_button_rect.return_value = (275, 388, 150, 50)

    window._session = session  # type: ignore[union-attr]
    window._renderer = mock_renderer  # type: ignore[union-attr]
    window._state = GameState.GAME_OVER  # type: ignore[misc,union-attr]

    window._handle_mouse_click((0, 0))  # type: ignore[union-attr]
    session.new_game.assert_not_called()
    assert window._state == GameState.GAME_OVER  # type: ignore[misc,union-attr]


# ===========================================================================
# TC-functional-5: Game-over transition (AC-6)
# ===========================================================================


def test_game_over_transition_after_move(window: object) -> None:
    """TC-functional-5 (AC-6): State transitions to GAME_OVER when session.game_over is True."""
    # Grid with no 2048 tile so win check fails
    grid_no_win = [[1024, 512, 256, 128], [64, 32, 16, 8], [4, 2, 4, 2], [2, 4, 2, 4]]
    session = _make_mock_session(board=grid_no_win, game_over=True)
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.PLAYING  # type: ignore[misc,union-attr]

    window._check_win_condition()  # type: ignore[union-attr]
    assert window._state == GameState.GAME_OVER  # type: ignore[misc,union-attr]


# ===========================================================================
# TC-functional-6: Win detection (AC-7)
# ===========================================================================


def test_win_transition_when_2048_tile_exists(window: object) -> None:
    """TC-functional-6a (AC-7): State transitions to WIN when grid has 2048+."""
    grid_win = [[2048, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    session = _make_mock_session(board=grid_win)
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.PLAYING  # type: ignore[misc,union-attr]

    window._check_win_condition()  # type: ignore[union-attr]
    assert window._state == GameState.WIN  # type: ignore[misc,union-attr]


def test_check_win_returns_true_for_2048() -> None:
    """TC-functional-6b (AC-7): _check_win() returns True when any cell >= 2048."""
    grid = [[2048, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    assert _check_win(grid) is True  # type: ignore[misc]


def test_check_win_returns_true_for_value_above_2048() -> None:
    """TC-functional-6c (AC-7): _check_win() returns True for values above 2048."""
    grid = [[0, 0, 0, 0], [0, 4096, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
    assert _check_win(grid) is True  # type: ignore[misc]


def test_check_win_returns_false_for_no_2048() -> None:
    """TC-functional-6d (AC-7): _check_win() returns False when no cell >= 2048."""
    grid = [[1024, 512, 256, 128], [64, 32, 16, 8], [4, 2, 4, 2], [2, 4, 2, 4]]
    assert _check_win(grid) is False  # type: ignore[misc]


# ===========================================================================
# TC-integration-1: Full render cycle completes without exception
# ===========================================================================


def test_full_render_cycle_no_exception(
    window: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TC-integration-1: _render() calls renderer.render() and display.flip() without error."""
    mock_screen = _make_mock_surface(700, 800)
    window._screen = mock_screen  # type: ignore[union-attr]

    mock_assets = _make_mock_assets()
    window._assets = mock_assets  # type: ignore[union-attr]

    mock_renderer = MagicMock()
    window._renderer = mock_renderer  # type: ignore[union-attr]

    session = _make_mock_session()
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.PLAYING  # type: ignore[misc,union-attr]

    flip_called = {"v": False}

    def _mock_flip() -> None:
        flip_called["v"] = True

    monkeypatch.setattr(pygame.display, "flip", _mock_flip)

    window._render()  # type: ignore[union-attr]
    call_kwargs = mock_renderer.render.call_args.kwargs
    assert call_kwargs["active_moves"] is None
    assert flip_called["v"], "pygame.display.flip() was not called"


# ===========================================================================
# TC-regression-1: No pygame imports in src/core/
# ===========================================================================


def test_no_pygame_imports_in_core() -> None:
    """TC-regression-1: Ensure src/core/ files contain no pygame imports."""
    import os

    core_dir = os.path.join(os.path.dirname(__file__), "..", "src", "core")
    for fname in os.listdir(core_dir):
        if not fname.endswith(".py"):
            continue
        fpath = os.path.join(core_dir, fname)
        with open(fpath) as f:
            content = f.read()
        assert "import pygame" not in content, (
            f"{fname} contains 'import pygame' — pygame must not be imported in src/core/"
        )
        assert "from pygame" not in content, (
            f"{fname} contains 'from pygame' — pygame must not be imported in src/core/"
        )


# ===========================================================================
# TC-regression-2: State guard tests (HIGH-severity coverage gaps from code review)
# ===========================================================================


def test_space_key_starts_new_game_in_game_over(window: object) -> None:
    """TC-regression-2a: Space key triggers new_game and transitions to IDLE from GAME_OVER."""
    session = _make_mock_session()
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.GAME_OVER  # type: ignore[misc,union-attr]

    window._handle_keydown(pygame.K_SPACE)  # type: ignore[union-attr]
    session.new_game.assert_called_once()
    assert window._state == GameState.IDLE  # type: ignore[misc,union-attr]


def test_space_key_starts_new_game_in_win(window: object) -> None:
    """TC-regression-2b: Space key triggers new_game and transitions to IDLE from WIN."""
    session = _make_mock_session()
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.WIN  # type: ignore[misc,union-attr]

    window._handle_keydown(pygame.K_SPACE)  # type: ignore[union-attr]
    session.new_game.assert_called_once()
    assert window._state == GameState.IDLE  # type: ignore[misc,union-attr]


def test_idle_transitions_to_playing_on_first_move(window: object) -> None:
    """TC-regression-2c: First successful keypress moves state from IDLE to PLAYING."""
    session = _make_mock_session()
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.IDLE  # type: ignore[misc,union-attr]

    window._handle_keydown(pygame.K_UP)  # type: ignore[union-attr]
    session.move.assert_called_once()
    assert window._state == GameState.PLAYING  # type: ignore[misc,union-attr]


def test_arrow_key_ignored_in_game_over(window: object) -> None:
    """TC-regression-2d: Arrow key does NOT call move() when state is GAME_OVER."""
    session = _make_mock_session()
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.GAME_OVER  # type: ignore[misc,union-attr]

    window._handle_keydown(pygame.K_UP)  # type: ignore[union-attr]
    session.move.assert_not_called()


def test_arrow_key_ignored_in_win(window: object) -> None:
    """TC-regression-2e: Arrow key does NOT call move() when state is WIN."""
    session = _make_mock_session()
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.WIN  # type: ignore[misc,union-attr]

    window._handle_keydown(pygame.K_UP)  # type: ignore[union-attr]
    session.move.assert_not_called()


def test_space_key_ignored_in_playing(window: object) -> None:
    """TC-regression-2f: Space key does NOT call new_game() when state is PLAYING."""
    session = _make_mock_session()
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.PLAYING  # type: ignore[misc,union-attr]

    window._handle_keydown(pygame.K_SPACE)  # type: ignore[union-attr]
    session.new_game.assert_not_called()


def test_space_key_ignored_in_idle(window: object) -> None:
    """TC-regression-2g: Space key does NOT call new_game() when state is IDLE."""
    session = _make_mock_session()
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.IDLE  # type: ignore[misc,union-attr]

    window._handle_keydown(pygame.K_SPACE)  # type: ignore[union-attr]
    session.new_game.assert_not_called()


def test_undo_ignored_in_non_playing(window: object) -> None:
    """TC-regression-2h: Z key does NOT call undo() when state is IDLE even if can_undo is True."""
    session = _make_mock_session(can_undo=True)
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.IDLE  # type: ignore[misc,union-attr]

    window._handle_keydown(pygame.K_z)  # type: ignore[union-attr]
    session.undo.assert_not_called()


# ===========================================================================
# Sprint 4-2: Achievement Monitoring Integration — TDD Red Phase Tests
# ===========================================================================


def test_handle_keydown_returns_new_achievements() -> None:
    """Sprint 4-2 AC-1: InputHandler.handle_keydown includes new_achievements in move result dict.

    Verifies that the return dict from a move action contains a
    'new_achievements' key with the correct Achievement objects from MoveResult.
    """
    ach1 = MagicMock()
    ach1.name = "First Bite"
    ach1.description = "Perform your first merge"
    ach2 = MagicMock()
    ach2.name = "Cupcake Collector"
    ach2.description = "Reach tile value 32"

    session = _make_mock_session()
    session.move.return_value = MagicMock(
        moved=True, tile_moves=[], new_achievements=[ach1, ach2]
    )

    result = InputHandler.handle_keydown(  # type: ignore[misc]
        key=pygame.K_UP,
        state=GameState.PLAYING,  # type: ignore[misc]
        session=session,
        animation_manager=None,
    )

    assert result is not None, "handle_keydown should return a dict for arrow key moves"
    assert "new_achievements" in result, (
        "Result dict must contain 'new_achievements' key"
    )
    achievements = result["new_achievements"]
    assert len(achievements) == 2, f"Expected 2 achievements, got {len(achievements)}"  # type: ignore[arg-type]
    names = {achievements[0].name, achievements[1].name}  # type: ignore[index]
    assert names == {"First Bite", "Cupcake Collector"}, (
        f"Unexpected achievement names: {names}"
    )


def test_game_window_creates_toast_manager(window: object) -> None:
    """Sprint 4-2 AC-2: GameWindow.__init__ creates self._toast_manager.

    Verifies that the constructor instantiates a ToastManager and stores
    it as self._toast_manager (not None).
    """
    assert hasattr(window, "_toast_manager"), (
        "GameWindow.__init__ must set self._toast_manager attribute"
    )
    assert window._toast_manager is not None, (  # type: ignore[union-attr]
        "GameWindow._toast_manager must be a ToastManager instance, not None"
    )


def test_handle_keydown_enqueues_toasts_for_new_achievements(window: object) -> None:
    """Sprint 4-2 AC-3: GameWindow._handle_keydown calls toast_manager.show for each achievement.

    Verifies that when a move result contains new achievements, the window
    calls toast_manager.show(achievement.name, achievement.description) for each.
    """
    ach1 = MagicMock()
    ach1.name = "First Bite"
    ach1.description = "Perform your first merge"
    ach2 = MagicMock()
    ach2.name = "Cupcake Collector"
    ach2.description = "Reach tile value 32"

    session = _make_mock_session()
    session.move.return_value = MagicMock(
        moved=True, tile_moves=[], new_achievements=[ach1, ach2]
    )
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.PLAYING  # type: ignore[misc,union-attr]

    mock_toast_manager = MagicMock()
    window._toast_manager = mock_toast_manager  # type: ignore[union-attr]

    window._handle_keydown(pygame.K_UP)  # type: ignore[union-attr]

    assert mock_toast_manager.show.call_count == 2, (
        f"toast_manager.show() called {mock_toast_manager.show.call_count} times, expected 2"
    )
    mock_toast_manager.show.assert_any_call("First Bite", "Perform your first merge")
    mock_toast_manager.show.assert_any_call("Cupcake Collector", "Reach tile value 32")


def test_render_calls_toast_update_and_render(
    window: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sprint 4-2 AC-4: GameWindow._render calls toast_manager.update(dt) and render(screen).

    Verifies that _render() invokes toast_manager.update() to advance the timer
    and toast_manager.render(screen) to draw the toast overlay, called after
    board rendering and before display.flip().
    """
    mock_toast_manager = MagicMock()
    window._toast_manager = mock_toast_manager  # type: ignore[union-attr]

    mock_screen = _make_mock_surface(700, 800)
    window._screen = mock_screen  # type: ignore[union-attr]
    window._assets = _make_mock_assets()  # type: ignore[union-attr]
    window._renderer = MagicMock()  # type: ignore[union-attr]
    window._state = GameState.PLAYING  # type: ignore[misc,union-attr]

    monkeypatch.setattr(pygame.display, "flip", lambda: None)

    window._render()  # type: ignore[union-attr]

    mock_toast_manager.update.assert_called_once()
    mock_toast_manager.render.assert_called_once_with(mock_screen)


def test_new_game_clears_toasts(window: object) -> None:
    """Sprint 4-2 AC-6: New game action clears toast_manager.

    Verifies that when action == 'new_game' (Space during GAME_OVER),
    GameWindow._handle_keydown calls self._toast_manager.clear() to reset state.
    """
    mock_toast_manager = MagicMock()
    window._toast_manager = mock_toast_manager  # type: ignore[union-attr]

    session = _make_mock_session()
    window._session = session  # type: ignore[union-attr]
    window._state = GameState.GAME_OVER  # type: ignore[misc,union-attr]

    window._handle_keydown(pygame.K_SPACE)  # type: ignore[union-attr]

    mock_toast_manager.clear.assert_called_once()
