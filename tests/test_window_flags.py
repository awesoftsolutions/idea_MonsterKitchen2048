"""Regression tests for window creation flags in src/main.py.

Purpose:
    Verify that the pygame window is created without the NOFRAME flag,
    ensuring the standard OS title bar and window controls are displayed.

System:
    These tests use pure text inspection of src/main.py source code —
    no pygame is initialised and no display is created. This approach
    is appropriate for verifying parameter-removal changes.

Dependencies:
    - pathlib.Path (for reading source file)

Used-by:
    - pytest test suite (run via `poetry run pytest`)

Public Interface:
    def test_no_noframe_flag_in_main() -> None
        Asserts that pygame.NOFRAME does not appear in src/main.py source.

    def test_set_mode_called_with_only_size_tuple() -> None
        Asserts that pygame.display.set_mode is called with only (700, 800)
        and no flags argument.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SRC_MAIN = Path(__file__).resolve().parent.parent / "src" / "main.py"


def _read_main_source() -> str:
    """Return the full source text of ``src/main.py``."""
    return _SRC_MAIN.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


def test_no_noframe_flag_in_main() -> None:
    """The production code must NOT reference ``pygame.NOFRAME``."""
    source = _read_main_source()
    assert "pygame.NOFRAME" not in source, (
        "src/main.py still references pygame.NOFRAME — "
        "the window should display with the system frame."
    )


def test_set_mode_called_with_only_size_tuple() -> None:
    """``pygame.display.set_mode`` must be called with ``(700, 800)`` and no extra flags."""
    source = _read_main_source()

    # Find the set_mode call line and assert it contains only the size tuple.
    matching_lines = [
        line for line in source.splitlines() if "pygame.display.set_mode" in line
    ]
    assert matching_lines, (
        "Could not find a pygame.display.set_mode() call in src/main.py."
    )

    # Every set_mode call site must use only the size tuple — no flags argument.
    # The expected post-fix call is: pygame.display.set_mode((700, 800))
    for line in matching_lines:
        assert "flags=" not in line, (
            f"pygame.display.set_mode still receives flags= keyword: {line.strip()!r}"
        )
        # Verify the call passes the explicit size tuple (700, 800).
        assert "(700, 800)" in line, (
            f"pygame.display.set_mode must use size tuple (700, 800): {line.strip()!r}"
        )
