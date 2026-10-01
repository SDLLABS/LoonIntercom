# WP2 execution plan — P4 bench bring-up

## Goal

Establish a small ESP-IDF P4 bench project, record an exact development-board candidate and one-CAT6/two-wired-device topology, and make each hardware proof gate explicit.

## Non-goals

No product PCB or production board selection, selected keypad, access authority, intercom transport, OpenChime import, or claim of camera/audio/PoE operation without physical measurements.

## Constraints

The P4 boots from NOR without Linux, SD or a boot-critical filesystem. Bell sensing and direct RoomKey delivery stay on the independent wired S3; P4 code has no relay output. Video/audio failure cannot suppress the bell. Indoor controller alone owns access authority. Network operations have bounded startup/reporting, and P4 flash writes remain limited.

## Current state

The inherited repository has `firmware/bell/` and `firmware/screen/`, but no `firmware/p4/` or `hardware/p4/`. Architecture v2 and ADR-0003 require both bell and P4 Ethernet behind one outdoor CAT6/PoE feed. Espressif's Function EV Board v1.5.2 guide/schematic documents a 16 MB SPI flash, IP101GRI RMII/RJ45, ES8311 codec and NS4150B speaker amplifier, plus an optional two-megapixel MIPI camera. The EV board is USB-powered and is a bench candidate, not the product board or a PoE board. Espressif's video examples identify the SC2336 camera driver; the actual accessory revision must be checked on receipt.

## Proposed design

Use a board-neutral `board_support` interface and keep Function EV v1.5.2 pin/PHY/I2C values in its own BSP profile. A future Waveshare Ethernet/PoE target gets a separate profile after its exact SKU/revision and schematic are known. A tiny app prints NOR/PSRAM capacity, probes the shared audio/camera I2C bus for ACK only, and starts the wired IP101 link/DHCP smoke path for the bench profile. Probes report their limited meaning; no camera frame, H.264, microphone capture, or speaker playback is claimed. The single-CAT6 reference topology is one standards-compliant indoor PoE PSE, outdoor PD/isolated DC conversion, a three-port 10/100 Ethernet switch, and independent protected bell/P4 branches. Bell supply is prioritized; P4 load shedding cannot reset the S3. The Ethernet switch and feed remain common-cause dependencies. Product parts and ratings remain unselected until measured.

## Security analysis

The outdoor board, switch and cable are physically exposed. The P4 firmware creates no actuator path and holds no credential logic. Link/DHCP events are diagnostic only. Neither a VLAN nor the switch authenticates access requests. Physical tamper, cable shorts and P4 compromise cannot directly energize indoor relays. A shared switch or PoE failure can still suppress remote RoomKey delivery and must be tested.

## Work breakdown

- [x] Read repository guidance and v2 decisions; inspect official board and ESP-IDF evidence.
- [x] Define development-board target, flash layout and no-SD boot path.
- [x] Keep board-specific pins/peripherals behind a selectable BSP; document Waveshare target information gate.
- [x] Add bounded, accurately named bring-up probes for boot memory, I2C presence and wired Ethernet.
- [x] Document one-CAT6 wiring/power choices and bench acceptance tests.
- [ ] Build with pinned ESP-IDF and flash actual board; measure camera/audio/PoE paths.

## Validation

Run `idf.py set-target esp32p4 build` with ESP-IDF release/v5.5 when available; inspect partition CSV and relative documentation links; run `git diff --check`. On hardware, test NOR boot without SD; Ethernet link/DHCP with P4 and bell on the same switch; SC2336 camera ID/frame/JPEG/H.264; ES8311 input/output; PoE cold start, brownout, load shedding and bell direct ring while P4 is reset. A host build cannot prove those paths.

## Progress

Source and topology drafted. Local ESP-IDF/toolchain search found no `idf.py` under `/home`, `/usr/local` or `/tmp`, and no RISC-V toolchain on PATH. Hardware is not attached. The build and device acceptance gates remain open.

## Decisions / discoveries

- Function EV Board v1.5.2 is an evidence-backed software/bench reference; it has no onboard PoE input and is not the product-board selection.
- Espressif's current dev-kit index lists this board under EOL. Check procurement or qualify a newer P4X revision before product-board selection; do not assume pin/IDF compatibility.
- Its microSD slot is optional and unused. A card-free project avoids SD/filesystem dependencies entirely.
- I2C ACK establishes bus presence only. It cannot validate camera capture or audio samples.
- A passive Ethernet splitter does not create two independent Ethernet ports. A switch or separately engineered wired channel is required.
- A Waveshare Ethernet/PoE profile cannot be populated until exact SKU/revision, PHY/PoE design and peripheral wiring are identified.

## Final result

Added an ESP-IDF source skeleton with a selectable BSP, memory/revision diagnostics, wired IP101 link/DHCP startup and bounded I2C ACK probes; documented the separate protected bell/P4 rail and internal switch reference topology. Function EV v1.5.2 remains an EOL software/bench reference; production board selection is open, and Waveshare needs exact SKU/revision data. Static validation checked 20 WP2 files, two local Markdown links, 16 MiB partition alignment/ranges and non-overlap, and compiled the board profile with the host C compiler. `git diff --check` passed after staging. `idf.py --version` failed with command not found; no ESP-IDF target build or flash was possible here. No board, camera/audio device, PoE assembly or bell/RoomKey hardware was available, so no hardware behavior was tested. An I2C ACK remains only a presence probe, not camera/audio bring-up proof.

The subsequent [WP2.1 Waveshare SKU 32086 plan](wp2-1-waveshare-32086.md) adds a distinct 32 MB bench profile from Waveshare's official schematic. The Function-EV-only status and future Waveshare gate above describe the original WP2 result at `ac7a38e`; product board, PoE and silicon-revision selection remain open.
