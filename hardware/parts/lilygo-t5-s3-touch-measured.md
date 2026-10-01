# LilyGO T5-4.7-S3 Touch (H716): measured

LilyGO publishes no mounting-hole positions, no thickness and nothing about the touch glass for this
board. These numbers come from one unit, measured with a digital caliper on 29 September 2026. The
board is silkscreened "Screen-4.7-S3 V2.4 2024-12-03".

## How it arrives

The board comes bare. **The screen is not mounted on it**: e-paper panel and touch glass form one
loose module that hangs on two ribbons, plus 3M double-sided foam pads. You fold the screen onto the
board yourself, like closing a book.

- **Black ribbon (picture)**: ends in a plug block on the board's *screen side*, at the end opposite
  the USB-C socket.
- **Orange ribbon (touch)**: carries the touch controller (GT911, I²C address 0x5D) on the ribbon itself
  and plugs into a small latched socket in the middle of the board, also on the screen side.
- The large socket and the small FPC socket on the component side are empty on this unit.

## Board

Lay it component side up, USB-C edge at the bottom. x counts from the left long edge (the one with the
microSD slot), y from the USB-C edge. All values in mm.

| | |
|---|---|
| Outline | 118.2 × 63.0 (LilyGO's V2.3 DXF: 118.122 × 63.119) |
| Thickness | 1.4 |
| Tallest part above the component side | 5.9 (7.28 over board and part) |
| Plug block of the picture ribbon | stands 1.82 above the screen side |

**Seven through-holes, Ø3.94:**

| Hole | Where | x | y |
|---|---|---|---|
| 1 | far end, left, outer | 4.54 | 113.06 |
| 2 | far end, left, inner | 4.53 | 105.88 |
| 3 | far end, right pair, outer | 47.73 | 112.92 |
| 4 | far end, right pair, inner | 47.98 | 105.92 |
| 5 | USB end, left corner | 4.58 | 5.18 |
| 6 | USB end, left of the USB-C socket | 12.56 | 5.17 |
| 7 | USB end, right corner | 58.39 | 5.21 |

Measured as the solid strip between board edge and hole wall, plus half the hole, so each centre is good
to about ±0.15. Holes 3 and 4 read 0.25 apart in x and are probably on one line.

## Screen module

| | |
|---|---|
| Touch glass | 120.1 × 66.77 |
| White print border | 4.91 on three sides, 13.28 at the ribbon end |
| Visible picture area | 56.95 × 101.9, centred across the glass |
| Thickness | about 2.1 (glass + panel) |
| 3M foam pad | 2.3 with its covers on |
| Cut-outs in the glass | none |

The panel's datasheet active area is 58.32 × 103.68; the white print covers roughly the outer
0.7–0.9 mm of it. **Size a window over this display to the visible 56.95 × 101.9, not to the
datasheet**, or a white line shows.

## Folded together

Folded as LilyGO intends, on the pads:

- Glass front to the back of the tallest part: **11.9**.
- At the far end the glass and the board are flush. At the USB end the glass overhangs the board by 1.9,
  and the ribbon bend stays inside the glass outline.
- The visible area then sits 4.91 below the board's far edge and about 3.0 in from each long edge.
- All seven holes end up under the glass. A screw head on the screen side only has the pad gap
  (about 2.3), so mount from the component side.
