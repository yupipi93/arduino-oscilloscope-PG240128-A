/*
 * M1 — Static waveform viewer (no trigger yet)
 *
 * Architecture (docs/04-build-plan.md): capture-then-draw.
 *   1. Burst-capture 240 samples from A7 with analogRead (~9.6 kSps,
 *      one sample per screen column, ~27 ms per sweep).
 *   2. Redraw the whole screen from the buffer (U8g2 page loop).
 * Sampling and drawing never overlap: the display bus (12 GPIOs
 * toggling) would couple noise into the ADC.
 *
 * Test signal: the Nano's own PWM on D3 (~490 Hz square, 50% duty)
 * fed through the front-end resistor:  D3 --[10k]--> A7
 * Expected: ~13 square-wave cycles dancing on screen (they drift
 * because there is no trigger yet — that's milestone M2).
 */

#include <Arduino.h>
#include <U8g2lib.h>

U8G2_T6963_240X128_1_8080 u8g2(U8G2_R0,
  /*DB0..DB7 =*/ 8, 9, 10, 11, 4, 5, 6, 7,
  /*WR=*/ 17, /*CE=*/ 14, /*C-D=*/ 15, /*RST=*/ 16);

#define N_SAMPLES   240
#define TEST_PWM_PIN  3   // ~490 Hz square wave test signal

uint8_t samples[N_SAMPLES];   // 8-bit samples, one per screen column

void capture(void) {
  for (uint16_t i = 0; i < N_SAMPLES; i++) {
    samples[i] = analogRead(A7) >> 2;   // 10-bit -> 8-bit
  }
}

// Map an 8-bit sample (0 = 0 V, 255 = 5 V) to a screen row:
// 0 V at the bottom (y=127), 5 V at the top (y=0).
static inline uint8_t sample_to_y(uint8_t s) {
  return 127 - (s >> 1);
}

void draw(void) {
  u8g2.firstPage();
  do {
    // Pure function of the sample buffer — runs 16x per frame.
    u8g2.drawFrame(0, 0, 240, 128);
    for (uint16_t x = 1; x < N_SAMPLES; x++) {
      u8g2.drawLine(x - 1, sample_to_y(samples[x - 1]),
                    x,     sample_to_y(samples[x]));
    }
  } while (u8g2.nextPage());
}

void setup(void) {
  u8g2.begin();
  analogWrite(TEST_PWM_PIN, 128);   // start the test signal
}

void loop(void) {
  capture();
  draw();
}
