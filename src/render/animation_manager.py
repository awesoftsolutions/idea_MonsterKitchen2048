"""Pure-logic tile animation manager for the 2048 game.

Computes per-tile pixel offsets and merge scale-pulse values for tile-slide
animation. The Renderer reads these offsets and applies them when blitting
tiles — AnimationManager does not blit anything itself.

This module has **zero pygame dependency**. All computation uses time-based
interpolation with plain Python floats and the TileMove dataclass from
src/core.board. Pixel offsets are relative to cell positions — the Renderer
converts grid coordinates to absolute pixels via BoardLayout.cell_rect() at
blit time.

Public API:
    AnimationManager
        __init__(duration_ms=250, cell_size=162)
        start_animation(tile_moves: list[TileMove]) → None
        update(dt: float) → None
        get_pixel_offset(row, col) → tuple[float, float]
        is_animating() → bool
        snap_to_end() → None
        get_merge_scale(row, col) → float

Internal:
    _AnimationEntry — dataclass storing per-tile animation state.

Constants:
    MERGE_PULSE_MS   — duration of the merge scale-pulse in milliseconds.
    PULSE_AMPLITUDE   — peak scale overshoot above 1.0 for merged tiles.
    DEFAULT_DURATION_MS — default slide animation duration in milliseconds.
"""

# CHANGELOG:
# - Sprint 4-1: New pure-logic AnimationManager class — tile-slide interpolation, merge scale-pulse, snap-to-end

from __future__ import annotations

from dataclasses import dataclass

from src.core.board import TileMove

# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------

MERGE_PULSE_MS: int = 200
PULSE_AMPLITUDE: float = 0.3
DEFAULT_DURATION_MS: int = 250


# ---------------------------------------------------------------------------
# Internal data structure
# ---------------------------------------------------------------------------


@dataclass
class _AnimationEntry:
    """Internal storage for a single tile's animation state.

    Attributes:
        source_pixel: Absolute pixel position of the source cell (x, y).
        dest_pixel: Absolute pixel position of the destination cell (x, y).
        delta: source_pixel minus dest_pixel — the total offset at t=0.
        value: Tile value.
        merged: True if this tile is the destination of a merge.
    """

    source_pixel: tuple[float, float]
    dest_pixel: tuple[float, float]
    delta: tuple[float, float]
    value: int
    merged: bool


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------


class AnimationManager:
    """Pure-logic tile animation manager.

    Computes per-tile pixel offsets and merge scale-pulse values for
    tile-slide animation. The Renderer reads these offsets and applies
    them when blitting tiles.

    Grid-to-pixel convention:
        Column → x-axis (horizontal), Row → y-axis (vertical).

    Offset semantics:
        get_pixel_offset(row, col) returns the delta FROM destination TO
        current visual position. At t=0, offset = full delta (tile at source).
        At t≥1, offset = (0, 0) (tile at destination).

    Attributes:
        duration_ms: Total animation duration in milliseconds.
        cell_size: Pixel size of one grid cell.
    """

    def __init__(
        self, duration_ms: int = DEFAULT_DURATION_MS, cell_size: int = 162
    ) -> None:
        """Initialize animation manager with animation duration and cell size.

        Args:
            duration_ms: Total animation duration in milliseconds.
            cell_size: Pixel size of one grid cell (default 162, matches BoardLayout).
        """
        self.duration_ms: int = duration_ms
        self.cell_size: int = cell_size
        self._elapsed_ms: float = 0.0
        self._entries: list[_AnimationEntry] = []
        self._merge_map: dict[tuple[int, int], int] = {}
        self._source_map: dict[tuple[int, int], int] = {}
        self._animating: bool = False

    def start_animation(self, tile_moves: list[TileMove]) -> None:
        """Begin a new animation from a list of TileMove records.

        An empty list is a no-op — existing animation state is preserved.

        Args:
            tile_moves: Movement records from the latest MoveResult.
        """
        if not tile_moves:
            return

        self._elapsed_ms = 0.0
        self._entries = []
        self._merge_map = {}
        self._source_map = {}

        for move in tile_moves:
            # Convert grid coordinates to pixel positions using cell_size.
            # col → x-axis, row → y-axis.
            source_x = float(move.source_col * self.cell_size)
            source_y = float(move.source_row * self.cell_size)
            dest_x = float(move.dest_col * self.cell_size)
            dest_y = float(move.dest_row * self.cell_size)

            # Delta = source - dest.  At progress=0, offset = delta (tile at source).
            # At progress=1, offset = (0, 0) (tile at destination).
            delta_x = source_x - dest_x
            delta_y = source_y - dest_y

            entry = _AnimationEntry(
                source_pixel=(source_x, source_y),
                dest_pixel=(dest_x, dest_y),
                delta=(delta_x, delta_y),
                value=move.value,
                merged=move.merged,
            )
            entry_index = len(self._entries)
            self._entries.append(entry)

            # Index by source position for get_pixel_offset lookup.
            self._source_map[(move.source_row, move.source_col)] = entry_index

            # Index merge destinations separately for get_merge_scale lookup.
            if move.merged:
                self._merge_map[(move.dest_row, move.dest_col)] = entry_index

        self._animating = True

    def update(self, dt: float) -> None:
        """Advance the animation timer by dt seconds.

        Args:
            dt: Delta time in seconds since last update.
        """
        if not self._animating:
            return

        # Convert dt from seconds to milliseconds and accumulate.
        dt_ms = dt * 1000.0
        self._elapsed_ms += dt_ms

        # Clamp to duration.
        if self._elapsed_ms >= self.duration_ms:
            self._elapsed_ms = float(self.duration_ms)
            self._animating = False

    def get_pixel_offset(self, row: int, col: int) -> tuple[float, float]:
        """Return the current pixel offset for a tile originating at (row, col).

        The offset is relative to the tile's destination cell — the Renderer
        adds it to the destination cell's absolute pixel position.

        Args:
            row: Grid row index (0-based).
            col: Grid column index (0-based).

        Returns:
            (offset_x, offset_y) in pixels from the tile's destination cell
            position. Returns (0.0, 0.0) if no animation active or tile not
            found.
        """
        if not self._animating:
            return (0.0, 0.0)

        key = (row, col)
        if key not in self._source_map:
            return (0.0, 0.0)

        entry = self._entries[self._source_map[key]]

        # Progress: linear interpolation, clamped to [0.0, 1.0].
        progress = self._elapsed_ms / self.duration_ms
        if progress > 1.0:
            progress = 1.0
        if progress < 0.0:
            progress = 0.0

        # Offset = delta * (1 - progress).
        # At progress=0: offset = delta (tile at source).
        # At progress=1: offset = (0, 0) (tile at destination).
        offset_x = entry.delta[0] * (1.0 - progress)
        offset_y = entry.delta[1] * (1.0 - progress)

        return (offset_x, offset_y)

    def is_animating(self) -> bool:
        """Return True while animation is in progress."""
        return self._animating

    def snap_to_end(self) -> None:
        """Immediately complete the animation.

        Sets elapsed time to the full duration and marks animation as
        complete. Used when new input interrupts a running animation.
        """
        if not self._animating:
            return

        self._elapsed_ms = float(self.duration_ms)
        self._animating = False

    def get_merge_scale(self, row: int, col: int) -> float:
        """Return merge pulse scale for a tile at destination (row, col).

        Args:
            row: Grid row index (0-based) — DESTINATION position of the tile.
            col: Grid column index (0-based) — DESTINATION position of the tile.

        Returns:
            Scale factor: 1.0 normally, >=1.0 during merge pulse window.
            Peak value is 1.0 + PULSE_AMPLITUDE (default 1.3).
        """
        key = (row, col)

        if key not in self._merge_map:
            return 1.0

        # Check if within pulse window.
        if self._elapsed_ms >= MERGE_PULSE_MS:
            return 1.0

        # Linear decay: starts at 1.0 + PULSE_AMPLITUDE, decays to 1.0.
        pulse_progress = self._elapsed_ms / MERGE_PULSE_MS
        scale = 1.0 + PULSE_AMPLITUDE * (1.0 - pulse_progress)

        return scale
