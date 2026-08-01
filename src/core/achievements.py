"""Achievements module — 12 Monster Kitchen-themed achievement definitions and evaluator.

Callable conditions per ADR-014. Zero rendering dependencies.

Public API:
    Achievement (dataclass): Value object returned by evaluate() for each newly unlocked achievement.
    Achievements (class): Evaluator that tracks unlocked achievements and game-session state.

Internal types (not exported):
    AchievementDefinition: Definition with callable condition for each achievement.
    _ACHIEVEMENT_DEFINITIONS: Module-level list of 12 achievement definitions
    (8 via condition-callables, 4 via inline checks in evaluate()).
    _get_max_tile(): Helper to extract maximum tile value from grid.
    _count_empty(): Helper to count zero-value cells in grid.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.core.board import BoardState

__all__ = ["Achievement", "Achievements"]


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------


@dataclass
class Achievement:
    """An unlocked achievement instance returned by Achievements.evaluate().

    Attributes:
        id: Unique identifier (e.g., "ACH-01").
        name: Display name (e.g., "First Bite").
        description: Unlock condition description.
        icon: Icon identifier for asset resolution in Phase 4.
    """

    id: str
    name: str
    description: str
    icon: str


# ---------------------------------------------------------------------------
# Internal dataclass (not exported)
# ---------------------------------------------------------------------------


@dataclass
class _AchievementDefinition:
    """Internal definition for one achievement. Not exported.

    Attributes:
        id: Unique identifier (e.g., "ACH-01").
        name: Display name.
        description: Unlock condition description.
        icon: Icon identifier.
        condition: Callable receiving (board_state, move_count, score, rotten_positions) -> bool.
    """

    id: str
    name: str
    description: str
    icon: str
    condition: Callable[[BoardState, int, int, list[tuple[int, int]]], bool]


# ---------------------------------------------------------------------------
# Helper functions (not exported)
# ---------------------------------------------------------------------------


def _get_max_tile(grid: list[list[int]]) -> int:
    """Return the maximum tile value across the entire grid.

    Args:
        grid: The 4x4 tile value grid from BoardState.grid.

    Returns:
        The maximum tile value, or 0 if the grid is empty or all zeros.
    """
    max_val = 0
    for row in grid:
        for cell in row:
            if cell > max_val:
                max_val = cell
    return max_val


def _count_empty(grid: list[list[int]]) -> int:
    """Return the count of cells with value 0 in the grid.

    Args:
        grid: The 4x4 tile value grid from BoardState.grid.

    Returns:
        Number of cells that are zero (empty).
    """
    return sum(1 for row in grid for cell in row if cell == 0)


# ---------------------------------------------------------------------------
# Module-level achievement definitions (8 condition-callable entries)
# ---------------------------------------------------------------------------

_ACHIEVEMENT_DEFINITIONS: list[_AchievementDefinition] = [
    # ACH-01 — First Bite
    _AchievementDefinition(
        id="ACH-01",
        name="First Bite",
        description="Perform your first merge",
        icon="first_bite",
        condition=lambda board_state, move_count, score, rotten_positions: score > 0,
    ),
    # ACH-02 — Cupcake Collector
    _AchievementDefinition(
        id="ACH-02",
        name="Cupcake Collector",
        description="Reach tile value 32",
        icon="cupcake_collector",
        condition=lambda board_state, move_count, score, rotten_positions: _get_max_tile(
            board_state.grid
        )
        >= 32,
    ),
    # ACH-03 — Cake Master
    _AchievementDefinition(
        id="ACH-03",
        name="Cake Master",
        description="Reach tile value 256",
        icon="cake_master",
        condition=lambda board_state, move_count, score, rotten_positions: _get_max_tile(
            board_state.grid
        )
        >= 256,
    ),
    # ACH-04 — Wedding Planner
    _AchievementDefinition(
        id="ACH-04",
        name="Wedding Planner",
        description="Reach tile value 1024",
        icon="wedding_planner",
        condition=lambda board_state, move_count, score, rotten_positions: _get_max_tile(
            board_state.grid
        )
        >= 1024,
    ),
    # ACH-07 — Speed Chef
    _AchievementDefinition(
        id="ACH-07",
        name="Speed Chef",
        description="Score 1000 in under 20 moves",
        icon="speed_chef",
        condition=lambda board_state, move_count, score, rotten_positions: score >= 1000
        and move_count < 20,
    ),
    # ACH-08 — Marathon Cook
    _AchievementDefinition(
        id="ACH-08",
        name="Marathon Cook",
        description="Survive 100 moves",
        icon="marathon_cook",
        condition=lambda board_state, move_count, score, rotten_positions: move_count >= 100,
    ),
    # ACH-09 — Score King
    _AchievementDefinition(
        id="ACH-09",
        name="Score King",
        description="Reach score 10000",
        icon="score_king",
        condition=lambda board_state, move_count, score, rotten_positions: score >= 10000,
    ),
    # ACH-10 — Full Kitchen
    _AchievementDefinition(
        id="ACH-10",
        name="Full Kitchen",
        description="Fill every cell on the board",
        icon="full_kitchen",
        condition=lambda board_state, move_count, score, rotten_positions: _count_empty(
            board_state.grid
        )
        == 0,
    ),
]


# Achievement metadata for inline-checked achievements (ACH-05, ACH-06, ACH-11, ACH-12).
# These are NOT in _ACHIEVEMENT_DEFINITIONS because their conditions depend on
# self._* tracking state that condition callables cannot access.
_INLINE_ACHIEVEMENTS: dict[str, Achievement] = {
    "ACH-05": Achievement(
        id="ACH-05",
        name="Kitchen Nightmare",
        description="Clear first rotten tile via merge",
        icon="kitchen_nightmare",
    ),
    "ACH-06": Achievement(
        id="ACH-06",
        name="Hygiene Hero",
        description="Clear 10 rotten tiles in one game",
        icon="hygiene_hero",
    ),
    "ACH-11": Achievement(
        id="ACH-11",
        name="No Waste",
        description="Win (reach 2048) without ever clearing a rotten tile",
        icon="no_waste",
    ),
    "ACH-12": Achievement(
        id="ACH-12",
        name="Contamination Survived",
        description="Survive 5 contamination spreads",
        icon="contamination_survived",
    ),
}


# ---------------------------------------------------------------------------
# Achievements evaluator class
# ---------------------------------------------------------------------------


class Achievements:
    """Achievement evaluator with callable conditions (ADR-014).

    Tracks unlocked achievements and game-session tracking state.
    Evaluates all 12 achievement conditions on each call to evaluate().
    Returns only newly unlocked achievements to prevent duplicate reporting.
    """

    def __init__(self) -> None:
        """Initialize with empty unlocked set and zeroed tracking state."""
        self._unlocked: set[str] = set()
        self._previous_rotten_count: int = 0
        self._cumulative_rotten_cleared: int = 0
        self._ever_cleared_rotten: bool = False
        self._cumulative_contaminated: int = 0

    def evaluate(
        self,
        board_state: BoardState,
        move_count: int,
        score: int,
        rotten_positions: list[tuple[int, int]],
    ) -> list[Achievement]:
        """Evaluate all conditions against current state.

        Returns only newly unlocked achievements (not previously in unlocked set).
        Updates internal tracking state based on rotten_positions delta.

        Args:
            board_state: Current grid, score, moves snapshot.
            move_count: Total board-changing moves so far.
            score: Current cumulative score.
            rotten_positions: Positions of currently-active rotten tiles.

        Returns:
            List of newly unlocked Achievement objects (empty if none).
        """
        current_rotten_count = len(rotten_positions)

        # Update tracking state based on delta from previous count
        if current_rotten_count < self._previous_rotten_count:
            self._ever_cleared_rotten = True
            self._cumulative_rotten_cleared += self._previous_rotten_count - current_rotten_count
        elif current_rotten_count > self._previous_rotten_count:
            self._cumulative_contaminated += current_rotten_count - self._previous_rotten_count

        self._previous_rotten_count = current_rotten_count

        newly_unlocked: list[Achievement] = []

        # Main loop: evaluate 8 condition-callable achievements
        for definition in _ACHIEVEMENT_DEFINITIONS:
            if definition.id in self._unlocked:
                continue
            if definition.condition(board_state, move_count, score, rotten_positions):
                self._unlocked.add(definition.id)
                newly_unlocked.append(
                    Achievement(
                        id=definition.id,
                        name=definition.name,
                        description=definition.description,
                        icon=definition.icon,
                    )
                )

        # Inline checks for tracking-dependent achievements (ACH-05, ACH-06, ACH-11, ACH-12)
        # These cannot use condition callables because they depend on self._* state.

        # ACH-05 — Kitchen Nightmare: first rotten tile cleared
        if "ACH-05" not in self._unlocked and self._ever_cleared_rotten:
            self._unlocked.add("ACH-05")
            newly_unlocked.append(_INLINE_ACHIEVEMENTS["ACH-05"])

        # ACH-06 — Hygiene Hero: clear 10 rotten tiles in one game
        if "ACH-06" not in self._unlocked and self._cumulative_rotten_cleared >= 10:
            self._unlocked.add("ACH-06")
            newly_unlocked.append(_INLINE_ACHIEVEMENTS["ACH-06"])

        # ACH-11 — No Waste: reach 2048 without ever clearing a rotten tile
        if (
            "ACH-11" not in self._unlocked
            and _get_max_tile(board_state.grid) >= 2048
            and not self._ever_cleared_rotten
        ):
            self._unlocked.add("ACH-11")
            newly_unlocked.append(_INLINE_ACHIEVEMENTS["ACH-11"])

        # ACH-12 — Contamination Survived: survive 5 contamination spreads
        if "ACH-12" not in self._unlocked and self._cumulative_contaminated >= 5:
            self._unlocked.add("ACH-12")
            newly_unlocked.append(_INLINE_ACHIEVEMENTS["ACH-12"])

        return newly_unlocked

    def to_dict(self) -> dict:
        """Serialize unlocked set and tracking state to JSON-compatible dict.

        Returns:
            A dict with keys: unlocked, previous_rotten_count,
            cumulative_rotten_cleared, ever_cleared_rotten, cumulative_contaminated.
        """
        return {
            "unlocked": sorted(self._unlocked),
            "previous_rotten_count": self._previous_rotten_count,
            "cumulative_rotten_cleared": self._cumulative_rotten_cleared,
            "ever_cleared_rotten": self._ever_cleared_rotten,
            "cumulative_contaminated": self._cumulative_contaminated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Achievements:
        """Reconstruct Achievements from serialized dict.

        Args:
            data: A dict with keys matching to_dict() output.

        Returns:
            A new Achievements instance with restored state.
        """
        ach = cls()
        ach._unlocked = set(data.get("unlocked", []))
        ach._previous_rotten_count = data.get("previous_rotten_count", 0)
        ach._cumulative_rotten_cleared = data.get("cumulative_rotten_cleared", 0)
        ach._ever_cleared_rotten = data.get("ever_cleared_rotten", False)
        ach._cumulative_contaminated = data.get("cumulative_contaminated", 0)
        return ach