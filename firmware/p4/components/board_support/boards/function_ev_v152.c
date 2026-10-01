#include "board_support.h"

/* Espressif Function EV hardware v1.5.2 only: EOL software/bench reference. */
static const struct p4_i2c_probe probes[] = {
    {"ES8311 codec", 0x18},
    {"possible SC2336 camera", 0x30},
};

const struct p4_board_config p4_function_ev_v152 = {
    .name = "Espressif Function EV v1.5.2 (EOL bench reference)",
    .expected_nor_bytes = 16u * 1024u * 1024u,
    /* Fitted PSRAM population must be measured on the actual EV board. */
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
};
