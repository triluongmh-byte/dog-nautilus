#include "settings.h"
#include <Arduino.h>
#include <Preferences.h>
#include <esp_system.h>

static Preferences prefs;

void Store::defaults(Settings& s) {
  for (int i = 0; i < LEG_COUNT; i++) {
    s.servo.neutralUs[i] = SERVO_NEUTRAL_DEFAULT_US;
    s.servo.sign[i] = SERVO_SIGN_DEFAULT[i];
    s.gait.secPerRev[i] = DEFAULT_SEC_PER_REV;
    s.gait.phaseTrim[i] = 0;
    s.gait.savedDelta[i] = 0;
  }
  s.apPass[0] = 0;
}

static void makePass(char* out) {
  static const char alpha[] = "abcdefghjkmnpqrstuvwxyz23456789";  // no look-alikes
  for (int i = 0; i < 8; i++) out[i] = alpha[esp_random() % (sizeof(alpha) - 1)];
  out[8] = 0;
}

void Store::load(Settings& s) {
  defaults(s);
  prefs.begin("dog", false);
  for (int i = 0; i < LEG_COUNT; i++) {
    char k[8];
    snprintf(k, sizeof k, "n%d", i);
    s.servo.neutralUs[i] = constrain((int)prefs.getShort(k, SERVO_NEUTRAL_DEFAULT_US),
                                     SERVO_NEUTRAL_DEFAULT_US - SERVO_TRIM_LIMIT_US,
                                     SERVO_NEUTRAL_DEFAULT_US + SERVO_TRIM_LIMIT_US);
    snprintf(k, sizeof k, "s%d", i);
    s.servo.sign[i] = prefs.getChar(k, SERVO_SIGN_DEFAULT[i]) < 0 ? -1 : 1;
    snprintf(k, sizeof k, "r%d", i);
    float r = prefs.getFloat(k, DEFAULT_SEC_PER_REV);
    s.gait.secPerRev[i] = (r >= 0.2f && r <= 20.0f) ? r : DEFAULT_SEC_PER_REV;
    snprintf(k, sizeof k, "p%d", i);
    s.gait.phaseTrim[i] = prefs.getFloat(k, 0);
    snprintf(k, sizeof k, "d%d", i);
    s.gait.savedDelta[i] = prefs.getFloat(k, 0);
  }
  String p = prefs.getString("pw", "");
  if (p.length() == 8) {
    strcpy(s.apPass, p.c_str());
  } else {
    makePass(s.apPass);
    prefs.putString("pw", s.apPass);
  }
  prefs.end();
}

void Store::save(const Settings& s, const Gait& g) {
  prefs.begin("dog", false);
  for (int i = 0; i < LEG_COUNT; i++) {
    char k[8];
    snprintf(k, sizeof k, "n%d", i);
    prefs.putShort(k, s.servo.neutralUs[i]);
    snprintf(k, sizeof k, "s%d", i);
    prefs.putChar(k, s.servo.sign[i]);
    snprintf(k, sizeof k, "r%d", i);
    prefs.putFloat(k, s.gait.secPerRev[i]);
    snprintf(k, sizeof k, "p%d", i);
    prefs.putFloat(k, s.gait.phaseTrim[i]);
    snprintf(k, sizeof k, "d%d", i);
    prefs.putFloat(k, g.delta(i));
  }
  prefs.end();
}
