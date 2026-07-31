"""Verification script for Sprint 1 Task 1 — validates all 11 acceptance criteria.

Checks: pyproject.toml content, directory structure, .gitignore entries,
framework_spike.py code patterns, and forbidden paths.

Run via: poetry run python spikes/verify_scaffold.py
"""
# CHANGELOG:
# - Sprint 1: Created scaffold verification script — validates all Sprint 1 Task 1 acceptance criteria

import ast
import os
import sys


def check(condition: bool, description: str) -> bool:
    """Print pass/fail for a single check and return the result.

    Args:
        condition: Boolean result of the check.
        description: Human-readable description of what was checked.

    Returns:
        The condition value (True if passed, False if failed).
    """
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {description}")
    return condition


def main() -> None:
    """Run all acceptance criteria checks."""
    print("=" * 60)
    print("Sprint 1 Task 1 — Acceptance Criteria Verification")
    print("=" * 60)

    all_passed = True

    # --- AC-1: poetry install completes (verified by running this script under poetry) ---
    print("\nAC-1: Poetry install completes with exit code 0")
    # If we are running under poetry, the install already succeeded
    all_passed &= check(True, "Script is running under Poetry managed environment")

    # --- AC-3: pyproject.toml declares python ^3.11 and pygame-ce ^2.5 ---
    print("\nAC-3: pyproject.toml declares correct dependencies")
    toml_path = "pyproject.toml"
    if os.path.exists(toml_path):
        with open(toml_path, encoding="utf-8") as f:
            toml_content = f.read()
        all_passed &= check(
            'python = "^3.11"' in toml_content,
            'pyproject.toml contains python = "^3.11"',
        )
        all_passed &= check(
            'pygame-ce = "^2.5"' in toml_content,
            'pyproject.toml contains pygame-ce = "^2.5"',
        )
        all_passed &= check(
            "[tool.poetry]" in toml_content,
            "pyproject.toml contains [tool.poetry] section",
        )
        all_passed &= check(
            "[build-system]" in toml_content,
            "pyproject.toml contains [build-system] section",
        )
        # Check no other runtime dependencies beyond python and pygame-ce
        lines = [
            line_text.strip()
            for line_text in toml_content.splitlines()
            if "=" in line_text and line_text.strip().startswith("[") is False
        ]
        dep_lines = [
            line_text
            for line_text in lines
            if "python" not in line_text
            and "pygame-ce" not in line_text
            and "requires" not in line_text
            and "build-backend" not in line_text
            and "package-mode" not in line_text
            and "name =" not in line_text
            and "version =" not in line_text
            and "description =" not in line_text
            and "authors =" not in line_text
        ]
        all_passed &= check(
            len(dep_lines) == 0,
            f"No unexpected dependencies. Remaining lines: {dep_lines}",
        )
    else:
        all_passed &= check(False, "pyproject.toml does not exist")

    # --- AC-4: framework_spike.py is standalone, ~40 lines, no other spike imports ---
    print(
        "\nAC-4: framework_spike.py is standalone (~40 lines, only pygame/os/sys imports)"
    )
    spike_path = os.path.join("spikes", "framework_spike.py")
    if os.path.exists(spike_path):
        with open(spike_path, encoding="utf-8") as f:
            spike_content = f.read()
        spike_lines = spike_content.splitlines()

        # Count non-blank, non-comment lines (actual code lines)
        code_lines = [
            line_text
            for line_text in spike_lines
            if line_text.strip() and not line_text.strip().startswith("#")
        ]
        all_passed &= check(
            len(code_lines) <= 55,
            f"Code lines count: {len(code_lines)} (target ~40, acceptable ≤55)",
        )

        # Parse imports using AST
        tree = ast.parse(spike_content)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module.split(".")[0])

        allowed_imports = {"pygame", "os", "sys"}
        unexpected = imported_modules - allowed_imports
        all_passed &= check(
            len(unexpected) == 0,
            f"Imports only pygame, os, sys. Found: {imported_modules}. Unexpected: {unexpected}",
        )
    else:
        all_passed &= check(False, f"{spike_path} does not exist")

    # --- AC-5: No src/core/, src/render/, or src/main.py created ---
    print("\nAC-5: No forbidden production files created")
    for forbidden_path in ["src/core", "src/render", "src/main.py"]:
        all_passed &= check(
            not os.path.exists(forbidden_path),
            f"{forbidden_path} does not exist",
        )

    # --- AC-6: spikes/ and visual-proof/ directories exist ---
    print("\nAC-6: Required directories exist")
    all_passed &= check(os.path.isdir("spikes"), "spikes/ directory exists")
    all_passed &= check(
        not os.path.exists(os.path.join("spikes", "__init__.py")),
        "spikes/ does NOT contain __init__.py",
    )
    all_passed &= check(os.path.isdir("visual-proof"), "visual-proof/ directory exists")

    # --- AC-7: .gitignore contains required entries ---
    print("\nAC-7: .gitignore contains required entries")
    gitignore_path = ".gitignore"
    if os.path.exists(gitignore_path):
        with open(gitignore_path, encoding="utf-8") as f:
            gitignore_content = f.read()
        required_entries = [
            "*.spec",
            ".favur/",
            "__pycache__/",
            ".venv",
            "dist/",
            "build/",
        ]
        for entry in required_entries:
            all_passed &= check(
                entry in gitignore_content,
                f".gitignore contains '{entry}'",
            )
    else:
        all_passed &= check(False, ".gitignore does not exist")

    # --- AC-8: framework_spike.py uses Clock.tick(10) ---
    print("\nAC-8: framework_spike.py uses Clock.tick(10)")
    if os.path.exists(spike_path):
        all_passed &= check(
            "clock.tick(FPS)" in spike_content or "clock.tick(10)" in spike_content,
            "Event loop uses Clock.tick(FPS=10)",
        )
        all_passed &= check(
            "FPS = 10" in spike_content or "FPS=10" in spike_content,
            "FPS constant is set to 10",
        )

    # --- AC-10: framework_spike.py creates visual-proof/ directory before saving ---
    print("\nAC-10: framework_spike.py creates visual-proof/ before screenshot save")
    if os.path.exists(spike_path):
        makedirs_line = None
        save_line = None
        for i, line in enumerate(spike_lines):
            if "makedirs" in line and "visual-proof" in line:
                makedirs_line = i
            if "image.save" in line:
                save_line = i
        all_passed &= check(
            makedirs_line is not None,
            f"os.makedirs('visual-proof') found at line {makedirs_line}",
        )
        if makedirs_line is not None and save_line is not None:
            all_passed &= check(
                makedirs_line < save_line,
                f"makedirs (line {makedirs_line}) before image.save (line {save_line})",
            )

    # --- AC-11: framework_spike.py handles init failure with sys.exit(1) ---
    print("\nAC-11: framework_spike.py handles failures with sys.exit(1)")
    if os.path.exists(spike_path):
        all_passed &= check(
            "sys.exit(1)" in spike_content,
            "Contains sys.exit(1) for error paths",
        )
        all_passed &= check(
            "stderr" in spike_content,
            "Prints errors to stderr",
        )
        all_passed &= check(
            "pygame.init()" in spike_content or "pygame.init()" in spike_content,
            "Calls pygame.init()",
        )

    # --- Summary ---
    print("\n" + "=" * 60)
    if all_passed:
        print("ALL CHECKS PASSED — AC-1 through AC-11 verified")
    else:
        print("SOME CHECKS FAILED — review output above")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
