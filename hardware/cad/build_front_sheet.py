"""Build the front sheet from ../front-sheet/layout-v5-bemasst.svg (engraving included).

Run with FreeCAD's command-line interpreter from this folder:
    freecadcmd build_front_sheet.py
Writes STEP/STL into ./out/: the one-piece master, a one-piece print STL and a
two-part print split (for beds smaller than the 260 mm sheet).
"""
import os
import sys

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:
    HERE = os.getcwd()
sys.path.insert(0, HERE)

import make_sheet_v5 as M

M.build_shape()
M.assemble()
M.export_print()
M.export_split()
