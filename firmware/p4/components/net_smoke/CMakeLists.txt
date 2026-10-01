idf_component_register(SRCS "net_smoke.c" INCLUDE_DIRS "include"
                       PRIV_REQUIRES board_support esp_eth esp_event esp_netif log)
