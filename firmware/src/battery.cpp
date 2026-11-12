#include "battery.h"
#ifndef HOST_TEST
#include <Arduino.h>
#endif

float Battery::percentFromVolts(float v) {
  float p = (v - VBAT_EMPTY_V) / (VBAT_FULL_V - VBAT_EMPTY_V) * 100.0f;
  return p < 0 ? 0 : (p > 100 ? 100 : p);
}
float Battery::voltsFromAdcMv(float mv) { return mv / 1000.0f * VBAT_DIVIDER_RATIO + VBAT_OFFSET_V; }

#ifndef HOST_TEST
static float g_v = 0;
static bool g_low = false, g_have = false;
static uint32_t g_lastMs = 0, g_lowSince = 0;

void Battery::begin() {
  analogSetPinAttenuation(PIN_VBAT_SENSE, ADC_11db);
  analogReadResolution(12);
  g_lastMs = 0;
  update();
}
void Battery::update() {
  uint32_t now = millis();
  if (g_have && now - g_lastMs < 100) return;
  g_lastMs = now;
  uint32_t acc = 0;
  for (int i = 0; i < VBAT_SAMPLES; i++) acc += analogReadMilliVolts(PIN_VBAT_SENSE);
  float v = voltsFromAdcMv(acc / (float)VBAT_SAMPLES);
  g_v = g_have ? g_v * 0.9f + v * 0.1f : v;
  g_have = true;
  if (g_v < LOW_BATT_CUTOFF_V) {
    if (!g_lowSince) g_lowSince = now ? now : 1;
    if (now - g_lowSince >= LOW_BATT_DEBOUNCE_MS) g_low = true;
  } else {
    g_lowSince = 0;
    if (g_v > LOW_BATT_RESUME_V) g_low = false;
  }
}
float Battery::volts() { return g_v; }
int Battery::percent() { return (int)(percentFromVolts(g_v) + 0.5f); }
bool Battery::lowLatched() { return g_low; }
#endif
