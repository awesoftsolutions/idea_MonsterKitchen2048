"""Entry point for ``python -m src.render`` execution."""

# --- Contract ---
# Purpose:   Thin entry point for ``python -m src.render`` execution.
# System:    Phase 3 rendering pipeline — delegates to src.main.main().
# Depends:   src.main.main
# Used by:   ``python -m src.render`` invocation.
# Public API: None (script-level; no public classes or functions).
# --- End Contract ---

from src.main import main

if __name__ == "__main__":
    main()
