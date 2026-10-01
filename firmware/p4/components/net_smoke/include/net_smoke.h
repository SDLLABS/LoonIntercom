#pragma once
#include "esp_err.h"

/* Starts the on-board wired IP101 interface and reports link/DHCP events. */
esp_err_t net_smoke_start(void);
