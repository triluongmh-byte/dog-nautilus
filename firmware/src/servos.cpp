#include "servos.h"
#include <math.h>
#ifndef HOST_TEST
#include <Arduino.h>
#endif

static const ServoSettings* g_s = nullptr;
static bool g_started = false;

uint32_t Servos::usToDuty(int us) {
  const uint32_t maxDuty = (1u << SERVO_LEDC_BITS) - 1;
  uint64_t period_us = 1000000ull / SERVO_FREQ_HZ;
  return (uint32_t)(((uint64_t)us * maxDuty) / period_us);
}

int Servos::commandToUs(const ServoSettings& s, int leg, float cmd) {
  if (cmd > 1) cmd = 1;
  if (cmd < -1) cmd = -1;
  int us = s.neutralUs[leg] + (int)lroundf(cmd * s.sign[leg] * SERVO_FULL_SPEED_DELTA_US);
  if (us < SERVO_PULSE_MIN_US) us = SERVO_PULSE_MIN_US;
  if (us > SERVO_PULSE_MAX_US) us = SERVO_PULSE_MAX_US;
  return us;
}

bool Servos::started() { return g_started; }

#ifndef HOST_TEST
void Servos::begin(const ServoSettings* s) {
  g_s = s;
  for (int i = 0; i < LEG_COUNT; i++) {
    ledcSetup(i, SERVO_FREQ_HZ, SERVO_LEDC_BITS);
    ledcWrite(i, usToDuty(commandToUs(*g_s, i, 0)));
    ledcAttachPin(SERVO_PINS[i], i);
  }
  g_started = true;
}
void Servos::write(int leg, float cmd) {
  if (!g_started) return;
  ledcWrite(leg, usToDuty(commandToUs(*g_s, leg, cmd)));
}
#else
void Servos::begin(const ServoSettings* s) { g_s = s; g_started = true; }
void Servos::write(int, float) {}
#endif

void Servos::stopAll() {
  for (int i = 0; i < LEG_COUNT; i++) write(i, 0);
}
