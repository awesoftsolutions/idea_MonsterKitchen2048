# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Monster Kitchen 2048.

Bundles src/main.py (entry point: src.main:main) into a standalone
--onefile executable with all 24+ PNG assets from assets/.

Requirements addressed:
  - E-PKG01: hidden imports for try/except loaded modules and pygame-ce internals
  - E-PKG02: --add-data for assets/ subdirectories (tiles, ui, mascot)
  - E-PKG03: correct path separator (spec file handles this natively)
  - E-PKG04: entry point src.main:main resolved via pathex=["."]

Runtime hook (scripts/runtime_hook.py) sets CWD to sys._MEIPASS so
AssetLoader's default assets_dir="assets" resolves correctly in
--onefile extracted mode.

Cross-reference: ADR-033, ADR-035, registry://docs/phase-6-architecture.md
"""

import sys

block_cipher = None

# ---------------------------------------------------------------------------
# Data files — all 28 PNGs under assets/ bundled to assets/ in the archive
# Spec file tuples use (source, dest_in_archive) — no platform separator
# needed unlike --add-data CLI flags.
# ---------------------------------------------------------------------------
added_files = [
    ("assets", "assets"),
]

# ---------------------------------------------------------------------------
# Hidden imports — modules loaded dynamically or via try/except in src/main.py
# and AssetLoader.deferred imports from src/render/layout.py.
# PyInstaller cannot trace these at Analysis time.
# ---------------------------------------------------------------------------
hiddenimports = [
    "src.core.board",
    "src.core.game_session",
    "src.core.achievements",
    "src.core.history",
    "src.core.rules",
    "src.core.score",
    "src.core.twist",
    "src.main",
    "src.render.animation",
    "src.render.animation_manager",
    "src.render.asset_loader",
    "src.render.layout",
    "src.render.merge_celebration",
    "src.render.renderer",
    "src.render.toast_manager",
    "pygame",
]

# ---------------------------------------------------------------------------
# Analysis — entry point is src/main.py, packaged as module src.main:main
# ---------------------------------------------------------------------------
a = Analysis(
    ["src/main.py"],
    pathex=["."],
    binaries=[],
    datas=added_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["scripts/runtime_hook.py"],
    excludes=["pytest", "unittest", "xml", "pydoc", "doctest", "tkinter"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ---------------------------------------------------------------------------
# Executable — onefile mode, windowed (no console), named the2048
# ---------------------------------------------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="the2048",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)