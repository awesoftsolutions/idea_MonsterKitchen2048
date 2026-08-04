# the2048 — Monster Kitchen 2048

[![CI](https://github.com/Favur/the2048/actions/workflows/ci.yml/badge.svg)](https://github.com/Favur/the2048/actions/workflows/ci.yml)

A fun **2048 puzzle game** with a cute food-and-monster twist! Slide tiles on a 4×4 board, merge matching food items into bigger recipes, and try to reach the legendary **2048 cake** — but watch out for Rotten Food that tries to spoil your kitchen!

Built with [pygame-ce](https://pyga.me/) and Python. Designed to be fun for kids and parents alike.

## Monster Kitchen Twist

Monster Kitchen replaces the abstract number tiles of classic 2048 with a **colorful kitchen/food world**. Every tile is a cute, cartoon food item crafted by little monster chefs. Players evolve a tiny **blueberry** (value 2) up through **cupcake → pie → cake → mega-cake**, reaching the legendary **2048 chef's masterpiece**. The board is a cheerful kitchen countertop and the merge animations are themed around "cooking up" bigger recipes.

The core 2048 mechanics (4×4 grid, directional sliding, merging identical tiles) are **completely preserved** — no board-size changes, no new input gestures, no unfamiliar rules for players already comfortable with sliding tile puzzles.

### Rotten Food Contamination

Every 3–5 moves, a **Rotten Food tile** spawns at a random empty cell. It carries a visible **3-turn countdown timer** (rendered as a ring that ticks down each move). When the countdown reaches zero, the tile **contaminates** one orthogonally adjacent tile, converting it into a new Rotten Food tile with its own 3-turn timer. If no empty neighbour exists, contamination is suppressed for that turn (but the tile stays on the board).

The mechanic forces **defensive play**: players cannot simply chase high-score merges; they must either merge Rotten tiles away (consuming them from the board) or manage the board to prevent uncontrollable spread. This is the twist's key tension — the same "keep your kitchen clean" metaphor that fits the food theme.

### Why food instead of numbers?

- **Immediate visual recognition** — an 8-year-old instantly identifies a blueberry; "512" is abstract
- **Story through merging** — the chain blueberry → cupcake → pie → cake → mega-cake is a coherent narrative progression, unlike 2→4→8→16
- **Natural contamination metaphor** — "rotten food spoils the kitchen" is immediately understandable to children; a "corrupted number" requires explanation

### Rejected Alternatives

The team evaluated four alternative creative twists before selecting Monster Kitchen (decision record: ADR-001):

| Alternative | Description | Reason Rejected |
|-------------|-------------|-----------------|
| **Gravity Collapse** | Tiles fall and settle under gravity after each move | Grid physics conflict: existing 4×4 directional-slide logic incompatible with gravity-based settling without a full renderer rewrite |
| **Elemental Clash** | Tiles represent elements (fire/water/earth/air) that combine via type-match rules | Type-match merge system unfamiliar to classic 2048 players, bad fit as a first-game introduction for 8-year-old learning the base game |
| **Shadow Realm** | Board develops a "dark side" with mirrored mechanics | Dark gothic aesthetic literally contradicts the target audience (8-year-olds, bright/cute mandate) |
| **Mirror Duel** | Two players share one board, PvP scoring race | Competitive PvP scope too large for initial release; shifts focus from single-player puzzle satisfaction |

## Features

- **Classic 2048 gameplay** — slide tiles up, down, left, or right; matching tiles merge into the next tier
- **11 food tiers** — evolve from a tiny blueberry (2) all the way up to a magnificent chef's masterpiece cake (2048)
- **Rotten Food contamination** — every few moves a gross rotten tile appears on the board with a countdown timer. If you do not merge it away in time, it spreads and contaminates a neighbour! Keep your kitchen clean!
- **Achievements** — unlock badges for reaching milestones and pulling off clever moves
- **Undo & restart** — made a mistake? Press Z to undo. Want a fresh start? Press Space for a new game
- **Score tracking** — your current score and best score are always visible

## Installation

You need **Python 3.11 or newer** and [Poetry](https://python-poetry.org/) installed on your computer.

```bash
# 1. Clone the repository
git clone https://github.com/Favur/the2048.git
cd the2048

# 2. Install all dependencies
poetry install
```

## Running the Game

Start the game with one command:

```bash
poetry run python -m src.main
```

### Controls

| Key | Action |
|-----|--------|
| **Arrow keys** | Slide tiles (up, down, left, right) |
| **Z** | Undo last move |
| **Space** | Start a new game |
| **Escape** | Quit |
| **Mouse click** | Press on-screen buttons |

## Running Tests

```bash
poetry run pytest
```

The test suite covers the core game logic (slide/merge mechanics, scoring, rotten food contamination, achievements) and runs in CI on Python 3.11, 3.12, and 3.13.

## Building a Standalone Executable

Create a single-file executable that runs without Python installed:

**Windows:**

```bash
poetry run python scripts/build.py
```

**macOS / Linux:**

```bash
poetry run python scripts/build.py
```

The built executable appears in the `dist/` directory (`the2048.exe` on Windows, `the2048` on macOS/Linux).

To force a clean rebuild:

```bash
poetry run python scripts/build.py --clean
```

> **Note:** The build script uses the `the2048.spec` PyInstaller configuration, which bundles all 24 game assets (tile sprites, UI elements, mascot) into a single-file executable and sets up a runtime hook so the game can find its assets after extraction.

## Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | ^3.11 (tested 3.11, 3.12, 3.13) | Runtime language |
| pygame-ce | ^2.5 | Game engine (community edition of pygame) |
| Poetry | Latest | Dependency management & virtual environments |
| pytest | ^9.1.1 | Test runner |
| pytest-cov | ^7.1.0 | Test coverage reporting |
| PyInstaller | ^6.21.0 | Standalone binary packaging |
| GitHub Actions CI | v1 | Continuous integration testing across Python 3.11–3.13 |

## Project Structure

```
├── src/                        # Game source code
│   ├── core/                   # Pure Python game logic (no pygame imports)
│   │   ├── board.py            #   4×4 grid state, slide & merge
│   │   ├── rules.py            #   Game rules & valid-move detection
│   │   ├── score.py            #   Score tracking
│   │   ├── achievements.py     #   Achievement definitions & tracking
│   │   ├── game_session.py     #   Read-only session facade for renderer
│   │   ├── history.py          #   Undo state stack
│   │   └── twist.py            #   Rotten Food contamination logic
│   ├── render/                 # Pygame rendering pipeline
│   │   ├── renderer.py         #   Central renderer (BoardRenderer)
│   │   ├── animation.py        #   Tile slide/merge animations
│   │   ├── animation_manager.py#   Animation orchestration
│   │   ├── asset_loader.py     #   PNG asset loading from assets/
│   │   ├── layout.py           #   Board layout & coordinate mapping
│   │   ├── merge_celebration.py#   Merge glow effects
│   │   └── toast_manager.py    #   Achievement toast popups
│   ├── main.py                 # Entry point — starts the game
│   └── __main__.py             # python -m src support
├── tests/                      # Test suite (422+ tests, pytest)
├── assets/                     # Game art: tiles, mascot, UI elements
│   ├── tiles/                  #   13 tile sprites (blueberry → mega-cake + rotten)
│   ├── ui/                     #   8 UI elements (board bg, score card, overlays)
│   └── mascot/                 #   3 mascot expressions (idle, happy, worried)
├── scripts/                    # Build & utility scripts
│   ├── build.py                #   PyInstaller build wrapper
│   └── runtime_hook.py         #   Runtime hook for --onefile asset resolution
├── .github/workflows/          # CI pipeline
│   └── ci.yml                  #   GitHub Actions: pytest on Python 3.11, 3.12, 3.13
├── visual-proof/               # Visual verification artifacts
├── the2048.spec                # PyInstaller configuration
├── pyproject.toml              # Project config & dependencies
├── poetry.lock                   # Poetry lockfile (generated)
└── .git*                         # Git metadata (excluded from repo tree)
```

## License

See the [LICENSE](LICENSE) file for details.