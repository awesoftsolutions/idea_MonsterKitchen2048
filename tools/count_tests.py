"""Count PASSED lines per test module in the regression report."""
import re
from collections import Counter

with open('docs/phase-5-test-regression-report.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_code = False
module_counts = Counter()
for line in lines:
    stripped = line.rstrip()
    if stripped.strip() == '```':
        in_code = not in_code
        continue
    if in_code and 'PASSED' in stripped:
        m = re.match(r'(tests/[^:]+)', stripped)
        if m:
            fname = m.group(1).replace('tests/', '').replace('.py', '')
            module_counts[fname] += 1

total = sum(module_counts.values())
print(f'Total PASSED: {total}')
print()
for mod in sorted(module_counts.keys()):
    print(f'{mod}: {module_counts[mod]}')