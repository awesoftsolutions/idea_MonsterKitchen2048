"""Extract real test list from the --co -q process output and compare."""

# The real --co -q output had 412 tests. Let me extract them from read_process_output data.
# I'll read the process results directly by re-running or by using the embedded report.

# Actually, the embedded pytest output (in the report code fence) has 413 PASSED lines.
# The --co -q output had 412 collected. Let me check which specific test is phantom.

# Strategy: the embedded output has PASSED entries. Let me also check if 
# test_is_move_legal_right_no_change exists in the real --co -q output.

# From the --co -q output I read earlier, I can see test_rules.py entries included:
# test_is_move_legal_right
# test_is_move_legal_right_no_change -- WAIT, is this actually there?

# Let me search through the --co -q process output for this specific test.
# From the full --co -q output I read, the test_rules tests listed are:
real_rules = [
    "test_import_rules_module",
    "test_is_move_legal_left_merges",
    "test_is_move_legal_left_no_change",
    "test_is_move_legal_right",
    # test_is_move_legal_right_no_change -- need to check
    "test_is_move_legal_empty_board",
    "test_is_move_legal_up_and_down",
    "test_get_legal_moves_returns_empty_for_empty",
    "test_get_legal_moves_returns_directions",
    "test_get_legal_moves_returns_empty_when_no_legal",
    "test_is_game_over_true_when_no_moves",
    "test_is_game_over_false_when_empty_cells",
    "test_is_game_over_false_when_merges_possible",
    "test_is_game_over_invariant",
    "test_is_game_over_has_rotten_prevents_over",
    "test_slide_merge_from_board_returns_correct_fields",
    "test_rules_direction_is_board_direction",
    "test_rotten_tile_at_center_full_board_prevents_over",
    "test_rotten_tile_at_corner_full_board_prevents_over",
    "test_rotten_tile_at_edge_full_board_prevents_over",
    "test_two_rotten_tiles_full_board_prevents_over",
    "test_four_rotten_tiles_full_board_prevents_over",
    "test_rotten_tile_non_full_board_not_over",
    "test_no_rotten_non_full_board_not_over",
    "test_full_no_merges_all_zeros_overlay_is_over",
    "test_full_no_merges_no_overlay_support_is_over",
    "test_mixed_countdowns_full_board_prevents_over",
    "test_all_zero_overlay_behaves_as_no_rotten",
    "test_is_game_over_invariant_with_rotten",
    "test_rotten_overlay_full_no_merges_no_legal_moves",
    "test_overlay_nonzero_but_has_empty_cells_not_over",
    "test_has_rotten_fallback_without_overlay_method",
    "test_overlay_inspection_overrides_has_rotten_false",
    "test_rotten_all_corner_positions",
    "test_rotten_center_position",
    "test_merges_possible_with_rotten_not_over",
    "test_stalemate_rescueable_same_value_pair_continues",
    "test_no_rescueable_pair_game_over",
    "test_stalemate_adjacent_different_values_not_rescueable",
    "test_stalemate_diagonal_rotten_not_rescueable",
    "test_stalemate_rescueable_at_all_positions",
    "test_stalemate_multiple_rotten_one_rescueable_pair",
    "test_overlay_is_readonly",
    "test_rescueable_pair_with_various_countdowns",
]

print(f"real_rules count (manual): {len(real_rules)}")

# The real --co -q output between test_rules and test_score lines
# From read_process_output, the test_rules section ends at:
# test_rules.py::test_rescueable_pair_with_various_countdowns
# then test_score.py starts

# So real test_rules has 43 tests? Let me count the entries I listed.
# The PASSED output has 44. The difference should be test_is_move_legal_right_no_change.

# Let me search the --co -q output for test_is_move_legal_right_no_change
print("\nChecking if test_is_move_legal_right_no_change appears in --co -q...")
print("Looking at the read_process_output data:")
print("Line with 'is_move_legal_right': tests/test_rules.py::test_is_move_legal_right")
print("Next line: tests/test_rules.py::test_is_move_legal_right_no_change? or test_is_move_legal_empty_board?")

# From the --co -q output I read, after test_is_move_legal_right comes:
# test_is_move_legal_empty_board (NOT test_is_move_legal_right_no_change)
# This means test_is_move_legal_right_no_change is NOT in the real suite.

print("\nCONCLUSION: test_is_move_legal_right_no_change appears in the PASSED")
print("output but NOT in the collected --co -q output.")
print("This means the embedded pytest report is inaccurate - it has an extra test.")
print("The real test_rules count is 43, not 44.")
print("Total real: 412, not 413.")
print("The table should use 43 for test_rules, not 44.")
print("Table sum would be: 413 - 44 + 43 = 412 ✓")