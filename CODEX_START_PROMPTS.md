# Codex Start Prompts

Use one prompt per work package. Start with WP1.

## WP1 — Architecture

Read `/AGENTS.md`, `/docs/CODEX_HANDOFF.md` and `/.agent/PLANS.md`.

Inspect the current `SDLLABS/intercom` repository plus the current upstream repositories `aikos-home/intercom` and `exddc/openchime`. Do not merge OpenChime into this repository.

Create an execution plan and complete WP1 from `docs/CODEX_HANDOFF.md`: produce the v2 architecture, upstream feature/provenance map, proposed module boundaries and architecture decision records. Preserve the existing bell reliability model. The outdoor unit must not control the lock relay.

Do not implement functional firmware in this task. End with exact follow-up tasks suitable for parallel agents.

## WP2 — ESP32-P4 bring-up

Read all repository agent instructions and the completed WP1 architecture/ADRs.

Create an execution plan for ESP32-P4 bring-up. Build a minimal ESP-IDF target under `firmware/p4/` that can become the multimedia outdoor unit.

Priorities:
1. reproducible build;
2. Ethernet;
3. camera discovery/capture;
4. hardware JPEG/H.264 capability;
5. microphone input;
6. speaker output;
7. operation without SD card.

Separate code that can be tested in CI from hardware-only tests. Never claim hardware verification unless it was actually performed.

## WP3 — Media feasibility

Read the architecture and P4 bring-up results.

Investigate a local-first media stack for:
- H.264 video to NVR;
- interactive browser/phone viewing;
- two-way audio;
- Opus where useful;
- acoustic echo cancellation.

Compare RTSP and WebRTC roles rather than assuming only one protocol.

Deliver a technical decision with CPU/RAM/latency/dependency implications and a minimal prototype only if the chosen libraries are credible on the target.

Do not touch bell semantics or lock control.

## WP4 — Access-control protocol

Read the architecture, threat model and `/AGENTS.md`.

Design and implement the trusted indoor access-control protocol and skeleton.

Requirements:
- no outdoor relay authority;
- authenticated messages;
- replay resistance;
- request expiry/bounded lifetime;
- strict parsing;
- rate limiting;
- safe relay defaults;
- hard relay-on timeout;
- tests for malformed, replayed and expired messages;
- no plaintext PIN storage/logging.

Caller ID must never be treated as a sole main-door credential.

## WP5 — Integration/QA

Review the outputs of WP1–WP4.

Build the integration/failure matrix, CI/build guidance, security checklist and HA/NVR/RoomKey integration documentation.

Specifically test or document:
- HA unavailable;
- NVR unavailable;
- P4 unavailable;
- camera unavailable;
- access controller unavailable;
- Internet unavailable;
- SD card absent.

The bell must retain its direct independent path.
