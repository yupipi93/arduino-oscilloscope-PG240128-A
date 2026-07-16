# Research: analog front-end and trigger

How the signal gets from the outside world into pin A7 safely, and how the scope decides *when* to start drawing. Designs ordered simplest → nicest; build them in that order.

## ⚠️ Safety first (read even if you read nothing else)

- The Nano pin must stay within **−0.5 V … +5.5 V**; beyond that, internal clamp diodes conduct, and the safe rule is **≤ 1 mA through the clamps** ([Microchip app note AVR182](https://ww1.microchip.com/downloads/en/Appnotes/Atmel-2508-Zero-Cross-Detector_ApplicationNote_AVR182.pdf)).
- **NEVER probe mains. Ever.** Three independent reasons: mains peaks (325 V for 230 VAC) destroy everything here; the Nano's GND is your PC's USB ground — probing mains connects mains to your laptop; and nothing on a breadboard has rated insulation. Also beware charged capacitors (PSU bulk caps, camera flashes).
- Safe envelope printed on the box: **0–5 V on the ×1 range, ±20 V on the ×10 range**, anything unknown = hostile until proven otherwise.

## Front-end designs

### Design A — bare minimum, DC 0–5 V (build this first)

```
signal o───[ 10 kΩ ]───┬───o A7
                       │
              BAT85 ─▶├─ to +5V   (optional but cheap insurance)
              BAT85 ─▶├─ to GND
signal GND o───────────┴───o Nano GND
```

One resistor. The 10 kΩ limits clamp current, making roughly **−10 V…+15 V survivable** even with no diodes (that figure is Peter Balch's, from the same 1 mA rule). Add the two Schottky clamps (BAT85/BAT54; 1N4148 acceptable) and a 0.25 W resistor tolerates ~±50 V faults. Range: 0…+5 V, DC only — negative halves of a waveform read as 0.

### Design B — AC coupling + mid-rail bias (audio and any AC signal)

```
signal o───[ 1 µF film, ≥63 V ]───┬───[ 10 kΩ ]───o A7 (+ clamps)
                                  │
                     +5V o──[100k]┤
                                  ├──[100k]──o GND
                     100 nF ──────┴──o GND (optional, quiets the node)
```

The capacitor blocks DC; the two 100 kΩ resistors re-center the signal on 2.5 V, so ±2.5 V swings fit the ADC range. Corner frequency: 1/(2π · 50 kΩ · 1 µF) ≈ **3.2 Hz** — everything audio passes. The 0 V line now sits mid-screen, like a real scope in AC mode.

### Design C — ±20 V DC-coupled in three resistors (Balch's trick, our ×10 range)

```
signal o───[ 470 kΩ ]───┬───o A6 or A7
                        │
             +5V o──[ 120 kΩ ]──┤
             GND o──[ 150 kΩ ]──┘
```

Scales *and* offsets simultaneously with no op-amp and no negative rail: approximately **−19.6 V … +20.7 V** maps into 0–5 V, input impedance 470 kΩ, and fault current through 470 kΩ is negligible ("in theory 470 V — but don't", [ArdOsc](https://www.instructables.com/Oscilloscope-in-a-Matchbox-Arduino/)). This is the exact network ArdOsc uses for its ±20 V voltmeter.

*Frequency compensation (optional, needed above ~10 kHz):* any high-value divider forms an RC low-pass with the ~15–25 pF at the pin. A **5–30 pF trimmer across the top resistor**, adjusted until a square wave has square corners, fixes it — the same procedure as compensating a real 10:1 probe ([Picotech guide](https://www.picotech.com/library/knowledge-bases/oscilloscopes/how-to-tune-x10-oscilloscope-probes)).

### Design D — op-amp buffer (the "nice" upgrade, optional)

Solves the source-impedance problem (ADC wants ≤10 kΩ) and enables millivolt ranges:

- Chip: **MCP6002** (dual, rail-to-rail in/out, 1 MHz, ~€0.40). TLV2372 for more bandwidth.
- **Avoid the LM358** unless you know why: its output can't go within ~1.5 V of Vcc ("its range is 0 V to 3.5 V — dreadful… a rather poor chip" — Balch).
- Simplest robust arrangement: Design C's network → MCP6002 unity-gain follower → 10 kΩ + clamps → A7. The second op-amp half can buffer the 2.5 V mid-rail or add a ×5 gain stage for a ±0.5 V sensitive range (ArdOsc chains two such stages for ±117 mV and ±25 mV).

### Range switching

An SPDT/rotary switch selects which network feeds A7 (×1 = A/B, ×10 = C); a spare Nano pin (D12, input pull-up) *reads* the switch so the firmware scales the graticule automatically. A real **P6100-class 10:1 probe (~€10–15)** in front of everything is the best upgrade: 10 MΩ loading, compensated, insulated, rated.

## Trigger: how the trace stands still

Options on the ATmega328P, and what real projects chose:

1. **Poll-then-capture (our design — what ArdOsc uses).** Watch live ADC values; arm when the signal is below the trigger level, fire on crossing above (rising edge; mirrored for falling), then burst-capture 240 samples. Add **hysteresis** (±2 counts) or nitsky's stronger filter — require **8 consecutive samples** on the arming side — so noise can't false-trigger. Crucially: a **timeout (~250 ms) falls back to free-running**, so the screen never freezes when no signal is present.
2. **Buffer scan.** Capture continuously into a circular buffer and search it for the crossing afterwards — gives *pre-trigger* display (you see what happened before the edge). A nice later upgrade; slightly more RAM juggling.
3. **On-chip analog comparator (Girino's way) — not available to us.** The comparator inputs are hard-wired to **AIN0/AIN1 = D6/D7, which our display's data bus occupies**, and they cannot be remapped. Alternatives if hardware trigger ever became a must: rewire two display data lines to D12/D13, or an external LM393 comparator into D2 (INT0). Not worth it: the best-documented Nano scopes chose software triggering deliberately (Balch measured the comparator/ISR approach as flaky at speed anyway).

Trigger level UI: a small marker at the trigger voltage on the graticule; level adjusted with the encoder/buttons (or a trimmer into A6 if we want a physical knob).

## Calibration (10 minutes, once)

1. **Vcc truth:** run the bandgap "secret voltmeter" (`Vcc = 1125300L / reading` mV), measure the real 5 V pin with a multimeter, adjust the constant until they agree. USB "5 V" is really 4.6–5.1 V.
2. **Zero:** short the probe to GND → adjust offset until the trace reads 0.00 V.
3. **Gain:** apply a known DC (the Nano's 3V3 pin, measured with the multimeter) → adjust the volts/count factor until the readout matches.

Same two-point procedure as [skillbank's calibration page](https://www.skillbank.co.uk/arduino/calibrate.htm) and ArdOsc's `calibrateZero`/`calibrateVolts`.

## Beginner bill of materials (breadboard front end)

| Qty | Part | Role | ~Cost |
|---|---|---|---|
| 1 | 10 kΩ 0.25 W metal film | series protection into A7 | €0.02 |
| 2 | BAT85 (or BAT54/1N4148) | clamps to 5 V / GND | €0.10 |
| 2 | 100 kΩ 1 % | 2.5 V bias divider | €0.04 |
| 1 | 1 µF ≥63 V film (MKT) | AC coupling | €0.30 |
| 1 | 470 kΩ + 150 kΩ + 120 kΩ 1 % | ±20 V network (×10 range) | €0.06 |
| 1 | 5–30 pF trimmer (optional) | divider compensation | €0.50 |
| 2 | 100 nF ceramic | bias node / pin reservoir | €0.04 |
| 1 | MCP6002 DIP-8 (optional) | buffer / gain stage | €0.50 |
| 1 | SPDT slide switch | ×1 / ×10 select | €0.40 |
| 1 | Header pins / croc leads / BNC | probe connection | €0.50–2 |

**≈ €2.50 core, ≈ €5 with options**, plus the recommended P6100 probe (~€12).
