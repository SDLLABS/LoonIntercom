# Waveshare ESP32-P4-ETH SKU 32086 — bench evidence and acceptance

This is a **bench target**, not a production board selection. [Waveshare's product documentation](https://docs.waveshare.com/ESP32-P4-ETH) maps SKU **32086** to the base **ESP32-P4-ETH**. Its [official three-page schematic](https://files.waveshare.com/wiki/ESP32-P4-ETH/ESP32-P4-ETH-datasheet.pdf), linked from [Waveshare's hardware resources](https://docs.waveshare.com/ESP32-P4-ETH/Resources-And-Documents), is the authority for the wiring below. Confirm the received PCB assembly/revision against that schematic before energizing peripherals. The exact silicon revision is **unknown** until its chip marking or serial boot log is read.

## Ethernet evidence

The schematic's Ethernet block uses **IP101GRI** (U10), **RMII**, a 25 MHz oscillator at the PHY and a PHY-generated 50 MHz REF_CLK into the P4. The pin map is:

| Signal | ESP32-P4 GPIO |
| --- | ---: |
| CRS_DV | 28 |
| RXD0 | 29 |
| RXD1 | 30 |
| MDC | 31 |
| TXD0 | 34 |
| TXD1 | 35 |
| TX_EN | 49 |
| REF_CLK external input | 50 |
| PHY RESET | 51 |
| MDIO | 52 |

The schematic shows PHY_AD0 strapped high (R65 populated to PHY_3V3, R66 not fitted) and PHY_AD3 low (R63 to ground). [Waveshare's official Ethernet example Kconfig](https://github.com/waveshareteam/ESP32-P4-Platform/blob/main/examples/esp-idf/11_ethernetbasic/components/ethernet_init/Kconfig.projbuild) defaults the IP101 PHY address to **1**. The BSP therefore sets address 1; verify the detected PHY address on the actual device via the ESP-IDF driver before treating it as accepted. [ESP-IDF v5.5.4](https://docs.espressif.com/projects/esp-idf/en/v5.5.4/esp32p4/api-reference/network/esp_eth.html) supports explicit RMII data pins and external clock input, which the shared Ethernet smoke code now reads from the selected BSP. Only IP101 RMII is supported by these two bench profiles.

SKU 32086 contributes **one** RJ45 Ethernet client. It does not replace the [internal-switch and power-distribution evaluation](README.md) needed to connect both the wired P4 and independent wired S3 bell behind one outdoor CAT6 feed. Bell traffic never traverses P4 firmware; do not move it to Wi-Fi.

## Audio, camera and storage evidence

The schematic connects **ES8311** (U9) over I2C SDA **GPIO7** and SCL **GPIO8**, with I2S DOUT **GPIO9**, LRCK/WS **GPIO10**, DIN **GPIO11**, SCLK/BCLK **GPIO12** and MCLK **GPIO13**. Its **NS4150B** amplifier (U11) has enable/control on **GPIO53**. The ESP32-P4-ETH's onboard microphone and speaker connector are board features, not evidence of working capture or playback. The `0x18` ES8311 I2C probe is a presence check only; it does not initialize the codec or test samples.

Waveshare documents a **two-lane MIPI-CSI**, **22-pin, 0.5 mm pitch** connector and lists **OV5647 compatibility**. The schematic shows the connector, but SKU 32086 does **not** establish that any camera sensor is attached. Record the actual module and adapter identity before choosing a sensor driver or claiming capture/H.264 operation.

Waveshare specifies **ESP32-P4NRW32**, **32 MB stacked PSRAM** and **32 MB onboard NOR flash**. The 32 MB Waveshare defaults and bench partition table are separate from the 16 MB Function-EV defaults. The [ESP-IDF v5.5.4 flash driver](https://github.com/espressif/esp-idf/blob/v5.5.4/components/spi_flash/esp_flash_spi_init.c) rejects its ROM implementation for flash of 32 MB or more, so that implementation is disabled in the Waveshare defaults. A boot log must confirm fitted NOR and PSRAM. The board has a physical microSD slot, but this firmware mounts no SD card or filesystem and must boot and run normally with the slot empty.

## Silicon revision and reproducible build

[Waveshare's FAQ](https://docs.waveshare.com/ESP32-P4-ETH/FAQ) recommends **ESP-IDF v5.5.1 through v5.5.4**. WP2.1 pins the [v5.5.4 release](https://github.com/espressif/esp-idf/releases/tag/v5.5.4), the latest in that stated range. Read the actual chip marking or serial boot log **before** choosing the pre-v3, v3.0 or v3.1 revision overlay in [the build instructions](../../firmware/p4/README.md). Do not infer silicon revision from SKU or PCB art. A revision mismatch requires a matching rebuild; never use `--force` to bypass the check. Generated `sdkconfig` and binary outputs from different board/revision profiles are not interchangeable.

## Device acceptance record to complete

No checks below have been run on hardware in WP2.1. Record serial logs, board/PCB/SoC markings, attached modules, power source and ESP-IDF revision for each check.

1. **NOR/PSRAM and revision:** read chip marking and boot log; confirm ESP32-P4 revision, detected 32 MB NOR and 32 MB stacked PSRAM, then build with the matching revision overlay. Available PSRAM heap is smaller than physical capacity and is only a diagnostic.
2. **No SD:** remove the microSD card; cold boot repeatedly from NOR and exercise normal I2C/Ethernet smoke behavior without any mounted filesystem.
3. **Wired Ethernet:** verify IP101 address, external REF_CLK, link up/down and a DHCP lease on the SKU 32086 RJ45. If the IDF driver supports it on the fitted revision, repeat `esp_eth_stop()`/`esp_eth_start()` at least ten times and require link plus DHCP recovery on every cycle. The current smoke app only starts once, so use a dedicated bench harness for restart cycling.
4. **Audio:** detect ES8311 at I2C `0x18`, initialize the actual codec/I2S path, record microphone samples and play a measured speaker tone through the NS4150B path. An I2C ACK alone does not pass capture or playback.
5. **Camera and encode:** when a camera is attached, record its exact module/sensor/adapter revision, identify it over its control bus, capture real frames on the two-lane CSI path, then exercise H.264 encoding and record frame rate, memory and errors. OV5647 compatibility alone is not a fitted-sensor claim.
6. **Single CAT6 and PoE:** with the independently wired S3 and an internal switch/power assembly, verify two distinct clients and direct RoomKey ringing through P4 reset/load faults. The base board exposes a **PoE module/power header**, not proven integrated PoE on SKU 32086. Qualify any fitted PoE module, isolated power, inrush, thermal and bell-priority behavior separately from base-board Ethernet.

The remaining production gates include PCB/SoC revision fit, camera module, PoE module or variant, switch/rail design, thermal/power margins and outdoor environmental qualification.
