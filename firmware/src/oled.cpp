#include "oled.h"
#include <Wire.h>
#include <U8g2lib.h>
#include "nqr.h"
#include "config.h"

#if OLED_USE_SSD1309
static U8G2_SSD1309_128X64_NONAME0_F_HW_I2C u8g2(OLED_ROTATION, U8X8_PIN_NONE, PIN_I2C_SCL, PIN_I2C_SDA);
#else
static U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(OLED_ROTATION, U8X8_PIN_NONE, PIN_I2C_SCL, PIN_I2C_SDA);
#endif

static bool g_present = false;
static String g_ssid, g_url = "http://192.168.4.1";
static char g_pass[9];
static uint32_t g_lastDraw = 0;
static int g_lastKey = -1;

static bool probe(uint8_t a) {
  Wire.beginTransmission(a);
  return Wire.endTransmission() == 0;
}
bool Oled::present() { return g_present; }

void Oled::begin(const String& ssid, const char* pass) {
  g_ssid = ssid;
  strncpy(g_pass, pass, 8);
  g_pass[8] = 0;
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL, I2C_FREQ_HZ);
  Wire.setClock(I2C_FREQ_HZ);
  uint8_t addr = OLED_I2C_ADDR;
  if (!probe(addr)) {
    if (probe(OLED_I2C_ADDR_ALT)) addr = OLED_I2C_ADDR_ALT;
    else return;  // no display: robot still works from the phone
  }
  u8g2.setI2CAddress(addr << 1);
  u8g2.begin();
  u8g2.setBusClock(I2C_FREQ_HZ);
  g_present = true;
}

// Draw a QR (lit quiet zone, dark modules) at the left, return nothing.
static void drawQr(const char* text, int version) {
  QRCode qr;
  uint8_t buf[200];
  if (qrcode_getBufferSize(version) > sizeof buf) return;
  if (qrcode_initText(&qr, buf, version, ECC_LOW, text) != 0) return;
  int scale = 60 / qr.size;
  if (scale < 1) scale = 1;
  int side = qr.size * scale;
  int x0 = 2 + 2, y0 = (64 - side) / 2;
  u8g2.setDrawColor(1);
  u8g2.drawBox(x0 - 2, y0 - 2, side + 4, side + 4);
  u8g2.setDrawColor(0);
  for (int y = 0; y < qr.size; y++)
    for (int x = 0; x < qr.size; x++)
      if (qrcode_getModule(&qr, x, y)) u8g2.drawBox(x0 + x * scale, y0 + y * scale, scale, scale);
  u8g2.setDrawColor(1);
}

static void drawSmiley(int batteryPct, float volts) {
  u8g2.drawCircle(32, 32, 26);
  u8g2.drawDisc(23, 24, 3);
  u8g2.drawDisc(41, 24, 3);
  u8g2.drawLine(20, 38, 22, 42);   // mouth: polyline arc
  u8g2.drawLine(22, 42, 27, 45);
  u8g2.drawLine(27, 45, 37, 45);
  u8g2.drawLine(37, 45, 42, 42);
  u8g2.drawLine(42, 42, 44, 38);
  u8g2.setFont(u8g2_font_logisoso24_tn);
  char b[8];
  snprintf(b, sizeof b, "%d%%", batteryPct);
  u8g2.drawStr(70, 40, b);
  u8g2.setFont(u8g2_font_6x10_tr);
  snprintf(b, sizeof b, "%.2fV", volts);
  u8g2.drawStr(78, 56, b);
}

static void drawHeart(int cx, int cy, int r) {  // two discs + a point; r = lobe radius
  u8g2.drawDisc(cx - r, cy - r / 2, r);
  u8g2.drawDisc(cx + r, cy - r / 2, r);
  u8g2.drawTriangle(cx - 2 * r, cy - r / 2 + 1, cx + 2 * r, cy - r / 2 + 1, cx, cy + 2 * r);
}

static void drawLove(int batteryPct) {
  u8g2.drawCircle(32, 32, 26);
  drawHeart(22, 24, 4);
  drawHeart(42, 24, 4);
  u8g2.drawLine(20, 38, 22, 42);  // same smile as drawSmiley
  u8g2.drawLine(22, 42, 27, 45);
  u8g2.drawLine(27, 45, 37, 45);
  u8g2.drawLine(37, 45, 42, 42);
  u8g2.drawLine(42, 42, 44, 38);
  u8g2.setFont(u8g2_font_logisoso24_tn);
  char b[8];
  snprintf(b, sizeof b, "%d%%", batteryPct);
  u8g2.drawStr(70, 40, b);
  drawHeart(96, 52, 3);
}

void Oled::update(int clients, int batteryPct, float volts, bool lowBatt, bool love) {
  if (!g_present) return;
  uint32_t now = millis();
  bool connected = clients > 0;
  int page = love ? 3 : connected ? 2 : (int)((now / QR_PHASE_MS) % 2);
  int key = lowBatt ? 9 : page * 1000 + (connected ? batteryPct : 0);
  if (key == g_lastKey && now - g_lastDraw < 1000) return;
  if (now - g_lastDraw < 250) return;
  g_lastKey = key;
  g_lastDraw = now;
  u8g2.clearBuffer();
  if (lowBatt) {
    u8g2.setFont(u8g2_font_helvB14_tr);
    u8g2.drawStr(8, 24, "LOW BATTERY");
    u8g2.setFont(u8g2_font_6x10_tr);
    char b[24];
    snprintf(b, sizeof b, "%.2f V  %d%%", volts, batteryPct);
    u8g2.drawStr(30, 42, b);
    u8g2.drawStr(12, 58, "Motors stopped. Charge.");
  } else if (page == 0) {
    char w[64];
    snprintf(w, sizeof w, "WIFI:T:WPA;S:%s;P:%s;;", g_ssid.c_str(), g_pass);
    drawQr(w, 3);
    u8g2.setFont(u8g2_font_5x7_tr);
    u8g2.drawStr(68, 10, "1. Join Wi-Fi");
    u8g2.drawStr(68, 22, g_ssid.substring(0, 12).c_str());
    u8g2.drawStr(68, 30, g_ssid.substring(12).c_str());
    u8g2.drawStr(68, 41, "Pass:");
    u8g2.drawStr(68, 50, g_pass);
    u8g2.drawStr(68, 60, "scan QR");
  } else if (page == 1) {
    drawQr(g_url.c_str(), 2);
    u8g2.setFont(u8g2_font_5x7_tr);
    u8g2.drawStr(68, 10, "2. Open page");
    u8g2.drawStr(68, 30, "192.168.4.1");
    u8g2.drawStr(68, 60, "scan QR");
  } else if (page == 3) {
    drawLove(batteryPct);
  } else {
    drawSmiley(batteryPct, volts);
  }
  u8g2.sendBuffer();
}
