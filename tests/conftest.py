"""Pytest conftest for the the2048 project.

Adds the project root to sys.path at index 0 so that imports like
``from src.core.rules import Direction, slide_merge`` resolve correctly
despite ``package-mode = false`` in pyproject.toml.
"""

from __future__ import annotations

import os
import sys

# Insert project root (parent of tests/) at the front of sys.path.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
