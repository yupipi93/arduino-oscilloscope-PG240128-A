# Build plan: the oscilloscope, step by step

Synthesis of the research ([projects](01-existing-projects.md) · [ADC](02-adc-and-sampling.md) · [front-end](03-analog-front-end-and-trigger.md)) into a concrete, ordered plan. Each milestone is small, testable, and leaves a working device.

## Target specification (realistic, research-backed)

| Item | Target |
|---|---|
| Channels | 1 (A7), expandable to 2 (A6) |
| Sample rate | 77 kSps max (8-bit, free-running ADC, prescaler 16) |
| Usable bandwidth | ~5–10 kHz clean, ~20 kHz visible |
| Time base | 1-2-5 steps, ~50 µs/div … 1 s/div |
| Vertical | ×1: 0–5 V (DC) / ±2.5 V (AC) · ×10: ±20 V |
| Trigger | software rising/falling edge, hysteresis, auto free-run timeout, Hold |
| Display layout | ~200×128 waveform area + right-side readout panel (V/div, t/div, trigger, Vpp, freq) |
| Controls | rotary encoder on D2/D3 + its button, or 3–4 buttons |
| Extra | PWM test-signal output on D3 for self-testing |

Novelty check: **no public Arduino scope uses a T6963C 240×128** — this will likely be the first documented one.

## Complete pin budget (nothing left to chance)

| Nano pin | Use |
|---|---|
| D0/D1 | USB serial (debug, PC streaming later) |
| **D2, D3** | rotary encoder A/B (both are hardware interrupts) — or 2 buttons. D3 doubles as PWM test-signal out if buttons go elsewhere |
| D4–D11 | display data bus DB4–DB7 + DB0–DB3 (see [hello world](00-hello-world-nano.md)) |
| **D12, D13** | encoder push-button / Hold button / range-switch sense |
| A0–A3 | display /CE, C/D, /RST, /WR |
| A4, A5 | free (I²C reserved — future RTC/expander) |
| **A6** | second channel / trigger-level trimmer / ±20 V voltmeter network |
| **A7** | **the probe input** |

Known trade-off (documented, deliberate): the on-chip analog comparator (hardware trigger) lives on D6/D7 which the display uses → software trigger, like ArdOsc and every display-attached scope.

## RAM budget (the 2 KB reality)

| Consumer | Bytes |
|---|---|
| Sample buffer (240 × 8-bit, one per column) | 240 |
| U8g2 page buffer (`_1_` mode) | 240 |
| U8g2 structure | ~100 |
| Serial buffers (2×64) + stack + globals | ~400 |
| **Total ≈** | **~1000 → comfortable** |

Rules learned from projects that hit the wall: all string/range tables in **PROGMEM**, no `String` class, drawing code = pure function of (buffer, settings).

## Architecture (the loop)

```
        ┌──────────────────────────────────────────────┐
        │ 1. read controls (encoder/buttons)           │
        │ 2. wait for trigger (poll ADC, timeout 250ms)│
        │ 3. burst-capture 240 samples  ── ADC only ── │
        │ 4. measure: Vmin/Vmax/Vpp, period → freq     │
        │ 5. draw: grid + trace + panel ── LCD only ── │
        │    (U8g2 firstPage/nextPage ×16)             │
        └──────────────────────────────────────────────┘
```

Sampling and drawing never overlap (12 GPIOs toggling would pollute the ADC). At 16 page passes per frame expect ~5–10 fps screen refresh — normal for this class of scope.

## Milestones

### ✅ M0 — Hello world ([done — the guide](00-hello-world-nano.md))
Display wired with the scope-ready pin map, U8g2 page mode running.

### M1 — Static waveform viewer
`analogRead(A7)` into the 240-byte buffer with no trigger, draw buffer as connected lines + border. Feed it the Nano's own PWM (`analogWrite(3, 128)` = 490 Hz square) through Design A (10 kΩ into A7). **Success: a square wave scrolls by.**

### M2 — Trigger
Poll-then-capture rising-edge trigger with hysteresis + 250 ms auto free-run. **Success: the square wave stands still.**

### M3 — Fast sampling
Free-running ADC, prescaler 16, ADLAR, polled burst capture; two-tier time base (prescaler tiers + timed slow tiers), 1-2-5 steps. **Success: a 5 kHz sine from a phone signal-generator app (through Design B) displays cleanly.**

### M4 — UI
Grid/graticule, right-side readout panel (V/div, t/div, trigger mode/level marker, Vpp, frequency), encoder/buttons: time base, trigger level, Hold, single-shot. Modes Auto/Normal/One (Mitsunaga vocabulary).

### M5 — Front-end board
Breadboard → stripboard: Designs A+B+C with the ×1/×10 switch and AC/DC switch, calibration procedure (bandgap Vcc + two-point), safe-limits label.

### M6 — Polish (pick and choose)
Second channel on A6 · pre-trigger capture (circular buffer) · PC streaming over serial · equivalent-time sampling for repetitive signals (GOscillo's 16 MSps-equivalent trick) · 3D-printed case.

## Code reuse policy

Structural references: **richardkuro/arduino-oscilloscope** and **nitsky/avr-oscilloscope** (both MIT — compatible with this repo's license). GPL projects (Girino, GOscillo, ArdOsc) are read for *ideas only*; we write our own implementation.
