#pragma once

#include "esphome/core/component.h"
#include "esphome/core/hal.h"
#include "esphome/components/display/display_buffer.h"

#include "epd_driver.h"

#include <freertos/FreeRTOS.h>
#include <freertos/semphr.h>
#include <freertos/task.h>

#ifdef USE_ESP32_FRAMEWORK_ARDUINO

namespace esphome {
namespace lilygo_t5_47_plus {

class LilygoT5_47PlusDisplay : public display::DisplayBuffer {
 public:
  float get_setup_priority() const override;

  void dump_config() override;

  void display();
  void update() override;
  void fill(Color color) override;

  void setup() override;
  void on_safe_shutdown() override;

  display::DisplayType get_display_type() override { return display::DisplayType::DISPLAY_TYPE_GRAYSCALE; }

  // Klingelbox: partial refresh without flashing, in one sweep. Only pixels that changed since the
  // last refresh get pulses, lightened or darkened by exactly the difference between old and new
  // grey; every full_update_every partial refreshes a full (flashing) refresh clears the ghosting.
  void set_partial_updating(bool partial) { this->partial_updating_ = partial; }
  void set_full_update_every(uint32_t every) { this->full_update_every_ = every; }
  // the next refresh is a full one (e.g. at night, to clear ghosting)
  void request_full_update() { this->force_full_ = true; }

  // A TRUE PAGE CHANGE: the UI switches to another screen. The next picture handed over gets a
  // clean full refresh with a short black-white flash, so no trace of the previous screen remains
  // (bench-proven 2026-09-29: every flash-free variant left the old screen behind as a light trace).
  // Changes within a screen (drawing, a counter, a button reacting) stay partial and flash-free.
  enum PageChangeStyle : uint8_t {
    PAGE_CHANGE_FLASH = 0,        // four black-white cycles (about 2 s): idle clean-up
    PAGE_CHANGE_SHORT_FLASH = 1,  // one black-white cycle (about 1 s): THE page change
    PAGE_CHANGE_DEEP_CLEAN = 2,   // five full clean-ups in a row (about 8 s), against lingering ghosts
  };
  void request_page_change() { this->page_change_next_ = true; }
  void set_page_change_style(uint8_t style) { this->page_change_style_ = style; }
  // above this share of changed pixels a full (flashing) refresh is used instead (100 = never)
  void set_max_partial_percent(uint8_t percent) { this->max_partial_percent_ = percent; }
  // ink time of a partial refresh, in % of a full refresh (each frame held at least this long)
  void set_partial_drive_percent(uint8_t percent) { this->partial_drive_percent_ = percent; }
  // true when no picture is waiting or being drawn, e.g. to pace an animation to the panel
  bool refresh_idle() const { return !this->pending_ && !this->busy_; }

 protected:
  void draw_absolute_pixel_internal(int x, int y, Color color) override;

  int get_width_internal() override { return 960; }

  int get_height_internal() override { return 540; }

  size_t get_buffer_length_();
  void display_full_(const uint8_t *fb, uint8_t style);
  bool display_partial_(const uint8_t *fb);
  static void refresh_task_(void *arg);
  void refresh_loop_();

  // Refreshing runs in its own task, so touch keeps being read while the panel updates. The main
  // loop hands over the newest picture in target_buffer_; the task draws the newest one it finds.
  uint8_t *prev_buffer_{nullptr};    // what the panel shows right now
  uint8_t *target_buffer_{nullptr};  // newest picture from the main loop
  uint8_t *work_buffer_{nullptr};    // picture the refresh task is drawing
  uint16_t *plan_{nullptr};          // per-pixel transition plan for epd_draw_plan
  uint8_t row_active_[540];          // rows the partial sweep drives
  int16_t row_x0_[540];              // per active row: first pixel to drive (even)
  int16_t row_x1_[540];              // per active row: last pixel to drive (odd)
  SemaphoreHandle_t lock_{nullptr};
  TaskHandle_t task_{nullptr};
  volatile bool pending_{false};
  bool page_change_next_{false};       // main loop: the next picture is a page change
  volatile bool target_page_change_{false};  // travels with target_buffer_ to the refresh task
  volatile uint8_t page_change_style_{PAGE_CHANGE_SHORT_FLASH};
  volatile bool busy_{false};
  uint8_t max_partial_percent_{50};
  uint8_t partial_drive_percent_{100};
  bool partial_updating_{true};
  uint32_t full_update_every_{30};
  uint32_t partial_count_{0};
  volatile bool force_full_{true};  // the first refresh after boot is always full
};

}  // namespace lilygo_t5_47_plus
}  // namespace esphome

#endif  // USE_ESP32_FRAMEWORK_ARDUINO
