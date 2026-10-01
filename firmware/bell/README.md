# Doorbell computer firmware

Stock ESPHome (tested with 2026.9.0, ESP-IDF). The doorbell computer does one job: read the brass button
over a supervised line and report every press to Home Assistant, at once. Nothing else runs on it, so
a crash or an update elsewhere can never silence the bell.

| File | What it is |
|---|---|
| [`bell-core.yaml`](bell-core.yaml) | The bell logic, the same on every board: line sampling, press detection, line supervision, diagnostics |
| [`s3poeeth-intercom-bell.yaml`](s3poeeth-intercom-bell.yaml) | **The doorbell computer:** Waveshare ESP32-S3-ETH (W5500 Ethernet, PoE via its plug-on module) |
| [`wt32eth-intercom-bell.yaml`](wt32eth-intercom-bell.yaml) | The first try on a WT32-ETH01, kept for the record: see *Why not the WT32-ETH01* below |
| [`secrets.example.yaml`](secrets.example.yaml) | Copy to `secrets.yaml` (never commit it) and fill in your own keys |

Build and flash once over USB-C, after that over the network:

```bash
esphome run s3poeeth-intercom-bell.yaml
```

## Direct ring path

Every press goes to Home Assistant **and**, at the same time, straight to the room keys over encrypted UDP (ESPHome
`packet_transport`, port 18511, unicast to each key's address, rolling code against replays), so the gong still
sounds while Home Assistant restarts. Each packet carries `boot_id` (24-bit random per boot; `packet_transport`
sends values as 32-bit floats, so larger integers would arrive rounded), `presses` (press number since boot) and
`ringing` (on while the button is held, off on release or after the adjustable maximum duration: holding rings one
continuous gong, like a school bell). A key rings once per new `(boot_id, presses)`, whichever path delivers it first.

## The supervised line

```
3V3 ── 10 kΩ ──┬── IO1 (ADC1)          at the button, at the far end of the cable:
               ├── 100 nF ── GND
               └── 1 kΩ ── cable ────┬──────────┐
                                     │  button   10 kΩ (end-of-line)
               GND ─── cable ────────┴──────────┘
```

The end-of-line resistor turns "nobody rings" and "cable cut" into two different voltages. Measured on
the bench (the ESP's internal pull-up is switched on too, see below):

| Line | Volts at the pin | Entity |
|---|---|---|
| idle | 2.03 | all clear |
| pressed | 0.34–0.47 (firm), 0.6–0.9 (half-closed contact) | *Doorbell button* on, one *Doorbell* event |
| cable cut | 3.18 | *Line cut* after 10 s |
| shorted | 0.0 | one press, then *Line shorted* after 60 s |

Keep `line_installed: "false"` until the line is wired: a floating ADC pin rings by itself.

## What the bench taught us

Each of these cost presses before it was fixed:

- **ESPHome batches API updates for 100 ms by default.** A fast on/off pair inside one batch reaches
  Home Assistant only as its last state, so storm ringing showed 2 of 5 presses. `api: batch_delay: 0ms`
  sends every change at once, and saves up to 100 ms of delay.
- **A loose signal wire looked like a held press.** A floating ESP32-S3 ADC pin reads about 0.1 V. The
  chip's internal pull-up is switched on after the ADC is set up (the ADC driver resets the pad), so a
  loose wire now reads as a cut cable.
- **A half-closed brass contact hovers between 0.6 and 0.9 V** and was counted twice. Hysteresis: a
  press starts below 1.30 V and ends only above 1.60 V.
- **A median filter hid very short contacts.** It is gone; the 100 nF on the line smooths enough. The
  line is sampled every millisecond (diagnostic *Line samples per second*, about 980).

Result on the bench: 10 of 10 slow presses; filmed storm ringing at about 5.7 presses per second, 14 of
15 counted, and the 15th only grazed the contact for 1 ms. Every counted press reached Home Assistant
exactly once. Grazes are deliberately not counted: that would make the line sensitive to noise on a
long outdoor cable.

## Why not the WT32-ETH01

The WT32-ETH01 was the first choice and was dropped. Its IO0 is both the boot-mode strapping pin and
the input for the 50 MHz Ethernet clock. On this unit the oscillator holds IO0 low while it is off, so
after one lucky start the chip always booted into download mode (`boot:0x3`), with or without a
network cable. Pull-ups of 10 kΩ and even 1 kΩ from IO0 to 3V3 did not win. A doorbell must come back
on its own after a power cut, so the board is unfit for this job. Others report the same symptom; if
your WT32 hangs at boot, the scripts in [`tools/wt32/`](../../tools/wt32/) show what IO0 does without
unplugging anything.
