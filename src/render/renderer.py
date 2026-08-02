"""src/render/renderer.py — Unified Renderer for Monster Kitchen.

Combines board rendering and HUD into a single :meth:`render` method that
blits all layers in a deterministic order on each frame.  Designed for
immediate-mode console-style rendering where the entire scene is redrawn
every tick.

Layer order (back to front):
    1. Background wallpaper (full window)
    2. Board background (under the 4×4 grid)
    3. Cell slots (empty or occupied tile sprite)
    3.5. Merge celebration effects (golden glow + score popup)
    4. Rotten overlay (warning/normal, skipped when value == 0)
    5. HUD — title logo, mascot (idle/happy/worried per game state), score card
    6. Game-over/win overlay — overlay sprite, final score text, new-game button

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
# - Sprint 3 Task 1: Removed pygame.NOFRAME for standard window chrome (main.py)
# - Sprint 3 Task 2: Mascot state, Layer 6 overlay consolidation
# - Sprint 4-2: Added celebration_effects parameter to render() (Layer 3.5)

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    import pygame.font

from src.render.merge_celebration import render_celebration_effects


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

    def render(
        self,
        surface: Any,
        session: Any,
        active_moves: dict[tuple[int, int], tuple[float, float]] | None = None,
        celebration_effects: list[Any] | None = None,
        game_state: str = "idle",
        rotten_overlay: list[list[int]] | None = None,
        score: int | None = None,
    ) -> None:
        """Render the complete game frame onto *surface*.

        Reads all state from *session* and draws sprites in strict layer
        order.  Every blit uses the exact sprite object returned by
        :class:`AssetLoader` to preserve mock identity assertions in tests.

        Args:
            surface: The target pygame.Surface (or mock) to draw onto.
            session: The current GameSession (or mock) providing game state.
            active_moves: Optional mapping of (row, col) to (offset_x, offset_y)
                pixel offsets for animated tiles. When provided, animated tiles
                are blitted at their offset positions. None means no animation.
            celebration_effects: Optional list of MergeCelebrationEffect objects
                for Layer 3.5 celebration rendering. None or empty means no
                celebration layer. Rendered between grid cells (Layer 3) and
                rotten overlay (Layer 4).
            game_state: "idle", "playing", "game_over", or "win". Controls
                mascot expression and Layer 6 overlay rendering.
            rotten_overlay: 4x4 rotten grid for Layer 4 rendering. Read from
                session when not provided (legacy behavior). Passed explicitly
                by main.py for overlay consolidation (ADR-S3-003).
            score: Final score for Layer 6 overlay display. None skips score
                text rendering on overlay. Does NOT affect HUD score card which
                reads from session.get_score().
        """
        import pygame

        layout = self._layout
        assets = self._assets

        # --- Read session state ---
        board = session.get_board_grid()
        overlay = (
            rotten_overlay
            if rotten_overlay is not None
            else session.get_rotten_overlay()
        )
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
                    # Apply animation pixel offsets when active_moves provided (AC-12)
                    blit_rect = rect
                    if active_moves is not None and (row_idx, col_idx) in active_moves:
                        offset_x, offset_y = active_moves[(row_idx, col_idx)]
                        blit_rect = rect.move(int(offset_x), int(offset_y))
                    surface.blit(tile_sprite, blit_rect)

        # --- Layer 3.5: Merge celebration effects ---
        if celebration_effects is not None and len(celebration_effects) > 0:
            render_celebration_effects(surface, celebration_effects, layout)

        # --- Layer 4: Rotten overlay ---
        for row_idx in range(4):
            for col_idx in range(4):
                overlay_value = overlay[row_idx][col_idx]
                if overlay_value == 0:
                    continue
                cell_x, cell_y = layout.cell_rect(row_idx, col_idx)[:2]
                if overlay_value == 1:
                    overlay_sprite = assets.get_special_sprite("rotten_warning")
                else:
                    overlay_sprite = assets.get_special_sprite("rotten_normal")
                surface.blit(overlay_sprite, (cell_x, cell_y))

        # --- Layer 5: HUD ---
        self._ensure_font()
        assert self._font is not None  # guaranteed by _ensure_font

        # Title logo
        title = assets.get_ui_sprite("title_logo")
        surface.blit(title, (10, 10))

        # --- Mascot state selection (ADR-S3-001) ---
        # Priority: win → happy, game_over → worried,
        #           playing/idle + rotten_overlay non-zero → worried,
        #           else → idle.
        if game_state == "win":
            mascot_state = "happy"
        elif game_state == "game_over":
            mascot_state = "worried"
        elif rotten_overlay is not None and any(
            cell != 0 for row in rotten_overlay for cell in row
        ):
            mascot_state = "worried"
        else:
            mascot_state = "idle"

        try:
            mascot = assets.get_mascot_sprite(mascot_state)
        except KeyError:
            mascot = assets.get_mascot_sprite("idle")
        mascot_x = title.get_width() + 20
        surface.blit(mascot, (mascot_x, 10))

        # Score card with centered text
        score_card = assets.get_ui_sprite("score_card")
        score_x = layout.window_width - score_card.get_width() - 10
        surface.blit(score_card, (score_x, 10))

        # HUD score text — centered on score card (uses session.get_score())
        hud_score = session.get_score()
        text_surface = self._font.render(str(hud_score), True, (255, 255, 255))
        text_x = score_x + (score_card.get_width() - text_surface.get_width()) // 2
        text_y = 10 + (score_card.get_height() - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))

        # --- Layer 6: Overlay rendering (game_over / win) ---
        # ADR-S3-003: overlay consolidates from main.py into Renderer.
        # Order: overlay sprite → score text → new_game_button.
        if game_state in ("game_over", "win"):
            # 6a: Full-window overlay sprite
            overlay_name = (
                "game_over_overlay" if game_state == "game_over" else "win_overlay"
            )
            try:
                overlay_sprite = assets.get_ui_sprite(overlay_name)
                surface.blit(overlay_sprite, (0, 0))
            except KeyError:
                pass

            # 6b: Final score text centered on window
            if score is not None:
                score_text_surface = self._font.render(
                    str(score), True, (255, 255, 255),
                )
                score_text_x = (
                    layout.window_width - score_text_surface.get_width()
                ) // 2
                score_text_y = layout.window_height // 2
                surface.blit(score_text_surface, (score_text_x, score_text_y))

            # 6c: New-game button sprite positioned below board
            try:
                button_sprite = assets.get_ui_sprite("new_game_button")
                button_rect = self.get_new_game_button_rect()
                surface.blit(button_sprite, (button_rect[0], button_rect[1]))
            except KeyError:
                pass

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
