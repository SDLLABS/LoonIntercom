#pragma once

#include "esp_err.h"

/* Bench camera smoke test. With CONFIG_P4_CAMERA_SMOKE it initialises the
   board's MIPI-CSI camera, reads the sensor chip ID, starts a capture task
   that counts frames and, if enabled, serves /snapshot.jpg and /status.
   Without it, returns ESP_ERR_NOT_SUPPORTED. Any failure is returned, never
   aborts, so the caller keeps running without video. */
esp_err_t camera_smoke_start(void);
