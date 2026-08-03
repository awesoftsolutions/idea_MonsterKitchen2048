"""Verification tests for visual-proof/README.md manifest completeness.

Confirms that the visual-proof README documents every PNG screenshot file
in the visual-proof/ directory and contains accurate AC-to-screenshot
mappings, false-positive corrections, and viewing instructions. These
tests are part of Phase 5 Sprint 1 and serve as the manifest
completeness check referenced in the sprint plan's "Tests To Create"
section.

Contract:
    Purpose: Verify manifest completeness for Phase 5 exit criteria.
    System: pytest test runner (discovered via tests/ directory)
    Dependencies: pathlib (stdlib only), re (stdlib only)
    Used-by: pytest discovery, CI pipeline
    Public Interface:
        test_readme_covers_all_pngs() -> None
        test_readme_covers_all_pngs_has_count() -> None
        test_readme_has_viewing_instructions() -> None
        test_readme_has_sow_ac_coverage_table() -> None
        test_readme_covers_all_sow_acs() -> None
        test_readme_has_corrections_log() -> None
        test_readme_corrections_are_true_positives() -> None
        test_readme_no_false_positive_ac_claims() -> None
        test_readme_ac5_gap_documented() -> None
        test_readme_screenshot_inventory_complete() -> None
        test_readme_false_positive_corrections_match() -> None
        test_sow_ac_coverage_table_ac_count() -> None
        test_sow_ac_coverage_categories_complete() -> None
        test_corrections_log_comprehensive() -> None
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
# CHANGELOG:
# - Sprint 1 Task 2: Added 8 manifest verification tests for rewritten README structure (SOW AC table, corrections log, false-positive elimination, field completeness)
# - Sprint 4 Task 2: Added 3 manifest verification tests for visual-proof README (screenshot existence, viewing instructions, window dimensions)


# ---------------------------------------------------------------------------
# Sprint 5 Helper Functions
# ---------------------------------------------------------------------------


def _parse_table_rows(section_heading: str) -> list[str]:
    """Return non-empty data rows from the markdown table under *section_heading*.

    Locates the section by heading text, skips header and separator rows
    (lines containing only `|---`), and returns each data row as a
    pipe-delimited string. Returns an empty list if the section or table
    is not found.
    """
    text = README_PATH.read_text(encoding="utf-8").splitlines()
    in_section = False
    in_table = False
    rows: list[str] = []
    for line in text:
        stripped = line.strip()
        if stripped.startswith("#") and section_heading in stripped:
            in_section = True
            in_table = False
            rows = []
            continue
        if in_section and stripped.startswith("#") and not stripped.startswith(section_heading[0:2]):
            break
        if in_section and stripped.startswith("|"):
            if not in_table:
                in_table = True
                continue
            if re.match(r"^\|[\s\-:|]+\|$", stripped):
                continue
            rows.append(stripped)
        elif in_section and in_table and not stripped.startswith("|"):
            break
    return rows


# ---------------------------------------------------------------------------
# Sprint 5 Tests — Manifest Structure Verification
# ---------------------------------------------------------------------------


def test_sow_ac_coverage_table_exists() -> None:
    """SOW AC Coverage Table section must exist in the rewritten manifest.

    After Step 3 rewrite the README.md should contain a '## SOW AC Coverage Table'
    section with a markdown table mapping all 14 SOW acceptance criteria. This test
    FAILS against the current (pre-rewrite) README because that section does not exist.
    """
    text = README_PATH.read_text(encoding="utf-8")
    has_heading = bool(re.search(r"#+\s*SOW AC Coverage Table", text))
    rows = _parse_table_rows("SOW AC Coverage Table")
    assert has_heading, "README.md is missing the 'SOW AC Coverage Table' section heading"
    assert len(rows) == 14, (
        f"SOW AC Coverage Table should have exactly 14 rows but found {len(rows)}. "
        f"All SOW ACs (AC-1 through AC-14) must be represented."
    )


def test_sow_ac_5_documented_as_automated_only() -> None:
    """AC-5 row in SOW AC Coverage Table must state it is verified by automated tests only.

    AC-5 (undo restores state) cannot be captured as a screenshot per ADR-030.
    The rewritten manifest must explicitly note 'automated tests only' in AC-5's
    evidence description. FAILS against current README because the SOW AC table
    does not exist.
    """
    rows = _parse_table_rows("SOW AC Coverage Table")
    ac5_row = next((r for r in rows if "AC-5" in r), None)
    assert ac5_row is not None, "AC-5 not found in SOW AC Coverage Table"
    assert "automated tests only" in ac5_row.lower(), (
        f"AC-5 row must state 'verified by automated tests only' but got: {ac5_row}"
    )


def test_false_positive_corrections_log_exists() -> None:
    """False-Positive Corrections Log section must exist with at least 7 entries.

    The rewritten manifest must document all 7 corrections from the Task 1
    coverage matrix. FAILS against current README because the section does not exist.
    """
    text = README_PATH.read_text(encoding="utf-8")
    has_heading = bool(re.search(r"#+\s*False-Positive Corrections Log", text))
    rows = _parse_table_rows("False-Positive Corrections Log")
    assert has_heading, (
        "README.md is missing the 'False-Positive Corrections Log' section heading"
    )
    assert len(rows) >= 7, (
        f"False-Positive Corrections Log should have at least 7 corrections but found {len(rows)}"
    )


def test_screenshot_inventory_has_required_fields() -> None:
    """Every screenshot entry must have all 5 required fields (columns).

    Each row in the Screenshot Inventory table must provide: Filename, Phase,
    Description, Input Sequence, and AC Coverage. This test verifies column
    count. Should PASS against current README since it already has 5 columns.
    """
    rows = _parse_table_rows("Screenshot Inventory")
    assert len(rows) == 10, f"Expected 10 screenshot entries but found {len(rows)}"
    for row in rows:
        columns = [c.strip() for c in row.split("|") if c.strip()]
        assert len(columns) == 5, (
            f"Screenshot entry should have 5 fields but found {len(columns)}: {row}"
        )


def test_phase4_feedback_no_false_positive_ac7() -> None:
    """phase4_feedback.png must NOT claim AC-7 (high score persists).

    False positive #1 from coverage matrix. AC-7 is automated-only — a single
    screenshot cannot demonstrate cross-session persistence. FAILS against current
    README because AC-7 appears in the AC Coverage column.
    """
    rows = _parse_table_rows("Screenshot Inventory")
    row = next((r for r in rows if "phase4_feedback.png" in r), None)
    assert row is not None, "phase4_feedback.png not found in Screenshot Inventory"
    columns = [c.strip() for c in row.split("|") if c.strip()]
    ac_coverage = columns[4] if len(columns) > 4 else ""
    assert "AC-7" not in ac_coverage, (
        f"phase4_feedback.png must not claim AC-7 (false positive) but got: {ac_coverage}"
    )


def test_phase4_mid_game_no_false_positive_ac3() -> None:
    """phase4_mid_game.png must NOT claim AC-3 (spawn distribution).

    False positive #3 from coverage matrix. AC-3 is automated-only — a single
    screenshot cannot show the 90/10 spawn distribution. FAILS against current
    README because AC-3 appears in the AC Coverage column.
    """
    rows = _parse_table_rows("Screenshot Inventory")
    row = next((r for r in rows if "phase4_mid_game.png" in r), None)
    assert row is not None, "phase4_mid_game.png not found in Screenshot Inventory"
    columns = [c.strip() for c in row.split("|") if c.strip()]
    ac_coverage = columns[4] if len(columns) > 4 else ""
    assert "AC-3" not in ac_coverage, (
        f"phase4_mid_game.png must not claim AC-3 (false positive) but got: {ac_coverage}"
    )


def test_phase4_mid_game_no_false_positive_ac5() -> None:
    """phase4_mid_game.png must NOT claim AC-5 (undo restores state).

    False positive #4 from coverage matrix. AC-5 is uncapturable per ADR-030.
    FAILS against current README because AC-5 appears in the AC Coverage column.
    """
    rows = _parse_table_rows("Screenshot Inventory")
    row = next((r for r in rows if "phase4_mid_game.png" in r), None)
    assert row is not None, "phase4_mid_game.png not found in Screenshot Inventory"
    columns = [c.strip() for c in row.split("|") if c.strip()]
    ac_coverage = columns[4] if len(columns) > 4 else ""
    assert "AC-5" not in ac_coverage, (
        f"phase4_mid_game.png must not claim AC-5 (false positive) but got: {ac_coverage}"
    )


def test_phase4_game_over_no_false_positive_ac7() -> None:
    """phase4_game_over.png must NOT claim AC-7 (high score persists).

    False positive #5 from coverage matrix. FAILS against current README because
    AC-7 appears in the AC Coverage column.
    """
    rows = _parse_table_rows("Screenshot Inventory")
    row = next((r for r in rows if "phase4_game_over.png" in r), None)
    assert row is not None, "phase4_game_over.png not found in Screenshot Inventory"
    columns = [c.strip() for c in row.split("|") if c.strip()]
    ac_coverage = columns[4] if len(columns) > 4 else ""
    assert "AC-7" not in ac_coverage, (
        f"phase4_game_over.png must not claim AC-7 (false positive) but got: {ac_coverage}"
    )


def test_phase4_game_over_no_false_positive_ac5() -> None:
    """phase4_game_over.png must NOT claim AC-5 (undo restores state).

    False positive #6 from coverage matrix. FAILS against current README because
    AC-5 appears in the AC Coverage column.
    """
    rows = _parse_table_rows("Screenshot Inventory")
    row = next((r for r in rows if "phase4_game_over.png" in r), None)
    assert row is not None, "phase4_game_over.png not found in Screenshot Inventory"
    columns = [c.strip() for c in row.split("|") if c.strip()]
    ac_coverage = columns[4] if len(columns) > 4 else ""
    assert "AC-5" not in ac_coverage, (
        f"phase4_game_over.png must not claim AC-5 (false positive) but got: {ac_coverage}"
    )


def test_phase4_feedback_no_false_positive_ac3() -> None:
    """phase4_feedback.png must NOT claim AC-3 (spawn distribution).

    False positive #2 from coverage matrix. AC-3 is automated-only. FAILS against
    current README because AC-3 appears in the AC Coverage column.
    """
    rows = _parse_table_rows("Screenshot Inventory")
    row = next((r for r in rows if "phase4_feedback.png" in r), None)
    assert row is not None, "phase4_feedback.png not found in Screenshot Inventory"
    columns = [c.strip() for c in row.split("|") if c.strip()]
    ac_coverage = columns[4] if len(columns) > 4 else ""
    assert "AC-3" not in ac_coverage, (
        f"phase4_feedback.png must not claim AC-3 (false positive) but got: {ac_coverage}"
    )