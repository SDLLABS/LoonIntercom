#include "driver/i2c_master.h"
#include "esp_log.h"
#include "board_support.h"
#include "peripheral_smoke.h"

static const char *TAG = "peripheral_smoke";

void peripheral_smoke_probe_i2c(void)
{
    const struct p4_i2c_config *board_i2c = &p4_board_get()->i2c;
    if (board_i2c->probe_count == 0) {
        ESP_LOGI(TAG, "board profile defines no I2C presence probes");
        return;
    }
    i2c_master_bus_handle_t bus = NULL;
    esp_err_t err = p4_board_i2c_bus(&bus);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "I2C bus init failed: %s", esp_err_to_name(err));
        return;
    }

    for (size_t i = 0; i < board_i2c->probe_count; ++i) {
        const struct p4_i2c_probe *probe = &board_i2c->probes[i];
        err = i2c_master_probe(bus, probe->address, 100);
        ESP_LOGI(TAG, "%s address 0x%02x ACK: %s (presence only)",
                 probe->label, probe->address, err == ESP_OK ? "yes" : "no");
    }
    /* The bus is shared with the camera and codec; it is not deleted. */
}
