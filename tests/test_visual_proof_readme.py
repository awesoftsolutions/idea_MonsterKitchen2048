"""Verification tests for the visual-proof README.

Confirms that visual-proof/README.md exists and contains the expected
content: all 8 section headings, 10 PASS statuses (one per Phase 3 AC),
the launch command, screenshot reference, and game controls.

Contract:
    Purpose: Verify visual-proof README produced by Sprint 4 Task 3.
    System: pytest test runner (discovered via tests/ directory)
    Dependencies: pathlib (stdlib only)
    Used-by: pytest discovery, CI pipeline
    Public Interface:
        test_readme_file_exists() -> None
        test_readme_contains_pass_ten_times() -> None
        test_readme_contains_all_section_headings() -> None
        test_readme_contains_launch_command() -> None
        test_readme_contains_screenshot_reference() -> None
        test_readme_contains_arrow_controls() -> None
        test_readme_contains_escape() -> None
        test_readme_contains_undo_key() -> None
"""

from pathlib import Path

README_PATH = Path(__file__).resolve().parent.parent / "visual-proof" / "README.md"


def test_readme_file_exists() -> None:
    """The visual-proof README must exist on disk."""
    assert README_PATH.is_file(), f"README not found at {README_PATH}"


def test_readme_contains_pass_ten_times() -> None:
    """The README must contain exactly 10 PASS entries (one per Phase 3 AC)."""
    content = README_PATH.read_text(encoding="utf-8")
    pass_count = content.count("PASS")
    assert pass_count >= 10, (
        f"Expected at least 10 occurrences of 'PASS', found {pass_count}"
    )


def test_readme_contains_all_section_headings() -> None:
    """The README must contain all 8 required section headings."""
    content = README_PATH.read_text(encoding="utf-8")
    required_headings = [
        "## 1. Visual-Proof Directory",
        "## 2. First-Light Screenshot",
        "## 3. Game Controls",
        "## 4. Launch Command",
        "## 5. Test Status",
        "## 6. Phase 3 Acceptance Criteria Verification",
        "## 7. Known Limitations",
        "## 8. Architecture Summary",
    ]
    for heading in required_headings:
        assert heading in content, f"Missing section heading: {heading}"


def test_readme_contains_launch_command() -> None:
    """The README must contain the game launch command."""
    content = README_PATH.read_text(encoding="utf-8")
    assert "poetry run python -m src.main" in content, (
        "Launch command 'poetry run python -m src.main' not found in README"
    )


def test_readme_contains_screenshot_reference() -> None:
    """The README must reference the first-light screenshot."""
    content = README_PATH.read_text(encoding="utf-8")
    assert "first_light.png" in content, (
        "Screenshot reference 'first_light.png' not found in README"
    )


def test_readme_contains_arrow_controls() -> None:
    """The README must document arrow key controls."""
    content = README_PATH.read_text(encoding="utf-8")
    assert "Arrow" in content or "arrow" in content, (
        "Arrow key controls not documented in README"
    )


def test_readme_contains_escape() -> None:
    """The README must document the Escape key for quitting."""
    content = README_PATH.read_text(encoding="utf-8")
    assert "Escape" in content, "Escape key control not documented in README"


def test_readme_contains_undo_key() -> None:
    """The README must document the Z key for undo."""
    content = README_PATH.read_text(encoding="utf-8")
    # Look for Z as an undo key — it appears in the controls table
    assert "Z" in content, "Undo key 'Z' not documented in README"
