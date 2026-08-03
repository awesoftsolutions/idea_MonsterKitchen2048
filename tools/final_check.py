"""Final verification: read the corrected table from the report and sum it."""

with open('docs/phase-5-test-regression-report.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_table = False
counts = {}
for line in lines:
    stripped = line.strip()
    if stripped.startswith('| Module'):
        in_table = True
        continue
    if in_table and stripped.startswith('|---'):
        continue
    if in_table and stripped.startswith('|'):
        parts = [p.strip() for p in stripped.split('|') if p.strip()]
        if len(parts) >= 2:
            mod = parts[0]
            try:
                count = int(parts[1])
                counts[mod] = count
            except ValueError:
                pass
    elif in_table and not stripped.startswith('|'):
        in_table = False

total = sum(counts.values())
print(f"Table has {len(counts)} modules")
print(f"Table sum: {total}")
for mod, count in sorted(counts.items()):
    print(f"  {mod}: {count}")

# Also check "29 test files" or "28 test files"
for i, line in enumerate(lines):
    if 'test files' in line.lower() and 'spanning' in line.lower():
        print(f"\nLine {i+1}: {line.rstrip()}")
