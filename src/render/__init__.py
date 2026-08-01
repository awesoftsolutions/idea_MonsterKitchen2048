"""src/render/__init__.py — Monster Kitchen render package.

Public exports: AssetLoader, BoardLayout, Renderer.

BoardLayout is available immediately. AssetLoader and Renderer
are importable once their respective modules exist (Task 3).

Usage:
    >>> from src.render import BoardLayout
    >>> layout = BoardLayout()
    >>> layout.cell_size
    162
"""

from src.render.layout import BoardLayout
from src.render.layout import MASCOT_STATES  # noqa: F401
from src.render.layout import TILE_SPRITES  # noqa: F401
from src.render.layout import UI_SPRITE_NAMES  # noqa: F401

from src.render.asset_loader import AssetLoader  # noqa: F401
from src.render.renderer import Renderer  # noqa: F401

__all__ = ["AssetLoader", "BoardLayout", "Renderer"]
