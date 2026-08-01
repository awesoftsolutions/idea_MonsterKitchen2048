"""Score module for Monster Kitchen 2048.

Tracks the current game score by accumulating merge value deltas.
Manages high-score persistence to disk as JSON per ADR-008.

Handles corrupt, missing, or empty high-score files gracefully
(returns 0, overwrites on next save). Only stdlib imports — zero
rendering dependencies.

Error codes: E-S01 (corrupt file → 0), E-S02 (missing file → 0),
E-S03 (write failure → log warning, no raise).
"""
# CHANGELOG:
# - Sprint 1: Created Score module for score tracking and high-score persistence

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_HIGH_SCORE_PATH = Path.home() / ".the2048" / "high_score.json"


class Score:
    """Score tracking and high-score persistence for Monster Kitchen 2048.

    Accumulates merge value deltas as the current score. Maintains an
    in-memory high score that auto-updates whenever the current score
    exceeds it. Persists the high score to a JSON file on disk.

    Args:
        high_score_path: Path to the JSON file for high-score persistence.
            Defaults to ``~/.the2048/high_score.json``.
    """

    def __init__(self, high_score_path: str | None = None) -> None:
        self._current_score: int = 0
        self._high_score: int = 0
        self._high_score_path: Path = (
            Path(high_score_path) if high_score_path else _DEFAULT_HIGH_SCORE_PATH
        )

    def add(self, delta: int) -> None:
        """Add *delta* to the current score.

        Automatically updates the in-memory high score if the new current
        score exceeds it.

        Args:
            delta: The merge value to add (must be non-negative in practice).
        """
        self._current_score += delta
        if self._current_score > self._high_score:
            self._high_score = self._current_score

    def get_score(self) -> int:
        """Return the current score."""
        return self._current_score

    def get_high_score(self) -> int:
        """Return the best score (from memory or disk).

        Returns the in-memory high score, which is the maximum of the
        value loaded from disk and the highest current score reached.
        """
        return self._high_score

    def load_high_score(self) -> int:
        """Read the high score from disk.

        Returns:
            The persisted high score, or 0 on any error (missing file,
            corrupt JSON, missing key, non-integer value).
        """
        try:
            data = json.loads(self._high_score_path.read_text(encoding="utf-8"))
            value = data["high_score"]
            if not isinstance(value, int):
                return 0
            self._high_score = value
            return value
        except (
            FileNotFoundError,
            json.JSONDecodeError,
            KeyError,
            ValueError,
            TypeError,
        ):
            return 0

    def save_high_score(self) -> None:
        """Write the current high score to disk as JSON.

        Creates parent directories if they don't exist. Logs a warning on
        write failure but does NOT raise (E-S03).
        """
        try:
            self._high_score_path.parent.mkdir(parents=True, exist_ok=True)
            self._high_score_path.write_text(
                json.dumps({"high_score": self._high_score}),
                encoding="utf-8",
            )
        except Exception:
            logger.warning(
                "Failed to save high score to %s",
                self._high_score_path,
                exc_info=True,
            )

    def reset(self) -> None:
        """Reset the current score to zero.

        Does NOT touch the high score — it persists in memory and on disk.
        """
        self._current_score = 0
