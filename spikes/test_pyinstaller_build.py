# CHANGELOG:
# - Sprint 2: Created PyInstaller build validation script with SMOKE-1 through SMOKE-5

"""PyInstaller build pipeline validation script.

Standalone smoke test runner that verifies the PyInstaller build pipeline
for the framework spike end-to-end. Produces structured PASS/FAIL output
and exits with code 0 (all pass) or 1 (any fail).

Runnable via: poetry run python spikes/test_pyinstaller_build.py
"""

import os
import re
import subprocess
import sys
from pathlib import Path

# Project root — this script lives in spikes/, so parent is the project root
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# Artifact paths
DIST_EXE: Path = PROJECT_ROOT / "dist" / "framework_spike.exe"
FINDINGS_DOC: Path = PROJECT_ROOT / "docs" / "pyinstaller-findings.md"

# Timeouts (seconds)
BUILD_TIMEOUT: int = 300  # PyInstaller build can be slow
LAUNCH_TIMEOUT: int = 30  # Binary should exit in <1s; 30s is a generous safety margin
IMPORT_TIMEOUT: int = 30  # PyInstaller import check
GIT_TIMEOUT: int = 15     # git status is instant

# Required section headers in docs/pyinstaller-findings.md
REQUIRED_FINDINGS_SECTIONS: list[str] = [
    "Build Environment",
    "Hidden Imports",
    "SDL and Display",
]


def _headless_env() -> dict[str, str]:
    """Return an environment dict with an SDL headless driver for pygame-ce rendering.

    Copies the current process environment and adds the appropriate SDL_VIDEODRIVER
    override for the current platform. On Windows, 'dummy' provides a virtual display.
    On Linux, 'offscreen' provides a software-only rendering surface. The original
    os.environ is never mutated.

    IMPLEMENTATION DECISION: Platform-specific driver selection.
    Rationale: SDL_VIDEODRIVER=offscreen is Linux-only. On Windows, only 'dummy'
    (and 'windib') are available headless backends. The pseudocode edge cases
    section explicitly identifies this as a known platform limitation.
    Alternatives: hardcode 'offscreen' (fails on Windows), detect driver at runtime
    (more complex, unnecessary for a build spike).
    """
    env = os.environ.copy()
    if sys.platform == "win32":
        env["SDL_VIDEODRIVER"] = "dummy"
    else:
        env["SDL_VIDEODRIVER"] = "offscreen"
    return env


# ---------------------------------------------------------------------------
# Smoke tests — each returns (passed: bool, detail: str)
# ---------------------------------------------------------------------------


def test_pyinstaller_installed() -> tuple[bool, str]:
    """SMOKE-1: Verify PyInstaller is importable within the Poetry environment.

    Runs: poetry run python -c "import PyInstaller; print(PyInstaller.__version__)"
    Expects: exit code 0, non-empty stdout containing a version string.
    Verifies: AC-1.
    """
    cmd = [
        "poetry", "run", "python", "-c",
        "import PyInstaller; print(PyInstaller.__version__)",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=IMPORT_TIMEOUT,
        )
    except FileNotFoundError:
        return False, "SMOKE-1: 'poetry' command not found — is Poetry installed and on PATH?"
    except subprocess.TimeoutExpired:
        return False, f"SMOKE-1: Timed out after {IMPORT_TIMEOUT}s waiting for PyInstaller import"

    if result.returncode != 0:
        stderr_lines = result.stderr.strip().splitlines()
        last_error = stderr_lines[-1] if stderr_lines else "(no stderr)"
        return False, (
            f"SMOKE-1 FAIL: PyInstaller import failed — exit code {result.returncode}\n"
            f"  stderr: {last_error}"
        )

    version = result.stdout.strip()
    if not version:
        return False, "SMOKE-1 FAIL: PyInstaller imported but printed empty version string"

    return True, f"SMOKE-1 PASS: PyInstaller version {version}"


def test_build_produces_binary() -> tuple[bool, str]:
    """SMOKE-2: Verify PyInstaller --onefile build produces dist/framework_spike.exe.

    Runs: poetry run pyinstaller --onefile spikes/framework_spike.py
    Expects: exit code 0, dist/framework_spike.exe exists with size > 0.
    Verifies: AC-2.
    """
    cmd = ["poetry", "run", "pyinstaller", "--onefile", "spikes/framework_spike.py"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=BUILD_TIMEOUT,
            cwd=str(PROJECT_ROOT),
        )
    except FileNotFoundError:
        return False, "SMOKE-2: 'poetry' command not found — is Poetry installed and on PATH?"
    except subprocess.TimeoutExpired:
        return False, f"SMOKE-2: Build timed out after {BUILD_TIMEOUT}s"

    if result.returncode != 0:
        stderr_tail = result.stderr.strip().splitlines()[-3:] if result.stderr.strip() else ["(no stderr)"]
        return False, (
            f"SMOKE-2 FAIL: PyInstaller build exited with code {result.returncode}\n"
            f"  stderr (last 3 lines):\n    " + "\n    ".join(stderr_tail)
        )

    if not DIST_EXE.exists():
        return False, f"SMOKE-2 FAIL: Build succeeded but {DIST_EXE} does not exist"

    size = DIST_EXE.stat().st_size
    if size == 0:
        return False, f"SMOKE-2 FAIL: {DIST_EXE} exists but is 0 bytes"

    size_mb = size / (1024 * 1024)
    return True, f"SMOKE-2 PASS: dist/framework_spike.exe exists ({size_mb:.1f} MB)"


def test_binary_launches_cleanly() -> tuple[bool, str]:
    """SMOKE-3: Verify the built binary launches with offscreen rendering and exits cleanly.

    Runs: dist/framework_spike.exe with SDL_VIDEODRIVER=offscreen
    Expects: exit code 0 within 30s, stdout contains "Framework spike completed successfully".
    Verifies: AC-3.
    """
    if not DIST_EXE.exists():
        return False, (
            f"SMOKE-3 FAIL: {DIST_EXE} does not exist — SMOKE-2 (build) must pass first"
        )

    try:
        result = subprocess.run(
            [str(DIST_EXE)],
            capture_output=True,
            text=True,
            timeout=LAUNCH_TIMEOUT,
            cwd=str(PROJECT_ROOT),
            env=_headless_env(),
        )
    except subprocess.TimeoutExpired:
        return False, (
            f"SMOKE-3 FAIL: Binary did not exit within {LAUNCH_TIMEOUT}s — "
            "possible infinite loop or blocking SDL call"
        )

    if result.returncode != 0:
        stderr = result.stderr.strip()
        hint = ""
        if "SDL_VIDEODRIVER" in stderr or "pygame.error" in stderr:
            hint = "\n  hint: Try SDL_VIDEODRIVER=dummy as fallback"
        return False, (
            f"SMOKE-3 FAIL: Binary exited with code {result.returncode}{hint}\n"
            f"  stderr: {stderr[:200]}"
        )

    stdout = result.stdout.strip()
    if "Framework spike completed successfully" not in stdout:
        return False, (
            "SMOKE-3 FAIL: Binary ran but did not print expected success message\n"
            f"  stdout: {stdout[:200]}\n"
            f"  stderr: {result.stderr.strip()[:200]}"
        )

    return True, "SMOKE-3 PASS: Binary launched with offscreen rendering, exited cleanly (exit code 0)"


def test_build_artifacts_gitignored() -> tuple[bool, str]:
    """SMOKE-4: Verify build artifacts are gitignored and do not appear in git status.

    Runs: git status --porcelain
    Expects: no lines matching dist/, build/, or .spec patterns.
    Verifies: .gitignore constraint.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT,
            cwd=str(PROJECT_ROOT),
        )
    except FileNotFoundError:
        return False, "SMOKE-4: 'git' command not found — is Git installed and on PATH?"

    if result.returncode != 0:
        return False, (
            f"SMOKE-4 FAIL: git status exited with code {result.returncode}\n"
            f"  stderr: {result.stderr.strip()}"
        )

    # Git porcelain format: "XY path" — status codes in first 2 chars, space, then path
    artifact_pattern = re.compile(r"^(?:dist/|build/)")
    spec_pattern = re.compile(r"\.spec$")

    offending_lines: list[str] = []
    for line in result.stdout.strip().splitlines():
        if len(line) < 4:
            continue
        filepath = line[3:]  # skip 2-char status + space
        if artifact_pattern.match(filepath) or spec_pattern.search(filepath):
            offending_lines.append(line)

    if offending_lines:
        return False, (
            "SMOKE-4 FAIL: Build artifacts are NOT gitignored\n"
            "  offending paths:\n    " + "\n    ".join(offending_lines)
        )

    return True, "SMOKE-4 PASS: All build artifacts correctly gitignored (dist/, build/, *.spec)"


def test_findings_document_exists() -> tuple[bool, str]:
    """SMOKE-5: Verify docs/pyinstaller-findings.md exists and contains required sections.

    Checks: file exists, size > 0, contains section headers for Build Environment,
    Hidden Imports, and SDL and Display.
    Verifies: AC-4.
    """
    if not FINDINGS_DOC.exists():
        return False, f"SMOKE-5 FAIL: {FINDINGS_DOC} does not exist"

    size = FINDINGS_DOC.stat().st_size
    if size == 0:
        return False, f"SMOKE-5 FAIL: {FINDINGS_DOC} exists but is empty (0 bytes)"

    content = FINDINGS_DOC.read_text(encoding="utf-8")

    missing_sections = [
        section for section in REQUIRED_FINDINGS_SECTIONS
        if section not in content
    ]

    if missing_sections:
        return False, (
            f"SMOKE-5 FAIL: {FINDINGS_DOC} missing required sections\n"
            f"  missing: {', '.join(missing_sections)}\n"
            f"  found: {[s for s in REQUIRED_FINDINGS_SECTIONS if s in content]}"
        )

    return True, (
        f"SMOKE-5 PASS: docs/pyinstaller-findings.md exists ({size} bytes) "
        f"with all required sections ({', '.join(REQUIRED_FINDINGS_SECTIONS)})"
    )


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

ALL_TESTS: list[tuple[str, callable]] = [
    ("SMOKE-1: PyInstaller installed", test_pyinstaller_installed),
    ("SMOKE-2: Build produces binary", test_build_produces_binary),
    ("SMOKE-3: Binary launches cleanly", test_binary_launches_cleanly),
    ("SMOKE-4: Build artifacts gitignored", test_build_artifacts_gitignored),
    ("SMOKE-5: Findings document exists", test_findings_document_exists),
]


def main() -> int:
    """Run all smoke tests and print structured results.

    Returns:
        0 if all tests pass, 1 if any test fails.
    """
    print("=" * 60)
    print("PyInstaller Build Validation — Smoke Tests")
    print(f"Project root: {PROJECT_ROOT}")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    for name, test_fn in ALL_TESTS:
        try:
            ok, detail = test_fn()
        except Exception as exc:
            ok = False
            detail = f"{name}: UNHANDLED EXCEPTION — {exc}"

        if ok:
            passed += 1
        else:
            failed += 1

        print(detail)
        print()

    print("-" * 60)
    total = passed + failed
    if failed == 0:
        print(f"All {total} tests passed")
    else:
        print(f"{passed}/{total} tests passed ({failed} failed)")
    print("-" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
