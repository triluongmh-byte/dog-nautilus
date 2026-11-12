#pragma once
#include <Arduino.h>
namespace Web {
void begin();
void loop();
int clients();                 // WebSocket clients currently connected
void pushState(bool force);    // telemetry to all clients (rate limited unless force)
}
