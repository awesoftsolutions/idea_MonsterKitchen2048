"""Test suite for Phase 4 components — import and structure verification.

Purpose:
    Minimal verification tests confirming that Phase 4 render-layer components
    (AnimationManager, ToastManager, MergeCelebrationEffect, Renderer) exist,
    are importable, expose expected methods and dataclass fields, and that
    module-level constants have the correct values. Also verifies that
    src/main.py creates the pygame window without the NOFRAME flag.

    This is NOT a behavioral test suite — it validates component existence
    and structure only. Behavioral tests live in dedicated per-component
    test files (test_animation_manager.py, test_toast_manager.py, etc.).

System:
    Headless pytest suite. No pygame.init() or display required — all
    tests exercise imports, hasattr checks, constant values, and source
    code text inspection. Each class groups tests for a single component.

Dependencies:
    pytest — third-party. All src.render.* modules — production code.
    pathlib — stdlib (for src/main.py text inspection).

Used-by:
    CI pipeline (pytest), Sprint 4 Task 1 acceptance verification.

Public API:
    Test classes (6):
        TestAnimationManagerExists     (4 tests) — AnimationManager import + methods
        TestToastManagerExists         (3 tests) — ToastManager import + methods
        TestMergeCelebrationExists     (2 tests) — MergeCelebrationEffect dataclass
        TestConstants                  (3 tests) — ANIMATION_DURATION_MS, DEFAULT_DURATION_MS, FADE_DURATION_MS
        TestRendererExists             (2 tests) — Renderer import + method
        TestWindowChrome               (1 test)  — NOFRAME absence in main.py
"""

from __future__ import annotations

from pathlib import Path


# ---------------------------------------------------------------------------
# TestAnimationManagerExists
# ---------------------------------------------------------------------------


class TestAnimationManagerExists:
    """Verify AnimationManager is importable and exposes expected methods."""

    def test_import(self) -> None:
        """AnimationManager is importable from src.render.animation_manager."""
        from src.render.animation_manager import AnimationManager  # noqa: F401

    def test_has_start_animation(self) -> None:
        """AnimationManager exposes start_animation as a callable method."""
        from src.render.animation_manager import AnimationManager

        assert hasattr(AnimationManager, "start_animation"), (
            "AnimationManager missing start_animation method"
        )
        assert callable(AnimationManager.start_animation), (
            "AnimationManager.start_animation is not callable"
        )

    def test_has_get_pixel_offset(self) -> None:
        """AnimationManager exposes get_pixel_offset as a callable method."""
        from src.render.animation_manager import AnimationManager

        assert hasattr(AnimationManager, "get_pixel_offset"), (
            "AnimationManager missing get_pixel_offset method"
        )
        assert callable(AnimationManager.get_pixel_offset), (
            "AnimationManager.get_pixel_offset is not callable"
        )

    def test_has_is_animating(self) -> None:
        """AnimationManager exposes is_animating as a callable method."""
        from src.render.animation_manager import AnimationManager

        assert hasattr(AnimationManager, "is_animating"), (
            "AnimationManager missing is_animating method"
        )
        assert callable(AnimationManager.is_animating), (
            "AnimationManager.is_animating is not callable"
        )


# ---------------------------------------------------------------------------
# TestToastManagerExists
# ---------------------------------------------------------------------------


class TestToastManagerExists:
    """Verify ToastManager is importable and exposes expected methods."""

    def test_import(self) -> None:
        """ToastManager is importable from src.render.toast_manager."""
        from src.render.toast_manager import ToastManager  # noqa: F401

    def test_has_show(self) -> None:
        """ToastManager exposes show as a callable method."""
        from src.render.toast_manager import ToastManager

        assert hasattr(ToastManager, "show"), (
            "ToastManager missing show method"
        )
        assert callable(ToastManager.show), (
            "ToastManager.show is not callable"
        )

    def test_has_render(self) -> None:
        """ToastManager exposes render as a callable method."""
        from src.render.toast_manager import ToastManager

        assert hasattr(ToastManager, "render"), (
            "ToastManager missing render method"
        )
        assert callable(ToastManager.render), (
            "ToastManager.render is not callable"
        )


# ---------------------------------------------------------------------------
# TestMergeCelebrationExists
# ---------------------------------------------------------------------------


class TestMergeCelebrationExists:
    """Verify MergeCelebrationEffect is a dataclass and create_effect exists."""

    def test_import(self) -> None:
        """MergeCelebrationEffect and create_effect are importable."""
        from src.render.merge_celebration import (  # noqa: F401
            MergeCelebrationEffect,
            create_effect,
        )

    def test_is_dataclass(self) -> None:
        """MergeCelebrationEffect is a dataclass (has __dataclass_fields__)."""
        from src.render.merge_celebration import MergeCelebrationEffect

        assert hasattr(MergeCelebrationEffect, "__dataclass_fields__"), (
            "MergeCelebrationEffect is not a dataclass — "
            "missing __dataclass_fields__ attribute"
        )


# ---------------------------------------------------------------------------
# TestConstants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify render-layer constants have expected values."""

    def test_animation_duration(self) -> None:
        """ANIMATION_DURATION_MS equals 250 (ms)."""
        from src.render.layout import ANIMATION_DURATION_MS

        assert ANIMATION_DURATION_MS == 250, (
            f"Expected ANIMATION_DURATION_MS == 250, got {ANIMATION_DURATION_MS}"
        )

    def test_toast_default_duration(self) -> None:
        """DEFAULT_DURATION_MS equals 2500 (ms)."""
        from src.render.toast_manager import DEFAULT_DURATION_MS

        assert DEFAULT_DURATION_MS == 2500, (
            f"Expected DEFAULT_DURATION_MS == 2500, got {DEFAULT_DURATION_MS}"
        )

    def test_toast_fade_duration(self) -> None:
        """FADE_DURATION_MS equals 500 (ms)."""
        from src.render.toast_manager import FADE_DURATION_MS

        assert FADE_DURATION_MS == 500, (
            f"Expected FADE_DURATION_MS == 500, got {FADE_DURATION_MS}"
        )


# ---------------------------------------------------------------------------
# TestRendererExists
# ---------------------------------------------------------------------------


class TestRendererExists:
    """Verify Renderer is importable and exposes get_new_game_button_rect."""

    def test_import(self) -> None:
        """Renderer is importable from src.render.renderer."""
        from src.render.renderer import Renderer  # noqa: F401

    def test_has_get_new_game_button_rect(self) -> None:
        """Renderer exposes get_new_game_button_rect as a callable method."""
        from src.render.renderer import Renderer

        assert hasattr(Renderer, "get_new_game_button_rect"), (
            "Renderer missing get_new_game_button_rect method"
        )
        assert callable(Renderer.get_new_game_button_rect), (
            "Renderer.get_new_game_button_rect is not callable"
        )


# ---------------------------------------------------------------------------
# TestWindowChrome
# ---------------------------------------------------------------------------


class TestWindowChrome:
    """Verify src/main.py window creation does not use NOFRAME flag."""

    def test_no_noframe_in_main(self) -> None:
        """pygame.display.set_mode() call in src/main.py does NOT include NOFRAME.

        Reads src/main.py and finds every line containing
        ``pygame.display.set_mode``. Asserts that none contain ``NOFRAME``.
        The changelog comment at line 71 mentioning NOFRAME is excluded
        because it does not contain ``set_mode``.
        """
        src_main = Path(__file__).resolve().parent.parent / "src" / "main.py"
        source = src_main.read_text(encoding="utf-8")

        set_mode_lines = [
            line
            for line in source.splitlines()
            if "pygame.display.set_mode" in line
        ]

        assert set_mode_lines, (
            "Could not find a pygame.display.set_mode() call in src/main.py"
        )

        for line in set_mode_lines:
            assert "NOFRAME" not in line, (
                f"pygame.display.set_mode call contains NOFRAME: {line.strip()!r}"
            )