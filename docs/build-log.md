# Build log

What happened, in order, including the dead ends. Dates are 2026.

## August: a doorbell that works

- The old doorbell had been dead for a long time: its button's circuit board had died from rain.
- First version: a plain brass button on an existing two-wire cable into an ESP32 indoors,
  running ESPHome, with a push notification through Home Assistant. No chime.
- **Lesson:** a floating input pin on a long cable acts as an antenna. At one point it
  produced 134 phantom rings in 15 minutes. The fix became the supervised line: pull-up,
  series resistor, filter capacitor and an end-of-line resistor at the button, so idle,
  pressed and a cut wire give three different voltages.
- **Lesson:** a component only does something if current can flow *through* it. A resistor
  plugged into an empty breadboard row changed nothing, and only the multimeter showed it.

## 17 September: from doorbell to intercom

- New goal: a small e-paper screen at the door, later speech in both directions.
- **Hard rule from day one: no camera at the door, ever.**
- Front design in five rounds of dimensioned drawings (generated in Python, true scale):
  - v2: portrait screen, one button, speaker grille;
  - v3: flush in the wall, a separate brass roof cap, a cable pipe bending into the wall;
  - v4: back to one folded sheet, with a brass cable pipe rising in front of the wall (rejected);
  - v5: no pipe, 100 × 260 mm, LED band in the fold with a quarter-round diffuser.

## 18 September: CAD

- The front sheet, the in-wall box, a carrier plate and the diffuser modelled in FreeCAD,
  driven by scripts. First prints of the sheet (in two parts, it is taller than the print bed)
  and the box.
- The speaker changed from a 3 W waterproof part to the smaller VISATON K 40 SQ: it is quieter on
  paper (0.5 W) but louder in practice (82 dB vs 74 dB at 1 W / 1 m). Sensitivity beats wattage.

## 24 September: parts, architecture, explorer

- Most parts arrived and were identified (some sold under vague names: an opto-coupled MOSFET
  module turned out to be usable because its optocoupler drives the gate from 12 V).
- Architecture settled:
  - **one** ready-made outdoor PoE cable instead of three cables plus a power cable;
  - three computers: a wired doorbell computer, a talk computer on WiFi, a screen computer
    on WiFi;
  - two-way talk via the community VoIP Stack for ESPHome, with walkie-talkie mode as the
    fallback.
- The [explorer](../explorer/) was built to make the whole system understandable, including
  every wire and every solder joint.

## 25 September: a roadmap

- Eight milestones from the bench to the door, with a separate track that proves the box can be
  sealed before the real brass plate is bought. See the [roadmap](roadmap.md).

## 29 September: the screen computer

- The LilyGO T5-4.7-S3 Touch arrived. The sources disagreed about its touch chip: LilyGO's wiki
  says GT911, their own driver code expects an L58. Only the GT911 has an ESPHome driver.
- A scan of the board's I²C bus answered it: **GT911 at address 0x5D** (it answers "911" when
  asked for its product id), plus the PCF8563 clock chip at 0x51. The script is
  [`tools/touch_scan.py`](../tools/touch_scan.py); it runs on MicroPython.
- **Lesson:** read out the whole flash before flashing anything. The factory program went into a
  16 MB backup first, so it can be put back byte for byte.
- Measured with a caliper, because LilyGO publishes none of it: seven mounting holes, the touch glass,
  the visible picture area and the folded stack ([numbers](../hardware/parts/lilygo-t5-s3-touch-measured.md)).
- **Surprise:** the screen arrives loose on two ribbons and is folded onto the board by the buyer.
- **Lesson:** a datasheet's active area is not what you see. The glass's white print hides almost 1 mm
  on every side, and the brass window has to be sized to what is visible.

- The screen runs ESPHome. The community driver wiped the whole panel black and white before every
  picture: two seconds of flashing, which at a door looks like a fault. The driver in
  [`firmware/screen/`](../firmware/screen/) now moves each pixel only by the difference between its
  old and new grey, all changed rows in one sweep, in a background task so touch is never ignored.
  A tap changes the picture in about half a second, without a flash.
- **Lesson:** lightening a pixel also fades its neighbours. Thin lines next to changed pixels vanished
  until the driver re-darkened them.

- A demo with eight test pages settled what the screen can show: text from 32 px at a normal
  distance, about 8 distinguishable greys, QR codes at any size ([findings](screen-ux.md)).
- **Lesson:** a flash-free change to another page always left the previous page behind as a faint
  trace, however carefully the old picture was undone. One short black-white flash (about a second)
  clears it. So the screen flashes briefly on a real page change and stays calm within a page.
- **Lesson:** e-paper must be driven balanced. A test animation that lightened pixels more than it had
  darkened them left a faint ring after about a hundred frames that even a flash did not remove at once.

- The doorbell computer moved boards. The WT32-ETH01 booted once, then always started in download
  mode: its IO0 is both the boot-mode pin and the Ethernet clock input, and the oscillator holds it
  low. Pull-ups of 10 kΩ and 1 kΩ did not win, and a doorbell must restart on its own after a power
  cut. The Waveshare ESP32-S3-ETH took over: no clock on a boot pin, USB-C, PoE via a plug-on module.
  It started on the first try and Home Assistant found it by itself.
- **Lesson:** read the boot line before blaming the software. `boot:0x3` means the chip never ran any
  program at all; the [probe scripts](../tools/wt32/) show it without unplugging anything.

- The bell rings, on the bench: brass button, supervised line on a breadboard, firmware in
  [`firmware/bell/`](../firmware/bell/), updates over the network. Slow presses 10 of 10; storm ringing
  filmed in slow motion, 14 of 15 counted, and the 15th only grazed the contact for 1 ms.
- **Lesson:** ESPHome collects API updates for 100 ms by default. Two quick presses inside one batch
  arrive as one, so storm ringing showed 2 of 5. Setting the batch delay to 0 fixed it.
- **Lesson:** a loose wire on an analog pin looks like a press, and a half-closed brass contact
  hovers right at a single threshold. The internal pull-up and a two-threshold hysteresis fixed both.
- Cable cut and short circuit are both reported, after 10 and 60 seconds.

## Next

The plan from here is the [roadmap](roadmap.md): all hardware on the table, measure and
alpha-print the box, build the software on the bench, prove the box can be sealed, then a beta
box on the desk, a pre-release box and finally the door.
