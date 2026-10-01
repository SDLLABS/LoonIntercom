# Codex Handoff — SDLLABS Intercom

## 1. Mission

Evolve `SDLLABS/intercom` from a clean fork of `aikos-home/intercom` into a local-first video intercom and access-control platform.

The project should combine:

- Aikos' reliability-first supervised doorbell, RoomKey direct-ring path, e-paper and environmental/mechanical work;
- selected OpenChime multimedia and security concepts;
- ESP32-P4 hardware for video/audio instead of a Raspberry Pi/Linux outdoor computer;
- a separate trusted indoor access controller for all physical unlock outputs.

The desired product is an appliance, not a small general-purpose computer.

## 2. Baseline

Repository:
`https://github.com/SDLLABS/intercom`

Forked from:
`https://github.com/aikos-home/intercom`

Baseline at handoff preparation:
- default branch: `main`
- fork was still effectively aligned with Aikos upstream
- latest observed inherited commit: `77b56da677b08da73ba137dddba78e8834585f59`

Reference project:
`https://github.com/exddc/openchime`

Do not assume these repositories remain unchanged. Inspect current state before coding.

## 3. Why this fork exists

Aikos has excellent reliability properties but intentionally excludes cameras.

OpenChime covers a broader smart-doorbell product, including camera, audio, WebRTC direction, relay control and security concepts, but its rewrite targets Raspberry Pi Zero hardware and a minimal Buildroot Linux image.

SDLLABS wants a different convergence:

```text
Aikos reliability
       +
OpenChime multimedia/security lessons
       +
ESP32-P4 hardware multimedia
       +
independent indoor access controller
       =
SDLLABS Intercom
```

## 4. Core product principles

### 4.1 Outdoor unit is firmware-first

Target:
- ESP32-P4
- ESP-IDF / FreeRTOS
- on-board NOR flash
- no Linux requirement
- no SD-card requirement
- no writable system filesystem requirement

The outdoor device should be capable of clean recovery after abrupt power loss without filesystem repair.

### 4.2 Bell path remains independent

The Aikos bell computer and supervised line are valuable and should remain a separate failure domain.

A crash in:
- camera,
- H.264 pipeline,
- audio,
- WebRTC,
- P4 UI,
- NVR,
- Home Assistant

must not suppress a physical ring.

Retain the direct encrypted RoomKey path when practical.

### 4.3 Unlock authority is indoors

Do NOT copy OpenChime's relay-at-the-outdoor-unit architecture.

The outdoor unit may:
- collect a PIN,
- receive a user action,
- validate input shape,
- create a signed/authenticated access request.

It may NOT directly energise the strike/gate relay.

A trusted indoor MCU:
- validates the authenticated request,
- applies policy,
- enforces replay resistance,
- controls relay timing,
- monitors door state.

This prevents physical access to the front panel from becoming physical access to the unlock relay.

## 5. Target architecture

```text
                         LOCAL NETWORK
                               |
                  +------------+------------+
                  |                         |
             Home Assistant                NVR
             orchestration             record/video
                  |                         |
                  +------------+------------+
                               |
                            Ethernet
                               |
                   +-----------+-----------+
                   | OUTDOOR ESP32-P4      |
                   |                       |
                   | MIPI camera           |
                   | HW H.264/JPEG         |
                   | microphone            |
                   | speaker               |
                   | keypad/UI             |
                   | tamper                |
                   | access-request client |
                   +-----------+-----------+
                               |
                      authenticated request
                               |
                   +-----------v-----------+
                   | INDOOR ACCESS MCU     |
                   |                       |
                   | auth/replay checking  |
                   | access policy         |
                   | door contact          |
                   | request-to-exit       |
                   | relay watchdog        |
                   +-----------+-----------+
                               |
                            strike/gate


Independent critical path:

physical button
      |
supervised line
      |
Aikos bell MCU
      +------ encrypted direct ring ------> RoomKeys
      |
      +------ event -----------------------> Home Assistant
```

## 6. What to reuse from Aikos

Preserve or adapt rather than rewrite:

- supervised analogue button line;
- pressed / cable-cut / short/stuck diagnostics;
- fast sampling and hysteresis approach;
- independent bell computer;
- encrypted direct ring path to RoomKeys;
- Home Assistant as secondary orchestration;
- e-paper screen work;
- environmental sensing;
- heater fail-cold behaviour;
- PoE/surge/environmental design lessons;
- hardware/mechanical documentation practices.

The bell code is considered a safety/reliability subsystem. Avoid unrelated refactors.

## 7. What to learn/port from OpenChime

Investigate selectively:

### Multimedia
- hardware H.264 direction;
- WebRTC architecture;
- Opus audio;
- duplex audio;
- acoustic echo cancellation requirements;
- media restart/failure behaviour.

### Messaging/security
- MQTT topic ideas;
- signed command payload concepts;
- nonce/replay protection;
- authenticated configuration/control;
- local fallback behaviour.

### Engineering practice
- separation of platform/product concerns;
- wiring and BOM documentation;
- failure/reliability runbooks;
- explicit interface contracts.

Do NOT port by default:
- Buildroot;
- Linux init/service management;
- POSIX process runners;
- Raspberry Pi-specific drivers;
- filesystem-dependent configuration infrastructure.

If source code is copied or adapted, preserve required MIT notices and record provenance.

## 8. ESP32-P4 initial scope

The first P4 milestone is not a finished intercom.

Create a minimal board-support and multimedia skeleton that can prove:

1. ESP-IDF project builds reproducibly.
2. Ethernet works.
3. PoE-powered board is stable on bench hardware.
4. Camera is detected and frames can be captured.
5. Hardware JPEG/H.264 path can be exercised.
6. Microphone input works.
7. Speaker output works.
8. All of the above operate without an SD card.

Do not block this milestone on WebRTC, Home Assistant integration or access-control UI.

## 9. Access-control protocol requirements

Create a documented protocol before implementing the relay controller.

Suggested conceptual request:

```text
version
device_id
request_id
credential_class
action
issued_at / monotonic epoch or challenge context
expiry / validity bound
nonce or rolling counter
payload
authentication tag/signature
```

Exact encoding is open to design.

Required properties:
- authenticated source;
- replay resistance;
- bounded request lifetime;
- strict parser;
- constant/bounded memory usage;
- rate limiting;
- audit event without leaking credentials;
- explicit protocol versioning.

### PINs

Do not store raw PIN values.

Prefer a memory-hard/password hash where platform resources allow; otherwise use a defensible keyed verifier design appropriate to the MCU and document the trade-off.

Temporary credentials need:
- not-before;
- expiry;
- usage limit;
- identity/label;
- revocation.

### Telephone / Caller ID

Caller ID alone must not unlock the main entrance.

Telephone access may use caller identity only as one signal, combined with another challenge such as:
- DTMF PIN;
- explicit authenticated confirmation;
- another possession factor.

Do not design security around the assumption that caller ID cannot be spoofed.

## 10. Multimedia direction

Desired end-state:

```text
camera -> ESP32-P4 ISP -> H.264 -> intercom/NVR transport
mic    -> audio pipeline -> Opus / selected transport
speaker<- decoded remote audio
```

WebRTC is attractive for browser/phone low-latency intercom and should be investigated, not assumed feasible until resource and library evaluation is complete.

RTSP may still be appropriate for NVR ingest.

A final design may use both:
- RTSP or another stable local stream for NVR;
- WebRTC for interactive talk/view.

Separate media transport decisions from bell semantics.

## 11. First five Codex work packages

### WP1 — Architecture and upstream map

Deliver:
- `docs/architecture-v2.md`
- `docs/upstream-map.md`
- proposed directory structure
- ADRs for:
  - no Linux/no SD dependency;
  - indoor-only relay authority;
  - independent bell failure domain;
  - OpenChime selective-port policy.

No functional code.

Acceptance:
- every planned component has a clear owner and trust boundary;
- no unlock path terminates at outdoor GPIO/relay;
- upstream provenance is documented.

### WP2 — ESP32-P4 bring-up

Deliver:
- `firmware/p4/`
- ESP-IDF build skeleton;
- board configuration;
- camera/audio/Ethernet smoke-test components;
- README with exact hardware assumptions.

Acceptance:
- clean build;
- no SD/filesystem requirement;
- hardware tests are clearly separated from tests actually run by Codex.

### WP3 — Intercom media feasibility

Deliver:
- technical spike/report comparing:
  - H.264 streaming to NVR;
  - WebRTC feasibility on target;
  - Opus/AEC options;
  - memory/CPU/network budget;
- smallest viable prototype if dependencies are sufficiently mature.

Acceptance:
- measured or sourced resource assumptions;
- no claim that full duplex works unless verified;
- graceful failure boundaries documented.

### WP4 — Access protocol + indoor controller skeleton

Deliver:
- `protocol/access.md`;
- host-side protocol tests;
- `firmware/access-controller/` skeleton;
- verifier/replay-state abstraction;
- safe relay-state machine with hard timeout.

Acceptance:
- malformed, expired and replayed requests rejected;
- relay defaults safe across boot/reset/error;
- no secrets logged;
- outdoor unit has no direct relay path.

### WP5 — Integration and QA

Deliver:
- CI/build instructions;
- failure matrix;
- security review checklist;
- integration documentation for HA/NVR/RoomKeys.

Acceptance:
- explicit answers for what happens when each component fails;
- bell path retains independence;
- unresolved hardware tests clearly listed.

## 12. Suggested task order

Run WP1 first.

WP2 and WP4 can then proceed in parallel.

WP3 begins once P4 camera/audio capabilities are confirmed enough to make dependency choices.

WP5 follows integration.

Do not start by merging OpenChime source trees.

## 13. Failure matrix to preserve

Desired behaviour:

| Failure | Bell | Video | Talk | PIN/access |
|---|---|---|---|---|
| Home Assistant down | YES via direct path | local stream may remain | transport-dependent | indoor controller should remain policy-dependent |
| NVR down | YES | live stream may remain | YES | YES |
| P4 crash | YES | NO | NO | outdoor keypad unavailable |
| Bell MCU crash | NO; must alert offline | YES | YES | potentially YES |
| Internet down | YES | YES locally | YES locally | YES locally |
| Access controller down | YES | YES | YES | NO unlock |
| Camera failure | YES | NO | audio may remain | YES |
| SD card absent | YES | YES | YES | YES |

Any implementation that violates the last row has moved away from the desired architecture.

## 14. Security threat model — minimum set

Consider at least:

- attacker removes/opens outdoor front panel;
- attacker shorts outdoor wires;
- attacker obtains LAN access to the intercom VLAN;
- replay of captured access packet;
- malformed packet intended to crash parser;
- stolen/guessed PIN;
- brute-force keypad attempts;
- tamper input spoofing;
- power cycle during OTA;
- Home Assistant compromise;
- P4 compromise;
- caller-ID spoofing;
- relay output stuck active.

Document mitigations and remaining risk.

## 15. Coding/PR expectations

For each work package:

1. create or update an execution plan;
2. inspect relevant current repository state;
3. inspect upstream source before assuming behaviour;
4. make focused changes;
5. run tests/builds that are possible;
6. do not fabricate hardware test results;
7. update docs;
8. produce a final summary containing:
   - implementation;
   - files changed;
   - tests run;
   - tests not run;
   - hardware assumptions;
   - risks/follow-ups.

## 16. Definition of success for the overall project

A successful SDLLABS Intercom eventually provides:

- supervised reliable doorbell;
- local direct indoor chime path;
- PoE/Ethernet;
- local video;
- two-way audio;
- e-paper/touch UX where retained;
- keypad credentials;
- optional secure telephone-assisted access;
- trusted indoor strike/gate control;
- NVR integration;
- Home Assistant integration;
- no mandatory cloud;
- no mandatory Linux on the outdoor unit;
- no mandatory SD card;
- recoverable firmware updates;
- documented security and failure behaviour.

Reliability and physical security take precedence over feature count.
