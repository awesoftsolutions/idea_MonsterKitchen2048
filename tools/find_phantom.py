"""Find phantom test: a PASSED line in the report that doesn't exist in the --co -q output."""
import re

# Read the report to get PASSED tests
with open('docs/phase-5-test-regression-report.md', 'r', encoding='utf-8') as f:
    report_lines = f.readlines()

in_code = False
passed_tests = set()
for line in report_lines:
    stripped = line.rstrip()
    if stripped.strip() == '```':
        in_code = not in_code
        continue
    if in_code and 'PASSED' in stripped:
        m = re.match(r'\s*(tests/.+?::.+?)\s+PASSED', stripped)
        if m:
            passed_tests.add(m.group(1).strip())

# The real test list from --co -q output (parsed from read_process_output)
# I'll extract from the raw process output lines
real_tests = set()

# Read the tool output file - actually I'll parse from the text we already have
# Let me parse the --co -q output I saw earlier
with open('tools/real_tests.txt', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if '::' in line and 'tests/' in line:
            name = line.split('\r')[0].strip()
            real_tests.add(name)

print(f"PASSED in report: {len(passed_tests)}")
print(f"Collected (--co -q): {len(real_tests)}")

phantom = passed_tests - real_tests
missing = real_tests - passed_tests

if phantom:
    print("\nPHANTOM tests (in PASSED but NOT in collected):")
    for t in sorted(phantom):
        print(f"  {t}")

if missing:
    print("\nMISSING tests (in collected but NOT in PASSED):")
    for t in sorted(missing):
        print(f"  {t}")

if not phantom and not missing:
    print("\nNo discrepancies found!")