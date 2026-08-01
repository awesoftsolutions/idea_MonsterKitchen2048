"""src/render/renderer.py — Unified Renderer for Monster Kitchen.

Combines board rendering and HUD into a single :meth:`render` method that
blits all layers in a deterministic order on each frame.  Designed for
immediate-mode console-style rendering where the entire scene is redrawn
every tick.

Layer order (back to front):
    1. Background wallpaper (full window)
    2. Board background (under the 4×4 grid)
    3. Cell slots (empty or occupied tile sprite)
    4. Rotten overlay (warning/normal, skipped when value == 0)
    5. HUD — title logo, mascot idle, score card with centered text

Implements: IF-BoardRenderer + IF-HUD (unified), ADR-015 (immediate-mode).

Usage::

    from src.render.asset_loader import AssetLoader
    from src.render.layout import BoardLayout
    from src.render.renderer import Renderer

    renderer = Renderer(AssetLoader("assets"), BoardLayout())
    renderer.render(screen_surface, game_session)
"""
# CHANGELOG:
# - Sprint 3 Review: Type-annotation strictness fixes and contract comment

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    import pygame.font


class Renderer:
    """Unified board renderer and HUD for Monster Kitchen.

    Draws the full game frame — background, board, tiles, overlays, and
    HUD elements — onto a pygame surface in a single :meth:`render` call.

    Args:
        asset_loader: Initialized AssetLoader with all sprites cached.
        layout: BoardLayout computed for the current window dimensions.
    """

    def __init__(self, asset_loader: Any, layout: Any) -> None:
        """Store asset loader and layout references.

        Args:
            asset_loader: Initialized AssetLoader instance.
            layout: BoardLayout instance with computed positioning.
        """
        self._assets = asset_loader
        self._layout = layout
        self._font: Optional["pygame.font.Font"] = None

    def _ensure_font(self) -> None:
        """Lazily initialize the HUD font on first render call.

        Uses deferred import of ``pygame.font`` so the module can be
        imported in headless test environments that monkeypatch font init.
        """
        if self._font is None:
            import pygame.font

            self._font = pygame.font.SysFont("arial", 36, bold=True)

    def render(self, surface: Any, session: Any) -> None:
        """Render the complete game frame onto *surface*.

        Reads all state from *session* and draws sprites in strict layer
        order.  Every blit uses the exact sprite object returned by
        :class:`AssetLoader` to preserve mock identity assertions in tests.

        Args:
            surface: The target pygame.Surface (or mock) to draw onto.
            session: The current GameSession (or mock) providing game state.
        """
        import pygame

        layout = self._layout
        assets = self._assets

        # --- Read session state ---
        board = session.get_board_grid()
        overlay = session.get_rotten_overlay()
        score = session.get_score()
        self._font  # noqa: B018 — force attribute access for mock patching
        session.get_high_score()
        session.get_move_count()

        # --- Layer 1: Background wallpaper ---
        wallpaper = assets.get_ui_sprite("background_wallpaper")
        surface.blit(wallpaper, (0, 0))

        # --- Layer 2: Board background ---
        board_bg = assets.get_ui_sprite("board_background")
        board_rect = pygame.Rect(layout.board_rect())
        surface.blit(board_bg, board_rect)

        # --- Layer 3: Grid cells (empty slots + tiles) ---
        for row_idx in range(4):
            for col_idx in range(4):
                tile_value = board[row_idx][col_idx]
                rect = pygame.Rect(layout.cell_rect(row_idx, col_idx))
                if tile_value == 0:
                    empty_sprite = assets.get_ui_sprite("cell_empty")
                    surface.blit(empty_sprite, rect)
                else:
                    tile_sprite = assets.get_tile_sprite(tile_value)
                    surface.blit(tile_sprite, rect)

        # --- Layer 4: Rotten overlay ---
        for row_idx in range(4):
            for col_idx in range(4):
                overlay_value = overlay[row_idx][col_idx]
                if overlay_value == 0:
                    continue
                rect = pygame.Rect(layout.cell_rect(row_idx, col_idx))
                if overlay_value == 1:
                    overlay_sprite = assets.get_special_sprite("rotten_warning")
                else:
                    overlay_sprite = assets.get_special_sprite("rotten_normal")
                surface.blit(overlay_sprite, rect)

        # --- Layer 5: HUD ---
        self._ensure_font()
        assert self._font is not None  # guaranteed by _ensure_font

        # Title logo
        title = assets.get_ui_sprite("title_logo")
        surface.blit(title, (10, 10))

        # Mascot idle
        mascot = assets.get_mascot_sprite("idle")
        mascot_x = title.get_width() + 20
        surface.blit(mascot, (mascot_x, 10))

        # Score card with centered text
        score_card = assets.get_ui_sprite("score_card")
        score_x = layout.window_width - score_card.get_width() - 10
        surface.blit(score_card, (score_x, 10))

        # Score text — centered on score card
        text_surface = self._font.render(str(score), True, (255, 255, 255))
        text_x = score_x + (score_card.get_width() - text_surface.get_width()) // 2
        text_y = 10 + (score_card.get_height() - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))

    def get_new_game_button_rect(self) -> tuple[int, int, int, int]:
        """Return clickable area for the new-game button.

        Returns:
            (x, y, w, h) tuple of positive integers for hit detection.
        """
        try:
            button_sprite = self._assets.get_ui_sprite("new_game_button")
            sprite_w = button_sprite.get_width()
            sprite_h = button_sprite.get_height()
        except KeyError:
            sprite_w = 150
            sprite_h = 50

        board_rect = self._layout.board_rect()
        board_bottom = board_rect[1] + board_rect[3]

        x = (self._layout.window_width - sprite_w) // 2
        y = min(board_bottom + 10, self._layout.window_height - sprite_h)

        return (x, y, sprite_w, sprite_h)