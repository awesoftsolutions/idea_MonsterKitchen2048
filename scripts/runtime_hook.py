"""
Runtime hook for PyInstaller --onefile mode.

Problem: In --onefile mode, PyInstaller extracts to sys._MEIPASS at runtime.
AssetLoader defaults to Path("assets") relative to CWD. By default, the
working directory is NOT sys._MEIPASS, so "assets" resolves to a nonexistent
path.

Solution: This hook changes the process working directory to sys._MEIPASS
*before* the main script runs, making all "assets" references work.

Reference: Phase 6 Architecture — E-PKG02, ADR-033
"""
from __future__ import annotations

import os
import sys

if getattr(sys, "_MEIPASS", None):
    os.chdir(sys._MEIPASS)