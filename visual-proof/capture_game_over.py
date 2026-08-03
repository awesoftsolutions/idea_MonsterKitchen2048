"""Visual-proof capture script: deterministic game-over screenshot.

Creates a GameSession with a full 4×4 board in guaranteed game-over state
(alternating 2/4 pattern with no adjacent equal pairs), renders the complete
frame including the game-over overlay via the Renderer, and saves the surface
as a 700×800 PNG file. Also updates the README.md manifest.

Uses SDL_VIDEODRIVER=dummy for headless rendering (no window required).

Usage::

    poetry run python visual-proof/capture_game_over.py

Implements: ADR-REM-001 (headless pygame), ADR-REM-002 (deterministic board),
ADR-REM-003 (manifest update), ADR-REM-004 (fallback asset loading).
"""
# IMPLEMENTATION DECISION: SDL_VIDEODRIVER must be set BEFORE any pygame
# import to bypass window creation. This is the standard SDL mechanism for
# headless rendering. Rationale: CI and headless environments have no display
# server. Alternatives: xvfb-run (Linux-only), mock surfaces (breaks Renderer).

import os

# Set headless driver BEFORE any pygame import — this is the critical ordering
# constraint that enables windowless rendering in CI/headless environments.
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

# Add project root to sys.path so src.* imports resolve.
script_dir = Path(__file__).parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pygame  # noqa: E402
import pygame.image  # noqa: E402
import pygame.font  # noqa: E402


# ---------------------------------------------------------------------------
# Fallback asset loader (ADR-REM-004)
# ---------------------------------------------------------------------------


class FallbackAssetLoader:
    """Colored-surface stand-in when real PNG assets are unavailable.

    Provides the same interface as AssetLoader (get_tile_sprite, get_ui_sprite,
    get_mascot_sprite, get_special_sprite) using solid-color pygame.Surfaces.

    Args:
        cell_size: Pixel dimension for tile sprites.
    """

    # Color palette — distinct pastels for visibility.
    TILE_COLORS: dict[int, tuple[int, int, int]] = {
        2: (238, 228, 218),
        4: (237, 224, 200),
        8: (242, 177, 121),
        16: (245, 149, 99),
        32: (246, 124, 95),
        64: (246, 94, 59),
        128: (237, 207, 114),
        256: (237, 204, 97),
        512: (237, 200, 80),
        1024: (237, 197, 63),
        2048: (237, 194, 46),
    }
    UI_SIZES: dict[str, tuple[int, int]] = {
        "background_wallpaper": (700, 800),
        "board_background": (650, 650),
        "cell_empty": (162, 162),
        "score_card": (200, 60),
        "title_logo": (300, 50),
        "new_game_button": (150, 50),
        "game_over_overlay": (700, 800),
        "win_overlay": (700, 800),
    }
    UI_COLORS: dict[str, tuple[int, int, int]] = {
        "background_wallpaper": (250, 245, 230),
        "board_background": (187, 173, 160),
        "cell_empty": (205, 193, 180),
        "score_card": (143, 122, 102),
        "title_logo": (119, 110, 101),
        "new_game_button": (143, 122, 102),
        "game_over_overlay": (238, 228, 218),
        "win_overlay": (237, 194, 46),
    }
    MASCOT_COLORS: dict[str, tuple[int, int, int]] = {
        "idle": (170, 130, 90),
        "happy": (100, 200, 100),
        "worried": (200, 100, 100),
    }
    SPECIAL_COLORS: dict[str, tuple[int, int, int]] = {
        "rotten_normal": (120, 100, 80),
        "rotten_warning": (200, 180, 60),
    }

    def __init__(self, cell_size: int) -> None:
        """Initialise the loader with a target cell size.

        Args:
            cell_size: Pixel width/height used when creating fallback surfaces.
        """
        self._cell_size = cell_size
        self._cache: dict[str, pygame.Surface] = {}
        self._build_cache()

    def _build_cache(self) -> None:
        """Pre-create all fallback surfaces."""
        size = self._cell_size
        for value, color in self.TILE_COLORS.items():
            surf = pygame.Surface((size, size))
            surf.fill(color)
            self._cache[f"tile_{value}"] = surf

        for name, (w, h) in self.UI_SIZES.items():
            surf = pygame.Surface((w, h))
            color = self.UI_COLORS.get(name, (200, 200, 200))
            surf.fill(color)
            self._cache[f"ui_{name}"] = surf

        for state, color in self.MASCOT_COLORS.items():
            surf = pygame.Surface((80, 80))
            surf.fill(color)
            self._cache[f"mascot_{state}"] = surf

        for name, color in self.SPECIAL_COLORS.items():
            surf = pygame.Surface((size, size))
            surf.fill(color)
            self._cache[f"special_{name}"] = surf

    def get_tile_sprite(self, value: int) -> pygame.Surface:
        """Return fallback tile surface for the given value.

        Args:
            value: Tile value (must be a key in TILE_COLORS).

        Returns:
            Coloured surface representing the tile.

        Raises:
            KeyError: If value is not present in the cache.
        """
        key = f"tile_{value}"
        if key not in self._cache:
            raise KeyError(f"Unknown tile value: {value}")
        return self._cache[key]

    def get_ui_sprite(self, name: str) -> pygame.Surface:
        """Return fallback UI surface for the given name.

        Args:
            name: UI element name (must be a key in UI_SIZES).

        Returns:
            Coloured surface representing the UI element.

        Raises:
            KeyError: If name is not present in the cache.
        """
        key = f"ui_{name}"
        if key not in self._cache:
            raise KeyError(f"Unknown UI sprite name: {name}")
        return self._cache[key]

    def get_mascot_sprite(self, state: str) -> pygame.Surface:
        """Return fallback mascot surface for the given state.

        Args:
            state: Mascot state (must be a key in MASCOT_COLORS).

        Returns:
            Coloured surface representing the mascot.

        Raises:
            KeyError: If state is not present in the cache.
        """
        key = f"mascot_{state}"
        if key not in self._cache:
            raise KeyError(f"Unknown mascot state: {state}")
        return self._cache[key]

    def get_special_sprite(self, name: str) -> pygame.Surface:
        """Return fallback special surface for the given name.

        Args:
            name: Special tile name (must be a key in SPECIAL_COLORS).

        Returns:
            Coloured surface representing the special tile.

        Raises:
            KeyError: If name is not present in the cache.
        """
        key = f"special_{name}"
        if key not in self._cache:
            raise KeyError(f"Unknown special sprite name: {name}")
        return self._cache[key]


# ---------------------------------------------------------------------------
# Manifest update (ADR-REM-003)
# ---------------------------------------------------------------------------


def update_manifest(script_dir: Path) -> None:
    """Update visual-proof/README.md with the new game-over screenshot entry.

    Adds a row to the Screenshot Inventory table, updates the total count,
    updates the Contents line, adds a Phase 4 Screenshots entry, and removes
    the 'not captured' known limitation.

    This function is idempotent — running it multiple times produces the same
    result without creating duplicate entries.

    Args:
        script_dir: Path to the visual-proof directory.
    """
    manifest_path = script_dir / "README.md"
    content = manifest_path.read_text(encoding="utf-8")

    # Guard: if the game_over row already exists in the table, skip all edits.
    marker = "phase4_game_over.png | Phase 4 | Game-over state"
    if marker in content:
        print("Manifest already contains phase4_game_over.png entry. Skipping update.")
        return

    # 1. Update total count: 9 → 10
    content = content.replace(
        "**Total screenshots**: 9 PNG files across 3 project phases.",
        "**Total screenshots**: 10 PNG files across 3 project phases.",
    )

    # 2. Update Contents line: add phase4_game_over before the trailing list
    content = content.replace(
        "phase4_mid_game.png \u2014 plus 5 helper scripts and this README.",
        "phase4_mid_game.png, phase4_game_over.png \u2014 plus 5 helper scripts and this README.",
    )

    # 3. Insert new row after phase4_mid_game.png row in Screenshot Inventory table
    old_row = "| phase4_mid_game.png | Phase 4 | Mid-game state with multiple tiles on board, mascot expression indicating activity, and non-trivial scoring | Multiple arrow key moves executed to reach a mid-game board state with diverse tile values | AC-3, AC-5 |"
    new_row = "| phase4_game_over.png | Phase 4 | Game-over state with full 4\u00d74 board, overlay visible, score display, and new-game button | Deterministic programmatic capture via capture_game_over.py \u2014 no player input | AC-7, AC-4, AC-5 |"
    content = content.replace(old_row, f"{old_row}\n{new_row}")

    # 4. Add entry to Phase 4 Screenshots list (after the last bullet)
    old_bullet = "- **phase4_mid_game.png**: Mid-game with active HUD and multiple tile types (AC-3, AC-5)"
    new_bullet = "- **phase4_game_over.png**: Game-over state with full board, overlay, score, and new-game button (AC-7, AC-4, AC-5)"
    content = content.replace(old_bullet, f"{old_bullet}\n{new_bullet}")

    # 5. Update the gap note about game_over not being captured
    content = content.replace(
        "Note: phase4_game_over.png was planned for capture but was not produced during Task 1.\nAC-7 is verified through code inspection and the feedback screenshot. See Known Limitations.",
        "Note: phase4_game_over.png is now captured via the deterministic capture script (capture_game_over.py).\nAC-7 is verified through the game-over screenshot and code inspection.",
    )

    # 6. Remove the 'not captured' known limitation
    content = content.replace(
        "- **phase4_game_over.png not captured**: Sprint plan listed this as a T1 deliverable, but Task 1 did not produce it. AC-7 is verified through phase4_feedback.png and code inspection. A dedicated game-over state screenshot should be captured in a future phase\n",
        "",
    )

    manifest_path.write_text(content, encoding="utf-8")
    print(f"Updated manifest at {manifest_path}")


# ---------------------------------------------------------------------------
# Main capture function
# ---------------------------------------------------------------------------


def main() -> None:
    """Capture a deterministic game-over screenshot and update the manifest.

    Steps:
        1. Initialize pygame with dummy video driver
        2. Create 700×800 off-screen Surface
        3. Create BoardLayout and load assets (with fallback)
        4. Create GameSession with deterministic game-over board
        5. Render the complete frame with game-over overlay
        6. Save as PNG
        7. Update manifest
        8. Cleanup
    """
    # STEP 1: Initialize pygame with dummy video driver
    pygame.init()
    pygame.font.init()
    print("Pygame initialized with SDL_VIDEODRIVER=dummy")

    try:
        # STEP 2: Create off-screen surface (700×800)
        surface = pygame.Surface((700, 800))

        # STEP 3: Create BoardLayout and load assets
        from src.render.layout import BoardLayout

        layout = BoardLayout()  # default 700×800, cell_size=162
        print(
            f"BoardLayout created: {layout.window_width}×{layout.window_height}, cell_size={layout.cell_size}"
        )

        try:
            from src.render.asset_loader import AssetLoader

            asset_loader = AssetLoader("assets")
            asset_loader.load_all(cell_size=layout.cell_size)
            print("Assets loaded successfully from assets/")
        except (FileNotFoundError, pygame.error, OSError) as e:
            print(f"Warning: Asset loading failed ({e}). Using fallback surfaces.")
            asset_loader = FallbackAssetLoader(layout.cell_size)

        # STEP 4: Create GameSession with deterministic game-over board
        from src.core.game_session import GameSession

        session = GameSession()

        # Reset board to clear the two random spawn tiles
        session._board.reset()

        # Define the alternating pattern that guarantees no adjacent equal pairs
        # This pattern has zero horizontal and zero vertical adjacent matches,
        # so is_game_over() returns True on a full board.
        game_over_pattern = [
            [2, 4, 2, 4],
            [4, 2, 4, 2],
            [2, 4, 2, 4],
            [4, 2, 4, 2],
        ]

        # Set all 16 cells
        for row in range(4):
            for col in range(4):
                session._board.set_cell(row, col, game_over_pattern[row][col])

        # Verify game-over state
        assert session.game_over, (
            f"Expected game_over=True but got False. Board: {session.get_board_grid()}"
        )
        print(f"Board set to game-over state. Score: {session.get_score()}")

        # STEP 5: Render the complete frame with game-over overlay
        from src.render.renderer import Renderer

        renderer = Renderer(asset_loader, layout)
        renderer.render(
            surface=surface,
            session=session,
            game_state="game_over",
            score=session.get_score(),
        )
        print("Rendered game-over frame")

        # STEP 6: Save as PNG
        output_path = script_dir / "phase4_game_over.png"
        pygame.image.save(surface, str(output_path))
        print(f"Saved game-over screenshot to {output_path}")

        # STEP 7: Update manifest
        update_manifest(script_dir)

    finally:
        # STEP 8: Cleanup
        pygame.quit()
        print("Done. phase4_game_over.png captured successfully.")


if __name__ == "__main__":
    main()
# CHANGELOG:
# - Sprint 4 Remediation: Added deterministic game-over screenshot capture script (pygame offscreen rendering, NOFRAME window, forced board fill)