"""Klingel v5 - ABS/ASA-Kasten v3. Geometrie AUSSCHLIESSLICH aus kasten_v3_params.py.

    exec(open(r"C:\\AI_Projects\\Intercom\\cad\\make_kasten_v3.py", encoding="utf-8").read())
    build_box(); build_plate(); check_cad(); export_print(); export_testprint()
    assemble()          # nur im GUI-Thread

check_cad() misst am FERTIGEN Koerper nach, nicht an den Parametern - das ist die zweite
Pruefstufe nach P.validate(). Beide muessen gruen sein.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kasten_v3_params as P

import FreeCAD as App
import Part
from FreeCAD import Vector as V

OUT = os.path.join(HERE, "out")
BREP_BOX = os.path.join(OUT, "_kasten_v3.brep")
BREP_PLATE = os.path.join(OUT, "_traegerplatte_v3.brep")

B, DEPTH, WALL, BACK = P.BOX, P.DEPTH, P.WALL, P.BACK
FW, FT = P.FLANGE_W, P.FLANGE_T
pt = lambda x, y, d: V(x, d, -y)


# ------------------------------------------------------------------ Helfer
def rbox(x0, y0, x1, y1, d0, d1, r=0.0):
    s = Part.makeBox(x1 - x0, d1 - d0, y1 - y0, pt(x0, y1, d0))
    if r > 0:
        edges = [e for e in s.Edges
                 if abs(abs((e.Vertexes[1].Point - e.Vertexes[0].Point).normalize().y) - 1.0) < 1e-6]
        s = s.makeFillet(r, edges)
    return s


def cyl(x, y, d0, d1, dia):
    return Part.makeCylinder(dia / 2, d1 - d0, pt(x, y, d0), V(0, 1, 0))


def prism_dy(pts, x0, x1):
    w = Part.makePolygon([pt(x0, y, d) for (d, y) in pts] + [pt(x0, pts[0][1], pts[0][0])])
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))


# ------------------------------------------------------------------ Schale
def box_shell():
    outer = rbox(B["x0"], B["y0"], B["x1"], B["y1"], 0.0, DEPTH, P.CORNER_R)
    cav = rbox(B["x0"] + WALL, B["y0"] + WALL, B["x1"] - WALL, B["y1"] - WALL,
               FT, DEPTH - BACK, max(P.CORNER_R - WALL, 0.5))
    mouth = rbox(B["x0"] + FW, B["y0"] + FW, B["x1"] - FW, B["y1"] - FW,
                 -1.0, FT + 0.001, max(P.CORNER_R - FW, 0.5))
    return outer.cut([cav, mouth])


def flange_ramps():
    """45-Grad-Rampen unter der Kragennase, sonst braucht der Kragen rundum Stuetzen."""
    xi0, yi0, xi1, yi1 = B["x0"] + WALL, B["y0"] + WALL, B["x1"] - WALL, B["y1"] - WALL
    xf0, yf0, xf1, yf1 = B["x0"] + FW, B["y0"] + FW, B["x1"] - FW, B["y1"] - FW
    r = FW - WALL
    out = []
    for xi, xf in ((xi0, xf0), (xi1, xf1)):
        w = Part.makePolygon([V(xf, FT, -yi0), V(xi, FT, -yi0), V(xi, FT + r, -yi0), V(xf, FT, -yi0)])
        out.append(Part.Face(w).extrude(V(0, 0, -(yi1 - yi0))))
    for yi, yf in ((yi0, yf0), (yi1, yf1)):
        w = Part.makePolygon([pt(xi0, yf, FT), pt(xi0, yi, FT), pt(xi0, yi, FT + r), pt(xi0, yf, FT)])
        out.append(Part.Face(w).extrude(V(xi1 - xi0, 0, 0)))
    return out


def grooves():
    """Umlaufende Dichtnut + Querriegel unter dem Gitterhohlraum."""
    G = P.GROOVE
    gx0, gy0 = B["x0"] + G["left"] - G["w"] / 2, B["y0"] + G["top"] - G["w"] / 2
    gx1, gy1 = B["x1"] - G["right"] + G["w"] / 2, B["y1"] - G["bottom"] + G["w"] / 2
    rout = max(P.CORNER_R - G["left"] + G["w"] / 2, 0.5)
    ring = rbox(gx0, gy0, gx1, gy1, -0.001, G["d"], rout).cut(
        rbox(gx0 + G["w"], gy0 + G["w"], gx1 - G["w"], gy1 - G["w"],
             -0.002, G["d"] + 0.001, max(rout - G["w"], 0.5)))
    sill = rbox(gx0, P.SILL_GROOVE_Y - G["w"] / 2, gx1, P.SILL_GROOVE_Y + G["w"] / 2, -0.001, G["d"])
    return ring.fuse(sill)


def flange_passes():
    out = [rbox(a - 1.0, P.LED_WIN_Y[0] - 1.0, b + 1.0, P.LED_WIN_Y[1] + 1.0, -1.0, FT + 1.0)
           for (a, b) in P.LED_WINS]
    out += [rbox(a - 1.5, P.LED_SLIT_Y[0] - 1.5, b + 1.5, P.LED_SLIT_Y[1] + 1.5, -1.0, FT + 1.0)
            for (a, b) in P.LED_SLITS]
    return out


def insert_bosses():
    """Doeme HINTER dem Kragen. Ohne sie ragt das 6-mm-Einsatzloch aus dem 4-mm-Kragen heraus."""
    add = [cyl(x, y, FT - 0.001, FT + P.INS_BOSS["l"], P.INS_BOSS["d"]) for (x, y) in P.SCREWS]
    cut = [cyl(x, y, -0.001, P.INS["l"], P.INS["d"]) for (x, y) in P.SCREWS]
    return add, cut


# ------------------------------------------------------------------ Gitterhohlraum + Lautsprecher
def grille_module():
    BL, C, S = P.BLOCK, P.CAV, P.SPK
    block = rbox(BL["x0"], BL["y0"], BL["x1"], BL["y1"], 0.0, C["d"] + P.SPK_WALL)
    slope = (C["y_back"] - C["y_front"]) / C["d"]
    prof = [(-1.0, C["y0"]), (C["d"], C["y0"]), (C["d"], C["y_back"]), (-1.0, C["y_front"] - slope)]
    cuts = [prism_dy(prof, C["x0"], C["x1"])]
    cuts.append(cyl(S["c"][0], S["c"][1], C["d"] - 0.5, C["d"] + P.SPK_WALL + 0.5, S["port_d"]))
    for sx in (-1, 1):
        for sy in (-1, 1):
            cuts.append(cyl(S["c"][0] + sx * S["pattern"] / 2, S["c"][1] + sy * S["pattern"] / 2,
                            C["d"] + P.SPK_WALL - 5.0, C["d"] + P.SPK_WALL + 0.5, 2.6))
    cuts.append(cyl(P.VENT["c"][0], P.VENT["c"][1], C["d"] - 0.5, C["d"] + P.SPK_WALL + 0.5,
                    P.VENT["d"]))
    return block, cuts


# ------------------------------------------------------------------ Taster
def button_mount():
    d0, d1 = P.RING_T - P.SHEET["t"], P.RING_T - P.SHEET["t"] + P.BTN_PLATE_T
    bore = P.BTN_CYL_D + 0.6
    solid = cyl(P.BTN_C[0], P.BTN_C[1], d0, d1, P.RING_D - 1.0).fuse([
        rbox(B["x0"] + WALL, P.BTN_C[1] - 6.0, P.BTN_C[0], P.BTN_C[1] + 6.0, d0, d1),
        rbox(P.BTN_C[0], P.BTN_C[1] - 6.0, B["x1"] - WALL, P.BTN_C[1] + 6.0, d0, d1),
        cyl(P.BTN_C[0], P.BTN_C[1], d0, d0 + 20.0, bore + 5.0)])
    cuts = [cyl(P.BTN_C[0], P.BTN_C[1], d0 - 1.0, d0 + 21.0, bore),
            rbox(P.BTN_C[0] - 6.0, P.BTN_C[1], P.BTN_C[0] + 6.0, P.BTN_C[1] + bore,
                 d0 + 6.0, d0 + 21.0)]
    for s in (-1, 1):
        cuts.append(cyl(P.BTN_C[0] + s * P.BTN_SCREW_CC / 2, P.BTN_C[1], d0, d0 + P.INS["l"],
                        P.INS["d"]))
    O = P.BTN_ORING
    cuts.append(cyl(P.BTN_C[0], P.BTN_C[1], d0 - 0.001, d0 + O["d"], O["mean"] + O["w"])
                .cut(cyl(P.BTN_C[0], P.BTN_C[1], d0 - 0.002, d0 + O["d"] + 0.1, O["mean"] - O["w"])))
    return solid.cut(cuts)


# ------------------------------------------------------------------ Doeme, Kabel
def board_bosses():
    d1 = DEPTH - BACK
    d0 = d1 - 6.0
    add, cut = [], []

    def boss(x, y):
        add.append(cyl(x, y, d0, d1, 1.7 + 4.0))
        cut.append(cyl(x, y, d0 - 0.5, d1 + 0.5, 1.7))

    for hx in P.BRD_B["hx"]:
        for hy in P.BRD_B["hy"]:
            boss(P.BRD_B["x"] + hx, P.BRD_B["y"] + hy)
    for o in (P.REG, P.AMP):
        for (hx, hy) in o["holes"]:
            boss(o["x"] + hx, o["y"] + hy)
    return add, cut


def plate_bosses():
    add, cut = [], []
    for (x, y) in P.PLATE_BOSSES:
        left = x < (B["x0"] + B["x1"]) / 2
        x0 = B["x0"] + WALL if left else x - 5.0
        x1 = x + 5.0 if left else B["x1"] - WALL
        add.append(rbox(x0, y - 5.0, x1, y + 5.0, P.PLATE_Z, P.PLATE_Z + 10.0))
        cut.append(cyl(x, y, P.PLATE_Z - 0.5, P.PLATE_Z + P.INS["l"], P.INS["d"]))
    return add, cut


def gland_boss():
    """Conta-Clip KDS-KV M25 in der RUECKWAND: Ø25.5 durch einen verdickten Boss."""
    G = P.GLAND
    add = cyl(G["c"][0], G["c"][1], DEPTH - BACK - (G["wall"] - BACK), DEPTH, G["boss"])
    cut = cyl(G["c"][0], G["c"][1], DEPTH - G["wall"] - 1.0, DEPTH + 1.0, G["hole_d"])
    return add, cut


def anchors():
    return [cyl(x, y, DEPTH - BACK - 0.5, DEPTH + 0.5, P.ANCHOR_D) for (x, y) in P.ANCHORS] + \
           [cyl(x, y, DEPTH - BACK - 0.001, DEPTH - BACK + 2.0, P.ANCHOR_HEAD_D)
            for (x, y) in P.ANCHORS]


# ------------------------------------------------------------------ Bauen
def build_box():
    block, block_cuts = grille_module()
    i_add, i_cut = insert_bosses()
    b_add, b_cut = board_bosses()
    p_add, p_cut = plate_bosses()
    g_add, g_cut = gland_boss()
    shape = box_shell().fuse([block, button_mount(), g_add] + flange_ramps() + i_add + b_add + p_add)
    shape = shape.cut([grooves(), g_cut] + flange_passes() + block_cuts + i_cut + b_cut + p_cut
                      + [cyl(P.BTN_C[0], P.BTN_C[1], -1.0, P.RING_T - P.SHEET["t"] + 0.3,
                             P.BTN_HOLE)] + anchors()).removeSplitter()
    os.makedirs(OUT, exist_ok=True)
    shape.exportBrep(BREP_BOX)
    print("Kasten v3: Solids %d | valid %s | %.0f mm3 (ASA 1.07 = %.0f g)"
          % (len(shape.Solids), shape.isValid(), shape.Volume, shape.Volume * 1.07e-3))
    return shape


def build_plate():
    PL = P.PLATE
    p = rbox(PL["x0"], PL["y0"], PL["x1"], PL["y1"], P.PLATE_Z - PL["t"], P.PLATE_Z, 4.0)
    p = p.cut([cyl(x, y, P.PLATE_Z - PL["t"] - 0.5, P.PLATE_Z + 0.5, 3.4) for (x, y) in P.PLATE_BOSSES])
    p.exportBrep(BREP_PLATE)
    print("Traegerplatte: %.0f x %.0f x %.0f | valid %s (leer - [MESSEN]-Teile fehlen)"
          % (PL["x1"] - PL["x0"], PL["y1"] - PL["y0"], PL["t"], p.isValid()))
    return p


# ------------------------------------------------------------------ Zweite Pruefstufe: am Koerper
def check_cad():
    sh = Part.Shape(); sh.importBrep(BREP_BOX)
    print("\n--- Am fertigen Koerper nachgemessen ---")
    bad = 0

    def ring_test(name, x, y, d0, d1, hole_d, need):
        """Ist rund um das Loch wirklich ueberall Material? Sonst bricht es nach aussen durch."""
        ann = cyl(x, y, d0, d1, hole_d + 2 * need).cut(cyl(x, y, d0 - 0.1, d1 + 0.1, hole_d))
        full = math.pi * ((hole_d / 2 + need) ** 2 - (hole_d / 2) ** 2) * (d1 - d0)
        got = sh.common(ann).Volume
        ok = got > full * 0.995
        print("  %-34s %5.1f%% Material im %.1f-mm-Ring %s"
              % (name, 100 * got / full, need, "" if ok else "<<< LUECKE"))
        return ok

    for (x, y) in P.SCREWS:
        # ab unterhalb der Dichtnut messen - die Nut ist gewollt, keine Luecke
        if not ring_test("Blendenschraube (%.0f,%.0f)" % (x, y), x, y,
                         P.GROOVE["d"] + 0.3, P.INS["l"] - 0.5, P.INS["d"], P.MIN_WALL):
            bad += 1
    for s in (-1, 1):
        x = P.BTN_C[0] + s * P.BTN_SCREW_CC / 2
        d0 = P.RING_T - P.SHEET["t"]
        # unterhalb der O-Ring-Nut messen, die ist gewollt
        if not ring_test("Tasterschraube (%.2f,%.0f)" % (x, P.BTN_C[1]), x, P.BTN_C[1],
                         d0 + P.BTN_ORING["d"] + 0.3, d0 + P.INS["l"] - 0.5, P.INS["d"], P.MIN_WALL):
            bad += 1
    if not ring_test("Kabelverschraubung", P.GLAND["c"][0], P.GLAND["c"][1],
                     DEPTH - P.GLAND["wall"] + 0.5, DEPTH - 0.5, P.GLAND["hole_d"], 2.0):
        bad += 1

    need = (P.RING_T - P.SHEET["t"]) + P.BTN_CYL_L + P.BTN_FREE
    col = cyl(P.BTN_C[0], P.BTN_C[1], P.RING_T - P.SHEET["t"] + 20.0, need,
              P.BTN_CYL_D + P.BTN_FREE)
    v = sh.common(col).Volume
    print("  %-34s %.1f mm3 (muss 0)" % ("ABS in der Taster-Freiraumsaeule", v))
    bad += (v > 0.5)

    sp = sh.common(cyl(P.SPK["c"][0], P.SPK["c"][1], P.CAV["d"] + 0.5,
                       P.CAV["d"] + P.SPK_WALL - 0.5, P.SPK["port_d"]))
    print("  %-34s %.1f mm3 (muss 0)" % ("Material in der Schalloeffnung", sp.Volume))
    bad += (sp.Volume > 0.5)

    bb = sh.BoundBox
    print("  %-34s %.1f x %.1f x %.1f mm" % ("BoundBox", bb.XLength, bb.YLength, bb.ZLength))
    print("\n%s" % ("ALLE CAD-PRUEFUNGEN BESTANDEN" if bad == 0 else "%d CAD-PRUEFUNGEN FEHLGESCHLAGEN" % bad))
    return bad


# ------------------------------------------------------------------ Export
def _print_orient(sh):
    sh = sh.copy()
    sh.rotate(V(0, 0, 0), V(1, 0, 0), -90.0)
    bb = sh.BoundBox
    sh.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
    return sh


def export_print(dev=0.03):
    import Mesh
    for name, brep in (("kasten", BREP_BOX), ("traegerplatte", BREP_PLATE)):
        s = Part.Shape(); s.importBrep(brep)
        s = _print_orient(s)
        bb = s.BoundBox
        Mesh.Mesh(s.tessellate(dev)).write(os.path.join(OUT, "klingel_%s_v3_print.stl" % name))
        print("%-14s %.1f x %.1f x %.1f mm" % (name, bb.XLength, bb.YLength, bb.ZLength))


LABEL_FONT = "C:/Windows/Fonts/arialbd.ttf"   # Schraegstriche: Backslash-a wird beim Schreiben sonst zu BEL


def wall_label(text, y_draw, depth_c=10.0, h=5.0, emboss=0.6):
    """Erhabene Schrift auf der linken Aussenwand, von aussen lesbar."""
    wires = Part.makeWireString(text, LABEL_FONT, h, 0)
    faces = [Part.makeFace(ws, "Part::FaceMakerBullseye") for ws in wires if ws]
    txt = faces[0] if len(faces) == 1 else faces[0].fuse(faces[1:])
    txt.rotate(V(0, 0, 0), V(1, 0, 0), 90.0)      # in die Ebene x = const kippen
    txt.rotate(V(0, 0, 0), V(0, 0, 1), -90.0)     # Leserichtung nach -Y drehen
    bb = txt.BoundBox
    txt.translate(V(B["x0"] + 1.0 - bb.XMin, depth_c - (bb.YMin + bb.YLength / 2),
                    -y_draw - (bb.ZMin + bb.ZLength / 2)))
    return txt.extrude(V(-(emboss + 1.0), 0, 0))


def export_testprint(dev=0.03):
    """Montage-Testdruck: volle Grundflaeche, nur die vorderen TESTPRINT_DEPTH mm.
    Enthaelt die 4 Blenden- und 2 Tasterschrauben mit allem, was an ihnen haengt."""
    import Mesh
    s = Part.Shape(); s.importBrep(BREP_BOX)
    keep = rbox(B["x0"] - 5, B["y0"] - 5, B["x1"] + 5, B["y1"] + 5, -1.0, P.TESTPRINT_DEPTH)
    s = s.common(keep)
    # zwei Loecher auf Kernloch-Durchmesser zuruecksetzen und beide Sorten beschriften
    s = s.fuse([cyl(x, y, 0.0, P.INS["l"] + 0.5, P.INS["d"] + 2 * P.MIN_WALL)
                for (x, y) in P.SCREWS_DIRECT])
    s = s.cut([cyl(x, y, -1.0, P.INS["l"], P.DIRECT_D) for (x, y) in P.SCREWS_DIRECT])
    s = s.fuse([wall_label("%.1f" % P.INS["d"], P.SCREWS_HEATSET[0][1]),
                wall_label("%.1f" % P.DIRECT_D, P.SCREWS_DIRECT[0][1])]).removeSplitter()
    s = _print_orient(s)
    bb = s.BoundBox
    Mesh.Mesh(s.tessellate(dev)).write(os.path.join(OUT, "klingel_kasten_v3_montagetest.stl"))
    print("Montagetest  %.1f x %.1f x %.1f mm | %.0f mm3 = %.0f g PLA | Solids %d | valid %s"
          % (bb.XLength, bb.YLength, bb.ZLength, s.Volume, s.Volume * 1.24e-3,
             len(s.Solids), s.isValid()))
    return s


def assemble():
    import Mesh
    doc = App.newDocument("Klingel_Kasten_v3")
    for name, brep, col in (("Kasten", BREP_BOX, (0.30, 0.32, 0.36)),
                            ("Traegerplatte", BREP_PLATE, (0.55, 0.60, 0.68))):
        s = Part.Shape(); s.importBrep(brep)
        o = doc.addObject("Part::Feature", name); o.Shape = s
        doc.recompute()
        if App.GuiUp:
            o.ViewObject.ShapeColor = col
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.ActiveDocument.ActiveView.viewAxonometric()
        Gui.SendMsgToActiveView("ViewFit")
    doc.saveAs(os.path.join(OUT, "klingel_kasten_v3.FCStd"))
    Part.export(doc.Objects, os.path.join(OUT, "klingel_kasten_v3.step"))
    print("gespeichert:", OUT)
    return doc
