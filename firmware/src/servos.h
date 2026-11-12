#pragma once
#include "config.h"
// LEDC 50 Hz continuous-servo driver. Pins stay unattached (no pulses) until begin().
struct ServoSettings {
  int16_t neutralUs[LEG_COUNT];
  int8_t sign[LEG_COUNT];
};
namespace Servos {
void begin(const ServoSettings* s);   // attach all four, neutral pulses
bool started();
uint32_t usToDuty(int us);            // pure, host-testable
int commandToUs(const ServoSettings& s, int leg, float cmd);  // cmd -1..1, pure
void write(int leg, float cmd);       // cmd -1..1 (sign and trim applied)
void stopAll();                       // neutral pulses on all
}
