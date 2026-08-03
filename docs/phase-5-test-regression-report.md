# Phase 5 Test Regression Report

**Phase**: 5 | **Sprint**: 1 | **Status**: PASS | **Date**: 2026-08-03

## Summary

Full regression test suite executed to verify Phase 5 documentation-only changes
introduce zero regressions. The test suite confirms that all existing functionality
remains intact after Phase 5 Sprint 1 work.

- **Test command**: `poetry run pytest -v`
- **Total tests**: 412
- **Passed**: 412
- **Failed**: 0
- **Skipped**: 0
- **Exit code**: 0
- **Duration**: 0.81s

---

## Detailed Results

Full `poetry run pytest -v` output:

```
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0
collecting ... collected 412 items

tests/test_achievements.py::test_import_achievements PASSED              [  0%]
tests/test_achievements.py::test_no_achievements_on_empty_state PASSED   [  0%]
tests/test_achievements.py::test_first_merge_unlocks_ach01 PASSED        [  0%]
tests/test_achievements.py::test_tile_32_unlocks_ach02 PASSED            [  0%]
tests/test_achievements.py::test_tile_256_unlocks_ach03 PASSED           [  1%]
tests/test_achievements.py::test_tile_1024_unlocks_ach04 PASSED          [  1%]
tests/test_achievements.py::test_rotten_cleared_unlocks_ach05 PASSED     [  1%]
tests/test_achievements.py::test_10_rotten_cleared_unlocks_ach06 PASSED  [  1%]
tests/test_achievements.py::test_speed_chef_unlocks_ach07 PASSED         [  2%]
tests/test_achievements.py::test_100_moves_unlocks_ach08 PASSED          [  2%]
tests/test_achievements.py::test_score_10000_unlocks_ach09 PASSED        [  2%]
tests/test_achievements.py::test_full_board_unlocks_ach10 PASSED         [  2%]
tests/test_achievements.py::test_no_waste_unlocks_ach11 PASSED           [  3%]
tests/test_achievements.py::test_contamination_survived_unlocks_ach12 PASSED [  3%]
tests/test_achievements.py::test_no_duplicate_unlocks PASSED             [  3%]
tests/test_achievements.py::test_12_achievements_defined PASSED          [  3%]
tests/test_achievements.py::test_persistence_round_trip PASSED           [  4%]
tests/test_achievements.py::test_achievement_definition_not_exported PASSED [  4%]
tests/test_achievements.py::test_no_pygame_imports PASSED                [  4%]
tests/test_animation_integration.py::test_animation_triggered_on_valid_move PASSED [  4%]
tests/test_animation_integration.py::test_no_animation_on_illegal_move PASSED [  5%]
tests/test_animation_integration.py::test_animation_interruption PASSED  [  5%]
tests/test_animation_integration.py::test_tile_positions_resolve_after_animation PASSED [  5%]
tests/test_animation_integration.py::test_animation_dt_zero_first_frame PASSED [  5%]
tests/test_animation_integration.py::test_pending_tile_moves_initialized PASSED [  6%]
tests/test_animation_manager.py::test_animation_starts PASSED            [  6%]
tests/test_animation_manager.py::test_interpolation_at_start PASSED      [  6%]
tests/test_animation_manager.py::test_interpolation_at_midpoint PASSED   [  6%]
tests/test_animation_manager.py::test_animation_completes PASSED         [  7%]
tests/test_animation_manager.py::test_snap_to_end PASSED                 [  7%]
tests/test_animation_manager.py::test_merge_scale_pulse PASSED           [  7%]
tests/test_animation_manager.py::test_no_animation_before_start PASSED   [  7%]
tests/test_animation_manager.py::test_merge_scale_for_non_merged_tile PASSED [  8%]
tests/test_animation_manager.py::test_rapid_successive_animations PASSED [  8%]
tests/test_animation_manager.py::test_empty_tile_moves_no_op PASSED      [  8%]
tests/test_asset_loader.py::test_load_all_success_with_valid_directory PASSED [  8%]
tests/test_asset_loader.py::test_load_all_raises_file_not_found_for_missing_directory PASSED [  9%]
tests/test_asset_loader.py::test_load_all_raises_pygame_error_for_corrupt_png PASSED [  9%]
tests/test_asset_loader.py::test_get_tile_sprite_returns_surface_after_load_all PASSED [  9%]
tests/test_asset_loader.py::test_get_tile_sprite_raises_keyerror_for_unknown_value PASSED [  9%]
tests/test_asset_loader.py::test_get_ui_sprite_returns_surface_after_load_all PASSED [ 10%]
tests/test_asset_loader.py::test_get_ui_sprite_raises_keyerror_for_unknown_name PASSED [ 10%]
tests/test_asset_loader.py::test_get_mascot_sprite_returns_surface_after_load_all PASSED [ 10%]
tests/test_asset_loader.py::test_get_mascot_sprite_raises_keyerror_for_unknown_state PASSED [ 10%]
tests/test_asset_loader.py::test_get_tile_sprite_cache_identity_returns_same_object PASSED [ 10%]
tests/test_asset_loader.py::test_get_special_sprite_rotten_normal PASSED [ 11%]
tests/test_asset_loader.py::test_get_special_sprite_raises_keyerror_for_unknown PASSED [ 11%]
tests/test_asset_loader.py::test_load_all_initializes_empty_cache_on_failure PASSED [ 11%]
tests/test_asset_loader.py::test_special_sprites_use_correct_filenames PASSED [ 11%]
tests/test_board.py::test_direction_enum_members PASSED                  [ 12%]
tests/test_board.py::test_slide_result_dataclass PASSED                  [ 12%]
tests/test_board.py::test_boardstate_dataclass PASSED                    [ 12%]
tests/test_board.py::test_board_initial_state PASSED                     [ 12%]
tests/test_board.py::test_board_get_set_cell PASSED                      [ 13%]
tests/test_board.py::test_board_out_of_bounds_raises PASSED              [ 13%]
tests/test_board.py::test_board_slide_left_merges PASSED                 [ 13%]
tests/test_board.py::test_board_slide_right_merges PASSED                [ 13%]
tests/test_board.py::test_board_slide_up_merges PASSED                   [ 14%]
tests/test_board.py::test_board_slide_down_merges PASSED                 [ 14%]
tests/test_board.py::test_board_slide_no_change_returns_false PASSED     [ 14%]
tests/test_board.py::test_board_slide_updates_score PASSED               [ 14%]
tests/test_board.py::test_board_is_game_over_true PASSED                 [ 15%]
tests/test_board.py::test_board_is_game_over_false PASSED                [ 15%]
tests/test_board.py::test_board_reset PASSED                             [ 15%]
tests/test_board.py::test_board_get_grid_defensive_copy PASSED           [ 15%]
tests/test_board.py::test_board_full_slide_cycle PASSED                  [ 16%]
tests/test_board.py::test_board_move_count_only_increments_on_change PASSED [ 16%]
tests/test_board.py::test_board_rng_injection PASSED                     [ 16%]
tests/test_board.py::test_boardstate_to_dict_roundtrip PASSED            [ 16%]
tests/test_board.py::test_board_to_dict_from_dict_roundtrip PASSED       [ 16%]
tests/test_board.py::test_tile_moves_left_slide PASSED                   [ 17%]
tests/test_board.py::test_tile_moves_right_slide PASSED                  [ 17%]
tests/test_board.py::test_tile_moves_up_slide PASSED                     [ 17%]
tests/test_board.py::test_tile_moves_down_slide PASSED                   [ 17%]
tests/test_board.py::test_tile_moves_merge_detection PASSED              [ 18%]
tests/test_board.py::test_tile_moves_no_move PASSED                      [ 18%]
tests/test_board.py::test_tile_moves_backward_compatibility PASSED       [ 18%]
tests/test_first_light.py::test_first_light_screenshot_exists PASSED     [ 18%]
tests/test_first_light.py::test_first_light_screenshot_non_empty PASSED  [ 19%]
tests/test_first_light.py::test_first_light_screenshot_is_valid_png PASSED [ 19%]
tests/test_game_session.py::test_constructor_creates_all_modules PASSED  [ 19%]
tests/test_game_session.py::test_constructor_spawns_initial_tiles PASSED [ 19%]
tests/test_game_session.py::test_constructor_shared_rng_injection PASSED [ 20%]
tests/test_game_session.py::test_constructor_custom_high_score_path PASSED [ 20%]
tests/test_game_session.py::test_move_full_orchestration PASSED          [ 20%]
tests/test_game_session.py::test_move_orchestration_calls_all_subsystems PASSED [ 20%]
tests/test_game_session.py::test_move_records_history_before_slide PASSED [ 21%]
tests/test_game_session.py::test_move_syncs_score PASSED                 [ 21%]
tests/test_game_session.py::test_move_result_fields PASSED               [ 21%]
tests/test_game_session.py::test_move_illegal_no_side_effects PASSED     [ 21%]
tests/test_game_session.py::test_move_triggers_achievements PASSED       [ 22%]
tests/test_game_session.py::test_undo_restores_board_and_score PASSED    [ 22%]
tests/test_game_session.py::test_undo_empty_history_returns_false PASSED [ 22%]
tests/test_game_session.py::test_undo_multiple_consecutive PASSED        [ 22%]
tests/test_game_session.py::test_undo_preserves_high_score PASSED        [ 23%]
tests/test_game_session.py::test_undo_does_not_revert_achievements PASSED [ 23%]
tests/test_game_session.py::test_new_game_resets_all_state PASSED        [ 23%]
tests/test_game_session.py::test_new_game_spawns_two_tiles PASSED        [ 23%]
tests/test_game_session.py::test_new_game_mid_game PASSED                [ 24%]
tests/test_game_session.py::test_game_over_no_rotten PASSED              [ 24%]
tests/test_game_session.py::test_game_over_with_rotten PASSED            [ 24%]
tests/test_game_session.py::test_game_over_empty_board PASSED            [ 24%]
tests/test_game_session.py::test_game_over_consistency_after_undo PASSED [ 25%]
tests/test_game_session.py::test_move_after_game_over PASSED             [ 25%]
tests/test_game_session.py::test_move_full_board_spawn_skipped PASSED    [ 25%]
tests/test_game_session.py::test_save_serializes_all_state PASSED        [ 25%]
tests/test_game_session.py::test_load_restores_full_state PASSED         [ 25%]
tests/test_game_session.py::test_save_load_round_trip PASSED             [ 26%]
tests/test_game_session.py::test_save_load_empty_history PASSED          [ 26%]
tests/test_game_session.py::test_save_load_no_achievements PASSED        [ 26%]
tests/test_game_session.py::test_save_load_with_rotten_tiles PASSED      [ 26%]
tests/test_game_session.py::test_load_missing_keys_raises PASSED         [ 27%]
tests/test_game_session.py::test_no_pygame_imports_in_game_session PASSED [ 27%]
tests/test_game_session.py::test_accessor_get_board_grid_initial PASSED  [ 27%]
tests/test_game_session.py::test_accessor_get_score_initial PASSED       [ 27%]
tests/test_game_session.py::test_accessor_get_high_score_initial PASSED  [ 28%]
tests/test_game_session.py::test_accessor_get_move_count_initial PASSED  [ 28%]
tests/test_game_session.py::test_accessor_get_rotten_overlay_initial PASSED [ 28%]
tests/test_game_session.py::test_accessor_can_undo_initial PASSED        [ 28%]
tests/test_game_session.py::test_accessor_post_move_state PASSED         [ 29%]
tests/test_game_session.py::test_accessor_grid_defensive_copy PASSED     [ 29%]
tests/test_game_session.py::test_accessor_overlay_defensive_copy PASSED  [ 29%]
tests/test_game_session.py::test_accessor_score_reflects_delta PASSED    [ 29%]
tests/test_game_session.py::test_accessor_can_undo_transition PASSED     [ 30%]
tests/test_game_session.py::test_accessor_high_score_persists_after_undo PASSED [ 30%]
tests/test_game_session.py::test_accessor_type_correctness PASSED        [ 30%]
tests/test_game_session.py::test_move_returns_tile_moves PASSED          [ 30%]
tests/test_game_session.py::test_move_illegal_returns_empty_tile_moves PASSED [ 31%]
tests/test_high001_fix.py::test_high001_attribute_access_grid PASSED     [ 31%]
tests/test_high001_fix.py::test_high001_attribute_access_score PASSED    [ 31%]
tests/test_high001_fix.py::test_high001_all_directions_attribute_access PASSED [ 31%]
tests/test_high001_fix.py::test_board_grid_property_exists PASSED        [ 32%]
tests/test_high001_fix.py::test_board_grid_satisfies_protocol PASSED     [ 32%]
tests/test_history.py::test_history_initial_state_can_undo_false PASSED  [ 32%]
tests/test_history.py::test_history_initial_state_pop_returns_none PASSED [ 32%]
tests/test_history.py::test_history_push_one_then_pop_returns_it PASSED  [ 33%]
tests/test_history.py::test_history_push_two_then_pop_returns_lifo_order PASSED [ 33%]
tests/test_history.py::test_history_max_depth_1_keeps_only_last PASSED   [ 33%]
tests/test_history.py::test_history_max_depth_3_with_5_pushes_keeps_last_3 PASSED [ 33%]
tests/test_history.py::test_history_max_depth_0_allows_unlimited_pushes PASSED [ 33%]
tests/test_history.py::test_history_pop_after_push_to_limit_discards_oldest PASSED [ 34%]
tests/test_history.py::test_history_deep_copy_isolation PASSED           [ 34%]
tests/test_history.py::test_history_push_none_raises_type_error PASSED   [ 34%]
tests/test_history.py::test_history_negative_max_depth_raises_value_error PASSED [ 34%]
tests/test_history.py::test_undo_returns_pushed_state PASSED             [ 35%]
tests/test_history.py::test_undo_empty_history_returns_none PASSED       [ 35%]
tests/test_history.py::test_multiple_undos_restore_initial_state PASSED  [ 35%]
tests/test_history.py::test_undo_restores_score PASSED                   [ 35%]
tests/test_history.py::test_can_undo_reflects_stack_state PASSED         [ 36%]
tests/test_history.py::test_max_depth_enforced PASSED                    [ 36%]
tests/test_history.py::test_undo_deep_copy_independence PASSED           [ 36%]
tests/test_history.py::test_boardstate_with_rotten_overlay_roundtrip PASSED [ 36%]
tests/test_history.py::test_record_alias_equivalence PASSED              [ 37%]
tests/test_input_handler.py::test_arrow_key_returns_direction PASSED     [ 37%]
tests/test_input_handler.py::test_non_arrow_key_returns_none PASSED      [ 37%]
tests/test_input_handler.py::test_handle_keydown_arrow_calls_session_move PASSED [ 37%]
tests/test_input_handler.py::test_handle_keydown_arrow_ignored_in_game_over PASSED [ 38%]
tests/test_input_handler.py::test_handle_keydown_idle_transitions_to_playing PASSED [ 38%]
tests/test_input_handler.py::test_handle_keydown_snap_during_animation PASSED [ 38%]
tests/test_input_handler.py::test_handle_keydown_no_snap_when_not_animating PASSED [ 38%]
tests/test_input_handler.py::test_handle_keydown_z_calls_undo PASSED     [ 39%]
tests/test_input_handler.py::test_handle_keydown_space_starts_new_game PASSED [ 39%]
tests/test_input_handler.py::test_handle_mouse_click_inside_button PASSED [ 39%]
tests/test_input_handler.py::test_handle_mouse_click_outside_button PASSED [ 39%]
tests/test_input_handler.py::test_handle_mouse_click_ignored_in_playing PASSED [ 40%]
tests/test_integration.py::test_full_game_lifecycle PASSED               [ 40%]
tests/test_integration.py::test_save_load_roundtrip PASSED               [ 40%]
tests/test_integration.py::test_twist_contamination_end_to_end PASSED    [ 40%]
tests/test_integration.py::test_score_pipeline PASSED                    [ 41%]
tests/test_integration.py::test_undo_pipeline PASSED                     [ 41%]
tests/test_integration.py::test_achievement_unlock_through_gameplay PASSED [ 41%]
tests/test_integration.py::test_game_over_detection PASSED               [ 41%]
tests/test_integration.py::test_game_over_not_triggered_with_rotten PASSED [ 41%]
tests/test_integration.py::test_new_game_resets_all_state PASSED         [ 42%]
tests/test_integration.py::test_full_state_restoration_with_twist_overlay PASSED [ 42%]
tests/test_integration.py::test_asset_loader_mock_returns_sprites_for_all_tile_values PASSED [ 42%]
tests/test_integration.py::test_renderer_render_completes_without_error PASSED [ 42%]
tests/test_integration.py::test_get_new_game_button_rect_returns_valid_tuple PASSED [ 43%]
tests/test_integration.py::test_game_session_state_visible_to_renderer PASSED [ 43%]
tests/test_integration.py::test_all_modules_importable_without_pygame PASSED [ 43%]
tests/test_main.py::test_game_state_enum_has_exactly_four_values PASSED  [ 43%]
tests/test_main.py::test_get_new_game_button_rect_returns_positive_tuple PASSED [ 44%]
tests/test_main.py::test_arrow_key_dispatches_direction_to_move PASSED   [ 44%]
tests/test_main.py::test_escape_quits_in_all_states PASSED               [ 44%]
tests/test_main.py::test_z_key_calls_undo_when_can_undo_true PASSED      [ 44%]
tests/test_main.py::test_z_key_does_not_call_undo_when_can_undo_false PASSED [ 45%]
tests/test_main.py::test_new_game_button_click_calls_new_game PASSED     [ 45%]
tests/test_main.py::test_click_outside_button_does_nothing PASSED        [ 45%]
tests/test_main.py::test_game_over_transition_after_move PASSED          [ 45%]
tests/test_main.py::test_win_transition_when_2048_tile_exists PASSED     [ 46%]
tests/test_main.py::test_check_win_returns_true_for_2048 PASSED          [ 46%]
tests/test_main.py::test_check_win_returns_true_for_value_above_2048 PASSED [ 46%]
tests/test_main.py::test_check_win_returns_false_for_no_2048 PASSED      [ 46%]
tests/test_main.py::test_full_render_cycle_no_exception PASSED           [ 47%]
tests/test_main.py::test_no_pygame_imports_in_core PASSED                [ 47%]
tests/test_main.py::test_space_key_starts_new_game_in_game_over PASSED   [ 47%]
tests/test_main.py::test_space_key_starts_new_game_in_win PASSED         [ 47%]
tests/test_main.py::test_idle_transitions_to_playing_on_first_move PASSED [ 48%]
tests/test_main.py::test_arrow_key_ignored_in_game_over PASSED           [ 48%]
tests/test_main.py::test_arrow_key_ignored_in_win PASSED                 [ 48%]
tests/test_main.py::test_space_key_ignored_in_playing PASSED             [ 48%]
tests/test_main.py::test_space_key_ignored_in_idle PASSED                [ 49%]
tests/test_main.py::test_undo_ignored_in_non_playing PASSED              [ 49%]
tests/test_main.py::test_handle_keydown_returns_new_achievements PASSED  [ 49%]
tests/test_main.py::test_game_window_creates_toast_manager PASSED        [ 49%]
tests/test_main.py::test_handle_keydown_enqueues_toasts_for_new_achievements PASSED [ 50%]
tests/test_main.py::test_render_calls_toast_update_and_render PASSED     [ 50%]
tests/test_main.py::test_new_game_clears_toasts PASSED                   [ 50%]
tests/test_merge_celebration.py::test_merge_celebration_effect_fields PASSED [ 50%]
tests/test_merge_celebration.py::test_golden_glow_alpha_decay PASSED     [ 50%]
tests/test_merge_celebration.py::test_score_popup_floats_upward PASSED   [ 51%]
tests/test_merge_celebration.py::test_update_removes_expired_effects PASSED [ 51%]
tests/test_merge_celebration.py::test_renderer_celebration_layer_order PASSED [ 51%]
tests/test_merge_celebration.py::test_no_pygame_at_import_time PASSED    [ 51%]
tests/test_merge_celebration.py::test_is_merge_destination_returns_true PASSED [ 52%]
tests/test_merge_celebration.py::test_celebration_effects_none_no_render PASSED [ 52%]
tests/test_merge_celebration.py::test_glow_surface_blitted_at_correct_position PASSED [ 52%]
tests/test_merge_celebration.py::test_multiple_concurrent_effects PASSED [ 52%]
tests/test_phase4_components.py::TestAnimationManagerExists::test_import PASSED [ 53%]
tests/test_phase4_components.py::TestAnimationManagerExists::test_has_start_animation PASSED [ 53%]
tests/test_phase4_components.py::TestAnimationManagerExists::test_has_get_pixel_offset PASSED [ 53%]
tests/test_phase4_components.py::TestAnimationManagerExists::test_has_is_animating PASSED [ 53%]
tests/test_phase4_components.py::TestToastManagerExists::test_import PASSED [ 54%]
tests/test_phase4_components.py::TestToastManagerExists::test_has_show PASSED [ 54%]
tests/test_phase4_components.py::TestToastManagerExists::test_has_render PASSED [ 54%]
tests/test_phase4_components.py::TestMergeCelebrationExists::test_import PASSED [ 54%]
tests/test_phase4_components.py::TestMergeCelebrationExists::test_is_dataclass PASSED [ 55%]
tests/test_phase4_components.py::TestConstants::test_animation_duration PASSED [ 55%]
tests/test_phase4_components.py::TestConstants::test_toast_default_duration PASSED [ 55%]
tests/test_phase4_components.py::TestConstants::test_toast_fade_duration PASSED [ 55%]
tests/test_phase4_components.py::TestRendererExists::test_import PASSED  [ 56%]
tests/test_phase4_components.py::TestRendererExists::test_has_get_new_game_button_rect PASSED [ 56%]
tests/test_phase4_components.py::TestWindowChrome::test_no_noframe_in_main PASSED [ 56%]
tests/test_render_layout.py::test_boardlayout_default_dimensions PASSED  [ 56%]
tests/test_render_layout.py::test_boardlayout_cell_size_is_positive_integer PASSED [ 57%]
tests/test_render_layout.py::test_boardlayout_computed_fields PASSED     [ 57%]
tests/test_render_layout.py::test_boardlayout_all_fields_are_integers PASSED [ 57%]
tests/test_render_layout.py::test_cell_rect_origin PASSED                [ 57%]
tests/test_render_layout.py::test_cell_rect_bottom_right PASSED          [ 58%]
tests/test_render_layout.py::test_cell_rect_returns_tuple_of_four PASSED [ 58%]
tests/test_render_layout.py::test_board_rect PASSED                      [ 58%]
tests/test_render_layout.py::test_tile_sprites_has_11_entries PASSED     [ 58%]
tests/test_render_layout.py::test_tile_sprites_filenames_match_disk PASSED [ 59%]
tests/test_render_layout.py::test_ui_sprite_names_has_8_entries PASSED   [ 59%]
tests/test_render_layout.py::test_mascot_states_has_3_entries PASSED     [ 59%]
tests/test_render_layout.py::test_tile_sprites_filenames_exist_on_disk PASSED [ 59%]
tests/test_render_layout.py::test_mascot_states_filenames_exist_on_disk PASSED [ 59%]
tests/test_render_layout.py::test_ui_sprite_names_filenames_exist_on_disk PASSED [ 60%]
tests/test_render_layout.py::test_all_sprite_filenames_exist_on_disk PASSED [ 60%]
tests/test_render_layout.py::test_init_exports_boardlayout PASSED        [ 60%]
tests/test_render_layout.py::test_init_all_contains_three_names PASSED   [ 60%]
tests/test_renderer.py::test_constructor_stores_asset_loader PASSED      [ 61%]
tests/test_renderer.py::test_constructor_stores_layout PASSED            [ 61%]
tests/test_renderer.py::test_render_blits_background_wallpaper_first PASSED [ 61%]
tests/test_renderer.py::test_render_blits_board_background_second PASSED [ 62%]
tests/test_renderer.py::test_render_empty_cell_blits_cell_empty_sprite PASSED [ 62%]
tests/test_renderer.py::test_render_tile_sprite_at_correct_position PASSED [ 62%]
tests/test_renderer.py::test_render_rotten_overlay_normal_for_countdown_ge_2 PASSED [ 62%]
tests/test_renderer.py::test_render_rotten_overlay_warning_for_countdown_eq_1 PASSED [ 63%]
tests/test_renderer.py::test_render_no_rotten_overlay_for_value_0 PASSED [ 63%]
tests/test_renderer.py::test_render_score_text_via_font PASSED           [ 63%]
tests/test_renderer.py::test_render_uses_asset_loader_for_images PASSED  [ 63%]
tests/test_renderer.py::test_render_uses_board_layout_for_positioning PASSED [ 63%]
tests/test_renderer.py::test_render_title_logo_at_top PASSED             [ 64%]
tests/test_renderer.py::test_render_mascot_beside_title PASSED           [ 64%]
tests/test_renderer.py::test_render_session_integration_calls_all_methods PASSED [ 64%]
tests/test_renderer.py::test_render_handles_empty_board_no_errors PASSED [ 64%]
tests/test_renderer.py::test_render_rotten_overlay_3_uses_normal PASSED  [ 65%]
tests/test_renderer.py::test_render_mixed_board_correct_sprite_per_cell PASSED [ 65%]
tests/test_renderer.py::test_idle_state_blits_idle_mascot PASSED         [ 65%]
tests/test_renderer.py::test_playing_state_blits_idle_mascot PASSED      [ 65%]
tests/test_renderer.py::test_game_over_state_blits_worried_mascot PASSED [ 66%]
tests/test_renderer.py::test_win_state_blits_happy_mascot PASSED         [ 66%]
tests/test_renderer.py::test_default_game_state_blits_idle_mascot PASSED [ 66%]
tests/test_renderer.py::test_rotten_overlay_blits_sprites_at_valid_positions PASSED [ 66%]
tests/test_renderer.py::test_rotten_overlay_skips_out_of_bounds_cells PASSED [ 66%]
tests/test_renderer.py::test_score_text_blitted_at_bottom_center PASSED  [ 67%]
tests/test_renderer.py::test_render_accepts_new_kwargs PASSED            [ 67%]
tests/test_renderer.py::test_params_have_correct_defaults PASSED         [ 67%]
tests/test_renderer.py::test_layer_6_order_overlay_score_button PASSED   [ 67%]
tests/test_renderer.py::test_mascot_worried_when_playing_with_rotten_overlay PASSED [ 68%]
tests/test_renderer.py::test_win_overlay_blitted_on_win_state PASSED     [ 68%]
tests/test_renderer.py::test_mascot_fallback_on_key_error PASSED         [ 68%]
tests/test_renderer.py::test_no_overlay_blitted_during_idle PASSED       [ 68%]
tests/test_renderer.py::test_main_render_has_no_overlay_blit_code PASSED [ 69%]
tests/test_rules.py::test_import_rules_module PASSED                     [ 69%]
tests/test_rules.py::test_is_move_legal_left_merges PASSED               [ 69%]
tests/test_rules.py::test_is_move_legal_left_no_change PASSED            [ 69%]
tests/test_rules.py::test_is_move_legal_right PASSED                     [ 70%]
tests/test_rules.py::test_is_move_legal_right_no_change PASSED           [ 70%]
tests/test_rules.py::test_is_move_legal_empty_board PASSED               [ 70%]
tests/test_rules.py::test_is_move_legal_up_and_down PASSED               [ 70%]
tests/test_rules.py::test_get_legal_moves_returns_empty_for_empty PASSED [ 70%]
tests/test_rules.py::test_get_legal_moves_returns_directions PASSED      [ 71%]
tests/test_rules.py::test_get_legal_moves_returns_empty_when_no_legal PASSED [ 71%]
tests/test_rules.py::test_is_game_over_true_when_no_moves PASSED         [ 71%]
tests/test_rules.py::test_is_game_over_false_when_empty_cells PASSED     [ 71%]
tests/test_rules.py::test_is_game_over_false_when_merges_possible PASSED [ 72%]
tests/test_rules.py::test_is_game_over_invariant PASSED                  [ 72%]
tests/test_rules.py::test_is_game_over_has_rotten_prevents_over PASSED   [ 72%]
tests/test_rules.py::test_slide_merge_from_board_returns_correct_fields PASSED [ 72%]
tests/test_rules.py::test_rules_direction_is_board_direction PASSED      [ 73%]
tests/test_rules.py::test_rotten_tile_at_center_full_board_prevents_over PASSED [ 73%]
tests/test_rules.py::test_rotten_tile_at_corner_full_board_prevents_over PASSED [ 73%]
tests/test_rules.py::test_rotten_tile_at_edge_full_board_prevents_over PASSED [ 73%]
tests/test_rules.py::test_two_rotten_tiles_full_board_prevents_over PASSED [ 74%]
tests/test_rules.py::test_four_rotten_tiles_full_board_prevents_over PASSED [ 74%]
tests/test_rules.py::test_rotten_tile_non_full_board_not_over PASSED     [ 74%]
tests/test_rules.py::test_no_rotten_non_full_board_not_over PASSED       [ 74%]
tests/test_rules.py::test_full_no_merges_all_zeros_overlay_is_over PASSED [ 75%]
tests/test_rules.py::test_full_no_merges_no_overlay_support_is_over PASSED [ 75%]
tests/test_rules.py::test_mixed_countdowns_full_board_prevents_over PASSED [ 75%]
tests/test_rules.py::test_all_zero_overlay_behaves_as_no_rotten PASSED   [ 75%]
tests/test_rules.py::test_is_game_over_invariant_with_rotten PASSED      [ 75%]
tests/test_rules.py::test_rotten_overlay_full_no_merges_no_legal_moves PASSED [ 76%]
tests/test_rules.py::test_overlay_nonzero_but_has_empty_cells_not_over PASSED [ 76%]
tests/test_rules.py::test_has_rotten_fallback_without_overlay_method PASSED [ 76%]
tests/test_rules.py::test_overlay_inspection_overrides_has_rotten_false PASSED [ 76%]
tests/test_rules.py::test_rotten_all_corner_positions PASSED             [ 77%]
tests/test_rules.py::test_rotten_center_position PASSED                  [ 77%]
tests/test_rules.py::test_merges_possible_with_rotten_not_over PASSED    [ 77%]
tests/test_rules.py::test_stalemate_rescueable_same_value_pair_continues PASSED [ 77%]
tests/test_rules.py::test_no_rescueable_pair_game_over PASSED            [ 78%]
tests/test_rules.py::test_stalemate_adjacent_different_values_not_rescueable PASSED [ 78%]
tests/test_rules.py::test_stalemate_diagonal_rotten_not_rescueable PASSED [ 78%]
tests/test_rules.py::test_stalemate_rescueable_at_all_positions PASSED   [ 78%]
tests/test_rules.py::test_stalemate_multiple_rotten_one_rescueable_pair PASSED [ 79%]
tests/test_rules.py::test_overlay_is_readonly PASSED                     [ 79%]
tests/test_rules.py::test_rescueable_pair_with_various_countdowns PASSED [ 79%]
tests/test_score.py::test_score_initial_score_is_zero PASSED             [ 79%]
tests/test_score.py::test_score_add_accumulates PASSED                   [ 80%]
tests/test_score.py::test_score_reset_clears_current PASSED              [ 80%]
tests/test_score.py::test_score_reset_preserves_high_score_on_disk PASSED [ 80%]
tests/test_score.py::test_high_score_persists_to_json PASSED             [ 80%]
tests/test_score.py::test_high_score_loads_from_json PASSED              [ 81%]
tests/test_score.py::test_high_score_missing_file_returns_zero PASSED    [ 81%]
tests/test_score.py::test_high_score_auto_updates PASSED                 [ 81%]
tests/test_score.py::test_high_score_does_not_decrease PASSED            [ 81%]
tests/test_score.py::test_corrupt_json_returns_zero PASSED               [ 82%]
tests/test_score.py::test_corrupt_structure_returns_zero PASSED          [ 82%]
tests/test_score.py::test_non_integer_value_returns_zero PASSED          [ 82%]
tests/test_score.py::test_save_creates_directory PASSED                  [ 82%]
tests/test_sprint_4_2_integration.py::test_toast_integrates_with_move_result_achievements PASSED [ 83%]
tests/test_sprint_4_2_integration.py::test_renderer_completes_with_active_moves PASSED [ 83%]
tests/test_sprint_4_2_integration.py::test_renderer_renders_celebration_effects PASSED [ 83%]
tests/test_sprint_4_2_integration.py::test_toast_and_animation_coexist PASSED [ 83%]
tests/test_sprint_4_2_integration.py::test_toast_renders_during_game_over PASSED [ 83%]
tests/test_sprint_4_2_integration.py::test_toast_clear_on_new_game PASSED [ 84%]
tests/test_sprint_4_2_rem.py::test_celebration_effects_created_on_merge PASSED [ 84%]
tests/test_sprint_4_2_rem.py::test_celebration_effects_updated_each_frame PASSED [ 84%]
tests/test_sprint_4_2_rem.py::test_celebration_effects_passed_to_renderer PASSED [ 84%]
tests/test_sprint_4_2_rem.py::test_celebration_effects_cleared_on_new_game PASSED [ 85%]
tests/test_sprint_4_2_rem.py::test_celebration_effects_cleared_on_mouse_new_game PASSED [ 85%]
tests/test_sprint_4_2_remediation.py::test_celebration_effects_created_for_merged_moves PASSED [ 85%]
tests/test_sprint_4_2_remediation.py::test_renderer_called_with_celebration_effects PASSED [ 85%]
tests/test_sprint_4_2_remediation.py::test_celebration_effects_cleared_on_new_game PASSED [ 86%]
tests/test_sprint_4_2_remediation.py::test_sprite_cache_smooth_scale PASSED [ 86%]
tests/test_sprint_4_2_remediation.py::test_sprite_cache_no_pygame_at_import PASSED [ 86%]
tests/test_state_manager.py::test_initial_state_is_idle PASSED           [ 86%]
tests/test_state_manager.py::test_custom_initial_state PASSED            [ 87%]
tests/test_state_manager.py::test_transition_to_changes_state PASSED     [ 87%]
tests/test_state_manager.py::test_check_win_condition_transitions_to_win PASSED [ 87%]
tests/test_state_manager.py::test_check_win_condition_transitions_to_game_over PASSED [ 87%]
tests/test_state_manager.py::test_check_win_condition_noop_in_non_playing PASSED [ 88%]
tests/test_state_manager.py::test_is_input_allowed PASSED                [ 88%]
tests/test_state_manager.py::test_is_new_game_allowed PASSED             [ 88%]
tests/test_state_manager.py::test_is_undo_allowed PASSED                 [ 88%]
tests/test_toast_manager.py::test_enqueue_adds_to_queue PASSED           [ 89%]
tests/test_toast_manager.py::test_empty_state PASSED                     [ 89%]
tests/test_toast_manager.py::test_clear_removes_all PASSED               [ 89%]
tests/test_toast_manager.py::test_update_decrements_timer PASSED         [ 89%]
tests/test_toast_manager.py::test_fade_out_begins_after_duration PASSED  [ 90%]
tests/test_toast_manager.py::test_sequential_display PASSED              [ 90%]
tests/test_toast_manager.py::test_render_draws_panel PASSED              [ 90%]
tests/test_toast_manager.py::test_no_pygame_import_at_module_level PASSED [ 90%]
tests/test_toast_manager.py::test_toast_y_position_le_50 PASSED          [ 91%]
tests/test_toast_positioning.py::test_toast_panel_within_visible_window PASSED [ 91%]
tests/test_toast_positioning.py::test_toast_panel_horizontally_centered PASSED [ 91%]
tests/test_twist.py::test_twist_import PASSED                            [ 91%]
tests/test_twist.py::test_twist_constructor_defaults PASSED              [ 91%]
tests/test_twist.py::test_overlay_initial_state PASSED                   [ 92%]
tests/test_twist.py::test_get_overlay_returns_copy PASSED                [ 92%]
tests/test_twist.py::test_is_rotten_and_get_countdown PASSED             [ 92%]
tests/test_twist.py::test_countdown_decrements_each_move PASSED          [ 92%]
tests/test_twist.py::test_countdown_does_not_go_below_zero PASSED        [ 93%]
tests/test_twist.py::test_expired_countdown_contaminates_adjacent PASSED [ 93%]
tests/test_twist.py::test_contamination_picks_one_adjacent PASSED        [ 93%]
tests/test_twist.py::test_contamination_skips_when_no_valid_target PASSED [ 93%]
tests/test_twist.py::test_spawn_new_rotten_on_interval PASSED            [ 94%]
tests/test_twist.py::test_spawn_skips_when_board_full PASSED             [ 94%]
tests/test_twist.py::test_tunable_spawn_interval PASSED                  [ 94%]
tests/test_twist.py::test_rotten_merges_rotten_removes_both PASSED       [ 94%]
tests/test_twist.py::test_rotten_does_not_merge_with_healthy PASSED      [ 95%]
tests/test_twist.py::test_rotten_merges_different_value_no_removal PASSED [ 95%]
tests/test_twist.py::test_board_spawn_tile PASSED                        [ 95%]
tests/test_twist.py::test_board_get_empty_cells PASSED                   [ 95%]
tests/test_twist.py::test_board_get_neighbors_corner PASSED              [ 96%]
tests/test_twist.py::test_board_get_state_set_state_roundtrip PASSED     [ 96%]
tests/test_twist.py::test_multiple_expirations_in_same_move PASSED       [ 96%]
tests/test_twist.py::test_contamination_avoids_empty_cells PASSED        [ 96%]
tests/test_visual_proof_manifest.py::test_readme_covers_all_pngs PASSED  [ 97%]
tests/test_visual_proof_manifest.py::test_readme_covers_all_pngs_has_count PASSED [ 97%]
tests/test_visual_proof_manifest.py::test_readme_has_viewing_instructions PASSED [ 97%]
tests/test_visual_proof_readme.py::test_readme_file_exists PASSED        [ 97%]
tests/test_visual_proof_readme.py::test_readme_contains_pass_ten_times PASSED [ 98%]
tests/test_visual_proof_readme.py::test_readme_contains_all_section_headings PASSED [ 98%]
tests/test_visual_proof_readme.py::test_readme_contains_launch_command PASSED [ 98%]
tests/test_visual_proof_readme.py::test_readme_contains_screenshot_reference PASSED [ 98%]
tests/test_visual_proof_readme.py::test_readme_contains_arrow_controls PASSED [ 99%]
tests/test_visual_proof_readme.py::test_readme_contains_escape PASSED    [ 99%]
tests/test_visual_proof_readme.py::test_readme_contains_undo_key PASSED  [ 99%]
tests/test_window_flags.py::test_no_noframe_flag_in_main PASSED          [ 99%]
tests/test_window_flags.py::test_set_mode_called_with_only_size_tuple PASSED [100%]

============================= 412 passed in 0.81s ==============================
```

---

## Source Integrity Check

Verified that no source files under `src/` were modified during Phase 5.

- **Command**: `git diff --name-only`
- **Result**: No output (clean working tree). No `src/` modifications detected.

- **Command**: `git diff --name-only --cached`
- **Result**: No output (no staged changes). No `src/` modifications detected.

- **Conclusion**: Source integrity is **CLEAN**. ADR-030 compliance confirmed.

---

## Regression Analysis

No regressions detected. All 412 tests pass with 0 failures.

Phase 5 documentation-only changes did not affect any test outcomes. The test suite
covers:

- **28 test files** spanning achievements, animation, asset loading, board logic,
  game session orchestration, history/undo, input handling, integration, main loop,
  merge celebration, rendering, rules/game-over, scoring, state management, twist
  mechanics, toast notifications, visual proof manifests, and window flags.

### Per-Module Breakdown

| Module | Tests | Status |
|--------|-------|--------|
| test_achievements | 19 | All PASS |
| test_animation_integration | 6 | All PASS |
| test_animation_manager | 10 | All PASS |
| test_asset_loader | 14 | All PASS |
| test_board | 28 | All PASS |
| test_first_light | 3 | All PASS |
| test_game_session | 48 | All PASS |
| test_high001_fix | 5 | All PASS |
| test_history | 20 | All PASS |
| test_input_handler | 12 | All PASS |
| test_integration | 15 | All PASS |
| test_main | 28 | All PASS |
| test_merge_celebration | 10 | All PASS |
| test_phase4_components | 15 | All PASS |
| test_render_layout | 18 | All PASS |
| test_renderer | 34 | All PASS |
| test_rules | 44 | All PASS |
| test_score | 13 | All PASS |
| test_sprint_4_2_integration | 6 | All PASS |
| test_sprint_4_2_rem | 5 | All PASS |
| test_sprint_4_2_remediation | 5 | All PASS |
| test_state_manager | 9 | All PASS |
| test_toast_manager | 9 | All PASS |
| test_toast_positioning | 2 | All PASS |
| test_twist | 22 | All PASS |
| test_visual_proof_manifest | 3 | All PASS |
| test_visual_proof_readme | 8 | All PASS |
| test_window_flags | 2 | All PASS |

### Comparison with Phase 4 Baseline

| Metric | Phase 4 (Sprint 4) | Phase 5 (This Run) | Delta |
|--------|--------------------|--------------------|-------|
| Total tests | 412 | 412 | 0 |
| Passed | 412 | 412 | 0 |
| Failed | 0 | 0 | 0 |
| Exit code | 0 | 0 | 0 |

No test count growth or regression since Phase 4 completion.

---

## Conclusion

**PASS** -- Phase 5 Sprint 1 Task 3 regression gate is satisfied.

- All 412 tests pass with 0 failures and exit code 0.
- No source files under `src/` were modified (ADR-030 compliance confirmed).
- No regressions introduced by Phase 5 documentation-only changes.
- The regression report has been committed to the repository.