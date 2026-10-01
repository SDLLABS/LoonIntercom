# Screen computer firmware

ESPHome firmware for the screen at the door: a LilyGO T5-4.7-S3 Touch (board V2.4) with a 4.7" e-paper
panel (ED047TC1, 960 × 540, 16 grey levels) and a GT911 touch chip. Bench-tested on 29 September 2026.

| File | What |
|---|---|
| `screen-test.yaml` | bench test page: orientation arrow, five touch targets, border lines |
| `screen-demo.yaml` | what the screen can do, 8 pages: drawing, photos, vector graphic and icons, QR codes, text sizes, grey levels, animation; bottom bar = page changes |
| `demo/demo.h`, `make_demo_assets.py`, `demo-assets/` | helpers and test pictures for the demo (`local-assets/` is generated from local sample photos and not published) |
| `components/lilygo_t5_47_plus/` | the display, touch and battery driver (**GPLv3**, see below), with the fast refresh |

## Build and flash

Needs ESPHome 2026.3 or newer (tested with 2026.9.0).

```
esphome compile screen-test.yaml
esptool --port COMx --after watchdog-reset write-flash 0x0 .esphome/build/klingel-screen-test/build/firmware.factory.bin
```

- **Windows:** build from PowerShell or cmd, not from Git Bash. ESP-IDF refuses to install from an MSYS shell.
- **First flash:** hold `STR_IO0`, tap `REST`, release `STR_IO0`, then flash. After that the USB port resets the
  board by itself. Use `--after watchdog-reset`: a plain reset can leave the chip in download mode.
- **Orientation:** `rotation: 270` gives portrait with the ribbon end of the glass at the bottom.
- **Touch:** no `transform`. The GT911 already reports portrait 540 × 960 in exactly this orientation.
  The upstream example (`swap_xy` + `mirror_y`) is for landscape.
- **Glass print:** the white print of the touch glass hides the outer 7–9 px of the panel on every edge.
  Keep content at least 10 px from the edge.

## How the screen updates without flashing

The upstream driver wipes the whole panel black and white before every picture (2 s, a full flash). That
looks like a defect to anyone at the door. The driver here keeps the flash for rare clean-ups and updates
everything else like an e-reader. These are the rules, in this order:

1. **Compare, don't clear.** The driver keeps a copy of what the panel shows. A new picture is compared
   with it pixel by pixel; unchanged pixels get no voltage at all.
2. **Darker: continue the grey scale. Lighter: undraw.** Grey level `v` (0 black … 15 white) is darkness
   `d = 15 − v`. The panel builds a grey from white in 15 frames: a pixel of darkness `d` is darkened in
   frames `0 … d−1`. A pixel that gets darker continues: frames `[d_old, d_new)`. A pixel that gets lighter
   is **undrawn**: lightened in frames `0 … d_old−1`, exactly the frames it was darkened with, then darkened
   to its new grey `0 … d_new−1` (a second phase, used when many greys sit next to lightened pixels).
   **Balance above everything:** a pixel must never get more white ink than it had black ink, or the other
   way round. A version that lightened every pixel fully (15 frames) ran a grey spinner for 110 frames and
   left a ring that even a full flash did not remove. E-paper has to be driven DC-balanced.
3. **One sweep.** All changed rows are driven in the same sweep (15 frames, or 30 with phase B), plus
   one neutral frame so no pixel is left holding a voltage. Only the changed stretch of each row is computed.
4. **Re-darken the fringe.** Lightening spills over onto neighbouring pixels and fades thin dark lines that
   did not change. Every unchanged dark pixel within 2 px of a lightened one is darkened again.
5. **Never block the input.** Refreshing runs in its own task. The main loop only hands over the newest
   picture and keeps reading touch; if pictures pile up, the panel jumps straight to the newest one.
6. **Clean up now and then.** Small updates leave faint traces. A full refresh with the flash runs at boot,
   every `full_update_every` partial refreshes (default 30, 0 = never), when more than half the screen
   changes, and on request (`id(epaper).request_full_update()`, e.g. at night).
7. **Power off after every picture**, as the original driver does. **No endless animations:** a few
   seconds at most; a running animation repeats every small imbalance hundreds of times.
8. **Same ink time for every update, exactly.** E-ink pigment needs time under voltage, and a sweep over
   a few rows is over much sooner than one over many. So every frame of a partial refresh is held until it
   lasts as long as the same frame in a full refresh (`partial_drive_percent`, keep 100; the full refresh at
   boot measures the frames, about 49 ms each). Shorter frames (60 %, tried for speed) make small updates
   grey at first and, worse, unbalanced: a page change undraws with full-refresh timing, so a drawing made
   with short frames got 1.7 times more white ink than black ink and left a light trace on the next page.
9. **True page change = explicit flag, and it flashes.** The UI marks a switch to another screen with
   `request_page_change()`; that picture gets a full refresh with **one short black-white flash**
   (`PAGE_CHANGE_SHORT_FLASH`, about 1 s, the default). Tested on the bench (2026-09-29): the short flash
   is as clean as the long one (four cycles, about 2 s), and only a flash leaves no trace. Every gentle route left the previous screen behind
   as a light trace: lightening only, undrawing the old picture with the darkening timing, undrawing with
   epdiy's gentler white timing, and the same for erasing within a page. Without measured manufacturer
   waveforms (none are public for the ED047TC1; epdiy's are generic tables from the same timings) the ink
   keeps a memory of what it showed, and only balanced full black-white cycles reset it. Changes within
   a screen stay partial and flash-free; erasing large content counts as a page change; after a pause
   without a touch, one flash cleans up while nobody looks.

Measured on the bench: a tap changes the picture in about 0.5 s (the original driver: 2.0–2.3 s), with no
flash and no visible shadow.

The panel stands on its side: its rows run across the portrait page. A line of text across the page
therefore touches about 300 of the 540 panel rows, and more rows mean a slower update.

## Licence of the driver

`components/lilygo_t5_47_plus/` is a modified copy of
[hbast/lilygo_t5_47_plus](https://github.com/hbast/lilygo_t5_47_plus) v1.0.0, which derives from
[vroland/epdiy](https://github.com/vroland/epdiy) and LilyGO's
[LilyGo-EPD47](https://github.com/Xinyuan-LilyGO/LilyGo-EPD47). It keeps the ESPHome licence of its
source: the C and C++ files are **GPLv3**, the Python files MIT ([LICENSE](components/lilygo_t5_47_plus/LICENSE)).
The changes for the fast refresh are in `display.cpp`, `display.h`, `display.py` and `epd_draw_plan`
in `epd_driver.c` / `epd_driver.h`, under the same terms. Everything else in this
repository stays MIT.
