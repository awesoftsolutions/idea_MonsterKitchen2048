"""Run pytest with SDL headless, capture output, and render as ci-green.png."""
import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# ── run pytest ────────────────────────────────────────────────────────────
env = os.environ.copy()
env["SDL_VIDEODRIVER"] = "offscreen"
env["SDL_AUDIODRIVER"] = "dummy"

proc = subprocess.run(
    [sys.executable, "-m", "pytest", "-v", "--tb=short", "--no-header"],
    capture_output=True,
    text=True,
    cwd=PROJECT_ROOT,
    env=env,
)

stdout = proc.stdout or ""
stderr = proc.stderr or ""
output = stdout + stderr

# ── summary lines ─────────────────────────────────────────────────────────
total = passed = failed = skipped = 0
for line in output.splitlines():
    if " passed" in line or " failed" in line or " error" in line:
        parts = line.split()
        for i, p in enumerate(parts):
            try:
                n = int(p)
            except ValueError:
                continue
            if i + 1 < len(parts):
                tag = parts[i + 1]
                if "passed" in tag:
                    total += n
                    passed += n
                elif "failed" in tag:
                    total += n
                    failed += n
                elif "skipped" in tag or "deselected" in tag:
                    skipped += n
summary_line = f"{passed} passed"
if failed:
    summary_line += f", {failed} failed"
if skipped:
    summary_line += f", {skipped} skipped"

# ── Keep only colour-free last 30 lines ───────────────────────────────────
raw_lines = output.splitlines()
keep = raw_lines[-30:]

# ── Remove ANSI escape codes ─────────────────────────────────────────────
import re  # noqa: E402
_ansi = re.compile(r"\x1b\[[0-9;]*m")
keep = [_ansi.sub("", ln) for ln in keep]

# ── Render PNG ────────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("PIL not available", file=sys.stderr)
    sys.exit(1)

W, H = 900, 720
im = Image.new("RGB", (W, H), (24, 24, 24))
d = ImageDraw.Draw(im)

def font(size=17, bold=False):
    names = [
        "c:/windows/fonts/consolab.ttf" if bold else "c:/windows/fonts/consola.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for n in names:
        if os.path.exists(n):
            return ImageFont.truetype(n, size)
    return ImageFont.load_default()

fH   = font(23, bold=True)
fBig = font(18, bold=True)
fReg = font(16)
fSm  = font(14)

# ── Header bar ────────────────────────────────────────────────────────────
d.rectangle([0, 0, W - 1, 90], fill=(94, 0, 14))
d.text((24, 20), "Monster Kitchen 2048  —  CI Verification", fill=(50, 217, 57), font=fH)
passed = proc.returncode == 0
badge_label = "ALL TESTS PASSED" if passed else "TESTS FAILED"
badge_color = (46, 204, 113) if passed else (231, 76, 60)
d.rounded_rectangle([W - 220, 20, W - 18, 58], fill=badge_color, radius=10)
d.text((W - 217, 24), f"  {badge_label}  ", fill=(255, 255, 255), font=fBig)

# ── Sub-header ────────────────────────────────────────────────────────────
d.text((24, 66), f"pytest exit code: {proc.returncode}   |   {summary_line}",
       fill=(180, 180, 180), font=fSm)

# ── Test output ───────────────────────────────────────────────────────────
y = 105
for line in keep:
    line = "".join(ch for ch in line if ch.isprintable() or ch == " ")
    fill = (220, 220, 220)
    if "PASSED" in line:
        fill = (46, 204, 113)
    elif "FAILED" in line or "ERROR" in line:
        fill = (231, 76, 60)
    elif "========" in line:
        fill = (140, 140, 140)
    d.text((14, y), line[:130], fill=fill, font=fReg)
    y += 18
    if y > H - 60:
        break

# ── Footer ────────────────────────────────────────────────────────────────
d.rectangle([0, H - 42, W, H], fill=(38, 38, 38))
d.text((18, H - 34),
       f"poetry run pytest   |   Python {sys.version.split()[0]}   |   SDL_VIDEODRIVER=offscreen   |   Exit {proc.returncode}",
       fill=(160, 160, 160), font=fSm)

out = os.path.join(SCRIPT_DIR, "ci-green.png")
im.save(out)
print(f"Saved {out}  exit_code={proc.returncode}  passed={passed}  total={total}")
sys.exit(0 if passed else 1)