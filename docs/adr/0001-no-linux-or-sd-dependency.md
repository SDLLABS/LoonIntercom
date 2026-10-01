# ADR-0001: Outdoor runtime needs neither Linux nor SD

Status: accepted for architecture v2, 2026-10-01.

## Context

The multimedia outdoor unit needs camera, codec, audio and networking, but is exposed to abrupt power loss and must boot as an appliance. OpenChime's current Chime uses a Buildroot Linux image and SD-backed A/B root filesystems. SDLLABS has selected an ESP32-P4/ESP-IDF/FreeRTOS direction; its exact board and media capability still need proof.

## Decision

Use ESP32-P4 firmware booting from on-board NOR flash. Core operation, including media startup, configuration needed to run, and recovery, has no Linux, SD card, writable system filesystem, database, or cloud prerequisite. Optional removable storage may hold noncritical data only. Separate bounded configuration from runtime; design signed/verified updates and recoverable A/B or equivalent rollback supported by the chosen flash layout. Bell and indoor controller update independently.

## Consequences

The [Espressif ESP32-P4 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-p4_datasheet_en.pdf) establishes a Baseline H.264 encoder with up to 1080p30 YUV420 performance, MIPI-CSI and ISP on the SoC. WP2 must still choose and validate the actual board, camera sensor/driver, Ethernet/PoE, PSRAM/NOR, audio and flash partition layout, and demonstrate capture/encode without SD. WP3 owns end-to-end streaming, RTSP/WebRTC, Opus/AEC, latency and resource budgets; Linux libraries or Pi drivers cannot be assumed portable. NOR writes need wear bounds. Failed updates must return to known-good firmware. Exact secure-boot, flash encryption and signing choices require board-specific design and validation.

## Rejected alternatives

Pi/Buildroot as the required outdoor computer, and SD-backed boot/rootfs, violate the appliance constraint. A removable card remains acceptable solely for optional noncritical recording/export.
