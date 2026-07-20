/*
 * M4 — Scope UI: buttons, graticule, measurements panel
 *
 * Layout: 200x128 waveform area (one sample per column) + 40 px
 * right-side panel with time base, trigger mode/state, Vpp and
 * frequency (GOscillo / Wu Hanqing convention, docs/01).
 *
 * Controls (to GND, internal pull-ups — no resistors), scope naming:
 *   SEC/DIV + = D2   short press: slower sweep (zoom out)
 *                    long press (>0.7 s): trigger mode AUTO -> NORM -> ONE
 *   SEC/DIV - = D12  short press: faster sweep (zoom in)
 *                    long press (>0.7 s): RUN/STOP (freeze display;
 *                                         in ONE mode: re-arm the shot)
 *   (D13 is NOT usable as a button: the onboard LED defeats the pull-up.)
 *
 * Trigger modes (Mitsunaga vocabulary, docs/01):
 *   AUTO  trigger if present, free-run after 250 ms without one
 *   NORM  only redraws on trigger (screen keeps last capture)
 *   ONE   arms, captures a single sweep on trigger, then holds
 *
 * Vertical: continuous auto-scale — each frame maps the captured
 * min..max to the screen with a 6-px margin, so any amplitude fills
 * the display (the true amplitude is the Vpp readout). Small ranges
 * are clamped (>=0.2 V) so flat/DC signals don't amplify noise.
 *
 * Vcc calibration ("secret voltmeter", docs/02): the internal 1.1 V
 * bandgap is measured against AVcc to compute the real supply voltage,
 * so Vpp uses true millivolts instead of assuming 5.00 V. The boot
 * splash shows the measured Vcc; refine once with a multimeter by
 * scaling BANDGAP_MV: new = 1100 * (Vcc_meter / Vcc_displayed).
 *
 * Runs fine with no buttons wired (defaults: AUTO, ~74 kSps tier).
 * Wiring: docs/images/wiring-m4-ui-buttons.png
 * Vpp assumes Vcc = 5.00 V — calibration arrives in M5 (docs/03).
 */

#include <Arduino.h>
#include <U8g2lib.h>

U8G2_T6963_240X128_1_8080 u8g2(U8G2_R0,
  /*DB0..DB7 =*/ 8, 9, 10, 11, 4, 5, 6, 7,
  /*WR=*/ 17, /*CE=*/ 14, /*C-D=*/ 15, /*RST=*/ 16);

#define N_SAMPLES   200          // one per waveform column (0..199)
#define PANEL_X     200
#define TEST_PWM_PIN  3
#define BTN_SDIV_PLUS   2   // SEC/DIV +
#define BTN_SDIV_MINUS 12   // SEC/DIV -
#define TRIG_LEVEL  128
#define TRIG_HYST     4
#define LONG_PRESS  700          // ms
#define BANDGAP_MV 1100UL        // this chip's bandgap; calibrate with a
                                 // multimeter: new = 1100 * Vmeter/Vshown
#define VCC_PERIOD 5000          // remeasure Vcc every 5 s

// ---- time base ---------------------------------------------------------
// us10 = sample period in 0.1 us units (for frequency math).
struct Tier {
  uint8_t adps;                  // burst prescaler bits, 0 = timed mode
  uint16_t us;                   // timed mode: sample period (us)
  uint16_t us10;                 // sample period in 0.1 us
  const char *label;             // full-screen window
};
#define PS(n) (n)
const Tier TIERS[] = {
  { _BV(ADPS1) | _BV(ADPS0),              0,    68, "1.4ms" },  // /8
  { _BV(ADPS2),                           0,   135, "2.7ms" },  // /16
  { _BV(ADPS2) | _BV(ADPS0),              0,   270, "5.4ms" },  // /32
  { _BV(ADPS2) | _BV(ADPS1),              0,   540, " 11ms" },  // /64
  { _BV(ADPS2) | _BV(ADPS1) | _BV(ADPS0), 0,  1080, " 22ms" },  // /128
  { 0,  250,  2500, " 50ms" },
  { 0,  500,  5000, " 0.1s" },
  { 0, 1000, 10000, " 0.2s" },
  { 0, 2000, 20000, " 0.4s" },
  { 0, 5000, 50000, " 1.0s" },
};
const uint8_t N_TIERS = sizeof(TIERS) / sizeof(TIERS[0]);
#define ADPS_128 (_BV(ADPS2) | _BV(ADPS1) | _BV(ADPS0))

// ---- state -------------------------------------------------------------
enum { MODE_AUTO, MODE_NORM, MODE_ONE };
const char *MODE_NAMES[] = { "AUTO", "NORM", "ONE" };

uint8_t  samples[N_SAMPLES];
uint8_t  tier = 1;               // ~74 kSps
uint8_t  trigMode = MODE_AUTO;
bool     hold = false;
bool     triggered = false;
uint16_t vcc_mV = 5000;          // measured supply voltage (the "ruler")
uint16_t vpp_cv = 0;             // Vpp in centivolts
uint32_t freq_hz = 0;            // 0 = unknown
uint8_t  v_mn = 0, v_mx = 255;   // capture min/max (vertical auto-scale)

// Measure Vcc via the internal 1.1 V bandgap: ADC input = bandgap,
// reference = AVcc  ->  Vcc = BANDGAP_MV * 1023 / reading.
uint16_t readVccmV(void) {
  ADCSRA = _BV(ADEN) | _BV(ADPS2) | _BV(ADPS1) | _BV(ADPS0);  // /128, single
  ADMUX  = _BV(REFS0) | 0x0E;          // AVcc reference, MUX=1110 = bandgap
  delay(3);                            // let the bandgap + S/H settle
  uint32_t acc = 0;
  for (uint8_t i = 0; i < 8; i++) {
    ADCSRA |= _BV(ADSC);
    while (ADCSRA & _BV(ADSC)) ;
    uint16_t v = ADCL;                 // ADCL first, then ADCH (10-bit)
    v |= (uint16_t)ADCH << 8;
    if (i >= 2) acc += v;              // discard the first two readings
  }
  return (uint32_t)(BANDGAP_MV * 1023UL) / (acc / 6);
}

// ---- ADC (registers only, free-running, 8-bit ADLAR) --------------------
void adcInit(uint8_t adps) {
  ADCSRA = 0;
  ADMUX  = _BV(REFS0) | _BV(ADLAR) | 0x07;   // AVcc, left-adjust, ADC7
  ADCSRB = 0;
  DIDR0  = 0x3F;
  ADCSRA = _BV(ADEN) | _BV(ADATE) | _BV(ADSC) | adps;
  while (!(ADCSRA & _BV(ADIF)));
  ADCSRA |= _BV(ADIF);
}

static inline uint8_t adcNext(void) {
  while (!(ADCSRA & _BV(ADIF)));
  ADCSRA |= _BV(ADIF);
  return ADCH;
}

static inline bool anyButtonDown(void) {
  return !digitalRead(BTN_SDIV_PLUS) || !digitalRead(BTN_SDIV_MINUS);
}

// 1 = triggered, 0 = timeout, -1 = button pressed (abort, keep screen)
int8_t waitForTrigger(uint16_t timeout_ms) {
  unsigned long t0 = millis();
  uint8_t n = 0;
  while (adcNext() >= TRIG_LEVEL - TRIG_HYST) {
    if (++n == 0 && anyButtonDown()) return -1;
    if (millis() - t0 > timeout_ms) return 0;
  }
  while (adcNext() < TRIG_LEVEL + TRIG_HYST) {
    if (++n == 0 && anyButtonDown()) return -1;
    if (millis() - t0 > timeout_ms) return 0;
  }
  return 1;
}

void capture(void) {
  const Tier &t = TIERS[tier];
  if (t.adps) {
    for (uint16_t i = 0; i < N_SAMPLES; i++) samples[i] = adcNext();
  } else {
    unsigned long next = micros();
    for (uint16_t i = 0; i < N_SAMPLES; i++) {
      while ((long)(micros() - next) < 0) ;
      next += t.us;
      samples[i] = ADCH;
    }
  }
}

// ---- measurements -------------------------------------------------------
void measure(void) {
  uint8_t mn = 255, mx = 0;
  for (uint16_t i = 0; i < N_SAMPLES; i++) {
    if (samples[i] < mn) mn = samples[i];
    if (samples[i] > mx) mx = samples[i];
  }
  vpp_cv = (uint16_t)((uint32_t)(mx - mn) * vcc_mV / 2560);
  v_mn = mn;
  v_mx = mx;

  // rising-edge crossings with hysteresis -> frequency
  int16_t first = -1, last = -1;
  uint8_t crossings = 0;
  bool below = samples[0] < TRIG_LEVEL - TRIG_HYST;
  for (uint16_t i = 1; i < N_SAMPLES; i++) {
    if (below && samples[i] >= TRIG_LEVEL + TRIG_HYST) {
      below = false;
      if (first < 0) first = i; else last = i;
      crossings++;
    } else if (samples[i] < TRIG_LEVEL - TRIG_HYST) {
      below = true;
    }
  }
  if (crossings >= 2) {
    uint32_t span_0p1us = (uint32_t)(last - first) * TIERS[tier].us10;
    freq_hz = (uint32_t)(crossings - 1) * 10000000UL / span_0p1us;
  } else {
    freq_hz = 0;
  }
}

// ---- buttons ------------------------------------------------------------
struct Btn {
  uint8_t pin;
  bool down;
  bool longFired;
  unsigned long tChange, tDown;
};
Btn btnSel  = { BTN_SDIV_PLUS,  false, false, 0, 0 };
Btn btnHold = { BTN_SDIV_MINUS, false, false, 0, 0 };

// Explicit prototype: the .ino preprocessor would otherwise hoist an
// auto-generated one above the Btn struct definition and fail to build.
void pollBtn(Btn &b, void (*onShort)(), void (*onLong)(), bool fireOnPress);

void selShort(void)  { tier = (tier + 1) % N_TIERS; }              // zoom out
void holdShort(void) { tier = (tier + N_TIERS - 1) % N_TIERS; }    // zoom in
void selLong(void)   {
  trigMode = (trigMode + 1) % 3;
  hold = false;                        // mode change resets hold/arm
}
void holdLong(void)  {
  if (trigMode == MODE_ONE) hold = false;   // re-arm the single shot
  else                      hold = !hold;
}

void pollBtn(Btn &b, void (*onShort)(), void (*onLong)(), bool fireOnPress) {
  bool raw = !digitalRead(b.pin);
  unsigned long now = millis();
  if (raw != b.down && now - b.tChange > 30) {
    b.down = raw;
    b.tChange = now;
    if (raw) {
      b.tDown = now;
      b.longFired = false;
      if (fireOnPress) onShort();
    } else if (!fireOnPress && !b.longFired) {
      onShort();
    }
  }
  if (b.down && !b.longFired && onLong && now - b.tDown > LONG_PRESS) {
    b.longFired = true;
    onLong();
  }
}

void handleButtons(void) {
  pollBtn(btnSel,  selShort,  selLong,  false);  // short on release, long on hold
  pollBtn(btnHold, holdShort, holdLong, false);
}

// ---- drawing ------------------------------------------------------------
// Vertical auto-scale: map [scaleLo .. scaleLo+scaleRng] to y 121..6.
uint8_t scaleLo = 0, scaleRng = 255;

void updateScale(void) {
  uint8_t lo = v_mn;
  uint16_t rng = v_mx - v_mn;
  if (rng < 10) {                    // clamp: >=0.2 V so DC doesn't zoom noise
    uint8_t mid = lo + rng / 2;
    lo  = (mid > 5) ? mid - 5 : 0;
    if (lo > 245) lo = 245;
    rng = 10;
  }
  scaleLo  = lo;
  scaleRng = rng;
}

static inline uint8_t sample_to_y(uint8_t s) {
  int16_t rel = (int16_t)s - scaleLo;
  if (rel < 0) rel = 0;
  if (rel > (int16_t)scaleRng) rel = scaleRng;
  return 6 + (uint8_t)((uint32_t)(scaleRng - rel) * 115 / scaleRng);
}

const char *statusText(void) {
  if (hold)      return "STOP";
  if (triggered) return "TRIG";
  if (trigMode == MODE_AUTO) return "FREE";
  return trigMode == MODE_ONE ? "ARM" : "WAIT";
}

void draw(void) {
  char vbuf[8], fbuf[8];
  snprintf(vbuf, sizeof(vbuf), "%u.%02uV", vpp_cv / 100, vpp_cv % 100);
  if (freq_hz == 0)            strcpy(fbuf, "---");
  else if (freq_hz < 1000)     snprintf(fbuf, sizeof(fbuf), "%luHz", freq_hz);
  else if (freq_hz < 100000)   snprintf(fbuf, sizeof(fbuf), "%lu.%luk",
                                        freq_hz / 1000, (freq_hz % 1000) / 100);
  else                         strcpy(fbuf, ">99k");

  updateScale();
  const bool trig_visible = TRIG_LEVEL >= scaleLo &&
                            TRIG_LEVEL <= scaleLo + scaleRng;
  const uint8_t trig_y = sample_to_y(TRIG_LEVEL);

  u8g2.firstPage();
  do {
    // graticule: dotted verticals every 25 px, horizontals at 32/64/96
    for (uint8_t gx = 25; gx < PANEL_X; gx += 25)
      for (uint8_t gy = 2; gy < 128; gy += 4)
        u8g2.drawPixel(gx, gy);
    for (uint8_t gy = 32; gy <= 96; gy += 32)
      for (uint8_t gx = 2; gx < PANEL_X; gx += 4)
        u8g2.drawPixel(gx, gy);

    // frame + panel divider
    u8g2.drawFrame(0, 0, 240, 128);
    u8g2.drawVLine(PANEL_X, 0, 128);

    // trigger-level marker (only when the level is inside the view)
    if (trig_visible) {
      u8g2.drawHLine(1, trig_y, 5);
      u8g2.drawPixel(6, trig_y - 1);
      u8g2.drawPixel(6, trig_y + 1);
    }

    // waveform
    for (uint16_t x = 1; x < N_SAMPLES; x++) {
      u8g2.drawLine(x - 1, sample_to_y(samples[x - 1]),
                    x,     sample_to_y(samples[x]));
    }

    // right panel
    u8g2.setFont(u8g2_font_6x10_tr);
    u8g2.drawStr(204, 12,  TIERS[tier].label);
    u8g2.drawStr(204, 24,  "/scr");
    u8g2.drawStr(204, 46,  MODE_NAMES[trigMode]);
    u8g2.drawStr(204, 58,  statusText());
    u8g2.drawStr(204, 70,  "Vauto");
    u8g2.drawStr(204, 84,  "Vpp");
    u8g2.drawStr(204, 96,  vbuf);
    u8g2.drawStr(204, 112, "freq");
    u8g2.drawStr(204, 124, fbuf);
  } while (u8g2.nextPage());
}

// ---- main ---------------------------------------------------------------
void drawSplash(void) {
  char buf[24];
  snprintf(buf, sizeof(buf), "Vcc = %u.%02u V", vcc_mV / 1000,
           (vcc_mV % 1000) / 10);
  u8g2.firstPage();
  do {
    u8g2.setFont(u8g2_font_ncenB14_tr);
    u8g2.drawStr(40, 50, "PG240128-A scope");
    u8g2.setFont(u8g2_font_7x13_tr);
    u8g2.drawStr(40, 74, buf);
    u8g2.setFont(u8g2_font_6x10_tr);
    u8g2.drawStr(40, 92, "bandgap-calibrated supply");
    u8g2.drawFrame(0, 0, 240, 128);
  } while (u8g2.nextPage());
}

void setup(void) {
  pinMode(BTN_SDIV_PLUS,  INPUT_PULLUP);
  pinMode(BTN_SDIV_MINUS, INPUT_PULLUP);
  u8g2.begin();
  analogWrite(TEST_PWM_PIN, 128);
  vcc_mV = readVccmV();
  drawSplash();
  delay(2000);
}

void loop(void) {
  static unsigned long tVcc = 0;
  handleButtons();
  if (millis() - tVcc > VCC_PERIOD) {   // track the supply as it drifts
    tVcc = millis();
    vcc_mV = readVccmV();
  }
  if (!hold) {
    adcInit(TIERS[tier].adps ? TIERS[tier].adps : ADPS_128);
    int8_t t = waitForTrigger(trigMode == MODE_AUTO ? 250 : 150);
    if (t < 0) return;                       // button: handle next pass
    if (t == 1 || trigMode == MODE_AUTO) {
      triggered = (t == 1);
      capture();
      measure();
      if (trigMode == MODE_ONE && t == 1) hold = true;   // single shot done
    } else {
      triggered = false;                     // NORM/ONE: keep last capture
    }
  }
  draw();
}
