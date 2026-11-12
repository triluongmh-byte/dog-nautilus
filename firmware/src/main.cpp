// Nautilus Dog V0 firmware: ESP32-C3 SuperMini, Arduino-ESP32.
#include <Arduino.h>
#include <WiFi.h>
#include "app.h"
#include "battery.h"
#include "oled.h"
#include "servos.h"
#include "web.h"

Settings g_cfg;
Gait g_gait;
uint32_t g_lastCmdMs = 0;
int g_speedPct = 50;
GaitType g_gaitType = GAIT_TROT;
Drive g_drive = DRV_STOP;

void appApplyDrive() {
  if (Battery::lowLatched()) g_gait.setDrive(DRV_STOP, 0, g_gaitType);
  else g_gait.setDrive(g_drive, g_speedPct, g_gaitType);
}

static String apName() {
  uint8_t mac[6];
  WiFi.macAddress(mac);
  char b[8];
  snprintf(b, sizeof b, "%02X%02X", mac[4], mac[5]);
  return String(AP_SSID_PREFIX) + b;
}

void setup() {
  // Expansion GPIOs: high-Z inputs. GPIO0/2/20/21 and the GPIO8 LED are never driven.
  pinMode(PIN_EXP_IO_A, INPUT);
  pinMode(PIN_EXP_IO_B, INPUT);
  Serial.begin(115200);  // USB-CDC; never blocks waiting for a host

  Store::load(g_cfg);
  g_gait.begin(&g_cfg.gait);
  Battery::begin();

  String ssid = apName();
  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(IPAddress(192, 168, 4, 1), IPAddress(192, 168, 4, 1), IPAddress(255, 255, 255, 0));
  WiFi.softAP(ssid.c_str(), g_cfg.apPass, AP_CHANNEL, 0, AP_MAX_CLIENTS);
  Web::begin();
  Oled::begin(ssid, g_cfg.apPass);

  Servos::begin(&g_cfg.servo);  // PWM starts here: neutral (stop) pulses on all four
  g_lastCmdMs = millis();
}

void loop() {
  static uint32_t lastTick = 0;
  uint32_t now = millis();

  Web::loop();
  Battery::update();

  // Command watchdog and low-battery stop.
  if (now - g_lastCmdMs > WATCHDOG_MS && g_drive != DRV_STOP) {
    g_drive = DRV_STOP;
    g_gait.cancelNudge();
  }
  if (Battery::lowLatched()) g_gait.cancelNudge();
  appApplyDrive();

  if (now - lastTick >= GAIT_TICK_MS) {
    float dt = (now - lastTick) / 1000.0f;
    if (dt > 0.1f) dt = 0.1f;
    lastTick = now;
    float cmd[LEG_COUNT];
    g_gait.update(dt, cmd);
    for (int i = 0; i < LEG_COUNT; i++) Servos::write(i, cmd[i]);
  }

  Web::pushState(false);
  Oled::update(WiFi.softAPgetStationNum(), Battery::percent(), Battery::volts(), Battery::lowLatched());
}
