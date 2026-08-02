# Contract: merge_celebration.py
# Purpose:     Merge celebration visual effects — golden glow + floating score popup.
# System:      Render layer (src/render/).  Deferred pygame imports —
#              zero dependency at module import time.
# Dependencies: pygame (deferred), dataclasses, typing
# Used-by:     Game loop via Sprint 4-2 Task 3 (integration)
# Public API:
#     MergeCelebrationEffect (dataclass)
#         row: int
#         col: int
#         value: int
#         glow_alpha: int
#         score_offset_y: float
#         score_alpha: int
#         elapsed_ms: float
#         duration_ms: float
#
#     create_effect(row, col, value, duration_ms=600.0) -> MergeCelebrationEffect
#     update_effects(effects, delta_ms) -> None
#     cleanup_expired_effects(effects) -> list[MergeCelebrationEffect]
#     render_celebration_effects(surface, effects, layout) -> None
# ---------------------------------------------------------------------------

"""Merge celebration visual effects for the 2048 game.

Renders timed golden glow rectangles and floating "+value" score popups for
merged tiles.  Celebrations outlast the 200ms scale-pulse window with a
default 600ms duration, fading linearly from full opacity to invisible.

This module has **zero pygame dependency at import time**.  All pygame access
is deferred inside ``render_celebration_effects()``, following the pattern
established in ``Renderer._ensure_font()`` and ``ToastManager._ensure_fonts()``.

Public API:
    MergeCelebrationEffect  -- dataclass holding timed visual effect state
    create_effect           -- factory to create a new celebration effect
    update_effects          -- advance all effects by delta_ms
    cleanup_expired_effects -- remove expired effects from a list
    render_celebration_effects -- render glow + score popup onto a surface

Constants:
    CELEBRATION_DURATION_MS -- default effect lifetime (600ms)
    SCORE_FLOAT_SPEED      -- upward drift speed in pixels/ms (0.08)
    GLOW_COLOR             -- RGB golden color for glow rectangle
    GLOW_PADDING           -- pixel extension beyond cell rect (6)
"""

# CHANGELOG:
# - Sprint 4-2 Task 2: New merge_celebration module — golden glow + score popup effects

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------

CELEBRATION_DURATION_MS: float = 600.0
SCORE_FLOAT_SPEED: float = 0.08  # pixels per millisecond upward
GLOW_COLOR: tuple[int, int, int] = (255, 215, 0)  # golden
GLOW_PADDING: int = 6  # pixels of glow extension beyond cell rect


# ---------------------------------------------------------------------------
# MergeCelebrationEffect dataclass
# ---------------------------------------------------------------------------


@dataclass
class MergeCelebrationEffect:
    """Timed visual celebration state for a merged tile.

    Attributes:
        row: Grid row index (0-based) of the merged tile destination.
        col: Grid column index (0-based) of the merged tile destination.
        value: The merged tile value (e.g. 4 for two 2s merging).
        glow_alpha: Current alpha for the golden glow rectangle (0-255).
        score_offset_y: Vertical pixel offset for score popup animation.
        score_alpha: Current alpha for the score popup text (0-255).
        elapsed_ms: Milliseconds elapsed since the effect was created.
        duration_ms: Total effect duration in milliseconds.
    """

    row: int
    col: int
    value: int
    glow_alpha: int = 255
    score_offset_y: float = 0.0
    score_alpha: int = 255
    elapsed_ms: float = 0.0
    duration_ms: float = CELEBRATION_DURATION_MS


# ---------------------------------------------------------------------------
# Standalone lifecycle functions
# ---------------------------------------------------------------------------


def create_effect(
    row: int,
    col: int,
    value: int,
    duration_ms: float = CELEBRATION_DURATION_MS,
) -> MergeCelebrationEffect:
    """Create a new celebration effect with default starting state.

    Args:
        row: Grid row index of the merged tile destination.
        col: Grid column index of the merged tile destination.
        value: The merged tile value.
        duration_ms: Total effect lifetime in milliseconds.

    Returns:
        A new MergeCelebrationEffect with initial alpha 255 and offset 0.
    """
    return MergeCelebrationEffect(
        row=row,
        col=col,
        value=value,
        glow_alpha=255,
        score_offset_y=0.0,
        score_alpha=255,
        elapsed_ms=0.0,
        duration_ms=duration_ms,
    )


def update_effects(
    effects: list[MergeCelebrationEffect],
    delta_ms: float,
) -> None:
    """Advance all effects by delta_ms; recompute derived fields.

    Recomputes glow_alpha, score_alpha, and score_offset_y from the updated
    elapsed time.  Elapsed time is clamped to duration_ms so alpha never
    goes negative.

    Args:
        effects: Mutable list of active effects to update in place.
        delta_ms: Milliseconds elapsed since last update call.
    """
    for effect in effects:
        effect.elapsed_ms += delta_ms

        # Clamp elapsed to not exceed duration
        if effect.elapsed_ms > effect.duration_ms:
            effect.elapsed_ms = effect.duration_ms

        progress = effect.elapsed_ms / effect.duration_ms

        # Glow alpha: linear decay from 255 to 0
        effect.glow_alpha = int(255 * (1.0 - progress))
        effect.glow_alpha = max(0, min(effect.glow_alpha, 255))

        # Score alpha: same linear decay
        effect.score_alpha = int(255 * (1.0 - progress))
        effect.score_alpha = max(0, min(effect.score_alpha, 255))

        # Score offset Y: linear upward drift
        effect.score_offset_y = effect.elapsed_ms * SCORE_FLOAT_SPEED


def cleanup_expired_effects(
    effects: list[MergeCelebrationEffect],
) -> list[MergeCelebrationEffect]:
    """Remove expired effects (elapsed >= duration).

    Mutates the list in-place and returns it so callers holding the same
    list reference see the update.

    Args:
        effects: Mutable list of active effects.

    Returns:
        The same list object, now containing only non-expired effects.
    """
    effects[:] = [e for e in effects if e.elapsed_ms < e.duration_ms]
    return effects


def render_celebration_effects(
    surface: Any,
    effects: list[MergeCelebrationEffect],
    layout: Any,
) -> None:
    """Render golden glow + score popup for all active effects.

    This is the only function in this module that imports pygame — all
    pygame access is deferred inside this function body.

    Args:
        surface: The target pygame.Surface (or mock) to draw onto.
        effects: Active celebration effects to render.
        layout: BoardLayout providing cell_rect(row, col) for positioning.
    """
    if not effects:
        return

    import pygame  # noqa: PLC0415 — deferred: zero pygame at import time

    for effect in effects:
        if effect.glow_alpha <= 0 and effect.score_alpha <= 0:
            continue

        # Get cell position
        rect = layout.cell_rect(effect.row, effect.col)
        x, y, w, h = rect

        # --- Golden glow ---
        if effect.glow_alpha > 0:
            glow_w = w + 2 * GLOW_PADDING
            glow_h = h + 2 * GLOW_PADDING
            glow_surface = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
            glow_surface.fill((*GLOW_COLOR, effect.glow_alpha))

            glow_x = x - GLOW_PADDING
            glow_y = y - GLOW_PADDING
            surface.blit(glow_surface, (glow_x, glow_y))

        # --- Score popup text ---
        if effect.score_alpha > 0:
            # Deferred font creation (follows ToastManager._ensure_fonts pattern)
            if not hasattr(render_celebration_effects, "_font"):
                import pygame.font  # noqa: PLC0415

                pygame.font.init()
                render_celebration_effects._font = pygame.font.SysFont(
                    "arial", 24, bold=True
                )

            font = render_celebration_effects._font
            text = "+" + str(effect.value)
            text_surface = font.render(text, True, (255, 255, 255))
            text_surface.set_alpha(effect.score_alpha)

            text_x = x + (w - text_surface.get_width()) // 2
            text_y = y - effect.score_offset_y
            surface.blit(text_surface, (text_x, text_y))
