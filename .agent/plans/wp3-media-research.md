# WP3 execution plan — media feasibility research

## Goal

Publish a sourced, neutral technical report that identifies credible P4 media options, preliminary resource and failure questions, and explicit gates for a later implementation decision.

## Non-goals

No functional firmware, prototype, dependency installation, board or media stack selection, OpenChime port, change to bell semantics, access control, or shared architecture/ADR edits.

## Constraints

Apply `AGENTS.md`: outdoor P4 runs ESP-IDF/FreeRTOS from NOR without required Linux, SD, cloud or writable filesystem; bell sensing and encrypted direct RoomKey delivery remain independent of all media; the outdoor unit has no relay authority; media/network input is untrusted, with bounded queues/timeouts; a single outdoor CAT6/PoE feed must retain wired Ethernet for bell and P4.

## Current state

`docs/architecture-v2.md` assigns board/camera/Ethernet/audio validation to WP2 and streaming/RTSP/WebRTC/Opus/AEC/resource evaluation to WP3. `docs/upstream-map.md` shows OpenChime Ring media as specification, not portable implementation. The repository has no `firmware/p4/` media implementation at the start of this research. Official Espressif sources and IETF RFCs are recorded in `docs/media-feasibility-research.md`.

## Proposed design

Research compares RTSP server/push for local NVR ingest, WebRTC for interactive local view/talk, and an optional indoor restreamer without selecting one. Define capture/encode, transport, audio processing and receiver boundaries; frame/resource budgets; and measurement gates. Media failures shed only media, never the bell path or indoor verifier.

## Security analysis

The P4 and outdoor wiring are physically untrusted; LAN and clients are untrusted. Later media code must authenticate viewers/signaling and bound network parsing, session count, queue size and lifetimes. WebRTC SRTP protects media but does not replace signaling authorization. RTSP security depends on selected deployment and endpoint. No media message can actuate indoor relays. Camera/mic privacy and secret-free diagnostics need an explicit session policy. Physical loss of shared PoE/switch/CAT6 remains a common cause for the wired bell and P4.

## Work breakdown

- [x] Read required repository guidance, architecture, upstream map and ADRs.
- [x] Inspect official P4 video, RTSP/WebRTC, audio codec/AEC and protocol sources; distinguish silicon, reference-board and product evidence.
- [x] Calculate transparent provisional memory/network/latency worksheet and mark vendor CPU figures by platform/configuration.
- [x] Document integration, failure and security risks and gates that depend on WP2 hardware and actual endpoints.
- [x] Publish `docs/media-feasibility-research.md` with no implementation commitment.
- [ ] Root agent review and commit with parallel work packages.

## Validation

Check local Markdown links and whitespace for this report and plan; run `git diff --check` for tracked changes and inspect `git status --short`. No build or hardware test applies to research-only work. Follow-up hardware checks are listed in the report and must not be claimed as completed.

## Progress

Research and report complete. Local Markdown links and whitespace checked (two documents, 24 links, no issues); `git diff --check` passed for tracked files. Awaiting root review and commit.

## Decisions / discoveries

- Espressif lists RTSP and WebRTC P4 examples and says video examples are verified on its Function EV board/SC2336; this does not prove the selected product board or combined NVR plus talk path.
- A published RTSP service currently describes a single client in server role, so viewer fan-out is an explicit gate.
- Espressif provides P4 AEC measurements; its cited Opus CPU measurements are on ESP32-S3R8 and must not be treated as P4 measurements.
- 1080p YUV420 frame storage is about 3.11 MB per frame; buffer counts and DMA constraints must be measured on WP2 hardware.

## Final result

Added a research-only report and plan. No firmware, dependencies or prototype. Documentation links and whitespace passed; `git diff --check` passed for tracked files. Untracked WP3 documents were checked by the link/whitespace script. No board/NVR/audio/latency/failure hardware validation was performed. WP2 and endpoint choices remain dependencies for a technical media decision.
