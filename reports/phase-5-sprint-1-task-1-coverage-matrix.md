# SOW AC Coverage Matrix — Phase 5 Sprint 1 Task 1

**Generated**: 2026-08-03
**Source**: sow.md (AC-1 through AC-14, Phase 5 scope)
**Manifest**: visual-proof/README.md (10 screenshots)
**Screenshots on disk**: 10 PNG files verified

## Category Definitions

| Category | Definition |
|----------|-----------|
| **screenshot-covered** | At least one existing screenshot directly demonstrates this AC |
| **automated-only** | Verified by automated tests (pytest); no visual evidence needed |
| **gap** | Not covered by any screenshot or automated test; requires resolution |
| **non-visual** | No observable visual outcome; structural or tooling requirement |

## Coverage Summary

| Category | Count | AC IDs |
|----------|-------|--------|
| screenshot-covered | 7 | AC-1, AC-2, AC-4, AC-6, AC-8, AC-9, AC-13 |
| automated-only | 4 | AC-3, AC-7, AC-11, AC-12 |
| gap | 2 | AC-5 (uncapturable), AC-14 (partial) |
| non-visual | 1 | AC-10 |
| **Total** | **14** | |

## Summary

Cross-references all 14 SOW acceptance criteria (AC-1 through AC-14) against 10 existing screenshots in visual-proof/ to identify coverage gaps and false-positive manifest claims. Produced as input to the Phase 5 visual-proof sweep manifest rewrite.

| SOW AC | Description | Category | Screenshot(s) | Manifest Claim | False Positive | Gap Resolution |
|--------|-------------|----------|---------------|----------------|----------------|----------------|
| AC-1 | Slide mechanics correct in all directions | screenshot-covered | phase4_after_right.png, phase4_after_move.png | phase4_after_right.png→AC-1, phase4_after_move.png→AC-1, phase4_feedback.png→AC-1 | No | Covered |
| AC-2 | Tile merge + scoring correct | screenshot-covered | phase4_feedback.png, phase4_after_move.png | phase4_feedback.png→AC-2, phase4_after_move.png→AC-2 | No | Covered |
| AC-3 | Spawn distribution 90% 2s / 10% 4s (seeded run) | automated-only | None (pytest) | phase4_feedback.png→AC-3, phase4_mid_game.png→AC-3 | Yes (x2) | Verified by pytest; no visual evidence needed |
| AC-4 | Score increases by merged tile value | screenshot-covered | phase4_feedback.png, phase4_game_over.png | phase4_feedback.png→AC-4, phase4_game_over.png→AC-4 | No | Covered |
| AC-5 | Undo restores exact previous board state and score | gap | None | phase4_mid_game.png→AC-5, phase4_game_over.png→AC-5 | Yes (x2) | Uncapturable per ADR-030 |
| AC-6 | Game ends when no empty cell and no merge remain | screenshot-covered | phase4_game_over.png | phase4_game_over.png→AC-6 | No | Covered |
| AC-7 | High score persists across separate runs | automated-only | None (pytest) | phase4_feedback.png→AC-7, phase4_game_over.png→AC-7 | Yes (x2) | Verified by pytest; no visual evidence needed |
| AC-8 | 10+ distinct achievements, each unlocks under stated condition | screenshot-covered | phase4_feedback.png (toast visible) | phase4_feedback.png→AC-8 | No | Covered |
| AC-9 | Committed twist and unconventional mechanic present | screenshot-covered | phase4_feedback.png (rotten tiles visible) | phase4_feedback.png→AC-9 | No | Covered |
| AC-10 | Project follows specified file structure | non-visual | None (structural check) | first_light.png→AC-10 | No | Verified by directory inspection |
| AC-11 | All Python files free of syntax errors | automated-only | None (pytest) | None claimed | No | Verified by pytest |
| AC-12 | poetry run pytest passes with 0 failures | automated-only | None (pytest) | None claimed | No | Verified by pytest |
| AC-13 | poetry run python -m src.main launches without errors | screenshot-covered | phase4_initial.png, phase4_initial_check.png | phase4_initial.png→AC-13, phase4_initial_check.png→AC-13 | No | Covered |
| AC-14 | visual-proof/ contains required artifacts with manifest | gap | visual-proof/README.md exists | README.md covers manifest requirement | No | Partial: needs dedicated merge and achievement-toast screenshots |

## Coverage Matrix

## False-Positive Analysis

The current manifest (visual-proof/README.md) contains 7 false-positive AC-to-screenshot mappings where the screenshot does not actually demonstrate the claimed criterion. These must be corrected in the manifest rewrite (Task 2).

| # | Screenshot | Claimed AC | False-Positive Rationale |
|---|-----------|------------|--------------------------|
| 1 | phase4_feedback.png | AC-7 (high score persists across runs) | High score persistence requires evidence across two separate game launches; a single screenshot cannot demonstrate cross-session persistence |
| 2 | phase4_feedback.png | AC-3 (spawn distribution 90/10) | Spawn distribution is a statistical property over a seeded run; a single gameplay screenshot cannot demonstrate the probability distribution |
| 3 | phase4_mid_game.png | AC-3 (spawn distribution 90/10) | Same rationale as above; one screenshot cannot show statistical spawn distribution |
| 4 | phase4_mid_game.png | AC-5 (undo restores previous state) | Undo requires a before/after state comparison; a single mid-game screenshot does not show state restoration |
| 5 | phase4_game_over.png | AC-7 (high score persists across runs) | Same rationale as #1; game-over screenshot does not demonstrate cross-session persistence |
| 6 | phase4_game_over.png | AC-5 (undo restores previous state) | Game-over screenshot shows a terminal state, not an undo action; no state restoration is visible |
| 7 | first_light.png | AC-10 (project file structure) | File structure is verified by directory inspection, not by a screenshot of the rendered game |

### False-Positive Correction Actions

- **AC-3**: Remove from phase4_feedback.png and phase4_mid_game.png manifests; add note "verified by pytest" in manifest
- **AC-5**: Remove from phase4_mid_game.png and phase4_game_over.png manifests; add note "uncapturable per ADR-030" in manifest
- **AC-7**: Remove from phase4_feedback.png and phase4_game_over.png manifests; add note "verified by pytest" in manifest
- **AC-10**: Remove from first_light.png manifest; add note "verified by directory inspection" in manifest

## Gap Analysis: AC-5 (Undo)

### Status: UNCAPTURABLE

**AC-5**: "Undo restores the exact previous board state and score."

### Why It Cannot Be Captured

Capturing a screenshot that demonstrates undo requires showing a **before state** and an **after state** where the after state is identical to a prior board configuration. This requires one of:

1. **Two sequential screenshots** showing the board before undo and after undo — but each screenshot is a single point in time and cannot carry the context of "this is the same state as 3 moves ago"
2. **Source code modification** to inject a specific board state for deterministic capture — prohibited by ADR-030
3. **Keyboard event simulation** (pressing Z to trigger undo) in a deterministic capture script — requires either modifying main.py to expose the undo handler or using OS-level key injection, neither of which is available within Phase 5 constraints

### Resolution

Document AC-5 as a gap in the manifest with the note: "Undo functionality verified by pytest (test_history.py); visual proof is uncapturable in Phase 5 due to the before/after state comparison requirement and ADR-030 prohibition on source code modifications."

The automated test suite (test_history.py) fully verifies undo correctness.

## Category Breakdown

| Category | Count | Percentage | Notes |
|----------|-------|------------|-------|
| screenshot-covered | 7 | 50% | AC-1, AC-2, AC-4, AC-6, AC-8, AC-9, AC-13 |
| automated-only | 4 | 29% | AC-3, AC-7, AC-11, AC-12 |
| gap | 2 | 14% | AC-5 (uncapturable), AC-14 (partial) |
| non-visual | 1 | 7% | AC-10 |
| **Total** | **14** | **100%** | |

### Coverage Assessment

- **50% of ACs** have direct screenshot evidence
- **29% of ACs** are verified by automated tests (pytest)
- **14% of ACs** are gaps — AC-5 is permanently uncapturable under ADR-030; AC-14 is partially covered and needs 2 additional screenshots
- **7% of ACs** are non-visual (structural)
- **False-positive count**: 7 manifest claims must be corrected in Task 2
- **Effective coverage**: 12 of 14 ACs (86%) are covered by either screenshots or automated tests; 2 ACs (14%) have gaps