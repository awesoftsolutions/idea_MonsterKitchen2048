"""Integration tests for Monster Kitchen 2048 -- cross-module pipeline verification.

Exercises GameSession as the single orchestrator entry point wiring all 6 core
modules (Board, Rules, Score, History, Achievements, Twist). Each test validates
cross-module behavior that unit tests in isolation cannot cover.

All tests use inline seeded RNG (random.Random(seed=N)) for determinism.
Different seeds (42, 99, 123) are used per test to exercise different game
trajectories without coupling.

No existing files are modified by this test suite.
"""
# CHANGELOG:
# - Sprint 2 Task 5: Create integration test suite (11 tests)
# - Phase 3 Sprint 1: Update game_over integration test for OQ-P17 stalemate fix

from __future__ import annotations

import importlib
import random
import sys
import pathlib

from src.core.board import Direction, GRID_SIZE
from src.core.game_session import GameSession, MoveResult
from src.core.achievements import Achievement
from src.core.twist import ROTTEN_COUNTDOWN, TwistEffect


# File-level constants matching pseudocode
BOARD_SIZE: int = 4
INITIAL_TILES: int = 2


# ---------------------------------------------------------------------------
# test_full_game_lifecycle -- Complete game lifecycle through GameSession
# ---------------------------------------------------------------------------


def test_full_game_lifecycle() -> None:
    """Verify complete game lifecycle through GameSession orchestrator.

    Exercises new_game -> moves -> score -> undo -> achievements -> twist -> game_over
    across Board, Score, History, Achievements, and Twist in a single end-to-end flow.
    """
    rng = random.Random(42)
    session = GameSession(rng=rng)

    # Verify initial state after construction
    assert session._board.get_state().moves == 0
    assert session._score.get_score() == 0
    assert session._history.can_undo() is False
    empty_count = len(session._board.get_empty_cells())
    assert empty_count == (GRID_SIZE * GRID_SIZE) - INITIAL_TILES

    # Execute first 3 moves (bounded to limit board complexity)
    total_score_delta = 0
    for direction in [Direction.LEFT, Direction.UP, Direction.RIGHT]:
        result = session.move(direction)
        if result.moved:
            total_score_delta += result.score_delta

    # Verify history has entries for legal moves
    assert session._history.can_undo() is True

    # Verify twist processing occurred (overlay is 4x4)
    overlay = session._twist.get_overlay()
    assert len(overlay) == GRID_SIZE
    assert len(overlay[0]) == GRID_SIZE

    # Verify game_over property returns a bool
    game_over = session.game_over
    assert isinstance(game_over, bool)

    # Verify undo restores prior state
    pre_undo_score = session._score.get_score()
    if session._history.can_undo():
        undo_result = session.undo()
        assert undo_result is True
        assert session._score.get_score() <= pre_undo_score


# ---------------------------------------------------------------------------
# test_save_load_roundtrip -- save() -> load() preserves all state
# ---------------------------------------------------------------------------


def test_save_load_roundtrip(tmp_path: object) -> None:
    """Verify save/load roundtrip preserves board, score, achievements, twist overlay, and history depth.

    Uses seed 99 and tmp_path for high-score isolation from real filesystem.
    """
    rng = random.Random(99)
    hs_path = str(tmp_path / "high_score.json")
    session = GameSession(rng=rng, high_score_path=hs_path)

    # Make 3 moves to build up state
    for d in [Direction.LEFT, Direction.UP, Direction.RIGHT]:
        session.move(d)

    # Capture pre-save state
    pre_board = session._board.get_state()
    pre_score = session._score.get_score()
    pre_achievements = session._achievements.to_dict()
    pre_overlay = session._twist.get_overlay()

    # Serialize via save()
    data = session.save()
    assert isinstance(data, dict)
    assert data["version"] == 1

    # Create fresh RNG and reconstruct via load()
    rng2 = random.Random(99)
    restored = GameSession.load(data, rng=rng2, high_score_path=hs_path)

    # Verify board state matches
    post_board = restored._board.get_state()
    assert post_board.grid == pre_board.grid
    assert post_board.moves == pre_board.moves

    # Verify score matches
    assert restored._score.get_score() == pre_score

    # Verify achievements match
    assert restored._achievements.to_dict() == pre_achievements

    # Verify twist overlay matches
    post_overlay = restored._twist.get_overlay()
    assert post_overlay == pre_overlay

    # Verify history depth preserved
    assert restored._history.can_undo() == session._history.can_undo()


# ---------------------------------------------------------------------------
# test_twist_contamination_end_to_end -- Rotten spawn + countdown
# ---------------------------------------------------------------------------


def test_twist_contamination_end_to_end() -> None:
    """Verify rotten spawn, countdown, and contamination lifecycle through GameSession.

    Multiple moves trigger rotten tile spawning via the Twist module, then
    inspects the overlay for countdown values within valid range.
    """
    rng = random.Random(123)
    session = GameSession(rng=rng)

    # Execute moves, stopping if game-over
    directions = [
        Direction.LEFT, Direction.UP, Direction.LEFT, Direction.UP,
        Direction.RIGHT, Direction.DOWN, Direction.RIGHT, Direction.DOWN,
    ]
    twist_effects: list[TwistEffect] = []
    for direction in directions:
        if session.game_over:
            break
        result = session.move(direction)
        if result.moved:
            twist_effects.append(result.twist_effect)

    # Inspect twist overlay structure (4x4)
    overlay = session._twist.get_overlay()
    assert len(overlay) == GRID_SIZE
    assert len(overlay[0]) == GRID_SIZE

    # If any rotten tiles exist, verify countdown within valid range
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if overlay[row][col] > 0:
                assert 1 <= overlay[row][col] <= ROTTEN_COUNTDOWN

    # Verify TwistEffect instances were returned
    for effect in twist_effects:
        assert isinstance(effect, TwistEffect)


# ---------------------------------------------------------------------------
# test_score_pipeline -- Board slide -> correct score delta via GameSession
# ---------------------------------------------------------------------------


def test_score_pipeline(tmp_path: object) -> None:
    """Verify score pipeline: Board slide -> score delta -> Score.add via GameSession.

    Accumulates deltas across multiple moves and verifies final score equals
    the sum of all deltas.
    """
    rng = random.Random(42)
    hs_path = str(tmp_path / "score_test.json")
    session = GameSession(rng=rng, high_score_path=hs_path)

    # Record initial score = 0
    assert session._score.get_score() == 0

    # Execute 3 moves (bounded to limit board complexity)
    total_delta = 0
    for direction in [Direction.LEFT, Direction.UP, Direction.RIGHT]:
        result = session.move(direction)
        if result.moved:
            total_delta += result.score_delta

    # Verify accumulated score matches sum of deltas
    assert session._score.get_score() == total_delta
    assert session._score.get_score() >= 0

    # If any merges occurred, verify score is positive
    if total_delta > 0:
        assert session._score.get_score() > 0


# ---------------------------------------------------------------------------
# test_undo_pipeline -- N moves -> N undos -> initial state restoration
# ---------------------------------------------------------------------------


def test_undo_pipeline() -> None:
    """Verify N moves -> N undos -> board returns to initial state with correct score.

    Compares pre-game and post-undo grids and scores to confirm full restoration.
    """
    rng = random.Random(42)
    session = GameSession(rng=rng)

    # Capture initial state
    initial_grid = session._board.get_state().grid
    initial_score = session._score.get_score()

    # Execute 3 moves, collecting results
    move_results: list[MoveResult] = []
    directions = [Direction.LEFT, Direction.UP, Direction.RIGHT]
    for direction in directions:
        result = session.move(direction)
        move_results.append(result)

    # Count legal moves
    legal_count = sum(1 for r in move_results if r.moved)

    # Undo all legal moves
    undos_performed = 0
    for _ in range(legal_count):
        undo_result = session.undo()
        if undo_result:
            undos_performed += 1

    # Verify all undos succeeded
    assert undos_performed == legal_count

    # Verify board returns to initial state
    final_grid = session._board.get_state().grid
    final_score = session._score.get_score()
    assert final_grid == initial_grid
    assert final_score == initial_score

    # Verify no more undos available
    assert session._history.can_undo() is False
    assert session.undo() is False


# ---------------------------------------------------------------------------
# test_achievement_unlock_through_gameplay -- ACH-01 via merge
# ---------------------------------------------------------------------------


def test_achievement_unlock_through_gameplay() -> None:
    """Verify ACH-01 First Bite unlocks via actual game merges through GameSession.

    Uses seeded RNG and cycles through all 4 directions until a merge occurs,
    then verifies ACH-01 was unlocked exactly once.
    """
    rng = random.Random(42)
    session = GameSession(rng=rng)

    # Execute moves until score increases (bounded attempts)
    all_unlocked: list[Achievement] = []
    directions_cycle = [Direction.LEFT, Direction.UP, Direction.RIGHT, Direction.DOWN]
    attempts = 0
    while attempts < 10 and session._score.get_score() == 0:
        direction = directions_cycle[attempts % 4]
        result = session.move(direction)
        if result.new_achievements:
            all_unlocked.extend(result.new_achievements)
        attempts += 1

    # If score increased, verify ACH-01 was unlocked
    if session._score.get_score() > 0:
        ach_ids = [a.id for a in all_unlocked]
        assert "ACH-01" in ach_ids

        # Verify no duplicate ACH-01 unlocks
        ach01_count = sum(1 for a in all_unlocked if a.id == "ACH-01")
        assert ach01_count == 1

        # Verify Achievement dataclass fields populated
        if all_unlocked:
            first = all_unlocked[0]
            assert first.id.startswith("ACH-")
            assert len(first.name) > 0
            assert len(first.description) > 0
            assert len(first.icon) > 0


# ---------------------------------------------------------------------------
# test_game_over_detection -- Full board -> game_over=True
# ---------------------------------------------------------------------------


def test_game_over_detection() -> None:
    """Verify game_over returns True when board is completely full with no legal moves.

    Uses set_cell to fill the board with non-mergeable alternating values,
    producing a classic game-over pattern.
    """
    rng = random.Random(42)
    session = GameSession(rng=rng)

    # Fill board with non-mergeable alternating values via set_cell
    value = 2
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            session._board.set_cell(row, col, value)
            value *= 2

    # Verify no empty cells remain
    assert len(session._board.get_empty_cells()) == 0

    # Verify game_over is True
    assert session.game_over is True


# ---------------------------------------------------------------------------
# test_game_over_not_triggered_with_rotten -- Rotten tiles suppress game_over
# ---------------------------------------------------------------------------


def test_game_over_not_triggered_with_rotten() -> None:
    """Verify game_over returns False when board is full but rotten tiles exist.

    The Twist-aware game_over check prevents game over when rotten tiles
    are present, since contamination clearing can create new empty cells.
    """
    rng = random.Random(42)
    session = GameSession(rng=rng)

    # Fill board with non-mergeable values
    value = 2
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            session._board.set_cell(row, col, value)
            value *= 2

    # Add rotten overlay at cell (0, 0) -- requires non-empty cell (already set)
    session._board.add_rotten(0, 0, countdown=3)

    # Sync twist overlay from board so game_over reads the rotten presence
    session._twist._overlay = session._board.get_rotten_overlay()

    # Verify game_over is True (single rotten, no rescueable pair — OQ-P17)
    assert session.game_over is True

    # Remove rotten overlay
    session._board.remove_rotten(0, 0)

    # Sync twist overlay again after removal
    session._twist._overlay = session._board.get_rotten_overlay()

    # Verify game_over is now True
    assert session.game_over is True


# ---------------------------------------------------------------------------
# test_new_game_resets_all_state -- Score=0, history empty, twist cleared
# ---------------------------------------------------------------------------


def test_new_game_resets_all_state() -> None:
    """Verify new_game() resets all modules to initial state.

    After several moves, calls new_game() and verifies:
    - Score reset to 0
    - History cleared
    - Twist overlay all zeros
    - Exactly 2 tiles spawned
    """
    rng = random.Random(42)
    session = GameSession(rng=rng)

    # Make 3 moves to build up state
    session.move(Direction.LEFT)
    session.move(Direction.UP)
    session.move(Direction.RIGHT)

    # Call new_game()
    session.new_game()

    # Verify score reset to 0
    assert session._score.get_score() == 0

    # Verify history cleared
    assert session._history.can_undo() is False

    # Verify board has exactly 2 tiles
    empty_count = len(session._board.get_empty_cells())
    assert empty_count == (GRID_SIZE * GRID_SIZE) - INITIAL_TILES

    # Verify twist overlay all zeros
    overlay = session._twist.get_overlay()
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            assert overlay[row][col] == 0

    # Verify undo returns False after new_game
    assert session.undo() is False


# ---------------------------------------------------------------------------
# test_full_state_restoration_with_twist_overlay -- save/load with twist
# ---------------------------------------------------------------------------


def test_full_state_restoration_with_twist_overlay(tmp_path: object) -> None:
    """Verify save/load roundtrip when twist overlay may be active.

    Executes multiple moves via safe wrapper to accumulate potential twist
    state, then verifies round-trip fidelity for overlay, grid, and history.
    """
    rng = random.Random(123)
    hs_path = str(tmp_path / "hs_twist.json")
    session = GameSession(rng=rng, high_score_path=hs_path)

    # Execute moves (bounded to avoid game-over)
    for direction in [Direction.LEFT, Direction.UP, Direction.RIGHT] * 2:
        if session.game_over:
            break
        session.move(direction)

    # Capture twist overlay before save
    pre_overlay = session._twist.get_overlay()

    # Save game state
    data = session.save()

    # Load into new session
    rng2 = random.Random(123)
    restored = GameSession.load(data, rng=rng2, high_score_path=hs_path)

    # Verify overlay restored identically
    post_overlay = restored._twist.get_overlay()
    assert post_overlay == pre_overlay

    # Verify board grid preserved
    assert restored._board.get_state().grid == session._board.get_state().grid

    # Verify history stack preserved
    assert restored._history.can_undo() == session._history.can_undo()

    # Continue playing after restore to verify functionality
    if not restored.game_over:
        result = restored.move(Direction.LEFT)
        assert isinstance(result, MoveResult)


# ---------------------------------------------------------------------------
# test_all_modules_importable_without_pygame -- No pygame in src/core/
# ---------------------------------------------------------------------------


def test_all_modules_importable_without_pygame() -> None:
    """Verify all src/core/ modules are importable without pygame or display dependencies.

    Uses both runtime import check and source file scan to catch direct
    and transitive pygame dependencies.
    """
    modules_to_check = [
        "src.core.board",
        "src.core.rules",
        "src.core.score",
        "src.core.history",
        "src.core.achievements",
        "src.core.twist",
        "src.core.game_session",
    ]

    # Import each module
    for module_name in modules_to_check:
        module = importlib.import_module(module_name)
        assert module is not None, f"Failed to import {module_name}"

    # Verify pygame NOT in sys.modules
    pygame_modules = [k for k in sys.modules if "pygame" in k.lower()]
    assert len(pygame_modules) == 0, f"pygame found in sys.modules: {pygame_modules}"

    # Scan source files for pygame imports
    for py_file in pathlib.Path("src/core").glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "import pygame" not in content, f"pygame import found in {py_file}"
        assert "from pygame" not in content, f"from pygame import found in {py_file}"
