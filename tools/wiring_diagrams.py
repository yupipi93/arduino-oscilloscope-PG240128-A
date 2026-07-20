"""Generate one wiring diagram per milestone (M0..M6) of the build plan.

The base scene is the M0 hello-world wiring (Nano + PG240128-A, rails,
contrast pot, backlight). Each milestone adds its hardware on top:
  M1  + test signal   D3 -[10k]-> A7
  M2  (software only — banner, wiring = M1)
  M3  (software only — banner, wiring = M1)
  M4  + buttons       SEC/DIV + (D2), SEC/DIV - (D12) to GND
  M5  + front-end board -> A7, RANGE sense -> A4, test loop becomes CAL post
  M6  + CH2 probe -> A6

Technique from multi-rocket-avionica/breadboard-wiring/wiring_diagram.py:
pure-PIL modules, pin circles, orthogonal color-coded wires, legend.

Run:  python3 tools/wiring_diagrams.py
Out:  docs/images/wiring-*.png (7 files)
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTDIR = Path(__file__).resolve().parent.parent / "docs" / "images"
OUTDIR.mkdir(parents=True, exist_ok=True)

W, H = 1900, 1320
BG = (250, 250, 248)

def load_font(size, bold=False):
    for c in (f"/usr/share/fonts/truetype/dejavu/DejaVuSans"
              f"{'-Bold' if bold else ''}.ttf",
              f"/usr/share/fonts/truetype/liberation/LiberationSans"
              f"{'-Bold' if bold else '-Regular'}.ttf"):
        try:
            return ImageFont.truetype(c, size)
        except OSError:
            pass
    return ImageFont.load_default()

F_TITLE  = load_font(40, bold=True)
F_SUB    = load_font(22)
F_MOD    = load_font(26, bold=True)
F_MODSUB = load_font(16)
F_PIN    = load_font(16, bold=True)
F_PINSM  = load_font(14, bold=True)
F_LEG    = load_font(20, bold=True)
F_LEGSM  = load_font(16)
F_BANNER = load_font(26, bold=True)
F_TINY   = load_font(13)

COL_5V    = (215, 40, 40)
COL_GND   = (35, 35, 40)
COL_DATA  = (40, 110, 220)
COL_CTRL  = (235, 140, 20)
COL_POT   = (150, 60, 200)
COL_SIG   = (35, 165, 75)      # green  — analog signal path / test signal
COL_BTN   = (0, 150, 160)      # teal   — UI buttons
COL_RANGE = (150, 100, 40)     # brown  — range-switch sense
COL_CH2   = (220, 100, 170)    # pink   — channel 2

COL_LCD_BOARD = (18, 92, 62)
COL_LCD_GLASS = (200, 208, 184)
COL_NANO      = (28, 70, 150)
COL_POT_BODY  = (70, 70, 78)
COL_RES_BODY  = (222, 196, 150)
COL_FE_BODY   = (36, 86, 78)
COL_CH2_BODY  = (80, 70, 100)
COL_BTN_BODY  = (60, 60, 66)
COL_TEXT       = (25, 25, 30)
COL_TEXT_LIGHT = (252, 252, 250)
COL_OUTLINE    = (40, 40, 50)
COL_PIN_FILL   = (245, 235, 110)

PIN_R = 9
WIRE_W = 5

# Geometry constants (shared by every diagram)
LCD_X0, LCD_Y0, LCD_W, LCD_H = 150, 140, 1100, 320
LCD_X1, LCD_Y1 = LCD_X0 + LCD_W, LCD_Y0 + LCD_H
RAIL_5V_Y, RAIL_GND_Y = 640, 668
RAIL_X0, RAIL_X1 = 170, 1620
NANO_X0, NANO_Y0, NANO_W, NANO_H = 620, 720, 300, 510
NANO_X1, NANO_Y1 = NANO_X0 + NANO_W, NANO_Y0 + NANO_H
LEG_X, LEG_Y, LEG_W, LEG_H = 1250, 760, 620, 470

LCD_PINS = ["Vss", "Vdd", "Vo", "C/D", "/RD", "/WR",
            "DB0", "DB1", "DB2", "DB3", "DB4", "DB5", "DB6", "DB7",
            "/CE", "/RST", "Vee", "MD2", "FS1", "NC"]
NANO_LEFT  = ["VIN", "GND", "RST", "5V", "A7", "A6", "A5", "A4",
              "A3", "A2", "A1", "A0", "AREF", "3V3", "D13"]
NANO_RIGHT = ["TX1", "RX0", "RST2", "GND2", "D2", "D3", "D4", "D5",
              "D6", "D7", "D8", "D9", "D10", "D11", "D12"]
NANO_LABEL = {"RST2": "RST", "GND2": "GND"}

MILESTONES = {
    0: ("wiring-hello-world.png", "M0 — Hello World wiring",
        "12 signal wires + power + contrast pot + backlight."),
    1: ("wiring-m1-waveform-viewer.png", "M1 — Waveform viewer wiring",
        "M0 + test signal: D3 —[10 kΩ]→ A7 (the Nano probes its own PWM)."),
    2: ("wiring-m2-trigger.png", "M2 — Trigger",
        "Software-only milestone: wiring identical to M1."),
    3: ("wiring-m3-fast-sampling.png", "M3 — Fast sampling (77 kSps)",
        "Software-only milestone: wiring identical to M1."),
    4: ("wiring-m4-ui-buttons.png", "M4 — UI wiring",
        "M1 + buttons SEC/DIV + (D2) and SEC/DIV − (D12) to GND — small text = long-press function. (D13 unusable: onboard LED)."),
    5: ("wiring-m5-front-end.png", "M5 — Analog front-end wiring",
        "Front-end board feeds A7 · RANGE sense on A4 · test PWM becomes a CAL post."),
    6: ("wiring-m6-dual-channel.png", "M6 — Dual channel wiring",
        "M5 + second probe into A6. Pre-trigger / PC streaming are software."),
}


def wire(d, points, color):
    for i in range(len(points) - 1):
        d.line([points[i], points[i + 1]], fill=color, width=WIRE_W)
    for pt in (points[0], points[-1]):
        d.ellipse((pt[0] - 7, pt[1] - 7, pt[0] + 7, pt[1] + 7),
                  fill=color, outline=COL_OUTLINE, width=1)


def draw_pin(d, x, y, highlight=False):
    d.ellipse((x - PIN_R, y - PIN_R, x + PIN_R, y + PIN_R),
              fill=(255, 255, 255) if highlight else COL_PIN_FILL,
              outline=COL_OUTLINE, width=2)


def draw_base(d, m):
    """Display + rails + Nano + pot + backlight + M0 wiring.
    Returns (lcd_xy, nano_xy)."""
    # ---- display ----
    d.rounded_rectangle((LCD_X0, LCD_Y0, LCD_X1, LCD_Y1), radius=12,
                        fill=COL_LCD_BOARD, outline=COL_OUTLINE, width=3)
    d.rounded_rectangle((LCD_X0 + 70, LCD_Y0 + 42, LCD_X1 - 70, LCD_Y1 - 92),
                        radius=6, fill=COL_LCD_GLASS, outline=COL_OUTLINE, width=2)
    d.text(((LCD_X0 + LCD_X1) // 2, (LCD_Y0 + LCD_Y1) // 2 - 30),
           "PG240128-A", font=F_MOD, fill=COL_TEXT, anchor="mm")
    d.text(((LCD_X0 + LCD_X1) // 2, (LCD_Y0 + LCD_Y1) // 2 + 4),
           "240 × 128 · T6963C", font=F_MODSUB, fill=COL_TEXT, anchor="mm")

    lcd_xy = {}
    pitch = LCD_W / 21.0
    for i, name in enumerate(LCD_PINS):
        px, py = LCD_X0 + pitch * (i + 1), LCD_Y1
        draw_pin(d, px, py)
        row_y = py - 24 if i % 2 == 0 else py - 50
        d.text((px, row_y), f"{i + 1}", font=F_PINSM,
               fill=(255, 220, 170), anchor="mb")
        d.text((px, row_y + 16), name, font=F_PIN,
               fill=COL_TEXT_LIGHT, anchor="mb")
        lcd_xy[name] = (px, py)

    bl_a = (LCD_X1, LCD_Y0 + 120)
    bl_k = (LCD_X1, LCD_Y0 + 180)
    for (px, py), lab in ((bl_a, "A"), (bl_k, "K")):
        draw_pin(d, px, py)
        d.text((px - 18, py), lab, font=F_PIN, fill=COL_TEXT_LIGHT, anchor="rm")
    d.text((LCD_X1 - 18, LCD_Y0 + 92), "backlight", font=F_MODSUB,
           fill=COL_TEXT_LIGHT, anchor="rm")

    # ---- rails ----
    d.line([(RAIL_X0, RAIL_5V_Y), (RAIL_X1, RAIL_5V_Y)], fill=COL_5V, width=7)
    d.line([(RAIL_X0, RAIL_GND_Y), (RAIL_X1, RAIL_GND_Y)], fill=COL_GND, width=7)
    d.text((RAIL_X1 + 12, RAIL_5V_Y), "+5 V rail", font=F_LEG, fill=COL_5V, anchor="lm")
    d.text((RAIL_X1 + 12, RAIL_GND_Y), "GND rail", font=F_LEG, fill=COL_GND, anchor="lm")

    # ---- Nano ----
    d.rounded_rectangle((NANO_X0, NANO_Y0, NANO_X1, NANO_Y1), radius=12,
                        fill=COL_NANO, outline=COL_OUTLINE, width=3)
    d.rounded_rectangle((NANO_X0 + NANO_W//2 - 55, NANO_Y1 - 8,
                         NANO_X0 + NANO_W//2 + 55, NANO_Y1 + 30),
                        radius=6, fill=(205, 205, 210), outline=COL_OUTLINE, width=2)
    d.text((NANO_X0 + NANO_W//2, NANO_Y1 + 34), "mini-USB",
           font=F_MODSUB, fill=COL_TEXT, anchor="mt")
    d.text((NANO_X0 + NANO_W//2, NANO_Y0 + 200), "Arduino",
           font=F_MOD, fill=COL_TEXT_LIGHT, anchor="mm")
    d.text((NANO_X0 + NANO_W//2, NANO_Y0 + 234), "NANO",
           font=F_MOD, fill=COL_TEXT_LIGHT, anchor="mm")
    d.text((NANO_X0 + NANO_W//2, NANO_Y0 + 268), "(USB down, top view)",
           font=F_MODSUB, fill=COL_TEXT_LIGHT, anchor="mm")

    nano_xy = {}
    n_top = NANO_Y0 + 40
    for i, name in enumerate(NANO_LEFT):
        x, y = NANO_X0, n_top + i * 30
        draw_pin(d, x, y)
        d.text((x + 16, y), name, font=F_PIN, fill=COL_TEXT_LIGHT, anchor="lm")
        nano_xy[name] = (x, y)
    for i, name in enumerate(NANO_RIGHT):
        x, y = NANO_X1, n_top + i * 30
        draw_pin(d, x, y)
        d.text((x - 16, y), NANO_LABEL.get(name, name), font=F_PIN,
               fill=COL_TEXT_LIGHT, anchor="rm")
        nano_xy[name] = (x, y)

    # ---- contrast pot ----
    d.rounded_rectangle((180, 800, 350, 930), radius=10,
                        fill=COL_POT_BODY, outline=COL_OUTLINE, width=3)
    d.ellipse((265 - 32, 865 - 24, 265 + 32, 865 + 40),
              fill=(120, 120, 128), outline=COL_OUTLINE, width=2)
    d.text((265, 942), "Contrast pot 10 kΩ", font=F_MODSUB, fill=COL_TEXT, anchor="mt")
    pot_l, pot_m, pot_r = (210, 800), (265, 800), (320, 800)
    for (px, py), lab in ((pot_l, "+5V"), (pot_m, "wiper"), (pot_r, "Vee")):
        draw_pin(d, px, py)
        d.text((px, py + 16), lab, font=F_PINSM, fill=COL_TEXT_LIGHT, anchor="mt")

    # ---- backlight resistor ----
    d.rounded_rectangle((1340, bl_a[1] - 20, 1450, bl_a[1] + 20), radius=8,
                        fill=COL_RES_BODY, outline=COL_OUTLINE, width=3)
    d.text((1395, bl_a[1]), "12 Ω", font=F_PIN, fill=COL_TEXT, anchor="mm")
    d.text((1395, bl_a[1] + 28), "≥ 0.5 W (or trimmer)", font=F_PINSM,
           fill=COL_TEXT, anchor="mt")

    # ---- M0 wiring ----
    x, y = nano_xy["5V"];  wire(d, [(x, y), (x - 120, y), (x - 120, RAIL_5V_Y)], COL_5V)
    x, y = nano_xy["GND"]; wire(d, [(x, y), (x - 150, y), (x - 150, RAIL_GND_Y)], COL_GND)
    x, y = lcd_xy["Vss"];  wire(d, [(x, y), (x, RAIL_GND_Y)], COL_GND)
    x, y = lcd_xy["Vdd"];  wire(d, [(x, y), (x, RAIL_5V_Y)],  COL_5V)
    x, y = lcd_xy["/RD"];  wire(d, [(x, y), (x, RAIL_5V_Y)],  COL_5V)
    x, y = lcd_xy["FS1"];  wire(d, [(x, y), (x, RAIL_GND_Y)], COL_GND)

    wire(d, [(1450, bl_a[1]), (1500, bl_a[1]), (1500, RAIL_5V_Y)], COL_5V)
    wire(d, [bl_a, (1340, bl_a[1])], COL_5V)
    wire(d, [bl_k, (1460, bl_k[1]), (1460, RAIL_GND_Y)], COL_GND)

    wire(d, [pot_l, (pot_l[0], RAIL_5V_Y)], COL_5V)
    vx, vy = lcd_xy["Vo"]
    wire(d, [pot_m, (pot_m[0], 470), (vx, 470), (vx, vy)], COL_POT)
    ex, ey = lcd_xy["Vee"]
    wire(d, [pot_r, (pot_r[0], 630), (ex, 630), (ex, ey)], COL_POT)

    data_map = [("DB0", "D8"), ("DB1", "D9"), ("DB2", "D10"), ("DB3", "D11"),
                ("DB4", "D4"), ("DB5", "D5"), ("DB6", "D6"), ("DB7", "D7")]
    lane_of = {"DB7": 480, "DB6": 492, "DB5": 504, "DB4": 516,
               "DB3": 528, "DB2": 540, "DB1": 552, "DB0": 564}
    chan_of = {"D4": 984, "D5": 996, "D6": 1008, "D7": 1020,
               "D8": 1032, "D9": 1044, "D10": 1056, "D11": 1068}
    for db, dpin in data_map:
        sx, sy = lcd_xy[db]
        tx, ty = nano_xy[dpin]
        wire(d, [(sx, sy), (sx, lane_of[db]), (chan_of[dpin], lane_of[db]),
                 (chan_of[dpin], ty), (tx, ty)], COL_DATA)

    ctrl = [("/RST", "A2", 576, 584), ("/CE", "A0", 588, 560),
            ("/WR", "A3", 600, 596), ("C/D", "A1", 612, 572)]
    for sig, apin, lane, chan in ctrl:
        sx, sy = lcd_xy[sig]
        tx, ty = nano_xy[apin]
        wire(d, [(sx, sy), (sx, lane), (chan, lane), (chan, ty), (tx, ty)], COL_CTRL)

    return lcd_xy, nano_xy


def draw_test_signal(d, nano_xy, as_cal=False):
    """M1..M4: D3 -[10k]-> A7 over the top of the Nano.
    M5+ (as_cal): the same PWM + 10k ends in a CAL post instead."""
    d3 = nano_xy["D3"]
    seg_a = [d3, (948, d3[1]), (948, 694), (790, 694)]
    wire(d, seg_a, COL_SIG)
    d.rounded_rectangle((700, 678, 790, 710), radius=8,
                        fill=COL_RES_BODY, outline=COL_OUTLINE, width=3)
    d.text((745, 694), "10 kΩ", font=F_PINSM, fill=COL_TEXT, anchor="mm")
    if not as_cal:
        a7 = nano_xy["A7"]
        wire(d, [(700, 694), (586, 694), (586, a7[1]), a7], COL_SIG)
        d.text((860, 700), "test ~490 Hz", font=F_PINSM, fill=COL_SIG, anchor="mt")
    else:
        wire(d, [(700, 694), (655, 694)], COL_SIG)
        d.ellipse((655 - 11, 694 - 11, 655 + 11, 694 + 11),
                  fill=(255, 255, 255), outline=COL_SIG, width=3)
        d.text((655, 712), "CAL post (~490 Hz)", font=F_PINSM,
               fill=COL_SIG, anchor="mt")


def draw_buttons(d, nano_xy):
    """M4+: SEC/DIV + on D2, SEC/DIV - on D12 (to GND, internal pull-ups).
    Small text under each button = its long-press secondary function."""
    buttons = ((1090, 940,  "SEC/DIV +", "long: TRIG MODE"),
               (1090, 1080, "SEC/DIV −", "long: RUN/STOP"))
    for (bx0, by0, label, sub) in buttons:
        d.rounded_rectangle((bx0, by0, bx0 + 80, by0 + 80), radius=10,
                            fill=COL_BTN_BODY, outline=COL_OUTLINE, width=3)
        d.ellipse((bx0 + 24, by0 + 24, bx0 + 56, by0 + 56),
                  fill=(180, 60, 60), outline=COL_OUTLINE, width=2)
        d.text((bx0 + 40, by0 + 86), label, font=F_PINSM, fill=COL_TEXT, anchor="mt")
        d.text((bx0 + 40, by0 + 104), sub, font=F_TINY, fill=(110, 110, 116),
               anchor="mt")

    d2 = nano_xy["D2"]
    draw_pin(d, 1130, 940)                       # SEC/DIV + top pin
    wire(d, [d2, (1130, d2[1]), (1130, 940)], COL_BTN)
    d12 = nano_xy["D12"]
    draw_pin(d, 1090, 1120)                      # SEC/DIV - left pin
    wire(d, [d12, (1050, d12[1]), (1050, 1120), (1090, 1120)], COL_BTN)
    # shared GND return
    draw_pin(d, 1170, 980)
    draw_pin(d, 1170, 1120)
    wire(d, [(1170, 1120), (1200, 1120), (1200, 980)], COL_GND)
    wire(d, [(1170, 980), (1200, 980), (1200, RAIL_GND_Y)], COL_GND)


def draw_frontend(d, nano_xy):
    """M5+: front-end board -> A7, RANGE sense -> D12, probe posts."""
    d.rounded_rectangle((180, 1000, 545, 1200), radius=12,
                        fill=COL_FE_BODY, outline=COL_OUTLINE, width=3)
    d.text((362, 1030), "FRONT-END", font=F_MOD, fill=COL_TEXT_LIGHT, anchor="mm")
    d.text((362, 1062), "AC/DC · ×1/×10 attenuator", font=F_MODSUB,
           fill=COL_TEXT_LIGHT, anchor="mm")
    d.text((362, 1086), "clamps + 10 kΩ  (docs/03)", font=F_MODSUB,
           fill=COL_TEXT_LIGHT, anchor="mm")
    d.text((362, 1216), "max ±20 V (×10) · 0–5 V (×1) · NEVER mains",
           font=F_PINSM, fill=(180, 40, 40), anchor="mt")

    # probe posts (left edge)
    for py, lab in ((1120, "PROBE"), (1170, "PROBE GND")):
        draw_pin(d, 180, py, highlight=True)
        d.text((196, py), lab, font=F_PINSM, fill=COL_TEXT_LIGHT, anchor="lm")

    # OUT -> A7 (top edge)
    a7 = nano_xy["A7"]
    draw_pin(d, 525, 1000)
    d.text((525, 1004), "OUT", font=F_PINSM, fill=COL_TEXT_LIGHT, anchor="mt")
    wire(d, [(525, 1000), (525, a7[1]), a7], COL_SIG)

    # RANGE sense -> A4 (right edge, short hop up the left side)
    a4 = nano_xy["A4"]
    draw_pin(d, 545, 1160)
    d.text((529, 1160), "RANGE", font=F_PINSM, fill=COL_TEXT_LIGHT, anchor="rm")
    wire(d, [(545, 1160), (575, 1160), (575, a4[1]), a4], COL_RANGE)

    # board GND -> GND rail
    wire(d, [(180, 1170), (156, 1170), (156, RAIL_GND_Y)], COL_GND)


def draw_ch2(d, nano_xy):
    """M6: second probe through its own 10k into A6."""
    d.rounded_rectangle((355, 860, 545, 940), radius=10,
                        fill=COL_CH2_BODY, outline=COL_OUTLINE, width=3)
    d.text((450, 884), "CH2 probe", font=F_PIN, fill=COL_TEXT_LIGHT, anchor="mm")
    d.text((450, 908), "10 kΩ + clamps", font=F_PINSM, fill=COL_TEXT_LIGHT, anchor="mm")
    a6 = nano_xy["A6"]
    draw_pin(d, 545, 900)
    wire(d, [(545, 900), (605, 900), (605, a6[1]), a6], COL_CH2)


def draw_banner(d, text1, text2):
    """Software-only milestones: on-screen message inside the LCD glass."""
    bx0, by0, bx1, by1 = 320, 200, 1080, 300
    d.rounded_rectangle((bx0, by0, bx1, by1), radius=10,
                        fill=(255, 255, 255), outline=(180, 40, 40), width=4)
    d.text(((bx0 + bx1) // 2, by0 + 26), text1, font=F_BANNER,
           fill=(180, 40, 40), anchor="mm")
    d.text(((bx0 + bx1) // 2, by0 + 66), text2, font=F_SUB,
           fill=COL_TEXT, anchor="mm")


def draw_legend(d, m):
    d.rounded_rectangle((LEG_X, LEG_Y, LEG_X + LEG_W, LEG_Y + LEG_H), radius=10,
                        fill=(255, 255, 255), outline=COL_OUTLINE, width=2)
    d.text((LEG_X + 20, LEG_Y + 14), "Wire color → function",
           font=F_LEG, fill=COL_TEXT, anchor="lt")

    if m == 0:
        entries = [
            (COL_DATA, "Data bus DB0–DB7 (8 wires)", [
                "DB0→D8   DB1→D9   DB2→D10  DB3→D11",
                "DB4→D4   DB5→D5   DB6→D6   DB7→D7"]),
            (COL_CTRL, "Control (4 wires)", [
                "/CE(15)→A0   C/D(4)→A1   /RST(16)→A2   /WR(6)→A3"]),
            (COL_5V, "+5 V", ["Vdd(2), /RD(5) strap, pot leg, 12Ω → backlight A"]),
            (COL_GND, "GND", ["Vss(1), FS1(19) strap, backlight K"]),
            (COL_POT, "Contrast", [
                "pot wiper → Vo(3)    pot leg → Vee(17)",
                "Vee is an OUTPUT: only the pot connects to it"]),
        ]
        notes = ["MD2 (18) and NC (20): leave unconnected.",
                 "Kept free for the scope: A7 probe · A6 ch2 · D2/D3 · D12/D13.",
                 ("Blank screen? Sweep the contrast pot slowly end to end first.",
                  (180, 40, 40))]
    else:
        entries = [
            (COL_DATA, "Display bus (as in M0)", [
                "8 data (blue) + 4 control (orange) — see M0 diagram"]),
            (COL_5V, "+5 V / GND", [
                "rails, straps /RD·FS1, backlight, contrast pot (purple)"]),
        ]
        notes = []
        if m in (1, 2, 3, 4):
            entries.append((COL_SIG, "Test signal (M1)", [
                "D3 →[10 kΩ]→ A7 — the Nano probes its own ~490 Hz PWM"]))
        if m >= 4:
            entries.append((COL_BTN, "Buttons (M4) — short press / long press", [
                "SEC/DIV + (D2): slower sweep / TRIG MODE (AUTO-NORM-ONE)",
                "SEC/DIV − (D12): faster sweep / RUN-STOP (freeze, re-arm)",
                "to GND, internal pull-ups — no resistors needed"]))
        if m >= 5:
            entries.append((COL_SIG, "Signal chain (M5)", [
                "probe → front-end → A7 · D3 →10k→ CAL self-test post"]))
            entries.append((COL_RANGE, "RANGE sense (M5)", [
                "front-end ×1/×10 switch position → A4 (input pull-up)"]))
        if m >= 6:
            entries.append((COL_CH2, "Channel 2 (M6)", [
                "CH2 probe →[10 kΩ + clamps]→ A6"]))
        if m == 2:
            notes = ["No new wiring: M2 adds the software edge trigger",
                     "(poll-then-capture + hysteresis + 250 ms auto free-run)."]
        elif m == 3:
            notes = ["No new wiring: M3 switches the ADC to free-running",
                     "mode, prescaler 16 → ~77 kSps burst captures."]
        elif m == 6:
            notes = ["Pre-trigger, PC streaming, equivalent-time sampling:",
                     "all software — no extra wires."]

    ly = LEG_Y + 54
    for col, title, rows in entries:
        d.rectangle((LEG_X + 22, ly + 4, LEG_X + 64, ly + 22), fill=col,
                    outline=COL_OUTLINE, width=1)
        d.text((LEG_X + 78, ly), title, font=F_LEG, fill=COL_TEXT, anchor="lt")
        ly += 28
        for r in rows:
            d.text((LEG_X + 78, ly), r, font=F_LEGSM, fill=COL_TEXT, anchor="lt")
            ly += 22
        ly += 8
    ly += 6
    for n in notes:
        txt, col = n if isinstance(n, tuple) else (n, COL_TEXT)
        d.text((LEG_X + 20, ly), txt, font=F_LEGSM, fill=col, anchor="lt")
        ly += 24


def render(m):
    fname, title, subtitle = MILESTONES[m]
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((W // 2, 26), f"Arduino Nano + PG240128-A — {title}",
           font=F_TITLE, fill=COL_TEXT, anchor="mt")
    d.text((W // 2, 74), subtitle, font=F_SUB, fill=COL_TEXT, anchor="mt")

    lcd_xy, nano_xy = draw_base(d, m)

    if 1 <= m <= 4:
        draw_test_signal(d, nano_xy, as_cal=False)
    if m >= 4:
        draw_buttons(d, nano_xy)
    if m >= 5:
        draw_test_signal(d, nano_xy, as_cal=True)
        draw_frontend(d, nano_xy)
    if m >= 6:
        draw_ch2(d, nano_xy)
    if m == 2:
        draw_banner(d, "SOFTWARE-ONLY MILESTONE",
                    "Wiring unchanged from M1 — this step adds the trigger.")
    if m == 3:
        draw_banner(d, "SOFTWARE-ONLY MILESTONE",
                    "Wiring unchanged from M1 — this step adds 77 kSps sampling.")

    draw_legend(d, m)
    out = OUTDIR / fname
    img.save(out)
    print(f"Saved: {out}")


if __name__ == "__main__":
    for m in sorted(MILESTONES):
        render(m)
