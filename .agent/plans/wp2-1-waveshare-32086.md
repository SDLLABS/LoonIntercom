# WP2.1 execution plan — Waveshare ESP32-P4-ETH bench profile

## Goal

Add Waveshare ESP32-P4-ETH SKU 32086 as a distinct, evidence-backed bench target while retaining the Espressif Function-EV software reference and the independent wired bell architecture.

## Non-goals

No product board, PoE module, camera sensor, speaker, microphone validation, switch or production power design is selected. No SD/filesystem runtime or access-control path is added.

## Constraints

Apply `AGENTS.md`: ESP-IDF/FreeRTOS and NOR boot only, no mandatory SD or filesystem, no P4 relay authority, no effect on the independent wired S3 bell, and board-specific pins only in BSP profiles. Do not infer chip revision or force-flash mismatched images.

## Current state

`firmware/p4/` has a Function-EV v1.5.2 profile, 16 MB defaults and a small NOR/I2C/Ethernet smoke app. `hardware/p4/README.md` documents a required internal wired switch and separate protected S3/P4 power branches. The Waveshare SKU 32086 documentation and official schematic now provide a real second board's wiring and 32 MB NOR/PSRAM specification. The PCB and silicon revisions of an actual board remain unknown.

## Proposed design

Add a separate `board_support/boards/waveshare_esp32_p4_eth_32086.c` profile and Kconfig selector. Extend only the existing IP101/RMII Ethernet descriptor to carry real RMII data and external REF_CLK pins, and apply them in `net_smoke`. Keep audio, camera-connector and expected-memory metadata in the BSP; no functional audio or video driver is introduced. Provide standalone 32 MB Waveshare defaults and a 32 MB, no-filesystem bench partition table. Keep chip-revision settings in separately selected overlays, after marking/boot-log identification. Pin the documented toolchain release to ESP-IDF v5.5.4.

## Security analysis

The outdoor board, RJ45 and optional PoE attachment are physically untrusted. Board pin metadata confers no unlock authority. The S3 direct ring remains a separate wired client and does not depend on P4 or media startup. A single RJ45 on SKU 32086 cannot serve both MCUs without the unresolved switch/power assembly. SD and writable filesystems are excluded from boot and normal runtime. Revision mismatch must stop flashing; no bypass is accepted.

## Work breakdown

- [x] Read repository guidance, WP2 plan, source and official Waveshare/Espressif evidence.
- [x] Add a distinct Waveshare BSP and minimal RMII configuration correction.
- [x] Add 32 MB build profile and revision-selection instructions.
- [x] Document schematic provenance, acceptance gates and single-CAT6/PoE limits.
- [x] Run available host/static/documentation checks and commit one focused change.

## Validation

Host-compile both board profiles where possible; statically check pin maps, 32 MB partition ranges, no-SD dependencies, profile selection and Markdown links; run `git diff --check`. Build with pinned ESP-IDF v5.5.4 if `idf.py` is present. Hardware-only gates cover NOR/PSRAM and revision detection, link/DHCP/restart, codec I2C/mic/speaker, attached-camera ID/capture/H.264, no-SD boot and single-feed bell isolation.

## Progress

Profile and documentation are complete. Host/static validation passed; the focused commit follows.

## Decisions / discoveries

- Waveshare SKU 32086 is the base Ethernet board; PoE hardware is a separate module/variant gate.
- The official schematic identifies IP101GRI with PHY_AD0 strapped high and PHY_AD3 low; Waveshare's own Ethernet example defaults PHY address to 1. Device confirmation remains required.
- The actual silicon revision is unknown, so Waveshare defaults cannot inherit Function-EV's pre-v3 setting.
- The pinned ESP-IDF v5.5.4 P4 EMAC defaults happen to match these RMII pins, but the smoke path now applies pins and external REF_CLK from each BSP explicitly.
- ESP-IDF v5.5.4 rejects its ROM flash implementation at 32 MB, so the Waveshare defaults disable it.
- ESP-IDF v5.5.4 exposes `esp_psram_get_size()`; smoke diagnostics now report detected PSRAM separately from available heap.

## Final result

Added the SKU 32086 BSP, explicit IP101 RMII configuration, detected-versus-expected 32 MB NOR/PSRAM diagnostics, audio/CSI metadata, standalone 32 MB defaults and partition table, revision overlays, and device acceptance documentation. Retained Function-EV as EOL software/bench reference; production hardware, attached camera, PoE module and silicon revision remain open. GCC compiled both BSP sources with strict warnings; Clang syntax checked both. Static checks passed for both partition tables, profile/revision separation, no SD/filesystem includes, changed Markdown local links and `git diff --check`. CMake selected both profiles and rejected missing Waveshare revision confirmation or 32 MB flash settings as intended. `idf.py --version` returned command not found, so no ESP-IDF target build, flash, hardware Ethernet/audio/camera/PoE test or bell-isolation test was run.
