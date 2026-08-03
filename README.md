# the2048 — Monster Kitchen 2048

[![CI](https://github.com/Favur/the2048/actions/workflows/ci.yml/badge.svg)](https://github.com/Favur/the2048/actions/workflows/ci.yml)

A fun **2048 puzzle game** with a cute food-and-monster twist! Slide tiles on a 4×4 board, merge matching food items into bigger recipes, and try to reach the legendary **2048 cake** — but watch out for Rotten Food that tries to spoil your kitchen!

Built with [pygame-ce](https://pyga.me/) and Python. Designed to be fun for kids and parents alike.

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

## Building a Standalone Executable

Create a single-file executable that runs without Python installed:

```bash
poetry run pyinstaller the2048.spec
```

The built executable appears in the `dist/` directory.

## Running Tests

```bash
poetry run pytest
```

The test suite covers the core game logic (slide/merge mechanics, scoring, rotten food contamination, achievements) and runs in CI on Python 3.11, 3.12, and 3.13.

## Development — Project Structure

```
├── src/                    # Game source code
│   ├── core/               # Game logic (board, scoring, achievements)
│   │   ├── board.py        #   4×4 grid state, slide & merge
│   │   ├── score.py        #   Score tracking
│   │   ├── level.py        #   Level progression
│   │   ├── direction.py    #   Direction enum & normalization
│   │   ├── twists.py       #   Rotten Food contamination logic
│   │   └── achievements.py #   Achievement definitions & tracking
│   ├── render/             # Pygame rendering & UI
│   │   ├── main_renderer.py#   Central renderer
│   │   ├── grid_view.py    #   Grid tile drawing
│   │   ├── animations.py   #   Tile animation engine
│   │   ├── ui.py           #   Score bar, buttons, overlays
│   │   ├── theming.py      #   Visual theme config
│   │   ├── colors.py       #   Color palette (RGBA)
│   │   └── sprites.py      #   Sprite loading
│   ├── main.py             # Entry point — starts the game
│   ├── constants.py        #   Window size, grid layout, tile size
│   └── __main__.py         #   python -m src support
├── tests/                  # Test suite (pytest)
├── assets/                 # Game art: tiles, mascot, UI elements
├── docs/                   # Design documents and exploration records
├── .github/workflows/      # CI pipeline (lint + tests)
├── pyproject.toml          # Project config & dependencies
└── LICENSE
```

## License

See [LICENSE](LICENSE) file for details.