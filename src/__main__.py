"""Entry point for ``python -m src`` execution."""

# --- Contract ---
# Purpose:   Thin entry point for ``python -m src`` execution.
# System:    Phase 3 rendering pipeline — delegates to src.main.main().
# Depends:   src.main.main
# Used by:   ``python -m src`` invocation.
# Public API: None (script-level; no public classes or functions).
# --- End Contract ---
# CHANGELOG:
# - Sprint 3 Review: Contract comment block added

from src.main import main

if __name__ == "__main__":
    main()