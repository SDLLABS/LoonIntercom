#include "sdkconfig.h"
#include "camera_smoke.h"

#if !CONFIG_P4_CAMERA_SMOKE

esp_err_t camera_smoke_start(void)
{
    return ESP_ERR_NOT_SUPPORTED;
}

#else

#include <fcntl.h>
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>

#include "driver/jpeg_encode.h"
#include "esp_cam_sensor_types.h"
#include "esp_heap_caps.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "esp_video_device.h"
#include "esp_video_init.h"
#include "esp_video_ioctl.h"
#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "freertos/task.h"
#include "linux/videodev2.h"
#if CONFIG_P4_CAMERA_SMOKE_HTTP
#include "esp_http_server.h"
#endif

#include "board_support.h"

#define NBUF CONFIG_P4_CAMERA_SMOKE_BUFFERS
#define FPS_WINDOW_US (2 * 1000 * 1000)
#define SNAPSHOT_WAIT_MS 2000
#define JPEG_TIMEOUT_MS 1000
#define CAPTURE_TASK_STACK 4096
#define CAPTURE_TASK_PRIO 5

static const char *TAG = "camera_smoke";

/* Counters are written only by the capture task and read by HTTP handlers;
   32-bit aligned loads/stores are atomic on the P4. */
static struct {
    int fd;
    uint8_t *buf[NBUF];
    uint32_t buf_len[NBUF];
    uint32_t width;
    uint32_t height;
    uint32_t pixfmt;
    uint16_t chip_pid;
    bool chip_id_ok;
    char card[32];
    volatile uint32_t frames;
    volatile uint32_t errors;
    volatile uint32_t fps_x10;
    volatile int64_t last_frame_us;
    jpeg_encoder_handle_t jpeg;
    uint8_t *jpeg_out;
    size_t jpeg_out_cap;
    volatile uint32_t snap_req_seq;  /* written by the handler holding snap_lock */
    volatile uint32_t snap_done_seq; /* written by the capture task */
    volatile uint32_t jpeg_len;
    volatile esp_err_t snap_err;
    SemaphoreHandle_t snap_lock;
    SemaphoreHandle_t snap_done;
} s = {.fd = -1};

static void read_chip_id(void)
{
    esp_cam_sensor_id_t id = {0};
    struct v4l2_ext_control ctrl = {
        .id = ESP_CAM_SENSOR_IOC_G_CHIP_ID,
        .size = sizeof(id),
        .p_u8 = (uint8_t *)&id,
    };
    struct v4l2_ext_controls ctrls = {
        .ctrl_class = V4L2_CTRL_CLASS_ESP_CAM_IOCTL,
        .count = 1,
        .controls = &ctrl,
    };
    s.chip_id_ok = ioctl(s.fd, VIDIOC_G_EXT_CTRLS, &ctrls) == 0;
    s.chip_pid = id.pid;
    if (s.chip_id_ok) {
        ESP_LOGI(TAG, "sensor chip id (PID): 0x%04" PRIx16, s.chip_pid);
    } else {
        ESP_LOGW(TAG, "sensor chip id could not be read");
    }
}

static esp_err_t open_and_stream(void)
{
    s.fd = open(ESP_VIDEO_MIPI_CSI_DEVICE_NAME, O_RDONLY);
    if (s.fd < 0) {
        ESP_LOGE(TAG, "open %s failed", ESP_VIDEO_MIPI_CSI_DEVICE_NAME);
        return ESP_FAIL;
    }

    struct v4l2_capability cap = {0};
    if (ioctl(s.fd, VIDIOC_QUERYCAP, &cap) == 0) {
        snprintf(s.card, sizeof(s.card), "%s", (const char *)cap.card);
        ESP_LOGI(TAG, "video device: driver=%s card=%s", cap.driver, cap.card);
    }
    read_chip_id();

    /* Keep the sensor's configured resolution; ask the ISP for RGB565. */
    struct v4l2_format fmt = {.type = V4L2_BUF_TYPE_VIDEO_CAPTURE};
    if (ioctl(s.fd, VIDIOC_G_FMT, &fmt) != 0) {
        ESP_LOGE(TAG, "VIDIOC_G_FMT failed");
        return ESP_FAIL;
    }
    fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_RGB565;
    if (ioctl(s.fd, VIDIOC_S_FMT, &fmt) != 0) {
        ESP_LOGE(TAG, "VIDIOC_S_FMT RGB565 %" PRIu32 "x%" PRIu32 " failed",
                 fmt.fmt.pix.width, fmt.fmt.pix.height);
        return ESP_FAIL;
    }
    s.width = fmt.fmt.pix.width;
    s.height = fmt.fmt.pix.height;
    s.pixfmt = fmt.fmt.pix.pixelformat;
    ESP_LOGI(TAG, "capture format: %" PRIu32 "x%" PRIu32 " RGB565", s.width, s.height);

    struct v4l2_requestbuffers req = {
        .count = NBUF,
        .type = V4L2_BUF_TYPE_VIDEO_CAPTURE,
        .memory = V4L2_MEMORY_MMAP,
    };
    if (ioctl(s.fd, VIDIOC_REQBUFS, &req) != 0) {
        ESP_LOGE(TAG, "VIDIOC_REQBUFS failed");
        return ESP_ERR_NO_MEM;
    }
    for (int i = 0; i < NBUF; ++i) {
        struct v4l2_buffer b = {
            .type = V4L2_BUF_TYPE_VIDEO_CAPTURE,
            .memory = V4L2_MEMORY_MMAP,
            .index = i,
        };
        if (ioctl(s.fd, VIDIOC_QUERYBUF, &b) != 0) return ESP_FAIL;
        s.buf[i] = mmap(NULL, b.length, PROT_READ | PROT_WRITE, MAP_SHARED, s.fd, b.m.offset);
        if (s.buf[i] == NULL || s.buf[i] == MAP_FAILED) {
            s.buf[i] = NULL;
            return ESP_ERR_NO_MEM;
        }
        s.buf_len[i] = b.length;
        if (ioctl(s.fd, VIDIOC_QBUF, &b) != 0) return ESP_FAIL;
    }
    int type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    if (ioctl(s.fd, VIDIOC_STREAMON, &type) != 0) {
        ESP_LOGE(TAG, "VIDIOC_STREAMON failed");
        return ESP_FAIL;
    }
    return ESP_OK;
}

static void encode_snapshot(const struct v4l2_buffer *b, uint32_t want)
{
    esp_err_t err = ESP_ERR_INVALID_STATE;
    uint32_t out_len = 0;
#if CONFIG_P4_CAMERA_SMOKE_HTTP
    jpeg_encode_cfg_t cfg = {
        .width = s.width,
        .height = s.height,
        .src_type = JPEG_ENCODE_IN_FORMAT_RGB565,
        .sub_sample = JPEG_DOWN_SAMPLING_YUV422,
        .image_quality = CONFIG_P4_CAMERA_SMOKE_JPEG_QUALITY,
    };
    err = jpeg_encoder_process(s.jpeg, &cfg, s.buf[b->index], b->bytesused,
                               s.jpeg_out, s.jpeg_out_cap, &out_len);
#endif
    s.jpeg_len = out_len;
    s.snap_err = err;
    s.snap_done_seq = want;
    xSemaphoreGive(s.snap_done);
}

static void capture_task(void *arg)
{
    (void)arg;
    uint32_t window_frames = 0;
    int64_t window_start = esp_timer_get_time();
    for (;;) {
        struct v4l2_buffer b = {
            .type = V4L2_BUF_TYPE_VIDEO_CAPTURE,
            .memory = V4L2_MEMORY_MMAP,
        };
        if (ioctl(s.fd, VIDIOC_DQBUF, &b) != 0) {
            ++s.errors;
            vTaskDelay(pdMS_TO_TICKS(10)); /* bounded back-off; never spin */
            continue;
        }
        if (b.flags & V4L2_BUF_FLAG_DONE) {
            ++s.frames;
            ++window_frames;
            s.last_frame_us = esp_timer_get_time();
            uint32_t want = s.snap_req_seq;
            if (want != s.snap_done_seq) encode_snapshot(&b, want);
        } else {
            ++s.errors;
        }
        if (ioctl(s.fd, VIDIOC_QBUF, &b) != 0) {
            ++s.errors;
            vTaskDelay(pdMS_TO_TICKS(10));
        }
        int64_t now = esp_timer_get_time();
        if (now - window_start >= FPS_WINDOW_US) {
            s.fps_x10 = (uint32_t)((int64_t)window_frames * 10 * 1000000 / (now - window_start));
            window_frames = 0;
            window_start = now;
        }
    }
}

#if CONFIG_P4_CAMERA_SMOKE_HTTP
static esp_err_t snapshot_handler(httpd_req_t *req)
{
    if (xSemaphoreTake(s.snap_lock, pdMS_TO_TICKS(SNAPSHOT_WAIT_MS)) != pdTRUE) {
        httpd_resp_set_status(req, "503 Service Unavailable");
        return httpd_resp_sendstr(req, "busy\n");
    }
    uint32_t want = s.snap_req_seq + 1;
    s.snap_req_seq = want;
    TickType_t deadline = xTaskGetTickCount() + pdMS_TO_TICKS(SNAPSHOT_WAIT_MS);
    while (s.snap_done_seq != want) {
        TickType_t now = xTaskGetTickCount();
        if (now >= deadline || xSemaphoreTake(s.snap_done, deadline - now) != pdTRUE) break;
    }
    esp_err_t ret;
    if (s.snap_done_seq == want && s.snap_err == ESP_OK && s.jpeg_len > 0) {
        httpd_resp_set_type(req, "image/jpeg");
        httpd_resp_set_hdr(req, "Cache-Control", "no-store");
        ret = httpd_resp_send(req, (const char *)s.jpeg_out, s.jpeg_len);
    } else {
        httpd_resp_set_status(req, "503 Service Unavailable");
        ret = httpd_resp_sendstr(req, s.snap_done_seq == want ? "jpeg encode failed\n"
                                                               : "no frame within 2 s\n");
    }
    xSemaphoreGive(s.snap_lock);
    return ret;
}

static esp_err_t status_handler(httpd_req_t *req)
{
    char out[512];
    int64_t now = esp_timer_get_time();
    int64_t last = s.last_frame_us;
    uint32_t fps = s.fps_x10;
    snprintf(out, sizeof(out),
             "sensor_pid: 0x%04" PRIx16 " (chip id read: %s)\n"
             "device: %s\n"
             "format: %" PRIu32 "x%" PRIu32 " RGB565\n"
             "frames: %" PRIu32 "\n"
             "errors: %" PRIu32 "\n"
             "fps: %" PRIu32 ".%" PRIu32 "\n"
             "last_frame_age_ms: %lld\n"
             "psram_free: %u\n"
             "internal_free: %u\n"
             "uptime_s: %lld\n",
             s.chip_pid, s.chip_id_ok ? "yes" : "no", s.card, s.width, s.height,
             s.frames, s.errors, fps / 10, fps % 10,
             last ? (long long)((now - last) / 1000) : -1LL,
             (unsigned)heap_caps_get_free_size(MALLOC_CAP_SPIRAM),
             (unsigned)heap_caps_get_free_size(MALLOC_CAP_INTERNAL),
             (long long)(now / 1000000));
    httpd_resp_set_type(req, "text/plain");
    httpd_resp_set_hdr(req, "Cache-Control", "no-store");
    return httpd_resp_sendstr(req, out);
}

static esp_err_t index_handler(httpd_req_t *req)
{
    httpd_resp_set_type(req, "text/plain");
    return httpd_resp_sendstr(req, "SDLLABS P4 camera bench smoke (no auth, bench only)\n"
                                   "/status        counters and format\n"
                                   "/snapshot.jpg  one hardware-encoded JPEG frame\n");
}

static esp_err_t start_http(void)
{
    jpeg_encode_engine_cfg_t eng = {.timeout_ms = JPEG_TIMEOUT_MS};
    esp_err_t err = jpeg_new_encoder_engine(&eng, &s.jpeg);
    if (err != ESP_OK) return err;
    jpeg_encode_memory_alloc_cfg_t mem = {.buffer_direction = JPEG_ENC_ALLOC_OUTPUT_BUFFER};
    /* RGB565 is 2 bytes/pixel; a quality <= 100 JPEG fits in half of that. */
    s.jpeg_out = jpeg_alloc_encoder_mem((size_t)s.width * s.height, &mem, &s.jpeg_out_cap);
    if (s.jpeg_out == NULL) return ESP_ERR_NO_MEM;

    httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
    cfg.server_port = CONFIG_P4_CAMERA_SMOKE_HTTP_PORT;
    cfg.ctrl_port = CONFIG_P4_CAMERA_SMOKE_HTTP_PORT == 32768 ? 32769 : 32768;
    cfg.max_uri_handlers = 4;
    cfg.max_open_sockets = 3;
    cfg.lru_purge_enable = true;
    httpd_handle_t server = NULL;
    err = httpd_start(&server, &cfg);
    if (err != ESP_OK) return err;
    static const httpd_uri_t uris[] = {
        {.uri = "/", .method = HTTP_GET, .handler = index_handler},
        {.uri = "/status", .method = HTTP_GET, .handler = status_handler},
        {.uri = "/snapshot.jpg", .method = HTTP_GET, .handler = snapshot_handler},
    };
    for (size_t i = 0; i < sizeof(uris) / sizeof(uris[0]); ++i) {
        err = httpd_register_uri_handler(server, &uris[i]);
        if (err != ESP_OK) return err;
    }
    ESP_LOGW(TAG, "HTTP bench server on port %d: NO authentication, bench use only",
             CONFIG_P4_CAMERA_SMOKE_HTTP_PORT);
    return ESP_OK;
}
#endif /* CONFIG_P4_CAMERA_SMOKE_HTTP */

esp_err_t camera_smoke_start(void)
{
    const struct p4_board_config *board = p4_board_get();
    i2c_master_bus_handle_t bus = NULL;
    esp_err_t err = p4_board_i2c_bus(&bus);
    if (err != ESP_OK) return err;

    s.snap_lock = xSemaphoreCreateMutex();
    s.snap_done = xSemaphoreCreateBinary();
    if (s.snap_lock == NULL || s.snap_done == NULL) return ESP_ERR_NO_MEM;

    const esp_video_init_csi_config_t csi = {
        .sccb_config = {
            .init_sccb = false,
            .i2c_handle = bus,
            .freq = board->camera.sccb_freq_hz,
        },
        .reset_pin = board->camera.reset_gpio,
        .pwdn_pin = board->camera.pwdn_gpio,
    };
    const esp_video_init_config_t video = {.csi = &csi};
    err = esp_video_init(&video);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "esp_video_init failed (%s): no sensor detected on %u-lane CSI?",
                 esp_err_to_name(err), board->camera.csi_lanes);
        return err;
    }
    err = open_and_stream();
    if (err != ESP_OK) return err;
#if CONFIG_P4_CAMERA_SMOKE_HTTP
    err = start_http();
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "HTTP bench server failed: %s", esp_err_to_name(err));
        return err;
    }
#endif
    if (xTaskCreate(capture_task, "cam_smoke", CAPTURE_TASK_STACK, NULL,
                    CAPTURE_TASK_PRIO, NULL) != pdPASS) {
        return ESP_ERR_NO_MEM;
    }
    ESP_LOGI(TAG, "capture started; frame counters at /status");
    return ESP_OK;
}

#endif /* CONFIG_P4_CAMERA_SMOKE */
