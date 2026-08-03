"""Validate the CI workflow YAML has correct SDL headless env vars."""
import sys
import os
from pathlib import Path

# Resolve YAML path relative to this script's parent (project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"

try:
    import yaml
except ImportError:
    # PyYAML not installed; fall back to basic string check
    with open(YAML_PATH, "r") as f:
        content = f.read()
    checks = [
        ("SDL_VIDEODRIVER: offscreen", "SDL_VIDEODRIVER" in content and "offscreen" in content),
        ("SDL_AUDIODRIVER: dummy", "SDL_AUDIODRIVER" in content and "dummy" in content),
        ("python-version matrix", '"3.11"' in content and '"3.12"' in content and '"3.13"' in content),
        ("push trigger to trunk", "trunk" in content),
        ("poetry install step", "poetry install" in content),
        ("poetry run pytest step", "poetry run pytest" in content),
    ]
    for name, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  {status}: {name}")
    sys.exit(0 if all(ok for _, ok in checks) else 1)

with open(YAML_PATH, "r") as f:
    data = yaml.safe_load(f)

checks = {}

# 1. Top-level structure
checks["top-level dict"] = isinstance(data, dict)
checks["on trigger present"] = data.get("on") is not None or data.get(True) is not None
checks["jobs section present"] = "jobs" in data

# 2. Test job exists
test_job = data.get("jobs", {}).get("test", {})
checks["test job exists"] = bool(test_job)

# 3. Python version matrix
matrix = test_job.get("strategy", {}).get("matrix", {})
versions = matrix.get("python-version", [])
checks["python-version is list"] = isinstance(versions, list)
checks["versions are strings"] = all(isinstance(v, str) for v in versions) if versions else False
checks["3 Python versions"] = len(versions) == 3 if isinstance(versions, list) else False

# 4. Steps
steps = test_job.get("steps", [])
step_names = [s.get("name", "") for s in steps]
checks["Poetry install step"] = any("Poetry" in n for n in step_names)
checks["test step present"] = any("test" in n.lower() for n in step_names)

# 5. SDL env vars on test step
test_step = next((s for s in steps if "test" in s.get("name", "").lower()), {})
env = test_step.get("env", {})
checks["SDL_VIDEODRIVER=offscreen"] = env.get("SDL_VIDEODRIVER") == "offscreen"
checks["SDL_AUDIODRIVER=dummy"] = env.get("SDL_AUDIODRIVER") == "dummy"

# Print results
all_pass = True
for name, ok in checks.items():
    status = "PASS" if ok else "FAIL"
    if not ok:
        all_pass = False
    print(f"  {status}: {name}")

print()
if all_pass:
    print("PASS: All CI workflow checks passed. SDL headless env vars verified.")
    sys.exit(0)
else:
    print("FAIL: One or more CI workflow checks failed.")
    sys.exit(1)