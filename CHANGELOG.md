# Changelog

All notable changes to **Monster Kitchen 2048** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-08-04

### 🍓 Phase 1 — Framework (Sprint 1–2)

#### Added
- Poetry project scaffold with Python ^3.11, pygame-ce ^2.5
- Core algorithm research spike: `spikes/slide_merge.py` with direction-based 4×4 sliding and merging
- "Monster Kitchen" creative twist design: Rotten Food contamination mechanic (ADR-001)
- PyInstaller packaging proof-of-concept for standalone binary builds
- Technical design: grid-agnostic merge algorithm, readable cell-string rendering, twist system architecture
- Initial test framework (pytest + pytest-cov) with 19 tests passing

#### Decisions
- 4×4 grid (operator override from SOW 5×5) — algorithm is grid-agnostic
- Generated image assets over programmatic tile rendering (operator-directed)
- "Monster Kitchen" food theme with Rotten Food contamination (operator-chosen from 4 alternatives)

---

### 🎮 Phase 2 — Core Logic (Sprint 3–4)

#### Added
- Complete core game engine in `src/core/` (12 modules, 179 tests):
  - `board.py` — 4×4 grid state, slide-and-merge mechanics
  - `rules.py` — game rules, valid-move detection, game-over and win conditions
  - `score.py` — score tracking with merge-bonus calculation
  - `history.py` — undo state stack for move reversal
  - `achievements.py` — 10+ achievement definitions and unlock tracking
  - `twist.py` — Rotten Food contamination logic (spawn, countdown, spread)
  - `game_session.py` — read-only session facade for renderer integration
- Comprehensive test suite: board mechanics, scoring, merge chains, contamination, achievements

#### Technical
- Pure Python core with zero pygame imports — fully testable without SDL
- Score multiplier system based on tile value
- Rotten Food tiles spawn every 3–5 moves with a 3-turn countdown timer

---

### 🎨 Phase 3 — Rendering (Sprint 5–8)

#### Added
- Pygame-ce rendering pipeline in `src/render/` (7 modules):
  - `asset_loader.py` — PNG sprite loading from `assets/` directory
  - `board_layout.py` — board coordinate mapping and cell sizing
  - `renderer.py` — central board renderer with HUD overlay
  - `animation.py` — tile slide and merge animation system
  - `animation_manager.py` — animation orchestration and timing
  - `merge_celebration.py` — merge glow and particle effects
  - `toast_manager.py` — achievement notification toasts
  - `game_window.py` — main game window and event loop
- 24 custom Monster Kitchen visual assets:
  - 11 food tile sprites (blueberry through 2048 chef's masterpiece)
  - 2 Rotten Food tile sprites (normal + warning state)
  - 8 UI elements (board background, score card, overlays)
  - 3 Monster Chef mascot expressions (idle, happy, worried)
- Asset manifest with full provenance tracking

#### Improved
- Test count grew from 179 to 288 tests through Phase 3

---

### ✨ Phase 4 — Visual Feedback (Sprint 9–12)

#### Added
- `AnimationManager` for coordinating tile slide, merge, and celebration animations
- `ToastManager` for in-game achievement popup notifications
- Merge celebration effects with glow and particle feedback
- Game-over and win overlay screens (friendly Monster Chef mascot)
- External achievement badge assets for UI display
- Integration of all visual feedback systems into the main game loop

#### Improved
- Test count grew from 288 to 422 tests — 91% code coverage
- Visual polish pass: consistent kawaii art style across all 24 assets

---

### 📋 Phase 5 — Visual Proof (Sprint 13)

#### Added
- Cross-referenced all 14 SOW acceptance criteria against 10 gameplay screenshots
- Corrected 7 false-positive AC-to-screenshot mappings
- Rewrote `visual-proof/README.md` with complete SOW AC coverage table
- Added 10 visual verification tests (21 total verification tests)

#### Fixed
- False-positive claims in visual proof manifest — all AC mappings now verified

---

### 📦 Phase 6 — Packaging & Release (Sprint 14–16)

#### Added
- GitHub Actions CI workflow (`.github/workflows/ci.yml`):
  - Tests on Python 3.11, 3.12, and 3.13
  - Headless SDL validation (`SDL_VIDEODRIVER=offscreen`, `SDL_AUDIODRIVER=dummy`)
  - CI badge in README
- PyInstaller standalone binary packaging:
  - Single-file executable (`the2048.exe`) — 27.2 MB
  - All 24 Monster Kitchen assets bundled via `--add-data`
  - Runtime hook for asset resolution after extraction
  - Console-less GUI mode (`console=False`)
  - 15+ hidden imports for pygame-ce submodules
- Comprehensive README rewrite with Technology Stack, Monster Kitchen Twist section, and accurate project structure
- Release documentation (this CHANGELOG, `docs/RELEASE.md`)

#### Fixed
- `the2048.spec` regression (HIGH-001): restored console=False, hidden imports, and runtime hook configuration

#### Technical
- Final verification: 422/422 tests passing, 91% code coverage
- Build verified on Windows (Python 3.13, PyInstaller 6.21.0)

---

## Release Metadata

| Property | Value |
|----------|-------|
| **Version** | 1.0.0 |
| **Release Date** | 2026-08-04 |
| **Python Version** | 3.11+ (tested 3.11, 3.12, 3.13) |
| **Runtime** | pygame-ce ^2.5 |
| **Test Count** | 422 tests, 91% coverage |
| **Binary Size** | ~27.2 MB (Windows one-file) |
| **License** | See LICENSE file |