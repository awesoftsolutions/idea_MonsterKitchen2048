"""GameSession module — top-level game loop coordinator for Monster Kitchen 2048.

Wires all 6 core modules (Board, Rules, Score, History, Achievements, Twist)
into a unified API that Phase 3-4 renderers consume to drive the game.
A slide direction becomes a complete game turn: history snapshot, board slide,
score update, tile spawn, twist processing, achievement evaluation, and
game-over detection.

Public API:
    MoveResult (dataclass): Return type for GameSession.move().
    GameSession (class): Game loop coordinator with move/undo/save/load.

Dependencies:
    copy, random, dataclasses — stdlib only. src.core.* modules.
Zero rendering dependencies.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Optional

from src.core.achievements import Achievement, Achievements
from src.core.board import Board, BoardState, Direction, GRID_SIZE
from src.core.history import History
from src.core.rules import Rules
from src.core.score import Score
from src.core.twist import Twist, TwistEffect


@dataclass
class MoveResult:
    """Result of a complete game move orchestrated by GameSession.

    Attributes:
        moved: True if the slide changed the board.
        score_delta: Points earned from merges this move (0 if not moved).
        new_achievements: Achievements unlocked this move.
        twist_effect: What the twist system did this move.
    """

    moved: bool = False
    score_delta: int = 0
    new_achievements: list[Achievement] = field(default_factory=list)
    twist_effect: TwistEffect = field(default_factory=TwistEffect)


class GameSession:
    """Game loop coordinator wiring Board, Rules, Score, History, Achievements, Twist.

    Provides the unified API that Phase 3-4 renderers consume.
    Each move() call orchestrates a complete game turn.
    """

    def __init__(
        self,
        rng: Optional[random.Random] = None,
        high_score_path: Optional[str] = None,
    ) -> None:
        """Create a new game session with fresh state.

        Args:
            rng: Optional random.Random for deterministic testing (ADR-010).
                If None, creates an unseeded random.Random().
            high_score_path: Path to high-score JSON file. If None, uses Score default.
        """
        # STEP 1: Resolve the RNG instance
        self._rng: random.Random = rng if rng is not None else random.Random()

        # STEP 2-7: Instantiate all core modules
        self._board = Board(self._rng)
        self._rules = Rules()
        self._score = Score(high_score_path)
        self._score.load_high_score()
        self._history = History()
        self._achievements = Achievements()
        self._twist = Twist(self._rng)

        # STEP 8: Spawn two initial tiles for standard 2048 start
        self._board.spawn_tile()
        self._board.spawn_tile()

    def move(self, direction: Direction) -> MoveResult:
        """Execute one complete game turn: history, slide, score, spawn, twist, achievements.

        Args:
            direction: One of Direction.UP, DOWN, LEFT, RIGHT.

        Returns:
            A MoveResult with moved, score_delta, new_achievements, twist_effect.
        """
        # STEP 1: Capture pre-move state BEFORE any mutation
        pre_move_board_state = self._board.get_state()
        pre_move_score = self._score.get_score()

        # STEP 2: Execute the slide
        slide_result = self._board.move(direction)

        # STEP 3: Check if move was legal
        if not slide_result.moved:
            return MoveResult(
                moved=False,
                score_delta=0,
                new_achievements=[],
                twist_effect=TwistEffect(),
            )

        # STEP 4: Record history snapshot (pre-move state + pre-move score)
        self._history.push((pre_move_board_state, pre_move_score))

        # STEP 5: Update Score with merge delta
        self._score.add(slide_result.score_delta)

        # STEP 6: Spawn a new tile after the slide (gracefully handle full board)
        try:
            self._board.spawn_tile()
        except ValueError:
            pass  # Board is full, continue to twist/achievements

        # STEP 7: Get move count from Board (incremented internally by Board.move())
        move_count = self._board.get_state().moves

        # STEP 8: Process Twist contamination
        twist_effect = self._twist.process_move(self._board, move_count)

        # STEP 9: Evaluate Achievements
        current_board_state = self._board.get_state()
        current_score = self._score.get_score()

        # Scan twist overlay for rotten positions
        overlay = self._twist.get_overlay()
        rotten_positions: list[tuple[int, int]] = []
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if overlay[row][col] > 0:
                    rotten_positions.append((row, col))

        new_achievements = self._achievements.evaluate(
            current_board_state, move_count, current_score, rotten_positions
        )

        # STEP 10: Return MoveResult
        return MoveResult(
            moved=True,
            score_delta=slide_result.score_delta,
            new_achievements=new_achievements,
            twist_effect=twist_effect,
        )

    def undo(self) -> bool:
        """Restore previous board state and score from history.

        Returns:
            True if undo succeeded, False if history is empty.
        """
        # STEP 1: Check if history is available
        if not self._history.can_undo():
            return False

        # STEP 2-3: Pop and restore
        result = self._history.pop()
        if result is None:
            return False

        board_state, saved_score = result
        self._board.set_state(board_state)

        # STEP 4: Restore Score
        self._score.reset()
        self._score.add(saved_score)

        # STEP 5: Achievements remain unchanged by design
        return True

    def new_game(self) -> None:
        """Reset all modules to initial state and spawn two starting tiles."""
        self._board.reset()
        self._score.reset()
        self._history = History()
        self._achievements = Achievements()
        self._twist = Twist(self._rng)
        self._board.spawn_tile()
        self._board.spawn_tile()

    @property
    def game_over(self) -> bool:
        """True if no moves remain, accounting for rotten tile presence."""
        # STEP 1: Check Twist overlay for rotten tiles
        overlay = self._twist.get_overlay()
        has_rotten = False
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if overlay[row][col] > 0:
                    has_rotten = True
                    break
            if has_rotten:
                break

        # STEP 2-3: Delegate to Rules
        return self._rules.is_game_over(self._board, has_rotten)

    def save(self) -> dict:
        """Serialize full game state to a JSON-compatible dict.

        Returns:
            A dict with keys: board, score, moves, history, achievements,
            twist_overlay, twist_spawn_interval, high_score_path, version.
        """
        board_state = self._board.get_state()
        current_score = self._score.get_score()

        # Serialize history stack (reaches into History internals)
        history_data: list[dict] = []
        for state, score in self._history._stack:
            history_data.append({
                "board_state": state.to_dict(),
                "score": score,
            })

        return {
            "board": board_state.to_dict(),
            "score": current_score,
            "history": history_data,
            "achievements": self._achievements.to_dict(),
            "twist_overlay": self._twist.get_overlay(),
            "twist_spawn_interval": self._twist._spawn_interval,
            "version": 1,
        }

    @classmethod
    def load(
        cls,
        data: dict,
        rng: Optional[random.Random] = None,
        high_score_path: Optional[str] = None,
    ) -> GameSession:
        """Reconstruct a GameSession from a saved dict.

        Args:
            data: A dict from save().
            rng: Optional random.Random.
            high_score_path: Optional path to high-score file.

        Returns:
            A restored GameSession instance.

        Raises:
            KeyError: If required keys are missing from data.
        """
        # STEP 1: Create object without spawning tiles
        obj = cls.__new__(cls)
        obj._rng = rng if rng is not None else random.Random()

        obj._board = Board(obj._rng)
        obj._rules = Rules()
        obj._score = Score(high_score_path)
        obj._history = History()
        obj._achievements = Achievements()
        spawn_interval = data.get("twist_spawn_interval", 4)
        obj._twist = Twist(obj._rng, spawn_interval=spawn_interval)

        # STEP 2: Restore Board state
        board_state = BoardState.from_dict(data["board"])
        obj._board.set_state(board_state)

        # STEP 3: Restore Score
        obj._score.reset()
        obj._score.add(data["score"])

        # STEP 4: Restore History stack
        for entry in data["history"]:
            state = BoardState.from_dict(entry["board_state"])
            obj._history.push((state, entry["score"]))

        # STEP 5: Restore Achievements
        obj._achievements = Achievements.from_dict(data["achievements"])

        # STEP 6: Restore Twist overlay
        obj._twist._overlay = copy.deepcopy(data["twist_overlay"])

        return obj