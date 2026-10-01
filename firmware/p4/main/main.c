#include "esp_log.h"
#include "board_support.h"
#include "net_smoke.h"
#include "peripheral_smoke.h"

static const char *TAG = "p4_bringup";

void app_main(void)
{
    const struct p4_board_config *board = p4_board_get();
    ESP_LOGI(TAG, "%s bring-up; no SD or filesystem is used", board->name);
    p4_board_report_memory();
    peripheral_smoke_probe_i2c();
    esp_err_t err = net_smoke_start();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "wired Ethernet start failed: %s", esp_err_to_name(err));
    }
    ESP_LOGI(TAG, "camera frame, H.264 and audio sample tests require later device gates");
}
