"""tests/test_input_handler.py — Unit tests for InputHandler class.

Tests the stand-alone InputHandler extracted from GameWindow using headless
mocks. InputHandler is implemented in src/main.py and provides input dispatch
for keyboard and mouse events.

These tests validate:
  - Key-to-Direction mapping (get_direction_for_key)
  - Arrow key → session.move() dispatch (handle_keydown)
  - State guards: arrow keys ignored in GAME_OVER/WIN
  - IDLE → PLAYING transition on first move
  - Animation snap during active animation (AC-18)
  - Z key → session.undo() dispatch
  - K_SPACE → session.new_game() dispatch
  - Mouse click → new-game button detection (handle_mouse_click)
  - Mouse click ignored in PLAYING state

Framework: pytest + unittest.mock. No real pygame.init() or display required.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pygame

# ---------------------------------------------------------------------------
# Module-level imports with graceful fallback
# ---------------------------------------------------------------------------

try:
    from src.main import GameState, InputHandler, _check_win
except ImportError:
    GameState = None  # type: ignore[assignment,misc]
    InputHandler = None  # type: ignore[assignment,misc]
    _check_win = None  # type: ignore[assignment,misc]

try:
    from src.core.board import Direction
except ImportError:
    Direction = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _make_mock_session() -> MagicMock:
    """Build a minimal mock GameSession for InputHandler tests.

    Returns:
        MagicMock configured with default move/undo/new_game behavior.
    """
    mock = MagicMock()
    mock.move.return_value = MagicMock(moved=True, tile_moves=[])
    mock.undo.return_value = True
    return mock


# ===========================================================================
# TD-IH-01: test_arrow_key_returns_direction (AC-1, AC-6)
# ===========================================================================


def test_arrow_key_returns_direction() -> None:
    """TD-IH-01 (AC-1, AC-6): All four arrow keys map to correct Direction values.

    Verifies KEY_DIRECTION_MAP class attribute and get_direction_for_key
    static method return the expected Direction for each arrow key constant.
    """
    key_direction_pairs = [
        (pygame.K_UP, Direction.UP),  # type: ignore[union-attr]
        (pygame.K_DOWN, Direction.DOWN),  # type: ignore[union-attr]
        (pygame.K_LEFT, Direction.LEFT),  # type: ignore[union-attr]
        (pygame.K_RIGHT, Direction.RIGHT),  # type: ignore[union-attr]
    ]
    for key, expected in key_direction_pairs:
        result = InputHandler.get_direction_for_key(key)  # type: ignore[misc]
        assert result == expected, f"Key {key} should map to {expected}, got {result}"


# ===========================================================================
# TD-IH-02: test_non_arrow_key_returns_none (AC-6)
# ===========================================================================


def test_non_arrow_key_returns_none() -> None:
    """TD-IH-02 (AC-6): Non-arrow keys return None from get_direction_for_key.

    Tests K_z, K_SPACE, and an arbitrary integer to confirm they all
    return None (not a valid direction).
    """
    for key in [pygame.K_z, pygame.K_SPACE, 9999]:
        result = InputHandler.get_direction_for_key(key)  # type: ignore[misc]
        assert result is None, f"Non-arrow key {key} should return None, got {result}"


# ===========================================================================
# TD-IH-03: test_handle_keydown_arrow_calls_session_move (AC-2)
# ===========================================================================


def test_handle_keydown_arrow_calls_session_move() -> None:
    """TD-IH-03 (AC-2): Arrow key in PLAYING state calls session.move(direction).

    Verifies the correct Direction is dispatched and the result dict
    contains action='move', moved=True, and state_transition=None (since
    no state change happens mid-game for a normal move).
    """
    mock_session = _make_mock_session()
    state = GameState.PLAYING  # type: ignore[misc]

    result = InputHandler.handle_keydown(  # type: ignore[misc]
        pygame.K_UP, state=state, session=mock_session, animation_manager=None
    )

    mock_session.move.assert_called_once_with(Direction.UP)  # type: ignore[union-attr]
    assert result is not None, "Result should not be None for arrow key"
    assert result["action"] == "move"
    assert result["moved"] is True
    assert result["state_transition"] is None


# ===========================================================================
# TD-IH-04: test_handle_keydown_arrow_ignored_in_game_over (AC-2)
# ===========================================================================


def test_handle_keydown_arrow_ignored_in_game_over() -> None:
    """TD-IH-04 (AC-2): Arrow key in GAME_OVER state is ignored — no move called.

    Confirms InputHandler rejects input when the game is over.
    """
    mock_session = _make_mock_session()
    state = GameState.GAME_OVER  # type: ignore[misc]

    result = InputHandler.handle_keydown(  # type: ignore[misc]
        pygame.K_UP, state=state, session=mock_session, animation_manager=None
    )

    mock_session.move.assert_not_called()
    assert result is None, "Arrow key in GAME_OVER should return None"


# ===========================================================================
# TD-IH-05: test_handle_keydown_idle_transitions_to_playing (AC-2)
# ===========================================================================


def test_handle_keydown_idle_transitions_to_playing() -> None:
    """TD-IH-05 (AC-2): First successful move from IDLE produces PLAYING transition.

    The result dict's state_transition field should be GameState.PLAYING
    to signal the caller to change state.
    """
    mock_session = _make_mock_session()
    state = GameState.IDLE  # type: ignore[misc]

    result = InputHandler.handle_keydown(  # type: ignore[misc]
        pygame.K_RIGHT, state=state, session=mock_session, animation_manager=None
    )

    assert result is not None, "Result should not be None for arrow key"
    assert result["state_transition"] == GameState.PLAYING  # type: ignore[misc]


# ===========================================================================
# TD-IH-06: test_handle_keydown_snap_during_animation (AC-18)
# ===========================================================================


def test_handle_keydown_snap_during_animation() -> None:
    """TD-IH-06 (AC-18): snap_to_end() called before session.move() during animation.

    When animation_manager.is_animating() returns True, InputHandler must
    snap the animation to completion before processing the new move.
    Verifies call ordering: snap_to_end before move.
    """
    mock_session = _make_mock_session()
    mock_anim = MagicMock()
    mock_anim.is_animating.return_value = True
    state = GameState.PLAYING  # type: ignore[misc]

    InputHandler.handle_keydown(  # type: ignore[misc]
        pygame.K_UP, state=state, session=mock_session, animation_manager=mock_anim
    )

    mock_anim.snap_to_end.assert_called_once()
    mock_session.move.assert_called_once()
    # Verify ordering: snap_to_end was called before move
    assert mock_anim.snap_to_end.call_count == 1
    assert mock_session.move.call_count == 1


# ===========================================================================
# TD-IH-07: test_handle_keydown_no_snap_when_not_animating (AC-18 negative)
# ===========================================================================


def test_handle_keydown_no_snap_when_not_animating() -> None:
    """TD-IH-07 (AC-18 negative): snap_to_end NOT called when not animating.

    When animation_manager exists but is_animating() is False,
    snap_to_end should not be called. session.move() still proceeds.
    """
    mock_session = _make_mock_session()
    mock_anim = MagicMock()
    mock_anim.is_animating.return_value = False
    state = GameState.PLAYING  # type: ignore[misc]

    InputHandler.handle_keydown(  # type: ignore[misc]
        pygame.K_UP, state=state, session=mock_session, animation_manager=mock_anim
    )

    mock_anim.snap_to_end.assert_not_called()
    mock_session.move.assert_called_once_with(Direction.UP)  # type: ignore[union-attr]


# ===========================================================================
# TD-IH-08: test_handle_keydown_z_calls_undo (AC-3)
# ===========================================================================


def test_handle_keydown_z_calls_undo() -> None:
    """TD-IH-08 (AC-3): Z key in PLAYING calls session.undo() when can_undo is True.

    Verifies undo is dispatched and result dict has action='undo'.
    """
    mock_session = _make_mock_session()
    mock_session.can_undo.return_value = True
    state = GameState.PLAYING  # type: ignore[misc]

    result = InputHandler.handle_keydown(  # type: ignore[misc]
        pygame.K_z, state=state, session=mock_session, animation_manager=None
    )

    mock_session.undo.assert_called_once()
    assert result is not None, "Result should not be None for Z key"
    assert result["action"] == "undo"


# ===========================================================================
# TD-IH-09: test_handle_keydown_space_starts_new_game (AC-4)
# ===========================================================================


def test_handle_keydown_space_starts_new_game() -> None:
    """TD-IH-09 (AC-4): K_SPACE in GAME_OVER calls session.new_game().

    Verifies new_game dispatch and result dict includes action='new_game'
    and new_state=GameState.IDLE.
    """
    mock_session = _make_mock_session()
    state = GameState.GAME_OVER  # type: ignore[misc]

    result = InputHandler.handle_keydown(  # type: ignore[misc]
        pygame.K_SPACE, state=state, session=mock_session, animation_manager=None
    )

    mock_session.new_game.assert_called_once()
    assert result is not None, "Result should not be None for SPACE key"
    assert result["action"] == "new_game"
    assert result["new_state"] == GameState.IDLE  # type: ignore[misc]


# ===========================================================================
# TD-IH-10: test_handle_mouse_click_inside_button (AC-5)
# ===========================================================================


def test_handle_mouse_click_inside_button() -> None:
    """TD-IH-10 (AC-5): Click inside new-game button rect returns True in GAME_OVER.

    Point (350, 410) is inside the button rect (275, 388, 150, 50).
    """
    mock_renderer = MagicMock()
    mock_renderer.get_new_game_button_rect.return_value = (275, 388, 150, 50)
    state = GameState.GAME_OVER  # type: ignore[misc]

    result = InputHandler.handle_mouse_click(  # type: ignore[misc]
        (350, 410), state=state, renderer=mock_renderer
    )

    assert result is True, "Click inside button should return True"


# ===========================================================================
# TD-IH-11: test_handle_mouse_click_outside_button (AC-5)
# ===========================================================================


def test_handle_mouse_click_outside_button() -> None:
    """TD-IH-11 (AC-5): Click outside new-game button rect returns False in GAME_OVER.

    Point (0, 0) is outside the button rect (275, 388, 150, 50).
    """
    mock_renderer = MagicMock()
    mock_renderer.get_new_game_button_rect.return_value = (275, 388, 150, 50)
    state = GameState.GAME_OVER  # type: ignore[misc]

    result = InputHandler.handle_mouse_click(  # type: ignore[misc]
        (0, 0), state=state, renderer=mock_renderer
    )

    assert result is False, "Click outside button should return False"


# ===========================================================================
# TD-IH-12: test_handle_mouse_click_ignored_in_playing (AC-5)
# ===========================================================================


def test_handle_mouse_click_ignored_in_playing() -> None:
    """TD-IH-12 (AC-5): Mouse click ignored in PLAYING state — button not even checked.

    Confirms handle_mouse_click returns False without calling
    renderer.get_new_game_button_rect() when state is PLAYING.
    """
    mock_renderer = MagicMock()
    mock_renderer.get_new_game_button_rect.return_value = (275, 388, 150, 50)
    state = GameState.PLAYING  # type: ignore[misc]

    result = InputHandler.handle_mouse_click(  # type: ignore[misc]
        (350, 410), state=state, renderer=mock_renderer
    )

    assert result is False, "Click in PLAYING state should return False"
    mock_renderer.get_new_game_button_rect.assert_not_called()
