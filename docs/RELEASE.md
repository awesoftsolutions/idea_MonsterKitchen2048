# Release Notes — Monster Kitchen 2048 v1.0.0

**Release Date:** 2026-08-04
**Version:** 1.0.0
**Author:** Favur (hello@favur.dev)
**Repository:** https://github.com/Favur/the2048

---

## Overview

Monster Kitchen 2048 is a standalone desktop 2048 puzzle game with a "Monster Kitchen" creative twist. Built with Python and pygame-ce featuring cute kawaii food-themed sprites, a custom Rotten Food contamination mechanic, 12+ achievements, and PyInstaller one-file packaging.

This release represents the complete delivery of all 6 project phases: Framework, Core Logic, Rendering, Visual Feedback, Visual Proof, and Packaging.

---

## What's Included

### Core Gameplay
- Classic 2048 slide-and-merge mechanics on a 4×4 grid
- 11 food tiers: evolve from Blueberry (2) to Chef's Masterpiece (2048)
- Rotten Food contamination: spawn every 3–5 moves, 3-turn countdown timer, contaminates one adjacent tile if not merged away
- Undo (Z key) and New Game (Space) support
- Score tracking with persistent high score

### Visual Content
- 24 custom Monster Kitchen pixel assets in kawaii/cartoon art style:
  - 13 tile sprites (blueberry, cupcake, pie, cake, mega-cake + rotten tiles)
  - 8 UI elements (board background, score card, overlays, buttons)
  - 3 Monster Chef mascot expressions (idle, happy, worried)
- Achievement toast notifications with overlay badges
- Game Over and Win overlay screens

### Achievements
- 12+ unlockable achievements triggered by gameplay milestones (first merge, reaching 16/64/1024 tiles, surviving contamination, using undo, and more)

### Technical
- PyInstaller one-file executable (`the2048.exe`, ~27.2 MB)
- Runtime hook for asset extraction from the packaged binary
- GitHub Actions CI: tests on Python 3.11, 3.12, 3.13 with headless SDL

---

## System Requirements

### Running from Source

| Requirement | Minimum Version |
|-------------|----------------|
| Operating System | Windows 10/11, macOS 12+, Ubuntu 20.04+ |
| Python | 3.11 or newer (tested 3.11, 3.12, 3.13) |
| SDL | 2.0+ (bundled with pygame-ce) |
| Display | 700 × 800 pixels minimum |
| Disk Space | ~50 MB (Python environment + assets) |

### Running the Standalone Binary (Windows)

| Requirement | Details |
|-------------|---------|
| Operating System | Windows 10 or newer (64-bit) |
| Disk Space | ~30 MB for the executable |
| Display | 700 × 800 pixels minimum |
| Python | **Not required** — the binary is self-contained |

---

## Installation

### Option A: Standalone Binary (Windows — No Python Required)

1. Download `the2048.exe` from the release assets
2. Double-click to launch — no installation needed

### Option B: Run from Source (All Platforms)

**Prerequisites:** Python 3.11+ and [Poetry](https://python-poetry.org/) installed.

```bash
# 1. Clone the repository
git clone https://github.com/Favur/the2048.git
cd the2048

# 2. Install all dependencies
poetry install

# 3. Launch the game
poetry run python -m src.main
```

### Controls

| Key | Action |
|-----|--------|
| Arrow Keys | Slide tiles (up, down, left, right) |
| Z | Undo last move |
| Space | Start a new game |
| Escape | Quit |
| Mouse Click | Press on-screen buttons |

---

## Building from Source

### Prerequisites

- Python 3.11+ with [Poetry](https://python-poetry.org/) installed
- PyInstaller 6.21.0+ (included as a dev dependency)

### Build Steps

```bash
# Install dependencies (if not already done)
poetry install

# Build the standalone executable
poetry run python scripts/build.py
```

The built executable appears in the `dist/` directory:
- `dist/the2048.exe` (Windows)

### Clean Rebuild

To force a full clean build (removes prior build artifacts):

```bash
poetry run python scripts/build.py --clean
```

### Build Configuration

The build uses `the2048.spec` (PyInstaller configuration):
- **Mode:** One-file (`--onefile`)
- **Entry point:** `src.main:main`
- **Assets:** All 24 Monster Kitchen sprites bundled via `--add-data`
- **Console:** Disabled (`console=False`) — GUI-only, no terminal window
- **Runtime hook:** `scripts/runtime_hook.py` — resolves asset paths after binary extraction
- **Hidden imports:** 15+ pygame-ce submodules explicitly listed

---

## Running Tests

```bash
# Run the full test suite
poetry run pytest tests/ -v --tb=short

# Run with coverage report
poetry run pytest tests/ -v --tb=short --cov=src --cov-report=term
```

### Test Environment (Headless SDL)

For running tests in environments without a display (CI, containers):

**Linux / macOS:**
```bash
SDL_VIDEODRIVER=offscreen SDL_AUDIODRIVER=dummy poetry run pytest
```

**Windows (PowerShell):**
```powershell
$env:SDL_VIDEODRIVER="offscreen"
$env:SDL_AUDIODRIVER="dummy"
poetry run pytest
```

---

## Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | ^3.11 | Runtime language |
| pygame-ce | ^2.5 | Game engine (community edition) |
| Poetry | Latest | Dependency management |
| pytest | ^9.1.1 | Test runner |
| pytest-cov | ^7.1.0 | Test coverage reporting |
| PyInstaller | ^6.21.0 | Standalone binary packaging |
| GitHub Actions | v1 | CI pipeline (Python 3.11, 3.12, 3.13) |

---

## Project Structure

```
├── src/                        # Game source code
│   ├── core/                   #   Pure Python game logic (7 modules, zero pygame)
│   │   ├── board.py            #     4×4 grid state, slide & merge
│   │   ├── rules.py            #     Game rules & valid-move detection
│   │   ├── score.py            #     Score tracking
│   │   ├── achievements.py     #     Achievement definitions & tracking
│   │   ├── game_session.py     #     Read-only session facade for renderer
│   │   ├── history.py          #     Undo state stack
│   │   └── twist.py            #     Rotten Food contamination logic
│   ├── render/                 #   Pygame rendering pipeline (4 modules)
│   │   ├── renderer.py         #     Central renderer (BoardRenderer)
│   │   ├── animation.py        #     Tile slide/merge animations
│   │   ├── animation_manager.py#     Animation orchestration
│   │   ├── asset_loader.py     #     PNG asset loading from assets/
│   │   ├── layout.py           #     Board layout & coordinate mapping
│   │   ├── merge_celebration.py#     Merge glow effects
│   │   └── toast_manager.py    #     Achievement toast popups
│   ├── main.py                 #   Entry point — starts the game
│   └── __main__.py             #   python -m src support
├── tests/                      # Test suite (422 tests, 91% coverage)
├── assets/                     # Game art: 24 Monster Kitchen assets
│   ├── tiles/                  #   13 tile sprites
│   ├── ui/                     #   8 UI elements
│   └── mascot/                 #   3 mascot expressions
├── scripts/                    # Build & utility scripts
│   ├── build.py                #   PyInstaller build wrapper
│   └── runtime_hook.py         #   Runtime hook for --onefile asset resolution
├── .github/workflows/          # CI pipeline
│   └── ci.yml                  #   GitHub Actions: pytest on Python 3.11–3.13
├── visual-proof/               # Visual verification screenshots
├── docs/                       # Project documentation and exit reports
├── the2048.spec                # PyInstaller configuration
└── pyproject.toml              # Project config & dependencies
```

---

## Known Limitations

- The standalone binary is currently Windows-only. macOS and Linux builds require building from source.
- SDL environment variables (`SDL_VIDEODRIVER`, `SDL_AUDIODRIVER`) are required for headless test execution.
- Score text positioning on overlay screens may overlap with character art in certain configurations (cosmetic issue).

---

## License

See [LICENSE](../LICENSE) file for details.

---

*Document version: 2026-08-04*