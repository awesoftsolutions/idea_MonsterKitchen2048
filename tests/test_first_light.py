"""Verification tests for the first-light screenshot.

Confirms that visual-proof/first_light.png was successfully created
by the first-light milestone: the file exists, is non-empty, and
contains valid PNG header bytes.

Contract:
    Purpose: Verify first-light screenshot artifact produced by the
        develop agent during Sprint 4 Task 2.
    System: pytest test runner (discovered via tests/ directory)
    Dependencies: pathlib (stdlib only)
    Used-by: pytest discovery, CI pipeline
    Public Interface:
        test_first_light_screenshot_exists() -> None
        test_first_light_screenshot_non_empty() -> None
        test_first_light_screenshot_is_valid_png() -> None
"""

from pathlib import Path

SCREENSHOT_PATH = (
    Path(__file__).resolve().parent.parent / "visual-proof" / "first_light.png"
)


def test_first_light_screenshot_exists():
    """The first-light screenshot must exist on disk."""
    assert SCREENSHOT_PATH.is_file(), f"Screenshot not found at {SCREENSHOT_PATH}"


def test_first_light_screenshot_non_empty():
    """The first-light screenshot must be a non-empty file."""
    size = SCREENSHOT_PATH.stat().st_size
    assert size > 0, f"Screenshot is empty (0 bytes) at {SCREENSHOT_PATH}"


def test_first_light_screenshot_is_valid_png():
    """The first-light screenshot must start with the PNG magic bytes."""
    with open(SCREENSHOT_PATH, "rb") as f:
        header = f.read(8)
    png_magic = b"\x89PNG\r\n\x1a\n"
    assert header == png_magic, (
        f"Expected PNG magic bytes {png_magic!r}, got {header!r}"
    )
