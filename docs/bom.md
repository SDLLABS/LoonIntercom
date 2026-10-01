# What to buy (bill of materials)

State: 2026-09-24. Prices are gross, from German/EU shops, and were read off the product pages on
that date. "Pending" means the choice is not made yet; do not buy those blind.

Parts marked **measure** have dimensions the maker does not publish. The drawings in
[hardware/parts](../hardware/parts/) show what is known and what still has to be measured.

## Indoors: network and power

| Qty | Part | Why | Notes |
|---|---|---|---|
| 1 | PoE switch port, 802.3af or better | data + power down one cable | put the switch on a UPS |
| 1 | Ubiquiti ETH-SP-G2 surge protector | protects the house network from the outdoor cable | **must be earthed by an electrician**; datasheet lists 802.3af only |
| 1 | Short patch cable | switch → surge protector | |

## Through the wall

| Qty | Part | Why | Notes |
|---|---|---|---|
| 1 | Ready-made outdoor Cat6 cable, goobay **55432** (10 m) | the one cable | solid copper AWG 24/1, U/UTP, double PE jacket, UV-resistant, -40 to +75 °C, outer Ø 6.0–6.6 mm; about €11–13. **Not** goobay 94389: almost the same title, but copper-clad aluminium |
| 1 | Split cable gland Conta-Clip KDS-KV M25 BK (28611.4) | lets the moulded plug through, then seals | lock nut included; Conta-Clip gives a **25.2 mm** hole; IP66 |
| 1 | Split sealing insert Conta-Clip KDS-DE 6-7 BK (28526.4) | seals around one 6–7 mm cable | measure your cable: 5-6 BK (28525.4) and 7-8 BK (28527.4) are the neighbours. Use BK (UV-stabilised), not GR |

## In the box: power

| Qty | Part | Why | Notes |
|---|---|---|---|
| 1 | Industrial PoE splitter, rated down to -40 °C | separates data and power | **pending** — see below |
| 1 | Pololu D30V30F5 step-down 12 → 5 V, 3.4 A | 5 V rail | only with the 12 V splitter |
| 1 set | Lever clamps (WAGO 221) | 5 V and ground distribution | |
| 1 | Short Cat6 patch cable, 0.25 m, copper | splitter → doorbell computer | some cheap 0.25 m cables are CCA too |
| 1 | USB-C plug to 2-pin screw terminal (VBUS/GND only) | 5 V into the screen computer | no data lines, no CC resistor: fine for feeding power *into* the board; check polarity first |
| 2 | Resettable PTC fuse, 0.5 A hold (e.g. FREI PFRA 050) | protects the rail from the LED branch | 0.5 A covers the ~4 LEDs used |
| 2 | 1000 µF / 25 V low-ESR and 10 µF electrolytic capacitors | at the LED strip and at the amplifier | stripe = minus |

**The splitter decision**

| | 12 V: TRENDnet TI-SG104 | 5 V: Waveshare industrial PoE splitter |
|---|---|---|
| Price seen | about €69–70 | €33.99 (DC plug) |
| Temperature | -40 to +75 °C | -40 to +85 °C |
| Size | 104 × 82 × 32 mm | 102.5 × 29.6 × 24.8 mm |
| DC output | 4-pin screw terminal | pigtail with a DC barrel plug (reviews disagree whether it is 5.5 × 2.1) or a USB-C variant |
| Power from 802.3af | 10.2 W at 12 V (TRENDnet's figure for version 2) | not stated |
| Heater switch | the opto-coupled FR120N module works (12 V gate drive) | needs a logic-level, non-isolated module (3.3–20 V trigger); opto-isolated "D4184" boards have the same gate problem as the FR120N |
| Heater | 12 V pad | 5 V polyimide foil (about 4.2 W, 0.84 A on the 5 V rail) |

## In the box: the three computers

| Qty | Part | Why | Notes |
|---|---|---|---|
| 1 | Waveshare ESP32-S3-POE-ETH (board + plug-on PoE Module (B)) | doorbell computer, wired | about €25–32; USB-C, so no serial adapter. Pin headers come loose and must be soldered |
| 1 | talk computer: open, an ESP32-S3 with PSRAM | two-way talk, on WiFi | the WT32-ETH01 planned first is **not** recommended: see [`firmware/bell/`](../firmware/bell/README.md#why-not-the-wt32-eth01) |
| 1 | LilyGO T5-4.7-S3 **Touch** (SKU H716) | screen computer + 4.7" e-paper, 960 × 540 | about €55 at OpenELAB; several marketplace listings with a touch photo are **not** touch versions; **measure** the mounting holes. Touch chip on ours: GT911 at I²C 0x5D, which ESPHome supports (check yours with `tools/touch_scan.py`) |

## Audio

| Qty | Part | Why | Notes |
|---|---|---|---|
| 1 | INMP441 I²S MEMS microphone module | voice at the door | 3.3 V only; the labelled side (sound hole) faces the membrane |
| 1 | Adafruit MAX98357A I²S amplifier | drives the speaker | set to 3 dB: 100 kΩ from GAIN to Vin (GAIN to ground is 12 dB, louder); 10 µF + 0.1 µF at its supply |
| 1 | VISATON K 40 SQ, 8 Ω, IP65/67 front | speaker behind the grille | 40 × 40 mm, Ø35 cut-out, 11.5 mm deep, 4 × Ø3.4 on 32 × 32; about €5.50 |
| 1 pack | Self-adhesive PTFE vent membrane B+B Thermo-Technik DAM-AD10 (12 pcs) | keeps water out of the mic holes | 10.2 mm outer, **5.5 mm active**: one membrane per mic hole. Sold as a pressure vent: test voice quality through it |

## Light, sensor, heater

| Qty | Part | Why | Notes |
|---|---|---|---|
| 1 | SK6812 RGBW LED strip, 5 V, ~4 LEDs used | light under the roof + status colours | a real white channel helps; **measure** height |
| 1 | SN74AHCT125N (DIP-14) + DIP-14 socket + 330 Ω | lifts the 3.3 V LED data to 5 V | cheap insurance against flaky LEDs in the cold |
| 1 | BME280 module (with humidity) | box temperature and humidity | many "BMP280" boards look the same: check the chip ID (0x60) |
| 1 | Heater for the 12 V path: silicone pad 12 V / 5 W, Ø50 mm — or a self-adhesive PTC foil 12 V / 3 W, 47 × 60 mm | keeps the e-paper above 0 °C | the silicone pad listing shows no adhesive, and acrylic tape bonds poorly to silicone; the PTC foil limits its own temperature |
| 1 | Thermal fuse 73 °C | one-shot overheat cut-off | soldering heat can blow it: clamp the leads in WAGO 221 clamps or crimp them with uninsulated butt connectors |
| 1 | Opto-coupled MOSFET module (FR120N type) | switches the heater | 12 V path only |
| – | Thermally conductive double-sided tape | only if the heater is not self-adhesive | |

## Button line

| Qty | Part | Why | Notes |
|---|---|---|---|
| 1 | A plain (dumb) brass push button, no electronics | the doorbell | the prototype uses a Ø48.5 mm ring |
| 2 | 10 kΩ resistor | pull-up + end-of-line at the button | the end-of-line one is soldered across the button contacts |
| 1 | 1 kΩ resistor, 1 × 100 nF capacitor | series resistor and filter | on perfboard |
| – | Adhesive-lined heat shrink | seals the joint behind the button | |

## Enclosure and front

| Qty | Part | Why | Notes |
|---|---|---|---|
| – | Filament for the box: ASA, or PETG | box and carrier plate | ASA is more UV-resistant, but Bambu Lab advises against large or dense ASA/ABS parts on the open-frame A1; PETG is the A1-friendly option |
| – | Translucent filament | diffuser | |
| – | PLA | front-sheet prototype | the final front is brass |
| 1 | 2 mm brass sheet, laser-cut and folded by a metal shop | the final front | from [the front-sheet STEP](../hardware/models/front-sheet-v5.step); only after the bench tests pass; have the countersinks done there (at least 1.7 mm deep) |
| 4 | M3 × 8 countersunk brass screws, single slot (DIN 963) + M3 heat-set inserts (6 mm long) | hold the front | M3 × 8 matches a 6 mm insert under a 2 mm sheet; M3 × 10 needs a 2 mm deeper hole |
| 1 | Pressure vent M12 × 1.5 (AGRO 595.15.AS, -40 to +100 °C, or Bopla DAE M12) + M12 × 1.5 lock nut | the sealed box breathes | vents into the grille cavity; Bopla: 12.2 mm hole + nut for walls under 3 mm, a printed M12 thread for thicker walls |
| – | Round gasket cord Ø2.0 mm, **solid** EPDM (not foam), about 1–2 m | rain seal between box and front | ends glued into a ring; a 2.0 mm cord fills a 2.4 × 1.5 mm groove to about 87 %, so a slightly wider groove is better |
| 1 | O-ring 26 × 2 mm (EPDM or NBR) | seals the button | use silicone grease, not mineral grease (EPDM swells) |
| – | Silica gel sachets | buffer against condensation | the vented box saturates them: replace now and then |
| – | Neutral-cure silicone | around the diffuser | acetic-cure silicone corrodes brass |
| – | Conformal coating (e.g. Kontakt Chemie PLASTIK 70) | protects the boards | rated only to +60 °C continuous: keep it away from the heater; mask the mic, the sensor, sockets and clamps |

## Tools and consumables

Solder with flux, perfboard, female pin headers (to plug modules instead of soldering them in),
nylon standoffs, wire ferrules and crimper, 22 AWG silicone wire, Kapton tape, isopropyl
alcohol, a multimeter, and a real USB-C data cable for flashing the S3 boards.

## Optional

| Qty | Part | Why |
|---|---|---|
| 1 | Home Assistant Voice PE (+ USB-C 5 V / 3 A supply, not included) | a chime inside the house |

## Not needed any more (so you do not buy them by mistake)

- A power supply in the technical room, passive PoE injector sets, a separate DC cable.
- Field-installable RJ45 plugs and cable rolls: the ready-made outdoor cable replaces them.
- A switch inside the box (only if WiFi calls fail the in-box test).
