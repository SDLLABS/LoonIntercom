# P4 and bell single-feed topology — bench design

The architecture requires **two independent wired Ethernet clients** outdoors: the inherited ESP32-S3 bell MCU, which directly rings RoomKeys, and the P4 multimedia MCU. The site offers one CAT6/PoE feed. This document chooses an electrical **reference topology to evaluate**, not a switch/PD/PCB BOM or installed hardware.

```text
Indoor LAN/PSE -- one CAT6 carrying 10/100 Ethernet + negotiated PoE -- outdoor PD
                                                              |
                                               isolated regulated power stage
                                                  |                  |
                                       protected priority S3 rail    switched/fused P4 rail
                                                  |                  |
CAT6 data pairs ------------------------------ 3-port 10/100 switch ---------
                                                   |                    |
                                             wired S3 PHY          wired P4 PHY
                                                   |                    |
                                         supervised button         camera/audio/UI
                                                   |
                                         direct encrypted RoomKey ring
```

The PD must negotiate a suitable IEEE 802.3 PoE class with the indoor PSE. An internal three-port switch gives the one upstream Ethernet link two distinct wired clients; each MCU keeps its own MAC/IP and PHY. The protected S3 rail has first claim on available power. P4 media, amplifier, display and heater loads must be switched/current-limited so their overload or reset cannot collapse the S3 rail. The heater must retain its inherited fail-cold design. Place surge/ESD protection and isolation at the cable/PD boundary, and account for outdoor temperature, leakage and enclosure thermal rise. No PoE class, regulator, switch, fuse or reserve capacity is selected before measuring real loads.

The common CAT6, PSE, PD, switch and upstream LAN remain shared failure points. A switch reset or CAT6 cut can stop direct RoomKey delivery even if the S3 is powered; detection and offline indication are therefore part of acceptance. The switch cannot make the bell physically independent from shared power/network infrastructure. P4 firmware has no role in forwarding S3 traffic, switching S3 power, sensing the supervised button or acknowledging a ring.

## Alternatives to evaluate

| Wired option | Assessment |
| --- | --- |
| Internal Ethernet switch plus one PoE PD and independently protected rails | Baseline for bench evaluation; preserves two normal Ethernet ports and separate processors, but switch/PD are common causes. |
| Two independent outdoor PoE feeds | Stronger power/network separation, but violates the current single-CAT6 site constraint unless cabling changes. Use as a measured reliability comparator, not the assumed installation. |
| Engineered multi-channel Ethernet over one cable with compatible indoor/outdoor couplers | Possible only with explicit cable-pair, PoE and standards analysis; passive pair splitting alone cannot turn one 10/100 port into two clients or provide safe independent PoE. No such coupler is selected. |
| Wi-Fi for the bell | Rejected for this architecture; critical direct RoomKey delivery remains wired. The EV board's C6 radio is irrelevant to the bell link. |

## Bench gates

- Identify the selected P4 PCB/SoC revision and its RJ45, camera, audio, NOR and PSRAM population. The [Function EV v1.5.2 guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32p4/esp32-p4-function-ev-board/user_guide.html) describes USB power, **not an onboard PoE PD**. Use a separately designed/compliant PD and regulated 5 V bench supply for this EV board; never put raw PoE voltage on its USB or 5 V header.
- Measure cold-start inrush, steady and simultaneous peak current for S3 + switch + P4 + camera + speaker + display/heater if fitted. Select PSE/PD class and supply margin only from measurements and worst-case environmental conditions.
- Prove S3 survives P4 rail removal, P4 short/overload, P4 watchdog reset and media load spike; then prove direct RoomKey ring and supervised-line cut/short diagnostics still work. Verify fail-cold heater behavior.
- Characterize switch boot time, brownout, upstream link loss and recovery; log S3 direct-ring availability. Test RoomKey/HA/NVR outages separately.
- Review grounding, isolation, surge/ESD, touch safety, cable ingress, thermal rise and secure routing of indoor-only strike/gate wires. No outdoor relay or unlock conductor may be exposed.

No topology above has been built or tested here. The exact product board, power parts and camera/codec driver revisions remain open.

## Board migration and Waveshare target gate

The Function EV v1.5.2 is an [EOL development board](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32p4/eol/eol-boards.html) used only for software and bench reference. Espressif currently documents the [P4X Function EV](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32p4/esp32-p4x-function-ev-board/user_guide.html) and [P4X-C5 Function EV](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32p4/esp32-p4x-c5-function-ev-board/user_guide.html) as migration/reference options; neither is selected for this product. Their pins, SoC revisions and power paths must be checked independently.

WP2.1 adds a distinct [Waveshare ESP32-P4-ETH SKU 32086 bench profile](waveshare-esp32-p4-eth-32086.md), using its official schematic for Ethernet and audio wiring and separate 32 MB NOR defaults. The exact received **PCB revision and SoC revision** must still be read and matched before flashing. The base board has a PoE module/power header; do not claim integrated PoE or qualify a power path until the fitted module/variant and isolation are identified. Its camera connector does not establish a fitted sensor. Run the linked no-SD, Ethernet, codec, camera and single-CAT6 acceptance steps before considering it validated. The EOL Function-EV profile remains a separate software/bench reference, and product hardware selection remains open. No relay or strike/gate wiring may terminate on either P4 board.
