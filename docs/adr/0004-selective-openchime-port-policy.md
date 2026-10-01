# ADR-0004: Evaluate OpenChime selectively

Status: accepted for architecture v2, 2026-10-01.

## Context

OpenChime `main` at `8085381` has an implemented Pi/Linux Chime service and platform/config code. Its Ring tree is presently a placeholder while the hardware specification describes future WebRTC, Opus, H.264, AEC, signed MQTT commands, and outdoor relays. Those are different maturity levels and trust boundaries.

## Decision

Use OpenChime as a reference for media requirements, bounded service behavior, separation of configuration and runtime, local operation, and hardware documentation. Port an individual algorithm or file only after a P4/ESP-IDF feasibility and license review identifies a concrete need. Do not merge its repository or import Buildroot, Linux init, POSIX process runners, Pi drivers, SD/rootfs configuration, or outdoor relay design. Ring command concepts inform WP4 threat analysis; the indoor controller protocol is designed and verified independently.

For every future copied/adapted file, record source path and commit, modification, copyright holder and license; preserve the OpenChime MIT notice and audit embedded third-party material. No OpenChime code is copied by WP1.

## Consequences

WP3 must verify media libraries and resource budgets on actual target hardware. WP4 cannot claim OpenChime has a finished signed/replay-resistant Ring protocol. A source-level port should be a small reviewable commit with host/target tests and provenance updates to `docs/upstream-map.md`.

## Rejected alternatives

Wholesale merge would import Linux-specific assumptions and an outdoor relay authority that conflict with the SDLLABS architecture.
