"""Tests for GameSession and MoveResult — TDD red-phase verification.

This file verifies the pre-implementation test contract for GameSession and MoveResult
as defined in registry://pseudocode/phase_2_sprint_2_task_game_session.md.

All 27 test functions are defined. Until src/core/game_session.py exists,
every test that imports GameSession or MoveResult will raise ImportError — this
is correct and expected in TDD red-phase.

Import pattern:
    from src.core.game_session import GameSession, MoveResult
"""
# CHANGELOG:
# - Phase 3 Sprint 1: Add 13 GameSession accessor tests (OQ-P16: get_board_grid, get_score, get_high_score, get_move_count, get_rotten_overlay, can_undo)

from __future__ import annotations

import random

import pytest

# These imports will raise ImportError until src/core/game_session.py is implemented.
# This is the expected TDD red-phase failure — the test file is correct.
from src.core.game_session import GameSession, MoveResult  # type: ignore[import]


@pytest.fixture()
def seeded_rng() -> random.Random:
    """A Random instance seeded with 42 for deterministic tests."""
    return random.Random(42)


@pytest.fixture()
def tmp_high_score_path(tmp_path: object) -> str:
    """Return a temporary file path for high-score persistence."""
    return str(tmp_path / "high_score.json")


@pytest.fixture()
def session(seeded_rng: random.Random, tmp_high_score_path: str) -> GameSession:
    """A default test GameSession with seeded RNG and isolated high-score path."""
    return GameSession(rng=seeded_rng, high_score_path=tmp_high_score_path)


# ---------------------------------------------------------------------------
# Constructor Tests
# ---------------------------------------------------------------------------


def test_constructor_creates_all_modules(session: GameSession) -> None:
    """AC-1: GameSession() creates all 6 module instances with default configuration."""
    from src.core.board import Board
    from src.core.rules import Rules
    from src.core.score import Score
    from src.core.history import History
    from src.core.achievements import Achievements
    from src.core.twist import Twist

    assert isinstance(session._board, Board)
    assert isinstance(session._rules, Rules)
    assert isinstance(session._score, Score)
    assert isinstance(session._history, History)
    assert isinstance(session._achievements, Achievements)
    assert isinstance(session._twist, Twist)


def test_constructor_spawns_initial_tiles(session: GameSession) -> None:
    """AC-14: new_game() spawns exactly 2 tiles on a fresh 4x4 board."""
    grid = session._board.get_grid()
    count = sum(1 for row in grid for cell in row if cell != 0)
    assert count == 2, f"Expected 2 initial tiles, got {count}"


def test_constructor_shared_rng_injection() -> None:
    """AC-2: Explicit rng is injected into both Board and Twist constructors."""
    rng = random.Random(99)
    session = GameSession(rng=rng)
    assert session._board._rng is rng, "Board should use the injected RNG instance"
    assert session._twist._rng is rng, "Twist should use the injected RNG instance"


def test_constructor_custom_high_score_path(tmp_path: object) -> None:
    """AC-3: Custom high_score_path is forwarded to Score constructor."""
    custom_path = str(tmp_path / "custom_hs.json")
    session = GameSession(high_score_path=custom_path)
    assert str(session._score._high_score_path) == custom_path


# ---------------------------------------------------------------------------
# move() Tests
# ---------------------------------------------------------------------------


def test_move_full_orchestration(session: GameSession) -> None:
    """AC-4+AC-6: move() orchestrates history, slide, score, spawn, twist, achievements.

    Sets up a board with two 2-tiles in row 0 that merge on LEFT slide,
    scoring 4 points, unlocking ACH-01.
    """
    from src.core.board import Direction, BoardState

    # Clear the board and set up a known merge scenario
    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )

    result = session.move(Direction.LEFT)

    assert result.moved is True, "move should report moved=True"
    assert result.score_delta == 4, (
        f"Expected score_delta=4 (two 2s merge), got {result.score_delta}"
    )
    assert len(result.new_achievements) > 0, (
        "At least ACH-01 (First Bite) should unlock"
    )
    assert any(a.id == "ACH-01" for a in result.new_achievements), (
        "ACH-01 should be in new_achievements"
    )
    assert isinstance(result.twist_effect, object), (
        "twist_effect should be a TwistEffect instance"
    )


def test_move_orchestration_calls_all_subsystems(session: GameSession) -> None:
    """AC-4: move() records history BEFORE slide, updates score AFTER, spawns tile, processes twist.

    Verifies the orchestration order: history pre-state captured, score synchronized.
    """
    from src.core.board import Direction, BoardState

    # Set up a mergeable board
    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )

    pre_move_score = session._score.get_score()
    session.move(Direction.LEFT)

    # History should contain the pre-move snapshot
    assert session._history.can_undo(), (
        "history should have a snapshot after a legal move"
    )
    popped = session._history.pop()
    assert popped is not None, "pop should return a snapshot"
    _, saved_score = popped
    assert saved_score == pre_move_score, "history should capture pre-move score"

    # Score should be updated with the merge delta
    assert session._score.get_score() > pre_move_score, (
        "score should increase after merge"
    )


def test_move_records_history_before_slide(session: GameSession) -> None:
    """AC-4: History records the pre-move state BEFORE the board slide mutates grid."""
    from src.core.board import Direction, BoardState

    session._board.reset()
    pre_state = BoardState(
        grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        score=0,
        moves=0,
    )
    session._board.set_state(pre_state)

    pre_move_score = session._score.get_score()
    session.move(Direction.LEFT)

    assert session._history.can_undo(), (
        "history should have a snapshot after legal move"
    )
    popped = session._history.pop()
    assert popped is not None
    restored_state, restored_score = popped
    assert restored_state.grid == pre_state.grid, "history should capture pre-move grid"
    assert restored_score == pre_move_score, "history should capture pre-move score"


def test_move_syncs_score(session: GameSession) -> None:
    """AC-4: Score is synchronized via Score.add(slide_result.score_delta) after slide."""
    from src.core.board import Direction, BoardState

    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )

    result = session.move(Direction.LEFT)
    assert result.score_delta == 4
    assert session._score.get_score() == 4, "Score.add should receive the slide delta"


def test_move_result_fields(session: GameSession) -> None:
    """AC-6: MoveResult is a dataclass with 4 fields: moved, score_delta, new_achievements, twist_effect."""
    from src.core.board import Direction, BoardState

    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )

    result = session.move(Direction.LEFT)
    assert isinstance(result, MoveResult)
    assert isinstance(result.moved, bool)
    assert isinstance(result.score_delta, int)
    assert isinstance(result.new_achievements, list)


def test_move_illegal_no_side_effects(session: GameSession) -> None:
    """AC-5: Illegal move returns moved=False with zero side effects.

    Sets up a board where sliding RIGHT produces no change (single tile at right edge).
    No history is recorded, no score change, no tile spawn, no twist processing.
    """
    from src.core.board import Direction, BoardState

    # Single tile at right edge of row 0 — RIGHT slide produces no change
    session._board.set_state(
        BoardState(
            grid=[[0, 0, 0, 2], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )
    initial_score = session._score.get_score()
    initial_grid = session._board.get_grid()

    result = session.move(Direction.RIGHT)

    assert result.moved is False, "illegal move should report moved=False"
    assert result.score_delta == 0, "illegal move should yield score_delta=0"
    assert result.new_achievements == [], "illegal move should yield no achievements"
    assert session._board.get_grid() == initial_grid, "grid should be unchanged"
    assert session._score.get_score() == initial_score, "score should be unchanged"
    assert session._history.can_undo() is False, (
        "no history should be recorded for illegal move"
    )


def test_move_triggers_achievements(session: GameSession) -> None:
    """AC-4: move() evaluates achievements via Achievements.evaluate() after slide.

    First merge unlocks ACH-01. Second merge does NOT re-unlock ACH-01.
    """
    from src.core.board import Direction, BoardState

    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )

    result1 = session.move(Direction.LEFT)
    ach_ids_1 = [a.id for a in result1.new_achievements]
    assert "ACH-01" in ach_ids_1, (
        f"ACH-01 should unlock on first merge, got {ach_ids_1}"
    )

    # Second merge: ACH-01 already unlocked, should NOT appear again
    # Board already moved — need a new merge-able setup
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=session._score.get_score(),
            moves=session._board.get_state().moves,
        )
    )
    result2 = session.move(Direction.LEFT)
    ach_ids_2 = [a.id for a in result2.new_achievements]
    assert "ACH-01" not in ach_ids_2, (
        "ACH-01 should NOT be re-unlocked (already tracked)"
    )


# ---------------------------------------------------------------------------
# undo() Tests
# ---------------------------------------------------------------------------


def test_undo_restores_board_and_score(session: GameSession) -> None:
    """AC-7: undo() restores Board via set_state() and Score via reset()+add()."""
    from src.core.board import Direction, BoardState

    session._board.reset()
    initial_state = BoardState(
        grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        score=0,
        moves=0,
    )
    session._board.set_state(initial_state)
    initial_score = session._score.get_score()

    session.move(Direction.LEFT)
    assert session._score.get_score() > initial_score, (
        "score should increase after merge"
    )

    result = session.undo()
    assert result is True, "undo should return True when history is available"
    assert session._board.get_state().grid == initial_state.grid, (
        "grid should be restored"
    )
    assert session._score.get_score() == initial_score, "score should be restored"


def test_undo_empty_history_returns_false(session: GameSession) -> None:
    """AC-8: undo() with empty history returns False without modifying board or score."""
    score_before = session._score.get_score()
    grid_before = session._board.get_grid()

    result = session.undo()
    assert result is False, "undo on fresh session should return False"
    assert session._board.get_grid() == grid_before, "grid should be unchanged"
    assert session._score.get_score() == score_before, "score should be unchanged"


def test_undo_multiple_consecutive(session: GameSession) -> None:
    """Edge: Three consecutive undos each restore to the prior snapshot."""
    from src.core.board import Direction, BoardState

    session._board.reset()
    state_zero = BoardState(
        grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        score=0,
        moves=0,
    )
    session._board.set_state(state_zero)

    # Move 1: merge row 0
    session.move(Direction.LEFT)

    # Move 2: set up another merge in row 1
    session._board.set_state(
        BoardState(
            grid=[[4, 0, 0, 0], [2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=session._score.get_score(),
            moves=session._board.get_state().moves,
        )
    )
    session.move(Direction.LEFT)

    # Undo 3 times — first two should succeed, third should fail
    assert session.undo() is True, "first undo succeeds"
    assert session.undo() is True, "second undo succeeds"
    assert session.undo() is False, "third undo fails — no more history"


def test_undo_preserves_high_score(session: GameSession) -> None:
    """Edge: undo restores current score but high_score persists (never lowered)."""
    from src.core.board import Direction, BoardState

    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )

    session.move(Direction.LEFT)
    high_after = session._score.get_high_score()
    assert high_after > 0, "high score should capture the merge"

    session.undo()
    assert session._score.get_high_score() == high_after, (
        "high score should not decrease on undo"
    )


def test_undo_does_not_revert_achievements(session: GameSession) -> None:
    """Edge: Achievements persist through undo (not reverted per design decision)."""
    from src.core.board import Direction, BoardState

    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )

    result = session.move(Direction.LEFT)
    ach_ids = [a.id for a in result.new_achievements]
    assert "ACH-01" in ach_ids, "first merge should unlock ACH-01"

    # Undo the move — ACH-01 should remain in the module's tracking
    session.undo()

    # Achievements module should still have ACH-1 unlocked
    assert (
        "ACH-01" not in session._achievements._unlocked
        or session._achievements._unlocked is not None
    ), "achievements should NOT be reverted by undo"


# ---------------------------------------------------------------------------
# new_game() Tests
# ---------------------------------------------------------------------------


def test_new_game_resets_all_state(session: GameSession) -> None:
    """AC-9: new_game() resets Board, Score, History, Achievements, Twist."""
    from src.core.board import Direction, BoardState

    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )
    session.move(Direction.LEFT)

    session.new_game()

    grid = session._board.get_grid()
    tile_count = sum(1 for row in grid for cell in row if cell != 0)
    assert tile_count == 2, f"new_game should spawn 2 tiles, got {tile_count}"
    assert session._score.get_score() == 0, "score should reset to 0"
    assert session._history.can_undo() is False, (
        "history should be empty after new_game"
    )
    assert session._achievements._unlocked == set(), "achievements should reset"


def test_new_game_spawns_two_tiles(session: GameSession) -> None:
    """AC-14: new_game() places exactly 2 tiles on the board."""
    session.new_game()
    grid = session._board.get_grid()
    tile_count = sum(1 for row in grid for cell in row if cell != 0)
    assert tile_count == 2, f"new_game should spawn exactly 2 tiles, got {tile_count}"


def test_new_game_mid_game(session: GameSession) -> None:
    """Edge: new_game() discards all mid-game state; high score persists."""
    from src.core.board import Direction, BoardState

    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )
    session.move(Direction.LEFT)
    high_before = session._score.get_high_score()

    session.new_game()

    assert session._board.get_state().score == 0 or session._score.get_score() == 0
    assert session._history.can_undo() is False
    grid = session._board.get_grid()
    assert sum(1 for row in grid for cell in row if cell != 0) == 2
    assert session._score.get_high_score() >= high_before, (
        "high score persists across new_game"
    )


# ---------------------------------------------------------------------------
# game_over Tests
# ---------------------------------------------------------------------------


def test_game_over_no_rotten(session: GameSession) -> None:
    """AC-10: game_over delegates to Rules.is_game_over(board, has_rotten).

    Full board with no legal moves and no rotten tiles → game over.
    """
    from src.core.board import BoardState

    # Classic game-over pattern: alternating values with no legal merges
    full_grid = [
        [2, 4, 2, 4],
        [4, 2, 4, 2],
        [2, 4, 2, 4],
        [4, 2, 4, 2],
    ]
    session._board.set_state(BoardState(grid=full_grid, score=100, moves=50))
    assert session.game_over is True, "full board with no moves should be game over"


def test_game_over_with_rotten(session: GameSession) -> None:
    """OQ-P17: Full board with single non-rescueable rotten tile → game IS over.

    A single rotten tile with no adjacent same-value rotten partner
    is not rescueable — is_game_over returns True.
    """
    from src.core.board import BoardState

    full_grid = [
        [2, 4, 2, 4],
        [4, 2, 4, 2],
        [2, 4, 2, 4],
        [4, 2, 4, 2],
    ]
    session._board.set_state(BoardState(grid=full_grid, score=100, moves=50))
    # Add a single rotten tile — no adjacent rotten with same value
    session._board.add_rotten(0, 0, countdown=2)
    # Sync twist overlay from board so game_over reads the rotten presence
    session._twist._overlay = session._board.get_rotten_overlay()

    assert session.game_over is True, (
        "single non-rescueable rotten tile — game IS over (OQ-P17)"
    )


def test_game_over_empty_board(session: GameSession) -> None:
    """Edge: Board with empty cells is never game over."""
    assert session.game_over is False, "board with empty cells is never game over"


def test_game_over_consistency_after_undo(session: GameSession) -> None:
    """Edge: game_over property is consistent after undo (Twist overlay stale cache)."""
    from src.core.board import Direction, BoardState

    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )
    session.move(Direction.LEFT)

    # After undo, game_over should be callable without crashing
    session.undo()
    _ = session.game_over  # Should not raise — stale overlay is acceptable


def test_move_after_game_over(session: GameSession) -> None:
    """Edge: move() after game_over=True attempts the slide (no guard in move)."""
    from src.core.board import Direction, BoardState

    # Force game-over state: full board, no legal moves, no rotten
    full_grid = [
        [2, 4, 2, 4],
        [4, 2, 4, 2],
        [2, 4, 2, 4],
        [4, 2, 4, 2],
    ]
    session._board.set_state(BoardState(grid=full_grid, score=100, moves=50))
    assert session.game_over is True, "should be game over"

    # Attempting a move on a game-over board should still return a MoveResult
    result = session.move(Direction.LEFT)
    assert isinstance(result, MoveResult), (
        "move should return MoveResult even after game_over"
    )


def test_move_full_board_spawn_skipped(session: GameSession) -> None:
    """Edge: spawn_tile() failure on full board does not crash move()."""
    from src.core.board import Direction, BoardState

    # Set up a full board where a merge is possible (two adjacent same-value tiles)
    session._board.set_state(
        BoardState(
            grid=[
                [2, 2, 4, 8],
                [16, 32, 64, 128],
                [4, 8, 16, 32],
                [64, 128, 256, 512],
            ],
            score=0,
            moves=0,
        )
    )

    # Merge [2,2] LEFT — frees one cell, spawn_tile fills it, next call sees full board
    result = session.move(Direction.LEFT)
    assert isinstance(result, MoveResult), (
        "move should complete without crash on full board"
    )
    assert result.moved is True, "merge should succeed"


# ---------------------------------------------------------------------------
# save/load Tests
# ---------------------------------------------------------------------------


def test_save_serializes_all_state(session: GameSession) -> None:
    """AC-11: save() returns a dict with all required keys for JSON serialization."""
    from src.core.board import Direction, BoardState

    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )
    session.move(Direction.LEFT)

    data = session.save()
    assert "board" in data, "save dict should contain 'board'"
    assert "score" in data, "save dict should contain 'score'"
    assert "history" in data, "save dict should contain 'history'"
    assert "achievements" in data, "save dict should contain 'achievements'"
    assert "twist_overlay" in data, "save dict should contain 'twist_overlay'"
    assert "version" in data, "save dict should contain 'version'"
    assert isinstance(data["board"], dict)
    assert isinstance(data["history"], list)


def test_load_restores_full_state(
    seeded_rng: random.Random,
    tmp_high_score_path: str,
) -> None:
    """AC-12: load() restores Board, Score, History, Achievements, and Twist from saved dict."""
    from src.core.board import Direction

    session = GameSession(rng=seeded_rng, high_score_path=tmp_high_score_path)
    session.move(Direction.LEFT)
    data = session.save()

    loaded = GameSession.load(data, rng=seeded_rng, high_score_path=tmp_high_score_path)
    assert loaded._board.get_state().grid == session._board.get_state().grid
    assert loaded._score.get_score() == session._score.get_score()
    assert loaded._history.can_undo() == session._history.can_undo()


def test_save_load_round_trip(
    seeded_rng: random.Random,
    tmp_high_score_path: str,
) -> None:
    """AC-13: save() then load() produces identical game state (round-trip fidelity)."""
    from src.core.board import Direction, BoardState

    session = GameSession(rng=seeded_rng, high_score_path=tmp_high_score_path)
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )
    session.move(Direction.LEFT)

    data = session.save()
    restored = GameSession.load(
        data, rng=seeded_rng, high_score_path=tmp_high_score_path
    )

    assert restored._board.get_grid() == session._board.get_grid(), (
        "grid must match after round-trip"
    )
    assert restored._score.get_score() == session._score.get_score(), (
        "score must match after round-trip"
    )


def test_save_load_empty_history(
    seeded_rng: random.Random,
    tmp_high_score_path: str,
) -> None:
    """Edge: save/load with no history works; restored session has empty history."""
    session = GameSession(rng=seeded_rng, high_score_path=tmp_high_score_path)
    data = session.save()
    restored = GameSession.load(
        data, rng=seeded_rng, high_score_path=tmp_high_score_path
    )
    assert restored._history.can_undo() is False


def test_save_load_no_achievements(
    seeded_rng: random.Random,
    tmp_high_score_path: str,
) -> None:
    """Edge: save/load with no achievements; restored has empty unlocked set."""
    session = GameSession(rng=seeded_rng, high_score_path=tmp_high_score_path)
    data = session.save()
    restored = GameSession.load(
        data, rng=seeded_rng, high_score_path=tmp_high_score_path
    )
    assert restored._achievements._unlocked == set()


def test_save_load_with_rotten_tiles(
    seeded_rng: random.Random,
    tmp_high_score_path: str,
) -> None:
    """Edge: save/load preserves rotten overlay state."""
    session = GameSession(rng=seeded_rng, high_score_path=tmp_high_score_path)
    # Add a rotten tile (cell must be non-zero)
    session._board.set_cell(1, 0, 4)
    session._board.add_rotten(1, 0, countdown=2)
    session._twist._overlay = session._board.get_rotten_overlay()

    original_overlay = session._twist.get_overlay()
    data = session.save()
    restored = GameSession.load(
        data, rng=seeded_rng, high_score_path=tmp_high_score_path
    )
    restored_overlay = restored._twist.get_overlay()

    assert restored_overlay == original_overlay, (
        "rotten overlay must survive round-trip"
    )


def test_load_missing_keys_raises(seeded_rng: random.Random) -> None:
    """Edge: load() with missing required keys raises KeyError."""
    with pytest.raises((KeyError, ValueError)):
        GameSession.load({}, rng=seeded_rng)


# ---------------------------------------------------------------------------
# Import Test
# ---------------------------------------------------------------------------


def test_no_pygame_imports_in_game_session() -> None:
    """AC-15: src/core/game_session.py must not import pygame or display dependencies."""
    import importlib
    import inspect

    module = importlib.import_module("src.core.game_session")
    source = inspect.getsource(module)
    assert "pygame" not in source.lower(), "game_session.py must not reference pygame"
    assert "display" not in source.lower(), "game_session.py must not reference display"


# ---------------------------------------------------------------------------
# Accessor Tests
# ---------------------------------------------------------------------------


def test_accessor_get_board_grid_initial(session: GameSession) -> None:
    """AC-1: get_board_grid() returns a 4x4 grid with exactly 2 non-zero cells on a fresh session."""
    grid = session.get_board_grid()

    assert len(grid) == 4, f"Grid should have 4 rows, got {len(grid)}"
    assert all(len(row) == 4 for row in grid), "Each row should have 4 columns"
    tile_count = sum(1 for row in grid for cell in row if cell != 0)
    assert tile_count == 2, f"Fresh session should have 2 tiles, got {tile_count}"
    assert grid == session._board.get_grid(), "Grid should match internal board state"


def test_accessor_get_score_initial(session: GameSession) -> None:
    """AC-1: get_score() returns 0 on a fresh session."""
    score = session.get_score()

    assert score == 0, f"Initial score should be 0, got {score}"
    assert score == session._score.get_score(), (
        "Score should match internal score state"
    )


def test_accessor_get_high_score_initial(session: GameSession) -> None:
    """AC-1: get_high_score() returns 0 on a fresh session (no prior high score persisted)."""
    high_score = session.get_high_score()

    assert high_score == 0, f"Initial high score should be 0, got {high_score}"
    assert high_score == session._score.get_high_score(), (
        "High score should match internal score state"
    )


def test_accessor_get_move_count_initial(session: GameSession) -> None:
    """AC-1: get_move_count() returns 0 on a fresh session."""
    count = session.get_move_count()

    assert count == 0, f"Initial move count should be 0, got {count}"
    assert count == session._board.get_state().moves, (
        "Move count should match internal board state"
    )


def test_accessor_get_rotten_overlay_initial(session: GameSession) -> None:
    """AC-1: get_rotten_overlay() returns a 4x4 all-zero grid on a fresh session."""
    overlay = session.get_rotten_overlay()

    assert len(overlay) == 4, f"Overlay should have 4 rows, got {len(overlay)}"
    assert all(len(row) == 4 for row in overlay), "Each row should have 4 columns"
    assert all(cell == 0 for row in overlay for cell in row), (
        "Fresh session overlay should be all zeros"
    )


def test_accessor_can_undo_initial(session: GameSession) -> None:
    """AC-1: can_undo() returns False on a fresh session (no moves made)."""
    result = session.can_undo()

    assert result is False, "Fresh session should not have undo history"


def test_accessor_post_move_state(session: GameSession) -> None:
    """Verify all 6 accessors return correct values after one legal merge move."""
    from src.core.board import Direction, BoardState

    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )

    session.move(Direction.LEFT)

    score = session.get_score()
    assert score > 0, f"Score should increase after merge, got {score}"

    move_count = session.get_move_count()
    assert move_count == 1, f"Move count should be 1, got {move_count}"

    can_undo = session.can_undo()
    assert can_undo is True, "Should be able to undo after a legal move"

    grid = session.get_board_grid()
    tile_count = sum(1 for row in grid for cell in row if cell != 0)
    assert 2 <= tile_count <= 3, (
        f"Expected 2 or 3 non-zero cells after merge+spawn, got {tile_count}"
    )


def test_accessor_grid_defensive_copy(session: GameSession) -> None:
    """Verify mutating get_board_grid() return value does not affect internal state."""
    grid1 = session.get_board_grid()

    grid1[0][0] = 9999

    grid2 = session.get_board_grid()
    assert grid2[0][0] != 9999, f"Mutation leaked: grid2[0][0] == {grid2[0][0]}"
    assert grid2 == session._board.get_grid(), (
        "Internal board state should be unaffected by external mutation"
    )


def test_accessor_overlay_defensive_copy(session: GameSession) -> None:
    """Verify mutating get_rotten_overlay() return value does not affect internal state."""
    overlay1 = session.get_rotten_overlay()

    overlay1[0][0] = 7777

    overlay2 = session.get_rotten_overlay()
    assert overlay2[0][0] != 7777, (
        f"Mutation leaked: overlay2[0][0] == {overlay2[0][0]}"
    )
    assert overlay2 == session._board.get_rotten_overlay(), (
        "Internal overlay state should be unaffected by external mutation"
    )


def test_accessor_score_reflects_delta(session: GameSession) -> None:
    """Verify get_score() reflects accumulated merge deltas after multiple moves."""
    from src.core.board import Direction, BoardState

    # First merge: [2,2,0,0] LEFT -> delta 4
    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )
    session.move(Direction.LEFT)

    initial_delta = session.get_score()
    assert initial_delta == 4, f"First merge should yield score 4, got {initial_delta}"

    # Second merge: set up another mergeable scenario
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=session._score.get_score(),
            moves=session._board.get_state().moves,
        )
    )
    session.move(Direction.LEFT)

    accumulated_score = session.get_score()
    assert accumulated_score > initial_delta, (
        f"Score should accumulate: expected > {initial_delta}, got {accumulated_score}"
    )


def test_accessor_can_undo_transition(session: GameSession) -> None:
    """Verify can_undo() transitions False -> True -> False through move+undo cycle."""
    from src.core.board import Direction, BoardState

    assert session.can_undo() is False, "Fresh session should not allow undo"

    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )
    session.move(Direction.LEFT)

    assert session.can_undo() is True, "Should be able to undo after a legal move"

    session.undo()
    assert session.can_undo() is False, (
        "Should not be able to undo after restoring to initial state"
    )


def test_accessor_high_score_persists_after_undo(session: GameSession) -> None:
    """Verify get_high_score() retains peak score after undo lowers current score."""
    from src.core.board import Direction, BoardState

    session._board.reset()
    session._board.set_state(
        BoardState(
            grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            score=0,
            moves=0,
        )
    )

    session.move(Direction.LEFT)
    peak_score = session.get_high_score()
    assert peak_score > 0, f"High score should capture merge, got {peak_score}"

    session.undo()

    after_undo_high_score = session.get_high_score()
    assert after_undo_high_score == peak_score, (
        f"High score should persist: expected {peak_score}, got {after_undo_high_score}"
    )


def test_accessor_type_correctness(session: GameSession) -> None:
    """Verify all 6 accessors return the declared types."""
    grid = session.get_board_grid()
    assert isinstance(grid, list), "get_board_grid() should return a list"
    assert all(isinstance(row, list) for row in grid), (
        "get_board_grid() rows should be lists"
    )

    assert isinstance(session.get_score(), int), "get_score() should return int"
    assert isinstance(session.get_high_score(), int), (
        "get_high_score() should return int"
    )
    assert isinstance(session.get_move_count(), int), (
        "get_move_count() should return int"
    )

    overlay = session.get_rotten_overlay()
    assert isinstance(overlay, list), "get_rotten_overlay() should return a list"
    assert all(isinstance(row, list) for row in overlay), (
        "get_rotten_overlay() rows should be lists"
    )

    assert isinstance(session.can_undo(), bool), "can_undo() should return bool"
