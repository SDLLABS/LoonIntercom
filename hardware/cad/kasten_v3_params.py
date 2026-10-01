"""Klingel v5 - ABS/ASA-Kasten v3: EINZIGE Quelle aller Masse.

Zeichnung, CAD und Pruefung lesen alle diese Datei. Sie koennen sich damit nicht widersprechen.
`validate()` prueft jede geometrische Regel und gibt am Ende FEHLER/WARNUNG/OK aus.

Tags: [DB] Datenblatt · [GEMESSEN] am realen Teil · [FREI] Konstruktionswahl · [PLATZ] Platzhalter.
Koordinaten: Ursprung = linke obere Ecke der Messingblende, x rechts, y unten, d = Tiefe in die Wand.

WAS SICH GEGENUEBER v2 AENDERT
  1. Blendenschrauben von (8,26)/(92,252) nach innen auf (12,30)/(88,248).
     Grund: bei 4 mm Randabstand blieben am unteren Loch 0.24 mm Wand - das Loch brach nach
     aussen durch. Jetzt 8 mm Rand.
  2. Lautsprecher VISATON K 40 SQ statt PUI AS03104MR.
  3. Kabeleinfuehrung: EIN Loch Ø25.5 fuer die Conta-Clip KDS-KV M25 Teilbarverschraubung.
  4. Kabelzone kleiner: Patchkabel statt Installationskabel, kein PoE-Splitter mehr.
  5. FRAME_T vorbereitet: Aussparung fuer den spaeteren Edelstahl-Gewinderahmen.
"""
import math

# ==================================================================== EINGEFROREN
# Vom Bauherrn ausdruecklich freigegebene Masse. Sie duerfen in keiner Iteration mehr
# ueberschrieben werden. validate() vergleicht die lebenden Werte gegen diese Liste
# und meldet jede Abweichung als FEHLER.
#
# Wer hier etwas aendern will, braucht die ausdrueckliche Freigabe des Bauherrn und traegt sie
# mit Datum ein. Nicht stillschweigend anpassen - auch nicht "nur kurz zum Testen".
FROZEN = {
    # 2026-09-18 Bauherr: "der taster und seine schraublochposition sind perfekt
    # und bleiben fuer immer so"
    "BTN_C": (50.0, 225.0),          # Mitte des Tasters in der Blende
    "BTN_SCREW_CC": 37.06,           # Lochabstand der beiden Tasterschrauben
    "BTN_HOLE": 49.5,                # Ausschnitt in der Blende
    "RING_D": 48.5,                  # gemessener Aussenring
    "RING_T": 4.77,                  # gemessene Ringdicke
    "BTN_CYL_D": 18.9,               # gemessener Zylinder
    "BTN_CYL_L": 32.5,
    "BTN_FREE": 10.0,                # geforderter Freiraum hinter den Kontaktschrauben
}

# ------------------------------------------------------------------ Blende (Vorgabe)
SHEET = dict(w=100.0, h=260.0, t=2.0)                       # [DB]
# Gitter: v3 nur noch 3 Reihen (Bauherr 2026-09-18, Optik). Die oberen 2 von 5 entfallen.
# Folge: offene Flaeche 718 -> 431 mm2 = 45 % statt 75 % der Schalloeffnung Ø35. Siehe Report.
GRILLE = dict(x0=21.0, y0=34.0, x1=79.0, y1=53.0, rows=3, row0=34.0, pitch=7.0, slot_h=5.0)
DISPLAY_WIN = dict(x0=21.35, y0=64.65, x1=78.65, y1=167.35)  # [DB] 57.3 x 102.7
DISPLAY_PANEL_TOP = 61.9                                    # [DB] Fensteroberkante 64 - Rand 2.1
LED_WINS, LED_WIN_Y = [(29.0, 47.0), (53.0, 71.0)], (8.0, 14.0)      # [DB]
LED_SLITS, LED_SLIT_Y = [(15.0, 25.0), (75.0, 85.0)], (9.7, 12.3)    # [DB]
MICS, MIC_D = [(82.0, 221.0), (82.0, 229.0)], 1.2           # [DB]
BTN_C, RING_D, RING_T = (50.0, 225.0), 48.5, 4.77           # [GEMESSEN]
BTN_HOLE = RING_D + 1.0                                     # 49.5 im Blech
BTN_SCREW_CC = 37.06                                        # [GEMESSEN] Pruefmass 40.66 bestaetigt
BTN_CYL_D, BTN_CYL_L, BTN_FREE = 18.9, 32.5, 10.0           # [GEMESSEN]
BTN_PLATE_T = 7.0   # [FREI] Tragscheibe hinter dem Ring. 7 statt 4: das 6-mm-Einsatzloch haette
# sonst 2 mm hinten herausgeragt und der Einsatz haette zur Haelfte in der Luft gesessen -
# derselbe Fehler wie am Kragen, von der CAD-Pruefung mit 65.9 % Material gemeldet.
# O-Ring unter dem Messingring. Mitte Ø28 = INNERHALB der beiden Tasterschrauben.
# Vorher Ø44 (aussen): dort blieben zwischen Einsatzloch und Nut nur 0.17 mm - das Loch waere
# in die Dichtnut durchgebrochen. Von der CAD-Pruefung mit 95.9 % Material gemeldet.
# Handelsware: O-Ring 26 x 2.
BTN_ORING = dict(mean=28.0, w=2.4, d=1.5)                   # [FREI]
DIFFUSOR = dict(r=18.0, x0=13.0, x1=87.0)                   # [DB]

# Blendenschrauben - GEAENDERT in v3 (Bauherr 2026-09-18)
SCREWS = [(12.0, 30.0), (88.0, 30.0), (12.0, 248.0), (88.0, 248.0)]   # [FREI]
SCREW_HOLE, SCREW_HEAD = 3.2, 6.0                           # [DB] M3 Senkkopf DIN 963
# Montagetest: zwei Loecher fuer Gewindeeinsaetze, zwei zum direkten Schrauben - damit der Bauherr an
# EINEM Teil vergleichen kann. Oben Einsatz (Ø4.2), unten direkt (Ø2.5 Kernloch fuer M3).
SCREWS_HEATSET = [(12.0, 30.0), (88.0, 30.0)]               # [FREI]
SCREWS_DIRECT = [(12.0, 248.0), (88.0, 248.0)]              # [FREI]
DIRECT_D = 2.5                                              # [FREI] Kernloch M3 in Kunststoff

# ------------------------------------------------------------------ Kasten
BOX = dict(x0=4.0, y0=4.0, x1=96.0, y1=256.0)               # [DB] 92 x 252
DEPTH = 50.0                                                # [PLATZ]
WALL, BACK = 3.0, 3.0                                       # [FREI]
CORNER_R = 10.0   # [PLATZ] Wandausschnitt. 10 statt 8, damit die Nut bei 4 mm Einzug in der
# Ecke noch R6 = 3x Schnurdurchmesser bekommt (Faustregel). Restwand an den Schrauben bleibt 5.1 mm.
FLANGE_W, FLANGE_T = 11.0, 4.0                              # [FREI]
FRAME_T = 0.0                # [PLATZ] Dicke des spaeteren Edelstahl-Gewinderahmens.
#                              0 = Prototyp ohne Rahmen. Beim Endteil 2.0-3.0 eintragen,
#                              dann sinkt die Kragenstirn um diesen Betrag ab.

GROOVE = dict(w=2.4, d=1.5, top=4.0, left=4.0, right=4.0, bottom=4.0)   # [FREI] Rundschnur Ø2.0
# Einzug 4: die Nut laeuft jetzt AUSSEN an den Schrauben vorbei. Bei 8 lag sie exakt auf den
# nach innen versetzten Schrauben (12/88) - vom Regelpruefer mit -3.30 mm gemeldet.
SILL_GROOVE_Y = 58.0                                        # [FREI]

INS = dict(d=4.2, l=6.0)     # [PLATZ] M3-Heat-Set - am gekauften Einsatz pruefen
INS_BOSS = dict(d=9.0, l=6.0)   # [FREI] Dom hinter dem Kragen. Ohne ihn ragt das 6-mm-Loch
# 2 mm aus dem nur 4 mm dicken Kragen heraus und der Einsatz sitzt zur Haelfte in der Luft.
MIN_WALL = 1.5               # [FREI] Abbruchkriterium: weniger Restwand ist ein FEHLER

# ------------------------------------------------------------------ Lautsprecher VISATON K 40 SQ [DB]
SPK = dict(c=(50.0, 36.5), frame=40.0, port_d=35.0, hole_d=3.4, pattern=32.0,
           depth=11.5, behind=10.9)
SPK_WALL = 6.0                                              # [FREI]
CAV = dict(x0=18.0, x1=82.0, y0=18.5, y_front=52.5, y_back=56.0, d=12.0)   # [FREI]
BLOCK = dict(x0=12.0, x1=88.0, y0=15.5, y1=61.5)            # [FREI]
VENT = dict(d=12.2, c=(26.0, 36.5))                         # [DB] Bopla DAE M12x1.5

# ------------------------------------------------------------------ Kabel
GLAND = dict(hole_d=25.5, boss=34.0, wall=5.0, c=(50.0, 170.0))   # [DB] Conta-Clip KDS-KV M25
# Sitzt in der RUECKWAND. (50,210) war falsch: dort schneidet der Ø34-Boss die Freiraumsaeule
# hinter dem Taster (braucht Ø28.9 bis 45.3 mm Tiefe).
CABLES = dict(data=3, data_d=3.0, power=1, power_d=6.0)          # [DB]
PLUG_ENV = dict(w=20.0, h=20.0, l=60.0)   # [PLATZ] Stecker + Knickschutz - NICHT veroeffentlicht

# ------------------------------------------------------------------ Platinen [DB]
BRD_B = dict(x=8.0, y=100.0, w=72.8, h=21.0, hx=(1.58, 55.73), hy=(1.37, 19.62))
REG = dict(x=10.0, y=150.0, w=17.8, h=20.3, holes=[(2.2, 2.2), (15.6, 18.1)])
AMP = dict(x=68.0, y=150.0, w=17.78, h=19.05, holes=[(2.54, 2.54), (15.24, 2.54)])

PLATE = dict(x0=16.0, x1=84.0, y0=64.0, y1=200.0, t=4.0)    # [FREI]
PLATE_Z = 22.0                                              # [PLATZ]
PLATE_BOSSES = [(17.5, 88.0), (17.5, 135.0), (17.5, 195.0),
                (82.5, 88.0), (82.5, 135.0), (82.5, 195.0)]
ANCHORS = [(21.0, 75.0), (79.0, 75.0), (21.0, 239.0), (79.0, 239.0)]   # [FREI]
ANCHOR_D, ANCHOR_HEAD_D = 9.0, 16.0
ACCESS_R = 6.0

TESTPRINT_DEPTH = 20.0       # [FREI] Montage-Testdruck: nur die vorderen 20 mm


# ------------------------------------------------------------------ Regelpruefung
def _rrect_inset(x, y, r):
    """Abstand von (x,y) bis zur Aussenkontur des abgerundeten Kastens."""
    ix0, ix1 = BOX["x0"] + r, BOX["x1"] - r
    iy0, iy1 = BOX["y0"] + r, BOX["y1"] - r
    dx, dy = max(ix0 - x, 0.0, x - ix1), max(iy0 - y, 0.0, y - iy1)
    if dx > 0 and dy > 0:
        return r - math.hypot(dx, dy)
    return min(x - BOX["x0"], BOX["x1"] - x, y - BOX["y0"], BOX["y1"] - y)


def validate(verbose=True):
    errs, warns, oks = [], [], []

    def rule(ok, msg, hard=True):
        (oks if ok else (errs if hard else warns)).append(msg)

    # --- 0. Eingefrorene Masse: zuerst, und ohne Ausnahme.
    for _k, _want in FROZEN.items():
        _got = globals()[_k]
        rule(_got == _want, "EINGEFROREN %-14s = %s%s" % (_k, _want,
             "" if _got == _want else "  <<< STEHT AUF %s" % (_got,)))

    # --- 1. Restwand um jedes Loch in der Aussenwand. DAS war der Fehler in v2.
    for (x, y) in SCREWS_DIRECT:
        w = _rrect_inset(x, y, CORNER_R) - DIRECT_D / 2
        rule(w >= MIN_WALL, "Direktschraube (%.0f,%.0f): %.2f mm Restwand" % (x, y, w))
    for (x, y) in SCREWS:
        w = _rrect_inset(x, y, CORNER_R) - INS["d"] / 2
        rule(w >= MIN_WALL, "Blendenschraube (%.0f,%.0f): %.2f mm Restwand zur Aussenkontur "
                            "(min %.1f)" % (x, y, w, MIN_WALL))
    for (x, y) in ANCHORS:
        w = _rrect_inset(x, y, CORNER_R) - ANCHOR_HEAD_D / 2
        rule(w >= MIN_WALL, "Wanddübel (%.0f,%.0f): %.2f mm Restwand um die Senkung" % (x, y, w))

    _gap = BTN_SCREW_CC / 2 - INS["d"] / 2 - (BTN_ORING["mean"] + BTN_ORING["w"]) / 2
    rule(_gap >= 0.8, "Tasterschraube haelt %.2f mm Abstand zur O-Ring-Nut" % _gap)
    rule((BTN_ORING["mean"] - BTN_ORING["w"]) / 2 > (BTN_CYL_D + 0.6) / 2 + 2.5,
         "O-Ring-Nut liegt ausserhalb der Fuehrungshuelse")
    rule(INS["l"] <= BTN_PLATE_T - 0.5, "Tasterschraube: Einsatz %.1f tief passt in die %.1f mm "
         "Tragscheibe" % (INS["l"], BTN_PLATE_T))
    rule(INS["l"] <= FLANGE_T + INS_BOSS["l"], "Einsatzloch %.1f tief passt in Kragen %.1f + Dom %.1f"
         % (INS["l"], FLANGE_T, INS_BOSS["l"]))
    rule(INS_BOSS["d"] / 2 + 0.5 <= FLANGE_W, "Einsatzdom Ø%.1f passt in den %.1f mm Kragen"
         % (INS_BOSS["d"], FLANGE_W))

    # --- 2. Blendenschrauben duerfen keine Blendenoeffnung treffen
    for (x, y) in SCREWS:
        r = SCREW_HEAD / 2
        rule(not (DISPLAY_WIN["x0"] - r < x < DISPLAY_WIN["x1"] + r
                  and DISPLAY_WIN["y0"] - r < y < DISPLAY_WIN["y1"] + r),
             "Blendenschraube (%.0f,%.0f) frei vom Displayfenster" % (x, y))
        rule(math.hypot(x - BTN_C[0], y - BTN_C[1]) > BTN_HOLE / 2 + r,
             "Blendenschraube (%.0f,%.0f) frei vom Tasterausschnitt" % (x, y))
        rule(not (GRILLE["x0"] - r < x < GRILLE["x1"] + r
                  and GRILLE["y0"] - r < y < GRILLE["y1"] + r),
             "Blendenschraube (%.0f,%.0f) frei vom Gitter" % (x, y))
        rule(min(math.hypot(x - mx, y - my) for (mx, my) in MICS) > r + MIC_D,
             "Blendenschraube (%.0f,%.0f) frei von den Mikrofonloechern" % (x, y))
        rule(not (DIFFUSOR["x0"] - r < x < DIFFUSOR["x1"] + r and y < DIFFUSOR["r"] + r),
             "Blendenschraube (%.0f,%.0f) frei vom Diffusor" % (x, y))

    # --- 3. Dichtnut: Lage, Abstand zu den Einsaetzen, Eckradius vs Schnurbiegung
    for (x, y) in SCREWS:
        gx = BOX["x0"] + GROOVE["left"] if x < 50 else BOX["x1"] - GROOVE["right"]
        gy = BOX["y0"] + GROOVE["top"] if y < 130 else BOX["y1"] - GROOVE["bottom"]
        d = min(abs(x - gx), abs(y - gy)) - INS["d"] / 2 - GROOVE["w"] / 2
        rule(d >= 0.5, "Dichtnut haelt %.2f mm Abstand zum Einsatz (%.0f,%.0f)" % (d, x, y))
    r_mid = (CORNER_R + max(CORNER_R - GROOVE["w"], 0.5)) / 2
    rule(r_mid >= 3 * 2.0, "Nut-Eckradius R%.1f = %.1f x Schnurdurchmesser (min 3x)"
         % (r_mid, r_mid / 2.0), hard=False)

    # --- 4. Tasterausschnitt gegen Kragen und Nut
    r = BTN_HOLE / 2
    rule(BOX["y1"] - (BTN_C[1] + r) > 0, "Tasterausschnitt endet %.2f mm vor der Kastenunterkante"
         % (BOX["y1"] - (BTN_C[1] + r)))
    gy = BOX["y1"] - GROOVE["bottom"]
    dy = gy - BTN_C[1]
    cut = 2 * math.sqrt(max(r ** 2 - dy ** 2, 0.0)) if abs(dy) < r else 0.0
    rule(cut == 0.0, "Untere Dichtnut vom Tasterausschnitt nicht unterbrochen (sonst %.1f mm)" % cut)

    # --- 5. Lautsprecher: Fenster, Display, Hohlraum
    y0s, y1s = SPK["c"][1] - SPK["frame"] / 2, SPK["c"][1] + SPK["frame"] / 2
    rule(y0s > LED_WIN_Y[1], "Lautsprecher (y %.1f) haelt %.1f mm Abstand zu den LED-Fenstern"
         % (y0s, y0s - LED_WIN_Y[1]))
    rule(y1s < DISPLAY_PANEL_TOP, "Lautsprecher (y %.1f) haelt %.1f mm Abstand zum Displaypanel"
         % (y1s, DISPLAY_PANEL_TOP - y1s))
    rule(CAV["x0"] < GRILLE["x0"] and CAV["x1"] > GRILLE["x1"] and CAV["y0"] < GRILLE["y0"]
         and CAV["y_front"] >= GRILLE["y1"] - 0.5, "Gitter liegt vollstaendig im Hohlraum")
    rule(CAV["y_front"] <= GRILLE["y1"], "Hohlraumboden trifft das Blech %.1f mm ueber der "
         "untersten Schlitzreihe - Wasser laeuft ab" % (GRILLE["y1"] - CAV["y_front"]))
    half = SPK["pattern"] / 2 + SPK["hole_d"] / 2 + 2.0
    d_diag = SPK["pattern"] / 2 * math.sqrt(2)      # Lochkreis DIAGONAL, nicht Mittellinie
    rule(SPK["port_d"] / 2 + SPK["hole_d"] / 2 < d_diag,
         "Lautsprecherschrauben liegen auf %.2f mm vom Zentrum, Schalloeffnung reicht bis %.2f"
         % (d_diag, SPK["port_d"] / 2 + SPK["hole_d"] / 2))
    rule(BLOCK["y1"] < DISPLAY_PANEL_TOP, "Gittermodul endet %.1f mm vor dem Displaypanel"
         % (DISPLAY_PANEL_TOP - BLOCK["y1"]))

    # --- 6. Tiefenbudget
    need_btn = (RING_T - SHEET["t"]) + BTN_CYL_L + BTN_FREE
    need_spk = CAV["d"] + SPK_WALL + SPK["behind"]
    inner = DEPTH - BACK
    rule(need_btn <= inner, "Tiefe: Taster braucht %.2f von %.2f mm Innentiefe" % (need_btn, inner))
    rule(need_spk <= inner, "Tiefe: Lautsprecher braucht %.2f mm" % need_spk)
    rule(inner - need_btn >= 2.0, "Tiefenreserve %.2f mm" % (inner - need_btn), hard=False)

    # --- 7. Kabelverschraubung
    gx, gy = GLAND["c"]
    rule(_rrect_inset(gx, gy, CORNER_R) > GLAND["boss"] / 2,
         "Kabelverschraubung: Boss Ø%.0f passt an Position (%.0f,%.0f)" % (GLAND["boss"], gx, gy))
    rule(math.hypot(gx - BTN_C[0], gy - BTN_C[1]) > (BTN_CYL_D + BTN_FREE) / 2 + GLAND["boss"] / 2,
         "Kabelverschraubung frei von der Taster-Freiraumsaeule")
    rule(GLAND["wall"] >= 3.0, "Wand an der Verschraubung %.1f mm (Mutter braucht >= 3)"
         % GLAND["wall"])

    # --- 8. Erreichbarkeit der Wandduebel mit eingebauter Hardware
    for (x, y) in ANCHORS:
        blocked = []
        if (BLOCK["x0"] - ACCESS_R < x < BLOCK["x1"] + ACCESS_R
                and BLOCK["y0"] - ACCESS_R < y < BLOCK["y1"] + ACCESS_R):
            blocked.append("Gittermodul")
        if not (BOX["x0"] + FLANGE_W + ACCESS_R <= x <= BOX["x1"] - FLANGE_W - ACCESS_R
                and BOX["y0"] + FLANGE_W + ACCESS_R <= y <= BOX["y1"] - FLANGE_W - ACCESS_R):
            blocked.append("Kragen")
        if math.hypot(x - BTN_C[0], y - BTN_C[1]) < (RING_D - 1.0) / 2 + ACCESS_R:
            blocked.append("Tasterscheibe")
        for nm, o in (("Board B", BRD_B), ("Regler", REG), ("Verstaerker", AMP)):
            if (o["x"] - ACCESS_R < x < o["x"] + o["w"] + ACCESS_R
                    and o["y"] - ACCESS_R < y < o["y"] + o["h"] + ACCESS_R):
                blocked.append(nm)
        rule(not blocked, "Wanddübel (%.0f,%.0f) erreichbar%s"
             % (x, y, "" if not blocked else " - VERDECKT von " + ", ".join(blocked)))

    # --- 9. Platinen im Innenraum, frei von der Tasterhuelse
    sleeve_r = (BTN_CYL_D + 0.6) / 2 + 2.5
    for nm, o in (("Board B", BRD_B), ("Regler", REG), ("Verstaerker", AMP)):
        rule(o["x"] >= BOX["x0"] + WALL and o["x"] + o["w"] <= BOX["x1"] - WALL
             and o["y"] >= BOX["y0"] + WALL and o["y"] + o["h"] <= BOX["y1"] - WALL,
             "%s liegt im Innenraum" % nm)
        dx = max(o["x"] - (BTN_C[0] + sleeve_r), BTN_C[0] - sleeve_r - (o["x"] + o["w"]))
        dy = max(o["y"] - (BTN_C[1] + sleeve_r), BTN_C[1] - sleeve_r - (o["y"] + o["h"]))
        rule(max(dx, dy) > 0, "%s frei von der Tasterhuelse (%.1f mm)" % (nm, max(dx, dy)))

    # --- 10. Schraubenabstand entlang der Dichtung (Durchbiegung der Blende)
    ys = sorted({y for (_, y) in SCREWS})
    span = max(b - a for a, b in zip(ys, ys[1:])) if len(ys) > 1 else 0.0
    rule(span <= 120.0, "Groesster Schraubenabstand laengs %.0f mm (Faustregel <= 120 fuer eine "
         "gleichmaessig gepresste Dichtung)" % span, hard=False)

    if verbose:
        for m in oks:
            print("  OK      %s" % m)
        for m in warns:
            print("  WARNUNG %s" % m)
        for m in errs:
            print("  FEHLER  %s" % m)
        print("\n%d Regeln: %d ok, %d Warnungen, %d FEHLER" % (len(oks) + len(warns) + len(errs),
                                                               len(oks), len(warns), len(errs)))
    return errs, warns


if __name__ == "__main__":
    validate()
