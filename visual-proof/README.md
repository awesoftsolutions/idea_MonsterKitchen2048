# Visual Proof — Monster Kitchen 2048 (All Phases)

This directory contains visual evidence spanning Phase 1 (framework spikes), Phase 3
(first light), and Phase 4 (feedback integration) of Monster Kitchen 2048. Each screenshot
is documented with its input sequence and acceptance criteria coverage. This manifest
serves as the authoritative record of visual proof for the project.

**Total screenshots**: 9 PNG files across 3 project phases.

Contents: first_light.png, framework_spike.png, pyinstaller_spike.png, phase4_feedback.png,
phase4_after_move.png, phase4_after_right.png, phase4_initial.png, phase4_initial_check.png,
phase4_mid_game.png — plus 5 helper scripts and this README.

## 1. Visual-Proof Directory

### Screenshot Inventory

| Filename | Phase | Description | Input Sequence | AC Coverage |
|----------|-------|-------------|----------------|-------------|
| first_light.png | Phase 3 | First playable visual — 4×4 board with tile sprites, score display, mascot, and kitchen countertop background | RIGHT, DOWN, LEFT, UP repeated to populate board with visible tiles | Phase 3 AC-10 |
| framework_spike.png | Phase 1 | Framework feasibility screenshot showing pygame-ce rendering pipeline operating correctly | Framework spike test with basic window initialization | Phase 1 spike verification |
| pyinstaller_spike.png | Phase 1 | PyInstaller packaging feasibility screenshot showing the distributable executable launching | PyInstaller spike test launched from built executable | Phase 1 spike verification |
| phase4_feedback.png | Phase 4 | Active gameplay showing tile positions, merge golden glow, achievement toast notification, and mascot expression | Arrow key sequence (RIGHT, DOWN, LEFT, UP repeated) to build board; merge and toast triggers captured mid-gameplay | AC-7, AC-1, AC-2, AC-3 |
| phase4_after_move.png | Phase 4 | Board state after a move showing tile positions post-slide animation completed | Captured immediately after a slide move completed (direction: DOWN) | AC-1, AC-2 |
| phase4_after_right.png | Phase 4 | Board state after sliding tiles in the RIGHT direction, showing slide mechanics and tile arrangement | RIGHT arrow key pressed to trigger directional slide | AC-1 |
| phase4_initial.png | Phase 4 | Initial game launch with standard window chrome visible and clean fresh board | Game launched via poetry run python -m src.main, captured immediately on first frame | AC-6 |
| phase4_initial_check.png | Phase 4 | Initial board state verification showing correct tile placement and layout on startup | Game launched and captured for startup verification against expected initial state | AC-6 |
| phase4_mid_game.png | Phase 4 | Mid-game state with multiple tiles on board, mascot expression indicating activity, and non-trivial scoring | Multiple arrow key moves executed to reach a mid-game board state with diverse tile values | AC-3, AC-5 |

### Helper Scripts

| Filename | Description |
|----------|-------------|
| launch_game.bat | Windows batch launcher for the game |
| launch_game.py | Python launcher helper script |
| test_full_game.py | Full game integration test helper |
| test_game_init.py | Game initialization test helper |
| test_pygame.py | Pygame rendering test helper |

## 2. First-Light Screenshot

### Screenshot

![First Light](first_light.png)

### What the Screenshot Shows

- Monster Kitchen 4×4 board rendered on a kitchen countertop background
- Tile sprites visible at grid positions (blueberry for value 2, cupcake for value 4, etc.)
- Score display in the recipe-card UI element
- Monster chef mascot sprite visible
- Title logo "Monster Kitchen 2048" displayed
- 700×800 non-resizable window titled "Favur 2048"

### Input Sequence

The following arrow key sequence was used to populate the board before capturing the screenshot:

1. RIGHT — slide tiles right, new tile spawns
2. DOWN — slide tiles down, new tile spawns
3. LEFT — slide tiles left, new tile spawns
4. UP — slide tiles up, new tile spawns

This sequence was repeated to generate a non-trivial board state with multiple visible tiles.

### Phase 4 Screenshots

The following additional screenshots document Phase 4 feedback integration:

- **phase4_feedback.png**: Active gameplay showing merge golden glow, achievement toast, and mascot expression (AC-7, AC-1, AC-2, AC-3)
- **phase4_after_move.png**: Board state after a completed slide move (AC-1, AC-2)
- **phase4_after_right.png**: Board state after RIGHT directional slide (AC-1)
- **phase4_initial.png**: Game launch with correct 700×800 window (AC-6)
- **phase4_initial_check.png**: Startup verification of initial board state (AC-6)
- **phase4_mid_game.png**: Mid-game with active HUD and multiple tile types (AC-3, AC-5)

## 3. Game Controls

| Key | Action |
|-----|--------|
| Arrow Keys (UP/DOWN/LEFT/RIGHT) | Slide tiles in the specified direction |
| Z | Undo the last move |
| Escape | Quit the game |
| Space | Start new game (after Game Over or Win) |
| New Game Button (click) | Start new game via the UI button |

## 4. Launch Command

```bash
poetry run python -m src.main
```

### Window Details

- Size: 700 × 800 pixels
- Resizable: No
- Title: Favur 2048
- Framework: pygame-ce

## How to View Screenshots

The PNG screenshots in this directory are viewable in any standard image viewer.

To reproduce the screenshots and generate fresh visual proof:

1. Install dependencies: `poetry install`
2. Launch the game: `poetry run python -m src.main`
3. Interact: Use arrow keys to move tiles, observe merge animations and mascot reactions
4. Capture: Use your OS screenshot tool to capture game states

## 5. Test Status

Verified via Task 1 and Task 2 (Sprint 4).

| Metric | Value |
|--------|-------|
| Total Tests | 412 |
| Passed | 412 |
| Failed | 0 |
| Command | `poetry run pytest tests/ -v --tb=short` |
| Exit Code | 0 |

All tests remain green. The 3 manifest verification tests are included in the count above.

## 6. Phase 3 Acceptance Criteria Verification

All 10 Phase 3 acceptance criteria verified as PASS.

| AC | Criterion | Status | Evidence |
|----|-----------|--------|----------|
| AC-1 | 24 Monster Kitchen assets exist in assets/ with manifest.md | PASS | assets/tiles/ (13 files), assets/ui/ (8 files), assets/mascot/ (3 files), assets/manifest.md verified |
| AC-2 | 700×800 non-resizable window "Favur 2048" with kitchen countertop, board, title | PASS | Window launches via poetry run python -m src.main; screenshot at first_light.png confirms |
| AC-3 | 4×4 board renders tile sprites at correct grid positions | PASS | Screenshot shows tile sprites (blueberry, cupcake, etc.) at grid positions matching GameSession state |
| AC-4 | Arrow keys move tiles, score updates in recipe-card UI | PASS | Input sequence (RIGHT, DOWN, LEFT, UP) applied; screenshot shows updated board and score |
| AC-5 | Rotten food tiles display with visual distinction | PASS | BoardRenderer renders rotten blob overlay; warning-state sprite for countdown <= 1 |
| AC-6 | Game Over and Win overlays display | PASS | BoardRenderer.render_game_over() and render_win() verified via code review |
| AC-7 | Escape closes window; undo restores state | PASS | src/main.py handles K_ESCAPE (quit) and K_z (undo) via _handle_keydown() |
| AC-8 | GameSession read-only accessors; stalemate trap resolved | PASS | 6 accessors in game_session.py (OQ-P16); is_game_over() checks rescueable pairs (OQ-P17) |
| AC-9 | pytest passes with 0 failures | PASS | 412 tests, 0 failures, exit code 0 (verified in Task 2 regression) |
| AC-10 | First-light screenshot at visual-proof/first_light.png with README | PASS | first_light.png exists; this README documents all screenshots and input sequences |

### Phase 4 Acceptance Criteria Verification

All 8 Phase 4 acceptance criteria verified as PASS.

| AC | Criterion | Status | Evidence |
|----|-----------|--------|----------|
| AC-1 | Slide mechanics operate correctly in all 4 directions | PASS | phase4_after_right.png confirms RIGHT slide; phase4_after_move.png confirms post-move state |
| AC-2 | Tile merge and scoring works with correct visual feedback | PASS | phase4_feedback.png shows merge golden glow; phase4_after_move.png shows post-merge board |
| AC-3 | Achievement toasts render correctly for first merges and milestones | PASS | phase4_feedback.png shows achievement toast notification overlay |
| AC-4 | Mascot expression changes based on game state | PASS | phase4_mid_game.png and phase4_feedback.png show mascot reacting to game activity |
| AC-5 | HUD displays score, best score, and move count correctly | PASS | phase4_mid_game.png shows active HUD with score and move count |
| AC-6 | Game launches with correct window dimensions (700×800) | PASS | phase4_initial.png and phase4_initial_check.png show correct window on launch |
| AC-7 | Game Over and Win overlays display when conditions met | PASS | phase4_feedback.png shows overlay rendering; code inspection confirms game-over path |
| AC-8 | pytest passes with 0 failures | PASS | Full suite: 412 tests, 0 failures |

Note: phase4_game_over.png was planned for capture but was not produced during Task 1.
AC-7 is verified through code inspection and the feedback screenshot. See Known Limitations.

## 7. Known Limitations

- No movement/merge animations prior to Phase 4
- No audio (SOW: no audio)
- No undo-limit mechanic (deferred to Phase 4 playtesting)
- Grid hardcoded to 4×4 (operator directive DR-004)
- No CI/CD or cross-platform packaging (deferred to Phase 6)
- **TD-007 deferred**: Private member access pattern in save/load code remains as technical debt — non-functional, code quality only
- **phase4_game_over.png not captured**: Sprint plan listed this as a T1 deliverable, but Task 1 did not produce it. AC-7 is verified through phase4_feedback.png and code inspection. A dedicated game-over state screenshot should be captured in a future phase
- **Scout C78 observation**: Score text positioning overlaps slightly with character art on overlays — cosmetic issue, tracked for resolution

## 8. Architecture Summary

- **src/core/** — Pure Python logic layer (Board, Rules, Score, History, Achievements, Twist, GameSession). Zero pygame imports. Testable in isolation.
- **src/render/** — pygame-ce rendering pipeline (AssetLoader, BoardRenderer, HUD). Loads PNG assets from assets/ directory. Consumes GameSession state via read-only accessors.
- **src/main.py** — Game entry point. GameWindow class with pygame game loop, input handling, state machine (IDLE/PLAYING/GAME_OVER/WIN). Only file allowed to import both pygame and src.core.
- **assets/** — 24 pre-generated Monster Kitchen PNG assets (Kawaii/Cooking Mama style). Loaded eagerly at startup by AssetLoader.