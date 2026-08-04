"""Tests for the2048.spec PyInstaller configuration validation.

Validates the spec file content by parsing it as Python AST and inspecting
the Analysis() and EXE() call arguments. These tests enforce the correct
PyInstaller configuration for the Monster Kitchen 2048 standalone binary.

TDD RED PHASE: Tests 1-5 and 8 are expected to FAIL against the current
regressed spec (console=True, empty hiddenimports, empty runtime_hooks,
absolute paths). Tests 6 and 7 pass because the regressed spec still has
valid syntax and an assets datas entry.
"""
# CHANGELOG:
# - Sprint 3: TDD red-phase tests for the2048.spec configuration validation via AST parsing

from __future__ import annotations

import ast
import re
from pathlib import Path

SPEC_PATH = Path(__file__).resolve().parent.parent / "the2048.spec"


def _read_spec() -> str:
    """Read the2048.spec content from project root."""
    return SPEC_PATH.read_text(encoding="utf-8")


def _parse_spec() -> ast.Module:
    """Parse the2048.spec as Python AST."""
    return ast.parse(_read_spec(), filename=str(SPEC_PATH))


def _find_call_by_name(tree: ast.Module, name: str) -> ast.Call:
    """Walk the AST and return the first Call node whose func is a Name matching *name*.

    Raises:
        AssertionError: If no matching Call node is found.
    """
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == name
        ):
            return node
    msg = f"No Call node with function name '{name}' found in spec AST"
    raise AssertionError(msg)


def _get_keyword_value(call: ast.Call, keyword_name: str) -> ast.expr:
    """Extract the value of a keyword argument from a Call node.

    Raises:
        AssertionError: If the keyword is not present.
    """
    for kw in call.keywords:
        if kw.arg == keyword_name:
            return kw.value
    msg = f"Keyword '{keyword_name}' not found in Call node at line {call.lineno}"
    raise AssertionError(msg)


def _extract_string_list(ast_node: ast.expr) -> list[str]:
    """Extract a list of string constants from an AST List node.

    Raises:
        AssertionError: If the node is not a List of string Constants.
    """
    if not isinstance(ast_node, ast.List):
        msg = f"Expected ast.List, got {type(ast_node).__name__}"
        raise AssertionError(msg)
    result: list[str] = []
    for elt in ast_node.elts:
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
            result.append(elt.value)
        else:
            msg = f"Expected string Constant in list, got {type(elt).__name__}"
            raise AssertionError(msg)
    return result


# ---------------------------------------------------------------------------
# AC-1: console=False in EXE block
# ---------------------------------------------------------------------------


def test_spec_console_is_false() -> None:
    """Verify that the EXE block sets console=False (AC-1).

    The regressed spec has console=True. After restoration it must be False
    to prevent a console window alongside the pygame-ce game window.
    """
    tree = _parse_spec()
    exe_call = _find_call_by_name(tree, "EXE")
    console_value = _get_keyword_value(exe_call, "console")
    assert isinstance(console_value, ast.Constant), (
        f"Expected console to be a Constant node, got {type(console_value).__name__}"
    )
    assert console_value.value is False, (
        f"Expected console=False, got console={console_value.value!r}"
    )


# ---------------------------------------------------------------------------
# AC-2: hiddenimports contains 15+ pygame-ce module paths
# ---------------------------------------------------------------------------


def test_spec_hiddenimports_has_minimum_count() -> None:
    """Verify hiddenimports has at least 15 entries (AC-2).

    The restored spec contains 16 hidden imports. An empty list would fail.
    """
    tree = _parse_spec()
    analysis_call = _find_call_by_name(tree, "Analysis")
    hiddenimports_node = _get_keyword_value(analysis_call, "hiddenimports")
    hiddenimports = _extract_string_list(hiddenimports_node)
    assert len(hiddenimports) >= 15, (
        f"Expected >= 15 hidden imports, got {len(hiddenimports)}: {hiddenimports}"
    )


# ---------------------------------------------------------------------------
# AC-2 (detailed): 7 src.core.* modules present
# ---------------------------------------------------------------------------

EXPECTED_CORE_MODULES = [
    "src.core.board",
    "src.core.game_session",
    "src.core.achievements",
    "src.core.history",
    "src.core.rules",
    "src.core.score",
    "src.core.twist",
]


def test_spec_hiddenimports_contain_core_modules() -> None:
    """Verify all 7 src.core.* hidden imports are present (AC-2).

    The restored spec must include all core game modules:
    board, game_session, achievements, history, rules, score, twist.
    """
    tree = _parse_spec()
    analysis_call = _find_call_by_name(tree, "Analysis")
    hiddenimports_node = _get_keyword_value(analysis_call, "hiddenimports")
    hiddenimports = _extract_string_list(hiddenimports_node)
    for expected in EXPECTED_CORE_MODULES:
        assert expected in hiddenimports, (
            f"Missing core module '{expected}' in hiddenimports: {hiddenimports}"
        )


# ---------------------------------------------------------------------------
# AC-2 (detailed): 7 src.render.* modules present
# ---------------------------------------------------------------------------

EXPECTED_RENDER_MODULES = [
    "src.render.animation",
    "src.render.animation_manager",
    "src.render.asset_loader",
    "src.render.layout",
    "src.render.merge_celebration",
    "src.render.renderer",
    "src.render.toast_manager",
]


def test_spec_hiddenimports_contain_render_modules() -> None:
    """Verify all 7 src.render.* hidden imports are present (AC-2).

    The restored spec must include all render modules:
    animation, animation_manager, asset_loader, layout,
    merge_celebration, renderer, toast_manager.
    """
    tree = _parse_spec()
    analysis_call = _find_call_by_name(tree, "Analysis")
    hiddenimports_node = _get_keyword_value(analysis_call, "hiddenimports")
    hiddenimports = _extract_string_list(hiddenimports_node)
    for expected in EXPECTED_RENDER_MODULES:
        assert expected in hiddenimports, (
            f"Missing render module '{expected}' in hiddenimports: {hiddenimports}"
        )


# ---------------------------------------------------------------------------
# AC-3: runtime_hooks references scripts/runtime_hook.py
# ---------------------------------------------------------------------------


def test_spec_runtime_hooks_references_hook() -> None:
    """Verify runtime_hooks contains 'scripts/runtime_hook.py' (AC-3).

    The runtime hook handles sys._MEIPASS CWD resolution for onefile mode.
    The regressed spec has runtime_hooks=[] which would fail this check.
    """
    tree = _parse_spec()
    analysis_call = _find_call_by_name(tree, "Analysis")
    runtime_hooks_node = _get_keyword_value(analysis_call, "runtime_hooks")
    runtime_hooks = _extract_string_list(runtime_hooks_node)
    assert "scripts/runtime_hook.py" in runtime_hooks, (
        f"Expected 'scripts/runtime_hook.py' in runtime_hooks, got {runtime_hooks}"
    )


# ---------------------------------------------------------------------------
# AC-4: datas bundles assets
# ---------------------------------------------------------------------------


def test_spec_datas_bundles_assets() -> None:
    """Verify datas contains an assets bundling configuration (AC-4).

    The spec must bundle the assets/ directory. Tuples appear as Tuple nodes
    in the AST containing Constant elements where 'assets' appears in source
    and dest positions.
    """
    tree = _parse_spec()
    analysis_call = _find_call_by_name(tree, "Analysis")
    datas_node = _get_keyword_value(analysis_call, "datas")
    assert isinstance(datas_node, ast.List), (
        f"Expected datas to be an ast.List, got {type(datas_node).__name__}"
    )
    found_assets = False
    for elt in datas_node.elts:
        if isinstance(elt, ast.Tuple) and len(elt.elts) == 2:
            source, dest = elt.elts
            if (
                isinstance(source, ast.Constant)
                and isinstance(source.value, str)
                and "assets" in source.value
                and isinstance(dest, ast.Constant)
                and isinstance(dest.value, str)
                and "assets" in dest.value
            ):
                found_assets = True
                break
    assert found_assets, (
        "Expected a datas entry bundling 'assets', but none found in datas list"
    )


# ---------------------------------------------------------------------------
# Functional: spec file is valid Python
# ---------------------------------------------------------------------------


def test_spec_file_is_valid_python() -> None:
    """Verify the2048.spec parses as valid Python (no SyntaxError).

    PyInstaller requires the spec to be valid Python. This test confirms
    ast.parse() succeeds without raising an exception.
    """
    spec_content = _read_spec()
    # ast.parse raises SyntaxError for invalid Python
    ast.parse(spec_content, filename=str(SPEC_PATH))


# ---------------------------------------------------------------------------
# Regression: no absolute paths
# ---------------------------------------------------------------------------

_ABSOLUTE_PATH_PATTERNS = [
    re.compile(r"[A-Z]:\\", re.IGNORECASE),  # Windows drive letters: C:\, D:\
    re.compile(r"/home/"),  # Linux home
    re.compile(r"/Users/"),  # macOS home
]


def test_spec_no_absolute_paths() -> None:
    """Verify the spec contains no absolute paths (regression prevention).

    The regressed spec contained C:\\Users\\ paths. The restored spec must
    use relative paths exclusively (pathex=['.'], entry 'src/main.py',
    datas 'assets') for portability.
    """
    spec_content = _read_spec()
    for pattern in _ABSOLUTE_PATH_PATTERNS:
        match = pattern.search(spec_content)
        assert match is None, (
            f"Found absolute path matching {pattern.pattern!r} in spec file. "
            f"Use relative paths only for portability."
        )
