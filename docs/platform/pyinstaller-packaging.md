# PyInstaller Packaging Runbook

| Field     | Value                              |
|-----------|------------------------------------|
| Version   | 1.0                                |
| Date      | 2026-08-03                         |
| Status    | **VERIFIED**                       |
| Sprint    | Phase 6, Sprint 2, Task 4         |
| Author    | Favur (hello@favur.dev)            |

## Overview

This runbook documents the verified PyInstaller packaging configuration for the2048.
The game is built as a standalone `--onefile` executable that bundles the Python interpreter,
all dependencies (pygame-ce 2.5.7), and all 24 game assets (tiles, UI, mascot PNGs).

This configuration follows **ADR-033** from `docs/phase-6-architecture.md` — PyInstaller
is invoked via command-line arguments only, with no `.spec` file maintained in version control.

## Prerequisites

- Python 3.13.x with Poetry-managed virtual environment
- `pyinstaller` ^6.21.0 installed as a dev dependency (`poetry install`)
- `assets/` directory populated with all 24 PNG game assets
- Working directory: project root

## Build Command

### Windows (PowerShell)

```powershell
poetry run pyinstaller --onefile --name the2048 src/main.py --add-data "assets;assets"
```

### macOS / Linux (Bash)

```bash
poetry run pyinstaller --onefile --name the2048 src/main.py --add-data "assets:assets"
```

**Key difference**: The `--add-data` separator is `;` on Windows and `:` on macOS/Linux.
This is a PyInstaller convention inherited from `os.pathsep`.

### Command Breakdown

| Flag                  | Value            | Purpose                                          |
|-----------------------|------------------|--------------------------------------------------|
| `--onefile`           | —                | Bundle everything into a single executable       |
| `--name`              | `the2048`        | Output binary name (the2048.exe on Windows)      |
| Entry point           | `src/main.py`    | Python script containing `main()` function       |
| `--add-data`          | `assets;assets`  | Copy `assets/` tree into the bundle at `assets/` |

## Build Results

| Metric                | Value                    |
|-----------------------|--------------------------|
| Output path           | `dist/the2048.exe`       |
| Binary size           | 27.24 MB                 |
| Build exit code       | 0                        |
| Hidden imports needed | **None**                 |
| Runtime launch        | Clean — no import errors |
| Platform              | Windows 11, AMD64        |
| Python                | 3.13.14 (CPython)        |
| PyInstaller           | 6.21.0                   |
| pygame-ce             | 2.5.7                    |

## Hidden Import Strategy

PyInstaller does not always detect dynamically-imported modules. The iterative strategy:

1. Run the build command above
2. Attempt to launch the binary: `.\dist\the2048.exe`
3. If `ModuleNotFoundError: No module named 'X'` appears:
   ```powershell
   poetry run pyinstaller --onefile --name the2048 src/main.py --add-data "assets;assets" --hidden-import X
   ```
4. Repeat until the binary launches cleanly
5. If stuck after 5 iterations, use the catch-all: `--collect-all pygame`

### Current Status

**No hidden imports were needed** for this project. pygame-ce 2.5.7 bundled cleanly with
PyInstaller's automatic analysis. All 13 direct and try/except imports were detected:

- `pygame` (direct)
- `src.core.board`, `src.core.game_session` (direct)
- `src.render.asset_loader`, `src.render.layout`, `src.render.renderer` (direct)
- `src.render.animation_manager`, `src.render.toast_manager`, `src.render.merge_celebration` (try/except)

If hidden imports are needed in the future (e.g., after pygame-ce version bumps), add
`--hidden-import <module_name>` flags to the build command and re-verify.

## Asset Bundling

All 24 game assets are bundled via `--add-data "assets;assets"`:

| Directory       | Count | Contents                                    |
|-----------------|-------|---------------------------------------------|
| `assets/tiles/` | 13    | Tile sprites (blueberry through 2048, rotten) |
| `assets/ui/`    | 8     | Board background, cell, score, title, buttons, overlays, wallpaper |
| `assets/mascot/`| 3     | Monster chef idle, happy, worried            |

PyInstaller copies the entire `assets/` directory into the bundle. At runtime, the binary
extracts to a temp directory and assets are accessible via the `assets/` relative path.
The code uses `sys._MEIPASS` detection (via PyInstaller's runtime hook) to locate assets
whether running from source or from the bundled binary.

## Regression Gate

All 422 pytest tests pass with the packaging configuration in place:

```
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
collected 422 items

422 passed in 0.70s
```

| Metric          | Result  |
|-----------------|---------|
| Tests collected | 422     |
| Passed          | 422     |
| Failed          | 0       |
| Errors          | 0       |
| Exit code       | 0       |

## Build Artifacts

| Artifact          | Path                | Git Status  |
|-------------------|---------------------|-------------|
| Binary            | `dist/the2048.exe`  | Excluded (.gitignore) |
| Build directory   | `build/the2048/`    | Excluded (.gitignore) |
| Spec file         | `the2048.spec`      | Excluded (.gitignore) |

All build artifacts are transient and gitignored. After verifying the binary works,
the `build/` directory and `.spec` file can be safely deleted:

```powershell
Remove-Item -Recurse -Force build, the2048.spec
```

Keep `dist/the2048.exe` for distribution.

## Troubleshooting

### E-PKG01: Missing Hidden Import

**Symptom**: `ModuleNotFoundError: No module named 'X'` when launching the binary.

**Fix**: Add `--hidden-import X` to the build command and rebuild.

### E-PKG02: Asset Not Found at Runtime

**Symptom**: `FileNotFoundError` or missing sprites when running the binary.

**Fix**: Verify `--add-data "assets;assets"` is included. Check that the path separator
matches your OS (`;` for Windows, `:` for macOS/Linux).

### E-PKG03: Wrong Path Separator

**Symptom**: Build succeeds but assets are missing at runtime.

**Fix**: You likely used the wrong OS separator. Windows uses `;`, macOS/Linux uses `:`.

### E-PKG04: Entry Point Failure

**Symptom**: Binary launches but exits immediately or crashes.

**Fix**: Verify `src/main.py` has a `main()` function and that it is called under
`if __name__ == "__main__":`.

## Checklist

- [x] PyInstaller build exits with code 0
- [x] `dist/the2048.exe` exists and is >1 MB (27.24 MB)
- [x] Binary launches without `ModuleNotFoundError`
- [x] No hidden imports needed (pygame-ce 2.5.7 bundles cleanly)
- [x] All 24 assets bundled via `--add-data`
- [x] Platform-specific `--add-data` separator documented (`;` Windows, `:` macOS/Linux)
- [x] pytest regression gate passes (422/422)
- [x] Build artifacts (build/, *.spec) are gitignored
- [x] ADR-033 compliance: command-line args only, no .spec file in version control
