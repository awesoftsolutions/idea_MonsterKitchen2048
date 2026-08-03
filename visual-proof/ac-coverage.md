# SOW AC Coverage Matrix — Visual Proof Audit

**Generated**: 2026-07-31
**Sprint**: Phase 5 Sprint 1, Task 1
**Source**: Phase 5 SOW acceptance criteria (AC-1 through AC-15)

## Overview

This document maps each SOW acceptance criterion to its corresponding visual proof
evidence in the `visual-proof/` directory. Each AC is classified as:

- **PASS** — screenshot(s) exist that demonstrate this criterion
- **MISSING** — no screenshot exists; gap requires resolution
- **PARTIAL** — some evidence exists but is incomplete per SOW requirements
- **N/A** — criterion is non-visual, automated-only, or deferred to another phase

## Screenshot Inventory

| Filename | Source Phase | Demonstrates |
|---|---|---|
| `first_light.png` | Phase 3 | First rendered game frame (empty board) |
| `phase4_initial.png` | Phase 4 | Game launched with 4×4 grid and initial tiles |
| `phase4_initial_check.png` | Phase 4 | Game launched — duplicate verification capture |
| `phase4_after_move.png` | Phase 4 | Board state after a slide/merge move |
| `phase4_after_right.png` | Phase 4 | Board state after a rightward slide |
| `phase4_feedback.png` | Phase 4 | Merge feedback with golden glow and achievement toast |
| `phase4_game_over.png` | Phase 4 | Game-over overlay displayed on full board |
| `phase4_achievement_check.png` | Phase 4 | Achievement system verification |
| `phase4_mid_game.png` | Phase 4 | Mid-game board with multiple tile values |
| `tile_merge_4_test.png` | Phase 4 | Tile merge behavior verification |

## AC Coverage Matrix

### AC-1 — Slide mechanics correct (directions, gaps, no double-move)

**Status**: PASS

| Screenshot | Evidence |
|---|---|
| `phase4_after_move.png` | Tiles shifted in one direction with gap consolidation |
| `phase4_after_right.png` | Rightward slide with tiles packed to right edge |
| `phase4_feedback.png` | Post-merge board state confirms single-move-per-input |

No gaps. Three independent captures verify directional sliding.

### AC-2 — Tile merge when equal values collide, score increments correctly

**Status**: PASS

| Screenshot | Evidence |
|---|---|
| `phase4_after_move.png` | Merged tile visible after slide |
| `phase4_after_right.png` | Merged tile visible after rightward slide |
| `phase4_feedback.png` | Golden glow on merged tile with score display |

No gaps. Merge mechanic and score increment both visually confirmed.

### AC-3 — Spawn distribution 90% [2, 4], 10% 16

**Status**: MISSING

| Screenshot | Evidence |
|---|---|
| *(none)* | No screenshot can visually demonstrate a statistical distribution |

**Gap rationale**: Spawn ratio is a probability distribution over many games.
A single screenshot cannot prove 90/10 split. This criterion must be verified
via automated tests (statistical sample over 1000+ spawns).

**Resolution path**: Automated test in `tests/` that spawns 1000 tiles and
validates the ratio falls within confidence interval. No screenshot required.

### AC-4 — Score increases when tiles merge

**Status**: PASS

| Screenshot | Evidence |
|---|---|
| `phase4_feedback.png` | Score display shows value greater than zero after merge |

No gaps. Score display confirms post-merge increment.

### AC-5 — Undo restores previous board state and score

**Status**: MISSING

| Screenshot | Evidence |
|---|---|
| *(none)* | No screenshot demonstrates the undo action or state restoration |

**Gap rationale**: Undo requires capturing before-state, performing undo, then
showing after-state matches before-state. ADR-030 prohibits source code changes
for deterministic capture. The undo action cannot be scripted via headless
keyboard simulation without modifying the game's event handling.

**Resolution path**: Verify via automated integration test that calls undo()
and asserts board state equality. No screenshot feasible without violating ADR-030.

### AC-6 — Game ends when no valid moves remain

**Status**: PASS

| Screenshot | Evidence |
|---|---|
| `phase4_game_over.png` | Game-over overlay displayed on full board |

No gaps. Game-over state captured with overlay visible.

### AC-7 — High score persists across sessions

**Status**: MISSING

| Screenshot | Evidence |
|---|---|
| *(none)* | Cross-session persistence cannot be demonstrated in a single screenshot |

**Gap rationale**: Proving persistence requires two separate game sessions
with the second session showing the high score from the first. A single
screenshot captures one session only. ADR-030 prohibits source modifications
that would enable a scriptable two-session capture.

**Resolution path**: Verify via automated test that saves high score to disk,
restarts the game process, and asserts the loaded score matches. No screenshot
feasible.

### AC-8 — 10+ achievements unlock based on gameplay events

**Status**: PASS

| Screenshot | Evidence |
|---|---|
| `phase4_feedback.png` | Achievement toast notification visible in game UI |

No gaps. Achievement toast confirms the achievement system triggers. Full
count of 10+ achievements verified by automated tests.

### AC-9 — Twist mechanic (rotten tiles) + unconventional mechanic present

**Status**: PASS

| Screenshot | Evidence |
|---|---|
| `phase4_feedback.png` | Rotten tile visual feedback visible on board |

No gaps. Rotten tile mechanic confirmed visually. Full mechanic behavior
(timing, contamination spread) verified by automated tests.

### AC-10 — File structure follows agreed conventions

**Status**: N/A

Non-visual criterion. Directory structure is verified by `ls` or directory
listing, not by screenshot. No screenshot required.

### AC-11 — No syntax errors in Python source files

**Status**: N/A

Automated-only criterion. Verified by `python -m py_compile` or pytest
collection. No screenshot applicable.

### AC-12 — pytest passes with zero failures

**Status**: N/A

Automated-only criterion. Verified by `pytest` exit code 0. No screenshot
applicable.

### AC-13 — Game launches and renders without errors

**Status**: PASS

| Screenshot | Evidence |
|---|---|
| `phase4_initial.png` | Game window rendered with grid and initial tiles |
| `phase4_initial_check.png` | Duplicate verification of successful launch |

No gaps. Two captures confirm successful launch and rendering.

### AC-14 — visual-proof/ directory complete with manifest

**Status**: PARTIAL

| Screenshot | Evidence |
|---|---|
| *(manifest file)* | `README.md` exists with per-file descriptions |

**Partial gaps per SOW requirements**:
- First light: covered by `first_light.png`
- Tiles after real moves: covered by `phase4_after_move.png` and `phase4_after_right.png`
- Merge with feedback: `phase4_feedback.png` exists but merge glow is brief
- Achievement toast: `phase4_feedback.png` shows toast — partially covered
- Game-over: covered by `phase4_game_over.png`

**Missing**: Dedicated merge-focused screenshot and dedicated achievement
toast screenshot. Current coverage relies on `phase4_feedback.png` for both.

**Resolution path**: Generate one additional screenshot capturing merge
feedback in isolation, and one capturing achievement toast in isolation.
This would bring AC-14 to PASS.

### AC-15 — GitHub Actions CI passes + standalone binary builds

**Status**: N/A

Deferred to Phase 6. CI pipeline and PyInstaller binary build are not
in scope for Phase 5 Sprint 1. Will be verified when Phase 6 work begins.

## False-Positive Analysis

The following entries in `visual-proof/README.md` claim AC coverage that
the corresponding screenshots do not actually demonstrate.

| Screenshot | Claimed AC | Actual Coverage | Why It Is a False Positive |
|---|---|---|---|
| `phase4_feedback.png` | AC-7 | No cross-session proof | Single screenshot cannot show persistence across sessions |
| `phase4_feedback.png` | AC-3 | Not visually determinable | 90/10 spawn ratio is a statistical property, not visible in one frame |
| `phase4_mid_game.png` | AC-3 | Not visually determinable | Spawn ratio cannot be determined from a mid-game board state |
| `phase4_mid_game.png` | AC-5 | No undo demonstrated | Mid-game board shows no before/after undo comparison |
| `phase4_game_over.png` | AC-7 | No cross-session proof | Game-over screen does not show high score persistence |
| `phase4_game_over.png` | AC-5 | No undo demonstrated | Game-over state does not demonstrate undo restoration |
| `phase4_achievement_check.png` | AC-10 | File structure is non-visual | Achievement check screenshot does not demonstrate directory conventions |

**Total false positives**: 7

**Note**: These are manifest metadata errors, not screenshot content errors.
The screenshots themselves are valid captures — the issue is incorrect AC
attribution in the README manifest.

## Gap Summary

| AC | Status | Gap Type | Resolution | Blocked By |
|---|---|---|---|---|
| AC-3 | MISSING | No visual proof possible | Automated statistical test | — |
| AC-5 | MISSING | Cannot capture undo action | Automated integration test | ADR-030 (no source changes) |
| AC-7 | MISSING | Cross-session proof impossible in one screenshot | Automated persistence test | ADR-030 (no source changes) |
| AC-14 | PARTIAL | Merge and achievement toast screenshots missing | Generate 2 additional screenshots | — |
| AC-15 | N/A | Deferred | Verify in Phase 6 | Phase 6 scope |

**Screenshot gap count**: 2 new screenshots needed (merge feedback, achievement toast)
**Automated test gaps**: 3 criteria (AC-3, AC-5, AC-7) — no screenshot possible;
verification is test-only per architecture ADRs.
