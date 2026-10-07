# WP2.2 execution plan — OV5647 camera capture smoke on Waveshare SKU 32086

## Goal

Ready-to-flash bench firmware that, when an OV5647 module is connected to the Waveshare ESP32-P4-ETH 22-pin MIPI-CSI connector, reads the sensor chip ID, streams 1080p frames through the ISP, reports frame rate and errors, and serves one hardware-encoded JPEG frame over the wired LAN. This is WP2 device gate 3 (capture/JPEG part) prepared in software before the camera arrives.

## Non-goals

No H.264, RTSP, WebRTC, audio, product camera selection, lens/IR-cut decision or enclosure work. No change to the bell, access controller or default bring-up build behaviour. No authentication on the bench HTTP endpoint.

## Constraints

From `AGENTS.md`: ESP-IDF/FreeRTOS, NOR boot, no SD/filesystem; video failure must not disable anything else; board pins only in BSP profiles; bounded timeouts for network/media; treat network input as untrusted; never claim hardware behaviour that was not tested.

## Current state

`firmware/p4/` had BSP profiles, NOR/PSRAM report, an I2C presence probe that created and deleted its own bus, and Ethernet/DHCP smoke. No camera code. The project had never been built: the first ESP-IDF v5.5.4 build exposed two existing defects (board CMake check ran during early expansion; missing `esp_chip_info.h`). Waveshare documents OV5647 compatibility and a camera SCCB shared with ES8311 on I2C GPIO7/GPIO8 (also stated by the `espp/esp32-p4-eth` BSP).

## Proposed design

- `board_support`: `p4_board_i2c_bus()` creates the internal I2C bus once and shares it (probe, camera SCCB, later codec). Camera descriptor gains reset/power-down GPIOs (none on either board) and SCCB speed.
- `camera_smoke` (new, Kconfig `P4_CAMERA_SMOKE`, default off): `esp_video_init` with the shared bus, open `/dev/video0`, read chip ID, request RGB565 from the ISP at the sensor's configured size, stream with 2 MMAP buffers, count frames/errors/fps in one task. Optional HTTP (`/`, `/status`, `/snapshot.jpg`) encodes the next captured frame with the hardware JPEG engine; requests are serialised and bounded at 2 s. Without the option the component is a stub and the default build links no video code.
- `sdkconfig.camera_ov5647.defaults` overlay: OV5647 auto-detect, RAW10 1920×1080 30 fps default, ISP pipeline controller (AE/AWB), no H.264/UVC/DVP/SPI.
- `esp_video` 2.5.* is declared in `camera_smoke/idf_component.yml`, conditional on the Kconfig option.

## Security analysis

The bench HTTP server is unauthenticated and exposes the camera image to the LAN; it is opt-in, logged as bench-only, and documented as never for an installed unit. Handlers read no request input (no query or body parsing). The camera has no relay or access path. Failure returns an error to `app_main`, which continues without video.

## Work breakdown

- [x] Install pinned ESP-IDF v5.5.4 and the RISC-V toolchain; establish a baseline build.
- [x] Fix the two existing build defects.
- [x] Shared I2C bus in the BSP; probe uses it; OV5647 SCCB presence probe (0x36) on Waveshare.
- [x] `camera_smoke` component, Kconfig, overlay, `app_main` wiring.
- [x] Build all variants; document the bench procedure.

## Validation

Built with ESP-IDF v5.5.4 (`riscv32-esp-elf` esp-14.2.0_20260121), zero warnings in project code:

- Waveshare + `sdkconfig.revision.v3_1.defaults` (camera off) — passes.
- Waveshare + `sdkconfig.revision.pre_v3.defaults` (camera off) — passes.
- Function-EV default — passes.
- Waveshare + v3.1 + `sdkconfig.camera_ov5647.defaults`, with `esp-video-components` master @ `dbbdcbd` (esp_video 2.5.0, esp_cam_sensor 2.6.0) and `esp-iot-solution` `cmake_utilities` as local components — passes; ELF contains the OV5647 detect function, `esp_video_init`, the JPEG encoder and the capture task.

The component-manager path (`idf_component.yml`) was **not** exercised here because the registry was unreachable from the build environment. **No hardware test has been run.** Remaining manual checks: sensor PID 0x5647 read, frames and fps at 1080p, snapshot image quality/colour, PSRAM headroom, temperature after an hour, behaviour with the camera unplugged.

## Decisions / discoveries

- The P4 ISP input limit is 1920×1080; the OV5647's 1080p30 RAW10 mode is used.
- The JPEG output buffer is sized at one byte per pixel (half of RGB565).
- Without the ISP pipeline controller, frames lack auto exposure/white balance.

## Final result

See Validation. Next bench step after a passing capture: enable the hardware H.264 device (needs `esp_h264`) and measure sustained encode.
