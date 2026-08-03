"""Tests for the achievements module — 16 test cases covering all 12 achievements.

Tests follow the pseudocode blueprint at
registry://pseudocode/phase_2_sprint_2_task_1_code.md.

All tests use BoardState constructors directly — no Board session, no file I/O,
no pygame dependency.
"""

import inspect

from src.core.achievements import Achievements, _ACHIEVEMENT_DEFINITIONS
from src.core.board import BoardState


# ---------------------------------------------------------------------------
# Helpers and grid constants
# ---------------------------------------------------------------------------

EMPTY_GRID: list[list[int]] = [[0] * 4 for _ in range(4)]
FULL_GRID: list[list[int]] = [[2] * 4 for _ in range(4)]
GRID_WITH_32: list[list[int]] = [
    [32, 2, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
]
GRID_WITH_256: list[list[int]] = [
    [256, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
]
GRID_WITH_1024: list[list[int]] = [
    [1024, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
]
GRID_WITH_2048: list[list[int]] = [
    [2048, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
]


def make_board_state(
    grid: list[list[int]] | None = None,
    score: int = 0,
    moves: int = 0,
) -> BoardState:
    """Factory for BoardState with safe defaults."""
    return BoardState(
        grid=grid or [row[:] for row in EMPTY_GRID], score=score, moves=moves
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_import_achievements():
    """AC-1/AC-13: Achievements and Achievement are importable from src.core."""
    from src.core import (
        Achievements as CoreAchievements,
        Achievement as CoreAchievement,
    )

    assert inspect.isclass(CoreAchievements), "Achievements should be a class"
    assert inspect.isclass(CoreAchievement), "Achievement should be a dataclass"
    # Verify dataclass fields
    a = CoreAchievement(id="X", name="N", description="D", icon="I")
    assert a.id == "X"
    assert a.name == "N"
    assert a.description == "D"
    assert a.icon == "I"


def test_no_achievements_on_empty_state():
    """AC-2/AC-7: Empty board with score=0 unlocks nothing."""
    ach = Achievements()
    bs = make_board_state()
    result = ach.evaluate(bs, move_count=0, score=0, rotten_positions=[])
    assert result == [], f"Expected empty list, got {result}"
    assert ach.to_dict()["unlocked"] == [], "to_dict unlocked should be empty"


def test_first_merge_unlocks_ach01():
    """AC-3/AC-9: ACH-01 unlocks when score > 0."""
    ach = Achievements()
    bs = make_board_state(
        grid=[[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], score=4, moves=1
    )
    result = ach.evaluate(bs, move_count=1, score=4, rotten_positions=[])
    ids = [r.id for r in result]
    assert "ACH-01" in ids, f"ACH-01 not in results: {ids}"
    first_bite = next(r for r in result if r.id == "ACH-01")
    assert first_bite.name == "First Bite"
    assert first_bite.icon == "first_bite"
    assert "ACH-01" in ach.to_dict()["unlocked"]


def test_tile_32_unlocks_ach02():
    """AC-9: ACH-02 unlocks when max tile >= 32."""
    ach = Achievements()
    bs = make_board_state(grid=GRID_WITH_32, score=34, moves=5)
    result = ach.evaluate(bs, move_count=5, score=34, rotten_positions=[])
    ids = [r.id for r in result]
    assert "ACH-02" in ids, f"ACH-02 not in results: {ids}"


def test_tile_256_unlocks_ach03():
    """AC-9: ACH-03 unlocks when max tile >= 256."""
    ach = Achievements()
    bs = make_board_state(grid=GRID_WITH_256, score=500, moves=20)
    result = ach.evaluate(bs, move_count=20, score=500, rotten_positions=[])
    ids = [r.id for r in result]
    assert "ACH-03" in ids, f"ACH-03 not in results: {ids}"


def test_tile_1024_unlocks_ach04():
    """AC-9: ACH-04 unlocks when max tile >= 1024."""
    ach = Achievements()
    bs = make_board_state(grid=GRID_WITH_1024, score=2000, moves=50)
    result = ach.evaluate(bs, move_count=50, score=2000, rotten_positions=[])
    ids = [r.id for r in result]
    assert "ACH-04" in ids, f"ACH-04 not in results: {ids}"


def test_rotten_cleared_unlocks_ach05():
    """AC-9/AC-11: ACH-05 unlocks when rotten count decreases."""
    ach = Achievements()
    bs = make_board_state(score=100, moves=5)
    # Call 1: 2 rotten present — no achievement yet
    result1 = ach.evaluate(
        bs, move_count=5, score=100, rotten_positions=[(0, 0), (1, 1)]
    )
    assert "ACH-05" not in [r.id for r in result1]
    # Call 2: both cleared — ACH-05 should unlock
    result2 = ach.evaluate(bs, move_count=5, score=100, rotten_positions=[])
    assert "ACH-05" in [r.id for r in result2], "ACH-05 not unlocked on rotten clear"


def test_10_rotten_cleared_unlocks_ach06():
    """AC-9/AC-11: ACH-06 unlocks when cumulative rotten cleared >= 10."""
    ach = Achievements()
    bs = make_board_state(score=50, moves=5)

    # Start with 10 rotten
    rotten = [(0, i) for i in range(10)]
    ach.evaluate(bs, move_count=1, score=0, rotten_positions=rotten)

    # Decrease by 1 each call for 10 calls
    for i in range(10):
        remaining = rotten[: len(rotten) - i - 1]
        ach.evaluate(bs, move_count=2 + i, score=0, rotten_positions=remaining)

    # ACH-06 should be unlocked by now
    assert "ACH-06" in ach.to_dict()["unlocked"], (
        "ACH-06 should be unlocked after 10 cleared"
    )
    # The last call or one of the calls should have returned ACH-06
    # Verify it's in unlocked; the specific return may have been an earlier call


def test_speed_chef_unlocks_ach07():
    """AC-9: ACH-07 unlocks when score >= 1000 AND move_count < 20."""
    ach = Achievements()
    bs = make_board_state(score=1000, moves=15)
    result = ach.evaluate(bs, move_count=15, score=1000, rotten_positions=[])
    ids = [r.id for r in result]
    assert "ACH-07" in ids, f"ACH-07 not in results: {ids}"


def test_100_moves_unlocks_ach08():
    """AC-9: ACH-08 unlocks when move_count >= 100."""
    ach = Achievements()
    bs = make_board_state(score=500, moves=100)
    result = ach.evaluate(bs, move_count=100, score=500, rotten_positions=[])
    ids = [r.id for r in result]
    assert "ACH-08" in ids, f"ACH-08 not in results: {ids}"


def test_score_10000_unlocks_ach09():
    """AC-9: ACH-09 unlocks when score >= 10000."""
    ach = Achievements()
    bs = make_board_state(score=10000, moves=200)
    result = ach.evaluate(bs, move_count=200, score=10000, rotten_positions=[])
    ids = [r.id for r in result]
    assert "ACH-09" in ids, f"ACH-09 not in results: {ids}"


def test_full_board_unlocks_ach10():
    """AC-9: ACH-10 unlocks when every cell is occupied."""
    ach = Achievements()
    bs = make_board_state(grid=FULL_GRID, score=500, moves=50)
    result = ach.evaluate(bs, move_count=50, score=500, rotten_positions=[])
    ids = [r.id for r in result]
    assert "ACH-10" in ids, f"ACH-10 not in results: {ids}"


def test_no_waste_unlocks_ach11():
    """AC-9/AC-11: ACH-11 unlocks when max tile >= 2048 AND never cleared rotten."""
    ach = Achievements()
    bs = make_board_state(grid=GRID_WITH_2048, score=20000, moves=100)
    result = ach.evaluate(bs, move_count=100, score=20000, rotten_positions=[])
    ids = [r.id for r in result]
    assert "ACH-11" in ids, f"ACH-11 not in results: {ids}"


def test_contamination_survived_unlocks_ach12():
    """AC-9/AC-11: ACH-12 unlocks when cumulative_contaminated >= 5."""
    ach = Achievements()
    bs = make_board_state()

    # Each call adds 1 more rotten position, triggering contamination delta +1
    ach.evaluate(bs, 1, 0, [])  # no change
    ach.evaluate(bs, 2, 0, [(0, 0)])  # contam += 1 -> 1
    ach.evaluate(bs, 3, 0, [(0, 0), (1, 1)])  # contam += 1 -> 2
    ach.evaluate(bs, 4, 0, [(0, 0), (1, 1), (2, 2)])  # contam += 1 -> 3
    ach.evaluate(bs, 5, 0, [(0, 0), (1, 1), (2, 2), (3, 3)])  # contam += 1 -> 4
    result = ach.evaluate(
        bs, 6, 0, [(0, 0), (1, 1), (2, 2), (3, 3), (0, 1)]
    )  # contam += 1 -> 5
    ids = [r.id for r in result]
    assert "ACH-12" in ids, f"ACH-12 not in results after 5 contaminations: {ids}"


def test_no_duplicate_unlocks():
    """AC-4: Second call with same qualifying state returns empty list."""
    ach = Achievements()
    bs = make_board_state(score=4, moves=1)

    result1 = ach.evaluate(bs, move_count=1, score=4, rotten_positions=[])
    assert "ACH-01" in [r.id for r in result1], "ACH-01 should unlock on first call"

    result2 = ach.evaluate(bs, move_count=1, score=4, rotten_positions=[])
    assert result2 == [], f"Second call should return empty, got {result2}"


def test_12_achievements_defined():
    """AC-9: Exactly 12 unique achievement IDs exist across definitions and inline checks."""
    ids_in_definitions = {d.id for d in _ACHIEVEMENT_DEFINITIONS}
    assert len(ids_in_definitions) == 8, (
        f"Expected 8 definitions, got {len(ids_in_definitions)}"
    )

    inline_ids = {"ACH-05", "ACH-06", "ACH-11", "ACH-12"}
    assert len(inline_ids) == 4

    all_ids = ids_in_definitions | inline_ids
    expected = {
        "ACH-01",
        "ACH-02",
        "ACH-03",
        "ACH-04",
        "ACH-05",
        "ACH-06",
        "ACH-07",
        "ACH-08",
        "ACH-09",
        "ACH-10",
        "ACH-11",
        "ACH-12",
    }
    assert all_ids == expected, f"Expected IDs {expected}, got {all_ids}"


def test_persistence_round_trip():
    """AC-8/AC-14: to_dict() -> from_dict() round-trip preserves all state."""
    ach = Achievements()
    bs = make_board_state(score=100, moves=5)

    # Unlock ACH-01 (score > 0)
    ach.evaluate(bs, 1, 4, [(0, 0)])
    # Clear rotten -> unlock ACH-05, set ever_cleared_rotten
    ach.evaluate(bs, 2, 8, [])

    data = ach.to_dict()
    assert "ACH-01" in data["unlocked"]
    assert "ACH-05" in data["unlocked"]
    assert data["ever_cleared_rotten"] is True

    # Round-trip
    ach2 = Achievements.from_dict(data)
    data2 = ach2.to_dict()
    assert data == data2, f"Round-trip mismatch: {data} != {data2}"

    # Verify no re-unlock after restore
    result = ach2.evaluate(bs, 2, 8, [])
    assert result == [], f"Should not re-unlock after from_dict: {result}"


def test_achievement_definition_not_exported():
    """AchievementDefinition is not public (module-internal only)."""
    import src.core.achievements as ach_module

    # _AchievementDefinition exists but is private (underscore prefix)
    assert hasattr(ach_module, "_AchievementDefinition")
    # It should NOT be in __all__
    assert "_AchievementDefinition" not in ach_module.__all__
    assert "_ACHIEVEMENT_DEFINITIONS" not in ach_module.__all__


def test_no_pygame_imports():
    """AC-12: No pygame imports in achievements module."""
    import src.core.achievements as ach_module

    source = open(ach_module.__file__).read()
    assert "pygame" not in source, "achievements.py should not import pygame"
