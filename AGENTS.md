# AGENTS.md

## Purpose

This repository is the SDLLABS fork of `aikos-home/intercom`. The goal is to evolve it into a local-first, appliance-grade video intercom and access-control system while preserving the original project's reliability-first doorbell architecture.

Before substantial work, read `docs/CODEX_HANDOFF.md`. For multi-step or architectural work, create/update an execution plan following `.agent/PLANS.md`.

## Architectural invariants

These are requirements, not suggestions.

1. **No Linux is required on the outdoor unit.** Target ESP32-P4 / ESP-IDF / FreeRTOS for multimedia workloads.
2. **No SD card is required for operation.** Runtime must boot from on-board NOR flash. Removable storage may be optional only.
3. **The doorbell remains independently reliable.** Preserve the Aikos supervised-line bell design and its direct ring path that does not require Home Assistant.
4. **Home Assistant is orchestration, not a critical dependency.** An HA outage must not prevent the physical bell from ringing locally/directly.
5. **Video/audio failure must not disable the bell.**
6. **The outdoor unit never owns physical unlock authority.** Strike/gate relays belong to a trusted indoor controller. The outdoor unit sends authenticated access requests only.
7. **No cloud dependency for core operation.**
8. **Security-sensitive commands require authentication and replay protection.**
9. **Do not weaken existing Aikos safety behaviour**, including cable-cut/short diagnostics, fail-cold heater behaviour, or encrypted direct-ring transport.
10. **Prefer appliance behaviour over writable local state.** Avoid databases and frequent flash writes on the outdoor unit.

## Upstream/reference projects

Use these as references, not repositories to merge wholesale:

- `https://github.com/aikos-home/intercom`
  - supervised bell
  - direct RoomKey ring path
  - e-paper UX
  - PoE/environmental/mechanical design
  - failure isolation

- `https://github.com/exddc/openchime`
  - WebRTC / H.264 / Opus direction
  - duplex audio / AEC requirements
  - MQTT command model
  - signed/replay-resistant control concepts
  - hardware documentation practices

OpenChime is MIT licensed. Preserve all required licence/copyright notices when porting code. Do not import Buildroot/Linux-specific layers unless explicitly requested.

## Target high-level architecture

```text
Outdoor multimedia unit
  ESP32-P4 + PoE/Ethernet
    camera -> hardware H.264/JPEG
    microphone + speaker
    intercom transport
    keypad / UI
    tamper input
    access-request client

Independent bell path
  ESP32-S3 Ethernet/PoE (existing Aikos design)
    supervised physical button
    direct encrypted ring to RoomKeys
    Home Assistant event as secondary/orchestration path

Trusted indoor access controller
  dedicated MCU
    credential policy
    authenticated request verification
    replay protection
    door contact / request-to-exit
    strike/gate relay
    hard maximum relay-on watchdog

Infrastructure
  Home Assistant: orchestration/UI only
  NVR: recording
  optional MQTT/WebRTC/signalling: local network
```

## Repository boundaries

Prefer modular additions and avoid large inherited-code reorganisations without justification.

```text
firmware/
  bell/                  # existing Aikos supervised bell
  screen/                # existing e-paper firmware
  p4/                    # new ESP32-P4 multimedia outdoor unit
  access-controller/     # trusted indoor lock controller

protocol/
  events.md
  access.md
  intercom.md

hardware/
  ... existing Aikos hardware ...
  p4/
  access-controller/
```

## Access-control rules

- PINs must not be stored or logged in plaintext.
- Implement rate limiting and lockout/backoff for keypad attempts.
- Temporary/one-time credentials require bounded validity and usage count.
- Caller ID alone is not a sufficient credential for a main entrance.
- If telephone access is implemented, combine caller identity with a second challenge/factor.
- Never expose relay control directly to the outdoor board.
- Door state should distinguish closed/open and, where supported, held-open/forced-open.
- Tamper events must never cause unlock.
- Unlock requests must have bounded lifetime and replay protection.
- Relay output must have an independent maximum-on watchdog.

## Implementation guidance

- Prefer ESP-IDF components with explicit interfaces over monolithic application code.
- Keep board-specific pins/config separate from product logic.
- Use bounded timeouts and watchdogs for network/media operations.
- Treat network input as untrusted.
- Validate lengths, IDs, enum values, timestamps/counters and authentication before acting.
- Separate configuration-plane functionality from critical runtime.
- Design OTA for recoverability (A/B or equivalent rollback where supported).
- Do not introduce a filesystem dependency for boot-critical behaviour.
- Avoid dynamic allocation in critical paths where practical.

## Tests and validation

For every change, run all checks available for the touched component. Add tests with new protocol/security logic.

When applicable:

- build affected ESP-IDF targets;
- run host-side tests for protocol/parsing/authentication logic;
- prove replayed/expired/malformed access requests are rejected;
- verify multimedia failures cannot suppress bell events;
- document hardware-only validation not executed.

Never claim hardware behaviour was tested unless it was actually tested on hardware.

## Change discipline

- Make focused commits.
- Do not rewrite unrelated inherited Aikos code.
- Keep upstream compatibility where it does not conflict with SDLLABS requirements.
- Identify copied/ported OpenChime code and preserve licences/notices.
- Update documentation with architecture changes.
- Final reports/PR descriptions must list:
  - changes made;
  - tests run;
  - tests not run;
  - known risks;
  - hardware assumptions.
