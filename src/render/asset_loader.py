"""AssetLoader — startup asset loading and caching for Monster Kitchen.

Loads all 24 Monster Kitchen PNG assets from the ``assets/`` directory at
startup, caches them as ``pygame.Surface`` objects, and provides typed
accessor methods for tile sprites, UI elements, mascot sprites, and special
tiles. Uses deferred imports for layout dictionaries to avoid circular
dependencies and enable headless testing via monkeypatch.

Implements: IF-AssetLoader, ADR-016 (eager loading), ADR-020 (dictionary
lookup). Error codes E-AL01 through E-AL04.

Usage::

    from src.render.asset_loader import AssetLoader

    loader = AssetLoader("assets")
    loader.load_all(cell_size=162)

    tile = loader.get_tile_sprite(2)
    bg = loader.get_ui_sprite("board_background")
    mascot = loader.get_mascot_sprite("happy")
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame


# ---------------------------------------------------------------------------
# Subdirectory constants
# ---------------------------------------------------------------------------

ALL_TILE_SUBDIR: str = "tiles"
ALL_UI_SUBDIR: str = "ui"
ALL_MASCOT_SUBDIR: str = "mascot"


# ---------------------------------------------------------------------------
# Special sprites — hardcoded, NOT from layout.py
# ---------------------------------------------------------------------------

SPECIAL_SPRITES: dict[str, str] = {
    "rotten_normal": "tile_12_rotten_food.png",
    "rotten_warning": "tile_13_rotten_warning.png",
}


class AssetLoader:
    """Load all 24 Monster Kitchen PNG assets at startup and cache them.

    Eagerly loads every required sprite into a flat ``dict[str, Surface]``
    cache during :meth:`load_all`. After that call succeeds, every accessor
    for a known key is guaranteed to return a valid ``pygame.Surface``.

    Args:
        assets_dir: Path to the root assets directory (default ``"assets"``).
    """

    def __init__(self, assets_dir: str | Path = "assets") -> None:
        self.assets_dir: Path = Path(assets_dir)
        self._cache: dict[str, pygame.Surface] = {}
        self._tile_size: int = 0

    def load_all(self, cell_size: int, window_width: int = 700, window_height: int = 800) -> None:
        """Load all 24 PNGs into ``self._cache``.

        Reads filenames from ``TILE_SPRITES``, ``UI_SPRITE_NAMES``, and
        ``MASCOT_STATES`` (imported from ``src.render.layout``) plus the
        module-level ``SPECIAL_SPRITES`` constant.

        Args:
            cell_size: Pixel size for scaling tile sprites.
            window_width: Window width in pixels for scaling full-window UI sprites (default 700).
            window_height: Window height in pixels for scaling full-window UI sprites (default 800).

        Raises:
            FileNotFoundError: If *assets_dir* does not exist (E-AL01).
            pygame.error: If any PNG is corrupt or unreadable (E-AL02).
        """
        # Step 1 — Validate assets directory
        if not self.assets_dir.is_dir():
            raise FileNotFoundError(f"Assets directory not found: {self.assets_dir}")

        self._tile_size = cell_size

        # Step 2 — Deferred import of layout dictionaries
        import pygame
        from src.render.layout import MASCOT_STATES
        from src.render.layout import TILE_SPRITES
        from src.render.layout import UI_SPRITE_NAMES
        from src.render.layout import TITLE_AREA_HEIGHT

        # Use a temporary dict so that self._cache stays empty on failure.
        temp_cache: dict[str, pygame.Surface] = {}

        # Step 3 — Load tile sprites (scaled to cell_size)
        for value, filename in TILE_SPRITES.items():
            full_path = self.assets_dir / ALL_TILE_SUBDIR / filename
            surface = pygame.image.load(full_path)
            temp_cache[f"tile_{value}"] = pygame.transform.smoothscale(
                surface, (cell_size, cell_size)
            )

        # Step 4 — Load special tile sprites (scaled to cell_size)
        for key, filename in SPECIAL_SPRITES.items():
            full_path = self.assets_dir / ALL_TILE_SUBDIR / filename
            surface = pygame.image.load(full_path)
            temp_cache[f"special_{key}"] = pygame.transform.smoothscale(
                surface, (cell_size, cell_size)
            )

        # Step 5 — Load UI sprites scaled to their intended display dimensions.
        # All source PNGs are 1024×1024; each is scaled to fit its role in the layout.
        _ui_sizes: dict[str, tuple[int, int]] = {
            "background_wallpaper": (window_width, window_height),
            "board_background": (window_width, window_height - TITLE_AREA_HEIGHT),
            "cell_empty": (cell_size, cell_size),
            "score_card": (cell_size, TITLE_AREA_HEIGHT),
            "title_logo": (cell_size * 2, TITLE_AREA_HEIGHT),
            "new_game_button": (cell_size, cell_size // 2),
            "game_over_overlay": (window_width, window_height),
            "win_overlay": (window_width, window_height),
        }
        for name, filename in UI_SPRITE_NAMES.items():
            full_path = self.assets_dir / ALL_UI_SUBDIR / filename
            surface = pygame.image.load(full_path)
            target_size = _ui_sizes.get(name)
            if target_size is not None:
                temp_cache[f"ui_{name}"] = pygame.transform.smoothscale(surface, target_size)
            else:
                temp_cache[f"ui_{name}"] = surface

        # Step 6 — Load mascot sprites scaled to HUD title area height
        mascot_size = (TITLE_AREA_HEIGHT, TITLE_AREA_HEIGHT)
        for state, filename in MASCOT_STATES.items():
            full_path = self.assets_dir / ALL_MASCOT_SUBDIR / filename
            surface = pygame.image.load(full_path)
            temp_cache[f"mascot_{state}"] = pygame.transform.smoothscale(surface, mascot_size)

        # Step 7 — Only commit on full success
        self._cache = temp_cache

    def get_tile_sprite(self, value: int) -> pygame.Surface:
        """Return the cached Surface for a tile value.

        Args:
            value: A power-of-2 tile value (2, 4, 8, …, 2048).

        Returns:
            ``pygame.Surface`` scaled to ``(cell_size, cell_size)``.

        Raises:
            KeyError: If *value* is not in the tile mapping (E-AL03).
        """
        cache_key = f"tile_{value}"
        if cache_key not in self._cache:
            raise KeyError(f"Unknown tile value: {value}")
        return self._cache[cache_key]

    def get_ui_sprite(self, name: str) -> pygame.Surface:
        """Return a cached UI element surface by name.

        Args:
            name: One of the ``UI_SPRITE_NAMES`` keys.

        Returns:
            ``pygame.Surface`` at native resolution.

        Raises:
            KeyError: If *name* is not in the UI mapping (E-AL04).
        """
        cache_key = f"ui_{name}"
        if cache_key not in self._cache:
            raise KeyError(f"Unknown UI sprite name: {name}")
        return self._cache[cache_key]

    def get_mascot_sprite(self, state: str) -> pygame.Surface:
        """Return a cached mascot sprite by state.

        Args:
            state: One of ``"idle"``, ``"happy"``, ``"worried"``.

        Returns:
            ``pygame.Surface`` at native resolution.

        Raises:
            KeyError: If *state* is not in the mascot mapping.
        """
        cache_key = f"mascot_{state}"
        if cache_key not in self._cache:
            raise KeyError(f"Unknown mascot state: {state}")
        return self._cache[cache_key]

    def get_special_sprite(self, name: str) -> pygame.Surface:
        """Return a cached special tile sprite by name.

        Args:
            name: One of ``"rotten_normal"``, ``"rotten_warning"``.

        Returns:
            ``pygame.Surface`` at native resolution.

        Raises:
            KeyError: If *name* is not in ``SPECIAL_SPRITES``.
        """
        cache_key = f"special_{name}"
        if cache_key not in self._cache:
            raise KeyError(f"Unknown special sprite name: {name}")
        return self._cache[cache_key]
