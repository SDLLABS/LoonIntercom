# ADR-0003: Preserve the independent supervised bell

Status: accepted for architecture v2, 2026-10-01.

## Context

The inherited Aikos ESP32-S3 bell senses a supervised analogue line, reports cut/short conditions, and sends encrypted direct ring packets to RoomKeys. P4 media, HA and NVR add complexity and failure modes.

## Decision

Keep the existing bell MCU and `firmware/bell/` as an independently updated critical subsystem. The button-to-direct-RoomKey path contains no synchronous P4, screen, media, HA, NVR, broker or access-controller step. Preserve hysteresis, diagnostics, duplicate identity, encrypted `packet_transport`, rolling code, ring cap, and HA-independent network behavior. HA receives a secondary event; media and UI may observe a ring but cannot acknowledge or gate it. Any future heater implementation must fail cold as specified in the inherited architecture; review shared power loads before P4 integration.

## Consequences

Later changes require regression checks for press detection, line cut/short, direct delivery with HA down, and media crash isolation. The target has one outdoor CAT6/PoE feed but both bell and P4 require wired Ethernet. WP2 must resolve coexistence with an internal Ethernet switch and power distribution or an equivalent wired topology; it must not silently move the bell to Wi-Fi. Separate processors do not eliminate shared PoE/switch/cable/RoomKey failures. Hardware design must prioritize bell power, provide offline diagnostics, and characterize the common-cause cases. A bell MCU crash still loses physical button sensing; it must be reported rather than concealed.

## Rejected alternatives

Moving the button to the P4, routing rings only through HA/MQTT, or waiting for media/UI before direct send would break the failure-domain contract.
