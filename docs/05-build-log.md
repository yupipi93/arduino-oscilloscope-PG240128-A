# Build log

Real-hardware progress diary. Newest entries first.

## 2026-07-17 — ✅ M3 verified · design fix (D13) · M4 uploaded

**M3 confirmed on hardware**: ~1.6 cycles at the 77 kSps tier, serial time-base control working across all 10 tiers.

**Design fix caught during M4 prep:** the plan had the HOLD button on D13, but the Nano's onboard LED loads that pin (~1.9 V against the internal pull-up = permanent LOW) — a D13 button can never work. **HOLD → D12; the M5 RANGE sense → A4.** Diagrams and docs updated.

**M4 (`firmware/scope_ui/`) compiled (13 240 B flash / 1 129 B RAM) and uploaded**: 200-px waveform + 40-px readout panel (time base, mode, state, Vpp, frequency), dotted graticule, trigger marker, and two buttons — SELECT (D2): short = time base, long = trigger mode AUTO/NORM/ONE; HOLD (D12): freeze / re-arm. Runs without buttons wired (defaults AUTO). Vpp assumes Vcc = 5.00 V until the M5 calibration.

Also added [docs/06-components.md](06-components.md) — the full component list to finish the project (~€3.20 mandatory for M4+M5).

## 2026-07-17 — ✅ M2 verified: the wave stands still · M3 uploaded

**M2 confirmed on hardware**: square wave locked in place, trigger marker and TRIG/FREE readout behaving as designed, and the drift-induced ghosting gone with the stable trace — exactly the predicted fix.

**M3 (`firmware/fast_sampler/`) compiled (11 432 B flash / 1 220 B RAM) and uploaded**: ADC moved to register-level free-running mode with ADLAR (analogRead retired), 10-tier time base from 1.6 ms to 1.2 s per screen (prescaler tiers /8…/128 + micros()-paced slow tiers). Tier selection over serial (115200 baud, `+`/`-`) until the M4 buttons replace it. Default tier: ~77 kSps. Success criterion: ~1.6 cycles of the 490 Hz PWM, still standing, edges one column wide.

## 2026-07-17 — ✅ M1 verified on hardware · M2 uploaded

**M1 works, confirmed with photos.** With `D3 —[10 kΩ]→ A7` bridged:

- PWM test signal: ~13 square-wave cycles across the screen, ~18–19 columns per cycle — matching the math exactly (490 Hz @ ~9.6 kSps → 12.8 cycles/240 columns). Flat tops/bottoms, connected vertical edges.
- Finger-on-the-resistor test: large drifting diagonals/X patterns = **1.25 cycles of 50 Hz mains hum per 25 ms sweep** — the scope's first real-world signal.
- As predicted, the untriggered trace drifts phase every sweep ("dances").

**Ghosting observation:** multiple faint superimposed traces. Two causes: (1) untriggered drift means each refresh lights *different* pixels while the slow STN panel (~150–300 ms pixel decay) still shows the previous ones — fixed by the M2 trigger (stable trace = same pixels every frame); (2) inherent STN pixel persistence — minor once the image is stable; slightly backing off an over-driven contrast pot also reduces smearing.

**M2 (`firmware/triggered_viewer/`) compiled (9 798 B flash / 927 B RAM) and uploaded** — poll-then-capture rising-edge trigger at mid-scale with ±4-count hysteresis, 250 ms auto free-run timeout, trigger-level marker and TRIG/FREE readout. Success criterion: the square wave stands still.

## 2026-07-17 — ✅ M0 complete: hello world running on real hardware

**The display works.** "Hello, PG240128-A!" on screen, contrast dialed in, adjustable backlight lit.

### What was built

- Arduino Nano (clone, CH340 USB chip) wired to the PG240128-A exactly per the [wiring diagram](images/wiring-hello-world.png): 8 data wires (DB0–DB7 → D8–D11, D4–D7), 4 control wires (/CE→A0, C/D→A1, /RST→A2, /WR→A3), /RD strapped to +5 V, FS1 strapped to GND, MD2 left unconnected, 10 kΩ contrast pot between Vdd and Vee with wiper on Vo.
- Powered from USB only — no external supply needed at this stage.

### Toolchain and upload (reproducible)

| Item | Value |
|---|---|
| Detection | CH340 (`1a86:7523`) → `/dev/ttyUSB0`, user in `dialout` |
| Toolchain | arduino-cli 1.5.1 + `arduino:avr` 1.8.8 + U8g2 2.36.19 |
| Firmware | [`firmware/hello_world/`](../firmware/hello_world/hello_world.ino) |
| Compile | 12 050 B flash (39 %), 752 B RAM (36 %) — page-buffer mode leaves ~1.3 KB free, as budgeted |
| Upload | `arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:nano:cpu=atmega328old` — **old bootloader**, worked first try |

```bash
arduino-cli compile --fqbn arduino:avr:nano:cpu=atmega328old firmware/hello_world
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:nano:cpu=atmega328old firmware/hello_world
```

### Things the hardware confirmed

- **Contrast pot is truly mandatory**: image appears only in a narrow band of the pot's travel, exactly as researched. The display worked before the backlight was even connected (readable under ambient light).
- **Old-bootloader profile** is the right default for CH340 clones.
- RAM/flash budget matches the [build plan](04-build-plan.md) predictions.

### Deviation from the plan: adjustable backlight 🔧

Instead of the fixed 12 Ω / 0.5 W resistor, the backlight is fed through a **multiturn trimmer** — brightness is now adjustable, and it works great.

⚠️ One caution for anyone copying this: a trimmer dialed to its low extreme approaches **0 Ω = no current limiting**, which can burn the backlight LEDs (and stress USB). Recommended practice: keep a small **fixed resistor (≈10 Ω) in series** with the trimmer so the minimum can never go below safe, or simply never wind the trimmer fully down. The fixed 12 Ω of the diagram remains the fool-proof default.

### Next

**M1 — static waveform viewer**: `analogRead(A7)` into the 240-byte buffer, drawn as connected lines, fed by the Nano's own PWM (`analogWrite(3, 128)`, ~490 Hz square) through a 10 kΩ resistor into A7. Success = a square wave scrolling on screen.
