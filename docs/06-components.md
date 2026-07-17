# Components: everything needed to finish the project

Complete, milestone-by-milestone component list from here (M3 done) to the finished oscilloscope. Prices are single-unit hobby prices (AliExpress / local shop / TME, 2026); most small parts come in the classic Arduino starter kits you may already own.

## ✅ Already on the bench (M0–M3, verified working)

| Part | Role |
|---|---|
| Arduino Nano (ATmega328P, CH340) | the brain |
| PG240128-A display | the screen |
| 10 kΩ potentiometer | contrast (Vdd↔Vee, wiper→Vo) |
| Multiturn trimmer (+ recommended ~10 Ω fixed in series) | adjustable backlight |
| 10 kΩ resistor | test-signal / probe series protection |
| Breadboard, dupont wires, mini-USB cable | infrastructure |

---

## M4 — UI: 2 pushbuttons (~€0.20)

### 1. Momentary pushbutton, 6×6 mm THT ("tactile switch") — ×2

- **Exact thing to buy:** 6×6 mm through-hole tactile switches, any height. They have 4 legs in 2 internally-joined pairs — on a breadboard, straddle the center groove and use diagonal legs and you can't get it wrong.
- **Role:** SELECT → D2 (short press = time base, long press = trigger mode) and HOLD → D12 (freeze / re-arm).
- **No resistors needed** — the firmware enables the Nano's internal pull-ups; the button just shorts the pin to GND.
- **Substitutes:** any momentary NO button; every starter kit has a bag of these. ~€0.10 each.

---

## M5 — Analog front-end (core ~€3, all passive)

The front-end gives three input ranges (0–5 V DC, ±2.5 V AC, ±20 V DC) with protection. Circuit details and schematics: [docs/03](03-analog-front-end-and-trigger.md).

### 2. Resistors, 0.25 W metal film (1 % where noted)

| Value | Qty | Circuit role |
|---|---|---|
| 10 kΩ | 1 (have) +1 spare | series protection right before A7 — the last line of defense |
| 100 kΩ 1 % | 2 | mid-rail bias divider (2.5 V) for the AC-coupled range |
| 470 kΩ 1 % | 1 | input resistor of the ±20 V network — sets the 1 mA fault-current limit and the input impedance |
| 150 kΩ 1 % | 1 | ±20 V network, pull toward GND |
| 120 kΩ 1 % | 1 | ±20 V network, pull toward +5 V |

Why 1 %: these three resistors *are* the ×10 scale factor — 5 % tolerance would put ~±8 % error on every voltage reading before calibration. A 1 % metal-film assortment costs ~€5 and lasts years.

### 3. Schottky diodes BAT85 — ×2

- **Role:** clamp the A7 node to +5 V and GND before the chip's internal diodes ever conduct (Schottky forward drop ≈0.3 V < 0.6 V internal).
- **Substitutes:** BAT42/BAT43 fine; **1N4148 acceptable** (clamps slightly outside the rails but still protective). Avoid SMD BAT54 on a breadboard.
- ~€0.05 each.

### 4. Film capacitor 1 µF, ≥63 V (MKT/MKS box type) — ×1

- **Role:** AC coupling — blocks DC so audio/AC signals can be viewed centered on screen. With the 100k‖100k bias it gives a 3.2 Hz corner.
- **Why film and not electrolytic:** no polarity (the signal swings both ways), no leakage, no aging. **Why ≥63 V:** the cap's rating is what protects you when probing DC-offset signals on the AC range.
- ~€0.30.

### 5. Ceramic capacitors 100 nF — ×2

- **Role:** one quiets the 2.5 V bias node; one as reservoir at the A7 pin (helps the ADC's sample capacitor with high-impedance sources).
- The most common capacitor on Earth (~€0.02, marked "104").

### 6. Slide switches SPDT, 2.54 mm pitch — ×2

- **Role:** one selects **×1 / ×10** (which network feeds A7 — its position is read by the firmware on A4), one selects **AC / DC** (bypass or engage the 1 µF cap).
- **Substitutes:** any SPDT toggle; even jumper links work while prototyping (that's how we'll test before buying).
- ~€0.40 each.

### 7. Stripboard/perfboard + male pin headers

- **Role:** M5's goal is moving the front-end from breadboard chaos to a small permanent board with labeled posts (PROBE, GND, CAL) that plugs next to the Nano.
- ~€1.50 for a 5×7 cm board + a strip of headers.

### Optional but nice (M5)

| Part | Why | ~€ |
|---|---|---|
| Trimmer capacitor 5–30 pF | frequency-compensates the ×10 divider above ~10 kHz (square corners on square waves) | 0.50 |
| MCP6002 (DIP-8, rail-to-rail op-amp) | buffers high-impedance dividers, enables millivolt ranges later. **Do not substitute LM358** — its output can't reach within 1.5 V of Vcc | 0.50 |
| **P6100 oscilloscope probe (10:1/1:1)** | the single best upgrade: 10 MΩ loading, compensated, insulated, rated. Pair with a **BNC female socket** (panel or PCB) | 12 + 1 |

---

## M6 — Extras (all optional)

| Part | Role | ~€ |
|---|---|---|
| 10 kΩ + 2× BAT85 (repeat of #2/#3) | minimal second channel into A6 | 0.15 |
| KY-040 rotary encoder — **threaded-bushing version** (M7 thread + nut, for panel-mounting in the M6 case; add a push-on knob) | nicer UI than buttons (D2/D3 interrupts) — only if you want it; costs the D3 test-signal pin | 1 |
| 3D-printed case | mechanical polish — no purchase, just filament | — |

Pre-trigger, PC streaming and equivalent-time sampling are **pure software** — zero components.

---

## Tools (not components, but you'll want them)

- **Multimeter** — required once, for the M5 calibration procedure (measure real Vcc and 3V3).
- **Phone + signal-generator app + sacrificial jack cable** — free function generator for testing the AC range (M3/M5 success criterion: a clean 5 kHz sine).
- **Soldering iron** — only for the M5 stripboard step.

---

## Consolidated buy list

| # | Item | Qty | Milestone | Required? | ~€ total |
|---|---|---|---|---|---|
| 1 | Tactile pushbutton 6×6 mm | 2 | M4 | **yes** | 0.20 |
| 2 | 100 kΩ 1 % | 2 | M5 | **yes** | 0.04 |
| 3 | 470 kΩ / 150 kΩ / 120 kΩ 1 % | 1+1+1 | M5 | **yes** | 0.06 |
| 4 | 10 kΩ 0.25 W | 1 spare | M5/M6 | yes | 0.02 |
| 5 | BAT85 (or 1N4148) | 2 (+2 for M6) | M5 | **yes** | 0.20 |
| 6 | 1 µF ≥63 V film | 1 | M5 | **yes** | 0.30 |
| 7 | 100 nF ceramic | 2 | M5 | **yes** | 0.04 |
| 8 | SPDT slide switch | 2 | M5 | **yes** | 0.80 |
| 9 | Stripboard + headers | 1 | M5 | **yes** | 1.50 |
| 10 | Trimmer cap 5–30 pF | 1 | M5 | optional | 0.50 |
| 11 | MCP6002 DIP-8 | 1 | M5 | optional | 0.50 |
| 12 | P6100 probe + BNC socket | 1 | M5 | recommended | 13 |
| 13 | KY-040 encoder | 1 | M6 | optional | 1 |

**Bottom line: ~€3.20 of mandatory parts finish M4+M5. ~€18 including the probe and all options.** Everything except the probe/BNC is standard starter-kit material.
