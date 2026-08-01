"""Test suite for src/render/layout.py — BoardLayout and sprite mappings.

Purpose:
    Verifies correctness of the BoardLayout dataclass (computed layout
    positioning constants) and three sprite-mapping dictionaries
    (TILE_SPRITES, UI_SPRITE_NAMES, MASCOT_STATES). Also verifies
    src/render/__init__.py exports.

System:
    Headless pytest suite. No fixtures, no conftest — each test constructs
    its own BoardLayout() instance for full isolation. Imports from
    src.render.layout (BoardLayout, TILE_SPRITES, UI_SPRITE_NAMES,
    MASCOT_STATES) and src.render (package init).

Dependencies:
    pytest, os — third-party and stdlib. src.render.layout — production code.

Used-by:
    CI pipeline (pytest), Sprint 2 Task 2 acceptance verification.

Public API:
    Test functions (18 standalone):
        test_boardlayout_default_dimensions()
            BoardLayout defaults match 700x800 window, GRID_SIZE 4.
        test_boardlayout_cell_size_is_positive_integer()
            cell_size is 162, positive, and isinstance int.
        test_boardlayout_computed_fields()
            All computed fields (board_width, board_height, grid_origin_x/y)
            match expected values.
        test_boardlayout_all_fields_are_integers()
            Every field on BoardLayout is an int (pygame pixel requirement).
        test_cell_rect_origin()
            cell_rect(0, 0) returns grid origin position.
        test_cell_rect_bottom_right()
            cell_rect(3, 3) returns correct bottom-right cell position.
        test_cell_rect_returns_tuple_of_four()
            cell_rect() return is tuple[int, int, int, int].
        test_board_rect()
            board_rect() covers the full grid area.
        test_tile_sprites_has_11_entries()
            TILE_SPRITES maps all 11 tile values (2..2048).
        test_tile_sprites_filenames_match_disk()
            Every TILE_SPRITES filename exists in assets/tiles/ on disk.
        test_ui_sprite_names_has_8_entries()
            UI_SPRITE_NAMES contains all 8 UI element names.
        test_mascot_states_has_3_entries()
            MASCOT_STATES contains idle, happy, worried states.
        test_init_exports_boardlayout()
            BoardLayout is importable from src.render package.
        test_init_all_contains_four_names()
            src.render.__all__ has exactly 4 exports.
"""

from __future__ import annotations

import os

from src.render.layout import BoardLayout, MASCOT_STATES, TILE_SPRITES, UI_SPRITE_NAMES


# ---------------------------------------------------------------------------
# BoardLayout Computation Tests
# ---------------------------------------------------------------------------


def test_boardlayout_default_dimensions() -> None:
    """BoardLayout() uses default 700x800 window dimensions."""
    layout = BoardLayout()
    assert layout.window_width == 700
    assert layout.window_height == 800
    assert layout.GRID_SIZE == 4
    assert layout.board_margin_x == 25
    assert layout.board_margin_y == 25


def test_boardlayout_cell_size_is_positive_integer() -> None:
    """AC-1: cell_size is computed as a positive integer."""
    layout = BoardLayout()
    assert layout.cell_size == 162
    assert layout.cell_size > 0
    assert isinstance(layout.cell_size, int)


def test_boardlayout_computed_fields() -> None:
    """AC-1: All computed fields match expected values."""
    layout = BoardLayout()
    assert layout.cell_size == 162
    assert layout.board_width == 648
    assert layout.board_height == 648
    assert layout.grid_origin_x == 25
    assert layout.grid_origin_y == 138


def test_boardlayout_all_fields_are_integers() -> None:
    """Every field on the layout instance is an int (pygame pixel requirement)."""
    layout = BoardLayout()
    field_names = [
        "window_width",
        "window_height",
        "GRID_SIZE",
        "board_margin_x",
        "board_margin_y",
        "cell_size",
        "board_width",
        "board_height",
        "grid_origin_x",
        "grid_origin_y",
    ]
    for field_name in field_names:
        value = getattr(layout, field_name)
        assert isinstance(value, int), (
            f"{field_name} is {type(value).__name__}, expected int"
        )


# ---------------------------------------------------------------------------
# cell_rect / board_rect Tests
# ---------------------------------------------------------------------------


def test_cell_rect_origin() -> None:
    """AC-2: cell_rect(0, 0) returns a tuple at the grid origin."""
    layout = BoardLayout()
    rect = layout.cell_rect(0, 0)
    assert rect == (25, 138, 162, 162)
    assert rect[0] == layout.grid_origin_x
    assert rect[1] == layout.grid_origin_y


def test_cell_rect_bottom_right() -> None:
    """cell_rect(3, 3) returns the correct bottom-right cell position."""
    layout = BoardLayout()
    rect = layout.cell_rect(3, 3)
    expected_x = 25 + 3 * 162
    expected_y = 138 + 3 * 162
    assert rect[0] == expected_x
    assert rect[1] == expected_y
    assert rect[2] == 162
    assert rect[3] == 162


def test_cell_rect_returns_tuple_of_four() -> None:
    """cell_rect() return type is tuple[int, int, int, int]."""
    layout = BoardLayout()
    rect = layout.cell_rect(1, 2)
    assert isinstance(rect, tuple)
    assert len(rect) == 4
    for value in rect:
        assert isinstance(value, int)


def test_board_rect() -> None:
    """board_rect() covers the full grid area."""
    layout = BoardLayout()
    rect = layout.board_rect()
    assert rect == (25, 138, 648, 648)
    assert rect[0] == layout.grid_origin_x
    assert rect[1] == layout.grid_origin_y
    assert rect[2] == layout.board_width
    assert rect[3] == layout.board_height


# ---------------------------------------------------------------------------
# Sprite Mapping Tests
# ---------------------------------------------------------------------------


def test_tile_sprites_has_11_entries() -> None:
    """AC-3: TILE_SPRITES maps all 11 tile values (2..2048)."""
    assert len(TILE_SPRITES) == 11
    expected_keys = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]
    for key in expected_keys:
        assert key in TILE_SPRITES


def test_tile_sprites_filenames_match_disk() -> None:
    """AC-3: Every TILE_SPRITES filename matches a file in assets/tiles/."""
    for value, filename in TILE_SPRITES.items():
        assert filename.endswith(".png")
        filepath = os.path.join("assets", "tiles", filename)
        assert os.path.exists(filepath), f"Missing tile sprite: {filepath}"


def test_ui_sprite_names_has_8_entries() -> None:
    """AC-4: UI_SPRITE_NAMES contains all 8 UI element names."""
    assert len(UI_SPRITE_NAMES) == 8
    expected_names = [
        "board_background",
        "cell_empty",
        "score_card",
        "title_logo",
        "new_game_button",
        "game_over_overlay",
        "win_overlay",
        "background_wallpaper",
    ]
    for name in expected_names:
        assert name in UI_SPRITE_NAMES
        assert UI_SPRITE_NAMES[name].endswith(".png")


# ---------------------------------------------------------------------------
# Mascot States Test
# ---------------------------------------------------------------------------


def test_mascot_states_has_3_entries() -> None:
    """AC-5: MASCOT_STATES contains idle, happy, worried states."""
    assert len(MASCOT_STATES) == 3
    expected_states = ["idle", "happy", "worried"]
    for state in expected_states:
        assert state in MASCOT_STATES
        assert MASCOT_STATES[state].endswith(".png")


# ---------------------------------------------------------------------------
# Disk-File Validation Tests (TDD Red Phase)
# ---------------------------------------------------------------------------


def test_tile_sprites_filenames_exist_on_disk() -> None:
    """Every TILE_SPRITES value matches an actual file in assets/tiles/.

    Iterates over all 11 tile-value entries and asserts each filename
    exists at the expected path on disk. Uses os.path.join for
    cross-platform path construction.
    """
    for value, filename in TILE_SPRITES.items():
        filepath = os.path.join("assets", "tiles", filename)
        assert os.path.isfile(filepath), (
            f"TILE_SPRITES[{value}] = '{filename}' -> Missing file: {filepath}"
        )


def test_mascot_states_filenames_exist_on_disk() -> None:
    """Every MASCOT_STATES value matches an actual file in assets/mascot/.

    Iterates over all 3 mascot state entries and asserts each filename
    exists at the expected path on disk. Validates that the tile_XX_
    prefixed filenames in MASCOT_STATES match actual files on disk.
    """
    for state, filename in MASCOT_STATES.items():
        filepath = os.path.join("assets", "mascot", filename)
        assert os.path.isfile(filepath), (
            f"MASCOT_STATES['{state}'] = '{filename}' -> Missing file: {filepath}"
        )


def test_ui_sprite_names_filenames_exist_on_disk() -> None:
    """Every UI_SPRITE_NAMES value matches an actual file in assets/ui/.

    Iterates over all 8 UI element entries and asserts each filename
    exists at the expected path on disk. Validates that the tile_XX_
    prefixed filenames in UI_SPRITE_NAMES match actual files on disk.
    """
    for name, filename in UI_SPRITE_NAMES.items():
        filepath = os.path.join("assets", "ui", filename)
        assert os.path.isfile(filepath), (
            f"UI_SPRITE_NAMES['{name}'] = '{filename}' -> Missing file: {filepath}"
        )


def test_all_sprite_filenames_exist_on_disk() -> None:
    """Integration: every filename in all three sprite dicts is present on disk.

    Combines all three dictionaries into a single sweep and asserts that
    every referenced filename resolves to an existing file. Provides a
    single comprehensive check that catches any sprite-to-disk mismatch
    regardless of which dictionary it belongs to.
    """
    tile_dir = os.path.join("assets", "tiles")
    ui_dir = os.path.join("assets", "ui")
    mascot_dir = os.path.join("assets", "mascot")
    failures: list[str] = []

    for value, filename in TILE_SPRITES.items():
        filepath = os.path.join(tile_dir, filename)
        if not os.path.isfile(filepath):
            failures.append(f"TILE_SPRITES[{value}] = '{filename}' -> {filepath}")

    for name, filename in UI_SPRITE_NAMES.items():
        filepath = os.path.join(ui_dir, filename)
        if not os.path.isfile(filepath):
            failures.append(f"UI_SPRITE_NAMES['{name}'] = '{filename}' -> {filepath}")

    for state, filename in MASCOT_STATES.items():
        filepath = os.path.join(mascot_dir, filename)
        if not os.path.isfile(filepath):
            failures.append(f"MASCOT_STATES['{state}'] = '{filename}' -> {filepath}")

    assert failures == [], "Sprite filenames missing from disk:\n  " + "\n  ".join(
        failures
    )


# ---------------------------------------------------------------------------
# __init__.py Export Tests
# ---------------------------------------------------------------------------


def test_init_exports_boardlayout() -> None:
    """AC-6: BoardLayout is importable from the render package."""
    import src.render as render_mod

    assert hasattr(render_mod, "BoardLayout")
    layout = render_mod.BoardLayout()
    assert layout.cell_size == 162


def test_init_all_contains_three_names() -> None:
    """AC-6: src.render.__all__ has exactly 3 exports."""
    import src.render as render_mod

    assert hasattr(render_mod, "__all__")
    assert len(render_mod.__all__) == 3
    expected_names = ["AssetLoader", "BoardLayout", "Renderer"]
    for name in expected_names:
        assert name in render_mod.__all__
