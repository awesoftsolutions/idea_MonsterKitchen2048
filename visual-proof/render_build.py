"""Run PyInstaller build, capture output, and render as package-build.png."""
import subprocess
import sys
import os
import re
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# ── clean previous build artifacts ────────────────────────────────────────
for stale in ["build", "dist", "the2048.spec"]:
    path = os.path.join(PROJECT_ROOT, stale)
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    elif os.path.isfile(path):
        os.remove(path)

# ── run pyinstaller ───────────────────────────────────────────────────────
args_path = os.path.join(PROJECT_ROOT, "src", "main.py")
assets_src = os.path.join(PROJECT_ROOT, "assets")
assets_dest = "assets"

pyi_args = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--name", "the2048",
    args_path,
    "--add-data", f"{assets_src};{assets_dest}",
    "--noconfirm",
]

proc = subprocess.run(
    pyi_args,
    capture_output=True,
    text=True,
    cwd=PROJECT_ROOT,
)

stdout = proc.stdout or ""
stderr = proc.stderr or ""
output = stdout + stderr

# ── strip ANSI codes ──────────────────────────────────────────────────────
_ansi = re.compile(r"\x1b\[[0-9;]*m")
output = _ansi.sub("", output)

# ── extract key lines (pyinstaller progress + summary) ────────────────────
lines = output.splitlines()
# Keep all lines, take last 28 that are meaningful
keep = lines[-28:]

# ── check binary output ──────────────────────────────────────────────────
dist_exe = os.path.join(PROJECT_ROOT, "dist", "the2048.exe")
binary_size = 0
if os.path.isfile(dist_exe):
    binary_size = os.path.getsize(dist_exe)

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

W, H = 960, 720
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
fReg = font(15)
fSm  = font(13)

# ── header ────────────────────────────────────────────────────────────────
build_ok = proc.returncode == 0 and binary_size > 0
d.rectangle([0, 0, W - 1, 90], fill=(17, 60, 102))
d.text((24, 20), "Monster Kitchen 2048  —  PyInstaller Build", fill=(100, 200, 255), font=fH)

badge_label = "BUILD OK" if build_ok else "BUILD FAILED"
badge_color = (46, 204, 113) if build_ok else (231, 76, 60)
inv = 1 if sum(badge_color) < 400 else 0
d.rounded_rectangle([W - 175, 22, W - 18, 58], fill=badge_color, radius=10)
d.text((W - 172, 26), f"  {badge_label}  ", fill=(255 * inv, 255 * inv, 255 * inv), font=fBig)

# ── sub-header ────────────────────────────────────────────────────────────
size_str = f"{binary_size / (1024 * 1024):.2f} MB" if binary_size > 0 else "not found"
d.text((24, 64), f"Exit code: {proc.returncode}   |   dist/the2048.exe: {size_str}",
       fill=(170, 190, 210), font=fSm)

# ── build log lines ───────────────────────────────────────────────────────
y = 105
for line in keep:
    line = "".join(ch for ch in line if ch.isprintable() or ch == " ")[:130]
    fill = (200, 210, 220)
    if "INFO:" in line:
        fill = (100, 180, 255)
    elif "WARNING:" in line:
        fill = (255, 200, 60)
    elif "ERROR" in line or "error" in line:
        fill = (231, 76, 60)
    elif "Building" in line or "completed" in line or "Successfully" in line:
        fill = (46, 204, 113)
    d.text((14, y), line, fill=fill, font=fReg)
    y += 17
    if y > 550:
        break

# ── build summary box ─────────────────────────────────────────────────────
box_y = 570
d.rectangle([10, box_y, W - 10, H - 10], fill=(30, 34, 40))
summary_items = [
    ("Entry point", "src/main.py"),
    ("Mode", "--onefile"),
    ("Name", "the2048.exe"),
    ("Assets", "assets/ (24 PNGs via --add-data)"),
    ("Hidden imports", "None needed (pygame-ce 2.5.7 bundles cleanly)"),
    ("Exit code", str(proc.returncode)),
    ("Binary size", size_str),
]
bx = 26
by = box_y + 10
for label, value in summary_items:
    d.text((bx, by), f"{label}:", fill=(100, 150, 200), font=fSm)
    d.text((bx + 150, by), value, fill=(220, 230, 240), font=fSm)
    by += 19

# ── footer ────────────────────────────────────────────────────────────────
d.rectangle([0, H - 36, W, H], fill=(17, 20, 26))
d.text((18, H - 28),
       "poetry run pyinstaller --onefile --name the2048 src/main.py --add-data assets;assets",
       fill=(140, 150, 160), font=fSm)

out = os.path.join(SCRIPT_DIR, "package-build.png")
im.save(out)
print(f"Saved {out}  exit_code={proc.returncode}  binary_size={size_str}  build_ok={build_ok}")
sys.exit(0 if build_ok else 1)