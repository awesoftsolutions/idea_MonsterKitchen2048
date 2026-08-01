"""tests/test_state_manager.py — Unit tests for StateManager class.

Tests the stand-alone StateManager extracted from GameWindow using headless
mocks. StateManager is implemented in src/main.py and owns the GameState
lifecycle (transitions, win/lose conditions, input-allowed guards).

These tests validate:
  - Default initial state is IDLE (AC-7)
  - Custom initial state accepted (AC-7)
  - transition_to unconditionally changes state (AC-8)
  - check_win_condition → WIN when grid has 2048+ (AC-9)
  - check_win_condition → GAME_OVER when session.game_over and no 2048 (AC-10)
  - check_win_condition is no-op when not PLAYING (AC-9 negative)
  - is_input_allowed for all 4 states (AC-11)
  - is_new_game_allowed for all 4 states (AC-12)
  - is_undo_allowed for all 4 states (AC-13)

Framework: pytest + unittest.mock. No real pygame.init() or display required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

# ---------------------------------------------------------------------------
# Module-level imports with graceful fallback
# ---------------------------------------------------------------------------

try:
    from src.main import GameState, StateManager, _check_win
except ImportError:
    GameState = None  # type: ignore[assignment,misc]
    StateManager = None  # type: ignore[assignment,misc]
    _check_win = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


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
    return mock


# Test grids
_WIN_GRID: list[list[int]] = [[2048, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
_NO_WIN_GRID: list[list[int]] = [
    [1024, 512, 256, 128],
    [64, 32, 16, 8],
    [4, 2, 4, 2],
    [2, 4, 2, 4],
]


# ===========================================================================
# TD-SM-01: test_initial_state_is_idle (AC-7)
# ===========================================================================


def test_initial_state_is_idle() -> None:
    """TD-SM-01 (AC-7): Default constructor produces IDLE state.

    Verifies the StateManager initializes to GameState.IDLE when no
    initial_state argument is provided.
    """
    sm = StateManager()  # type: ignore[misc]
    assert sm.state == GameState.IDLE, f"Expected IDLE, got {sm.state}"


# ===========================================================================
# TD-SM-02: test_custom_initial_state (AC-7)
# ===========================================================================


def test_custom_initial_state() -> None:
    """TD-SM-02 (AC-7): Constructor with initial_state=PLAYING produces PLAYING state.

    Verifies the StateManager accepts a custom initial state.
    """
    sm = StateManager(initial_state=GameState.PLAYING)  # type: ignore[misc]
    assert sm.state == GameState.PLAYING, f"Expected PLAYING, got {sm.state}"


# ===========================================================================
# TD-SM-03: test_transition_to_changes_state (AC-8)
# ===========================================================================


def test_transition_to_changes_state() -> None:
    """TD-SM-03 (AC-8): transition_to unconditionally changes state.

    Verifies successive calls to transition_to update the state property.
    """
    sm = StateManager()  # type: ignore[misc]

    sm.transition_to(GameState.PLAYING)  # type: ignore[misc]
    assert sm.state == GameState.PLAYING, (
        f"Expected PLAYING after first transition, got {sm.state}"
    )

    sm.transition_to(GameState.GAME_OVER)  # type: ignore[misc]
    assert sm.state == GameState.GAME_OVER, (
        f"Expected GAME_OVER after second transition, got {sm.state}"
    )


# ===========================================================================
# TD-SM-04: test_check_win_condition_transitions_to_win (AC-9)
# ===========================================================================


def test_check_win_condition_transitions_to_win() -> None:
    """TD-SM-04 (AC-9): check_win_condition transitions to WIN when grid has 2048+.

    Sets StateManager to PLAYING, then calls check_win_condition with
    a session whose grid contains a 2048 tile.
    """
    sm = StateManager(initial_state=GameState.PLAYING)  # type: ignore[misc]
    mock_session = _make_mock_session(board=_WIN_GRID, game_over=False)

    sm.check_win_condition(mock_session)  # type: ignore[misc]

    assert sm.state == GameState.WIN, f"Expected WIN, got {sm.state}"


# ===========================================================================
# TD-SM-05: test_check_win_condition_transitions_to_game_over (AC-10)
# ===========================================================================


def test_check_win_condition_transitions_to_game_over() -> None:
    """TD-SM-05 (AC-10): check_win_condition transitions to GAME_OVER when no 2048 and game_over.

    Sets StateManager to PLAYING, then calls check_win_condition with
    a session whose grid has no 2048 tile but game_over is True.
    """
    sm = StateManager(initial_state=GameState.PLAYING)  # type: ignore[misc]
    mock_session = _make_mock_session(board=_NO_WIN_GRID, game_over=True)

    sm.check_win_condition(mock_session)  # type: ignore[misc]

    assert sm.state == GameState.GAME_OVER, f"Expected GAME_OVER, got {sm.state}"


# ===========================================================================
# TD-SM-06: test_check_win_condition_noop_in_non_playing (AC-9 negative)
# ===========================================================================


def test_check_win_condition_noop_in_non_playing() -> None:
    """TD-SM-06 (AC-9 negative): check_win_condition is no-op when state is not PLAYING.

    Even though the session has a win grid and game_over=True, the
    StateManager should remain IDLE because it was never in PLAYING state.
    """
    sm = StateManager()  # type: ignore[misc]
    mock_session = _make_mock_session(board=_WIN_GRID, game_over=True)

    sm.check_win_condition(mock_session)  # type: ignore[misc]

    assert sm.state == GameState.IDLE, f"Expected IDLE (unchanged), got {sm.state}"


# ===========================================================================
# TD-SM-07: test_is_input_allowed (AC-11)
# ===========================================================================


def test_is_input_allowed() -> None:
    """TD-SM-07 (AC-11): is_input_allowed returns True for IDLE and PLAYING, False otherwise.

    Tests all four GameState values to ensure input is only accepted
    during active gameplay.
    """
    sm = StateManager()  # type: ignore[misc]

    expected = {
        GameState.IDLE: True,  # type: ignore[misc]
        GameState.PLAYING: True,  # type: ignore[misc]
        GameState.GAME_OVER: False,  # type: ignore[misc]
        GameState.WIN: False,  # type: ignore[misc]
    }

    for state, should_allow in expected.items():
        sm.transition_to(state)  # type: ignore[misc]
        result = sm.is_input_allowed()  # type: ignore[misc]
        assert result == should_allow, (
            f"is_input_allowed() for {state} should be {should_allow}, got {result}"
        )


# ===========================================================================
# TD-SM-08: test_is_new_game_allowed (AC-12)
# ===========================================================================


def test_is_new_game_allowed() -> None:
    """TD-SM-08 (AC-12): is_new_game_allowed returns True for GAME_OVER and WIN only.

    Tests all four GameState values to ensure new game is only allowed
    in terminal states.
    """
    sm = StateManager()  # type: ignore[misc]

    expected = {
        GameState.IDLE: False,  # type: ignore[misc]
        GameState.PLAYING: False,  # type: ignore[misc]
        GameState.GAME_OVER: True,  # type: ignore[misc]
        GameState.WIN: True,  # type: ignore[misc]
    }

    for state, should_allow in expected.items():
        sm.transition_to(state)  # type: ignore[misc]
        result = sm.is_new_game_allowed()  # type: ignore[misc]
        assert result == should_allow, (
            f"is_new_game_allowed() for {state} should be {should_allow}, got {result}"
        )


# ===========================================================================
# TD-SM-09: test_is_undo_allowed (AC-13)
# ===========================================================================


def test_is_undo_allowed() -> None:
    """TD-SM-09 (AC-13): is_undo_allowed returns True only for PLAYING.

    Tests all four GameState values to ensure undo is only allowed
    during active gameplay.
    """
    sm = StateManager()  # type: ignore[misc]

    expected = {
        GameState.IDLE: False,  # type: ignore[misc]
        GameState.PLAYING: True,  # type: ignore[misc]
        GameState.GAME_OVER: False,  # type: ignore[misc]
        GameState.WIN: False,  # type: ignore[misc]
    }

    for state, should_allow in expected.items():
        sm.transition_to(state)  # type: ignore[misc]
        result = sm.is_undo_allowed()  # type: ignore[misc]
        assert result == should_allow, (
            f"is_undo_allowed() for {state} should be {should_allow}, got {result}"
        )
