# Architecture

State: 2026-09-24. Prototype stage: parts are on the bench, nothing is installed at the door yet.

The interactive version of this page is the [explorer](../explorer/). It shows every part, wire,
joint and solder spot, and walks through what happens on a ring, in winter, at dusk and during a call.

## The idea in one picture

```
 house network                 technical room                wall           box in the facade          brass front
 ─────────────                 ──────────────                ────           ─────────────────          ───────────
 Home Assistant ── LAN ── PoE switch (on a UPS) ── surge ── one outdoor ── cable ── PoE splitter ─┬─ data ─ doorbell computer ── button, light, heater, sensor
       │                                         protector   Cat6 cable    gland        │         │
       │                                          (earthed)                             │         └─ DC ─── 5 V rail ── talk computer ── mic, amplifier, speaker
       │                                                                                │                        └──── screen computer ── 4.7" e-paper touch
       └──────────────── WiFi access point ~1 m away ···· radio ···· talk + screen computers
```

- **One cable.** A single ready-made outdoor Cat6 cable carries data and power (PoE, about 48 V)
  from the switch into the box. There is no power supply at the door and no switch in the box.
- **Three small computers, each with one job.** They share only power and ground; no signal
  wires run between them.

| Computer | Board | Link | Job |
|---|---|---|---|
| Doorbell computer | Waveshare ESP32-S3-ETH (W5500), PoE via its plug-on module | wired | button line, light, heater, climate sensor, power governor |
| Talk computer | open: an ESP32-S3 with PSRAM (the talk stack needs it) | WiFi | microphone, amplifier, two-way talk |
| Screen computer | LilyGO T5-4.7-S3 Touch (H716) | WiFi | 4.7" e-paper touch screen behind the brass window |

Why three and not one: the bell is the one function that must never fail. A crash or an update
in the audio code cannot take it down when it runs on its own board with stock ESPHome only.
The e-paper panel is a parallel panel that needs its own driver board anyway.

## The ring path (the part that must always work)

1. The brass button sits on a **supervised line**: 10 kΩ pull-up to 3.3 V, 1 kΩ series resistor,
   100 nF to ground, and a 10 kΩ end-of-line resistor soldered straight across the button.
   That gives three distinct voltages on an analog (ADC1) input:

   | State | Voltage (measured on the bench, with the ESP's internal pull-up on) |
   |---|---|
   | idle | 2.03 V |
   | pressed | 0.34 to 0.47 V (a half-closed contact: 0.6 to 0.9 V) |
   | wire cut | 3.18 V |

   A cut or corroded wire is reported instead of going silent. The pull-up exists because a
   floating input on the first prototype produced 134 phantom rings in 15 minutes. The ESP's own
   pull-up is switched on as well, so a loose signal wire reads as "cut", not as a press.
2. The doorbell computer samples the line every millisecond. A press starts below 1.30 V and ends
   only above 1.60 V, so a wobbly contact is still one press, and every change goes to Home
   Assistant at once (ESPHome's default 100 ms batching is off). Bench results and the reasons are
   in [`firmware/bell/`](../firmware/bell/).
3. It sends the ring event **first**, over the cable, to Home Assistant, which pushes a
   high-priority notification to the phone (target: under 1 second, not yet measured).
4. Only then does the door give local feedback: the light flashes, the screen changes.
   Nothing on the ring path waits for the screen, the talk computer or WiFi.

## Power

| Stage | Detail |
|---|---|
| Switch port | PoE on, switch on a UPS so a short power cut does not stop the bell |
| Surge protector | Ubiquiti ETH-SP-G2 before the outdoor cable; only works when earthed (electrician's job) |
| Splitter | industrial, rated down to -40 °C; output **12 V or 5 V still undecided** |
| 12 → 5 V | Pololu D30V30F5 step-down (only with a 12 V splitter) |
| 5 V rail | lever clamps feed all three computers, the amplifier, the level shifter and the LED strip |
| 3.3 V | made on the doorbell and talk computers for the sensor, the button pull-up and the microphone |
| Heater | about 5 W pad behind the display, through a 73 °C one-shot thermal fuse, switched low-side by an opto-coupled MOSFET module |

**Budget.** The surge protector's datasheet lists 802.3af, which allows 12.95 W at the device.
A ring plus a call with the heater on comes to roughly 12.1 W (an estimate, not measured), so the
doorbell computer runs a **governor**: heater off during calls and for 5 minutes after a press,
LED brightness capped while it heats.

## Winter

The e-paper panel is rated 0 to +50 °C; the box sees frost. A BME280 in the box reads
temperature and humidity. The heater **fails cold**: off at boot, off if the sensor fails,
firmware cut-off around 40 °C, and the thermal fuse as the last line of defence. Below about
+2 °C the screen does not refresh.

## Two-way talk (chosen, not yet proven)

- Software: the community [VoIP Stack for ESPHome](https://github.com/n-IA-hane/esphome-intercom)
  with its Home Assistant integration (via HACS). Home Assistant acts as the SIP router and
  hands the call to the phone.
- Flow: ring → Home Assistant starts a call to the talk computer → the phone gets a notification
  with a talk button → tapping it answers. Receiving the notification never opens a microphone.
- Audio: INMP441 MEMS microphone, MAX98357A I²S amplifier at its lowest gain (100 kΩ from GAIN to
  Vin), VISATON K 40 SQ speaker (82 dB at 1 W / 1 m, rated 0.5 W).
- If the echo cannot be tuned out: walkie-talkie mode with the stack's mute switches.
- **Security:** the stack's SIP endpoint has no authentication or encryption. The door devices
  belong in their own VLAN with a firewall that only lets Home Assistant reach them, and
  auto-answer stays locked off.
- **Privacy:** the microphone only opens after a visitor presses something, it is announced on the
  screen and by the LED colour, nothing is recorded without that. (In Germany, § 201 StGB makes
  recording the spoken word without consent a criminal offence.)

Not designed yet: push-to-talk into speakers inside the house, and voice messages delivered to
a phone as audio plus a local Whisper transcript.

## Mechanics

- **Front:** one 2 mm brass sheet, 100 × 260 mm, with a folded rain roof and drip edge. It is
  held by four slotted brass countersunk screws (M3, DIN 963). Cut-outs: display window, speaker
  grille (3 rows of slanted slots), 2 × Ø1.2 mm mic holes and the button hole (Ø49.5 mm for a
  Ø48.5 mm ring). The LED band sits in the bend: 2 windows for the strip and 2 slits for the
  diffuser's tabs.
- **Box:** 3D-printed (ASA; PETG on open-frame printers, which warp large ASA parts), set flush
  into 14 cm of facade insulation and fixed into the masonry behind it. Gasket cord in a rim groove, pressed by the front. A pressure vent lets it breathe
  into the grille cavity; the grille cavity counts as outside air and has to drain.
- **Cable entry:** a split cable gland (Conta-Clip KDS-KV M25, 25.2 mm hole) with a split
  sealing insert for the 6–7 mm cable, so the ready-made cable with its moulded plug can go
  through.
- **No camera. Ever.** This is a design rule, not an open question.

## Open points

See the "Still open" list in the explorer. In short: splitter voltage, real power draw, pin
assignment on the bench, WiFi signal inside the box, the LED strip type, and a CAD fix (the grille cavity floor slopes the wrong way).
