"""Verification script for Phase 1 Direction Document constraint compliance.

Checks that the spike-vs-source file restructuring (Sprint 2) satisfies all
Phase 1 Direction Document constraints:
    CON-C01: spikes/slide_merge.py exists as the canonical slide_merge module.
    CON-C02: src/ directory does not exist (code lives in spikes/).
    CON-C03: No stale src.core imports remain in spikes/ files.

Run via: python spikes/verify_constraint_compliance.py

Exit codes:
    0 ── all checks passed
    1 ── one or more checks failed
"""
# CHANGELOG:
# - Sprint 2: Created constraint compliance verification script

from __future__ import annotations

import glob
import importlib
import os
import sys

# Ensure project root is on sys.path for import resolution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check(condition: bool, description: str) -> bool:
    """Print pass/fail for a single check and return the result.

    Args:
        condition: Boolean result of the check.
        description: Human-readable description of what was checked.

    Returns:
        The condition value (True if passed, False if failed).
    """
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {description}")
    return condition


def main() -> None:
    """Run all Phase 1 constraint compliance checks."""
    print("=" * 60)
    print("Phase 1 Direction Document ── Constraint Compliance")
    print("=" * 60)

    all_passed = True

    # --- CON-C01: spikes/slide_merge.py exists as valid Python file ---
    print("\nCON-C01: spikes/slide_merge.py exists and is a valid Python file")
    slide_merge_path = os.path.join("spikes", "slide_merge.py")
    all_passed &= check(
        os.path.isfile(slide_merge_path),
        f"{slide_merge_path} exists",
    )
    if os.path.isfile(slide_merge_path):
        all_passed &= check(
            slide_merge_path.endswith(".py"),
            f"{slide_merge_path} has .py extension",
        )

    # --- CON-C02: src/ directory does not exist ---
    print("\nCON-C02: No src/ directory present")
    all_passed &= check(
        not os.path.isdir("src"),
        "src/ directory does not exist",
    )

    # --- CON-C02b: tests/ directory does not exist ---
    print("\nCON-C02b: No tests/ directory present")
    all_passed &= check(
        not os.path.isdir("tests"),
        "tests/ directory does not exist",
    )

    # --- CON-C01b: spikes/slide_merge.py is importable ---
    print("\nCON-C01b: spikes/slide_merge.py can be imported with full contract")
    try:
        mod = importlib.import_module("spikes.slide_merge")
        has_direction = hasattr(mod, "Direction")
        has_slide_result = hasattr(mod, "SlideResult")
        has_slide_merge = hasattr(mod, "slide_merge")
        all_passed &= check(
            has_direction, "Direction is importable from spikes.slide_merge"
        )
        all_passed &= check(
            has_slide_result, "SlideResult is importable from spikes.slide_merge"
        )
        all_passed &= check(
            has_slide_merge, "slide_merge is importable from spikes.slide_merge"
        )
    except ImportError as exc:
        all_passed &= check(False, f"Import failed: {exc}")
    except Exception as exc:
        all_passed &= check(False, f"Unexpected error during import: {exc}")

    # --- CON-C03: No stale src.core imports in spikes/ ---
    # Skip this script itself — it contains the literal string "from src.core"
    # in its check logic, which is not an actual import.
    print("\nCON-C03: No stale 'from src.core' imports in spikes/")
    self_path = os.path.abspath(__file__)
    spike_files = [
        f
        for f in glob.glob(os.path.join("spikes", "*.py"))
        if os.path.abspath(f) != self_path
    ]
    any_stale = False
    for spike_file in sorted(spike_files):
        with open(spike_file, encoding="utf-8") as f:
            content = f.read()
        if "from src.core" in content:
            all_passed &= check(False, f"Stale import found in {spike_file}")
            any_stale = True
    if not any_stale:
        all_passed &= check(
            True,
            f"No 'from src.core' imports found in {len(spike_files)} spikes/ files",
        )

    # --- CON-C01c: README.md no longer references src/ or tests/ paths ---
    print("\nCON-C01c: README.md does not reference src/ or tests/")
    readme_path = "README.md"
    if os.path.isfile(readme_path):
        with open(readme_path, encoding="utf-8") as f:
            readme_content = f.read()
        all_passed &= check(
            "src/" not in readme_content,
            "README.md does not reference src/",
        )
        all_passed &= check(
            "tests/" not in readme_content,
            "README.md does not reference tests/",
        )
    else:
        all_passed &= check(False, f"{readme_path} does not exist")

    # --- Summary ---
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL CHECKS PASSED — Phase 1 constraints verified")
    else:
        print("SOME CHECKS FAILED — review output above")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
