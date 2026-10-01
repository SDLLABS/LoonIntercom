"""Klingel v5 - Diffusor (ABS/PLA weiss), Stand 2026-09-18.

Viertelrundstab in der Innenecke zwischen Frontblech und Dach, Enden kugelig ("Hotdog laengs
geviertelt"). Hohl: der LED-Streifen liegt darin, das Blech und die Dachunterseite schliessen die
Kammer. Zwei Laschen greifen durch die Blechschlitze.

Quellen: klingel\\HANDOFF-CAD-BLECH.md, entwurf\\make_layout_v5.py (DIFF_R=18, DIFF_X=13..87).
Tags: [DB] aus Zeichnung/Datenblatt · [FREI] Konstruktionswahl · [PLATZ] Platzhalter.

ZWEI KORREKTUREN GEGENUEBER DER ZEICHNUNG:
 1. Die Zeichnung legt die Diffusor-Oberseite waagerecht auf y = 0.1826. Die Dachunterseite faellt
    aber 5 Grad nach vorn - am aeusseren Ende laege der Diffusor damit 1.57 mm IM Dach.
    Hier ist die Oberseite mitgeneigt.
 2. Die Ecke Blech/Dach ist deshalb 85 Grad, nicht 90. Der Bogen ueberstreicht 95 Grad.

Achsen wie beim Blech: X = Zeichnungs-x, Z = -Zeichnungs-y, Y = -xs (Blechvorderseite Y = -2).

    exec(open(r"C:\\AI_Projects\\Intercom\\cad\\make_diffusor_v1.py", encoding="utf-8").read())
    build(); check(); export_print()      # headless
    assemble()                            # nur im GUI-Thread
"""
import math
import os

import FreeCAD as App
import Part
from FreeCAD import Vector as V

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
BREP = os.path.join(OUT, "_diffusor_v1.brep")

# ------------------------------------------------------------------ Blech-Vorgaben [DB]
SHEET_T = 2.0
CAP_ANGLE = 85.0
_A = math.radians(90 - CAP_ANGLE)
TAN, SEC = math.tan(_A), 1 / math.cos(_A)
C0 = SHEET_T * (SEC - 1)
roof_under = lambda xs: xs * TAN + C0
Y_CORNER = roof_under(SHEET_T)           # 0.1826
LED_WINS = [(29.0, 47.0), (53.0, 71.0)]
LED_SLITS, SLIT_Y = [(15.0, 25.0), (75.0, 85.0)], (9.7, 12.3)
FLANGE_PASS_Y = (8.2, 13.8)              # Durchbruch im Kastenkragen, 1.5 groesser als der Schlitz

# ------------------------------------------------------------------ Diffusor
R = 18.0                 # [DB]
X0, X1 = 13.0, 87.0      # [DB]
WALL = 2.0               # [FREI] duenn genug zum Durchleuchten, dick genug zum Drucken
STRIP_W, STRIP_T = 10.0, 2.5    # [DB] SK6812 RGBW IP65

# Laschen: keilfoermig, sie klemmen sich im Schlitz fest. KEIN Schnapphaken - eine Rastnase
# braeuchte bei 4.5 mm Armlaenge 1.2 mm Federweg, das sind in PLA rund 18x die zulaessige Dehnung.
# Gehalten wird ohnehin vom Silikon; die Lasche positioniert und klemmt beim Aushaerten.
TAB_W = 9.8              # [FREI] Schlitz ist 10.0
TAB_ROOT_T, TAB_TIP_T = 2.6, 2.2         # [FREI] Schlitz ist 2.6 hoch -> Keil laeuft sich fest
TAB_LEN = 4.5            # [FREI] Blech 2.0 + 2.5 in den Kragendurchbruch hinein
TAB_Y = (SLIT_Y[0] + SLIT_Y[1]) / 2      # 11.0
RIB_H = 6.0              # [FREI] Hoehe der Traegerrippe im Hohlraum

# Silikon soll von aussen NICHT sichtbar sein (Bauherr). Dafuer werden die beiden Auflageraender
# von 2.0 auf 3.5 mm verbreitert und bekommen eine Kammer, in die das Silikon beim Andruecken
# ausweicht. Aussen bleiben 1.4 mm sauberer Kontakt, innen 0.9 mm.
LIP_W = 3.5              # [FREI] Breite der Auflageflaeche
LIP_T = 1.5              # [FREI] wie weit die Lippe in den Hohlraum ragt
SIL_OUT, SIL_IN, SIL_D = 1.4, 2.6, 0.6   # [FREI] Kammer zwischen Radius R-1.4 und R-2.6, 0.6 tief

pt = lambda x, y, xs: V(x, -xs, -y)      # Zeichnung -> CAD


# ------------------------------------------------------------------ Helfer
def quarter_capsule(radius):
    """Kapsel (Zylinder + zwei Kugelenden) auf der Eckkante, auf das Viertel in der Ecke beschnitten."""
    axis0, axis1 = X0 + R, X1 - R        # Kugelmittelpunkte
    body = Part.makeCylinder(radius, axis1 - axis0, pt(axis0, Y_CORNER, SHEET_T), V(1, 0, 0))
    body = body.fuse([Part.makeSphere(radius, pt(axis0, Y_CORNER, SHEET_T)),
                      Part.makeSphere(radius, pt(axis1, Y_CORNER, SHEET_T))])
    # Halbraum 1: alles hinter der Blechvorderseite weg (xs > SHEET_T -> Y > -SHEET_T)
    behind = Part.makeBox(200, 60, 200, V(X0 - 60, -SHEET_T, -100))
    # Halbraum 2: alles oberhalb der Dachunterseite weg. Ebene: Z = Y*TAN - C0
    pts = [(-80.0, -80.0 * TAN - C0), (20.0, 20.0 * TAN - C0), (20.0, 80.0), (-80.0, 80.0)]
    w = Part.makePolygon([V(X0 - 30, y, z) for (y, z) in pts] + [V(X0 - 30, pts[0][0], pts[0][1])])
    above = Part.Face(w).extrude(V((X1 + 30) - (X0 - 30), 0, 0))
    return body.cut([behind, above])


def above_roof(offset=0.0):
    """Halbraum oberhalb der (geneigten) Dachunterseite, optional um `offset` nach unten versetzt."""
    pts = [(-80.0, -80.0 * TAN - C0 - offset), (20.0, 20.0 * TAN - C0 - offset),
           (20.0, 80.0), (-80.0, 80.0)]
    w = Part.makePolygon([V(X0 - 30, y, z) for (y, z) in pts] + [V(X0 - 30, pts[0][0], pts[0][1])])
    return Part.Face(w).extrude(V(140.0, 0, 0))


def plate_slab(t):
    """Scheibe der Dicke t vor der Blechvorderseite."""
    return Part.makeBox(120, t, 120, V(X0 - 10, -SHEET_T - t, -60.0))


def lips_and_silicone():
    """Verbreiterte Auflageraender + Silikonkammer darin."""
    ring = quarter_capsule(R).cut(quarter_capsule(R - LIP_W))
    lip = ring.common(plate_slab(LIP_T).fuse(above_roof(LIP_T).cut(above_roof(0.0))))
    chamber = quarter_capsule(R - SIL_OUT).cut(quarter_capsule(R - SIL_IN))
    groove = chamber.common(plate_slab(SIL_D).fuse(above_roof(SIL_D).cut(above_roof(0.0))))
    return lip, groove


def tabs():
    """Keil-Laschen + Rippen, die sie im Hohlraum abstuetzen."""
    add, solid_ribs = [], []
    for (a, b) in LED_SLITS:
        cx = (a + b) / 2
        # Rippe von der Blechebene bis in die Aussenhaut, spaeter am Aussenkoerper beschnitten
        solid_ribs.append(Part.makeBox(b - a, 40.0, RIB_H,
                                       V(a, -42.0, -(TAB_Y + RIB_H / 2))))
        # Keil: Wurzel an der Blechvorderseite (Y=-2), Spitze 4.5 mm dahinter (Y=+2.5)
        prof = [(-SHEET_T, -(TAB_Y + TAB_ROOT_T / 2)), (TAB_LEN - SHEET_T, -(TAB_Y + TAB_TIP_T / 2)),
                (TAB_LEN - SHEET_T, -(TAB_Y - TAB_TIP_T / 2)), (-SHEET_T, -(TAB_Y - TAB_ROOT_T / 2))]
        w = Part.makePolygon([V(cx - TAB_W / 2, y, z) for (y, z) in prof]
                             + [V(cx - TAB_W / 2, prof[0][0], prof[0][1])])
        add.append(Part.Face(w).extrude(V(TAB_W, 0, 0)))
    return add, solid_ribs


def build_shape(wall=None):
    wall = WALL if wall is None else wall
    outer = quarter_capsule(R)
    inner = quarter_capsule(R - wall)
    shell = outer.cut(inner)
    tab_solids, ribs = tabs()
    ribs = [r.common(outer) for r in ribs]          # Rippen auf die Aussenkontur beschneiden
    lip, groove = lips_and_silicone()
    return shell.fuse(ribs + [lip]).cut(groove).fuse(tab_solids).removeSplitter()


def build():
    shape = build_shape()
    os.makedirs(OUT, exist_ok=True)
    shape.exportBrep(BREP)
    bb = shape.BoundBox
    print("Diffusor: Solids %d | valid %s | %.0f mm3 (PLA 1.24 = %.0f g)"
          % (len(shape.Solids), shape.isValid(), shape.Volume, shape.Volume * 1.24e-3))
    print("  BoundBox %.1f x %.1f x %.1f mm" % (bb.XLength, bb.YLength, bb.ZLength))
    return shape


# ------------------------------------------------------------------ Testplatte Wandstaerken
LABEL_FONT = r"C:\Windows\Fonts\arialbd.ttf"   # [FREI]
LABEL_SIZE, LABEL_H = 6.0, 0.6                 # [FREI] Schrifthoehe / Erhabenheit
LABEL_X, LABEL_OFF = 12.0, 6.0                 # [FREI] Position: 12 mm vom Ende, 6 mm neben dem Scheitel


def _placed(shapes, ang, tr):
    for s in shapes:
        if ang:
            s.rotate(V(0, 0, 0), V(1, 0, 0), ang)
        s.translate(tr)
    return shapes


def label_solid(text, part, skin):
    """Erhabene Schrift, senkrecht auf den Bogen projiziert. Erhaben statt graviert: eine
    0.4-mm-Gravur wuerde die duennste Wand (0.8) halb durchtrennen."""
    wires = Part.makeWireString(text, LABEL_FONT, LABEL_SIZE, 0)
    faces = [Part.makeFace(ws, "Part::FaceMakerBullseye") for ws in wires if ws]
    txt = faces[0] if len(faces) == 1 else faces[0].fuse(faces[1:])
    bb = part.BoundBox
    top = part.common(Part.makeBox(bb.XLength + 2, bb.YLength + 2, 2.0,
                                   V(bb.XMin - 1, bb.YMin - 1, bb.ZMax - 1.0)))
    apex_y = (top.BoundBox.YMin + top.BoundBox.YMax) / 2      # Scheitel des Bogens
    away = 1.0 if apex_y < (bb.YMin + bb.YMax) / 2 else -1.0  # davon weg ins Bogeninnere
    tb = txt.BoundBox
    txt.translate(V(bb.XMin + LABEL_X - tb.XMin,
                    apex_y + away * LABEL_OFF - (tb.YMin + tb.YLength / 2),
                    bb.ZMax + 2.0 - tb.ZMin))
    return txt.extrude(V(0, 0, -8.0)).common(skin)


def export_test_plate(walls=(0.8, 1.2, 1.6, 2.0, 2.4), gap=6.0, dev=0.02):
    """Druckfertige Platte: je ein vollstaendiger Diffusor pro Wandstaerke, beschriftet."""
    import Mesh
    ang = 180.0 - (90 - CAP_ANGLE)
    parts, y = [], 0.0
    for w in walls:
        sh, skin = build_shape(w), quarter_capsule(R + LABEL_H).cut(quarter_capsule(R))
        _placed([sh, skin], ang, V(0, 0, 0))
        bb = sh.BoundBox
        _placed([sh, skin], 0.0, V(-bb.XMin, y - bb.YMin, -bb.ZMin))
        part = sh.fuse(label_solid("%.1f" % w, sh, skin)).removeSplitter()
        pb = part.BoundBox
        print("  Wand %.1f: %6.0f mm3 = %4.1f g | %.1f x %.1f x %.1f | Solids %d | valid %s"
              % (w, part.Volume, part.Volume * 1.24e-3, pb.XLength, pb.YLength, pb.ZLength,
                 len(part.Solids), part.isValid()))
        parts.append(part)
        y = sh.BoundBox.YMax + gap
    plate = Part.Compound(parts)
    bb, tot = plate.BoundBox, sum(p.Volume for p in parts)
    Mesh.Mesh(plate.tessellate(dev)).write(os.path.join(OUT, "klingel_diffusor_testplatte.stl"))
    print("Testplatte %.1f x %.1f x %.1f mm | %d Teile | %.0f mm3 = %.0f g PLA"
          % (bb.XLength, bb.YLength, bb.ZLength, len(parts), tot, tot * 1.24e-3))
    return plate


# ------------------------------------------------------------------ Nachrechnen
def check():
    sh = Part.Shape(); sh.importBrep(BREP)
    print("\n--- Nachgerechnet ---")
    print("Oberseite mitgeneigt: bei xs=%.0f liegt die Dachunterseite auf y=%.3f" % (20, roof_under(20)))
    # Gegen die GENEIGTE Dachebene pruefen, nicht gegen eine waagerechte (erster Test war falsch).
    eps = 0.02
    pts = [(-80.0, -80.0 * TAN - C0 + eps), (20.0, 20.0 * TAN - C0 + eps), (20.0, 80.0), (-80.0, 80.0)]
    w = Part.makePolygon([V(X0 - 30, y, z) for (y, z) in pts] + [V(X0 - 30, pts[0][0], pts[0][1])])
    above = Part.Face(w).extrude(V(140.0, 0, 0))
    print("  Material oberhalb der Dachunterseite: %.3f mm3 (muss 0)" % sh.common(above).Volume)
    # Hinter dem Blech darf NUR die Lasche stehen -> ausserhalb der Schlitz-x-Bereiche messen
    behind = Part.makeBox(120, 20, 80, V(X0 - 10, -SHEET_T + eps, -40.0))
    for (a, b) in LED_SLITS:
        behind = behind.cut(Part.makeBox(b - a + 2, 30, 90, V(a - 1, -SHEET_T - 1, -45.0)))
    print("  Material hinter dem Blech ausserhalb der Laschen: %.3f mm3 (muss 0)" % sh.common(behind).Volume)
    tabvol = sh.common(Part.makeBox(120, 20, 80, V(X0 - 10, -SHEET_T + eps, -40.0))).Volume
    print("  Laschenvolumen hinter dem Blech: %.1f mm3 (2 Stueck)" % tabvol)

    for nm, (a, b), (y0, y1) in [("LED-Fenster %d" % i, w, (8.0, 14.0)) for i, w in enumerate(LED_WINS, 1)] \
            + [("Schlitz %d" % i, s, SLIT_Y) for i, s in enumerate(LED_SLITS, 1)]:
        covered = (X0 <= a and b <= X1 and Y_CORNER <= y0 and y1 <= Y_CORNER + R)
        print("  %-12s x %.0f..%.0f y %.1f..%.1f -> %s" % (nm, a, b, y0, y1,
              "vom Diffusor ueberdeckt" if covered else "NICHT ueberdeckt"))

    # Passt der LED-Streifen zwischen die Laschen und in den Hohlraum?
    print("Streifen %.0f x %.1f: laeuft x %.0f..%.0f zwischen den Laschen; Hohlraum reicht %.1f mm "
          "an der Blechebene nach unten" % (STRIP_W, STRIP_T, LED_SLITS[0][1] + 1, LED_SLITS[1][0] - 1,
                                            R - WALL))
    # Laschen gegen Blech und Kragen
    print("Lasche: Wurzel %.1f / Spitze %.1f in einem %.1f-Schlitz -> klemmt; Laenge %.1f (Blech %.1f + %.1f)"
          % (TAB_ROOT_T, TAB_TIP_T, SLIT_Y[1] - SLIT_Y[0], TAB_LEN, SHEET_T, TAB_LEN - SHEET_T))
    print("  Spitze endet bei y %.1f..%.1f, Kragendurchbruch ist y %.1f..%.1f -> passt"
          % (TAB_Y - TAB_TIP_T / 2, TAB_Y + TAB_TIP_T / 2, *FLANGE_PASS_Y))


def export_print(dev=0.02):
    """Drucklage: Dachflaeche aufs Bett. Dann zeigen die Laschen waagerecht zur Seite und der
    Bogen laeuft nach oben aus - keine Stuetzen ausser ggf. unter den Laschen."""
    import Mesh
    sh = Part.Shape(); sh.importBrep(BREP)
    sh = sh.copy()
    sh.rotate(V(0, 0, 0), V(1, 0, 0), 180.0 - (90 - CAP_ANGLE))
    bb = sh.BoundBox
    sh.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
    bb = sh.BoundBox
    Mesh.Mesh(sh.tessellate(dev)).write(os.path.join(OUT, "klingel_diffusor_v1_print.stl"))
    print("Druck-STL %.1f x %.1f x %.1f mm" % (bb.XLength, bb.YLength, bb.ZLength))


def assemble():
    import Mesh
    doc = App.newDocument("Klingel_Diffusor_v1")
    s = Part.Shape(); s.importBrep(BREP)
    o = doc.addObject("Part::Feature", "Diffusor"); o.Shape = s
    doc.recompute()
    if App.GuiUp:
        import FreeCADGui as Gui
        o.ViewObject.ShapeColor = (0.95, 0.94, 0.88)
        Gui.ActiveDocument.ActiveView.viewAxonometric()
        Gui.SendMsgToActiveView("ViewFit")
    doc.saveAs(os.path.join(OUT, "klingel_diffusor_v1.FCStd"))
    Part.export([o], os.path.join(OUT, "klingel_diffusor_v1.step"))
    Mesh.export([o], os.path.join(OUT, "klingel_diffusor_v1.stl"))
    print("gespeichert:", OUT)
    return doc
