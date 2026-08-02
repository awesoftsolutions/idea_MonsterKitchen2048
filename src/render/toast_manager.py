# Contract: toast_manager.py
# Purpose:     Toast notification manager — queues and renders temporary
#              on-screen notifications for achievement unlocks.
# System:      Render layer (src/render/).  Deferred pygame imports —
#              zero dependency at module import time.
# Dependencies: pygame.font (deferred), dataclasses, typing
# Used-by:     Game loop via Sprint 4-2 Task 3 (integration)
# Public API:
#     Toast (dataclass)
#         message: str        — display text
#         icon_key: str       — icon identifier (empty string = no icon)
#         created_at: float   — pygame.time.get_ticks() at creation
#         duration_ms: int    — display duration (default 2500)
#
#     ToastManager
#         __init__(self) -> None
#         show(message: str, icon_key: str = "") -> Toast
#         update(dt: float) -> None
#         get_active(self) -> Toast | None
#         render(target_surface: Any) -> None
#         clear(self) -> None
#         is_empty(self) -> bool  (property)
# ---------------------------------------------------------------------------

"""Toast notification manager for the 2048 game.

Manages temporary on-screen notification toasts that display achievement names
when unlocked during gameplay. Toasts render as semi-transparent panels with
bold achievement name and regular description text. Toasts display sequentially
with a linear fade-out animation in the final 500ms of each toast's duration.

This module has **zero pygame dependency at import time**. Font resources are
loaded lazily on first `render()` call via `_ensure_fonts()`, following the
deferred-import pattern established in `Renderer._ensure_font()`.

Public API:
    ToastManager
        __init__(self) -> None
        show(message: str, icon_key: str = "") -> Toast
        update(dt: float) -> None
        get_active(self) -> Toast | None
        render(target_surface: Any) -> None
        clear(self) -> None
        is_empty(self) -> bool  (property)

Internal:
    Toast — dataclass storing per-toast display state.

Constants:
    DEFAULT_DURATION_MS — default toast display time in milliseconds.
    FADE_DURATION_MS    — duration of the fade-out animation in milliseconds.
    TOAST_HEIGHT        — fixed panel height in pixels.
    TOAST_PADDING       — horizontal/vertical text padding inside the panel.
    (TOAST_MARGIN_BOTTOM removed \u2014 panel_y now uses constant 50 per ADR-R02)
"""
# CHANGELOG:
# - Sprint 4-2: New ToastManager class - deferred font init, sequential
#               toast queue, linear fade-out alpha over 500 ms

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------

DEFAULT_DURATION_MS = 2500
FADE_DURATION_MS = 500
TOAST_HEIGHT = 80
TOAST_PADDING = 16
TOAST_MARGIN_BOTTOM = 20


# ---------------------------------------------------------------------------
# Toast dataclass
# ---------------------------------------------------------------------------


@dataclass
class Toast:
    """A single toast notification state.

    Attributes:
        message: Achievement name displayed in bold.
        icon_key: Asset key for future icon rendering; description text this sprint.
        created_at: Millisecond timestamp (pygame.time.get_ticks()) when queued.
        duration_ms: Total display time in milliseconds.
    """

    message: str
    icon_key: str
    created_at: float
    duration_ms: int = DEFAULT_DURATION_MS


# ---------------------------------------------------------------------------
# ToastManager
# ---------------------------------------------------------------------------


class ToastManager:
    """Manages temporary on-screen notification toasts.

    Queues achievement toasts and displays them sequentially with
    fade-in/fade-out animations applied via surface alpha.
    Zero pygame dependency at import time — font resources are loaded
    lazily on first render() call following Renderer._ensure_font() pattern.
    """

    def __init__(self) -> None:
        """Initialize empty toast queue and no active toast."""
        self._active: Optional[Toast] = None
        self._queue: list[Toast] = []
        self._elapsed_ms: float = 0.0
        self._bold_font: Any = None
        self._regular_font: Any = None

    def show(self, message: str, icon_key: str = "") -> Toast:
        """Create a Toast and queue it for display.

        Args:
            message: Achievement name text.
            icon_key: Asset key or description text.

        Returns:
            The newly created Toast instance.
        """
        import pygame  # noqa: PLC0415  # deferred: zero pygame at import time

        toast = Toast(
            message=message, icon_key=icon_key, created_at=pygame.time.get_ticks()
        )

        if self._active is None:
            self._active = toast
            self._elapsed_ms = 0.0
        else:
            self._queue.append(toast)

        return toast

    def update(self, dt: float) -> None:
        """Advance toast timer by dt seconds.

        Args:
            dt: Delta time in seconds since last update call.
        """
        if self._active is None:
            return

        dt_ms = dt * 1000.0
        self._elapsed_ms += dt_ms

        # IMPLEMENTATION DECISION: Activate next toast immediately on expiry.
        # Rationale: FIFO queue pattern — when active expires, next queued
        # toast activates with elapsed reset to 0. Alternatives: frame-delay
        # activation, but immediate matches game loop cadence.
        if self._elapsed_ms >= self._active.duration_ms:
            if self._queue:
                new_toast = self._queue.pop(0)
                self._active = new_toast
                self._elapsed_ms = 0.0
            else:
                # Leave _elapsed_ms at its accumulated value so callers can
                # observe the timer exceeded the toast duration.
                self._active = None

    def get_active(self) -> Optional[Toast]:
        """Return the currently displayed toast, or None."""
        return self._active

    def _ensure_fonts(self) -> None:
        """Lazily initialize pygame.font resources.

        Follows Renderer._ensure_font() pattern: checks if fonts are already
        loaded, then imports pygame.font and creates SysFont instances.
        """
        if self._bold_font is not None:
            return

        import pygame.font  # noqa: PLC0415  # deferred: zero pygame at import time

        pygame.font.init()
        self._bold_font = pygame.font.SysFont("arial", 28, bold=True)
        self._regular_font = pygame.font.SysFont("arial", 20, bold=False)

    def render(self, target_surface: Any) -> None:
        """Draw the active toast panel onto target_surface.

        Args:
            target_surface: pygame.Surface (or compatible) to draw onto.
        """
        if self._active is None:
            return

        import pygame  # noqa: PLC0415  # deferred: zero pygame at import time

        self._ensure_fonts()

        toast = self._active

        # Compute alpha for fade-out
        if self._elapsed_ms < (toast.duration_ms - FADE_DURATION_MS):
            current_alpha = 255
        else:
            fade_elapsed = self._elapsed_ms - (toast.duration_ms - FADE_DURATION_MS)
            fade_ratio = fade_elapsed / FADE_DURATION_MS
            fade_ratio = min(max(fade_ratio, 0.0), 1.0)
            current_alpha = int(255 * (1.0 - fade_ratio))
            current_alpha = max(0, min(current_alpha, 255))

        if current_alpha <= 0:
            return  # fully transparent, nothing to draw

        # Render text surfaces
        name_surface = self._bold_font.render(toast.message, True, (255, 255, 255))
        desc_surface = self._regular_font.render(toast.icon_key, True, (200, 200, 200))

        # Apply alpha to text surfaces before blitting to panel
        name_surface.set_alpha(current_alpha)
        if toast.icon_key:
            desc_surface.set_alpha(current_alpha)

        # Calculate panel dimensions
        panel_width = max(
            name_surface.get_width(),
            desc_surface.get_width() + (2 * TOAST_PADDING if toast.icon_key else 0),
        )
        panel_width = max(panel_width, name_surface.get_width() + 2 * TOAST_PADDING)
        if toast.icon_key:
            panel_width = max(panel_width, desc_surface.get_width() + 2 * TOAST_PADDING)
        panel_height = TOAST_HEIGHT

        # Panel position: centered horizontally, above board bottom
        window_width = target_surface.get_width()
        panel_x = (window_width - panel_width) // 2
        panel_y = 50

        # Create semi-transparent panel
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((40, 40, 40, int(204 * current_alpha / 255)))

        # Blit text onto panel
        text_x = TOAST_PADDING
        if toast.icon_key:
            text_y_name = (
                panel_height - name_surface.get_height() - desc_surface.get_height() - 4
            ) // 2
            text_y_desc = text_y_name + name_surface.get_height() + 4
            panel_surface.blit(name_surface, (text_x, text_y_name))
            panel_surface.blit(desc_surface, (text_x, text_y_desc))
        else:
            text_y_name = (panel_height - name_surface.get_height()) // 2
            panel_surface.blit(name_surface, (text_x, text_y_name))

        # Blit completed panel onto the target surface
        target_surface.blit(panel_surface, (panel_x, panel_y))

    def clear(self) -> None:
        """Remove all toasts (active and queued)."""
        self._active = None
        self._queue = []
        self._elapsed_ms = 0.0

    @property
    def is_empty(self) -> bool:
        """Return True when no toasts are queued or active."""
        return (self._active is None) and (len(self._queue) == 0)
