/*
 * M3 — Fast sampling: free-running ADC, selectable time base
 *
 * The ADC now runs in free-running mode with ADLAR (8-bit reads from
 * ADCH) and a per-tier prescaler — up to ~148 kSps burst capture,
 * ~77 kSps at the default tier (docs/02). Slow tiers pace the same
 * free-running stream with micros(). analogRead() is gone.
 *
 * Time base: 10 tiers (full-screen window 1.6 ms ... 1.2 s).
 * Until the M4 buttons arrive, select it over SERIAL (115200 baud):
 *   send '+' = faster, '-' = slower. Current tier shows on screen.
 *
 * Wiring: same as M1/M2 (D3 --[10k]--> A7). No new wires.
 * Expected at the default tier: ~1.6 cycles of the 490 Hz PWM,
 * standing still, edges one column wide.
 */

#include <Arduino.h>
#include <U8g2lib.h>

U8G2_T6963_240X128_1_8080 u8g2(U8G2_R0,
  /*DB0..DB7 =*/ 8, 9, 10, 11, 4, 5, 6, 7,
  /*WR=*/ 17, /*CE=*/ 14, /*C-D=*/ 15, /*RST=*/ 16);

#define N_SAMPLES     240
#define TEST_PWM_PIN    3
#define TRIG_LEVEL    128
#define TRIG_HYST       4
#define TRIG_TIMEOUT  250   // ms

uint8_t samples[N_SAMPLES];
bool triggered = false;

// ---- time-base table -------------------------------------------------
// adps != 0: burst capture at that ADC prescaler (13.5 ADC clocks/sample)
// adps == 0: free-run at /128, take one sample every `us` microseconds
struct Tier {
  uint8_t adps;          // ADPS2:0 bits, or 0 for timed mode
  uint16_t us;           // timed mode: sample period in us
  const char *label;     // full-screen window, shown on the display
};
const Tier TIERS[] = {
  { _BV(ADPS1) | _BV(ADPS0),               0, "1.6ms" },   // /8   ~148 kSps
  { _BV(ADPS2),                            0, "3.2ms" },   // /16   ~77 kSps
  { _BV(ADPS2) | _BV(ADPS0),               0, "6.5ms" },   // /32   ~38 kSps
  { _BV(ADPS2) | _BV(ADPS1),               0, " 13ms" },   // /64   ~19 kSps
  { _BV(ADPS2) | _BV(ADPS1) | _BV(ADPS0),  0, " 26ms" },   // /128 ~9.6 kSps
  { 0,  250, " 60ms" },
  { 0,  500, "120ms" },
  { 0, 1000, "240ms" },
  { 0, 2000, "0.5s " },
  { 0, 5000, "1.2s " },
};
const uint8_t N_TIERS = sizeof(TIERS) / sizeof(TIERS[0]);
uint8_t tier = 1;                                  // default: ~77 kSps

// ---- ADC, registers only (docs/02) -----------------------------------
#define ADPS_128 (_BV(ADPS2) | _BV(ADPS1) | _BV(ADPS0))

void adcInit(uint8_t adps) {
  ADCSRA = 0;
  ADMUX  = _BV(REFS0) | _BV(ADLAR) | 0x07;   // AVcc, left-adjust, ADC7
  ADCSRB = 0;                                // free-running
  DIDR0  = 0x3F;                             // digital buffers off, A0-A5
  ADCSRA = _BV(ADEN) | _BV(ADATE) | _BV(ADSC) | adps;
  while (!(ADCSRA & _BV(ADIF)));             // discard first conversion
  ADCSRA |= _BV(ADIF);
}

static inline uint8_t adcNext(void) {        // blocking: next fresh sample
  while (!(ADCSRA & _BV(ADIF)));
  ADCSRA |= _BV(ADIF);
  return ADCH;
}

bool waitForTrigger(void) {
  unsigned long t0 = millis();
  while (adcNext() >= TRIG_LEVEL - TRIG_HYST)
    if (millis() - t0 > TRIG_TIMEOUT) return false;
  while (adcNext() < TRIG_LEVEL + TRIG_HYST)
    if (millis() - t0 > TRIG_TIMEOUT) return false;
  return true;
}

void capture(void) {
  const Tier &t = TIERS[tier];
  if (t.adps) {                              // burst at ADC speed
    for (uint16_t i = 0; i < N_SAMPLES; i++) samples[i] = adcNext();
  } else {                                   // paced by micros()
    unsigned long next = micros();
    for (uint16_t i = 0; i < N_SAMPLES; i++) {
      while ((long)(micros() - next) < 0) ;
      next += t.us;
      samples[i] = ADCH;                     // latest completed conversion
    }
  }
}

// ---- drawing ----------------------------------------------------------
static inline uint8_t sample_to_y(uint8_t s) { return 127 - (s >> 1); }

void draw(void) {
  const uint8_t trig_y = sample_to_y(TRIG_LEVEL);
  u8g2.firstPage();
  do {
    u8g2.drawFrame(0, 0, 240, 128);
    u8g2.drawHLine(1, trig_y, 6);
    u8g2.drawPixel(7, trig_y - 1);
    u8g2.drawPixel(7, trig_y + 1);
    for (uint16_t x = 1; x < N_SAMPLES; x++) {
      u8g2.drawLine(x - 1, sample_to_y(samples[x - 1]),
                    x,     sample_to_y(samples[x]));
    }
    u8g2.setDrawColor(0);
    u8g2.drawBox(146, 3, 91, 13);
    u8g2.setDrawColor(1);
    u8g2.setFont(u8g2_font_6x10_tr);
    u8g2.drawStr(149, 13, TIERS[tier].label);
    u8g2.drawStr(186, 13, "scr");
    u8g2.drawStr(210, 13, triggered ? "TRIG" : "FREE");
  } while (u8g2.nextPage());
}

// ---- serial time-base control (replaced by buttons in M4) --------------
void pollSerial(void) {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '+' && tier > 0)           tier--;
    if (c == '-' && tier < N_TIERS - 1) tier++;
    if (c == '+' || c == '-') {
      Serial.print(F("time base: "));
      Serial.print(TIERS[tier].label);
      Serial.println(F(" per screen"));
    }
  }
}

void setup(void) {
  Serial.begin(115200);
  Serial.println(F("M3 fast sampler — send + or - to change time base"));
  u8g2.begin();
  analogWrite(TEST_PWM_PIN, 128);
  adcInit(TIERS[tier].adps ? TIERS[tier].adps : ADPS_128);
}

void loop(void) {
  pollSerial();
  adcInit(TIERS[tier].adps ? TIERS[tier].adps : ADPS_128);
  triggered = waitForTrigger();
  capture();
  draw();
}
