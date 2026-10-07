set(board_sources "board_support.c")
# Kconfig values are not available during ESP-IDF's early requirement
# expansion pass; only validate the board profile in the real build pass.
if(NOT CMAKE_BUILD_EARLY_EXPANSION)
    if(CONFIG_P4_BOARD_FUNCTION_EV_V152)
        list(APPEND board_sources "boards/function_ev_v152.c")
    elseif(CONFIG_P4_BOARD_WAVESHARE_ESP32_P4_ETH_32086)
        if(NOT CONFIG_P4_WAVESHARE_REVISION_RECORDED)
            message(FATAL_ERROR "Identify Waveshare chip revision and select a matching sdkconfig.revision.*.defaults overlay")
        endif()
        if(NOT CONFIG_ESPTOOLPY_FLASHSIZE_32MB)
            message(FATAL_ERROR "Waveshare SKU 32086 bench profile requires 32 MB NOR configuration")
        endif()
        list(APPEND board_sources "boards/waveshare_esp32_p4_eth_32086.c")
    else()
        message(FATAL_ERROR "No implemented P4 board profile selected")
    endif()
endif()

idf_component_register(SRCS ${board_sources} INCLUDE_DIRS "include"
                       REQUIRES esp_driver_i2c
                       PRIV_REQUIRES spi_flash esp_psram heap esp_system freertos log)
