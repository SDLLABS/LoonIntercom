"""Test pictures for the screen demo (screen-demo.yaml).

demo-assets/  own work, published: front drawing (SVG rendered to PNG), spinner and bell animations
local-assets/ NOT published (Windows sample photos, optionally your own board photo): photos with and
              without dithering, a panning "video"

The display driver maps ESPHome's COLOR_ON (white) to black ink, so every picture is stored as its
negative. Run: python make_demo_assets.py
"""
import math
import os
import pathlib
import subprocess
import time

from PIL import Image, ImageDraw, ImageOps

HERE = pathlib.Path(__file__).parent
PUB = HERE / "demo-assets"
LOC = HERE / "local-assets"
PUB.mkdir(exist_ok=True)
LOC.mkdir(exist_ok=True)
PHOTO = r"C:\Windows\Web\Wallpaper\ThemeC\img28.jpg"
# the PUBLIC, anonymised drawing (MUSTERMANN), never the private one in entwurf/ with the real names
FRONT_SVG = next(p for p in (HERE.parent.parent / "hardware" / "front-sheet" / "layout-v5-bemasst.svg",  # in the repo
                             pathlib.Path.home() / "intercom" / "hardware" / "front-sheet" / "layout-v5-bemasst.svg")
                 if p.exists())
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def neg(im):
    return ImageOps.invert(im.convert("L"))


def to16(im, dither):
    """Reduce to the panel's 16 grey levels, optionally with Floyd-Steinberg dithering."""
    pal = Image.new("P", (1, 1))
    pal.putpalette(sum(([v * 17] * 3 for v in range(16)), []) + [0] * (256 - 16) * 3)
    q = im.convert("RGB").quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE)
    return q.convert("L")


def fit(im, w, h):
    return ImageOps.fit(im, (w, h), Image.Resampling.LANCZOS)


# --- photo, plain and dithered
photo = Image.open(PHOTO).convert("L")
p = fit(photo, 520, 325)
neg(to16(p, False)).save(LOC / "photo_plain.png")
neg(to16(p, True)).save(LOC / "photo_dither.png")

# --- second photo page: four subjects, 255 x 170 each, plain and dithered
SUBJECTS = [
    ("forest", r"C:/Windows/Web/Wallpaper/ThemeC/img29.jpg", None),
    ("dark", r"C:/Windows/Web/Wallpaper/ThemeB/img26.jpg", None),
    ("soft", r"C:/Windows/Web/Wallpaper/ThemeD/img32.jpg", None),
    # a photo of the circuit board with small writing, if there is one; otherwise another sample picture
    ("board", str(HERE.parent / "fotos" / "measurement.jpg"), (290, 575, 605, 785))
    if (HERE.parent / "fotos" / "measurement.jpg").exists()
    else ("board", r"C:/Windows/Web/Wallpaper/ThemeC/img30.jpg", None),
]
for name, path, box in SUBJECTS:
    im = Image.open(path).convert("L")
    if box:
        im = im.crop(box)
    im = fit(im, 255, 170)
    neg(to16(im, False)).save(LOC / f"p2_{name}_plain.png")
    neg(to16(im, True)).save(LOC / f"p2_{name}_dither.png")

# --- panning "video": 16 frames across the photo, 360 x 240
frames = []
W, H = photo.size
for i in range(16):
    t = i / 15
    cw, ch = int(W * 0.55), int(H * 0.55)
    x = int((W - cw) * t)
    y = int((H - ch) * (0.5 + 0.3 * math.sin(t * math.pi)) * 0.8)
    f = photo.crop((x, y, x + cw, y + ch)).resize((360, 240), Image.Resampling.LANCZOS)
    frames.append(neg(to16(f, True)).convert("P"))
frames[0].save(LOC / "video.gif", save_all=True, append_images=frames[1:], duration=100, loop=0)

# --- spinner: 12 dots, one dark and fading tail, 96 x 96
frames = []
for i in range(12):
    im = Image.new("L", (96, 96), 255)
    d = ImageDraw.Draw(im)
    for k in range(12):
        a = 2 * math.pi * k / 12 - math.pi / 2
        age = (i - k) % 12
        grey = 0 if age == 0 else min(255, 40 + age * 22)
        cx, cy = 48 + 34 * math.cos(a), 48 + 34 * math.sin(a)
        d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=grey)
    frames.append(neg(im).convert("P"))
frames[0].save(PUB / "spinner.gif", save_all=True, append_images=frames[1:], duration=80, loop=0)

# --- bell swinging, 200 x 200
def bell(angle):
    im = Image.new("L", (400, 400), 255)
    d = ImageDraw.Draw(im)
    d.ellipse((188, 40, 212, 64), fill=0)                          # hanger
    d.pieslice((100, 60, 300, 260), 180, 360, fill=0)              # dome
    d.polygon([(100, 160), (300, 160), (330, 290), (70, 290)], fill=0)  # body
    d.rounded_rectangle((50, 280, 350, 310), 12, fill=0)           # rim
    d.ellipse((170, 300, 230, 350), fill=0)                        # clapper
    im = im.rotate(angle, center=(200, 52), resample=Image.Resampling.BICUBIC, fillcolor=255)
    return im.resize((200, 200), Image.Resampling.LANCZOS)


frames = [neg(to16(bell(18 * math.sin(2 * math.pi * i / 10)), False)).convert("P") for i in range(10)]
frames[0].save(PUB / "bell.gif", save_all=True, append_images=frames[1:], duration=100, loop=0)

# --- front drawing: render the SVG with headless Edge at 520 px wide
w = 520
h = round(w * 380 / 360)
html = HERE / "local-assets" / "_front.html"
html.write_text(f"<html><body style='margin:0;background:#fff'><img src='{FRONT_SVG.as_uri()}' "
                f"style='width:{w}px;height:{h}px;display:block'></body></html>", encoding="utf-8")
shot = LOC / "_front_shot.png"
if shot.exists():
    shot.unlink()
subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={w},{h}",
                "--force-device-scale-factor=1", "--allow-file-access-from-files", "--virtual-time-budget=3000",
                f"--screenshot={shot}", html.as_uri()], check=True, capture_output=True)
for _ in range(40):
    if shot.exists() and shot.stat().st_size > 0:
        break
    time.sleep(0.25)
time.sleep(0.3)
front = Image.open(shot).convert("L").crop((0, 0, w, h))
neg(to16(front, False)).save(PUB / "front.png")

for f in sorted(list(PUB.glob("*")) + list(LOC.glob("*"))):
    if f.suffix in (".png", ".gif") and not f.name.startswith("_"):
        im = Image.open(f)
        print(f.relative_to(HERE), im.size, getattr(im, "n_frames", 1), "frames")
