# Hello World: Arduino Nano + PG240128-A, for dummies

This is **step 0 of the oscilloscope project**: before measuring anything, we make the screen say hello. Follow it in order, don't skip the checkpoints, and you cannot get lost. No electronics knowledge is assumed.

> The pins chosen here are not random: they deliberately leave free **A6/A7** (the future oscilloscope probe inputs) and **D2/D3** (the future buttons). Wire it like this once and you won't have to rewire anything for the oscilloscope.

---

## 1. What we are building

```
                    ┌──────────────────────────────┐
   USB ──► [Nano] ──► 12 wires ──►  PG240128-A     │
                    │   "Hello, PG240128-A!"       │
                    └──────────────────────────────┘
```

The PG240128-A is a 240×128 pixel LCD from the 90s-industrial school of design: it speaks an 8-bit parallel protocol (8 data wires + 4 control wires), runs on 5 V, and has a controller chip (Toshiba T6963C) with its own memory. The Arduino Nano is a perfect partner because it is also 5 V — **no level shifters, no extra chips, just wires**.

## 2. Shopping list

| # | Item | Notes |
|---|---|---|
| 1 | Arduino Nano (ATmega328P) | clone is fine (CH340 USB chip) |
| 2 | PG240128-A display | this repo is all about it |
| 3 | Potentiometer 10 kΩ | contrast adjustment — **mandatory**, screen shows nothing without it |
| 4 | Resistor 12–15 Ω, ≥ 0.5 W | backlight current limiting |
| 5 | Breadboard + dupont wires | ~25 wires. Male-female if your display has pins soldered |
| 6 | Mini-USB cable | the Nano uses mini-USB, not micro! |

Optional but recommended: a 20-pin single-row header to solder onto the display if it came bare.

## 3. Know your two parts

### The display's 20-pin connector

Pin 1 is marked on the board (small "1" or a square pad). Double-check — counting from the wrong end is the classic first mistake.

| Pin | Name | What it is | Where it goes |
|---|---|---|---|
| 1 | Vss | ground | GND rail |
| 2 | Vdd | +5 V power | 5V rail |
| 3 | Vo | contrast input | **pot wiper (middle leg)** |
| 4 | C/D | "command or data?" | Nano **A1** |
| 5 | /RD | read strobe | **5V rail** (we never read) |
| 6 | /WR | write strobe | Nano **A3** |
| 7 | DB0 | data bit 0 | Nano **D8** |
| 8 | DB1 | data bit 1 | Nano **D9** |
| 9 | DB2 | data bit 2 | Nano **D10** |
| 10 | DB3 | data bit 3 | Nano **D11** |
| 11 | DB4 | data bit 4 | Nano **D4** |
| 12 | DB5 | data bit 5 | Nano **D5** |
| 13 | DB6 | data bit 6 | Nano **D6** |
| 14 | DB7 | data bit 7 | Nano **D7** |
| 15 | /CE | chip enable | Nano **A0** |
| 16 | /RST | reset | Nano **A2** |
| 17 | Vee | **negative voltage OUTPUT** | **pot outer leg** (nothing else!) |
| 18 | MD2 | factory configuration | **leave unconnected** |
| 19 | FS1 | font select | **GND rail** (mandatory) |
| 20 | NC | nothing | leave unconnected |

Somewhere on the display board there are also two backlight pads marked **A** (anode) and **K** (cathode) — separate from the 20-pin connector.

> ⚠️ **Pin 17 (Vee) is special.** The display *generates* about −12 V on this pin for its own use. It is an output. Never connect it to the Nano, never to 5 V, never to GND. Its only job is to feed one leg of the contrast pot.

### The Nano pins we use

```
                     ┌───────USB───────┐
   (future button) ──│ D12         D13 │── (future button)
                     │ 3V3        AREF │
   /CE  ◄────────────│ A0           D2 │── (future button/encoder)
   C/D  ◄────────────│ A1           D3 │── (future button/encoder)
   /RST ◄────────────│ A2           D4 │────────► DB4
   /WR  ◄────────────│ A3           D5 │────────► DB5
   (free, I2C)       │ A4           D6 │────────► DB6
   (free, I2C)       │ A5           D7 │────────► DB7
   (FUTURE PROBE) ──►│ A6           D8 │────────► DB0
   (FUTURE PROBE) ──►│ A7           D9 │────────► DB1
                     │ 5V          D10 │────────► DB2
                     │ RST         D11 │────────► DB3
                     │ GND         RX0 │
                     │ VIN         TX1 │
                     └─────────────────┘
```

## 4. Wiring, step by step

The complete picture (generated with [tools/wiring_hello_world.py](../tools/wiring_hello_world.py)):

![Wiring diagram: Arduino Nano + PG240128-A hello world](images/wiring-hello-world.png)

Do it in this order and check each step off.

### Step 4.1 — Power rails

1. Nano **5V** → breadboard **red (+) rail**
2. Nano **GND** → breadboard **blue (−) rail**
3. Display **pin 1 (Vss)** → blue rail
4. Display **pin 2 (Vdd)** → red rail

### Step 4.2 — The three "set and forget" pins

5. Display **pin 5 (/RD)** → **red rail** (+5 V). We only ever write to the display.
6. Display **pin 19 (FS1)** → **blue rail** (GND). Tells the display to use the memory layout our library expects.
7. Display **pin 18 (MD2)** and **pin 20 (NC)**: touch nothing, connect nothing.

### Step 4.3 — Contrast pot (the step everyone gets wrong)

The pot has 3 legs. Middle leg = wiper.

```
   red rail (+5V) ────────┐
                       ┌──┴──┐
                       │ POT │ 10 kΩ
        Vo (pin 3) ◄───┤wiper│
                       └──┬──┘
   Vee (pin 17) ──────────┘
```

8. Pot **outer leg 1** → red rail (+5 V)
9. Pot **outer leg 2** → display **pin 17 (Vee)**
10. Pot **middle leg (wiper)** → display **pin 3 (Vo)**

Why so weird? The LCD glass needs about **−7 V** to become visible. The display makes that negative voltage itself and hands it to you on pin 17; the pot lets you dial Vo anywhere between +5 V and −12 V. With the pot in the wrong position **the screen looks completely dead even when everything works** — remember that for later.

### Step 4.4 — Backlight

```
   red rail (+5V) ──[ 12 Ω resistor ]──► A pad
   K pad ──────────────────────────────► blue rail (GND)
```

11. Red rail → **12 Ω resistor** → display **A** pad
12. Display **K** pad → blue rail

Never connect A straight to 5 V — the resistor limits the LED current.

### Step 4.5 — The 12 signal wires

13–20. Data bus (order matters — note it is *not* sequential!):

| Display | → | Nano |
|---|---|---|
| pin 7 (DB0) | → | D8 |
| pin 8 (DB1) | → | D9 |
| pin 9 (DB2) | → | D10 |
| pin 10 (DB3) | → | D11 |
| pin 11 (DB4) | → | D4 |
| pin 12 (DB5) | → | D5 |
| pin 13 (DB6) | → | D6 |
| pin 14 (DB7) | → | D7 |

21–24. Control lines:

| Display | → | Nano |
|---|---|---|
| pin 15 (/CE) | → | A0 |
| pin 4 (C/D) | → | A1 |
| pin 16 (/RST) | → | A2 |
| pin 6 (/WR) | → | A3 |

**✅ Checkpoint:** count your wires. You should have: 4 power/rail wires, 2 strap wires (/RD, FS1), 3 pot wires, 2 backlight wires, 12 signal wires. Keep signal wires short (< 15 cm) — long loose jumpers cause ghost pixels.

## 5. Software

### Step 5.1 — Arduino IDE and driver

1. Install the [Arduino IDE](https://www.arduino.cc/en/software).
2. Clone Nanos need the **CH340 USB driver** on Windows/macOS (Linux has it built in). If no serial port appears when you plug in the Nano, that's why — search "CH340 driver" for your OS.

### Step 5.2 — Install the U8g2 library

IDE menu → **Sketch → Include Library → Manage Libraries…** → search **"U8g2"** → install the one by **olikraus**.

### Step 5.3 — The sketch

Paste this complete sketch (also explained line by line below):

```cpp
#include <Arduino.h>
#include <U8g2lib.h>

// PG240128-A on Arduino Nano, U8g2 page-buffer mode.
// The Nano has only 2 KB of RAM: a full framebuffer (3840 bytes) is
// impossible, so U8g2 draws the screen in 16 horizontal slices using a
// small 240-byte buffer. That's what the "_1_" in the class name means.
// A0..A3 are written as their digital numbers: A0=14, A1=15, A2=16, A3=17.
U8G2_T6963_240X128_1_8080 u8g2(U8G2_R0,
  /*DB0..DB7 =*/ 8, 9, 10, 11, 4, 5, 6, 7,
  /*WR=*/ 17, /*CE=*/ 14, /*C-D=*/ 15, /*RST=*/ 16);

void setup(void) {
  u8g2.begin();   // resets the display and configures the T6963C
}

void loop(void) {
  u8g2.firstPage();
  do {
    // Everything you want on screen must be drawn inside this loop —
    // it runs 16 times per frame, once per slice.
    u8g2.setFont(u8g2_font_ncenB14_tr);
    u8g2.drawStr(24, 40, "Hello, PG240128-A!");
    u8g2.setFont(u8g2_font_6x10_tr);
    u8g2.drawStr(24, 60, "Arduino Nano says hi :)");
    u8g2.drawFrame(0, 0, 240, 128);           // border
    u8g2.drawFrame(2, 2, 236, 124);           // double border, fancy
    u8g2.drawDisc(210, 95, 12);               // filled circle
    u8g2.drawCircle(180, 95, 12);             // empty circle
  } while (u8g2.nextPage());

  delay(1000);
}
```

### Step 5.4 — Board settings and upload

1. **Tools → Board → Arduino Nano**
2. **Tools → Processor → ATmega328P** — and if the upload fails with `stk500_getsync()` errors, switch to **ATmega328P (Old Bootloader)**. Nearly all clones need the old bootloader. This single dropdown causes 90 % of all Nano upload failures.
3. **Tools → Port →** the port that appeared when you plugged it in.
4. Click **Upload** (→ arrow).

## 6. The moment of truth

After upload the backlight should be lit. Now, **slowly** turn the contrast pot from one end to the other:

- one extreme: screen totally blank
- other extreme: all pixels dark
- somewhere in between: **"Hello, PG240128-A!"** appears, crisp

That's it. Working display, and the wiring is already oscilloscope-ready.

## 7. Nothing? Troubleshooting in order of probability

1. **Turn the pot again, slower, full range.** Seriously. The display can be working perfectly and show nothing.
2. Backlight not lit? → Check the 12 Ω resistor path and the A/K pads; check 5 V is on the red rail (measure it if you can).
3. Backlight lit, contrast swept, still blank →
   - /RD (pin 5) really tied to +5 V?
   - FS1 (pin 19) really tied to GND?
   - Pot outer leg really on **pin 17**, not pin 18 or GND?
4. Garbage / random pixels stay forever → one of the 8 data wires is swapped or loose. Re-check the table in step 4.5 (remember: DB0 is D8, **not** D4).
5. Image appears but doubled/wrapped weirdly → FS1 is floating instead of grounded.
6. Upload fails → Old Bootloader dropdown (step 5.4.2), then CH340 driver, then try another USB cable ("charge-only" cables exist and are evil).
7. Still stuck → the long-form guides in the companion display repo: [lcd-pg-240128A](https://github.com/yupipi93/lcd-pg-240128A) (hardware reference + troubleshooting).

## 8. What's next

With this exact wiring, the oscilloscope project continues using:

- **A7** → the analog signal input (probe) — see [analog front-end doc](03-analog-front-end-and-trigger.md)
- **D2 / D3** → buttons (they support hardware interrupts)
- **D12 / D13** → more buttons or status LED

Continue with the [build plan](04-build-plan.md).
