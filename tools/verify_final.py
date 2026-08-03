"""Verify final table sum after test_rules 44->43 fix."""
counts = {
    'test_achievements': 19,
    'test_animation_integration': 6,
    'test_animation_manager': 10,
    'test_asset_loader': 14,
    'test_board': 28,
    'test_first_light': 3,
    'test_game_session': 48,
    'test_high001_fix': 5,
    'test_history': 20,
    'test_input_handler': 12,
    'test_integration': 15,
    'test_main': 28,
    'test_merge_celebration': 10,
    'test_phase4_components': 15,
    'test_render_layout': 18,
    'test_renderer': 34,
    'test_rules': 43,
    'test_score': 13,
    'test_sprint_4_2_integration': 6,
    'test_sprint_4_2_rem': 5,
    'test_sprint_4_2_remediation': 5,
    'test_state_manager': 9,
    'test_toast_manager': 9,
    'test_toast_positioning': 2,
    'test_twist': 22,
    'test_visual_proof_manifest': 3,
    'test_visual_proof_readme': 8,
    'test_window_flags': 2,
}
total = sum(counts.values())
print(f"Table sum: {total} (expected: 412)")
assert total == 412, f"FAIL: sum is {total}, expected 412"
print("PASS: Table sums to 412")

# Count test files
print(f"Test file count: {len(counts)} (expected: 28)")
assert len(counts) == 28, f"FAIL: count is {len(counts)}, expected 28"
print("PASS: 28 test files")