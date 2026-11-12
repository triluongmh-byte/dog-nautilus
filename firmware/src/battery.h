#pragma once
#include "config.h"
namespace Battery {
float percentFromVolts(float v);      // 6.4 V=0%, 8.4 V=100%, linear, clamped (pure)
float voltsFromAdcMv(float adcMv);    // adc volts * divider ratio + offset (pure)
void begin();
void update();                        // call often; samples every 100 ms
float volts();
int percent();
bool lowLatched();                    // true => servos must stay stopped
}
