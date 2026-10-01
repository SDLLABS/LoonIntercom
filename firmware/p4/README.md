# ESP32-P4 bench bring-up

This ESP-IDF project retains the **Espressif ESP32-P4-Function-EV-Board hardware v1.5.2** as its default software/bench reference. It is [EOL](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32p4/eol/eol-boards.html), not a selected production board. The [board guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32p4/esp32-p4-function-ev-board/user_guide.html) and [schematic](https://dl.espressif.com/dl/schematics/esp32-p4-function-ev-board-schematics_v1.52.pdf) document 16 MB SPI NOR, IP101GRI RMII, ES8311, NS4150B and an optional MIPI-CSI camera accessory. Its [example camera module data sheet](https://dl.espressif.com/dl/schematics/camera_datasheet.pdf) labels AS-AG638A32M2-50, while [Espressif's SC2336 component](https://github.com/espressif/esp-video-components/blob/master/esp_cam_sensor/sensors/sc2336/include/sc2336.h) is only a driver lead until the delivered accessory is identified. The actual EV PSRAM and fitted camera require bench identification.

WP2.1 adds a separate **Waveshare ESP32-P4-ETH, SKU 32086** bench BSP. The [official Waveshare documentation and schematic evidence](../../hardware/p4/waveshare-esp32-p4-eth-32086.md) establish its 32 MB NOR, 32 MB stacked PSRAM, IP101GRI RMII, ES8311 audio and two-lane CSI connector. No production board, camera sensor, PoE module or silicon revision is selected. The physical microSD slot is unused on both profiles.

## Build and run

Use the pinned [ESP-IDF v5.5.4 release](https://github.com/espressif/esp-idf/releases/tag/v5.5.4) for reproducible WP2.1 builds. Waveshare's [FAQ](https://docs.waveshare.com/ESP32-P4-ETH/FAQ) recommends v5.5.1–v5.5.4. In an initialized ESP-IDF shell, the existing Function-EV default remains:

```sh
cd firmware/p4
idf.py set-target esp32p4
idf.py build
idf.py -p PORT flash monitor
```

For **Waveshare SKU 32086**, first read the fitted chip marking or serial boot log. Select exactly one revision overlay from `sdkconfig.revision.pre_v3.defaults`, `sdkconfig.revision.v3_0.defaults` or `sdkconfig.revision.v3_1.defaults` that matches that silicon. In a fresh build directory with no stale generated `sdkconfig`, replace `CHOSEN_REVISION_OVERLAY` below with the verified filename:

```sh
cd firmware/p4
idf.py -D "SDKCONFIG_DEFAULTS=sdkconfig.defaults.waveshare_32086;CHOSEN_REVISION_OVERLAY" set-target esp32p4 build
idf.py -p PORT flash monitor
```

The Waveshare BSP refuses a build without a recorded revision choice and the 32 MB flash setting. A mismatched chip revision needs a corrected overlay and rebuild; **never use `--force`**. Do not reuse a generated `sdkconfig` or binary across boards or revisions. This instruction is a future bench procedure; no target build or flash has run in this workspace.

The Function-EV `partitions.csv` uses 16 MB NOR with two 4 MB OTA application slots. The separate Waveshare `partitions_waveshare_32mb.csv` is a **32 MB bench layout** with two 8 MB OTA slots and no filesystem partition. Both boot from NOR and require neither SD nor a writable filesystem. OTA verification, signed updates, rollback and production key provisioning are future work; two slots alone do not establish recoverable updates. The current app uses neither NVS writes nor network credentials.

Serial output reports detected NOR and PSRAM capacities, warns on mismatches with the selected board profile, and separately reports ESP-IDF available PSRAM heap bytes. The selected BSP supplies I2C probes: Function-EV checks ES8311 and a *possible* SC2336, while Waveshare checks **ES8311 only**, since no camera module is assumed. Wired IP101 link-up and a DHCP address are reported asynchronously. **An I2C ACK is neither sensor identification nor proof of camera capture or audio input/output.** No Wi-Fi fallback is configured. No relay, unlock, access credential, media transport, cloud or Home Assistant logic is present.

## Board/BSP boundary and smoke scope

`components/board_support/include/board_support.h` defines the board-neutral configuration consumed by the app and smoke components. `boards/function_ev_v152.c` and `boards/waveshare_esp32_p4_eth_32086.c` own their respective memory expectations, IP101 RMII pin maps, I2C probes and peripheral metadata. `Kconfig.projbuild` selects exactly one profile; `sdkconfig.defaults` retains the EOL Function-EV default, while `sdkconfig.defaults.waveshare_32086` is standalone and does **not** inherit its 16 MB or pre-v3 assumptions. The application and Ethernet/I2C smoke code contain no board GPIO literals. The network path uses the pinned [ESP-IDF v5.5.4 EMAC configuration API](https://docs.espressif.com/projects/esp-idf/en/v5.5.4/esp32p4/api-reference/network/esp_eth.html) with BSP-supplied RMII data pins and external REF_CLK. Both supported profiles use IP101; no speculative PHY factory is added. The I2C smoke component performs bounded 100 ms address probes, which show ACK only, not codec initialization or sensor identification.

The default `sdkconfig.defaults` includes the historical Function-EV pre-v3 setting. Waveshare's profile contains **no** silicon revision choice: the actual board must identify it first. The per-revision overlays only record an operator's verified choice. The present board profile documents connector and audio pins for later work; it does not add audio or video functionality. Product hardware selection remains open.

## Device acceptance gates still required

1. Read actual PCB and SoC revisions, fitted camera sensor/adapter and NOR/PSRAM capacity. Boot with no SD card, interrupt power repeatedly, and confirm boot from NOR. Use the matching revision overlay, never a forced revision-mismatch flash.
2. Build and flash with pinned v5.5.4, then demonstrate wired link and DHCP on direct LAN and through the single-CAT6 switch/PoE assembly. Check both P4 and independent S3 have distinct MAC/IP addresses and remain wired. Cycle Ethernet stop/start repeatedly with a bench harness if the fitted revision supports it.
3. Use a pinned Espressif video component release to identify the camera, capture frames, exercise JPEG and H.264 hardware encoding, and record format, throughput, frame loss and memory. The SoC's documented Baseline H.264 1080p30 rating is not a board result.
4. Initialize ES8311/I2S; capture actual microphone samples and play a measured speaker tone. Measure PA load and acoustic behavior. I2C ACK alone is insufficient.
5. Qualify a **separately fitted** PoE module/variant and measure its input plus every regulated rail during cold start, camera/encoder, speaker peaks and heater worst case. SKU 32086 has a PoE module/power header; its base-board Ethernet test is separate from PoE qualification. Reset/overload the P4 branch and prove the S3 direct RoomKey ring still works. Repeat with HA and NVR down.
6. Test partition/OTA rollback on the selected NOR and board; choose secure boot/signing and wear policy before a deployed image.

The [Waveshare acceptance record](../../hardware/p4/waveshare-esp32-p4-eth-32086.md) has the full pin evidence and device steps. The [single-feed network and power design](../../hardware/p4/README.md) remains open. WP3 owns RTSP/WebRTC, Opus/AEC, interactive latency and end-to-end resource budgets.

## Current validation status

The files are source-only until built with ESP-IDF and run on hardware. This workspace had no `idf.py`, RISC-V ESP toolchain, board or PoE assembly at authoring time. The listed device gates are **not yet passed**.
