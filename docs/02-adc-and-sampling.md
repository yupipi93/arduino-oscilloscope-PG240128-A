# Research: the Nano's ADC as an oscilloscope sampler

How fast and how well the ATmega328P can digitize a signal, from `analogRead()` to direct register control. Sources linked throughout; primary reference is the [ATmega328P datasheet](https://ww1.microchip.com/downloads/en/DeviceDoc/ATmega48A-PA-88A-PA-168A-PA-328-P-DS-DS40002061B.pdf), [Nick Gammon's ADC page](https://www.gammon.com.au/adc) and [Open Music Labs' in-depth measurements](http://www.openmusiclabs.com/learning/digital/atmega-adc/).

## Why `analogRead()` is slow (~9.6 kHz)

The 10-bit ADC needs **13 ADC-clock cycles per conversion**. The Arduino core sets the ADC clock to 125 kHz (prescaler 128) because the datasheet wants 50–200 kHz for full 10-bit resolution → 13 ÷ 125 kHz ≈ **104 µs per conversion**, ~110 µs with call overhead. Good enough only for slow time bases.

## The speed dial: the ADC prescaler

| Prescaler | ADC clock | Conversion | Rate | Real resolution (measured ENOB) |
|---|---|---|---|---|
| 128 (default) | 125 kHz | 104 µs | ~9.6 kSps | ~9.8 bits (the practical max) |
| 64 | 250 kHz | 52 µs | ~19 kSps | >9 bits |
| 32 | 500 kHz | 26 µs | ~38 kSps | >9 bits |
| **16** | **1 MHz** | **13 µs** | **~77 kSps** | **~8 bits** ← our fast setting |
| 8 | 2 MHz | 6.5 µs | ~154 kSps | <8 bits |
| 4 | 4 MHz | 3.25 µs | ~300 kSps | degraded, distortion |

ENOB figures are Open Music Labs' spectral measurements ([in-depth analysis](http://www.openmusiclabs.com/learning/digital/atmega-adc/in-depth/index.html)); above 1 MHz the ADC adds distortion, and beyond 4 MHz it stops working usefully.

**Why 8-bit resolution is not a loss for us:** our waveform area is ~100 pixels tall — less than 7 bits of vertical display. So we run the ADC left-adjusted (**ADLAR**) and read only the high byte (`ADCH`): one byte per sample, half the RAM, one register read. Every fast Arduino scope does this (Girino, ArdOsc, nitsky).

## Free-running mode (the fast capture engine)

Set once, then the ADC converts continuously; you just collect bytes:

```c
ADMUX  = _BV(REFS0)        // AVcc reference
       | _BV(ADLAR)        // left-adjust -> 8-bit read from ADCH
       | 0b0111;           // input = ADC7 (Nano pin A7)
ADCSRB = 0;                // free-running mode
DIDR0  = 0x3F;             // disable digital buffers on A0-A5
ADCSRA = _BV(ADEN)         // ADC on
       | _BV(ADATE)        // auto-trigger (free run)
       | _BV(ADPS2);       // prescaler 16 -> 1 MHz ADC clock
ADCSRA |= _BV(ADSC);       // go
```

Then either poll or use the interrupt:

- **Polling loop (recommended):** wait for ADIF, grab `ADCH`, clear the flag, store into the buffer. Peter Balch measured interrupt-driven capture (Girino-style ISR) as reliable only to **~37 kSps** — his mature design polls with interrupts off, and so do we ([ArdOsc](https://www.instructables.com/Oscilloscope-in-a-Matchbox-Arduino/)).
- Auto-triggered conversions take 13.5 cycles → book rates **~74–77 kSps at prescaler 16, ~148–154 kSps at prescaler 8**.

Don't try to "read faster than the ADC": reading `ADCH` before a conversion finishes just returns the *previous* value — ArdOsc's famous "1 MSps" mode actually produces ~250 kSps with each sample repeated 4× ([Balch's own honest write-up](https://www.instructables.com/Oscilloscope-in-a-Matchbox-Arduino/)).

## Two time-base mechanisms

1. **Fast ranges (µs/div to few ms/div):** back-to-back free-running captures; change the prescaler per range (GOscillo's approach: /4–/16 for fast ranges, /128 for slow).
2. **Slow ranges (10 ms/div to s/div):** one timed conversion per sample point (`analogRead` class is fine here), paced by `micros()` or a timer.

Both fill the same 240-byte buffer; only the pacing changes.

## Input impedance — why the front-end design matters

The ADC samples onto a **14 pF capacitor** through an internal MUX and is "optimized for source impedance ≤ 10 kΩ" (datasheet). Consequences:

- A bare 900 kΩ/100 kΩ divider (≈90 kΩ Thevenin) is too stiff for fast sampling — the S/H cap doesn't charge fully → amplitude errors at speed.
- Fixes, in beginner order: keep divider impedance low; add a 1–10 nF reservoir cap at the pin (fine for audio, filters HF); or buffer with an op-amp ([front-end doc](03-analog-front-end-and-trigger.md)).
- The S/H settles in ~500 ns (≈1 µs after a MUX channel change) — relevant only if we ever multiplex two channels.

## References, noise, calibration hooks

- **Reference options:** AVcc (default), internal 1.1 V bandgap, external AREF. Never drive AREF externally while an internal reference is selected. AREF is already decoupled with 100 nF on the Nano.
- **The "secret voltmeter":** measure the 1.1 V bandgap *against* AVcc to compute the real Vcc: `Vcc = 1125300L / adcReading` mV. Essential on USB power, where "5 V" is really 4.6–5.1 V — this scales our volts/div truthfully ([JeeLabs](https://jeelabs.org/wp-content/uploads/2012/05/04/measuring-vcc-via-the-bandgap), [Majenko](https://majenko.co.uk/blog/our-blog-1/making-accurate-adc-readings-on-the-arduino-25)).
- The bandgap is spec'd 1.0–1.2 V but is stable per chip: calibrate the constant once against a multimeter ([skillbank two-point procedure](https://www.skillbank.co.uk/arduino/calibrate.htm)).
- **Noise hygiene specific to this project:** the display bus is 12 GPIOs banging away — **never sample while drawing**. Capture first, then draw (which the capture-then-draw architecture gives us for free). Set DIDR0, keep probe ground short to Nano GND.

## Bottom line for the build

- Fast engine: free-running, prescaler 16, ADLAR, polled, on **A7** → **~77 kSps**, 8-bit.
- Displayed bandwidth: clean to **~5–10 kHz**, usable to ~20 kHz (≈10 samples/period rule).
- 240 samples = 240 bytes — one per screen column, coexists happily with U8g2's 240-byte page buffer in 2 KB of RAM.
