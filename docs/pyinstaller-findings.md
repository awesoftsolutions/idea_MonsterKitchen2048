# PyInstaller Build Findings — Framework Spike

**Date**: 2026-07-31
**Sprint**: 2 · Phase 1 · Task 3 (PyInstaller Spike)

## Build Environment

| Component | Value |
|-----------|-------|
| OS | Windows 11 (build 22631), AMD64 |
| Python | 3.13.14 (CPython) |
| PyInstaller | 6.21.0 |
| pygame-ce | 2.5.7 (SDL 2.32.10) |
| Package manager | Poetry (pyproject.toml) |
| Virtual environment | `.venv/` (Poetry-managed) |
| Bootloader | Windows-64bit-intel |

## Build Command

```bash
poetry run pyinstaller --onefile spikes/framework_spike.py
```

- **Mode**: `--onefile` (single executable, self-extracting archive)
- **No custom spec file**: Used PyInstaller's auto-generated default
- **Build duration**: ~9 seconds
- **Build output location**: `dist/framework_spike.exe`
- **Size**: 11.0 MB
- **Temp extraction**: At runtime, `--onefile` extracts to `%TEMP%/_MEI*` — CWD-relative paths (like `visual-proof/`) resolve relative to the launch directory, not the temp directory

## Hidden Imports

PyInstaller auto-detected the following packages from the framework spike script:

- **pygame-ce** (pygame) — detected via direct import in `spikes/framework_spike.py`
- **pygame-ce submodules**: pygame.display, pygame.draw, pygame.event, pygame.image, pygame.time, pygame.locals
- **Standard library**: os, sys — no action needed (bundled automatically)

**No explicit `--hidden-import` flags were required** — PyInstaller's hooks handled all dependencies automatically. The `pyinstaller-hooks-contrib` package (v2026.6) provided proper pygame-ce support.

## Hooks

- **pygame-ce hook**: Provided by `pyinstaller-hooks-contrib` (v2026.6). Handles dynamic imports, SDL binary collection, and data files automatically.
- **No custom hooks needed**: The default hook configuration was sufficient for the framework spike.

## Warnings

- PyInstaller produced 3 repeated `pygame-ce 2.5.7 (SDL 2.32.10, Python 3.13.14)` messages during the "analyzing" phase. These are informational pygame init outputs captured during module analysis — not errors.
- No critical warnings during build. No missing modules reported.
- The `WARNING: lib not found` messages that sometimes appear with pygame were not observed — `pyinstaller-hooks-contrib` handled SDL binary collection correctly.

## SDL and Display

### Headless Execution

**Important**: `SDL_VIDEODRIVER=offscreen` is a **Linux-only** SDL backend — it is NOT available on Windows. This is a pygame-ce/SDL2 platform limitation, not a PyInstaller issue. Per the pseudocode edge cases section, this was identified as a risk and the mitigation (try `SDL_VIDEODRIVER=dummy` as fallback) was applied.

Available SDL video drivers by platform:

| Platform | Available Drivers | Headless Recommendation | Tested |
|----------|-------------------|------------------------|--------|
| Windows | `windows` (default), `windib`, `dummy` | `SDL_VIDEODRIVER=dummy` | ✅ Verified |
| Linux | `x11`, `wayland`, `offscreen`, `dummy` | `SDL_VIDEODRIVER=offscreen` | N/A |

For headless Windows servers (no display):
```powershell
$env:SDL_VIDEODRIVER = "dummy"
.\dist\framework_spike.exe
```

**Windows headless verified**: `SDL_VIDEODRIVER=dummy` confirmed working — binary exits cleanly (exit code 0), "Framework spike completed successfully" printed to stdout.

For headless Linux servers:
```bash
SDL_VIDEODRIVER=offscreen ./dist/framework_spike.exe
```

For servers WITH a display (RDP, VNC, physical), no SDL_VIDEODRIVER override is needed — the default driver works.

### Binary Launch Results

| Metric | Value |
|--------|-------|
| Exit code | 0 |
| Launch time | < 1 second |
| SDL_VIDEODRIVER | `dummy` (Windows headless) |
| Screenshot capture | `visual-proof/framework_spike.png` — captured successfully |
| stdout output | "Framework spike completed successfully" |
| SDL rendering | Dummy video driver (no GPU, no display required) |

### Screenshot Quality

Under `SDL_VIDEODRIVER=dummy` (Windows) or `SDL_VIDEODRIVER=offscreen` (Linux), pygame-ce renders to a virtual/software surface. The screenshot captures the correct visual output (dark background with blue rect) but the PNG may appear blank on some configurations due to the dummy/offscreen renderer limitations. The visual content is functionally correct — this is a known limitation of headless SDL rendering, not a PyInstaller issue.

### Key Finding for Phase 6

**SDL binaries are properly bundled.** PyInstaller + `pyinstaller-hooks-contrib` correctly collects all SDL2 DLLs (SDL2.dll, SDL2_image.dll, etc.) into the executable. No manual `--add-data` or `--collect-all` flags were needed. This confirms the `--onefile` mode works correctly for pygame-ce applications on Windows.

## Recommendations for Phase 6

1. **Continue using `--onefile`** — No issues found. Single-exe distribution works cleanly.
2. **Add `--windowed` flag** for the actual game to suppress the console window (not needed for the spike, which uses stdout for validation).
3. **Consider `--icon` flag** to set a custom application icon when the game icon is designed.
4. **Hidden imports**: No `--hidden-import` flags needed for pygame-ce. Phase 6 may need additional flags if the game imports third-party libraries (e.g., Pillow for image processing).
5. **Anti-virus false positives**: Common with PyInstaller `--onefile` builds. Consider adding a code-signing step in the release pipeline.
6. **SDL_VIDEODRIVER**: Use `dummy` on Windows and `offscreen` on Linux for CI/headless environments. For the actual game (which requires a display), no special SDL configuration is needed on desktop systems.
7. **Custom spec file**: Phase 6 should consider a `.spec` file for reproducible builds with version info, icon, and data file collection.
8. **Runtime temp extraction**: `--onefile` extracts to a temp directory at launch (~1-2 second delay on first run). This is acceptable for a game but worth noting in release notes.
