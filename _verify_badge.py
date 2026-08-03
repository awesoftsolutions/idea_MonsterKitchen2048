"""Verify CI badge markdown syntax for the2048 README."""
import re
import sys

badge = '[![CI](https://github.com/Favur/the2048/actions/workflows/ci.yml/badge.svg)](https://github.com/Favur/the2048/actions/workflows/ci.yml)'

checks = {}

# 1. Bracket balance
checks["brackets_balanced"] = badge.count('[') == badge.count(']') == 2
checks["parens_balanced"] = badge.count('(') == badge.count(')') == 2

# 2. Image URL
expected_img = "https://github.com/Favur/the2048/actions/workflows/ci.yml/badge.svg"
checks["image_url_correct"] = expected_img in badge

# 3. Link URL
expected_link = "https://github.com/Favur/the2048/actions/workflows/ci.yml/"
checks["link_url_correct"] = expected_link in badge or badge.rstrip(')').endswith('/ci.yml')

# Actually check exact link URL
exact_link = "https://github.com/Favur/the2048/actions/workflows/ci.yml"
checks["link_url_exact"] = badge.endswith(f"]({exact_link})")

# 4. No placeholders
checks["no_placeholders"] = not any(p in badge for p in ['<', '>', 'TODO', 'FIXME', 'PLACEHOLDER', '{', '}'])

# 5. Matches standard GitHub Actions badge pattern
pattern = r'\[!\[CI\]\(https://github\.com/Favur/the2048/actions/workflows/ci\.yml/badge\.svg\)\]\(https://github\.com/Favur/the2048/actions/workflows/ci\.yml\)$'
checks["pattern_match"] = bool(re.match(pattern, badge))
print(f"Badge: {badge}")
print()
pass_count = sum(1 for v in checks.values() if v)
total = len(checks)
for key, val in checks.items():
    status = "PASS" if val else "FAIL"
    print(f"  {status} {key}")
print(f"\n{pass_count}/{total} checks passed")
sys.exit(0 if pass_count == total else 1)