"""Core package for Monster Kitchen 2048.

Re-exports the public API from submodules so callers can import directly::

    from src.core import (
        Board, BoardState, Direction, SlideResult, slide_merge,
        BoardProtocol, Rules, Score,
        Achievement, Achievements, Twist, TwistEffect,
        GameSession, MoveResult,
    )

Import order follows dependency chain: board (leaf) -> rules -> score ->
achievements -> twist -> game_session.
"""
# CHANGELOG:
# - Sprint 2: Added Achievement, Achievements, Twist, TwistEffect, GameSession, MoveResult exports

from src.core.board import Board, BoardState, Direction, SlideResult, slide_merge
from src.core.rules import BoardProtocol, Rules
from src.core.score import Score
from src.core.achievements import Achievement, Achievements
from src.core.twist import Twist, TwistEffect
from src.core.game_session import GameSession, MoveResult

__all__ = [
    "Board",
    "BoardState",
    "Direction",
    "SlideResult",
    "slide_merge",
    "BoardProtocol",
    "Rules",
    "Score",
    "Achievement",
    "Achievements",
    "Twist",
    "TwistEffect",
    "GameSession",
    "MoveResult",
]