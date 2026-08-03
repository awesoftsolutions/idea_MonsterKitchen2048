# Contract: test_toast_positioning.py
# Purpose:     Validates toast panel positioning within the visible 800px
#              window after the C52 fix (panel_y=50). Two tests verify
#              vertical bounds and horizontal centering via mock surface
#              blit interception.
# System:      pytest suite (tests/).  No pygame at import time.
# Dependencies: pytest, unittest.mock, src.render.toast_manager
# Used-by:     CI pipeline, Sprint 4-2 Task 2 acceptance verification
# Test API:
#     _make_mock_surface(width, height) -> MagicMock
#     _patch_toast_fonts(monkeypatch)   -> MagicMock  [fixture]
#     test_toast_panel_within_visible_window  -- AC-1
#     test_toast_panel_horizontally_centered  -- AC-2
# ---------------------------------------------------------------------------

"""Test suite for toast positioning within visible window (Sprint 4-2 Task 2).

Purpose:
    Validates the C52 toast positioning fix by confirming the toast panel
    renders within the visible 800px window (vertical bounds) and is
    horizontally centered (centering math). Both tests operate entirely
    headless via mock surface blit interception.

System:
    Headless pytest suite. Each test constructs its own ToastManager
    instance for full isolation. pygame.time.get_ticks() is patched
    via context manager inside each test to ensure zero side effects.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

try:
    from src.render.toast_manager import ToastManager, TOAST_HEIGHT
except ImportError:  # pragma: no cover -- TDD red phase compatibility
    ToastManager = None  # type: ignore[misc,assignment]
    TOAST_HEIGHT = 80  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Helper: Mock surface builder
# ---------------------------------------------------------------------------


def _make_mock_surface(width: int = 700, height: int = 800) -> MagicMock:
    """Build a mock pygame.Surface with configurable dimensions.

    Args:
        width: Surface width in pixels.
        height: Surface height in pixels.

    Returns:
        MagicMock configured to behave like a pygame.Surface.
    """
    mock = MagicMock()
    mock.get_width.return_value = width
    mock.get_height.return_value = height
    return mock


# ---------------------------------------------------------------------------
# Fixture: Headless font mocks
# ---------------------------------------------------------------------------


@pytest.fixture()
def _patch_toast_fonts(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch pygame.font.SysFont, font.init, and pygame.Surface for headless rendering.

    Creates a mock font whose .render() returns a mock surface with
    realistic get_width/get_height values. Also patches pygame.Surface
    to return a MagicMock so that panel_surface.blit() (line 252 of
    toast_manager.py) does not fail when it receives mock text surfaces.

    Args:
        monkeypatch: pytest monkeypatch fixture.

    Returns:
        The mock font instance (for assertion on render calls).
    """
    mock_font = MagicMock()
    mock_text_surface = _make_mock_surface(120, 32)
    mock_font.render.return_value = mock_text_surface

    import pygame
    import pygame.font

    monkeypatch.setattr(pygame.font, "init", lambda: None)
    monkeypatch.setattr(pygame.font, "SysFont", lambda *a, **kw: mock_font)
    monkeypatch.setattr(pygame, "Surface", lambda *a, **kw: MagicMock())

    return mock_font


# ---------------------------------------------------------------------------
# Test 1: Vertical bounds -- AC-1
# ---------------------------------------------------------------------------


@pytest.mark.skipif(ToastManager is None, reason="ToastManager not importable")
def test_toast_panel_within_visible_window(
    _patch_toast_fonts: MagicMock,
) -> None:
    """Verify the toast panel does not extend below the 800px window.

    Scenario:
        Render a toast on a 700x800 mock surface and confirm
        panel_y + TOAST_HEIGHT <= 800.
    """
    manager = ToastManager()  # type: ignore[misc]
    mock_surface = _make_mock_surface(700, 800)

    with patch("pygame.time.get_ticks", return_value=0):
        manager.show("Test Achievement", "Test Description")

    manager.render(mock_surface)

    assert mock_surface.blit.called, "render() should call target_surface.blit"

    blit_calls = mock_surface.blit.call_args_list
    assert len(blit_calls) >= 1, (
        f"Expected at least one blit call on target_surface, got {len(blit_calls)}"
    )

    # The only blit to target_surface is the panel blit at line 259:
    #   target_surface.blit(panel_surface, (panel_x, panel_y))
    # Text blits go onto panel_surface (a different mock), not target_surface.
    panel_blit = blit_calls[0]
    position = panel_blit[0][1]  # second positional arg: (panel_x, panel_y)
    panel_y = position[1]

    assert panel_y + TOAST_HEIGHT <= 800, (
        f"Toast panel top ({panel_y}) + height ({TOAST_HEIGHT}) "
        f"= {panel_y + TOAST_HEIGHT} must be <= 800 (window height). "
        f"Panel extends below visible window."
    )


# ---------------------------------------------------------------------------
# Test 2: Horizontal centering -- AC-2
# ---------------------------------------------------------------------------


@pytest.mark.skipif(ToastManager is None, reason="ToastManager not importable")
def test_toast_panel_horizontally_centered(
    _patch_toast_fonts: MagicMock,
) -> None:
    """Verify the toast panel is horizontally centered within the window.

    Scenario:
        Render a toast on a 700-wide mock surface and confirm
        panel_x == (window_width - panel_width) // 2.
    """
    manager = ToastManager()  # type: ignore[misc]
    mock_surface = _make_mock_surface(700, 800)

    with patch("pygame.time.get_ticks", return_value=0):
        manager.show("Test Achievement", "Test Description")

    manager.render(mock_surface)

    assert mock_surface.blit.called, "render() should call target_surface.blit"

    blit_calls = mock_surface.blit.call_args_list
    assert len(blit_calls) >= 1, (
        f"Expected at least one blit call on target_surface, got {len(blit_calls)}"
    )

    # Extract panel_x from the same panel blit as test 1.
    panel_blit = blit_calls[0]
    position = panel_blit[0][1]  # (panel_x, panel_y)
    panel_x = position[0]

    # Compute expected panel_width from the mock font dimensions.
    # Mock font renders return a 120x32 surface for all calls.
    # panel_width = max(120, 120 + 2*16, 120 + 2*16, 120 + 2*16) = 152
    # (see toast_manager.py lines 227-233)
    expected_panel_width = max(120, 120 + 2 * 16, 120 + 2 * 16, 120 + 2 * 16)
    expected_panel_x = (700 - expected_panel_width) // 2

    assert panel_x == expected_panel_x, (
        f"Panel should be horizontally centered: expected "
        f"panel_x={expected_panel_x}, got {panel_x}. "
        f"window_width=700, panel_width={expected_panel_width}"
    )
