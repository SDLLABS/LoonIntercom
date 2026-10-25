idf_component_register(SRCS "camera_smoke.c"
                       INCLUDE_DIRS "include"
                       PRIV_REQUIRES board_support esp_driver_jpeg esp_http_server
                                     esp_timer heap freertos vfs log)

# esp_video is only linked when the smoke test is enabled, so the default
# bring-up build needs no extra components. With the component manager it
# arrives as espressif__esp_video (see idf_component.yml); a local checkout
# passed through EXTRA_COMPONENT_DIRS is named esp_video.
if(CONFIG_P4_CAMERA_SMOKE)
    idf_component_optional_requires(PRIVATE espressif__esp_video esp_video)
endif()
