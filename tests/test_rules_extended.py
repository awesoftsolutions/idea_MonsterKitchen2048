"""Extended pytest test suite for the slide_merge algorithm — green phase.

Adds 3 new hand-worked board states that exercise scenarios not covered
by the existing 16 tests in tests/test_rules.py. Targets complex multi-row
multi-direction merges, large-value merges, and double-pair patterns.

Acceptance criteria coverage:
    AC-1  — 3 new hand-worked board states (not duplicates of existing 16)
    AC-2  — test_complex_4x4_multirow_down (complex 4×4 multi-row board)
    AC-3  — test_large_value_merge_128_128 (128+128=256 large-value merge)
    AC-3  — test_double_pair_merge_row ([2,2,2,2] → [4,4] double-pair)
"""

from __future__ import annotations

from src.core.rules import Direction, slide_merge


# ---------------------------------------------------------------------------
# Test 1: Complex 4×4 multi-row DOWN slide (AC-2)
# ---------------------------------------------------------------------------


def test_complex_4x4_multirow_down() -> None:
  """DOWN slide on a realistic mid-game 4×4 board with merges in multiple columns.

  Column-by-column expected derivation:
    Col 0: [2,4,2,0] → DOWN → [0,2,4,2] (no merge, gap fill)
    Col 1: [4,4,2,0] → DOWN → [0,0,8,2] (merge 4+4=8, score 8)
    Col 2: [2,0,4,0] → DOWN → [0,0,2,4] (no merge, gap fill)
    Col 3: [8,8,0,2] → DOWN → [0,0,16,2] (merge 8+8=16, score 16)
  Total score: 0 + 8 + 0 + 16 = 24
  """
  input_grid: list[list[int]] = [
    [2, 4, 2, 8],
    [4, 4, 0, 8],
    [2, 2, 4, 0],
    [0, 0, 0, 2],
  ]
  expected_grid: list[list[int]] = [
    [0, 0, 0, 0],
    [2, 0, 0, 0],
    [4, 8, 2, 16],
    [2, 2, 4, 2],
  ]

  new_grid, score_delta = slide_merge(input_grid, Direction.DOWN)

  assert new_grid == expected_grid
  assert score_delta == 24


# ---------------------------------------------------------------------------
# Test 2: Large-value merge 128+128=256 (AC-3)
# ---------------------------------------------------------------------------


def test_large_value_merge_128_128() -> None:
  """LEFT slide merging 128+128=256; verifies large power-of-two handling.

  Row: [0, 128, 128, 0] → compact: [128, 128, 0, 0] → merge: [256, 0, 0, 0]
  Score: 256
  """
  input_grid: list[list[int]] = [[0, 128, 128, 0]]
  expected_grid: list[list[int]] = [[256, 0, 0, 0]]

  new_grid, score_delta = slide_merge(input_grid, Direction.LEFT)

  assert new_grid == expected_grid
  assert score_delta == 256


# ---------------------------------------------------------------------------
# Test 3: Double-pair merge row (AC-3)
# ---------------------------------------------------------------------------


def test_double_pair_merge_row() -> None:
  """LEFT slide on [2, 2, 2, 2] producing two independent merges.

  Row: [2, 2, 2, 2] → compact: [2, 2, 2, 2]
  → merge: pair (0,1)=4, pair (2,3)=4 → [4, 4, 0, 0]
  Score: 4 + 4 = 8
  CRITICAL: must NOT cascade into [8, 0, 0, 0] — one merge per tile.
  """
  input_grid: list[list[int]] = [[2, 2, 2, 2]]
  expected_grid: list[list[int]] = [[4, 4, 0, 0]]

  new_grid, score_delta = slide_merge(input_grid, Direction.LEFT)

  assert new_grid == expected_grid
  assert new_grid != [[8, 0, 0, 0]], "Double merge cascade must not occur"
  assert score_delta == 8