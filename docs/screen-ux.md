# What the door screen can do

The screen at the door is a 4.7" e-paper panel (ED047TC1, 540 × 960 portrait, 0.108 mm per pixel, 16 grey
levels) behind a touch glass, on a LilyGO T5-4.7-S3 board. These findings come from a demo program with
eight test pages ([`firmware/screen/screen-demo.yaml`](../firmware/screen/screen-demo.yaml)), judged on
the real panel at arm's length. They set the rules for the door pages; how the screen updates is in
[`firmware/screen/README.md`](../firmware/screen/README.md).

| Topic | What we saw | Rule |
|---|---|---|
| Text | everything is readable up close; at a normal distance 32 px is the smallest that works | text for visitors ≥ 32 px (3.5 mm) |
| Line art | a dimensioned drawing: names in the engraving readable, the tiny dimension text not | no text below ~12 px |
| Icons (Material Symbols) | 32, 48, 72 and 96 px all very clear | icons work from 32 px |
| QR codes | a phone scans every size, even 6.3 mm (0.22 mm modules), through the glass | any size works; ~12 mm to be safe |
| Grey levels | levels 0–6 look alike, and so do 14 and 15 | only about 8 greys are distinguishable: black, a few mid tones, white |
| Fine patterns | 1 px lines just visible up close, 2 px better, a 1 px checkerboard reads as flat grey | lines ≥ 2 px |
| Drawing with a finger | solid black, continuous line, follows in steps of about half a second | usable for a quick sketch or note |
| Changing to another page | every flash-free way left the previous page behind as a faint light trace; a flash leaves none, and one short black-white cycle (~1 s) is enough | a real page change is marked as such and gets a short flash; changes within a page stay flash-free |
| Leftover traces | small updates within a page leave faint history over time | one flash after a pause without a touch, while nobody is looking |
| Animation | 1–2 frames per second; running animations accumulate traces | short and small only, never endless |

Still open: plain or dithered photos, and how long the pause before the clean-up flash should be at the door.
