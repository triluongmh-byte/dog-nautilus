#pragma once
#include <Arduino.h>
namespace Oled {
void begin(const String& ssid, const char* pass);
void update(int clients, int batteryPct, float volts, bool lowBatt);  // call often
bool present();
}
