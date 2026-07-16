"""Generate the wiring diagram for the hello-world milestone:
Arduino Nano + PG240128-A (T6963C), matching docs/00-hello-world-nano.md.

Technique borrowed from multi-rocket-avionica/breadboard-wiring/
wiring_diagram.py: pure-PIL modules with pin circles and orthogonal,
color-coded wire bundles + legend.

Run:  python3 tools/wiring_hello_world.py
Out:  docs/images/wiring-hello-world.png
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "docs" / "images" / "wiring-hello-world.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

# --- Canvas -----------------------------------------------------------
W, H = 1900, 1320
BG = (250, 250, 248)
img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# --- Fonts ------------------------------------------------------------
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

# --- Colors -----------------------------------------------------------
COL_5V    = (215, 40, 40)     # red    — +5 V
COL_GND   = (35, 35, 40)      # black  — GND
COL_DATA  = (40, 110, 220)    # blue   — DB0..DB7
COL_CTRL  = (235, 140, 20)    # orange — /CE, C/D, /RST, /WR
COL_POT   = (150, 60, 200)    # purple — contrast (Vo / Vee)

COL_LCD_BOARD = (18, 92, 62)
COL_LCD_GLASS = (200, 208, 184)
COL_NANO      = (28, 70, 150)
COL_POT_BODY  = (70, 70, 78)
COL_RES_BODY  = (222, 196, 150)
COL_TEXT       = (25, 25, 30)
COL_TEXT_LIGHT = (252, 252, 250)
COL_OUTLINE    = (40, 40, 50)
COL_PIN_FILL   = (245, 235, 110)

# --- Title ------------------------------------------------------------
d.text((W // 2, 26), "Arduino Nano + PG240128-A — Hello World wiring",
       font=F_TITLE, fill=COL_TEXT, anchor="mt")
d.text((W // 2, 74),
       "12 signal wires + power + contrast pot + backlight."
       "   Matches docs/00-hello-world-nano.md — pin map is oscilloscope-ready.",
       font=F_SUB, fill=COL_TEXT, anchor="mt")

# =====================================================================
# PG240128-A display — top, 20-pin header on the BOTTOM edge
# =====================================================================
LCD_X0, LCD_Y0 = 150, 140
LCD_W,  LCD_H  = 1100, 320
LCD_X1, LCD_Y1 = LCD_X0 + LCD_W, LCD_Y0 + LCD_H

d.rounded_rectangle((LCD_X0, LCD_Y0, LCD_X1, LCD_Y1), radius=12,
                    fill=COL_LCD_BOARD, outline=COL_OUTLINE, width=3)
# glass
d.rounded_rectangle((LCD_X0 + 70, LCD_Y0 + 42, LCD_X1 - 70, LCD_Y1 - 92),
                    radius=6, fill=COL_LCD_GLASS, outline=COL_OUTLINE, width=2)
d.text(((LCD_X0 + LCD_X1) // 2, (LCD_Y0 + LCD_Y1) // 2 - 30),
       "PG240128-A", font=F_MOD, fill=COL_TEXT, anchor="mm")
d.text(((LCD_X0 + LCD_X1) // 2, (LCD_Y0 + LCD_Y1) // 2 + 4),
       "240 × 128 · T6963C", font=F_MODSUB, fill=COL_TEXT, anchor="mm")

PIN_R = 9
LCD_PINS = ["Vss", "Vdd", "Vo", "C/D", "/RD", "/WR",
            "DB0", "DB1", "DB2", "DB3", "DB4", "DB5", "DB6", "DB7",
            "/CE", "/RST", "Vee", "MD2", "FS1", "NC"]
lcd_xy = {}
pitch = LCD_W / 21.0
for i, name in enumerate(LCD_PINS):
    px = LCD_X0 + pitch * (i + 1)
    py = LCD_Y1
    d.ellipse((px - PIN_R, py - PIN_R, px + PIN_R, py + PIN_R),
              fill=COL_PIN_FILL, outline=COL_OUTLINE, width=2)
    # label inside the board, alternating two rows: "n·NAME"
    row_y = py - 24 if i % 2 == 0 else py - 50
    d.text((px, row_y), f"{i + 1}", font=F_PINSM,
           fill=(255, 220, 170), anchor="mb")
    d.text((px, row_y + 16), name, font=F_PIN,
           fill=COL_TEXT_LIGHT, anchor="mb")
    lcd_xy[name] = (px, py)

# Backlight pads on the RIGHT edge
BL_A = (LCD_X1, LCD_Y0 + 120)
BL_K = (LCD_X1, LCD_Y0 + 180)
for (px, py), lab in ((BL_A, "A"), (BL_K, "K")):
    d.ellipse((px - PIN_R, py - PIN_R, px + PIN_R, py + PIN_R),
              fill=COL_PIN_FILL, outline=COL_OUTLINE, width=2)
    d.text((px - 18, py), lab, font=F_PIN, fill=COL_TEXT_LIGHT, anchor="rm")
d.text((LCD_X1 - 18, LCD_Y0 + 92), "backlight", font=F_MODSUB,
       fill=COL_TEXT_LIGHT, anchor="rm")

# =====================================================================
# Power rails (breadboard style)
# =====================================================================
RAIL_5V_Y  = 640
RAIL_GND_Y = 668
RAIL_X0, RAIL_X1 = 170, 1620
d.line([(RAIL_X0, RAIL_5V_Y), (RAIL_X1, RAIL_5V_Y)], fill=COL_5V, width=7)
d.line([(RAIL_X0, RAIL_GND_Y), (RAIL_X1, RAIL_GND_Y)], fill=COL_GND, width=7)
d.text((RAIL_X1 + 12, RAIL_5V_Y), "+5 V rail", font=F_LEG, fill=COL_5V, anchor="lm")
d.text((RAIL_X1 + 12, RAIL_GND_Y), "GND rail", font=F_LEG, fill=COL_GND, anchor="lm")

# =====================================================================
# Arduino Nano — bottom center, USB at the BOTTOM (top view)
# With USB down: LEFT column top→bottom  = VIN GND RST 5V A7 A6 A5 A4 A3 A2 A1 A0 AREF 3V3 D13
#                RIGHT column top→bottom = TX1 RX0 RST GND D2 D3 D4 D5 D6 D7 D8 D9 D10 D11 D12
# =====================================================================
NANO_X0, NANO_Y0 = 620, 720
NANO_W,  NANO_H  = 300, 510
NANO_X1, NANO_Y1 = NANO_X0 + NANO_W, NANO_Y0 + NANO_H

d.rounded_rectangle((NANO_X0, NANO_Y0, NANO_X1, NANO_Y1), radius=12,
                    fill=COL_NANO, outline=COL_OUTLINE, width=3)
# USB at bottom
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

NANO_LEFT  = ["VIN", "GND", "RST", "5V", "A7", "A6", "A5", "A4",
              "A3", "A2", "A1", "A0", "AREF", "3V3", "D13"]
NANO_RIGHT = ["TX1", "RX0", "RST2", "GND2", "D2", "D3", "D4", "D5",
              "D6", "D7", "D8", "D9", "D10", "D11", "D12"]
NANO_LABEL = {"RST2": "RST", "GND2": "GND"}

nano_xy = {}
N_PITCH = 30
N_TOP   = NANO_Y0 + 40
for i, name in enumerate(NANO_LEFT):
    x, y = NANO_X0, N_TOP + i * N_PITCH
    d.ellipse((x - PIN_R, y - PIN_R, x + PIN_R, y + PIN_R),
              fill=COL_PIN_FILL, outline=COL_OUTLINE, width=2)
    d.text((x + 16, y), name, font=F_PIN, fill=COL_TEXT_LIGHT, anchor="lm")
    nano_xy[name] = (x, y)
for i, name in enumerate(NANO_RIGHT):
    x, y = NANO_X1, N_TOP + i * N_PITCH
    d.ellipse((x - PIN_R, y - PIN_R, x + PIN_R, y + PIN_R),
              fill=COL_PIN_FILL, outline=COL_OUTLINE, width=2)
    d.text((x - 16, y), NANO_LABEL.get(name, name), font=F_PIN,
           fill=COL_TEXT_LIGHT, anchor="rm")
    nano_xy[name] = (x, y)

# =====================================================================
# Contrast pot — bottom left, 3 pins on TOP edge
# =====================================================================
POT_X0, POT_Y0 = 180, 800
POT_W,  POT_H  = 170, 130
d.rounded_rectangle((POT_X0, POT_Y0, POT_X0 + POT_W, POT_Y0 + POT_H),
                    radius=10, fill=COL_POT_BODY, outline=COL_OUTLINE, width=3)
d.ellipse((POT_X0 + POT_W//2 - 32, POT_Y0 + POT_H//2 - 24,
           POT_X0 + POT_W//2 + 32, POT_Y0 + POT_H//2 + 40),
          fill=(120, 120, 128), outline=COL_OUTLINE, width=2)
d.text((POT_X0 + POT_W//2, POT_Y0 + POT_H + 12), "Contrast pot 10 kΩ",
       font=F_MODSUB, fill=COL_TEXT, anchor="mt")
POT_L = (POT_X0 + 30,  POT_Y0)   # outer leg -> +5V
POT_M = (POT_X0 + 85,  POT_Y0)   # wiper     -> Vo
POT_R = (POT_X0 + 140, POT_Y0)   # outer leg -> Vee
for (px, py), lab in ((POT_L, "+5V"), (POT_M, "wiper"), (POT_R, "Vee")):
    d.ellipse((px - PIN_R, py - PIN_R, px + PIN_R, py + PIN_R),
              fill=COL_PIN_FILL, outline=COL_OUTLINE, width=2)
    d.text((px, py + 16), lab, font=F_PINSM, fill=COL_TEXT_LIGHT, anchor="mt")

# =====================================================================
# Backlight resistor — right of the display
# =====================================================================
RES_X0, RES_Y0 = 1340, BL_A[1] - 20
RES_W,  RES_H  = 110, 40
d.rounded_rectangle((RES_X0, RES_Y0, RES_X0 + RES_W, RES_Y0 + RES_H),
                    radius=8, fill=COL_RES_BODY, outline=COL_OUTLINE, width=3)
d.text((RES_X0 + RES_W//2, RES_Y0 + RES_H//2), "12 Ω",
       font=F_PIN, fill=COL_TEXT, anchor="mm")
d.text((RES_X0 + RES_W//2, RES_Y0 + RES_H + 8), "≥ 0.5 W",
       font=F_PINSM, fill=COL_TEXT, anchor="mt")

# =====================================================================
# Wire helpers
# =====================================================================
WIRE_W = 5

def wire(points, color):
    for i in range(len(points) - 1):
        d.line([points[i], points[i + 1]], fill=color, width=WIRE_W)
    for pt in (points[0], points[-1]):
        d.ellipse((pt[0] - 7, pt[1] - 7, pt[0] + 7, pt[1] + 7),
                  fill=color, outline=COL_OUTLINE, width=1)

# ---------------------------------------------------------------------
# Power: rails fed from the Nano, display + straps tap the rails
# ---------------------------------------------------------------------
# Nano 5V / GND feed the rails (exit LEFT of the Nano)
x, y = nano_xy["5V"];  wire([(x, y), (x - 120, y), (x - 120, RAIL_5V_Y)], COL_5V)
x, y = nano_xy["GND"]; wire([(x, y), (x - 150, y), (x - 150, RAIL_GND_Y)], COL_GND)

# Display power + straps (straight vertical taps)
x, y = lcd_xy["Vss"];  wire([(x, y), (x, RAIL_GND_Y)], COL_GND)   # 1  Vss -> GND
x, y = lcd_xy["Vdd"];  wire([(x, y), (x, RAIL_5V_Y)],  COL_5V)    # 2  Vdd -> +5V
x, y = lcd_xy["/RD"];  wire([(x, y), (x, RAIL_5V_Y)],  COL_5V)    # 5  /RD -> +5V (strap!)
x, y = lcd_xy["FS1"];  wire([(x, y), (x, RAIL_GND_Y)], COL_GND)   # 19 FS1 -> GND (strap!)

# Backlight: +5V rail -> 12Ω -> A ; K -> GND rail
wire([(RES_X0 + RES_W, RES_Y0 + RES_H // 2), (1500, RES_Y0 + RES_H // 2),
      (1500, RAIL_5V_Y)], COL_5V)
wire([(BL_A[0], BL_A[1]), (RES_X0, RES_Y0 + RES_H // 2)], COL_5V)
wire([(BL_K[0], BL_K[1]), (1460, BL_K[1]), (1460, RAIL_GND_Y)], COL_GND)

# Contrast pot (purple = contrast net)
wire([POT_L, (POT_L[0], RAIL_5V_Y)], COL_5V)                       # leg -> +5V rail
vx, vy = lcd_xy["Vo"]
wire([POT_M, (POT_M[0], 470), (vx, 470), (vx, vy)], COL_POT)       # wiper -> Vo (3)
ex, ey = lcd_xy["Vee"]
wire([POT_R, (POT_R[0], 630), (ex, 630), (ex, ey)], COL_POT)       # leg -> Vee (17)

# ---------------------------------------------------------------------
# Data bus (blue): DB0..DB7 -> D8 D9 D10 D11 D4 D5 D6 D7
# Lanes assigned right-to-left; channel x sorted by target pin height
# so blue wires cross as little as possible.
# ---------------------------------------------------------------------
DATA_MAP = [("DB0", "D8"), ("DB1", "D9"), ("DB2", "D10"), ("DB3", "D11"),
            ("DB4", "D4"), ("DB5", "D5"), ("DB6", "D6"), ("DB7", "D7")]
lane_of = {"DB7": 480, "DB6": 492, "DB5": 504, "DB4": 516,
           "DB3": 528, "DB2": 540, "DB1": 552, "DB0": 564}
chan_of = {"D4": 984, "D5": 996, "D6": 1008, "D7": 1020,
           "D8": 1032, "D9": 1044, "D10": 1056, "D11": 1068}
for db, dpin in DATA_MAP:
    sx, sy = lcd_xy[db]
    tx, ty = nano_xy[dpin]
    lane, chan = lane_of[db], chan_of[dpin]
    wire([(sx, sy), (sx, lane), (chan, lane), (chan, ty), (tx, ty)], COL_DATA)

# ---------------------------------------------------------------------
# Control (orange): /CE->A0  C/D->A1  /RST->A2  /WR->A3  (Nano LEFT side)
# ---------------------------------------------------------------------
CTRL = [("/RST", "A2", 576, 584),
        ("/CE",  "A0", 588, 560),
        ("/WR",  "A3", 600, 596),
        ("C/D",  "A1", 612, 572)]
for sig, apin, lane, chan in CTRL:
    sx, sy = lcd_xy[sig]
    tx, ty = nano_xy[apin]
    wire([(sx, sy), (sx, lane), (chan, lane), (chan, ty), (tx, ty)], COL_CTRL)

# =====================================================================
# Legend — bottom right
# =====================================================================
LEG_X, LEG_Y = 1250, 760
LEG_W, LEG_H = 620, 470
d.rounded_rectangle((LEG_X, LEG_Y, LEG_X + LEG_W, LEG_Y + LEG_H),
                    radius=10, fill=(255, 255, 255),
                    outline=COL_OUTLINE, width=2)
d.text((LEG_X + 20, LEG_Y + 14), "Wire color → function",
       font=F_LEG, fill=COL_TEXT, anchor="lt")

legend = [
    (COL_DATA, "Data bus DB0–DB7 (8 wires)", [
        "DB0→D8   DB1→D9   DB2→D10  DB3→D11",
        "DB4→D4   DB5→D5   DB6→D6   DB7→D7",
    ]),
    (COL_CTRL, "Control (4 wires)", [
        "/CE(15)→A0   C/D(4)→A1   /RST(16)→A2   /WR(6)→A3",
    ]),
    (COL_5V, "+5 V", [
        "Vdd(2), /RD(5) strap, pot leg, 12Ω → backlight A",
    ]),
    (COL_GND, "GND", [
        "Vss(1), FS1(19) strap, backlight K",
    ]),
    (COL_POT, "Contrast", [
        "pot wiper → Vo(3)    pot leg → Vee(17)",
        "Vee is an OUTPUT: only the pot connects to it",
    ]),
]
ly = LEG_Y + 54
for col, title, rows in legend:
    d.rectangle((LEG_X + 22, ly + 4, LEG_X + 64, ly + 22), fill=col,
                outline=COL_OUTLINE, width=1)
    d.text((LEG_X + 78, ly), title, font=F_LEG, fill=COL_TEXT, anchor="lt")
    ly += 28
    for r in rows:
        d.text((LEG_X + 78, ly), r, font=F_LEGSM, fill=COL_TEXT, anchor="lt")
        ly += 22
    ly += 8

d.text((LEG_X + 20, LEG_Y + LEG_H - 90),
       "MD2 (18) and NC (20): leave unconnected.",
       font=F_LEGSM, fill=COL_TEXT, anchor="lt")
d.text((LEG_X + 20, LEG_Y + LEG_H - 66),
       "Kept free for the scope: A7 probe · A6 ch2 · D2/D3 encoder · D12/D13.",
       font=F_LEGSM, fill=COL_TEXT, anchor="lt")
d.text((LEG_X + 20, LEG_Y + LEG_H - 42),
       "Blank screen? Sweep the contrast pot slowly end to end first.",
       font=F_LEGSM, fill=(180, 40, 40), anchor="lt")

img.save(OUT)
print(f"Saved: {OUT}")
