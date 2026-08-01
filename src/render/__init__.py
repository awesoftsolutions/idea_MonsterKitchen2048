"""src/render/__init__.py — Monster Kitchen render package.

Public exports: AssetLoader, BoardLayout, BoardRenderer, HUD.

BoardLayout is available immediately. AssetLoader, BoardRenderer, and HUD
are forward-reference names in __all__ that become importable once their
respective modules are created in Tasks 3-5.

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
# TODO(Task 4): from src.render.board_renderer import BoardRenderer
# TODO(Task 5): from src.render.hud import HUD

__all__ = ["AssetLoader", "BoardLayout", "BoardRenderer", "HUD"]
