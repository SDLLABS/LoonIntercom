"""Hausklingel – Layout v5 (2026-09-17)

Neu gegenüber v4:
  * Rohr komplett raus (der Bauherr sucht selbst einen anderen Kabelweg), Mini-Gravur raus.
  * Front wieder 100 × 260.
  * Front + Dach bleiben EIN gekantetes Blech (2 mm, oben 85°, Tropfkante 6).
  * NEU: LED-Band in der Kantung – zwei Fenster für den LED-Streifen, außen je ein Schlitz für die
    Haltelaschen des Diffusors; davor sitzt der viertelrunde ABS-Diffusor (Enden rund, „Hotdog“).
  * Obere Schrauben von y = 19 auf y = 26, weil der Diffusor bis y = 18 reicht.

Koordinaten in mm.
Vorderansicht: x nach rechts, y nach unten; Ursprung = linke obere Ecke der Messingfront.
Seitenansicht:  xs = 0 ist die Wandoberfläche; xs < 0 in der Wand, xs > 0 davor.

Erzeugt: gemini-zeichnung-v5.png (für Gemini, ohne verdeckte Kanten),
         layout-v5-referenz.png, detail-kantung-v5.png (fürs CAD), layout-v5-bemasst.svg
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
WINF = "C:/Windows/Fonts/"
FONT_FILE, FONT_LABEL = WINF + "segoeui.ttf", "Segoe UI Regular"

# ------------------------------------------------------------------ Front
W, H = 100, 260
T = 2.0                               # Blechdicke Front + Dach (ein Teil)
BEND_RI = 2.0                         # Innenradius der Kantung
GRILLE_Y0, ROWS, PER_ROW = 20, 5, 18
ROW_PITCH, SLASH_H, SLOT_W, SLASH_ANG = 7, 5, 1.5, 70
SCR = (21, 64, 79, 168)               # sichtbare Displayfläche 58 × 104, hochkant
COL_X0, COL_X1 = 21, 79
NAMES = "MAX · ERIKA · ANNA · PAUL"          # Platzhalter: eigene Vornamen eintragen
NAMES_BASE, NAMES_CAP_MAX, NAMES_MIN_TRACK = 182.2, 3.2, 0.35
FAMILY, FAMILY_BASE, FAMILY_CAP = "MUSTERMANN", 193.5, 8.0   # Platzhalter
RING_C, RING_D, BTN_D, BTN_HOLE = (50, 225), 48.5, 20, 22    # Ring gemessen 2026-09-17; Knopf/Loch offen
MIC, MIC_D = [(82, 221), (82, 229)], 1.2
SCREWS = [(8, 26), (92, 26), (8, 252), (92, 252)]
SCREW_D, SCREW_SLOT, SCREW_HOLE = 6.0, 0.8, 3.2              # M3 Senkkopf DIN 963, Kopf Ø6

# ------------------------------------------------------------------ LED-Band + Diffusor
LED_OFF = 0.15 * W                    # 15 % der Breite frei lassen
SLIT_W, SLIT_H = 10, 2.6              # Schlitz für je eine Haltelasche des Diffusors
WIN_W, WIN_H, WEB, GAP = 18, 6, 6, 4  # Fenster für den LED-Streifen, Steg, Abstand zum Schlitz
WIN_Y0 = 8                            # Abstand von der Kante: Löcher dürfen nicht in die Kantung
BAND_MID = WIN_Y0 + WIN_H / 2
SLITS = [(LED_OFF, LED_OFF + SLIT_W), (W - LED_OFF - SLIT_W, W - LED_OFF)]
_w0 = LED_OFF + SLIT_W + GAP
WINS = [(_w0, _w0 + WIN_W), (_w0 + WIN_W + WEB, _w0 + 2 * WIN_W + WEB)]
DIFF_R, DIFF_X = 18, (13, 87)         # Viertelrund, Enden rund; überdeckt Fenster und Schlitze

# ------------------------------------------------------------------ Dach (gleiches Blech)
CAP_LEN, CAP_ANGLE, CAP_DRIP = 60, 85, 6
CAP_TOP = -T
_TN = math.tan(math.radians(90 - CAP_ANGLE))
_CS = math.cos(math.radians(90 - CAP_ANGLE))
CAP_DROP = CAP_LEN * _TN
roof_top = lambda xs: -T + xs * _TN
roof_under = lambda xs: roof_top(xs) + T / _CS
BAND_BOT = roof_under(CAP_LEN) + CAP_DRIP

# ------------------------------------------------------------------ Kasten
BOX = (4, 4, 96, H - 4)               # je 4 mm unter der Front verdeckt
BOX_DEPTH = 50                        # PLATZHALTER bis das CAD steht
BOT = H + 30                          # Zeichnungsrand unten

SL_W = SLOT_W / math.sin(math.radians(SLASH_ANG))
SL_OFF = SLASH_H / math.tan(math.radians(SLASH_ANG))
SL_PITCH = (COL_X1 - SL_OFF - SL_W - COL_X0) / (PER_ROW - 1)
SL_WEB = SL_PITCH * math.sin(math.radians(SLASH_ANG)) - SLOT_W

BRASS = (196, 160, 92)
DIFF_COL = (253, 246, 228)
INK = (38, 30, 16)
rnd = random.Random(7)


# ------------------------------------------------------------------ Schrift und Gravur
class Face:
    def __init__(self, path):
        self.path = path
        self.tt = TTFont(path)
        self.gs = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.upm = self.tt["head"].unitsPerEm
        self.cap = getattr(self.tt["OS/2"], "sCapHeight", 0) or self.bounds("H")[3]
        self.dot = next(c for c in "·•∙" if ord(c) in self.cmap)

    def bounds(self, ch):
        bp = BoundsPen(self.gs)
        self.gs[self.cmap[ord(ch)]].draw(bp)
        return bp.bounds

    def adv(self, ch):
        return self.tt["hmtx"][self.cmap[ord(ch)]][0]

    def path_d(self, ch):
        pen = SVGPathPen(self.gs)
        self.gs[self.cmap[ord(ch)]].draw(pen)
        return pen.getCommands()


WORDS = [w.strip() for w in NAMES.split("·")]
GAP_K = 1.9


def word_metrics(face, word, t_units):
    advs = [face.adv(c) for c in word]
    b0, bl = face.bounds(word[0]), face.bounds(word[-1])
    ink = sum(advs[:-1]) + (len(word) - 1) * t_units + bl[2] - b0[0]
    pos, x = [], -b0[0]
    for a in advs:
        pos.append(x)
        x += a + t_units
    return ink, pos


def layout_names(face):
    target = COL_X1 - COL_X0
    n_inner = sum(len(w) - 1 for w in WORDS)
    cap = NAMES_CAP_MAX
    while True:
        s = cap / face.cap
        gap = GAP_K * cap
        base = sum(word_metrics(face, w, 0)[0] for w in WORDS) * s
        t_mm = (target - (len(WORDS) - 1) * gap - base) / n_inner
        if t_mm >= NAMES_MIN_TRACK or cap <= 1.5:
            break
        cap -= 0.02
    b = face.bounds(face.dot)
    dy = face.cap / 2 - (b[1] + b[3]) / 2
    glyphs, x = [], 0.0
    for i, w in enumerate(WORDS):
        ink, pos = word_metrics(face, w, t_mm / s)
        glyphs += [(ch, x + p * s, 0) for ch, p in zip(w, pos)]
        x += ink * s
        if i < len(WORDS) - 1:
            glyphs.append((face.dot, x + gap / 2 - (b[0] + b[2]) / 2 * s, dy))
            x += gap
    return cap, s, t_mm, glyphs


FAMILY_MIN_TRACK = 0.6   # mm Luft zwischen den Buchstaben; laengere Namen werden kleiner statt enger


def layout_family(face):
    advs = [face.adv(c) for c in FAMILY]
    b0, bl = face.bounds(FAMILY[0]), face.bounds(FAMILY[-1])
    cap = FAMILY_CAP
    while True:
        s = cap / face.cap
        track = ((COL_X1 - COL_X0) / s - (sum(advs[:-1]) + bl[2] - b0[0])) / (len(FAMILY) - 1)
        if track * s >= FAMILY_MIN_TRACK or cap <= 3.0:
            break
        cap -= 0.05
    glyphs, x = [], -b0[0]
    for ch, a in zip(FAMILY, advs):
        glyphs.append((ch, x * s, 0))
        x += a + track
    return s, track * s, glyphs


def draw_line(img, face, glyphs, s, x0_px, base_px, S, color, width=COL_X1 - COL_X0):
    size = face.upm * s * S
    f = ImageFont.truetype(face.path, size)
    pad = int(size * 2)
    tmp = Image.new("L", (int(width * S) + 2 * pad, pad * 2), 0)
    td = ImageDraw.Draw(tmp)
    for ch, x_mm, dy in glyphs:
        td.text((pad + x_mm * S, pad - dy * s * S), ch, font=f, fill=255, anchor="ls")
    bb = tmp.getbbox()
    ink = tmp.crop((bb[0], 0, bb[2], tmp.height)).resize((round(width * S), tmp.height), Image.LANCZOS)
    img.paste(Image.new("RGB", ink.size, color), (round(x0_px), round(base_px - pad)), ink)


# ------------------------------------------------------------------ Zeichenhilfen
def brushed(d, rect_px, base):
    x0, y0, x1, y1 = [int(v) for v in rect_px]
    for yy in range(y0, y1):
        k = rnd.uniform(-10, 10)
        d.line([(x0, yy), (x1, yy)], fill=tuple(max(0, min(255, int(v + k))) for v in base))


def dashed(d, pts, col, w=2, dash=10, gap=7):
    period, done = dash + gap, 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        if L == 0:
            continue
        n = -(done % period)
        while n < L:
            a, e = max(n, 0), min(n + dash, L)
            if e > a:
                d.line([(x0 + (x1 - x0) * a / L, y0 + (y1 - y0) * a / L),
                        (x0 + (x1 - x0) * e / L, y0 + (y1 - y0) * e / L)], fill=col, width=w)
            n += period
        done += L


def arrow2(d, p0, p1, col, w=2, head=11):
    d.line([p0, p1], fill=col, width=w)
    for a, b in ((p0, p1), (p1, p0)):
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        for sgn in (1, -1):
            d.line([b, (b[0] - head * math.cos(ang + sgn * 0.4), b[1] - head * math.sin(ang + sgn * 0.4))],
                   fill=col, width=w)


def hull(pts):
    pts = sorted(set(pts))
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (p[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (p[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(p)
        return out
    return half(pts)[:-1] + half(list(reversed(pts)))[:-1]


def bez(p0, c, p1, n=8):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]) for t in [i / n for i in range(n + 1)]]


def sheet_profile():
    """Querschnitt Front + Dach als EIN gekantetes Blech, Punkte (xs, y)."""
    ro, ri = T + BEND_RI, BEND_RI
    pts = [(0, H)]
    pts += bez((0, -T + ro), (0, -T), (ro, roof_top(ro)))
    pts += [(CAP_LEN, roof_top(CAP_LEN)), (CAP_LEN, BAND_BOT), (CAP_LEN - T, BAND_BOT),
            (CAP_LEN - T, roof_under(CAP_LEN - T))]
    pts += bez((T + ri, roof_under(T + ri)), (T, roof_under(T)), (T, roof_under(T) + ri))
    pts += [(T, H)]
    return pts


def diffusor_profile(n=16):
    """Viertelkreis im Innenwinkel, Punkte (xs, y): flach an der Front, flach am Dach."""
    a = [math.pi / 2 * i / n for i in range(n + 1)]
    return [(T, roof_under(T) + DIFF_R)] + [(T + DIFF_R * math.sin(t), roof_under(T) + DIFF_R * math.cos(t))
                                            for t in a] + [(T, roof_under(T))]


def slash_polys():
    polys = []
    for r in range(ROWS):
        yt = GRILLE_Y0 + r * ROW_PITCH
        yb = yt + SLASH_H
        for i in range(PER_ROW):
            x0 = COL_X0 + i * SL_PITCH
            polys.append([(x0, yb), (x0 + SL_W, yb), (x0 + SL_OFF + SL_W, yt), (x0 + SL_OFF, yt)])
    return polys


def fake_qr(d, P, x0, y0, size, n=25, seed=3):
    """Zufallsmuster im QR-Look – kodiert nichts."""
    r = random.Random(seed)
    m = size / n
    cell = lambda i, j: d.rectangle([P(x0 + i * m, y0 + j * m), P(x0 + (i + 1) * m, y0 + (j + 1) * m)],
                                    fill=(25, 25, 25))
    reserved = set()
    for ci, cj in ((0, 0), (n - 7, 0), (0, n - 7)):
        for i in range(7):
            for j in range(7):
                if i in (0, 6) or j in (0, 6) or (2 <= i <= 4 and 2 <= j <= 4):
                    cell(ci + i, cj + j)
        reserved |= {(ci + i, cj + j) for i in range(-1, 8) for j in range(-1, 8)}
    for i in range(n):
        for j in range(n):
            if (i, j) not in reserved and r.random() < 0.45:
                cell(i, j)


def draw_screw(d, P, x, y, S):
    r = SCREW_D / 2
    d.ellipse([P(x - r, y - r), P(x + r, y + r)], fill=(218, 188, 122), outline=(118, 90, 46), width=max(1, S // 3))
    d.ellipse([P(x - r + 0.9, y - r + 0.9), P(x + r - 0.9, y + r - 0.9)], outline=(240, 220, 170), width=1)
    d.rectangle([P(x - SCREW_SLOT / 2, y - r + 0.6), P(x + SCREW_SLOT / 2, y + r - 0.6)], fill=(70, 52, 24))


def draw_diffusor_front(d, P, S):
    """Diffusor von vorn: Rechteck mit runden Enden (Viertelrund, Enden kugelig)."""
    x0, x1 = DIFF_X
    d.rectangle([P(x0 + DIFF_R, 0), P(x1 - DIFF_R, DIFF_R)], fill=DIFF_COL)
    for cx, a0, a1 in ((x0 + DIFF_R, 90, 180), (x1 - DIFF_R, 0, 90)):
        d.pieslice([P(cx - DIFF_R, -DIFF_R), P(cx + DIFF_R, DIFF_R)], a0, a1, fill=DIFF_COL)
    d.arc([P(x0 + DIFF_R - DIFF_R, -DIFF_R), P(x0 + DIFF_R + DIFF_R, DIFF_R)], 90, 180,
          fill=(205, 196, 176), width=max(1, S // 2))
    d.arc([P(x1 - DIFF_R - DIFF_R, -DIFF_R), P(x1 - DIFF_R + DIFF_R, DIFF_R)], 0, 90,
          fill=(205, 196, 176), width=max(1, S // 2))
    d.line([P(x0 + DIFF_R, DIFF_R), P(x1 - DIFF_R, DIFF_R)], fill=(205, 196, 176), width=max(1, S // 2))


# ------------------------------------------------------------------ Vorderansicht
def draw_front(img, face, OX, OY, S, cap=True, hidden=False, cutouts=False):
    d = ImageDraw.Draw(img)
    P = lambda x, y: (OX + x * S, OY + y * S)
    brushed(d, (*P(0, 0), *P(W, H)), BRASS)
    d.rectangle([P(0, 0), P(W, H)], outline=(120, 95, 50), width=2)
    if hidden:
        b = BOX
        dashed(d, [P(b[0], b[1]), P(b[2], b[1]), P(b[2], b[3]), P(b[0], b[3]), P(b[0], b[1])], (90, 90, 90), w=2)
    draw_diffusor_front(d, P, S)
    if cutouts:           # LED-Fenster und Laschenschlitze liegen hinter dem Diffusor
        for (a, b) in WINS:
            dashed(d, [P(a, WIN_Y0), P(b, WIN_Y0), P(b, WIN_Y0 + WIN_H), P(a, WIN_Y0 + WIN_H), P(a, WIN_Y0)],
                   (120, 120, 120), w=2, dash=6, gap=4)
        for (a, b) in SLITS:
            y0 = BAND_MID - SLIT_H / 2
            dashed(d, [P(a, y0), P(b, y0), P(b, y0 + SLIT_H), P(a, y0 + SLIT_H), P(a, y0)],
                   (120, 120, 120), w=2, dash=6, gap=4)
    g0, glen = (BAND_BOT, 30) if cap else (0, 45)
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(int(glen * S)):
        gd.line([(OX, OY + g0 * S + i), (OX + W * S, OY + g0 * S + i)],
                fill=(255, 235, 185, int(110 * (1 - i / (glen * S)) ** 2)))
    img.paste(glow, (0, 0), glow)
    d = ImageDraw.Draw(img)
    for (x, y) in SCREWS:
        draw_screw(d, P, x, y, S)
    cx, cy = RING_C
    d.ellipse([P(cx - RING_D / 2, cy - RING_D / 2), P(cx + RING_D / 2, cy + RING_D / 2)],
              fill=(168, 134, 72), outline=(100, 78, 40), width=3)
    d.ellipse([P(cx - RING_D / 2 + 2, cy - RING_D / 2 + 2), P(cx + RING_D / 2 - 2, cy + RING_D / 2 - 2)],
              fill=(186, 150, 84))
    d.ellipse([P(cx - BTN_D / 2, cy - BTN_D / 2), P(cx + BTN_D / 2, cy + BTN_D / 2)],
              fill=(214, 182, 116), outline=(110, 85, 45), width=3)
    d.ellipse([P(cx - 6, cy - 6), P(cx + 1, cy + 1)], fill=(236, 214, 160))
    for (mx, my) in MIC:
        d.ellipse([P(mx - MIC_D / 2, my - MIC_D / 2), P(mx + MIC_D / 2, my + MIC_D / 2)], fill=(40, 32, 18))
    cap_h, s, t_names, gl = layout_names(face)
    draw_line(img, face, gl, s, OX + COL_X0 * S, OY + NAMES_BASE * S, S, INK)
    s2, t_fam, gl2 = layout_family(face)
    draw_line(img, face, gl2, s2, OX + COL_X0 * S, OY + FAMILY_BASE * S, S, INK)
    d = ImageDraw.Draw(img)
    d.rectangle([P(SCR[0] - 1, SCR[1] - 1), P(SCR[2] + 1, SCR[3] + 1)], fill=(55, 55, 55))
    d.rectangle([P(*SCR[:2]), P(*SCR[2:])], fill=(228, 227, 221))
    fb = ImageFont.truetype(WINF + "segoeuib.ttf", 9 * S)
    fr = ImageFont.truetype(WINF + "segoeui.ttf", 5 * S)
    t0, sx = SCR[1], OX + 50 * S
    d.text((sx, OY + (t0 + 16) * S), "Hallo!", font=fb, fill=(30, 30, 30), anchor="ms")
    d.text((sx, OY + (t0 + 26) * S), "Bitte klingeln.", font=fr, fill=(30, 30, 30), anchor="ms")
    d.line([P(32, t0 + 34), P(68, t0 + 34)], fill=(120, 120, 120), width=max(1, S // 2))
    fake_qr(d, P, 36, t0 + 42, 28)
    d.text((sx, OY + (t0 + 83) * S), "Schreib uns", font=fr, fill=(30, 30, 30), anchor="ms")
    for poly in slash_polys():
        d.polygon([P(x, y) for (x, y) in poly], fill=(40, 32, 18))
    if cap:    # Dach von vorn: schräge Oberseite + Tropfkante, so breit wie die Front
        brushed(d, (*P(0, CAP_TOP), *P(W, CAP_TOP + CAP_DROP + T)), (222, 192, 128))
        brushed(d, (*P(0, CAP_TOP + CAP_DROP + T), *P(W, BAND_BOT)), (170, 136, 74))
        d.line([P(0, BAND_BOT), P(W, BAND_BOT)], fill=(90, 70, 35), width=2)
    return cap_h, t_names, t_fam


# ------------------------------------------------------------------ Seitenschnitt
def draw_side(img, SX, OY, S, labels=False):
    d = ImageDraw.Draw(img)
    P = lambda xs, y: (SX + xs * S, OY + y * S)
    top, bot = -40, BOT
    d.rectangle([P(-70, top), P(0, bot)], fill=(234, 227, 208))           # Putz + Dämmung
    for y in range(top, bot, 8):
        d.line([P(-70, y + 8), P(-62, y)], fill=(200, 190, 165), width=1)
    d.line([P(0, top), P(0, bot)], fill=(90, 90, 90), width=3)             # Wandoberfläche
    d.rectangle([P(-BOX_DEPTH, BOX[1]), P(0, BOX[3])], fill=(28, 28, 30))  # Kasten
    d.rectangle([P(-BOX_DEPTH + 3, BOX[1] + 3), P(-1.5, BOX[3] - 3)], fill=(64, 64, 68))
    dashed(d, [P(-BOX_DEPTH, 150), P(-66, 150)], (120, 120, 120), w=3)     # Kabelweg offen
    d.polygon([P(xs, y) for xs, y in sheet_profile()], fill=(170, 136, 74), outline=(100, 78, 40))
    d.ellipse([P(-1.5, CAP_TOP - 2.5), P(1.5, CAP_TOP + 0.5)], fill=(150, 150, 150))   # Silikonfuge
    # Diffusor + LED-Streifen + Lasche durch den Schlitz
    d.polygon([P(xs, y) for xs, y in diffusor_profile()], fill=DIFF_COL, outline=(190, 182, 164))
    d.rectangle([P(-7, BAND_MID - SLIT_H / 2), P(T, BAND_MID + SLIT_H / 2)], fill=(90, 90, 96))
    d.polygon([P(-7, BAND_MID - SLIT_H / 2), P(-7, BAND_MID + SLIT_H / 2 + 1.6),
               P(-4.5, BAND_MID + SLIT_H / 2)], fill=(90, 90, 96))
    d.rectangle([P(T, WIN_Y0 - 2), P(T + 1.4, WIN_Y0 + WIN_H + 2)], fill=(60, 66, 60))
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).polygon([P(T + DIFF_R, 8), P(T + 40, BAND_BOT + 14), P(T + 2, 84)],
                                 fill=(255, 232, 170, 80))
    img.paste(glow, (0, 0), glow)
    d = ImageDraw.Draw(img)
    d.polygon([P(xs, y) for xs, y in diffusor_profile()], fill=DIFF_COL, outline=(190, 182, 164))
    for y in (SCREWS[0][1], SCREWS[2][1]):                                  # Schrauben
        d.rectangle([P(-12, y - 0.8), P(T - 1.6, y + 0.8)], fill=(110, 96, 70))
        d.polygon([P(T, y - 3), P(T, y + 3), P(T - 1.7, y + 1.5), P(T - 1.7, y - 1.5)], fill=(218, 188, 122))
    ry = RING_C[1]
    d.rectangle([P(T, ry - RING_D / 2), P(T + 1.5, ry + RING_D / 2)], fill=(168, 134, 72))
    d.rounded_rectangle([P(T, ry - BTN_D / 2), P(T + 4, ry + BTN_D / 2)], radius=6,
                        fill=(214, 182, 116), outline=(110, 85, 45))


# ------------------------------------------------------------------ Blatt für Gemini
def make_gemini_sheet(face):
    S = 4
    K, ANG = 0.30, math.radians(22)
    col, ext = (60, 60, 60), (175, 175, 175)
    ft = ImageFont.truetype(WINF + "segoeuib.ttf", 34)
    fd = ImageFont.truetype(WINF + "segoeui.ttf", 27)
    fbig = ImageFont.truetype(WINF + "segoeuib.ttf", 30)
    p1x = 60
    p2x = p1x + 170 * S
    p3x = p2x + 245 * S
    O1x, O2x, O3x = p1x + 25 * S, p2x + 25 * S, p3x + 80 * S
    Oy = 150 + 40 * S
    img = Image.new("RGB", (O3x + 140 * S, Oy + (BOT + 20) * S + 120), "white")
    d = ImageDraw.Draw(img)
    d.text((p1x, 40), "3D-ANSICHT", font=ft, fill=(120, 120, 120))
    d.text((p2x, 40), "VORDERANSICHT · Maße in mm", font=ft, fill=(120, 120, 120))
    d.text((p3x, 40), "SEITENSCHNITT · Wand links", font=ft, fill=(120, 120, 120))

    # --- 3D (Kabinett), dz = Abstand vor der Wand
    O1y = Oy
    pr = lambda x, y, dz: (O1x + (x + dz * K * math.cos(ANG)) * S, O1y + (y + dz * K * math.sin(ANG)) * S)
    d.rectangle([pr(-30, -45, 0), pr(W + 45, BOT, 0)], fill=(238, 236, 231))
    d.polygon([pr(0, y, xs) for xs, y in sheet_profile()], fill=(140, 110, 58))
    tex = Image.new("RGB", (int(W * S) + 1, int(H * S) + 1), "white")
    draw_front(tex, face, 0, 0, S, cap=False)
    tp = pr(0, 0, T)
    img.paste(tex, (round(tp[0]), round(tp[1])))
    d = ImageDraw.Draw(img)
    # Diffusor als Viertelrund mit runden Enden
    secs = []
    for i in range(41):
        x = DIFF_X[0] + (DIFF_X[1] - DIFF_X[0]) * i / 40
        e = min(x - DIFF_X[0], DIFF_X[1] - x)
        r = DIFF_R if e >= DIFF_R else math.sqrt(max(0.0, DIFF_R ** 2 - (DIFF_R - e) ** 2))
        for t in [math.pi / 2 * k / 8 for k in range(9)]:
            secs.append(pr(x, roof_under(T) + r * math.cos(t), T + r * math.sin(t)))
        secs.append(pr(x, roof_under(T), T))
    d.polygon(hull(secs), fill=DIFF_COL, outline=(214, 205, 186))
    # Dach: Oberseite, Seitenkante, Tropfkante
    yf = roof_top(CAP_LEN)
    d.line([pr(0, CAP_TOP, 0), pr(W, CAP_TOP, 0)], fill=(150, 150, 150), width=3)
    d.polygon([pr(0, CAP_TOP, 0), pr(W, CAP_TOP, 0), pr(W, yf, CAP_LEN), pr(0, yf, CAP_LEN)],
              fill=(222, 192, 128), outline=(140, 110, 58))
    d.polygon([pr(0, y, xs) for xs, y in sheet_profile() if y < 3 or xs > T + 0.01], fill=(150, 118, 62))
    d.polygon([pr(0, yf, CAP_LEN), pr(W, yf, CAP_LEN), pr(W, BAND_BOT, CAP_LEN), pr(0, BAND_BOT, CAP_LEN)],
              fill=(182, 148, 84), outline=(120, 92, 48))
    d.line([pr(0, roof_under(T) + 0.5, T + 0.5), pr(W, roof_under(T) + 0.5, T + 0.5)], fill=(236, 210, 150), width=2)

    # --- Vorderansicht mit Maßen
    draw_front(img, face, O2x, Oy, S, hidden=True)
    d = ImageDraw.Draw(img)
    P = lambda x, y: (O2x + x * S, Oy + y * S)
    yb = BOT - 8
    for x in (0, W):
        d.line([P(x, H), P(x, yb + 2)], fill=ext, width=1)
    arrow2(d, P(0, yb), P(W, yb), col)
    d.text(((P(0, 0)[0] + P(W, 0)[0]) / 2, P(0, yb)[1] - 6), "100", font=fbig, fill=col, anchor="md")
    for y in (0, H):
        d.line([P(-2, y), P(-14, y)], fill=ext, width=1)
    arrow2(d, P(-12, 0), P(-12, H), col)
    d.text(P(-14, H / 2), str(H), font=fbig, fill=col, anchor="rm")
    arrow2(d, P(COL_X0 + 0.5, SCR[3] - 5), P(COL_X1 - 0.5, SCR[3] - 5), (20, 20, 20))
    d.text(((P(COL_X0, 0)[0] + P(COL_X1, 0)[0]) / 2, P(0, SCR[3] - 6)[1]), "58", font=fbig, fill=(20, 20, 20),
           anchor="md")
    arrow2(d, P(13, SCR[1]), P(13, SCR[3]), (20, 20, 20))
    d.text(P(11.5, (SCR[1] + SCR[3]) / 2), "104", font=fbig, fill=(20, 20, 20), anchor="rm")
    gr_mid = GRILLE_Y0 + ((ROWS - 1) * ROW_PITCH + SLASH_H) / 2
    scr_mid = (SCR[1] + SCR[3]) / 2
    rc = RING_C[1]
    callouts = [
        (W, 1, -2, "Dach: SELBES Blech, gekantet"),
        (W, 8, 6, "Tropfkante 6"),
        (DIFF_X[1], DIFF_R - 3, 14, "Diffusor: weiß, viertelrund,"),
        (DIFF_X[1], DIFF_R - 3, 22, "leuchtet warmweiß"),
        (SCREWS[1][0] + 3, SCREWS[1][1], 32, "4 Messing-Senkschrauben"),
        (SCREWS[1][0] + 3, SCREWS[1][1], 40, "M3, EIN Schlitz, senkrecht"),
        (COL_X1, gr_mid, gr_mid + 12, "5 × 18 Schrägschlitze"),
        (COL_X1, scr_mid, scr_mid - 5, "DISPLAY HOCHKANT"),
        (COL_X1, scr_mid, scr_mid + 5, "58 breit × 104 hoch"),
        (COL_X1, FAMILY_BASE - 4, FAMILY_BASE - 4, "Gravur 58 breit (2 Zeilen)"),
        (RING_C[0] + RING_D / 2, rc, rc - 8, "Ring Ø48,5 (gemessen) · Knopf Ø20?"),
        (60, rc, rc, "einziger Knopf"),
        (MIC[1][0], MIC[1][1], rc + 8, "2 Mikrofonlöcher"),
        (BOX[2], BOX[3] - 20, rc + 20, "Kasten in der Wand (verdeckt)"),
    ]
    for (zx, zy, ty, t) in callouts:
        big = t.startswith(("DISPLAY", "58 breit"))
        d.line([P(zx, zy), P(W + 8, ty)], fill=ext, width=1)
        d.text(P(W + 9, ty), t, font=fbig if big else fd, fill=(20, 20, 20) if big else col, anchor="lm")

    # --- Seitenschnitt mit Maßen
    draw_side(img, O3x, Oy, S)
    d = ImageDraw.Draw(img)
    Q = lambda xs, y: (O3x + xs * S, Oy + y * S)
    arrow2(d, Q(0, -16), Q(CAP_LEN, -16), col)
    d.text(((Q(0, 0)[0] + Q(CAP_LEN, 0)[0]) / 2, Q(0, -16)[1] - 6), "60", font=fbig, fill=col, anchor="md")
    arrow2(d, Q(-BOX_DEPTH, -30), Q(0, -30), col)
    d.text(((Q(-BOX_DEPTH, 0)[0] + Q(0, 0)[0]) / 2, Q(0, -30)[1] - 6), f"{BOX_DEPTH}?", font=fbig, fill=col,
           anchor="md")
    d.text(Q(24, 20), "85°", font=fbig, fill=(190, 40, 40), anchor="lm")
    d.text(Q(CAP_LEN + 3, CAP_DROP + 4), "6", font=fbig, fill=col, anchor="lm")
    d.text(Q(-BOX_DEPTH + 4, 180), "Kasten", font=fd, fill=(225, 225, 225), anchor="lm")
    d.text(Q(-BOX_DEPTH + 4, 188), "(Unterputz)", font=fd, fill=(225, 225, 225), anchor="lm")
    d.text(Q(-68, -18), "Wand / Dämmung", font=fd, fill=(120, 110, 90), anchor="lm")
    d.text(Q(8, 70), "Front + Dach:", font=fbig, fill=(20, 20, 20), anchor="lm")
    d.text(Q(8, 79), "EIN Blech, 2 mm,", font=fbig, fill=(20, 20, 20), anchor="lm")
    d.text(Q(8, 88), "oben gekantet", font=fbig, fill=(20, 20, 20), anchor="lm")
    d.text(Q(8, -38), "Silikonfuge", font=fd, fill=col, anchor="lm")
    d.line([Q(0, -2), Q(7, -38)], fill=ext, width=1)
    d.text(Q(26, 34), f"Diffusor R{DIFF_R}", font=fd, fill=col, anchor="lm")
    d.line([Q(15, 16), Q(25, 33)], fill=ext, width=1)
    d.text(Q(26, 44), "(ABS, Enden rund)", font=fd, fill=col, anchor="lm")
    d.text(Q(-66, 143), "Kabelweg: offen", font=fd, fill=(120, 110, 90), anchor="lm")
    d.text((p1x, img.height - 60),
           "Maßstäblich, alle Ansichten gleicher Maßstab. Front und Dach sind EIN gekantetes Blech. "
           "Hochformat-Display 58 × 104 mm. Ein Knopf. Kasten unsichtbar in der Wand, gestrichelt = verdeckt. "
           "Kein Rohr, keine Kamera.", font=fd, fill=(90, 90, 90))
    img.save(os.path.join(HERE, "gemini-zeichnung-v5.png"))
    return img


# ------------------------------------------------------------------ saubere Vorlage (ohne Maße)
def make_reference(face):
    S = 5
    OX, OY = 120, 160 + 10 * S
    SX = OX + W * S + 120 + 75 * S
    img = Image.new("RGB", (SX + 110 * S, OY + (BOT + 15) * S + 60), "white")
    d = ImageDraw.Draw(img)
    ft = ImageFont.truetype(WINF + "segoeui.ttf", 30)
    d.text((OX, 50), "VORDERANSICHT", font=ft, fill=(150, 150, 150))
    d.text((SX - 60 * S, 50), "SEITENSCHNITT (Wand links)", font=ft, fill=(150, 150, 150))
    caps = draw_front(img, face, OX, OY, S, cutouts=True)
    draw_side(img, SX, OY, S)
    img.save(os.path.join(HERE, "layout-v5-referenz.png"))
    return caps, img, OX, OY, S


# ------------------------------------------------------------------ Detailblatt fürs CAD
def sheet_profile_clip(x_max=38, y_max=40):
    """Kantung als Detail: Blechprofil, vorne abgeschnitten."""
    ro, ri = T + BEND_RI, BEND_RI
    pts = [(0, y_max)]
    pts += bez((0, -T + ro), (0, -T), (ro, roof_top(ro)))
    pts += [(x_max, roof_top(x_max)), (x_max, roof_under(x_max))]
    pts += bez((T + ri, roof_under(T + ri)), (T, roof_under(T)), (T, roof_under(T) + ri))
    pts += [(T, y_max)]
    return pts


def make_detail():
    S = 10                                   # 10 px/mm
    fb = ImageFont.truetype(WINF + "segoeuib.ttf", 30)
    fd = ImageFont.truetype(WINF + "segoeui.ttf", 23)
    col, ext = (50, 50, 50), (170, 170, 170)
    OX, OY = 230, 210
    SX, SY = OX + 200 * S, 320
    img = Image.new("RGB", (SX + 120 * S, 1120), "white")
    d = ImageDraw.Draw(img)
    P = lambda x, y: (OX + x * S, OY + y * S)
    Q = lambda xs, y: (SX + xs * S, SY + y * S)
    d.text((OX, 60), "DETAIL A \u00b7 KANTUNG VON VORN \u00b7 10:1", font=fb, fill=(90, 90, 90))
    d.text((SX - 44 * S, 60), "DETAIL B \u00b7 SCHNITT DURCH DIE KANTUNG \u00b7 10:1", font=fb, fill=(90, 90, 90))

    # --- Detail A: LED-Band von vorn
    brushed(d, (*P(0, -5), *P(W, 32)), BRASS)
    d.rectangle([P(0, -5), P(W, 32)], outline=(120, 95, 50), width=2)
    d.line([P(0, 0), P(W, 0)], fill=(150, 120, 60), width=3)
    d.text(P(1, -2.5), "Biegekante = Oberkante Front (y = 0)", font=fd, fill=(110, 85, 45), anchor="lm")
    for (a, b) in WINS:
        d.rectangle([P(a, WIN_Y0), P(b, WIN_Y0 + WIN_H)], fill=(40, 40, 44), outline=(20, 20, 20))
    for (a, b) in SLITS:
        d.rectangle([P(a, BAND_MID - SLIT_H / 2), P(b, BAND_MID + SLIT_H / 2)], fill=(40, 40, 44),
                    outline=(20, 20, 20))
    for (x, y) in SCREWS[:2]:
        d.ellipse([P(x - SCREW_D / 2, y - SCREW_D / 2), P(x + SCREW_D / 2, y + SCREW_D / 2)],
                  outline=(120, 95, 50), width=2)
        d.ellipse([P(x - SCREW_HOLE / 2, y - SCREW_HOLE / 2), P(x + SCREW_HOLE / 2, y + SCREW_HOLE / 2)],
                  fill=(40, 40, 44))
    for x in DIFF_X:
        dashed(d, [P(x, -5), P(x, 21)], (170, 110, 110), w=2, dash=8, gap=5)
    dashed(d, [P(DIFF_X[0], DIFF_R), P(DIFF_X[1], DIFF_R)], (170, 110, 110), w=2, dash=8, gap=5)
    d.text(P(W + 1.5, DIFF_R), "Umriss Diffusor (R%d, x %d\u2013%d)" % (DIFF_R, DIFF_X[0], DIFF_X[1]), font=fd,
           fill=(170, 110, 110), anchor="lm")
    d.text(P(W + 1.5, SCREWS[0][1]), "4 \u00d7 \u00d8%s mit 90\u00b0-Senkung auf \u00d8%.0f" % (SCREW_HOLE, SCREW_D),
           font=fd, fill=(20, 20, 20), anchor="lm")
    hy = 38
    chain = [(0, LED_OFF, "%.0f (15 %%)" % LED_OFF), (LED_OFF, LED_OFF + SLIT_W, str(SLIT_W)),
             (LED_OFF + SLIT_W, WINS[0][0], str(GAP)), (WINS[0][0], WINS[0][1], str(WIN_W)),
             (WINS[0][1], WINS[1][0], str(WEB)), (WINS[1][0], WINS[1][1], str(WIN_W)),
             (WINS[1][1], SLITS[1][0], str(GAP)), (SLITS[1][0], SLITS[1][1], str(SLIT_W)),
             (SLITS[1][1], W, "%.0f (15 %%)" % LED_OFF)]
    for (a, b, lab) in chain:
        for x in (a, b):
            d.line([P(x, 32), P(x, hy + 1)], fill=ext, width=1)
        arrow2(d, P(a, hy), P(b, hy), col, w=2, head=7)
        d.text(P((a + b) / 2, hy - 1.3), lab, font=fd, fill=col, anchor="ms")
    for (y0, y1, lab, x) in ((WIN_Y0, WIN_Y0 + WIN_H, str(WIN_H), -3),
                             (BAND_MID - SLIT_H / 2, BAND_MID + SLIT_H / 2, str(SLIT_H), -9),
                             (0, WIN_Y0, str(WIN_Y0), -15)):
        for y in (y0, y1):
            d.line([P(x - 1, y), P(min(x + 5, -0.5), y)], fill=ext, width=1)
        arrow2(d, P(x, y0), P(x, y1), col, w=2, head=7)
        d.text(P(x - 0.8, (y0 + y1) / 2), lab, font=fd, fill=col, anchor="rm")
    leaders = [(WINS[0][1] - 2, WIN_Y0 + WIN_H, 46,
                "2 \u00d7 Fenster %d \u00d7 %d (Steg %d) \u2013 der LED-Streifen wird hier nach vorn gef\u00fchrt"
                % (WIN_W, WIN_H, WEB)),
               (SLITS[0][0] + 3, BAND_MID + SLIT_H / 2, 51,
                "2 \u00d7 Schlitz %d \u00d7 %s \u2013 Haltelaschen des Diffusors" % (SLIT_W, SLIT_H))]
    for (zx, zy, ty, t) in leaders:
        d.line([P(zx, zy), P(zx, ty - 1.2)], fill=ext, width=1)
        d.text(P(zx + 1, ty), t, font=fd, fill=(20, 20, 20), anchor="lm")

    # --- Detail B: Schnitt durch die Kantung
    d.rectangle([Q(-44, -22), Q(0, 40)], fill=(234, 227, 208))
    for y in range(-22, 40, 5):
        d.line([Q(-44, y + 5), Q(-39, y)], fill=(205, 196, 172), width=1)
    d.line([Q(0, -22), Q(0, 40)], fill=(90, 90, 90), width=3)
    d.rectangle([Q(-44, 4), Q(0, 40)], fill=(34, 34, 38))
    d.rectangle([Q(-41, 7), Q(-1.5, 40)], fill=(70, 70, 76))
    d.polygon([Q(xs, y) for xs, y in sheet_profile_clip(38, 40)], fill=(198, 164, 96), outline=(100, 78, 40))
    d.polygon([Q(xs, y) for xs, y in diffusor_profile()], fill=DIFF_COL, outline=(180, 172, 154))
    d.rectangle([Q(-8, BAND_MID - SLIT_H / 2), Q(T, BAND_MID + SLIT_H / 2)], fill=(95, 95, 102))
    d.polygon([Q(-8, BAND_MID - SLIT_H / 2), Q(-8, BAND_MID + SLIT_H / 2 + 2.5),
               Q(-4.5, BAND_MID + SLIT_H / 2)], fill=(95, 95, 102))
    d.rectangle([Q(T, WIN_Y0 - 1.5), Q(T + 1.4, WIN_Y0 + WIN_H + 1.5)], fill=(55, 62, 55))
    d.ellipse([Q(-1.6, CAP_TOP - 2.6), Q(1.6, CAP_TOP + 0.6)], fill=(150, 150, 150))
    d.ellipse([Q(T - 1.2, DIFF_R - 1.2), Q(T + 2.4, DIFF_R + 2.4)], fill=(150, 150, 150))
    arrow2(d, Q(T, -8), Q(T + DIFF_R, -8), col, w=2, head=7)
    d.text(Q(T + DIFF_R / 2, -9.3), str(DIFF_R), font=fd, fill=col, anchor="ms")
    d.line([Q(T + DIFF_R, -8), Q(T + DIFF_R, 1)], fill=ext, width=1)
    arrow2(d, Q(34, 0.2), Q(34, DIFF_R), col, w=2, head=7)
    d.text(Q(34.8, DIFF_R / 2), str(DIFF_R), font=fd, fill=col, anchor="lm")
    d.line([Q(T + DIFF_R, DIFF_R), Q(34, DIFF_R)], fill=ext, width=1)
    notes = [(-43, -18, "Innenradius %.0f" % BEND_RI, (90, 70, 40)),
             (-43, -14, "L\u00f6cher \u2265 %d mm von der Biegekante" % WIN_Y0, (90, 70, 40)),
             (38, 4, "Diffusor: Viertelrund R%d, wei\u00df," % DIFF_R, (20, 20, 20)),
             (38, 8, "Enden rund (Hotdog l\u00e4ngs geviertelt)", (20, 20, 20)),
             (38, 14, "LED-Streifen: durchs Fenster nach vorn,", (20, 20, 20)),
             (38, 18, "liegt in der Ecke im Diffusor", (20, 20, 20)),
             (38, 24, "Silikonfuge rundum \u2192 Fenster und", (20, 20, 20)),
             (38, 28, "Schlitze sind dicht", (20, 20, 20)),
             (-42, 20, "Lasche wird HINTER dem Blech", (235, 235, 235)),
             (-42, 24, "gesichert (Rastnase oder Schraube)", (235, 235, 235)),
             (-42, 28, "\u2192 von au\u00dfen unsichtbar", (235, 235, 235)),
             (-42, 36, "Kasten (Unterputz)", (235, 235, 235))]
    for (tx, ty, t, fill) in notes:
        d.text(Q(tx, ty), t, font=fd, fill=fill, anchor="lm")
    for (zx, zy, tx, ty) in ((T + 12, 9, 37, 5), (T + 1, WIN_Y0 + 3, 37, 15), (T + 1.5, DIFF_R + 1, 37, 25)):
        d.line([Q(zx, zy), Q(tx, ty)], fill=ext, width=1)

    d.text((OX, img.height - 130),
           "Blech 2 mm Messing: Front 100 \u00d7 260, oben 85\u00b0 gekantet, Dach 60, Tropfkante 6. Durchbr\u00fcche: "
           "Gitter 5 \u00d7 18 Schr\u00e4gschlitze, Display 58 \u00d7 104 (y = 64\u2013168), Knopfloch, 2 \u00d7 Mikro \u00d81,2,",
           font=fd, fill=(90, 90, 90))
    d.text((OX, img.height - 100),
           "4 \u00d7 \u00d8%s gesenkt, 2 \u00d7 LED-Fenster %d \u00d7 %d, 2 \u00d7 Laschenschlitz %d \u00d7 %s. "
           "Alle Ma\u00dfe in layout-v5-bemasst.svg (1 Einheit = 1 mm)." % (SCREW_HOLE, WIN_W, WIN_H, SLIT_W, SLIT_H),
           font=fd, fill=(90, 90, 90))
    d.text((OX, img.height - 70),
           "Offen f\u00fcrs CAD: Knopfloch nach dem echten Taster ausmessen (Platzhalter \u00d822) \u00b7 "
           "Displayausschnitt ggf. 0,5 mm \u00dcberdeckung zur aktiven Fl\u00e4che 58,32 \u00d7 103,68 \u00b7 "
           "Kabeleinf\u00fchrung in den Kasten.", font=fd, fill=(150, 60, 60))
    img.save(os.path.join(HERE, "detail-kantung-v5.png"))


def measure_ink(img, OX, OY, S, y0_mm, y1_mm, ink=INK):
    px = img.load()
    xs = [x for y in range(int(OY + y0_mm * S), int(OY + y1_mm * S))
          for x in range(int(OX + 5 * S), int(OX + 95 * S))
          if all(abs(a - b) < 40 for a, b in zip(px[x, y][:3], ink))]
    return ((min(xs) - OX) / S, (max(xs) + 1 - OX) / S) if xs else None


# ------------------------------------------------------------------ SVG, bemaßt
def make_svg(face):
    o = []
    A = o.append
    A('<svg xmlns="http://www.w3.org/2000/svg" width="360mm" height="380mm" viewBox="-40 -70 360 380" '
      'font-family="Arial, sans-serif">')
    A('<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" '
      'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#333"/></marker></defs>')
    A('<rect x="-40" y="-70" width="360" height="380" fill="white"/>')
    ln = 'stroke="#222" stroke-width="0.3"'
    dim = 'stroke="#333" stroke-width="0.25" marker-start="url(#a)" marker-end="url(#a)"'
    hid = 'stroke="#555" stroke-width="0.3" stroke-dasharray="2 1.2" fill="none"'
    aux = 'stroke="#c66" stroke-width="0.3" stroke-dasharray="3 1.5 0.6 1.5" fill="none"'
    pts = lambda seq: " ".join(f"{x:.2f},{y:.2f}" for x, y in seq)
    A(f'<rect x="0" y="0" width="{W}" height="{H}" {ln} fill="#f3e6c8"/>')
    A(f'<rect x="{BOX[0]}" y="{BOX[1]}" width="{BOX[2] - BOX[0]}" height="{BOX[3] - BOX[1]}" {hid}/>')
    A(f'<rect x="0" y="{CAP_TOP:.2f}" width="{W}" height="{BAND_BOT - CAP_TOP:.2f}" {ln} fill="#e2cf9f"/>')
    for (a, b) in WINS:
        A(f'<rect x="{a}" y="{WIN_Y0}" width="{b - a}" height="{WIN_H}" {ln} fill="#444"/>')
    for (a, b) in SLITS:
        A(f'<rect x="{a}" y="{BAND_MID - SLIT_H / 2}" width="{b - a}" height="{SLIT_H}" {ln} fill="#444"/>')
    A(f'<path {aux} d="M{DIFF_X[0]},-2 V{DIFF_R} H{DIFF_X[1]} V-2"/>')
    for (x, y) in SCREWS:
        A(f'<circle cx="{x}" cy="{y}" r="{SCREW_D / 2}" {ln} fill="#e8d6a8"/>')
        A(f'<circle cx="{x}" cy="{y}" r="{SCREW_HOLE / 2}" fill="#444"/>')
    A(f'<circle cx="{RING_C[0]}" cy="{RING_C[1]}" r="{RING_D / 2}" {ln} fill="#e2cf9f"/>')
    A(f'<circle cx="{RING_C[0]}" cy="{RING_C[1]}" r="{BTN_HOLE / 2}" {ln} fill="#444"/>')
    for (mx, my) in MIC:
        A(f'<circle cx="{mx}" cy="{my}" r="{MIC_D / 2}" fill="#222"/>')

    def engrave(glyphs, s, base, x0=COL_X0):
        for ch, x_mm, dy in glyphs:
            A(f'<path fill="#222" transform="translate({x0 + x_mm:.3f} {base - dy * s:.3f}) '
              f'scale({s:.5f} {-s:.5f})" d="{face.path_d(ch)}"/>')

    cap_h, s, t_names, gl = layout_names(face)
    engrave(gl, s, NAMES_BASE)
    s2, t_fam, gl2 = layout_family(face)
    engrave(gl2, s2, FAMILY_BASE)
    A(f'<rect x="{SCR[0]}" y="{SCR[1]}" width="{SCR[2] - SCR[0]}" height="{SCR[3] - SCR[1]}" {ln} fill="#e4e3dd"/>')
    for poly in slash_polys():
        A(f'<polygon fill="#444" points="{pts(poly)}"/>')
    A(f'<line x1="-10" y1="0" x2="-10" y2="{H}" {dim}/>')
    A(f'<text x="-12" y="{H / 2}" font-size="3.4" text-anchor="middle" transform="rotate(-90 -12 {H / 2})">{H}</text>')
    A(f'<line x1="0" y1="{H + 10}" x2="{W}" y2="{H + 10}" {dim}/>')
    A(f'<text x="{W / 2}" y="{H + 8.5}" font-size="3.4" text-anchor="middle">{W}</text>')
    # Maßkette des LED-Bandes
    chain = [(0, LED_OFF, f"{LED_OFF:.0f}"), (LED_OFF, LED_OFF + SLIT_W, f"{SLIT_W}"),
             (LED_OFF + SLIT_W, WINS[0][0], f"{GAP}"), (WINS[0][0], WINS[0][1], f"{WIN_W}"),
             (WINS[0][1], WINS[1][0], f"{WEB}"), (WINS[1][0], WINS[1][1], f"{WIN_W}"),
             (WINS[1][1], SLITS[1][0], f"{GAP}"), (SLITS[1][0], SLITS[1][1], f"{SLIT_W}"),
             (SLITS[1][1], W, f"{LED_OFF:.0f}")]
    for (a, b, lab) in chain:
        A(f'<line x1="{a}" y1="-16" x2="{b}" y2="-16" {dim}/>')
        A(f'<text x="{(a + b) / 2}" y="-17" font-size="2.6" text-anchor="middle">{lab}</text>')
    ords = [(CAP_TOP, f"{CAP_TOP:.0f} Oberkante Dach (an der Wand)"), (0, "0 Biegekante / Oberkante Front"),
            (BAND_BOT, f"{BAND_BOT:.1f} Unterkante Tropfkante"),
            (WIN_Y0, f"{WIN_Y0} LED-Fenster oben ({WIN_W} × {WIN_H}, 2 ×)"),
            (BAND_MID, f"{BAND_MID:.0f} Mitte Laschenschlitze ({SLIT_W} × {SLIT_H}, 2 ×)"),
            (DIFF_R, f"{DIFF_R} Unterkante Diffusor (Viertelrund, x {DIFF_X[0]}–{DIFF_X[1]})"),
            (SCREWS[0][1], f"{SCREWS[0][1]} obere Schrauben (x = 8 / 92)"),
            (GRILLE_Y0, f"{GRILLE_Y0} Gitter oben"),
            (GRILLE_Y0 + (ROWS - 1) * ROW_PITCH + SLASH_H,
             f"{GRILLE_Y0 + (ROWS - 1) * ROW_PITCH + SLASH_H} Gitter unten"),
            (SCR[1], f"{SCR[1]} Display oben"), (SCR[3], f"{SCR[3]} Display unten"),
            (NAMES_BASE, f"{NAMES_BASE} Grundlinie Vornamen ({cap_h:.1f} hoch)"),
            (FAMILY_BASE, f"{FAMILY_BASE} Grundlinie {FAMILY} ({FAMILY_CAP:.0f} hoch)"),
            (RING_C[1], f"{RING_C[1]} Knopfmitte (Ring Ø40, Loch Ø{BTN_HOLE} = Platzhalter)"),
            (SCREWS[2][1], f"{SCREWS[2][1]} untere Schrauben (x = 8 / 92)"), (H, f"{H} Unterkante Front")]
    for i, (y, lab) in enumerate(ords):
        ty = -8 + i * 18
        A(f'<line x1="{W}" y1="{y:.2f}" x2="{W + 8}" y2="{ty:.2f}" stroke="#999" stroke-width="0.2"/>')
        A(f'<text x="{W + 9}" y="{ty + 1.1:.2f}" font-size="3" fill="#333">y = {lab}</text>')
    # Seitenschnitt
    A('<g transform="translate(250 0)">')
    A(f'<rect x="-60" y="-40" width="60" height="{H + 60}" fill="#efe9d8"/>')
    A(f'<line x1="0" y1="-40" x2="0" y2="{H + 20}" stroke="#555" stroke-width="0.8"/>')
    A(f'<rect x="{-BOX_DEPTH}" y="{BOX[1]}" width="{BOX_DEPTH}" height="{BOX[3] - BOX[1]}" fill="#222"/>')
    A(f'<polygon {ln} fill="#c9a861" points="{pts(sheet_profile())}"/>')
    A(f'<polygon {ln} fill="#fbf7ec" points="{pts(diffusor_profile())}"/>')
    A(f'<rect x="-7" y="{BAND_MID - SLIT_H / 2}" width="{7 + T}" height="{SLIT_H}" {ln} fill="#888"/>')
    A(f'<rect x="{T}" y="{WIN_Y0 - 2}" width="1.4" height="{WIN_H + 4}" {ln} fill="#4a524a"/>')
    for y in (SCREWS[0][1], SCREWS[2][1]):
        A(f'<rect x="-12" y="{y - 0.8}" width="{12 + T - 1.6}" height="1.6" fill="#777"/>')
        A(f'<polygon fill="#d9bb7a" stroke="#222" stroke-width="0.2" points="{T},{y - 3} {T},{y + 3} '
          f'{T - 1.7},{y + 1.5} {T - 1.7},{y - 1.5}"/>')
    A(f'<rect x="{T}" y="{RING_C[1] - BTN_D / 2}" width="4" height="{BTN_D}" rx="1.5" {ln} fill="#e8d6a8"/>')
    A(f'<line x1="0" y1="-20" x2="{CAP_LEN}" y2="-20" {dim}/>')
    A(f'<text x="{CAP_LEN / 2}" y="-21.5" font-size="3.4" text-anchor="middle">Dach {CAP_LEN} ab Wand</text>')
    A(f'<line x1="{-BOX_DEPTH}" y1="-32" x2="0" y2="-32" {dim}/>')
    A(f'<text x="{-BOX_DEPTH / 2}" y="-33.5" font-size="3.2" text-anchor="middle">{BOX_DEPTH} (Platzhalter)</text>')
    A(f'<text x="20" y="20" font-size="3.2" fill="#c33">{CAP_ANGLE}° (5° Gefälle), Innenradius {BEND_RI:.0f}</text>')
    notes = [(CAP_LEN + 2, BAND_BOT - 2, f"Tropfkante {CAP_DRIP}"),
             (T + DIFF_R + 2, 6, f"Diffusor Viertelrund R{DIFF_R}, Enden rund, ABS/PLA weiß"),
             (T + DIFF_R + 2, 10.5, "Silikonfuge rundum → Fenster und Schlitze sind dicht"),
             (T + 3, WIN_Y0 + WIN_H + 7, "LED-Streifen durchs Fenster nach vorn, liegt in der Ecke"),
             (-38, 100, "Kasten (Unterputz)"), (-58, 60, "Putz / Dämmung"),
             (-38, BAND_MID + 8, "Lasche hinter dem Blech gesichert (Rastnase/Schraube)"),
             (6, 80, "Front + Dach = EIN Blech, 2 mm"),
             (-58, 130, "Kabelweg: offen"),
             (4, -6, "Silikonfuge Dach/Wand; unten offen lassen (Drainage)")]
    for (tx, ty, t) in notes:
        fill = "#ddd" if tx < -30 and ty > 50 else "#444"
        A(f'<text x="{tx:.1f}" y="{ty:.1f}" font-size="3" fill="{fill}">{t}</text>')
    A('</g>')
    A('<text x="-38" y="-60" font-size="4.4" font-weight="bold">Hausklingel – Unterputz, Front + Dach aus einem '
      'Blech, LED-Band in der Kantung, Entwurf v5 (2026-09-17) · Maße in mm</text>')
    info = [
        f"Schrift {FONT_LABEL} · Vornamen und {FAMILY} exakt {COL_X1 - COL_X0} mm breit, bündig mit Display und Gitter",
        f"Gitter {ROWS} × {PER_ROW} Schrägschlitze {SLOT_W} × {SLASH_H}, {SLASH_ANG}°, Teilung {SL_PITCH:.2f}, Steg {SL_WEB:.2f}",
        f"Schrauben: 4 × M3 Senkkopf Messing, ein Schlitz (DIN 963), senkrecht; Loch Ø{SCREW_HOLE} + 90°-Senkung "
        f"auf Ø{SCREW_D:.0f}; Gewindeeinsätze im Kasten",
        f"LED-Band: 2 Fenster {WIN_W} × {WIN_H} (Steg {WEB}), außen 2 Schlitze {SLIT_W} × {SLIT_H} für die "
        f"Diffusor-Laschen, je {LED_OFF:.0f} mm (15 %) Abstand zur Seite",
        f"Kasten außen {BOX[2] - BOX[0]} × {BOX[3] - BOX[1]} (4 mm unter der Front verdeckt), Tiefe offen; "
        "Kabelweg in den Kasten offen (kein Rohr)",
    ]
    for i, t in enumerate(info):
        A(f'<text x="-38" y="{-54 + i * 4.4}" font-size="3" fill="#555">{t}</text>')
    A('</svg>')
    with open(os.path.join(HERE, "layout-v5-bemasst.svg"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(o))


if __name__ == "__main__":
    face = Face(FONT_FILE)
    (cap_h, t_names, t_fam), img, OX, OY, S = make_reference(face)
    make_svg(face)
    make_gemini_sheet(face)
    make_detail()
    print(f"{FONT_LABEL}: Vornamen {cap_h:.2f} mm, Laufweite {t_names:.2f}; {FAMILY} Laufweite {t_fam:.2f}")
    print(f"Dach: Gefälle {CAP_DROP:.2f} mm, Tropfkante unten bei y = {BAND_BOT:.2f}")
    print(f"LED-Band: Schlitze {SLITS}, Fenster {WINS}, Diffusor x {DIFF_X}, R {DIFF_R}")
    print("gemessen Vornamen:", measure_ink(img, OX, OY, S, NAMES_BASE - 5, NAMES_BASE + 1))
    print(f"gemessen {FAMILY}:", measure_ink(img, OX, OY, S, FAMILY_BASE - 9, FAMILY_BASE + 1))
