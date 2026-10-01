// Helpers for screen-demo.yaml: a 1-bit drawing canvas in portrait coordinates (540 x 960).
#pragma once

#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <algorithm>
#include <esp_heap_caps.h>
#include "esphome/components/display/display.h"

namespace demo {

static const int CW = 540, CH = 960;
static const int CSTRIDE = 68;     // bytes per canvas row: 544 px, so every row starts on a byte
static uint8_t *canvas = nullptr;  // 1 bit per pixel, set = ink

inline bool canvas_ready() {
  if (canvas == nullptr)
    canvas = (uint8_t *) heap_caps_calloc(CSTRIDE * CH, 1, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
  return canvas != nullptr;
}

inline void canvas_clear() {
  if (canvas_ready())
    memset(canvas, 0, CSTRIDE * CH);
}

// a round brush dot, clipped to y0..y1
inline void canvas_dot(int cx, int cy, int r, int y0, int y1) {
  if (!canvas_ready())
    return;
  for (int y = cy - r; y <= cy + r; y++) {
    if (y < y0 || y > y1)
      continue;
    for (int x = cx - r; x <= cx + r; x++) {
      if (x < 0 || x >= CW || (x - cx) * (x - cx) + (y - cy) * (y - cy) > r * r)
        continue;
      canvas[y * CSTRIDE + (x >> 3)] |= 1 << (x & 7);
    }
  }
}

inline void canvas_line(int x0, int y0, int x1, int y1, int r, int ymin, int ymax) {
  const int steps = std::max(std::abs(x1 - x0), std::abs(y1 - y0));
  if (steps == 0) {
    canvas_dot(x0, y0, r, ymin, ymax);
    return;
  }
  for (int i = 0; i <= steps; i++)
    canvas_dot(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps, r, ymin, ymax);
}

inline void canvas_draw(esphome::display::Display &it, int y0, int y1) {
  if (canvas == nullptr)
    return;
  for (int y = y0; y <= y1; y++) {
    const uint8_t *row = canvas + y * CSTRIDE;
    for (int b = 0; b < CSTRIDE; b++) {
      if (row[b] == 0)
        continue;
      for (int k = 0; k < 8; k++)
        if ((row[b] & (1 << k)) && b * 8 + k < CW)
          it.draw_pixel_at(b * 8 + k, y, esphome::display::COLOR_ON);
    }
  }
}

// 4x4 Bayer threshold, for the dithered gradient
inline int bayer4(int x, int y) {
  static const uint8_t m[4][4] = {{0, 8, 2, 10}, {12, 4, 14, 6}, {3, 11, 1, 9}, {15, 7, 13, 5}};
  return m[y & 3][x & 3];
}

// paper grey 0 (black) .. 255 (white); the driver draws COLOR_ON as black ink, so invert
inline esphome::Color paper(int grey) {
  const uint8_t c = 255 - grey;
  return esphome::Color(c, c, c);
}

}  // namespace demo
