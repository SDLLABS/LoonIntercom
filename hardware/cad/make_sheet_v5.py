"""Klingel v5 - Frontblech (Front + Dach, EIN gekantetes Blech, 2 mm).

Run inside FreeCAD (MCP), in zwei Schritten - Dokument und Ansicht NUR im GUI-Thread:
    exec(open(r"C:\\AI_Projects\\Intercom\\cad\\make_sheet_v5.py", encoding="utf-8").read())
    build_shape()   # schwere OCCT-Booleans, kein Dokument, kein GUI
    assemble()      # Dokument, Farbe, Ansicht, Export

Masse aus ../front-sheet/make_layout_v5.py bzw. layout-v5-bemasst.svg.
Gemeinsame Masse mit dem Kasten kommen aus kasten_v3_params.py - keine zweite Kopie mehr.

Zeichnung: x nach rechts, y nach UNTEN, Ursprung = linke obere Ecke der Front.
CAD-Achsen: X = x (Breite), Z = -y (Hoehe), Y = -xs (Wand bei Y = 0, Front bei Y = -2,
Dachvorderkante bei Y = -60). Y ist gespiegelt, damit FreeCADs VORDERANSICHT die echte
Vorderseite zeigt und die Schrift richtig herum steht - mit Y = +xs steht alles spiegelverkehrt.
"""
import math
import os
import re
import sys

import FreeCAD as App
import Part
from FreeCAD import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kasten_v3_params as _P   # gemeinsame Massquelle mit dem Kasten

# ------------------------------------------------------------------ Masse
W, H, T = 100.0, 260.0, 2.0
BEND_RI = 2.0
CAP_LEN, CAP_ANGLE, CAP_DRIP = 60.0, 85.0, 6.0

GRILLE_Y0, ROWS, PER_ROW = _P.GRILLE["row0"], _P.GRILLE["rows"], 18   # v3: 3 statt 5 Reihen
ROW_PITCH, SLASH_H, SLOT_W, SLASH_ANG = 7.0, 5.0, 1.5, 70.0
COL_X0, COL_X1 = 21.0, 79.0

SCR_VIS = (21.0, 64.0, 79.0, 168.0)       # sichtbare Displayflaeche 58 x 104
SCR_OVERLAP = True                         # Blech ueberdeckt die Aktivflaeche ~0.5 mm
SCR_CUT = (57.3, 102.7)

BTN_C, RING_D, RING_FIT = _P.BTN_C, _P.RING_D, 1.0      # EINGEFROREN (siehe _P.FROZEN)
BTN_HOLE = RING_D + RING_FIT                            # 49.5 im Blech
MIC, MIC_D = [(82.0, 221.0), (82.0, 229.0)], 1.2
SCREWS = _P.SCREWS                                      # v3 nach innen versetzt
SCREW_HOLE, SCREW_HEAD, SCREW_ANG = 3.2, 6.0, 90.0      # M3 Senkkopf DIN 963

LED_OFF = 0.15 * W
SLIT_W, SLIT_H = 10.0, 2.6
WIN_W, WIN_H, WEB, GAP = 18.0, 6.0, 6.0, 4.0
WIN_Y0 = 8.0
BAND_MID = WIN_Y0 + WIN_H / 2
SLITS = [(LED_OFF, LED_OFF + SLIT_W), (W - LED_OFF - SLIT_W, W - LED_OFF)]
_w0 = LED_OFF + SLIT_W + GAP
WINS = [(_w0, _w0 + WIN_W), (_w0 + WIN_W + WEB, _w0 + 2 * WIN_W + WEB)]

ENGRAVE_DEPTH = 0.3
SVG = os.path.join(HERE, "..", "front-sheet", "layout-v5-bemasst.svg")
OUT = os.path.join(HERE, "out")
BREP = os.path.join(OUT, "_frontblech_v5.brep")
SIDE = -1.0                                # Tiefenrichtung: vor der Wand = -Y

_A = math.radians(90 - CAP_ANGLE)          # 5 Grad Gefaelle
_t, _sec = math.tan(_A), 1 / math.cos(_A)
roof_top = lambda xs: -T + xs * _t
roof_under = lambda xs: xs * _t + T * (_sec - 1)
BAND_BOT = roof_under(CAP_LEN) + CAP_DRIP

SL_W = SLOT_W / math.sin(math.radians(SLASH_ANG))
SL_OFF = SLASH_H / math.tan(math.radians(SLASH_ANG))
SL_PITCH = (COL_X1 - SL_OFF - SL_W - COL_X0) / (PER_ROW - 1)


# ------------------------------------------------------------------ Querschnitt
def sheet_solid():
    """Front + Dach als ein gekantetes Blech: Profil in der YZ-Ebene, ueber die Breite extrudiert."""
    cy, cz = T + BEND_RI, BEND_RI * _sec + (T + BEND_RI) * _t + T * (_sec - 1)
    C = (cy, cz)                                   # Mittelpunkt beider Kantungsradien, (xs, y)

    def foot(c, m, b):                             # Lotfusspunkt auf y = m*xs + b
        xs = (c[0] + m * (c[1] - b)) / (1 + m * m)
        return (xs, m * xs + b)

    p_out_top = foot(C, _t, -T)                    # Tangente an die Dachoberseite
    p_in_top = foot(C, _t, T * (_sec - 1))         # Tangente an die Dachunterseite

    def arc(p0, p1, r):
        v0 = (p0[0] - C[0], p0[1] - C[1])
        v1 = (p1[0] - C[0], p1[1] - C[1])
        n0, n1 = math.hypot(*v0), math.hypot(*v1)
        mx, my = v0[0] / n0 + v1[0] / n1, v0[1] / n0 + v1[1] / n1
        nm = math.hypot(mx, my)
        return (C[0] + r * mx / nm, C[1] + r * my / nm)

    S = lambda p: V(0.0, SIDE * p[0], -p[1])       # (xs, y) -> CAD
    a_out = arc((0.0, cz), p_out_top, T + BEND_RI)
    a_in = arc(p_in_top, (T, cz), BEND_RI)

    edges = [
        Part.makeLine(S((0.0, H)), S((0.0, cz))),                       # Rueckseite an der Wand
        Part.Arc(S((0.0, cz)), S(a_out), S(p_out_top)).toShape(),       # Kantung aussen, R4
        Part.makeLine(S(p_out_top), S((CAP_LEN, roof_top(CAP_LEN)))),   # Dach oben
        Part.makeLine(S((CAP_LEN, roof_top(CAP_LEN))), S((CAP_LEN, BAND_BOT))),        # Tropfkante
        Part.makeLine(S((CAP_LEN, BAND_BOT)), S((CAP_LEN - T, BAND_BOT))),
        Part.makeLine(S((CAP_LEN - T, BAND_BOT)), S((CAP_LEN - T, roof_under(CAP_LEN - T)))),
        Part.makeLine(S((CAP_LEN - T, roof_under(CAP_LEN - T))), S(p_in_top)),         # Dach unten
        Part.Arc(S(p_in_top), S(a_in), S((T, cz))).toShape(),           # Kantung innen, R2
        Part.makeLine(S((T, cz)), S((T, H))),                           # Frontflaeche
        Part.makeLine(S((T, H)), S((0.0, H))),                          # Unterkante
    ]
    face = Part.Face(Part.Wire(Part.__sortEdges__(edges)))
    return face.extrude(V(W, 0, 0))


# ------------------------------------------------------------------ Durchbrueche
def prism(poly, y0=1.0, h=T + 2.0):
    w = Part.makePolygon([V(x, y0, -y) for (x, y) in poly] + [V(poly[0][0], y0, -poly[0][1])])
    return Part.Face(w).extrude(V(0, SIDE * h, 0))


def rect(x0, y0, x1, y1):
    return prism([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def hole(x, y, d):
    return Part.makeCylinder(d / 2, T + 2.0, V(x, 1.0, -y), V(0, SIDE, 0))


def slash_polys():
    out = []
    for r in range(ROWS):
        yt = GRILLE_Y0 + r * ROW_PITCH
        yb = yt + SLASH_H
        for i in range(PER_ROW):
            x0 = COL_X0 + i * SL_PITCH
            out.append([(x0, yb), (x0 + SL_W, yb), (x0 + SL_OFF + SL_W, yt), (x0 + SL_OFF, yt)])
    return out


def countersink(x, y):
    """90-Grad-Senkung von der Frontseite auf Kopfdurchmesser."""
    over = 0.5
    r_top = SCREW_HEAD / 2 + over * math.tan(math.radians(SCREW_ANG / 2))
    depth = (SCREW_HEAD - SCREW_HOLE) / 2 / math.tan(math.radians(SCREW_ANG / 2)) + over
    return Part.makeCone(r_top, SCREW_HOLE / 2, depth, V(x, SIDE * (T + over), -y), V(0, -SIDE, 0))


# ------------------------------------------------------------------ Gravur aus dem SVG
def svg_glyph_faces(path=SVG, plane_y=None):
    """Die Buchstaben-Pfade (fill #222) aus dem bemassten SVG als Flaechen."""
    plane_y = SIDE * (T - ENGRAVE_DEPTH) if plane_y is None else plane_y
    src = open(path, encoding="utf-8").read()
    pat = re.compile(r'<path fill="#222" transform="translate\(([-\d.]+) ([-\d.]+)\) '
                     r'scale\(([-\d.]+) ([-\d.]+)\)" d="([^"]+)"')
    num = re.compile(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?')
    faces = []
    for m in pat.finditer(src):
        tx, ty, sx, sy = (float(v) for v in m.groups()[:4])
        pt = lambda px, py: V(tx + sx * px, plane_y, -ty + (-sy) * py)   # sy negativ (SVG-Flip)
        wires, edges = [], []
        cur = start = None
        for cmd, args in re.findall(r'([MLHVQZmlhvqz])([^MLHVQZmlhvqz]*)', m.group(5)):
            a = [float(v) for v in num.findall(args)]
            if cmd == 'M':
                cur = start = (a[0], a[1])
            elif cmd == 'L':
                nxt = (a[0], a[1]); edges.append(Part.makeLine(pt(*cur), pt(*nxt))); cur = nxt
            elif cmd == 'H':
                nxt = (a[0], cur[1]); edges.append(Part.makeLine(pt(*cur), pt(*nxt))); cur = nxt
            elif cmd == 'V':
                nxt = (cur[0], a[0]); edges.append(Part.makeLine(pt(*cur), pt(*nxt))); cur = nxt
            elif cmd == 'Q':
                for i in range(0, len(a), 4):
                    c, nxt = (a[i], a[i + 1]), (a[i + 2], a[i + 3])
                    bez = Part.BezierCurve()
                    bez.setPoles([pt(*cur), pt(*c), pt(*nxt)])
                    edges.append(bez.toShape())
                    cur = nxt
            elif cmd in 'Zz':
                if cur != start:
                    edges.append(Part.makeLine(pt(*cur), pt(*start)))
                wires.append(Part.Wire(Part.__sortEdges__(edges)))
                edges, cur = [], start
        if edges:
            wires.append(Part.Wire(Part.__sortEdges__(edges)))
        faces.append(Part.makeFace(wires, "Part::FaceMakerBullseye"))   # Punzen bleiben stehen
    return faces


# ------------------------------------------------------------------ Bauen
def build_shape():
    sheet = sheet_solid()
    cuts = [prism(p) for p in slash_polys()]                            # Lautsprechergitter

    cx, cy_ = (SCR_VIS[0] + SCR_VIS[2]) / 2, (SCR_VIS[1] + SCR_VIS[3]) / 2
    sw, sh = (SCR_CUT if SCR_OVERLAP else (SCR_VIS[2] - SCR_VIS[0], SCR_VIS[3] - SCR_VIS[1]))
    cuts.append(rect(cx - sw / 2, cy_ - sh / 2, cx + sw / 2, cy_ + sh / 2))            # Display

    cuts.append(hole(BTN_C[0], BTN_C[1], BTN_HOLE))                     # Tasterloch, Ring liegt darin
    cuts += [hole(x, y, MIC_D) for (x, y) in MIC]                       # Mikrofone
    cuts += [hole(x, y, SCREW_HOLE) for (x, y) in SCREWS]               # Schrauben
    cuts += [countersink(x, y) for (x, y) in SCREWS]                    # + 90-Grad-Senkung
    cuts += [rect(a, WIN_Y0, b, WIN_Y0 + WIN_H) for (a, b) in WINS]     # LED-Fenster
    cuts += [rect(a, BAND_MID - SLIT_H / 2, b, BAND_MID + SLIT_H / 2) for (a, b) in SLITS]

    engrave = [f.extrude(V(0, SIDE * (ENGRAVE_DEPTH + 0.3), 0)) for f in svg_glyph_faces()]
    shape = sheet.cut(cuts + engrave).removeSplitter()

    os.makedirs(OUT, exist_ok=True)
    shape.exportBrep(BREP)
    report(shape, sw, sh)
    return shape


def assemble():
    """Dokument, Farbe, Ansicht, Export - NUR im GUI-Thread."""
    import Mesh
    shape = Part.Shape()
    shape.importBrep(BREP)
    doc = App.newDocument("Klingel_Frontblech_v5")
    obj = doc.addObject("Part::Feature", "Frontblech")
    obj.Shape = shape
    doc.recompute()
    if App.GuiUp:
        import FreeCADGui as Gui
        obj.ViewObject.ShapeColor = (0.77, 0.63, 0.36)
        Gui.ActiveDocument.ActiveView.viewAxonometric()
        Gui.SendMsgToActiveView("ViewFit")
    doc.saveAs(os.path.join(OUT, "klingel_frontblech_v5.FCStd"))
    Part.export([obj], os.path.join(OUT, "klingel_frontblech_v5.step"))
    Mesh.export([obj], os.path.join(OUT, "klingel_frontblech_v5.stl"))
    print("gespeichert:", OUT)
    return doc, obj


# ------------------------------------------------------------------ Druckteilung
SEAM = 18.0            # Trennung bei Zeichnungs-y (Unterkante Diffusor)
LAP_Y0 = 14.5          # Stufenfalz von y 14.5 bis zur Naht: unter den LED-Fenstern (Ende y 14),
LAP_T = 0.8            # ueber dem Gitter. Zunge = hintere 0.8 mm, volle Breite.
LAP_GAP = 0.15         # Luft fuer FDM
PEG_X, PEG_D, PEG_H = (25.0, 75.0), 2.0, 0.4   # Passzapfen statt Stifte - 2 mm Blech
PEG_Y = (LAP_Y0 + SEAM) / 2


def split_for_print():
    """Master bleibt einteilig. Fuer den Druck: unteres Teil + oberes Teil mit Stufenfalz."""
    sh = Part.Shape()
    sh.importBrep(BREP)
    big = 400.0
    below = Part.makeBox(120, 80, big, V(-10, -70.0, -big - SEAM))          # unterhalb der Naht
    lap = Part.makeBox(120, LAP_T, SEAM - LAP_Y0, V(-10, 0.0, -SEAM))      # Zunge, hintere 0.8 mm
    lap.translate(V(0, -LAP_T, 0))
    pocket = Part.makeBox(120, LAP_T + LAP_GAP, SEAM - LAP_Y0 + LAP_GAP,
                          V(-10, -LAP_T - LAP_GAP, -SEAM))                 # Tasche mit Luft

    pegs = [Part.makeCylinder(PEG_D / 2, PEG_H, V(x, -LAP_T, -PEG_Y), V(0, -1, 0)) for x in PEG_X]
    holes = [Part.makeCylinder(PEG_D / 2 + 0.2, PEG_H + 0.1, V(x, -LAP_T - LAP_GAP, -PEG_Y),
                               V(0, -1, 0)) for x in PEG_X]

    unten = sh.common(below.fuse(lap)).fuse(pegs).removeSplitter()
    oben = sh.cut(below.fuse(pocket)).cut(holes).removeSplitter()
    return unten, oben


def export_split(dev=0.02):
    import Mesh
    unten, oben = split_for_print()
    out = []
    for name, sh, rot in (("unten", unten, -90.0), ("oben", oben, 175.0)):
        s = sh.copy()
        s.rotate(V(0, 0, 0), V(1, 0, 0), rot)      # unten: Rueckseite aufs Bett / oben: Dach aufs Bett
        bb = s.BoundBox
        s.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
        bb = s.BoundBox
        Mesh.Mesh(s.tessellate(dev)).write(os.path.join(OUT, "klingel_frontblech_v5_print_%s.stl" % name))
        print("%-6s %6.1f x %6.1f x %5.1f mm | Solids %d | valid %s | %.1f mm3"
              % (name, bb.XLength, bb.YLength, bb.ZLength, len(sh.Solids), sh.isValid(), sh.Volume))
        out.append(bb)
    ganz = Part.Shape()
    ganz.importBrep(BREP)
    print("Summe %.1f von %.1f mm3 (Differenz = Fugenluft)" % (unten.Volume + oben.Volume, ganz.Volume))
    x = out[0].XLength + out[1].XLength + 10
    y = max(out[0].YLength, out[1].YLength)
    print("beide nebeneinander: %.1f x %.1f mm auf 256 x 256 -> %s"
          % (x, y, "passt" if x < 256 and y < 256 else "PASST NICHT"))


def export_print(dev=0.02):
    """STL einteilig: Rueckseite auf dem Bett, Front nach oben."""
    import Mesh
    sh = Part.Shape()
    sh.importBrep(BREP)
    sh = sh.copy()
    sh.rotate(V(0, 0, 0), V(1, 0, 0), -90.0)
    bb = sh.BoundBox
    sh.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
    bb = sh.BoundBox
    Mesh.Mesh(sh.tessellate(dev)).write(os.path.join(OUT, "klingel_frontblech_v5_print.stl"))
    print("Druck-STL  %.1f x %.1f x %.1f mm (Bett-Diagonale noetig ab 260 mm Kante)"
          % (bb.XLength, bb.YLength, bb.ZLength))


# ------------------------------------------------------------------ Nachrechnen
def check(brep=None):
    sh = Part.Shape()
    sh.importBrep(brep or BREP)
    slab = lambda a, b: sh.common(Part.makeBox(120, abs(b - a), 320, V(-10, min(a, b), -300))).Volume
    gravur = slab(-1.3, -1.0) - slab(-2.0, -1.7)
    print("Gravur: %.1f mm3 entfernt = %.1f mm2 Schrift bei %.1f tief"
          % (gravur, gravur / ENGRAVE_DEPTH, ENGRAVE_DEPTH))
    for name, box in (("Displayausschnitt", Part.makeBox(80, 4, 120, V(10, -3, -180))),
                      ("Knopfbereich", Part.makeBox(60, 4, 60, V(20, -3, -255)))):
        print("%-18s Restvolumen %.1f mm3" % (name, sh.common(box).Volume))


def report(shape, sw, sh_):
    bb = shape.BoundBox
    print("Solids       :", len(shape.Solids), "| valid:", shape.isValid())
    print("BoundBox  X/Y/Z: %.2f / %.2f / %.2f" % (bb.XLength, bb.YLength, bb.ZLength))
    print("Y (Wand = 0)   : %.2f .. %.2f  (Dachtiefe %.0f, Front bei %.0f)"
          % (bb.YMin, bb.YMax, CAP_LEN, SIDE * T))
    print("Z (oben/unten) : %.2f .. %.2f  (Tropfkante unten y=%.2f)" % (bb.ZMin, bb.ZMax, BAND_BOT))
    print("Volumen        : %.1f mm3  -> Messing 8.5 g/cm3 = %.0f g"
          % (shape.Volume, shape.Volume * 8.5e-3))
    print("Gitter: %d Reihen, y %.0f..%.0f | Gravurtiefe %.1f | Display %.1f x %.1f | Taster %.1f"
          % (ROWS, GRILLE_Y0, GRILLE_Y0 + (ROWS - 1) * ROW_PITCH + SLASH_H,
             ENGRAVE_DEPTH, sw, sh_, BTN_HOLE))
    for nm, (fx, fy, fr) in (("Mikro", (82.0, 221.0, MIC_D / 2)),
                             ("Schraube unten", (SCREWS[3][0], SCREWS[3][1], SCREW_HEAD / 2)),
                             ("Gravur Familienname", (50.0, 193.5, 0.0))):
        print("  Luft Tasterloch -> %-15s %.2f mm"
              % (nm, math.hypot(fx - BTN_C[0], fy - BTN_C[1]) - fr - BTN_HOLE / 2))
