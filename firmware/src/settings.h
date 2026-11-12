#pragma once
#include "config.h"
#include "gait.h"
#include "servos.h"
// NVS-backed (Preferences, namespace "dog") calibration + Wi-Fi password.
struct Settings {
  ServoSettings servo;
  GaitConfig gait;
  char apPass[9];  // 8 chars + NUL, generated on first boot
};
namespace Store {
void load(Settings& s);   // defaults for anything missing
void save(const Settings& s, const Gait& g);
void defaults(Settings& s);
}
