"""Compare PASSED lines vs collected tests to find phantom."""
import re
from collections import Counter

with open('docs/phase-5-test-regression-report.md', 'r', encoding='utf-8') as f:
    report_lines = f.readlines()

# Extract PASSED test names from embedded pytest output
in_code = False
passed_tests = []
for line in report_lines:
    stripped = line.rstrip()
    if stripped.strip() == '```':
        in_code = not in_code
        continue
    if in_code and 'PASSED' in stripped:
        m = re.match(r'\s*(tests/.+?::.+?)\s+PASSED', stripped)
        if m:
            passed_tests.append(m.group(1))

print(f"Total PASSED lines: {len(passed_tests)}")

# Count per module
module_counts = Counter()
for t in passed_tests:
    mod = t.split('::')[0].replace('tests/', '').replace('.py', '')
    module_counts[mod] += 1

print("\nPer-module PASSED counts:")
for mod in sorted(module_counts.keys()):
    print(f"  {mod}: {module_counts[mod]}")

# Now check: which module in the table differs from the PASSED count?
table_corrected = {
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
    'test_rules': 44,
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

table_sum = sum(table_corrected.values())
print(f"\nTable sum (corrected): {table_sum}")

print("\nDiscrepancies (PASSED != table):")
for mod in sorted(set(list(module_counts.keys()) + list(table_corrected.keys()))):
    p = module_counts.get(mod, 0)
    t = table_corrected.get(mod, 0)
    if p != t:
        print(f"  {mod}: PASSED={p}, table={t}, diff={p-t}")

# Also check test_rules specifically for test_is_move_legal_right_no_change
print("\ntest_is_move_legal_right_no_change in report?")
found = False
for line in report_lines:
    if 'test_is_move_legal_right_no_change' in line:
        print(f"  YES: {line.rstrip()}")
        found = True
if not found:
    print("  NO - not found in report")

# Check which test in rules is extra
rules_passed = [t for t in passed_tests if 'test_rules.py' in t]
print(f"\ntest_rules PASSED ({len(rules_passed)}):")
for t in rules_passed:
    print(f"  {t}")