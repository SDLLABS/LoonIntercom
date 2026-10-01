# WP1 execution plan — architecture and upstream map

## Goal

Publish a reviewable v2 system architecture, current upstream provenance map, module boundaries, and four decisions that preserve direct bell operation and place all unlock authority indoors.

## Non-goals

No functional firmware, protocol implementation, hardware selection, OpenChime merge, or claims of hardware validation.

## Constraints

Apply all invariants in `AGENTS.md`: ESP32-P4/ESP-IDF without required Linux or SD; independent supervised bell and direct encrypted RoomKey path; HA/cloud/media outside the bell critical path; indoor-only relays; authenticated replay-resistant control; fail-cold heater; bounded outdoor writable state.

## Current state

Local `codex/architecture-v2` is `3e56b7d`, based on Aikos `77b56da`; `main` of both Aikos and SDLLABS is `77b56da` (checked 2026-10-01). Existing `firmware/bell/` contains supervised-line logic and direct encrypted UDP RoomKey delivery; `firmware/screen/` contains the e-paper driver. `docs/architecture.md` and the inherited roadmap describe the camera-free Aikos baseline, while `docs/ARCHITECTURE_V2_DRAFT.md` is a handoff sketch. OpenChime `main` is `8085381` (checked 2026-10-01): Chime runtime exists; Ring media/control is largely specified in `hardware/ring/` and `ring/README.md` is a placeholder.

## Proposed design

Document three device owners: bell MCU for physical rings, outdoor P4 for media/UI/request creation, indoor MCU for policy and actuators. Specify protocol and hardware module boundaries, trust/data flows, local service dependencies, and failure behavior. Record each binding decision as an ADR.

## Security analysis

Treat the front plate and LAN as untrusted. The indoor MCU verifies source authentication, request freshness/replay state, credentials/policy, and rate limits before energizing a relay through a bounded timer and independent maximum-on cutoff. P4, HA, MQTT, and NVR cannot directly actuate outputs. PIN values never appear in plaintext storage or logs. Exact crypto/encoding and provisioning remain WP4 design work.

## Work breakdown

- [x] Read repository instructions, handoff, WP1 brief, and inherited implementation/docs.
- [x] Inspect current SDLLABS, Aikos, and OpenChime heads and distinguish implemented features from plans.
- [x] Publish `docs/architecture-v2.md` and `docs/upstream-map.md` with proposed module boundaries.
- [x] Publish four ADRs under `docs/adr/`.
- [x] Validate links, decisions, acceptance invariants, and git diff; update this plan.

## Validation

Run `git diff --check`, a local documentation/link/invariant review, and `git status --short`. No firmware build or hardware validation is applicable to documentation-only WP1.

## Progress

WP1 documentation complete. Relative links and whitespace checked; source/implementation status reviewed against the pinned upstream commits.

## Decisions / discoveries

- The bell's `packet_transport` direct path already exists; older `docs/architecture.md` has an HA-first description and a no-camera rule that describe the inherited design, not v2.
- OpenChime Ring's WebRTC/Opus/H.264 and signed commands are requirements in the hardware variant specification; current `ring/` has no implementation to port.
- Shared PoE power and LAN/switch infrastructure remain possible common-cause failures despite separate processors.

## Final result

Created v2 architecture, provenance map, module structure, four ADRs and follow-up work packages. No functional firmware or OpenChime source was added. Validation: local documentation link/whitespace check and `git diff --check`; hardware and ESP-IDF builds were not run because this is documentation-only work. Remaining risks are target-board/media feasibility, shared PoE/LAN/RoomKey failure, controller hardware/cutoff/egress qualification and exact access cryptography/provisioning.

## WP1.1 architecture hardening — 2026-10-01

### Goal and scope

Clarify outdoor PIN exposure, the single-CAT6 wired topology, and the distinction between documented P4 H.264 silicon capability and board/stream feasibility. Documentation only; no keypad hardware selection or firmware.

### Work and decisions

- [x] Re-read `AGENTS.md`, handoff, architecture, provenance map and ADRs 0001–0004.
- [x] Verify H.264 Baseline 1080p30, MIPI-CSI and ISP against the Espressif ESP32-P4 datasheet.
- [x] Document P4-connected convenience credentials versus a dedicated direct indoor keypad path; indoor verification does not hide a PIN entered through P4.
- [x] Require WP2 to resolve two wired Ethernet devices and power behind one outdoor CAT6/PoE feed without moving the bell to Wi-Fi.
- [x] Assign board/camera/PoE/PSRAM/NOR/audio validation to WP2 and end-to-end media/latency/resource work to WP3.
- [x] Run documentation/link and `git diff --check` checks; commit the focused result.

### Validation and remaining risks

Relative Markdown links and whitespace passed (seven documents, nine relative links); `git diff --check` passed. No firmware build or hardware test applies. The selected board, Ethernet switch/power distribution, sensor/driver and keypad assurance hardware remain open; shared network/power failures still need bench tests.
