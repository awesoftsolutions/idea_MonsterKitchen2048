"""src/render/animation.py — SpriteCache for deferred pygame smooth-scaling.

Provides a simple caching layer around ``pygame.transform.smoothscale()``.
Pygame is imported **inside** the :meth:`SpriteCache.smooth_scale` method body
so the module can be imported without triggering any pygame side-effects —
essential for headless test environments.

Public API:
    SpriteCache
        __init__(self) -> None
        smooth_scale(self, surface, size) -> object
        clear(self) -> None
"""

# CHANGELOG:
# - Sprint 4-2 remediation: New SpriteCache utility with deferred pygame import

from __future__ import annotations

from typing import Any


class SpriteCache:
    """Cache for pygame.transform.smoothscale results.

    Stores scaled surfaces keyed by ``(source_size, target_size)`` so repeated
    requests for the same source dimensions and target dimensions skip the
    expensive smoothscale operation.

    All pygame access is deferred into :meth:`smooth_scale` — the module
    contains zero module-level pygame imports.
    """

    def __init__(self) -> None:
        """Initialize an empty cache."""
        self._cache: dict[tuple[Any, tuple[int, int]], Any] = {}

    def smooth_scale(
        self,
        surface: Any,
        size: tuple[int, int],
    ) -> Any:
        """Scale *surface* to *size* using smoothscale, with caching.

        Args:
            surface: The source pygame.Surface (or compatible object) to scale.
            size: Target ``(width, height)`` tuple.

        Returns:
            The scaled surface.

        Raises:
            pygame.error: If smoothscale fails.
        """
        import pygame.transform  # noqa: PLC0415 — deferred: zero pygame at import time

        source_size = surface.get_size()
        cache_key = (source_size, size)

        if cache_key in self._cache:
            return self._cache[cache_key]

        scaled = pygame.transform.smoothscale(surface, size)
        self._cache[cache_key] = scaled
        return scaled

    def clear(self) -> None:
        """Empty the cache, releasing all stored surfaces."""
        self._cache.clear()