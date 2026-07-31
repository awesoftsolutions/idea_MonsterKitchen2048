"""Test suite for src/core/score.py — Score class interface.

13 standalone test functions covering all acceptance criteria from
Sprint 1 Task 2 (Score Module) architecture contract (IF-Score).

All tests use tmp_path for file-based tests to avoid writing to the
real home directory. Tests are designed to FAIL until src/core/score.py
is implemented (TDD red phase).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest  # noqa: F401 — required for tmp_path fixture

from src.core.score import Score


# ---------------------------------------------------------------------------
# Initial State
# ---------------------------------------------------------------------------


def test_score_initial_score_is_zero() -> None:
    """AC: Fresh Score has current score of 0."""
    score = Score()
    assert score.get_score() == 0


# ---------------------------------------------------------------------------
# Score Accumulation
# ---------------------------------------------------------------------------


def test_score_add_accumulates() -> None:
    """AC: add() accumulates score correctly."""
    score = Score()
    score.add(100)
    score.add(50)
    assert score.get_score() == 150


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


def test_score_reset_clears_current() -> None:
    """AC: reset() zeroes the current score."""
    score = Score()
    score.add(100)
    score.reset()
    assert score.get_score() == 0


def test_score_reset_preserves_high_score_on_disk(
    tmp_path: Path,
) -> None:
    """AC: reset() clears current score but high score persists on disk.

    After saving high_score to disk, reset clears the current score.
    A fresh Score instance loading from the same path should read the
    persisted high score.
    """
    path = tmp_path / "high_score.json"
    score = Score(high_score_path=str(path))
    score.add(100)
    score.save_high_score()
    score.reset()
    assert score.get_score() == 0
    assert score.get_high_score() == 100


# ---------------------------------------------------------------------------
# High Score Persistence
# ---------------------------------------------------------------------------


def test_high_score_persists_to_json(
    tmp_path: Path,
) -> None:
    """AC: save_high_score writes {"high_score": N} to the JSON file."""
    path = tmp_path / "score.json"
    score = Score(high_score_path=str(path))
    score.add(250)
    score.save_high_score()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {"high_score": 250}


def test_high_score_loads_from_json(
    tmp_path: Path,
) -> None:
    """AC: load_high_score reads {"high_score": N} from a JSON file."""
    path = tmp_path / "score.json"
    path.write_text(json.dumps({"high_score": 500}), encoding="utf-8")
    score = Score(high_score_path=str(path))
    assert score.load_high_score() == 500


# ---------------------------------------------------------------------------
# Missing File (E-S02)
# ---------------------------------------------------------------------------


def test_high_score_missing_file_returns_zero(
    tmp_path: Path,
) -> None:
    """E-S02: Missing high score file returns 0 (no exception)."""
    path = tmp_path / "nonexistent.json"
    score = Score(high_score_path=str(path))
    assert score.load_high_score() == 0


# ---------------------------------------------------------------------------
# Auto-Update
# ---------------------------------------------------------------------------


def test_high_score_auto_updates() -> None:
    """AC: get_high_score returns the current score when it exceeds stored high."""
    score = Score()
    score.add(300)
    assert score.get_high_score() == 300


# ---------------------------------------------------------------------------
# High Score Does Not Decrease
# ---------------------------------------------------------------------------


def test_high_score_does_not_decrease(
    tmp_path: Path,
) -> None:
    """AC: High score is preserved across resets — only increases."""
    path = tmp_path / "score.json"
    score = Score(high_score_path=str(path))
    score.add(500)
    score.save_high_score()
    score.reset()
    score.add(100)
    assert score.get_high_score() == 500


# ---------------------------------------------------------------------------
# Corrupt / Invalid JSON (E-S01)
# ---------------------------------------------------------------------------


def test_corrupt_json_returns_zero(
    tmp_path: Path,
) -> None:
    """E-S01: Corrupt (unparseable) JSON returns 0, no exception raised."""
    path = tmp_path / "score.json"
    path.write_text("not json at all", encoding="utf-8")
    score = Score(high_score_path=str(path))
    assert score.load_high_score() == 0


def test_corrupt_structure_returns_zero(
    tmp_path: Path,
) -> None:
    """E-S01: Valid JSON with wrong schema returns 0."""
    path = tmp_path / "score.json"
    path.write_text(json.dumps({"wrong_key": 123}), encoding="utf-8")
    score = Score(high_score_path=str(path))
    assert score.load_high_score() == 0


def test_non_integer_value_returns_zero(
    tmp_path: Path,
) -> None:
    """E-S01: Valid JSON with non-int high_score value returns 0."""
    path = tmp_path / "score.json"
    path.write_text(json.dumps({"high_score": "not_int"}), encoding="utf-8")
    score = Score(high_score_path=str(path))
    assert score.load_high_score() == 0


# ---------------------------------------------------------------------------
# Directory Creation
# ---------------------------------------------------------------------------


def test_save_creates_directory(
    tmp_path: Path,
) -> None:
    """AC: save_high_score creates parent directories if they don't exist."""
    path = tmp_path / "subdir" / "score.json"
    score = Score(high_score_path=str(path))
    assert not path.parent.exists()
    score.save_high_score()
    assert path.parent.exists()
    assert path.exists()
