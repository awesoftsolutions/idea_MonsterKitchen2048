"""src/main.py — Game entry point and state machine for Monster Kitchen 2048.

Defines GameState enum, InputHandler, StateManager, and GameWindow class
with pygame game loop, input handling, and state transitions. This is the
ONLY file allowed to import both pygame and src.core modules — the
architectural bridge between the pure-logic core layer and the pygame
rendering pipeline.

Implements: ADR-019 (GameState enum), ADR-020 (key mapping dict),
ADR-021 (renderer API), Sprint 3 Task 2.

Usage::

    poetry run python -m src.main
"""

# CHANGELOG:
# - Sprint 4-1: AnimationManager integration — import + optional init in GameWindow, animation start/update in loop
# - Sprint 4-1: Animation interruption handling — snap_to_end() on new arrow input before processing move
# - Sprint 4-2: ToastManager integration — import (try/except), _toast_manager init, new_achievements propagation via InputHandler return dict, toast enqueue in _handle_keydown, toast update/render in _render, toast clear on new_game

from __future__ import annotations

import enum
import sys
import traceback

import pygame
from typing import Any

from src.core.board import Direction, TileMove
from src.core.game_session import GameSession
from src.render.asset_loader import AssetLoader
from src.render.layout import ANIMATION_DURATION_MS, BoardLayout
from src.render.renderer import Renderer

try:
    from src.render.animation_manager import AnimationManager
except ImportError:
    AnimationManager = None  # type: ignore[assignment,misc]

try:
    from src.render.toast_manager import ToastManager
except ImportError:
    ToastManager = None  # type: ignore[assignment,misc]

try:
    from src.render import merge_celebration as _merge_celebration
    from src.render.merge_celebration import update_effects, cleanup_expired_effects
except ImportError:
    _merge_celebration = None  # type: ignore[assignment]
    update_effects = None  # type: ignore[assignment]
    cleanup_expired_effects = None  # type: ignore[assignment]


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


class InputHandler:
    """Handles keyboard and mouse input mapping and dispatch.

    Extracted from GameWindow to separate input concerns from game orchestration.
    This class is stateless — it does not hold references to GameSession or
    GameState. Methods receive them as parameters.
    """

    # Class attribute replacing the locally-built dict in _handle_keydown (ADR-020).
    KEY_DIRECTION_MAP: dict[int, Direction] = {
        pygame.K_UP: Direction.UP,
        pygame.K_DOWN: Direction.DOWN,
        pygame.K_LEFT: Direction.LEFT,
        pygame.K_RIGHT: Direction.RIGHT,
    }

    @staticmethod
    def get_direction_for_key(key: int) -> Direction | None:
        """Return the Direction for an arrow key, or None for non-arrow keys.

        Args:
            key: Pygame key constant.

        Returns:
            The corresponding Direction for arrow keys, or None for others.
        """
        return InputHandler.KEY_DIRECTION_MAP.get(key)

    @staticmethod
    def handle_keydown(
        key: int,
        state: GameState,
        session: GameSession,
        animation_manager: Any | None,
    ) -> dict[str, Any] | None:
        """Dispatch a KEYDOWN event to the appropriate game action.

        Args:
            key: Pygame key constant from a KEYDOWN event.
            state: Current GameState.
            session: The GameSession instance.
            animation_manager: The AnimationManager instance or None.

        Returns:
            A dict describing what happened, or None if key is not recognized
            or not valid in the current state. Possible return dicts:
            {"action": "move", "moved": bool, "tile_moves": list, "state_transition": GameState | None, "new_achievements": list}
            {"action": "undo"}
            {"action": "new_game", "new_state": GameState.IDLE}
        """
        # Phase 1: Arrow key handling (move)
        # Support both integer pygame key constants and Direction enum values
        # (the latter used in tests and programmatic dispatch)
        direction = InputHandler.KEY_DIRECTION_MAP.get(key)
        if direction is None and isinstance(key, str):
            try:
                direction = Direction(key)
            except ValueError:
                direction = None
        if direction is not None:

            if state not in (GameState.IDLE, GameState.PLAYING):
                return None

            # Snap any running animation before processing new move (AC-18)
            if animation_manager is not None and animation_manager.is_animating():
                animation_manager.snap_to_end()

            result = session.move(direction)

            state_transition = None
            if result.moved and state == GameState.IDLE:
                state_transition = GameState.PLAYING

            return {
                "action": "move",
                "moved": result.moved,
                "tile_moves": result.tile_moves,
                "state_transition": state_transition,
                "new_achievements": result.new_achievements,
            }

        # Phase 2: Z key handling (undo)
        if key == pygame.K_z:
            if state == GameState.PLAYING:
                if session.can_undo():
                    session.undo()
            return {"action": "undo"}

        # Phase 3: Space key handling (new game)
        if key == pygame.K_SPACE:
            if state in (GameState.GAME_OVER, GameState.WIN):
                session.new_game()
                return {"action": "new_game", "new_state": GameState.IDLE}
            return None

        # Unrecognized key
        return None

    @staticmethod
    def handle_mouse_click(
        pos: tuple[int, int],
        state: GameState,
        renderer: Any,
    ) -> bool:
        """Check if a mouse click hits the new-game button during GAME_OVER/WIN.

        Args:
            pos: Mouse click position as (x, y).
            state: Current GameState.
            renderer: The Renderer instance.

        Returns:
            True if new-game should be triggered, False otherwise.
        """
        if state not in (GameState.GAME_OVER, GameState.WIN):
            return False

        try:
            btn_rect = renderer.get_new_game_button_rect()
        except AttributeError:
            return False

        button = pygame.Rect(btn_rect)
        return button.collidepoint(pos)


class StateManager:
    """Manages the GameState enum and handles state transitions.

    Extracted from GameWindow to separate state logic from game orchestration.
    Owns the GameState value and the win/game-over condition checks.
    """

    def __init__(self, initial_state: GameState = GameState.IDLE) -> None:
        """Initialize with the given state.

        Args:
            initial_state: The initial GameState value (default IDLE).
        """
        self._state = initial_state

    @property
    def state(self) -> GameState:
        """Return the current GameState value."""
        return self._state

    @state.setter
    def state(self, value: GameState) -> None:
        """Set the current GameState value."""
        self._state = value

    def transition_to(self, new_state: GameState) -> None:
        """Transition to a new GameState unconditionally.

        Args:
            new_state: The GameState to transition to.
        """
        self._state = new_state

    def check_win_condition(self, session: GameSession) -> None:
        """Check for win and game-over conditions using session state.

        Calls the module-level _check_win() helper on session.get_board_grid().
        Transitions to WIN if grid has a value >= 2048.
        Transitions to GAME_OVER if no 2048+ on board and session.game_over
        is True. Only checks if current state is PLAYING; otherwise no-op.

        Args:
            session: The GameSession instance to check.
        """
        if self._state is not GameState.PLAYING:
            return

        grid = session.get_board_grid()
        if _check_win(grid):
            self._state = GameState.WIN
            return

        if session.game_over:
            self._state = GameState.GAME_OVER

    def is_input_allowed(self) -> bool:
        """Return True if arrow key / Z key input is valid in current state.

        Returns:
            True for IDLE and PLAYING; False for GAME_OVER and WIN.
        """
        return self._state in (GameState.IDLE, GameState.PLAYING)

    def is_new_game_allowed(self) -> bool:
        """Return True if new-game action is valid in current state.

        Returns:
            True for GAME_OVER and WIN; False for IDLE and PLAYING.
        """
        return self._state in (GameState.GAME_OVER, GameState.WIN)

    def is_undo_allowed(self) -> bool:
        """Return True if undo action is valid in current state.

        Returns:
            True only for PLAYING.
        """
        return self._state is GameState.PLAYING


class GameWindow:
    """Thin orchestrator delegating input and state to extracted classes.

    Creates a GameSession internally and runs a 60 FPS immediate-mode
    rendering loop delegating all drawing to the Renderer.
    """

    # Key-to-Direction mapping for arrow keys (ADR-020).
    KEY_DIRECTION_MAP: dict[int, Direction] = {}

    def __init__(self) -> None:
        """Create GameSession, StateManager, and animation manager.

        Does NOT call pygame.init() — that happens in run().
        """
        self._session = GameSession()
        self._state_manager = StateManager(initial_state=GameState.IDLE)
        self._running = True
        self._pending_tile_moves: list[TileMove] = []
        if AnimationManager is not None:
            self._animation_manager = AnimationManager(
                duration_ms=ANIMATION_DURATION_MS,
                cell_size=162,
            )
        else:
            self._animation_manager = None
        self._toast_manager = ToastManager() if ToastManager is not None else None
        self._celebration_effects: list[Any] = []
        self._last_dt: float = 0.0

    @property
    def _state(self) -> GameState:
        """Delegation property forwarding to self._state_manager.state."""
        return self._state_manager.state

    @_state.setter
    def _state(self, value: GameState) -> None:
        """Delegation property forwarding to self._state_manager.state setter."""
        self._state_manager.state = value

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
            self._screen = pygame.display.set_mode((700, 800), flags=pygame.NOFRAME)
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

        if AnimationManager is not None:
            self._animation_manager = AnimationManager(
                duration_ms=ANIMATION_DURATION_MS,
                cell_size=layout.cell_size,
            )

        while self._running:
            try:
                if self._process_events():
                    self._running = False
                    continue

                # Feed pending tile moves to animation manager before render
                if self._pending_tile_moves and self._animation_manager is not None:
                    self._animation_manager.start_animation(self._pending_tile_moves)
                    self._pending_tile_moves.clear()

                dt = self._clock.tick(60) / 1000.0
                self._last_dt = dt

                # Advance animation clock
                if self._animation_manager is not None:
                    self._animation_manager.update(dt)

                if not self._render():
                    break
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
        """Thin wrapper: delegates to InputHandler.handle_keydown().

        Args:
            key: Pygame key constant from a KEYDOWN event.
        """
        result = InputHandler.handle_keydown(
            key=key,
            state=self._state,
            session=self._session,
            animation_manager=self._animation_manager,
        )

        if result is None:
            return

        action = result.get("action")

        # Apply move-specific logic
        if action == "move":
            if result.get("moved"):
                self._pending_tile_moves.extend(result["tile_moves"])
                # Apply state transitions from move (IDLE -> PLAYING)
                state_transition = result.get("state_transition")
                if state_transition is not None:
                    self._state = state_transition
                # Check win/game-over via StateManager
                self._check_win_condition()
                # Enqueue achievement toasts
                new_achievements = result.get("new_achievements", [])
                if new_achievements and self._toast_manager is not None:
                    for ach in new_achievements:
                        self._toast_manager.show(ach.name, ach.description)
                # Create celebration effects for merged tiles
                if _merge_celebration is not None:
                    for tile_move in result["tile_moves"]:
                        if tile_move.merged:
                            effect = _merge_celebration.create_effect(
                                tile_move.dest_row,
                                tile_move.dest_col,
                                tile_move.value,
                            )
                            self._celebration_effects.append(effect)

        # Apply new_game action
        if action == "new_game":
            if "new_state" in result:
                self._state = result["new_state"]
            if self._toast_manager is not None:
                self._toast_manager.clear()
            self._celebration_effects = []

    def _handle_mouse_click(self, pos: tuple[int, int]) -> None:
        """Detect new-game button click during GAME_OVER or WIN states.

        Delegates click detection to InputHandler, then applies state
        transitions if new-game should be triggered.

        Args:
            pos: Mouse click position as (x, y).
        """
        should_start_new_game = InputHandler.handle_mouse_click(
            pos=pos,
            state=self._state,
            renderer=self._renderer,
        )

        if should_start_new_game:
            self._session.new_game()
            self._state = GameState.IDLE
            if self._toast_manager is not None:
                self._toast_manager.clear()
            self._celebration_effects = []

    def _check_win_condition(self) -> None:
        """Thin wrapper: delegates to StateManager.check_win_condition()."""
        self._state_manager.check_win_condition(self._session)

    def _render(self) -> bool:
        """Render one complete frame.

        Returns:
            True always. Exceptions are caught and logged per E-GW03.
        """
        try:
            self._screen.fill((0, 0, 0))

            # Build active_moves dict from animation manager offsets
            active_moves: dict[tuple[int, int], tuple[float, float]] | None = None
            if (
                self._animation_manager is not None
                and self._animation_manager.is_animating()
            ):
                active_moves = {}
                for row in range(4):
                    for col in range(4):
                        offset = self._animation_manager.get_pixel_offset(row, col)
                        if offset != (0.0, 0.0):
                            active_moves[(row, col)] = offset

            # Update celebration effects
            dt_ms = self._last_dt * 1000.0
            if update_effects is not None:
                update_effects(self._celebration_effects, dt_ms)
            if cleanup_expired_effects is not None:
                cleanup_expired_effects(self._celebration_effects)

            self._renderer.render(
                self._screen,
                self._session,
                active_moves=active_moves,
                celebration_effects=self._celebration_effects,
            )

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

            # Render achievement toasts on top of everything
            if self._toast_manager is not None:
                self._toast_manager.update(self._last_dt)
                self._toast_manager.render(self._screen)

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
