"""src/main.py — Game entry point and state machine for Monster Kitchen 2048.

Defines GameState enum, GameWindow class with pygame game loop, input
handling, and state transitions. This is the ONLY file allowed to import
both pygame and src.core modules — the architectural bridge between the
pure-logic core layer and the pygame rendering pipeline.

Implements: ADR-019 (GameState enum), ADR-020 (key mapping dict),
ADR-021 (renderer API), Sprint 3 Task 2.

Usage::

    poetry run python -m src.main
"""

from __future__ import annotations

import enum
import sys
import traceback

import pygame

from src.core.board import Direction
from src.core.game_session import GameSession
from src.render.asset_loader import AssetLoader
from src.render.layout import BoardLayout
from src.render.renderer import Renderer


class GameState(enum.Enum):
    """Four-value game state enum used by the GameWindow state machine.

    Members:
        IDLE: Initial state with a fresh game board.
        PLAYING: Player has made at least one move.
        GAME_OVER: No legal moves remain.
        WIN: A tile with value >= 2048 has been created.
    """

    IDLE = "IDLE"
    PLAYING = "PLAYING"
    GAME_OVER = "GAME_OVER"
    WIN = "WIN"


def _check_win(grid: list[list[int]]) -> bool:
    """Scan a 4x4 grid for any cell with value >= 2048.

    Args:
        grid: The 4x4 tile value grid.

    Returns:
        True if any cell value >= 2048, False otherwise.
    """
    for row in grid:
        for value in row:
            if value >= 2048:
                return True
    return False


class GameWindow:
    """Main window managing pygame initialization, game loop, and state machine.

    Creates a GameSession internally and runs a 60 FPS immediate-mode
    rendering loop delegating all drawing to the Renderer.
    """

    # Key-to-Direction mapping for arrow keys (ADR-020).
    KEY_DIRECTION_MAP: dict[int, Direction] = {}

    def __init__(self) -> None:
        """Create GameSession and set initial state.

        Does NOT call pygame.init() — that happens in run().
        """
        self._session = GameSession()
        self._state = GameState.IDLE
        self._running = True

    def run(self) -> None:
        """Initialize pygame, create window, and enter the game loop.

        Raises:
            SystemExit: If pygame initialization or window creation fails.
        """
        try:
            pygame.init()
        except Exception as e:
            raise SystemExit(f"Failed to initialize pygame: {e}") from e

        try:
            self._screen = pygame.display.set_mode(
                (700, 800), flags=pygame.NOFRAME
            )
            pygame.display.set_caption("Favur 2048")
        except Exception as e:
            pygame.quit()
            raise SystemExit(f"Failed to create window: {e}") from e

        self._clock = pygame.time.Clock()

        layout = BoardLayout()
        asset_loader = AssetLoader()
        asset_loader.load_all(cell_size=layout.cell_size)
        self._renderer = Renderer(asset_loader, layout)
        self._assets = asset_loader

        while self._running:
            try:
                if self._process_events():
                    self._running = False
                    continue

                if not self._render():
                    break

                self._clock.tick(60)
            except pygame.error:
                traceback.print_exc()
                continue

        pygame.quit()

    def _process_events(self) -> bool:
        """Process all pygame events for the current frame.

        Returns:
            True if the game should quit, False to continue.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return True
                self._handle_keydown(event.key)

            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event.pos)

        return False

    def _handle_keydown(self, key: int) -> None:
        """Dispatch keyboard input to GameSession based on current state.

        Args:
            key: Pygame key constant from a KEYDOWN event.
        """
        key_direction_map = {
            pygame.K_UP: Direction.UP,
            pygame.K_DOWN: Direction.DOWN,
            pygame.K_LEFT: Direction.LEFT,
            pygame.K_RIGHT: Direction.RIGHT,
        }

        if key in key_direction_map:
            direction = key_direction_map[key]
            if self._state in (GameState.IDLE, GameState.PLAYING):
                result = self._session.move(direction)
                if result.moved:
                    if self._state == GameState.IDLE:
                        self._state = GameState.PLAYING
                    self._check_win_condition()
            return

        if key == pygame.K_z:
            if self._state == GameState.PLAYING:
                if self._session.can_undo():
                    self._session.undo()
            return

        if key == pygame.K_SPACE:
            if self._state in (GameState.GAME_OVER, GameState.WIN):
                self._session.new_game()
                self._state = GameState.IDLE
            return

    def _handle_mouse_click(self, pos: tuple[int, int]) -> None:
        """Detect new-game button click during GAME_OVER or WIN states.

        Args:
            pos: Mouse click position as (x, y).
        """
        if self._state not in (GameState.GAME_OVER, GameState.WIN):
            return

        try:
            btn_rect = self._renderer.get_new_game_button_rect()
        except AttributeError:
            return

        button = pygame.Rect(btn_rect)
        if button.collidepoint(pos):
            self._session.new_game()
            self._state = GameState.IDLE

    def _check_win_condition(self) -> None:
        """Check for win and game-over conditions after a successful move."""
        if self._state != GameState.PLAYING:
            return

        grid = self._session.get_board_grid()
        if _check_win(grid):
            self._state = GameState.WIN
            return

        if self._session.game_over:
            self._state = GameState.GAME_OVER

    def _render(self) -> bool:
        """Render one complete frame.

        Returns:
            True always. Exceptions are caught and logged per E-GW03.
        """
        try:
            self._screen.fill((0, 0, 0))
            self._renderer.render(self._screen, self._session)

            if self._state == GameState.GAME_OVER:
                try:
                    overlay = self._assets.get_ui_sprite("game_over_overlay")
                    self._screen.blit(overlay, (0, 0))
                except KeyError:
                    pass

            if self._state == GameState.WIN:
                try:
                    overlay = self._assets.get_ui_sprite("win_overlay")
                    self._screen.blit(overlay, (0, 0))
                except KeyError:
                    pass

            pygame.display.flip()
            return True

        except Exception:
            traceback.print_exc()
            return True


def main() -> None:
    """Module-level entry point for Monster Kitchen 2048."""
    try:
        window = GameWindow()
        window.run()
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        sys.exit(e.code)
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)