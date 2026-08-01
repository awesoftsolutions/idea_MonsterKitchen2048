"""src/render/layout.py — BoardLayout dataclass and sprite mapping constants.

Purpose:
    Defines computed layout positioning for the 4×4 game grid in a 700×800
    pixel pygame window, plus three sprite-mapping dictionaries used by the
    AssetLoader, BoardRenderer, and HUD components.

Design:
    BoardLayout is a pure-Python dataclass that returns ``tuple[int, int, int, int]``
    from ``cell_rect()`` and ``board_rect()`` rather than ``pygame.Rect``.
    Callers convert at the usage site: ``rect = pygame.Rect(layout.cell_rect(row, col))``.
    This keeps layout math testable in headless pytest without a pygame context.

    No pygame, os, or pathlib imports — pure Python only.
    All pixel values are integers (``//`` integer division throughout).

Usage:
    >>> from src.render.layout import BoardLayout
    >>> layout = BoardLayout()
    >>> layout.cell_size
    162
    >>> layout.cell_rect(0, 0)
    (25, 138, 162, 162)
    >>> layout.cell_rect(3, 3)
    (511, 624, 162, 162)

Constants:
    GRID_SIZE (int): Number of cells per row/column (4).
    BOARD_MARGIN (int): Pixel margin from window edge to board (25).
    TITLE_AREA_HEIGHT (int): Pixels reserved above grid for title/logo/mascot (113).

Exports:
    BoardLayout          — computed layout positioning dataclass
    TILE_SPRITES         — tile value → sprite filename mapping (11 entries)
    UI_SPRITE_NAMES      — UI element name → sprite filename mapping (8 entries)
    MASCOT_STATES        — mascot state → sprite filename mapping (3 entries)
"""

# CHANGELOG:
# - Sprint 4-1: Add ANIMATION_DURATION_MS constant (250ms) for AnimationManager integration

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Module-level layout constants
# ---------------------------------------------------------------------------

GRID_SIZE: int = 4
BOARD_MARGIN: int = 25
TITLE_AREA_HEIGHT: int = 113
ANIMATION_DURATION_MS: int = 250


# ---------------------------------------------------------------------------
# BoardLayout dataclass
# ---------------------------------------------------------------------------


@dataclass
class BoardLayout:
    """Computed layout positioning for the 4×4 grid in a 700×800 window.

    All fields are integers (pygame pixel requirement). Computed in __post_init__.
    cell_rect and board_rect return (x, y, w, h) tuples for pygame.Rect() compatibility.
    """

    window_width: int = 700
    window_height: int = 800
    GRID_SIZE: int = 4
    board_margin_x: int = BOARD_MARGIN
    board_margin_y: int = BOARD_MARGIN
    cell_size: int = 0  # computed: (window_width - 2 * board_margin_x) // GRID_SIZE
    board_width: int = 0  # computed: cell_size * GRID_SIZE
    board_height: int = 0  # computed: cell_size * GRID_SIZE
    grid_origin_x: int = 0  # computed: board_margin_x
    grid_origin_y: int = 0  # computed: TITLE_AREA_HEIGHT + board_margin_y

    def __post_init__(self) -> None:
        """Compute derived layout fields from window dimensions and margins."""
        self.cell_size = (self.window_width - 2 * self.board_margin_x) // self.GRID_SIZE
        self.board_width = self.cell_size * self.GRID_SIZE
        self.board_height = self.cell_size * self.GRID_SIZE
        self.grid_origin_x = self.board_margin_x
        self.grid_origin_y = TITLE_AREA_HEIGHT + self.board_margin_y

    def cell_rect(self, row: int, col: int) -> tuple[int, int, int, int]:
        """Return (x, y, width, height) for the cell at (row, col).

        Args:
            row: Grid row index (0-based, 0..GRID_SIZE-1).
            col: Grid column index (0-based, 0..GRID_SIZE-1).

        Returns:
            4-tuple (x, y, width, height) compatible with pygame.Rect().
        """
        x = self.grid_origin_x + col * self.cell_size
        y = self.grid_origin_y + row * self.cell_size
        return (x, y, self.cell_size, self.cell_size)

    def board_rect(self) -> tuple[int, int, int, int]:
        """Return (x, y, width, height) for the full grid area.

        Returns:
            4-tuple (x, y, width, height) compatible with pygame.Rect().
        """
        return (
            self.grid_origin_x,
            self.grid_origin_y,
            self.board_width,
            self.board_height,
        )


# ---------------------------------------------------------------------------
# Sprite mapping constants (ADR-020)
# ---------------------------------------------------------------------------

TILE_SPRITES: dict[int, str] = {
    2: "tile_01_blueberry.png",
    4: "tile_02_cupcake.png",
    8: "tile_03_pie.png",
    16: "tile_04_cake.png",
    32: "tile_05_birthday_cake.png",
    64: "tile_06_wedding_cake.png",
    128: "tile_07_rainbow_cake.png",
    256: "tile_08_trophy_cake.png",
    512: "tile_09_galaxy_cake.png",
    1024: "tile_10_phoenix_cake.png",
    2048: "tile_11_mega_cake.png",
}

# All UI sprite filenames follow the tile_XX_<name>.png convention (see asset manifest).
UI_SPRITE_NAMES: dict[str, str] = {
    "board_background": "tile_14_board_background.png",
    "cell_empty": "tile_15_cell_empty.png",
    "score_card": "tile_16_score_card.png",
    "title_logo": "tile_17_title_logo.png",
    "new_game_button": "tile_18_new_game_button.png",
    "game_over_overlay": "tile_19_game_over_overlay.png",
    "win_overlay": "tile_20_win_overlay.png",
    "background_wallpaper": "tile_21_background_wallpaper.png",
}

# All mascot sprite filenames follow the tile_XX_<name>.png convention (see asset manifest).
MASCOT_STATES: dict[str, str] = {
    "idle": "tile_22_mascot_idle.png",
    "happy": "tile_23_mascot_happy.png",
    "worried": "tile_24_mascot_worried.png",
}
