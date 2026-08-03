"""Verification tests for visual-proof/README.md manifest completeness.

Confirms that the visual-proof README documents every PNG screenshot file
in the visual-proof/ directory and contains viewing instructions. These tests
are part of Sprint 4 Task 2 (Phase 4) and serve as the manifest completeness
check referenced in the sprint plan's "Tests To Create" section.

Contract:
    Purpose: Verify manifest completeness for Phase 4 exit criteria.
    System: pytest test runner (discovered via tests/ directory)
    Dependencies: pathlib (stdlib only), re (stdlib only)
    Used-by: pytest discovery, CI pipeline
    Public Interface:
        test_readme_covers_all_pngs() -> None
        test_readme_has_viewing_instructions() -> None
"""

import re
from pathlib import Path

VISUAL_PROOF_DIR = Path(__file__).resolve().parent.parent / "visual-proof"
README_PATH = VISUAL_PROOF_DIR / "README.md"


def test_readme_covers_all_pngs() -> None:
    """Every .png file in visual-proof/ must be mentioned in README.md.

    Enumerates all PNG files in the visual-proof directory using pathlib,
    reads the README content, and asserts that each PNG filename appears
    as a substring. This ensures the manifest is complete and no screenshot
    is undocumented.
    """
    png_files = sorted(VISUAL_PROOF_DIR.glob("*.png"))
    assert png_files, f"No PNG files found in {VISUAL_PROOF_DIR}"

    readme_content = README_PATH.read_text(encoding="utf-8")

    missing = []
    for png_path in png_files:
        if png_path.name not in readme_content:
            missing.append(png_path.name)

    assert not missing, (
        f"The following PNG files exist in visual-proof/ but are NOT "
        f"mentioned in README.md: {missing}. "
        f"Each screenshot must have a corresponding entry in the manifest."
    )


def test_readme_covers_all_pngs_has_count() -> None:
    """The README must reference at least as many .png filenames as exist on disk.

    A secondary count-based check to catch cases where the README might
    list filenames in bulk but miss individual entries.
    """
    png_count = len(list(VISUAL_PROOF_DIR.glob("*.png")))

    readme_content = README_PATH.read_text(encoding="utf-8")

    png_mentions = 0
    for png_path in VISUAL_PROOF_DIR.glob("*.png"):
        if png_path.name in readme_content:
            png_mentions += 1

    assert png_mentions == png_count, (
        f"README.md references {png_mentions} of {png_count} PNG files. "
        f"All PNG screenshots must be documented in the manifest."
    )


def test_readme_has_viewing_instructions() -> None:
    """README.md must contain a 'How to View' section with launch command and window details."""

    readme_content = README_PATH.read_text(encoding="utf-8")

    # Check for 'How to View' section heading
    has_how_to_view = bool(
        re.search(r"#+\s*How to View", readme_content, re.IGNORECASE)
    )

    # Check for the launch command
    has_launch_command = "poetry run python -m src.main" in readme_content

    # Check for window details (size or dimensions mentioned)
    has_window_details = bool(re.search(r"700\s*[x×]\s*800", readme_content))

    failures = []
    if not has_how_to_view:
        failures.append(
            "Missing '## How to View' section (or equivalent heading "
            "with 'How to View' text)"
        )
    if not has_launch_command:
        failures.append("Missing launch command 'poetry run python -m src.main'")
    if not has_window_details:
        failures.append(
            "Missing window dimensions (expected '700 x 800' or equivalent)"
        )

    assert not failures, (
        f"README.md is missing viewing instructions: {failures}. "
        f"The manifest must tell users how to view screenshots and reproduce them."
    )
