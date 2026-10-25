#include "board_support.h"

/* Waveshare ESP32-P4-ETH, SKU 32086. GPIOs from the official board schematic.
   IP101GRI RMII, ES8311 codec and NS4150B amplifier are fitted. This is the
   base Ethernet board; a PoE module and camera are not assumed. The camera
   SCCB shares the internal I2C bus (GPIO7/GPIO8) with the codec. */
static const struct p4_i2c_probe probes[] = {
    {"ES8311 codec", 0x18},
    {"possible OV5647 camera (SCCB)", 0x36},
};

const struct p4_board_config p4_waveshare_esp32_p4_eth_32086 = {
    .name = "Waveshare ESP32-P4-ETH SKU 32086 (bench target)",
    .expected_nor_bytes = 32u * 1024u * 1024u,
    .expected_psram_bytes = 32u * 1024u * 1024u,
    .ethernet = {
        .mdc_gpio = 31,
        .mdio_gpio = 52,
        .reset_gpio = 51,
        .phy_address = 1,
        .rmii = {
            .crs_dv_gpio = 28,
            .rxd0_gpio = 29,
            .rxd1_gpio = 30,
            .txd0_gpio = 34,
            .txd1_gpio = 35,
            .tx_en_gpio = 49,
            .ref_clk_input_gpio = 50,
        },
    },
    .i2c = {
        .port = 0,
        .sda_gpio = 7,
        .scl_gpio = 8,
        .probes = probes,
        .probe_count = sizeof(probes) / sizeof(probes[0]),
    },
    .audio = {
        .i2s_dout_gpio = 9,
        .i2s_lrck_gpio = 10,
        .i2s_din_gpio = 11,
        .i2s_sclk_gpio = 12,
        .i2s_mclk_gpio = 13,
        .amplifier_enable_gpio = 53,
    },
    .camera = {
        .csi_lanes = 2,
        .pin_count = 22,
        .pitch_um = 500,
        .reset_gpio = -1,
        .pwdn_gpio = -1,
        .sccb_freq_hz = 100000,
    },
};
