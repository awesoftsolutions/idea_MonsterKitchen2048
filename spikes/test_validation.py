"""Standalone validation script for the SlideResult dataclass contract.

Runs 3 validation cases derived from tests/test_rules_extended.py.
Executes as a standalone script (NOT under pytest).
Uses assert statements and print-based pass/fail reporting.

Exit codes:
    0 — all validations passed
    1 — one or more validations failed

NOTE: This script expects SlideResult to be importable from spikes.slide_merge.
      During TDD red phase it will fail with ImportError — this is expected.
"""

from __future__ import annotations

import os
import sys

# Ensure spikes/ is importable when running as a standalone script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spikes.slide_merge import Direction, SlideResult, slide_merge  # noqa: E402, I001

passed = 0
failed = 0


# ---------------------------------------------------------------------------
# Validation 1: Complex 4×4 multi-row DOWN slide
# (derived from test_complex_4x4_multirow_down in tests/test_rules_extended.py)
# ---------------------------------------------------------------------------

try:
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
    expected_score = 24

    result = slide_merge(input_grid, Direction.DOWN)

    assert isinstance(result, SlideResult), f"Expected SlideResult, got {type(result)}"
    assert result.grid == expected_grid, (
        f"Grid mismatch: {result.grid} != {expected_grid}"
    )
    assert result.score == expected_score, (
        f"Score mismatch: {result.score} != {expected_score}"
    )

    print("PASS: Validation 1 — complex 4×4 multi-row DOWN slide")
    passed += 1
except Exception as e:
    print(f"FAIL: Validation 1 — complex 4×4 multi-row DOWN slide: {e}")
    failed += 1


# ---------------------------------------------------------------------------
# Validation 2: Large-value merge 128+128=256
# (derived from test_large_value_merge_128_128 in tests/test_rules_extended.py)
# ---------------------------------------------------------------------------

try:
    input_grid = [[0, 128, 128, 0]]
    expected_grid = [[256, 0, 0, 0]]
    expected_score = 256

    result = slide_merge(input_grid, Direction.LEFT)

    assert isinstance(result, SlideResult), f"Expected SlideResult, got {type(result)}"
    assert result.grid == expected_grid, (
        f"Grid mismatch: {result.grid} != {expected_grid}"
    )
    assert result.score == expected_score, (
        f"Score mismatch: {result.score} != {expected_score}"
    )

    print("PASS: Validation 2 — large-value merge 128+128=256")
    passed += 1
except Exception as e:
    print(f"FAIL: Validation 2 — large-value merge 128+128=256: {e}")
    failed += 1


# ---------------------------------------------------------------------------
# Validation 3: Double-pair merge row [2,2,2,2] → [4,4]
# (derived from test_double_pair_merge_row in tests/test_rules_extended.py)
# ---------------------------------------------------------------------------

try:
    input_grid = [[2, 2, 2, 2]]
    expected_grid = [[4, 4, 0, 0]]
    expected_score = 8

    result = slide_merge(input_grid, Direction.LEFT)

    assert isinstance(result, SlideResult), f"Expected SlideResult, got {type(result)}"
    assert result.grid == expected_grid, (
        f"Grid mismatch: {result.grid} != {expected_grid}"
    )
    assert result.score == expected_score, (
        f"Score mismatch: {result.score} != {expected_score}"
    )
    assert result.grid != [[8, 0, 0, 0]], "Double merge cascade must not occur"

    print("PASS: Validation 3 — double-pair merge row [2,2,2,2] → [4,4]")
    passed += 1
except Exception as e:
    print(f"FAIL: Validation 3 — double-pair merge row [2,2,2,2] → [4,4]: {e}")
    failed += 1


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print(f"\nResults: {passed} passed, {failed} failed, {passed + failed} total")
sys.exit(0 if failed == 0 else 1)
