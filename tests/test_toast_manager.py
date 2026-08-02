# Contract: test_toast_manager.py
# Purpose:     Headless test suite for ToastManager — verifies toast
#              lifecycle, sequential display, fade-out timing, and
#              deferred-import pattern compliance.
# System:      pytest suite (tests/).  No pygame at import time.
# Dependencies: pytest, unittest.mock, src.render.toast_manager
# Used-by:     CI pipeline, Sprint 4-2 Task 1 acceptance verification
# Test API:
#     _make_mock_surface(width, height) -> MagicMock
#     test_enqueue_adds_to_queue              -- AC-1
#     test_update_decrements_timer             -- AC-2
#     test_fade_out_begins_after_duration      -- AC-4
#     test_sequential_display                  -- AC-2, AC-5
#     test_empty_state                         -- AC-6
#     test_render_draws_panel                  -- AC-3
#     test_clear_removes_all                   -- clear()
#     test_no_pygame_import_at_module_level    -- AC-6
# ---------------------------------------------------------------------------

"""Test suite for src/render/toast_manager.py -- ToastManager class.

Purpose:
    TDD Red Phase tests for the ToastManager class -- a render-layer component
    that queues and displays temporary on-screen toast notifications for
    achievement unlocks. Covers all acceptance criteria from Sprint 4-2
    Task 1 pseudocode (AC-1 through AC-6).

System:
    Headless pytest suite. Each test constructs its own ToastManager
    instance for full isolation. pygame.time.get_ticks() is mocked
    via unittest.mock.patch per test since show() imports pygame
    internally and calls get_ticks() for the toast timestamp.

Dependencies:
    pytest, unittest.mock -- standard test tooling.
    src.render.toast_manager -- production code (TARGET OF TDD RED PHASE).

Used-by:
    CI pipeline (pytest), Sprint 4-2 Task 1 acceptance verification.

Public API:
    Helper:
        _make_mock_surface(width, height) -> MagicMock
            Build a mock pygame.Surface for headless render assertions.

    Test functions (9 standalone):
        test_enqueue_adds_to_queue              -- AC-1: show() creates Toast, is_empty=False.
        test_update_decrements_timer             -- AC-2: update() advances elapsed_ms.
        test_fade_out_begins_after_duration      -- AC-4: elapsed_ms reaches fade region.
        test_sequential_display                  -- AC-2, AC-5: next toast activates on expiry.
        test_empty_state                         -- AC-6: fresh manager is_empty=True.
        test_render_draws_panel                  -- AC-3: render() blits to target surface.
        test_clear_removes_all                   -- clear() empties queue and active.
        test_no_pygame_import_at_module_level    -- AC-6: no pygame at import time.
        test_toast_y_position_le_50              -- Fix 2: toast y <= 50px.
"""

from __future__ import annotations

import inspect
import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Module-level import with graceful fallback (TDD red phase)
# ---------------------------------------------------------------------------

try:
    from src.render.toast_manager import (
        DEFAULT_DURATION_MS,
        FADE_DURATION_MS,
        Toast,
        ToastManager,
    )
except ImportError:
    ToastManager = None  # type: ignore[assignment,misc]
    Toast = None  # type: ignore[assignment,misc]
    DEFAULT_DURATION_MS = 2500  # type: ignore[assignment]
    FADE_DURATION_MS = 500  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Helper
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
# Queue and State Tests
# ---------------------------------------------------------------------------


def test_enqueue_adds_to_queue() -> None:
    """AC-1: show() creates a Toast, is_empty returns False, get_active() returns it.

    Calls show("First Bite", "Perform your first merge") on a fresh
    ToastManager. Verifies the returned Toast is not None, the manager
    reports non-empty, and get_active() returns the same toast.
    """
    manager = ToastManager()  # type: ignore[misc]

    assert manager.is_empty is True
    assert manager.get_active() is None

    with patch("pygame.time.get_ticks", return_value=1000):
        toast = manager.show("First Bite", "Perform your first merge")

    assert toast is not None
    assert toast.message == "First Bite"
    assert toast.icon_key == "Perform your first merge"
    assert manager.is_empty is False
    assert manager.get_active() is toast


def test_empty_state() -> None:
    """AC-6: Fresh ToastManager has is_empty=True and get_active() is None.

    No show() called -- verifies the initial empty-queue state before any
    toasts are enqueued.
    """
    manager = ToastManager()  # type: ignore[misc]

    assert manager.is_empty is True
    assert manager.get_active() is None


def test_clear_removes_all() -> None:
    """clear() empties both the active toast and the queue.

    Calls show() twice to create one active and one queued toast, then
    calls clear(). Verifies is_empty is True, get_active() is None.
    """
    manager = ToastManager()  # type: ignore[misc]

    with patch("pygame.time.get_ticks", return_value=0):
        manager.show("First", "")
        manager.show("Second", "")

    assert manager.is_empty is False

    manager.clear()

    assert manager.is_empty is True
    assert manager.get_active() is None


# ---------------------------------------------------------------------------
# Update and Timing Tests
# ---------------------------------------------------------------------------


def test_update_decrements_timer() -> None:
    """AC-2: update(dt) advances the internal elapsed timer by dt*1000 ms.

    Calls show() to activate a toast, then update(0.5) to advance 500ms.
    Verifies the internal _elapsed_ms is approximately 500.0.
    """
    manager = ToastManager()  # type: ignore[misc]

    with patch("pygame.time.get_ticks", return_value=0):
        manager.show("Test", "")

    manager.update(0.5)

    assert manager._elapsed_ms == pytest.approx(500.0, abs=1.0)


def test_fade_out_begins_after_duration() -> None:
    """AC-4: Alpha computation follows the fade formula in the pseudocode.

    Pseudocode alpha formula (from ToastManager.render):
        if _elapsed_ms < (duration_ms - FADE_DURATION_MS):
            alpha = 255
        else:
            fade_ratio = (_elapsed_ms - (duration_ms - FADE_DURATION_MS))
                         / FADE_DURATION_MS
            alpha = int(255 * (1.0 - fade_ratio))

    For default toast (duration=2500ms, FADE_DURATION=500ms):
        Full alpha region: _elapsed_ms < 2000ms.
        Fade region: 2000ms <= _elapsed_ms < 2500ms.

    Expected alpha values at specific timepoints:
        At 1500ms: elapsed < 2000 -> alpha = 255 (full opacity).
        At 2100ms: elapsed >= 2000 -> fade_ratio = 100/500 = 0.2
                   alpha = int(255 * 0.8) = 204.

    Note: This test verifies _elapsed_ms at each timepoint since alpha is
    computed on-demand inside render(). Once the green phase adds render(),
    alpha can be verified through mock surface assertions.
    """
    manager = ToastManager()  # type: ignore[misc]

    with patch("pygame.time.get_ticks", return_value=0):
        manager.show("Test Toast", "")

    # Advance to 1500ms -- still in full alpha region (< 2000ms)
    manager.update(1.5)
    assert manager._elapsed_ms == pytest.approx(1500.0, abs=1.0)
    assert manager.get_active() is not None, "Toast must still be active at 1500ms"

    # Advance to 2100ms -- in fade region (>= 2000ms)
    # Expected alpha: int(255 * (1.0 - (2100 - 2000) / 500)) = int(255 * 0.8) = 204
    manager.update(0.6)
    assert manager._elapsed_ms == pytest.approx(2100.0, abs=1.0)
    assert manager.get_active() is not None, "Toast must still be active at 2100ms"

    # Advance past duration (2600ms > 2500ms) -- toast expires
    manager.update(0.5)
    assert manager._elapsed_ms >= DEFAULT_DURATION_MS, (
        f"_elapsed_ms should exceed duration, got {manager._elapsed_ms}"
    )


# ---------------------------------------------------------------------------
# Sequential Display Tests
# ---------------------------------------------------------------------------


def test_sequential_display() -> None:
    """AC-2, AC-5: When active toast expires, next queued toast activates.

    show("First", "") creates the active toast. show("Second", "") queues
    the second. update(2.6) advances 2600ms past the first toast's 2500ms
    duration, causing it to expire. get_active() should then return the
    second toast with message "Second".
    """
    manager = ToastManager()  # type: ignore[misc]

    with patch("pygame.time.get_ticks", return_value=0):
        manager.show("First", "")
        manager.show("Second", "")

    assert manager.get_active().message == "First"  # type: ignore[union-attr]
    assert manager.is_empty is False

    # Advance past first toast's 2500ms duration
    manager.update(2.6)

    active = manager.get_active()
    assert active is not None, "Second toast should be active after first expires"
    assert active.message == "Second", f"Expected 'Second', got '{active.message}'"


# ---------------------------------------------------------------------------
# Render Tests
# ---------------------------------------------------------------------------


def test_render_draws_panel() -> None:
    """AC-3: render() draws onto the target surface when a toast is active.

    Calls show() to enqueue a toast, then render(mock_surface). Verifies
    that mock_surface.blit was called (panel and text drawn onto surface).
    Font initialization is handled by the conftest mock pygame.font.
    """
    manager = ToastManager()  # type: ignore[misc]
    mock_surface = _make_mock_surface(700, 800)

    with patch("pygame.time.get_ticks", return_value=0):
        manager.show("Test Name", "Test Description")

    manager.render(mock_surface)

    assert mock_surface.blit.called, (
        "render() should call target_surface.blit to draw the toast panel"
    )


# ---------------------------------------------------------------------------
# Module Import Verification Tests
# ---------------------------------------------------------------------------


def test_no_pygame_import_at_module_level() -> None:
    """AC-6: Importing toast_manager does not load pygame at module level.

    Inspects the source code of src.render.toast_manager and verifies
    that no 'import pygame' or 'from pygame' statement appears at
    module level (i.e., not indented inside a function body). This
    confirms the deferred-import design where pygame is only loaded
    inside _ensure_fonts() and show().

    Note: If src.render.toast_manager does not exist, this test will fail
    with ImportError -- expected behavior during TDD red phase.
    """
    try:
        mod = sys.modules.get("src.render.toast_manager")
        if mod is None:
            import importlib  # noqa: PLC0415

            mod = importlib.import_module("src.render.toast_manager")
    except ImportError:
        pytest.skip("src.render.toast_manager does not exist yet (TDD red phase)")
        return

    source = inspect.getsource(mod)
    lines = source.split("\n")

    module_level_pygame_imports: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if stripped.startswith("import pygame") or stripped.startswith("from pygame"):
            if not line[0].isspace():
                module_level_pygame_imports.append(stripped)

    assert len(module_level_pygame_imports) == 0, (
        f"Found pygame import(s) at module level: {module_level_pygame_imports}. "
        "Pygame must only be imported inside method bodies (_ensure_fonts, show) "
        "to maintain headless test compatibility."
    )


# ---------------------------------------------------------------------------
# Fix 2: Toast y-position (Sprint 4-2 remediation)
# ---------------------------------------------------------------------------


def test_toast_y_position_le_50() -> None:
    """Fix 2 AC-4: Toast panel y-position must be <= 50 pixels from top of window.

    Renders a toast and inspects the panel blit position on the target surface.
    The panel_y coordinate (from target_surface.blit call) must be <= 50 to
    prevent the toast from falling below the visible game area on small screens.

    Calculation reference (toast_manager.py lines 239-240):
        board_bottom = 138 + 4 * 162  = 786
        panel_y = board_bottom + TOAST_MARGIN_BOTTOM(20) = 806

    FAIL REASON: Current panel_y = 806, which is well above the 50px threshold.
    The fix must move the toast to a position that ensures visibility.
    """
    manager = ToastManager()  # type: ignore[misc]
    mock_surface = _make_mock_surface(700, 900)

    with patch("pygame.time.get_ticks", return_value=0):
        manager.show("First Bite", "Perform your first merge")

    manager.render(mock_surface)

    # Extract the panel blit position from the target surface
    # render() calls target_surface.blit(panel_surface, (panel_x, panel_y)) once
    assert mock_surface.blit.called, (
        "render() should call target_surface.blit to draw the toast panel"
    )
    blit_calls = mock_surface.blit.call_args_list
    # The only blit on the target surface is the panel blit at line 260
    assert len(blit_calls) >= 1, "Expected at least one blit call on target_surface"
    # The panel blit is the last call (text blits go to the panel_surface, not target)
    panel_blit = blit_calls[0]
    position = panel_blit[0][1]  # second positional arg = (panel_x, panel_y)
    panel_y = position[1]

    assert panel_y <= 50, (
        f"Toast panel y-position must be <= 50, got {panel_y}. "
        "The toast falls outside the visible area on small screens."
    )
