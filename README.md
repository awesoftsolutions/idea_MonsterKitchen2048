# the2048 — Monster Kitchen 2048

[![CI](https://github.com/Favur/the2048/actions/workflows/ci.yml/badge.svg)](https://github.com/Favur/the2048/actions/workflows/ci.yml)

A 2048 puzzle game with a **Monster Kitchen** creative twist — a colorful kitchen/food world where tiles are cute food items crafted by little monster chefs.

## Monster Kitchen Twist

The2048 is a twist on the classic 2048 sliding-tile puzzle. The board is a **4×4 grid** where tiles represent cute food items that grow in elaboration as values increase — starting with a simple blueberry (value 2) and culminating in a legendary chef's masterpiece cake (value 2048). The visual identity is **Kawaii meets Cooking Mama**: bright pastels, rounded shapes, thick outlines, and friendly monster chef characters.

### Rotten Food Contamination

The core tension mechanic is **Rotten Food contamination**. Rotten Food tiles spawn randomly on the board every 3–5 moves. Each rotten tile carries a **3-turn countdown**. If a rotten tile is not merged away before the countdown expires, it **contaminates one adjacent tile**, converting it into a new rotten tile with its own countdown. Players must actively manage the board to prevent contamination chains from filling the grid with unusable garbage.

This creates genuine defensive pressure — the player cannot simply chase high scores but must allocate moves to sanitizing rotten tiles, producing a **dual-objective gameplay loop** (score optimization + contamination management) that does not exist in standard 2048.

### Why Monster Kitchen

| Criterion | Result |
|-----------|--------|
| preserves_core | ✅ Standard slide-and-merge on 4×4 grid, one-merge-per-tile enforced |
| adds_tension | ✅ Rotten food countdown creates urgency; contamination spread forces defensive moves |
| has_unconventional | ✅ Contamination spread as a board-degradation mechanic is not found in standard puzzle games |
| has_identity | ✅ Kawaii/Cooking Mama kitchen theme with food tiles, monster chefs, and kitchen-themed UI |

**Rationale**: The contamination mechanic creates a genuine dual-objective loop (score + defense) that satisfies all four SOW criteria. The kitchen/food theme provides a cohesive, age-appropriate visual identity. The 4×4 grid tightens the contamination pressure — fewer cells means rotten tiles have more immediate impact. Operator pre-approved.

## Rejected Alternatives

Four additional twist ideas were evaluated against the SOW criteria (preserves core mechanics, adds consistent tension, includes one unconventional mechanic, has clear identity). Each rejected alternative failed at least one criterion. Full exploration details: [`docs/twist-exploration.md`](docs/twist-exploration.md).

### Gravity Collapse

After each player slide, a gravity phase pulls all tiles downward regardless of slide direction. Tiles behave as if they have weight on a physical surface.

**Rejected**: Fails **preserves_core**. In standard 2048, tiles are stationary until the player initiates a slide. Gravity Collapse imposes a constant downward force that moves tiles without player input, changing the core mechanic from player-driven movement only to player input plus automatic physics. This is a different game, not a twist on 2048.

### Elemental Clash

Tiles carry elemental types (fire, water, earth, wind) assigned at spawn. Mismatched elements trigger special reactions (steam burst, sandstorm, lava flow, frost).

**Rejected**: Fails **adds_tension**. The tension derives from randomness, not skill — which elements spawn is unpredictable, so the player cannot develop a meaningful strategy around elemental matchups. Reactions feel like lucky breaks or unfortunate accidents rather than earned strategic decisions.

### Shadow Realm

The board is shrouded in darkness. Tiles start hidden and are revealed only when adjacent to a tile that was just moved or merged, fading back into shadow after 3 turns.

**Rejected**: Fails **has_identity**. Shadow Realm requires visual obscurity (darkness, hidden tiles) as its core mechanic, which directly undermines the ability to create a clear, joyful visual identity. You cannot express distinct tile values when tiles are hidden. The mechanic sacrifices the game's visual reward loop for cognitive challenge.

### Mirror Duel

Two 4×4 boards displayed side by side. Every slide executes on both boards simultaneously in the same direction. New tiles spawn independently on each board.

**Rejected**: Fails **adds_tension**. Mirror Duel does not introduce a new type of tension. It duplicates existing 2048 decisions across two parallel boards — the same choices on both boards with no new mechanic connecting them. This is multiplication of existing tension, not introduction of new tension.

## Phase 1 Research Findings

### Framework Validation

- **pygame-ce 2.5.x** confirmed working: window opens at 700×800 with title "Favur 2048", draws colored primitives, screenshot captured to `visual-proof/`
- Zero compatibility issues found with Python 3.13.14
- Window event loop runs cleanly with Escape-to-quit

### Packaging Validation

- **PyInstaller 6.21.0** confirmed packaging in `--onefile` mode
- Standalone binary builds and launches successfully on Windows 11
- No pygame-ce hidden-imports or custom hooks required for basic builds
- Build artifacts (`dist/`, `build/`, `*.spec`) are gitignored

### Slide/Merge Algorithm

- Pure-Python `slide_merge(grid, direction)` function validated against ≥6 hand-worked board states
- **Row-based approach with direction normalization**: LEFT/RIGHT process rows directly; UP/DOWN transpose, process as LEFT, transpose back
- One-merge-per-tile enforced: `[2, 2, 2, 0]` sliding LEFT → `[4, 2, 0, 0]`, not `[8, 0, 0, 0]`
- Grid representation: `list[list[int]]` — grid-agnostic, no numpy dependency
- Zero pygame or display imports — fully importable for headless testing

## Technology Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | ≥3.11 | Runtime |
| pygame-ce | ≥2.5 | Game framework (windowing, rendering, events) |
| Poetry | — | Dependency management and build |
| PyInstaller | ≥6.21.0 | Standalone binary packaging (dev dependency) |
| pytest | ≥9.1.1 | Test runner (dev dependency, formal test suite in Phase 2) |

## Getting Started

### Installation

```bash
poetry install
```

### Running the Framework Spike

```bash
poetry run python spikes/framework_spike.py
```

Opens a 700×800 window titled "Favur 2048" with a colored rectangle. Press Escape or close the window to exit.

### Building the Standalone Binary

```bash
poetry run pyinstaller --onefile spikes/framework_spike.py
```

Produces `dist/framework_spike.exe`. Run the binary directly to launch the game window.

### Running the Slide/Merge Validation

```bash
poetry run python spikes/test_validation.py
```

Validates the slide/merge algorithm against hand-worked board states. Exits with code 0 on all pass.

## Project Structure

```
├── spikes/                 # Research and validation scripts
│   ├── framework_spike.py        # pygame-ce window spike
│   ├── slide_merge.py            # Pure-Python slide/merge algorithm
│   ├── slide_merge_demo.py       # Interactive console demo
│   ├── test_validation.py        # Standalone validation script
│   ├── test_pyinstaller_build.py # PyInstaller build validation
│   ├── verify_constraint_compliance.py # Phase 1 constraint verification
│   └── verify_scaffold.py        # Scaffold verification
├── visual-proof/           # Screenshots and visual evidence
├── docs/                   # Project documentation
│   └── twist-exploration.md # Twist exploration record
├── pyproject.toml          # Poetry project configuration
└── README.md               # This file
```

## Phase 2 Handoff Notes

- **Algorithm adoption**: `slide_merge()` in `spikes/slide_merge.py` is validated and ready for adoption into the production board module (Phase 2). Same interface (`grid: list[list[int]], direction: Direction -> SlideResult`), same row-based approach.
- **Grid size**: The algorithm is grid-agnostic. Monster Kitchen uses a 4×4 grid (operator decision, overriding SOW's 5×5). Phase 2 implements `Board` with `size=4`.
- **Twist implementation**: The Rotten Food contamination mechanic spawns rotten tiles every 3–5 moves with a 3-turn countdown. When countdown expires, one adjacent tile is contaminated. Merging two identical rotten tiles removes both. Full specification in `docs/twist-exploration.md`.
- **pygame-ce compatibility**: No issues found. Standard pygame API calls work as documented. No hidden-imports needed for PyInstaller.
- **Testing approach**: Phase 1 used standalone validation scripts (not pytest). Phase 2 creates formal pytest suites. Hand-worked board states from `spikes/test_validation.py` become seed cases for Phase 2 test modules.

## License

See LICENSE file for details.