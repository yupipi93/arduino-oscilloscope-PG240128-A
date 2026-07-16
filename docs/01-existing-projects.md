# Research: existing Arduino oscilloscope projects

What's already out there, what they achieved on the same chip we use (ATmega328P), and what we can reuse. Researched July 2026; every claim links its source.

**Headline finding: no public Arduino oscilloscope project targets a T6963C 240×128 display.** The closest precedents are 128×64 GLCD/OLED scopes. Our project ports those proven patterns to a screen four times the area — a genuine gap ([the only trace is a 2012 unanswered forum question](https://forum.arduino.cc/t/oscilloscope-using-t6963/110526)).

## The projects that matter

### Girino — the classic (2012)

Instructable by Cristiano Lino Fontana. Uno-class ATmega328P, no display (streams to a PC). The reference design for **fast capture**: free-running ADC with interrupt, ~154 kSps at 8 bits (prescaler 8), circular buffer with pre-trigger, and a **hardware trigger using the chip's analog comparator** (threshold set by filtered PWM). License GPL-3+.
[Instructable](https://www.instructables.com/Girino-Fast-Arduino-Oscilloscope/) · [firmware + design notes](https://github.com/sangorrin/arduino-oscilloscope) · [Girinoscope PC GUI](https://github.com/Chatanga/Girinoscope)

*For us:* the comparator trigger needs AIN0/AIN1 = **D6/D7, which our display occupies** — so we use software triggering like every display-attached scope below. The circular-buffer/pre-trigger idea remains portable.

### ArdOsc — "Oscilloscope in a Matchbox" (Peter Balch)

**Arduino Nano** + SH1106 OLED. The most complete single write-up for our exact MCU: ranges DC 0–5 V / AC down to ±25 mV (LM358 stages), 7 time bases, software mid-scale trigger with a 250 ms timeout that falls back to free-run, frequency counter, voltmeter on A6, PWM test-signal generator on D3, two-button UI (short press = cycle, hold 1 s = menu). Claims "1 MSps" but honestly documents it as ~250 kSps effective, with the analog path rolling off above ~20 kHz. Zero display framebuffer in RAM — draws in 8-px "swathes" (same concept as U8g2 page mode). GPL.
[Instructable](https://www.instructables.com/Oscilloscope-in-a-Matchbox-Arduino/) · [full-text mirror](https://trybotics.com/project/Oscilloscope-in-a-Matchbox-Arduino-98979) · [rebuild with schematics](https://electronics.qetesh.de/ardosc/)

### Noriaki Mitsunaga's GLCD scope (2009) → GOscillo family

The ancestor of most Arduino scopes: KS0108 128×64 GLCD, 2 channels, 10 s/div–1.2 ms/div, ~8.6 kSps with analogRead, trigger modes **Auto / Normal / Scan / One-shot** ([original page](http://n.mtng.org/ele/arduino/oscillo.html)). Its maintained descendant is **[GOscillo / ArduinoOLEDOscilloscope](https://github.com/siliconvalley4066/ArduinoOLEDOscilloscope)** (GPL-3.0): PROGMEM range tables (1–0.05 V/div), per-range ADC prescaler switching, 33 µs/div real-time plus **equivalent-time sampling to "16 MSps"** on repetitive signals, FFT, pulse/DDS generators — while documenting that above 100 µs/div effective resolution drops below 6 bits and flash sits at 94–99 %.

### richardkuro/arduino-oscilloscope — our closest software template (MIT)

Uno/Nano + SSD1306, **U8g2 in `_1` page-buffer mode** (exactly our stack), ADC prescaler 16 (~13.5 µs/conversion), 128-sample buffer, **KY-040 rotary encoder on D2 (interrupt) + D3 + D4**, freeze button, grid + line-connected trace, text on filled boxes for legibility. MIT license — safe to copy from.
[GitHub](https://github.com/richardkuro/arduino-oscilloscope)

### nitsky/avr-oscilloscope — cleanest trigger engineering (MIT)

Bare-metal ATmega328, 150 kSps free-running 8-bit, **1024-sample circular buffer with the trigger event centered**, and a software edge trigger with a noise filter that requires **8 consecutive samples past the level** before firing. MIT license.
[GitHub](https://github.com/nitsky/avr-oscilloscope)

### Wu Hanqing / mircemk — ST7920 GLCD scope

Nano + 128×64 GLCD, 10 Hz–50 kHz, nine 1-2-5 time-base steps (0.02–10 ms/div), auto trigger, Hold button, and a layout worth copying: **waveform area + side info panel showing frequency and Vpp**; a pot for vertical position.
[Hackaday.io](https://hackaday.io/project/174425-diy-10hz-50khz-arduino-oscilloscope-on-128x64-lcd) · [Hackster mirror](https://www.hackster.io/mircemk/diy-10hz-50khz-oscilloscope-on-128x64-lcd-display-52ecfe)

### Also noted

- [CircuitDigest mini scope](https://circuitdigest.com/microcontroller-projects/diy-mini-oscilloscope-using-arduino-nano) — documented ArdOsc derivative, 76 kSps, mid-scale trigger with ±2-count hysteresis (GPL).
- [Scope-O-Matic](https://github.com/josbouten/Scope-O-Matic) — notes 1 KB ATmega168 is *not* enough RAM; the 328P is the floor.
- [Yourigh/Arduino_Nano_oscilloscope](https://github.com/Yourigh/Arduino_Nano_oscilloscope) — 65 kSps, "memory space maxed out".
- [small-scope](https://github.com/marvin-sinister/small-scope) — Girino derivative + Qt GUI (GPL-3.0).

## Architecture patterns (what everyone converged on)

1. **Capture-then-draw.** Wait for trigger → burst-capture N samples into an 8-bit array → compute Vpp/frequency → redraw the whole screen → repeat. Streaming only makes sense with a PC display.
2. **One sample per pixel column.** 128-px screens use 128-sample buffers. Our 240-px screen ⇒ **240-byte buffer** (or ~200 columns of waveform + a readout panel, GOscillo-style).
3. **Software edge trigger** with (a) hysteresis or a consecutive-samples noise filter, and (b) a **timeout that falls back to free-running** so the screen never silently freezes.
4. **Time base = two mechanisms.** Fast ranges: change the ADC prescaler and capture back-to-back. Slow ranges: timed sampling down to seconds/div. 1-2-5 step sequence.
5. **8-bit samples everywhere fast.** `ADLAR` left-adjust, read `ADCH` only — halves RAM and skips a register read; effective resolution at high speed is <8 bits anyway.
6. **Drawing under 2 KB RAM:** the U8g2 page loop redraws grid + trace + text 16 times per frame, so drawing code must be a *pure function* of the sample buffer and settings — never sample inside the page loop.

## Realistic performance on the ATmega328P (measured by these projects)

| Configuration | Sample rate |
|---|---|
| `analogRead()`, default prescaler 128 | ~9.6 kSps |
| Prescaler 16 (datasheet limit for stated accuracy) | **~77 kSps** ← our fast default |
| Prescaler 8, 8-bit free-running (Girino) | ~154 kSps |
| Prescaler 4, 8-bit (nitsky, Girino max) | ~150–308 kSps |
| ArdOsc "1 MSps" polling loop | ~250 kSps effective |

Practical planning number: **~77 kSps capture ⇒ clean traces to ~5–10 kHz, usable to ~20 kHz** (≈10 samples per period for a recognizable waveform; the analog front-end rolls off before the ADC does at silly prescaler settings).

## Licenses (for code reuse)

MIT (freely reusable): **richardkuro**, **nitsky**. GPL-3: Girino, GOscillo, wayri, ArdOsc, CircuitDigest. We write our own code, using the MIT projects as structural references.

## What this means for our build

- Pin map from the [hello-world guide](00-hello-world-nano.md) works unmodified: probe on **A7**, rotary encoder or buttons on **D2/D3** (interrupts) + D12/D13, exactly the richardkuro pattern.
- Buffer plan: 240 B samples + 240 B U8g2 page buffer + stack ≈ well under 2 KB. Range-label tables in PROGMEM (flash is the scarce resource).
- Feature ladder and details: see the [build plan](04-build-plan.md).
