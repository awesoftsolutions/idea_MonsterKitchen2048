"""Tests for AssetLoader — headless mock-based test suite.

Uses unittest.mock to patch pygame.image.load and pygame.transform.smoothscale.
No real pygame display context is needed. Layout dictionaries are mocked via
monkeypatch since src/render/layout.py (Task 2) does not exist yet.

TDD Red Phase: All tests are expected to FAIL with ImportError because
src/render/asset_loader.py does not exist yet. This is correct behavior —
Step 3 of the implementation workflow creates the production code.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Inline test dictionaries — mirror the exact shapes from layout.py (Task 2).
# Defined here because layout.py does not exist yet.
# ---------------------------------------------------------------------------

TILE_SPRITES_TEST: dict[int, str] = {
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

UI_SPRITE_NAMES_TEST: dict[str, str] = {
    "board_background": "tile_14_board_background.png",
    "cell_empty": "tile_15_cell_empty.png",
    "score_card": "tile_16_score_card.png",
    "title_logo": "tile_17_title_logo.png",
    "new_game_button": "tile_18_new_game_button.png",
    "game_over_overlay": "tile_19_game_over_overlay.png",
    "win_overlay": "tile_20_win_overlay.png",
    "background_wallpaper": "tile_21_background_wallpaper.png",
}

MASCOT_STATES_TEST: dict[str, str] = {
    "idle": "tile_22_mascot_idle.png",
    "happy": "tile_23_mascot_happy.png",
    "worried": "tile_24_mascot_worried.png",
}

# Total expected asset count: 11 tiles + 2 special + 8 UI + 3 mascot = 24
EXPECTED_ASSET_COUNT = (
    len(TILE_SPRITES_TEST)
    + len(UI_SPRITE_NAMES_TEST)
    + len(MASCOT_STATES_TEST)
    + 2  # special sprites (rotten_normal, rotten_warning)
)

# Minimal PNG header bytes for dummy asset files.
_DUMMY_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


# ---------------------------------------------------------------------------
# Helper: deferred import of AssetLoader.
# ---------------------------------------------------------------------------


def _get_asset_loader_class() -> type:
    """Import and return the AssetLoader class (deferred)."""
    from src.render.asset_loader import AssetLoader  # noqa: F811

    return AssetLoader


def _get_special_sprites() -> dict[str, str]:
    """Import and return the SPECIAL_SPRITES constant (deferred)."""
    from src.render.asset_loader import SPECIAL_SPRITES  # noqa: F811

    return SPECIAL_SPRITES


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_asset_dir(tmp_path: Path) -> Path:
    """Create a temporary assets directory with all 24 placeholder PNG files."""
    assets = tmp_path / "assets"

    # Tile sprites directory (11 regular + 2 special = 13 files)
    tiles_dir = assets / "tiles"
    tiles_dir.mkdir(parents=True)
    for filename in TILE_SPRITES_TEST.values():
        (tiles_dir / filename).write_bytes(_DUMMY_PNG_BYTES)
    for filename in ("tile_12_rotten_food.png", "tile_13_rotten_warning.png"):
        (tiles_dir / filename).write_bytes(_DUMMY_PNG_BYTES)

    # UI sprites directory (8 files)
    ui_dir = assets / "ui"
    ui_dir.mkdir(parents=True)
    for filename in UI_SPRITE_NAMES_TEST.values():
        (ui_dir / filename).write_bytes(_DUMMY_PNG_BYTES)

    # Mascot sprites directory (3 files)
    mascot_dir = assets / "mascot"
    mascot_dir.mkdir(parents=True)
    for filename in MASCOT_STATES_TEST.values():
        (mascot_dir / filename).write_bytes(_DUMMY_PNG_BYTES)

    return assets


@pytest.fixture(autouse=True)
def _patch_layout_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """Inject a mock src.render.layout module into sys.modules.

    Since layout.py (Task 2) does not exist yet, we provide the three
    dictionaries AssetLoader expects as module-level attributes on a mock.
    Also cleans up pygame from sys.modules at teardown so that tests
    like test_all_modules_importable_without_pygame are not polluted.
    """
    mock_layout = MagicMock()
    mock_layout.TILE_SPRITES = dict(TILE_SPRITES_TEST)
    mock_layout.UI_SPRITE_NAMES = dict(UI_SPRITE_NAMES_TEST)
    mock_layout.MASCOT_STATES = dict(MASCOT_STATES_TEST)
    monkeypatch.setitem(sys.modules, "src.render.layout", mock_layout)

    # Capture any pre-existing pygame keys so we only remove what this test added.
    pygame_keys_before = {k for k in sys.modules if "pygame" in k.lower()}

    yield

    # Clean up pygame entries added by unittest.mock.patch (which imports
    # the real pygame module as a side effect of patching "pygame.image.load", etc.)
    for key in list(sys.modules):
        if "pygame" in key.lower() and key not in pygame_keys_before:
            del sys.modules[key]


def _make_mock_surface() -> MagicMock:
    """Create a mock pygame.Surface with spec-like attributes."""
    surface = MagicMock(name="MockSurface")
    surface.get_width.return_value = 64
    surface.get_height.return_value = 64
    return surface


# ---------------------------------------------------------------------------
# Helper: create and load an AssetLoader with mocked pygame.
# ---------------------------------------------------------------------------


def _create_and_load(
    assets_dir: Path,
    cell_size: int = 100,
    surface_factory=None,
):
    """Create an AssetLoader, patch pygame, and call load_all().

    Args:
        assets_dir: Path to the temporary assets directory.
        cell_size: Pixel size for scaling tile sprites.
        surface_factory: Optional callable returning a mock surface.
            Defaults to _make_mock_surface.

    Returns:
        Tuple of (loader, mock_load_calls) for assertion flexibility.
    """
    if surface_factory is None:
        surface_factory = _make_mock_surface

    AssetLoader = _get_asset_loader_class()
    loader = AssetLoader(assets_dir=assets_dir)

    mock_load = MagicMock(return_value=surface_factory())
    mock_scale = MagicMock(return_value=surface_factory())

    with (
        patch("pygame.image.load", mock_load),
        patch("pygame.transform.smoothscale", mock_scale),
    ):
        loader.load_all(cell_size=cell_size)

    return loader, mock_load


# ===========================================================================
# Test Case 1: load_all() succeeds with valid directory — AC-1
# ===========================================================================


def test_load_all_success_with_valid_directory(mock_asset_dir: Path) -> None:
    """load_all() loads all 24 assets when given a valid assets directory."""
    AssetLoader = _get_asset_loader_class()
    loader = AssetLoader(assets_dir=mock_asset_dir)

    mock_surface = _make_mock_surface()
    mock_load = MagicMock(return_value=mock_surface)
    mock_scale = MagicMock(return_value=mock_surface)

    with (
        patch("pygame.image.load", mock_load),
        patch("pygame.transform.smoothscale", mock_scale),
    ):
        loader.load_all(cell_size=100)

    assert len(loader._cache) == EXPECTED_ASSET_COUNT, (
        f"Expected {EXPECTED_ASSET_COUNT} cached assets, got {len(loader._cache)}"
    )

    # Verify all cache keys follow expected prefix patterns.
    expected_prefixes = ("tile_", "ui_", "mascot_", "special_")
    for key in loader._cache:
        assert key.startswith(expected_prefixes), (
            f"Cache key '{key}' does not start with any expected prefix {expected_prefixes}"
        )


# ===========================================================================
# Test Case 2: load_all() raises FileNotFoundError for missing dir — AC-2
# ===========================================================================


def test_load_all_raises_file_not_found_for_missing_directory() -> None:
    """load_all() raises FileNotFoundError when assets directory does not exist (E-AL01)."""
    AssetLoader = _get_asset_loader_class()
    loader = AssetLoader(assets_dir="/nonexistent/path/to/assets")

    with pytest.raises(FileNotFoundError) as exc_info:
        loader.load_all(cell_size=100)

    assert (
        "nonexistent" in str(exc_info.value).lower()
        or "not found" in str(exc_info.value).lower()
    ), f"Expected path or 'not found' in error message, got: {exc_info.value}"


# ===========================================================================
# Test Case 3: load_all() raises pygame.error for corrupt PNG — E-AL02
# ===========================================================================


def test_load_all_raises_pygame_error_for_corrupt_png(mock_asset_dir: Path) -> None:
    """A corrupt PNG raises pygame.error during load_all() (E-AL02)."""
    # Import pygame.error as a real exception type so pytest.raises can catch it.
    import pygame

    AssetLoader = _get_asset_loader_class()
    loader = AssetLoader(assets_dir=mock_asset_dir)

    mock_load = MagicMock(side_effect=pygame.error("Cannot load image: corrupt"))
    mock_scale = MagicMock()

    with (
        patch("pygame.image.load", mock_load),
        patch("pygame.transform.smoothscale", mock_scale),
    ):
        with pytest.raises(pygame.error, match="corrupt"):
            loader.load_all(cell_size=100)


# ===========================================================================
# Test Case 4: get_tile_sprite(2) returns Surface after load_all — AC-3
# ===========================================================================


def test_get_tile_sprite_returns_surface_after_load_all(mock_asset_dir: Path) -> None:
    """get_tile_sprite(2) returns a Surface object for the blueberry tile."""
    loader, _ = _create_and_load(mock_asset_dir, cell_size=100)

    surface = loader.get_tile_sprite(2)

    assert surface is not None, "get_tile_sprite(2) returned None"


# ===========================================================================
# Test Case 5: get_tile_sprite(999) raises KeyError — AC-4
# ===========================================================================


def test_get_tile_sprite_raises_keyerror_for_unknown_value(
    mock_asset_dir: Path,
) -> None:
    """get_tile_sprite(999) raises KeyError for an unknown tile value (E-AL03)."""
    loader, _ = _create_and_load(mock_asset_dir, cell_size=100)

    with pytest.raises(KeyError) as exc_info:
        loader.get_tile_sprite(999)

    assert str(999) in str(exc_info.value) or "999" in str(exc_info.value), (
        f"Expected '999' in KeyError message, got: {exc_info.value}"
    )


# ===========================================================================
# Test Case 6: get_ui_sprite("score_card") returns Surface — AC-5
# ===========================================================================


def test_get_ui_sprite_returns_surface_after_load_all(mock_asset_dir: Path) -> None:
    """get_ui_sprite("score_card") returns a Surface."""
    loader, _ = _create_and_load(mock_asset_dir, cell_size=100)

    surface = loader.get_ui_sprite("score_card")

    assert surface is not None, "get_ui_sprite('score_card') returned None"


# ===========================================================================
# Test Case 7: get_ui_sprite("nonexistent") raises KeyError — E-AL04
# ===========================================================================


def test_get_ui_sprite_raises_keyerror_for_unknown_name(
    mock_asset_dir: Path,
) -> None:
    """get_ui_sprite("nonexistent") raises KeyError."""
    loader, _ = _create_and_load(mock_asset_dir, cell_size=100)

    with pytest.raises(KeyError) as exc_info:
        loader.get_ui_sprite("nonexistent")

    assert "nonexistent" in str(exc_info.value), (
        f"Expected 'nonexistent' in KeyError message, got: {exc_info.value}"
    )


# ===========================================================================
# Test Case 8: get_mascot_sprite("happy") returns Surface — AC-6
# ===========================================================================


def test_get_mascot_sprite_returns_surface_after_load_all(
    mock_asset_dir: Path,
) -> None:
    """get_mascot_sprite("happy") returns a Surface."""
    loader, _ = _create_and_load(mock_asset_dir, cell_size=100)

    surface = loader.get_mascot_sprite("happy")

    assert surface is not None, "get_mascot_sprite('happy') returned None"


# ===========================================================================
# Test Case 9: get_mascot_sprite("unknown_state") raises KeyError
# ===========================================================================


def test_get_mascot_sprite_raises_keyerror_for_unknown_state(
    mock_asset_dir: Path,
) -> None:
    """get_mascot_sprite("unknown_state") raises KeyError."""
    loader, _ = _create_and_load(mock_asset_dir, cell_size=100)

    with pytest.raises(KeyError) as exc_info:
        loader.get_mascot_sprite("unknown_state")

    assert "unknown_state" in str(exc_info.value), (
        f"Expected 'unknown_state' in KeyError message, got: {exc_info.value}"
    )


# ===========================================================================
# Test Case 10: get_tile_sprite(2) cache identity — AC-7
# ===========================================================================


def test_get_tile_sprite_cache_identity_returns_same_object(
    mock_asset_dir: Path,
) -> None:
    """Repeated get_tile_sprite(2) calls return the same Python object."""
    loader, _ = _create_and_load(mock_asset_dir, cell_size=100)

    first = loader.get_tile_sprite(2)
    second = loader.get_tile_sprite(2)

    assert first is second, (
        "get_tile_sprite(2) returned different objects on repeated calls — "
        "expected cache identity (is) to hold"
    )


# ===========================================================================
# Test Case 11: get_special_sprite("rotten_normal") returns Surface
# ===========================================================================


def test_get_special_sprite_rotten_normal(mock_asset_dir: Path) -> None:
    """get_special_sprite("rotten_normal") returns a Surface."""
    loader, _ = _create_and_load(mock_asset_dir, cell_size=100)

    surface = loader.get_special_sprite("rotten_normal")

    assert surface is not None, "get_special_sprite('rotten_normal') returned None"


# ===========================================================================
# Test Case 12: get_special_sprite("nonexistent") raises KeyError
# ===========================================================================


def test_get_special_sprite_raises_keyerror_for_unknown(
    mock_asset_dir: Path,
) -> None:
    """get_special_sprite("nonexistent") raises KeyError."""
    loader, _ = _create_and_load(mock_asset_dir, cell_size=100)

    with pytest.raises(KeyError) as exc_info:
        loader.get_special_sprite("nonexistent")

    assert "nonexistent" in str(exc_info.value), (
        f"Expected 'nonexistent' in KeyError message, got: {exc_info.value}"
    )


# ===========================================================================
# Test Case 13: load_all() leaves cache empty on failure
# ===========================================================================


def test_load_all_initializes_empty_cache_on_failure(mock_asset_dir: Path) -> None:
    """If load_all() fails partway through (corrupt PNG on 5th file),
    the cache remains in its pre-call state (empty dict).

    The implementation should use a fresh local dict during loading and only
    assign self._cache = local_dict after the full loop completes. If an
    exception occurs during the loop, the local dict is discarded.
    """
    import pygame

    AssetLoader = _get_asset_loader_class()
    loader = AssetLoader(assets_dir=mock_asset_dir)

    call_count = 0

    def _load_and_fail_on_fifth(path: str) -> MagicMock:
        nonlocal call_count
        call_count += 1
        if call_count >= 5:
            raise pygame.error(f"Corrupt PNG at load #{call_count}")
        return _make_mock_surface()

    mock_load = MagicMock(side_effect=_load_and_fail_on_fifth)
    mock_scale = MagicMock(return_value=_make_mock_surface())

    with (
        patch("pygame.image.load", mock_load),
        patch("pygame.transform.smoothscale", mock_scale),
    ):
        with pytest.raises(pygame.error):
            loader.load_all(cell_size=100)

    # Cache must be empty — the implementation should not leave partial state.
    assert len(loader._cache) == 0, (
        f"Expected empty cache after failed load_all(), got {len(loader._cache)} entries"
    )


# ===========================================================================
# Test Case 14: SPECIAL_SPRITES uses correct disk filenames
# ===========================================================================


def test_special_sprites_use_correct_filenames() -> None:
    """SPECIAL_SPRITES references the actual disk filenames (Scout C31 fix)."""
    special = _get_special_sprites()

    assert special["rotten_normal"] == "tile_12_rotten_food.png", (
        f"Expected 'tile_12_rotten_food.png', got '{special['rotten_normal']}'"
    )
    assert special["rotten_warning"] == "tile_13_rotten_warning.png", (
        f"Expected 'tile_13_rotten_warning.png', got '{special['rotten_warning']}'"
    )
