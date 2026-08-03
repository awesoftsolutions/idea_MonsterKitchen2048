"""Count tests per module from the real pytest --co -q output and verify table."""

# Real test list from poetry run pytest tests/ --co -q output
real_tests = []
import re
with open('docs/phase-5-test-regression-report.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# We'll parse the collected output from process output directly. Let me just 
# hardcode the counts from the --co -q output by extracting from the file.

# Actually, count PASSED lines from the embedded report, but also count from --co -q
# For embedded report PASSED, count test_rules carefully:
in_code = False
rules_passed = []
for line in lines:
    stripped = line.rstrip()
    if stripped.strip() == '```':
        in_code = not in_code
        continue
    if in_code and 'test_rules.py' in stripped and 'PASSED' in stripped:
        m = re.match(r'\s*(tests/test_rules\.py::.+?)\s+PASSED', stripped)
        if m:
            rules_passed.append(m.group(1))

print(f"test_rules PASSED lines in embedded output ({len(rules_passed)}):")
for t in rules_passed:
    print(f"  {t}")

# Check for test_is_move_legal_right_no_change vs test_is_move_legal_right
print("\n--- Checking for phantom test ---")
for t in rules_passed:
    if 'is_move_legal_right' in t:
        print(f"  Found: {t}")