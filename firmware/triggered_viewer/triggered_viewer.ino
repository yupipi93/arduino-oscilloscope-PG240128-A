/*
 * M2 — Triggered waveform viewer
 *
 * Adds the software edge trigger to M1 (poll-then-capture, ArdOsc
 * pattern from docs/03): watch the live ADC, arm when the signal sits
 * below (trigger level - hysteresis), fire on crossing above the
 * level, then burst-capture. A 250 ms timeout falls back to free-run
 * so the screen never freezes without a signal ("Auto" mode).
 *
 * Wiring: same as M1 (D3 --[10k]--> A7). No new wires.
 * Expected: the square wave now STANDS STILL, and the ghosting that
 * came from untriggered drift disappears with it.
 */

#include <Arduino.h>
#include <U8g2lib.h>

U8G2_T6963_240X128_1_8080 u8g2(U8G2_R0,
  /*DB0..DB7 =*/ 8, 9, 10, 11, 4, 5, 6, 7,
  /*WR=*/ 17, /*CE=*/ 14, /*C-D=*/ 15, /*RST=*/ 16);

#define N_SAMPLES     240
#define TEST_PWM_PIN    3
#define TRIG_LEVEL    128   // mid-scale (2.5 V), 8-bit counts
#define TRIG_HYST       4   // hysteresis band against noise
#define TRIG_TIMEOUT  250   // ms without trigger -> free-run (Auto)

uint8_t samples[N_SAMPLES];
bool triggered = false;

static inline uint8_t adc8(void) {
  return (uint8_t)(analogRead(A7) >> 2);
}

// Poll-then-capture: returns true if a rising edge fired,
// false on timeout (free-run).
bool waitForTrigger(void) {
  unsigned long t0 = millis();
  while (adc8() >= TRIG_LEVEL - TRIG_HYST) {          // arm below level
    if (millis() - t0 > TRIG_TIMEOUT) return false;
  }
  while (adc8() < TRIG_LEVEL + TRIG_HYST) {           // fire above level
    if (millis() - t0 > TRIG_TIMEOUT) return false;
  }
  return true;
}

void capture(void) {
  for (uint16_t i = 0; i < N_SAMPLES; i++) {
    samples[i] = adc8();
  }
}

static inline uint8_t sample_to_y(uint8_t s) {
  return 127 - (s >> 1);
}

void draw(void) {
  const uint8_t trig_y = sample_to_y(TRIG_LEVEL);
  u8g2.firstPage();
  do {
    u8g2.drawFrame(0, 0, 240, 128);
    // trigger-level marker at the left edge
    u8g2.drawHLine(1, trig_y, 6);
    u8g2.drawPixel(7, trig_y - 1);
    u8g2.drawPixel(7, trig_y + 1);
    // waveform
    for (uint16_t x = 1; x < N_SAMPLES; x++) {
      u8g2.drawLine(x - 1, sample_to_y(samples[x - 1]),
                    x,     sample_to_y(samples[x]));
    }
    // status readout, on a cleared box so the trace can't cross it
    u8g2.setDrawColor(0);
    u8g2.drawBox(204, 3, 33, 13);
    u8g2.setDrawColor(1);
    u8g2.setFont(u8g2_font_6x10_tr);
    u8g2.drawStr(207, 13, triggered ? "TRIG" : "FREE");
  } while (u8g2.nextPage());
}

void setup(void) {
  u8g2.begin();
  analogWrite(TEST_PWM_PIN, 128);
}

void loop(void) {
  triggered = waitForTrigger();
  capture();
  draw();
}
