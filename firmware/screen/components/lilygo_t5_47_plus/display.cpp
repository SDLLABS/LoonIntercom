#include "display.h"
#include "esphome/core/log.h"
#include "esphome/core/application.h"
#include "esphome/core/helpers.h"
#ifdef USE_ESP32_FRAMEWORK_ARDUINO

#include <esp32-hal-gpio.h>
#include <esp_heap_caps.h>
#include <esp_sleep.h>
#include <algorithm>
#include <cstring>

namespace esphome {
namespace lilygo_t5_47_plus {

static const char *const TAG = "lilygo_t5_47_plus";

void LilygoT5_47PlusDisplay::setup() {
  ESP_LOGV(TAG, "Initialize called");

  ESP_LOGV(TAG, "Free heap: %d bytes", heap_caps_get_free_size(MALLOC_CAP_8BIT));
  ESP_LOGV(TAG, "Free PSRAM: %d bytes", heap_caps_get_free_size(MALLOC_CAP_SPIRAM));
  ESP_LOGV(TAG, "Largest free PSRAM block: %d bytes", heap_caps_get_largest_free_block(MALLOC_CAP_SPIRAM));

  epd_init();
  uint32_t buffer_size = this->get_buffer_length_();
  ESP_LOGD(TAG, "Buffer size: %u bytes", buffer_size);

  this->buffer_ = (uint8_t *) heap_caps_malloc(buffer_size, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
  if (this->buffer_ == nullptr) {
    ESP_LOGE(TAG, "Could not allocate display buffer (%u bytes). Is PSRAM enabled?", buffer_size);
    this->mark_failed();
    return;
  }

  memset(this->buffer_, 0xFF, buffer_size);

  // Klingelbox: what the panel shows, the newest picture, the picture being drawn, the plan,
  // and a background task that does the refreshing
  const uint32_t caps = MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT;
  this->prev_buffer_ = (uint8_t *) heap_caps_malloc(buffer_size, caps);
  this->target_buffer_ = (uint8_t *) heap_caps_malloc(buffer_size, caps);
  this->work_buffer_ = (uint8_t *) heap_caps_malloc(buffer_size, caps);
  this->plan_ = (uint16_t *) heap_caps_malloc(960 * 540 * sizeof(uint16_t), caps);
  this->lock_ = xSemaphoreCreateMutex();
  if (this->prev_buffer_ == nullptr || this->target_buffer_ == nullptr || this->work_buffer_ == nullptr ||
      this->plan_ == nullptr || this->lock_ == nullptr ||
      xTaskCreatePinnedToCore(LilygoT5_47PlusDisplay::refresh_task_, "epd_refresh", 8192, this, 2, &this->task_, 0) !=
          pdPASS) {
    ESP_LOGW(TAG, "No memory for background refresh; refreshing in the main loop, always full");
    this->task_ = nullptr;
    this->partial_updating_ = false;
  }
}

float LilygoT5_47PlusDisplay::get_setup_priority() const { return setup_priority::PROCESSOR; }
size_t LilygoT5_47PlusDisplay::get_buffer_length_() {
  return this->get_width_internal() * this->get_height_internal() / 2;
}

void LilygoT5_47PlusDisplay::update() {
  uint32_t t0 = esphome::millis();
  this->do_update_();
  uint32_t t1 = esphome::millis();
  this->display();
  uint32_t t2 = esphome::millis();
  ESP_LOGV(TAG, "update(): do_update_=%ums, display=%ums, total=%ums", t1 - t0, t2 - t1, t2 - t0);
}

void HOT LilygoT5_47PlusDisplay::draw_absolute_pixel_internal(int x, int y, Color color) {
  if (x >= this->get_width_internal() || y >= this->get_height_internal() || x < 0 || y < 0)
    return;
  // ESPHome's logical COLOR_ON is a marked pixel. On E-Paper that means black,
  // while COLOR_OFF is the unmarked white paper background.
  uint8_t luminance =
      (color.red * 2126 / 10000) + (color.green * 7152 / 10000) + (color.blue * 722 / 10000);
  uint8_t gs = 255 - luminance;
  epd_draw_pixel(x, y, gs, this->buffer_);
}

void LilygoT5_47PlusDisplay::fill(Color color) {
  if (this->buffer_ == nullptr)
    return;
  // Match draw_absolute_pixel_internal(): logical OFF is white paper and ON is
  // black ink.
  uint8_t luminance =
      (color.red * 2126 / 10000) + (color.green * 7152 / 10000) + (color.blue * 722 / 10000);
  uint8_t gs = 255 - luminance;
  // 4-bit per pixel: pack same value into both nibbles
  uint8_t fill_byte = (gs & 0xF0) | (gs >> 4);
  memset(this->buffer_, fill_byte, this->get_buffer_length_());
}

void LilygoT5_47PlusDisplay::dump_config() {
  LOG_DISPLAY("", "LilygoT5_47PlusDisplay", this);
  LOG_UPDATE_INTERVAL(this);
  // Log why the ESP32-S3 woke up — helps verify deep sleep is working
  esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
  switch (cause) {
    case ESP_SLEEP_WAKEUP_UNDEFINED:
      ESP_LOGCONFIG(TAG, "  Wakeup cause: power-on / normal reset");
      break;
    case ESP_SLEEP_WAKEUP_TIMER:
      ESP_LOGCONFIG(TAG, "  Wakeup cause: timer (deep sleep)");
      break;
    case ESP_SLEEP_WAKEUP_EXT0:
      ESP_LOGCONFIG(TAG, "  Wakeup cause: ext0 pin");
      break;
    case ESP_SLEEP_WAKEUP_EXT1:
      ESP_LOGCONFIG(TAG, "  Wakeup cause: ext1 pin(s)");
      break;
    case ESP_SLEEP_WAKEUP_TOUCHPAD:
      ESP_LOGCONFIG(TAG, "  Wakeup cause: touch pad");
      break;
    default:
      ESP_LOGCONFIG(TAG, "  Wakeup cause: other (%d)", (int) cause);
      break;
  }
}

void LilygoT5_47PlusDisplay::display() {
  if (this->task_ == nullptr) {
    this->display_full_(this->buffer_, PAGE_CHANGE_FLASH);
    return;
  }
  xSemaphoreTake(this->lock_, portMAX_DELAY);
  memcpy(this->target_buffer_, this->buffer_, this->get_buffer_length_());
  // a page change stays with its picture, even if a newer picture replaces it before it is drawn
  this->target_page_change_ = this->target_page_change_ || this->page_change_next_;
  this->page_change_next_ = false;
  this->pending_ = true;
  xSemaphoreGive(this->lock_);
  xTaskNotifyGive(this->task_);
}

void LilygoT5_47PlusDisplay::refresh_task_(void *arg) { static_cast<LilygoT5_47PlusDisplay *>(arg)->refresh_loop_(); }

void LilygoT5_47PlusDisplay::refresh_loop_() {
  for (;;) {
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
    // draw the newest picture; if another one arrived meanwhile, go again (in between pictures
    // are skipped, the panel jumps straight to the latest state)
    for (;;) {
      xSemaphoreTake(this->lock_, portMAX_DELAY);
      if (!this->pending_) {
        xSemaphoreGive(this->lock_);
        break;
      }
      memcpy(this->work_buffer_, this->target_buffer_, this->get_buffer_length_());
      const bool page_change = this->target_page_change_;
      this->target_page_change_ = false;
      this->busy_ = true;
      this->pending_ = false;
      xSemaphoreGive(this->lock_);

      if (page_change) {
        this->display_full_(this->work_buffer_, this->page_change_style_);
      } else {
        const bool full = this->force_full_ || !this->partial_updating_ ||
                          (this->full_update_every_ > 0 && this->partial_count_ >= this->full_update_every_);
        if (full || !this->display_partial_(this->work_buffer_))
          this->display_full_(this->work_buffer_, PAGE_CHANGE_FLASH);
      }
      this->busy_ = false;
    }
  }
}

void LilygoT5_47PlusDisplay::display_full_(const uint8_t *fb, uint8_t style) {
  static const char *const STYLES[3] = {"flash", "short flash", "deep clean"};
  uint32_t t0 = esphome::millis();
  ESP_LOGD(TAG, "Refreshing EPD (full, %s)...", STYLES[style < 3 ? style : 0]);

  epd_poweron();
  uint32_t t1 = esphome::millis();

  // clear to white, then draw the picture from white (the grey scale is calibrated from white)
  switch (style) {
    case PAGE_CHANGE_SHORT_FLASH:
      epd_clear_area_cycles(epd_full_screen(), 1, 50);  // one black-white cycle
      break;
    case PAGE_CHANGE_DEEP_CLEAN:
      for (int i = 0; i < 5; i++)
        epd_clear();  // 5 x 4 balanced black-white cycles
      break;
    default:
      epd_clear();  // four black-white cycles, the cleanest
      break;
  }
  uint32_t t2 = esphome::millis();

  epd_draw_grayscale_image(epd_full_screen(), (uint8_t *) fb);
  uint32_t t3 = esphome::millis();

  epd_poweroff();
  uint32_t t4 = esphome::millis();

  if (this->prev_buffer_ != nullptr && fb != this->prev_buffer_)
    memcpy(this->prev_buffer_, fb, this->get_buffer_length_());
  this->partial_count_ = 0;
  this->force_full_ = false;

  ESP_LOGD(TAG, "EPD refresh done: poweron=%ums clear=%ums draw=%ums poweroff=%ums total=%ums", t1 - t0, t2 - t1,
           t3 - t2, t4 - t3, t4 - t0);
  ESP_LOGD(TAG, "Full-draw frames (ms): %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d",
           (int) (epd_full_frame_us(0) / 1000), (int) (epd_full_frame_us(1) / 1000), (int) (epd_full_frame_us(2) / 1000),
           (int) (epd_full_frame_us(3) / 1000), (int) (epd_full_frame_us(4) / 1000), (int) (epd_full_frame_us(5) / 1000),
           (int) (epd_full_frame_us(6) / 1000), (int) (epd_full_frame_us(7) / 1000), (int) (epd_full_frame_us(8) / 1000),
           (int) (epd_full_frame_us(9) / 1000), (int) (epd_full_frame_us(10) / 1000),
           (int) (epd_full_frame_us(11) / 1000), (int) (epd_full_frame_us(12) / 1000),
           (int) (epd_full_frame_us(13) / 1000), (int) (epd_full_frame_us(14) / 1000));
}

// Klingelbox: flash-free partial refresh. Works out, per pixel, how far it has to be darkened or
// lightened to get from what the panel shows to the new picture, and draws all of it in one sweep
// over the changed rows, touching only the changed stretch of each row. Returns false when so much
// changed that a full refresh looks cleaner.
bool LilygoT5_47PlusDisplay::display_partial_(const uint8_t *fb) {
  static const int W = 960, H = 540, STRIDE = W / 2;  // 4 bits per pixel
  static const int FRINGE = 2;                        // px around a lightened pixel
  // plan bits: phase A dir 12-13, from 4-7, to 0-3; phase B darken flag 14, to 8-11 (see epd_driver.h)
  static const uint16_t DARKEN = 1 << 12, LIGHTEN = 2 << 12, DIR_MASK = 3 << 12, B_DARKEN = 1 << 14;
  uint32_t t0 = esphome::millis();

  auto nib = [](const uint8_t *row, int x) -> int {
    const uint8_t v = row[x / 2];
    return (x & 1) ? (v >> 4) : (v & 0x0F);
  };

  // 1. per row: first and last changed pixel (-1 = row unchanged)
  int16_t cx0[H], cx1[H];
  int changed_rows = 0;
  for (int y = 0; y < H; y++) {
    const uint8_t *cur = fb + y * STRIDE, *old = this->prev_buffer_ + y * STRIDE;
    cx0[y] = cx1[y] = -1;
    if (memcmp(cur, old, STRIDE) == 0)
      continue;
    int b0 = 0, b1 = STRIDE - 1;
    while (cur[b0] == old[b0])
      b0++;
    while (cur[b1] == old[b1])
      b1--;
    cx0[y] = b0 * 2;
    cx1[y] = b1 * 2 + 1;
    changed_rows++;
  }
  if (changed_rows == 0) {
    ESP_LOGD(TAG, "EPD: nothing changed, no refresh");
    return true;
  }

  // 2. rows to drive: changed rows widened by FRINGE rows; x range widened by FRINGE px
  memset(this->row_active_, 0, sizeof(this->row_active_));
  int active_rows = 0;
  for (int y = 0; y < H; y++) {
    int x0 = W, x1 = -1;
    for (int yy = std::max(0, y - FRINGE); yy <= std::min(H - 1, y + FRINGE); yy++) {
      if (cx0[yy] < 0)
        continue;
      x0 = std::min(x0, (int) cx0[yy]);
      x1 = std::max(x1, (int) cx1[yy]);
    }
    if (x1 < 0)
      continue;
    this->row_active_[y] = 1;
    this->row_x0_[y] = std::max(0, x0 - FRINGE) & ~1;
    this->row_x1_[y] = std::min(W - 1, x1 + FRINGE) | 1;
    active_rows++;
  }

  // 3. provisional plan, darkness d = 15 - grey value:
  //    darker:           frames [d_old, d_new) darkening, continuing the panel's grey scale
  //    lighter to white: frames [0, d_old) lightening = "undraw", exactly the frames it was darkened with
  //    lighter to grey:  provisionally lightened by the difference, see step 5
  //    BALANCE: a pixel never gets more white ink than it had black ink. Lightening "fully" (15 frames)
  //    for every pixel built up an electrical imbalance in a grey animation that even a flash did not
  //    remove (2026-09-29): e-paper must be driven DC-balanced.
  static const uint16_t NEAR = 1u << 15;         // marks pixels within FRINGE px of a lightened pixel
  static const int GREY_SENSITIVE_MAX = 1500;    // above this, use the second phase (see step 4)
  int changed_px = 0, grey_lighten = 0;
  for (int y = 0; y < H; y++) {
    if (!this->row_active_[y])
      continue;
    const uint8_t *cur = fb + y * STRIDE, *old = this->prev_buffer_ + y * STRIDE;
    uint16_t *pl = this->plan_ + y * W;
    for (int x = this->row_x0_[y]; x <= this->row_x1_[y]; x++) {
      const int d_old = 15 - nib(old, x);
      const int d_new = 15 - nib(cur, x);
      if (d_new > d_old) {
        pl[x] = DARKEN | (d_old << 4) | d_new;
        changed_px++;
      } else if (d_new < d_old) {
        if (d_new == 0) {
          pl[x] = LIGHTEN | (0 << 4) | d_old;
        } else {
          pl[x] = LIGHTEN | (d_new << 4) | d_old;
          grey_lighten++;
        }
        changed_px++;
      } else {
        pl[x] = 0;
      }
    }
  }
  if (changed_px * 100 > W * H * this->max_partial_percent_)
    return false;  // so much changed that a full refresh looks cleaner

  // 4. lightening spills over onto the pixels around it. Mark every pixel within FRINGE px of a
  //    lightened one (unchanged white pixels don't care). Greys among them are sensitive: black
  //    saturates, but a grey that loses some darkening shows as a light outline. With many sensitive
  //    pixels (e.g. a photo appearing where a drawing was), use a second phase: go through white.
  int sensitive = grey_lighten;
  for (int y = 0; y < H; y++) {
    if (!this->row_active_[y])
      continue;
    const uint8_t *cur = fb + y * STRIDE;
    uint16_t *pl = this->plan_ + y * W;
    for (int x = this->row_x0_[y]; x <= this->row_x1_[y]; x++) {
      if ((pl[x] & DIR_MASK) == LIGHTEN)
        continue;
      const int d_new = 15 - nib(cur, x);
      if (pl[x] == 0 && d_new == 0)
        continue;
      bool near_lighten = false;
      for (int yy = std::max(0, y - FRINGE); yy <= std::min(H - 1, y + FRINGE) && !near_lighten; yy++) {
        if (!this->row_active_[yy])
          continue;
        const uint16_t *pn = this->plan_ + yy * W;
        const int xa = std::max((int) this->row_x0_[yy], x - FRINGE);
        const int xb = std::min((int) this->row_x1_[yy], x + FRINGE);
        for (int xx = xa; xx <= xb; xx++) {
          if ((pn[xx] & DIR_MASK) == LIGHTEN) {
            near_lighten = true;
            break;
          }
        }
      }
      if (near_lighten) {
        pl[x] |= NEAR;
        if (d_new > 0 && d_new < 15)
          sensitive++;
      }
    }
  }
  const bool two_phase = sensitive > GREY_SENSITIVE_MAX;

  // 5. final plan
  //    one phase:  as provisional; unchanged black next to lightening is re-darkened alongside
  //    two phases: every pixel that gets lighter, and every grey next to lightening, goes through
  //                white: fully lightened in phase A, darkened [0, d_new) in phase B like a full
  //                refresh; pixels darkening from white next to lightening wait for phase B
  int fringe_px = 0;
  for (int y = 0; y < H; y++) {
    if (!this->row_active_[y])
      continue;
    const uint8_t *cur = fb + y * STRIDE;
    uint16_t *pl = this->plan_ + y * W;
    for (int x = this->row_x0_[y]; x <= this->row_x1_[y]; x++) {
      const uint16_t pv = pl[x];
      const bool near = pv & NEAR;
      const int d_new = 15 - nib(cur, x);
      // through white, balanced: undraw the old darkness [0, d_old), then draw the new one [0, d_new)
      auto through_white = [&](int d_old) -> uint16_t {
        return (d_old > 0 ? (LIGHTEN | (0 << 4) | d_old) : 0) | (d_new > 0 ? (B_DARKEN | (d_new << 8)) : 0);
      };
      if ((pv & DIR_MASK) == LIGHTEN) {
        pl[x] = two_phase ? through_white(pv & 0x0F) : pv;
      } else if ((pv & DIR_MASK) == DARKEN) {
        const int d_old = (pv >> 4) & 0x0F;
        if (two_phase && near)
          pl[x] = through_white(d_old);
        else
          pl[x] = pv & ~NEAR;
      } else if (near) {
        fringe_px++;
        if (d_new == 15)
          pl[x] = two_phase ? (B_DARKEN | (15 << 8)) : (DARKEN | (0 << 4) | 15);
        else
          pl[x] = two_phase ? through_white(d_new) : 0;
      }
    }
  }
  uint32_t t1 = esphome::millis();

  epd_poweron();
  epd_draw_plan(this->plan_, this->row_active_, this->row_x0_, this->row_x1_, 5, this->partial_drive_percent_,
                two_phase ? 1 : 0);
  epd_poweroff();

  memcpy(this->prev_buffer_, fb, this->get_buffer_length_());
  this->partial_count_++;
  ESP_LOGD(TAG, "EPD partial refresh: %d rows swept, %d px changed, %d fringe, %d grey-sensitive, %s, plan %ums, "
                "draw %ums (drive %u%%, partial %u of %u)",
           active_rows, changed_px, fringe_px, sensitive, two_phase ? "2 phases" : "1 phase", t1 - t0,
           esphome::millis() - t1, this->partial_drive_percent_, this->partial_count_, this->full_update_every_);
  return true;
}

void LilygoT5_47PlusDisplay::on_safe_shutdown() {
  // Fully power off the EPD supply before entering deep sleep.
  // The e-paper retains its image without power, so this is safe.
  epd_poweroff_all();
  ESP_LOGD(TAG, "EPD powered off for shutdown");
}

}  // namespace lilygo_t5_47_plus
}  // namespace esphome

#endif  // USE_ESP32_FRAMEWORK_ARDUINO
