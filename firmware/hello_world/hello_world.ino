/*
 * M0 — Hello World: Arduino Nano + PG240128-A (T6963C)
 * Wiring: docs/00-hello-world-nano.md + docs/images/wiring-hello-world.png
 * Library: U8g2 (olikraus)
 *
 * Page-buffer mode (_1_): the Nano's 2 KB of SRAM cannot hold the full
 * 3840-byte framebuffer, so U8g2 draws in 16 slices of 240 bytes.
 * A0..A3 written as digital pin numbers: A0=14, A1=15, A2=16, A3=17.
 */

#include <Arduino.h>
#include <U8g2lib.h>

U8G2_T6963_240X128_1_8080 u8g2(U8G2_R0,
  /*DB0..DB7 =*/ 8, 9, 10, 11, 4, 5, 6, 7,
  /*WR=*/ 17, /*CE=*/ 14, /*C-D=*/ 15, /*RST=*/ 16);

void setup(void) {
  u8g2.begin();   // resets the display and configures the T6963C
}

void loop(void) {
  u8g2.firstPage();
  do {
    // Everything must be drawn inside this loop (runs 16x per frame).
    u8g2.setFont(u8g2_font_ncenB14_tr);
    u8g2.drawStr(24, 40, "Hello, PG240128-A!");
    u8g2.setFont(u8g2_font_6x10_tr);
    u8g2.drawStr(24, 60, "Arduino Nano says hi :)");
    u8g2.drawStr(24, 74, "M0 milestone - oscilloscope next");
    u8g2.drawFrame(0, 0, 240, 128);
    u8g2.drawFrame(2, 2, 236, 124);
    u8g2.drawDisc(210, 95, 12);
    u8g2.drawCircle(180, 95, 12);
  } while (u8g2.nextPage());

  delay(1000);
}
