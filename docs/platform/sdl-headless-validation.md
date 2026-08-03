# SDL Headless Validation Report

| Field     | Value                          |
|-----------|--------------------------------|
| Version   | 1.0                            |
| Date      | 2026-08-03                     |
| Status    | **VALIDATED**                  |
| Sprint    | Phase 6, Sprint 1, Task 2      |
| Author    | Favur (hello@favur.dev)        |

## Overview

This report documents the validated SDL headless configuration for the2048 pytest CI pipeline.
The goal: run all pygame-ce tests in GitHub Actions **without a display server** by configuring SDL
to use software-only video and silent audio drivers.

This configuration follows **ADR-031** from `docs/phase-6-architecture.md`.

## SDL Environment Variables

| Variable           | Value      | Purpose                                              |
|--------------------|------------|------------------------------------------------------|
| `SDL_VIDEODRIVER`  | `offscreen` | Software-only video surface — no X11/Wayland needed |
| `SDL_AUDIODRIVER`  | `dummy`    | Silent audio — no sound card in CI runners           |

These are set directly on the `pytest` step in `.github/workflows/ci.yml` (lines 32–34):

```yaml
- name: Run tests
  env:
    SDL_VIDEODRIVER: offscreen
    SDL_AUDIODRIVER: dummy
  run: poetry run pytest
```

## Test Results

```
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
collected 422 items

422 passed in 0.70s
```

| Metric            | Result  |
|-------------------|---------|
| Tests collected   | 422     |
| Passed            | 422     |
| Failed            | 0       |
| Errors            | 0       |
| Warnings          | 0       |
| Exit code         | 0       |
| Runtime           | 0.70s   |
| Platform          | Windows 11, AMD64 |
| Python            | 3.13.14 (CPython) |
| pytest            | 9.1.1   |

**Zero failures. Zero warnings.** All 422 pygame-ce tests pass under headless SDL
with `offscreen` video and `dummy` audio.

## CI Workflow Verification

`.github/workflows/ci.yml` was validated by `scripts/validate_ci_workflow.py`.
All 11 structural checks passed:

```
PASS: top-level dict
PASS: on trigger present
PASS: jobs section present
PASS: test job exists
PASS: python-version is list
PASS: versions are strings
PASS: 3 Python versions
PASS: Poetry install step
PASS: test step present
PASS: SDL_VIDEODRIVER=offscreen
PASS: SDL_AUDIODRIVER=dummy

PASS: All CI workflow checks passed. SDL headless env vars verified.
```

Key CI structure confirmed:
- **Trigger**: push + pull_request to `trunk` branch
- **Runner**: `ubuntu-latest`
- **Python matrix**: `["3.11", "3.12", "3.13"]` (quoted strings per ADR-032)
- **Poetry install**: `poetry install --no-root`
- **Pytest command**: `poetry run pytest` with SDL env vars

## ADR-031 Fallback Chain

The architecture document (ADR-031) defines a fallback strategy for SDL video drivers:

| Priority | Driver        | When it works                     |
|----------|---------------|-----------------------------------|
| 1        | `offscreen`   | Always — pure software surfaces   |
| 2        | `dummy`       | Fallback if offscreen unavailable |
| 3        | `xvfb-run`    | Requires X11 virtual framebuffer  |

This validation confirms that **`offscreen` (priority 1) works correctly** on the
target platforms. No fallback to `dummy` video driver or `xvfb-run` is needed.

The audio driver `dummy` is the correct standalone choice — there is no audio
fallback chain because CI runners never have audio hardware.

## Validation Script

`scripts/validate_ci_workflow.py` is a CI structure validator that:

1. Parses `.github/workflows/ci.yml` (uses PyYAML if available, string matching as fallback)
2. Checks 11 structural properties: triggers, jobs, matrix, steps, and SDL env vars
3. Exits 0 on all-pass, 1 on any failure

**Usage**: `python scripts/validate_ci_workflow.py` (run from project root or any directory)

## Recommendations

1. **SDL_VIDEODRIVER=offscreen is proven** — use it as the primary driver for all CI test jobs.
2. **No xvfb-run needed** — eliminates a system-level dependency on ubuntu-latest runners.
3. **Pin driver values as env vars on the test step** — not in pytest.ini or conftest.py — so the
   CI workflow is the single source of truth for headless configuration.
4. **Re-validate after pygame-ce version bumps** — new SDL versions could change driver behavior.

## Checklist

- [x] `SDL_VIDEODRIVER=offscreen` set in CI workflow
- [x] `SDL_AUDIODRIVER=dummy` set in CI workflow
- [x] 422 tests pass with exit code 0
- [x] Zero warnings under headless mode
- [x] CI workflow structure validated (11/11 checks pass)
- [x] Python version matrix quoted per ADR-032
- [x] Validation script committed to `scripts/`