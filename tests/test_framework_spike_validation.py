"""Standalone validation test for the framework spike script.

Runs spikes/framework_spike.py via subprocess with headless SDL drivers
and asserts that the screenshot artifact is produced correctly.

Usage:
    poetry run python tests/test_framework_spike_validation.py

Not a pytest suite — plain assert-based validation script.
Exit 0 = all checks passed, exit 1 = at least one failure.
"""

import os
import subprocess
import sys

# Paths relative to project root
SPIKE_SCRIPT = os.path.join("spikes", "framework_spike.py")
SCREENSHOT_PATH = os.path.join("visual-proof", "framework_spike.png")
# PNG magic bytes: 0x89 followed by "PNG" (0x50 0x4E 0x47)
PNG_MAGIC = b"\x89PNG"


def run() -> int:
    """Execute all validation checks. Returns 0 on full pass, 1 on any failure."""
    passed = 0
    failed = 0
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # --- Step 1: Run the framework spike script ---
    print("[1/4] Running spikes/framework_spike.py via subprocess …", flush=True)
    env = os.environ.copy()
    # Use 'dummy' driver — available on both Windows CI and Linux headless.
    # 'offscreen' is not available on all SDL builds (e.g., Windows without
    # SDL offscreen video backend). 'dummy' creates a valid display surface
    # without requiring a real screen — suitable for subprocess validation.
    env["SDL_VIDEODRIVER"] = "dummy"
    env["SDL_AUDIODRIVER"] = "dummy"
    try:
        result = subprocess.run(
            [sys.executable, SPIKE_SCRIPT],
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        print("  FAIL — subprocess timed out after 30 s", flush=True)
        return 1

    # --- Step 2: Assert exit code == 0 ---
    print("[2/4] Checking subprocess exit code …", flush=True)
    if result.returncode == 0:
        print("  PASS — exit code 0")
        passed += 1
    else:
        print(f"  FAIL — exit code {result.returncode}")
        if result.stdout.strip():
            print(f"  stdout:\n{result.stdout}", flush=True)
        if result.stderr.strip():
            print(f"  stderr:\n{result.stderr}", flush=True)
        failed += 1
        # Cannot continue meaningfully without a successful run
        _summary(passed, failed)
        return 1

    if result.stdout.strip():
        print(f"  [stdout] {result.stdout.strip()}")

    screenshot = os.path.join(project_root, SCREENSHOT_PATH)

    # --- Step 3: Assert screenshot exists and is non-empty ---
    print("[3/4] Checking screenshot artifact exists and is non-empty …", flush=True)
    if not os.path.isfile(screenshot):
        print(f"  FAIL — {SCREENSHOT_PATH} does not exist")
        failed += 1
    else:
        size = os.path.getsize(screenshot)
        if size > 0:
            print(f"  PASS — {SCREENSHOT_PATH} exists ({size} bytes)")
            passed += 1
        else:
            print(f"  FAIL — {SCREENSHOT_PATH} exists but is empty (0 bytes)")
            failed += 1

    # --- Step 4: Validate PNG magic bytes ---
    print("[4/4] Validating PNG magic bytes …", flush=True)
    try:
        with open(screenshot, "rb") as f:
            header = f.read(4)
        if header[:4] == PNG_MAGIC:
            print("  PASS — file starts with 0x89504E47 (\\x89PNG)")
            passed += 1
        else:
            print(f"  FAIL — expected {PNG_MAGIC!r}, got {header[:4]!r}")
            failed += 1
    except FileNotFoundError:
        print(f"  FAIL — {SCREENSHOT_PATH} not found (skipped in step 3)")
        failed += 1

    _summary(passed, failed)
    return 1 if failed > 0 else 0


def _summary(passed: int, failed: int) -> None:
    """Print a human-readable pass/fail summary to stdout."""
    total = passed + failed
    print(f"\n{'=' * 50}")
    print(f"RESULT: {passed}/{total} checks passed", flush=True)
    if failed == 0:
        print("All checks passed ✓")
    else:
        print(f"{failed} check(s) FAILED ✗")


if __name__ == "__main__":
    sys.exit(run())
