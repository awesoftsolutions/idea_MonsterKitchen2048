"""Standalone build script for Monster Kitchen 2048 PyInstaller packaging.

Usage:
    python scripts/build.py          # Build onefile executable
    python scripts/build.py --clean  # Clean build + dist dirs before building
    python scripts/build.py --help   # Show help

Produces:
    dist/the2048.exe  (Windows)
    dist/the2048      (Linux/macOS)

Reference: Phase 6 Architecture - ADR-035, E-PKG02
"""

# CHANGELOG:
# - Sprint 2: Added as the PyInstaller build wrapper for Monster Kitchen 2048 standalone packaging.

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPEC_FILE = PROJECT_ROOT / "the2048.spec"
DIST_DIR = PROJECT_ROOT / "dist"


def main() -> None:
    """Parse CLI options, run PyInstaller build, verify output."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Build Monster Kitchen 2048 standalone executable"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove build/ and dist/ directories before building.",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Optional clean
    # ------------------------------------------------------------------
    if args.clean:
        for dir_name in ("build", "dist"):
            dir_path = PROJECT_ROOT / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path, ignore_errors=True)
                print(f"  Removed: {dir_path}")

    # ------------------------------------------------------------------
    # Validate spec file
    # ------------------------------------------------------------------
    if not SPEC_FILE.exists():
        raise SystemExit(f"Spec file not found: {SPEC_FILE}\n"
                         f"Run from project root: {PROJECT_ROOT}")

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    print(f"Building: {SPEC_FILE.name}")
    print(f"Python:   {sys.executable}")
    print()

    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(SPEC_FILE)],
        cwd=str(PROJECT_ROOT),
        check=False,
    )

    if result.returncode != 0:
        raise SystemExit(
            f"\nBuild FAILED (exit code {result.returncode}).\n"
            f"Check the output above for specific error messages."
        )

    # ------------------------------------------------------------------
    # Verify output
    # ------------------------------------------------------------------
    exe_name = "the2048.exe" if sys.platform == "win32" else "the2048"
    exe_path = DIST_DIR / exe_name

    if not exe_path.exists():
        raise SystemExit(
            f"\nBuild completed but expected executable not found:\n  {exe_path}\n"
            f"Check dist/ directory: {DIST_DIR}"
        )

    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print()
    print("Build successful!")
    print(f"  Executable : {exe_path}")
    print(f"  Size       : {size_mb:.1f} MB")


if __name__ == "__main__":
    main()