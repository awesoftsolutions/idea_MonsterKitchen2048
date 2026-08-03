"""Check for duplicate PASSED lines and verify counts."""
import re
from collections import Counter

with open('docs/phase-5-test-regression-report.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_code = False
all_passed = []
for line in lines:
    stripped = line.rstrip()
    if stripped.strip() == '```':
        in_code = not in_code
        continue
    if in_code and 'PASSED' in stripped:
        m = re.match(r'tests/([^:]+::.+?)\s+PASSED', stripped)
        if m:
            all_passed.append(m.group(1))

# Check for duplicates
counter = Counter(all_passed)
duplicates = {k: v for k, v in counter.items() if v > 1}
if duplicates:
    print("DUPLICATES FOUND:")
    for name, count in duplicates.items():
        print(f"  {name}: {count} times")
else:
    print("No duplicates found")

print(f"\nTotal PASSED lines: {len(all_passed)}")
print(f"Unique test names: {len(counter)}")