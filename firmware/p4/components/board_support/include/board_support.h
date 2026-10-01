#pragma once

#include <stddef.h>
#include <stdint.h>

/* Board-neutral capabilities. Both supported bench profiles use IP101 RMII. */
struct p4_rmii_pins {
    int crs_dv_gpio;
    int rxd0_gpio;
    int rxd1_gpio;
    int txd0_gpio;
    int txd1_gpio;
    int tx_en_gpio;
    int ref_clk_input_gpio;
};

struct p4_ethernet_config {
    int mdc_gpio;
    int mdio_gpio;
    int reset_gpio;
    int phy_address;
    struct p4_rmii_pins rmii;
};

struct p4_audio_config {
    int i2s_dout_gpio;
    int i2s_lrck_gpio;
    int i2s_din_gpio;
    int i2s_sclk_gpio;
    int i2s_mclk_gpio;
    int amplifier_enable_gpio;
};

struct p4_camera_connector {
    uint8_t csi_lanes;
    uint8_t pin_count;
    uint16_t pitch_um;
};

struct p4_i2c_probe {
    const char *label;
    uint8_t address;
};

struct p4_i2c_config {
    int port;
    int sda_gpio;
    int scl_gpio;
    const struct p4_i2c_probe *probes;
    size_t probe_count;
};

struct p4_board_config {
    const char *name;
    uint32_t expected_nor_bytes;
    uint32_t expected_psram_bytes; /* Zero means population is not established. */
    struct p4_ethernet_config ethernet;
    struct p4_i2c_config i2c;
    struct p4_audio_config audio;
    struct p4_camera_connector camera;
};

const struct p4_board_config *p4_board_get(void);
void p4_board_report_memory(void);
