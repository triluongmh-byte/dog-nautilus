#include "web.h"
#include <WiFi.h>
#include <WebServer.h>
#include <WebSocketsServer.h>
#include "app.h"
#include "battery.h"
#include "web_pages.h"

static WebServer http(HTTP_PORT);
static WebSocketsServer ws(WS_PORT);
static uint32_t g_lastPush = 0;
static int g_wsClients = 0;

static void sendPage(const char* page) {
  // Assemble from flash once per request; substitute %CSS% and %JS%.
  String s = FPSTR(page);
  s.replace("%CSS%", FPSTR(PAGE_CSS));
  s.replace("%JS%", FPSTR(PAGE_COMMON_JS));
  http.sendHeader("Cache-Control", "no-store");
  http.send(200, "text/html", s);
}

static void calReport(int i) {
  char b[96];
  snprintf(b, sizeof b, "cal %d %d %d %.2f %.2f", i, g_cfg.servo.neutralUs[i], (int)g_cfg.servo.sign[i],
           g_cfg.gait.secPerRev[i], g_gait.delta(i));
  ws.broadcastTXT(b);
}
static void say(const char* m) {
  String s = String("msg ") + m;
  ws.broadcastTXT(s);
}

static void handleCmd(const String& m) {
  g_lastCmdMs = millis();
  char op[12] = {0};
  int a = -1;
  float f = 0;
  int n = sscanf(m.c_str(), "%11s %d %f", op, &a, &f);
  if (n < 1) return;
  String o(op);
  if (o == "hb") return;
  if (o == "drive") {
    char c = m.length() > 6 ? m[6] : 'S';
    g_drive = c == 'F' ? DRV_FWD : c == 'B' ? DRV_BACK : c == 'L' ? DRV_LEFT : c == 'R' ? DRV_RIGHT : DRV_STOP;
    if (g_drive == DRV_STOP) g_gait.cancelNudge();
    appApplyDrive();
  } else if (o == "spd" && n >= 2) {
    g_speedPct = constrain(a, 0, 100);
    appApplyDrive();
  } else if (o == "gait") {
    g_gaitType = m.indexOf("walk") > 0 ? GAIT_WALK : GAIT_TROT;
    appApplyDrive();
  } else if (a >= 0 && a < LEG_COUNT) {
    if (o == "nudge" && n >= 3) {
      if (!g_gait.nudge(a, (int)f)) say("stop first");
    } else if (o == "spin") {
      if (!g_gait.nudge(a, 1, 5000, 1.0f)) say("stop first");
    } else if (o == "trim" && n >= 3) {
      g_cfg.servo.neutralUs[a] = constrain(g_cfg.servo.neutralUs[a] + (int)f,
                                           SERVO_NEUTRAL_DEFAULT_US - SERVO_TRIM_LIMIT_US,
                                           SERVO_NEUTRAL_DEFAULT_US + SERVO_TRIM_LIMIT_US);
    } else if (o == "sign") {
      g_cfg.servo.sign[a] = -g_cfg.servo.sign[a];
    } else if (o == "zero") {
      g_gait.markZero(a);
    } else if (o == "rev" && n >= 3 && f >= 0.2f && f <= 20.0f) {
      g_cfg.gait.secPerRev[a] = f;
    }
    calReport(a);
  } else if (o == "save") {
    Store::save(g_cfg, g_gait);
    say("saved");
  }
}

static void onWs(uint8_t num, WStype_t type, uint8_t* payload, size_t len) {
  if (type == WStype_DISCONNECTED) {
    g_wsClients = max(0, g_wsClients - 1);
    if (g_wsClients == 0) { g_drive = DRV_STOP; g_gait.cancelNudge(); appApplyDrive(); }
  } else if (type == WStype_CONNECTED) {
    g_wsClients++;
    g_lastCmdMs = millis();
    Web::pushState(true);
    for (int i = 0; i < LEG_COUNT; i++) calReport(i);
  } else if (type == WStype_TEXT && len < 48) {
    handleCmd(String((const char*)payload));
  }
}

void Web::begin() {
  http.on("/", []() { sendPage(PAGE_INDEX); });
  http.on("/cal", []() { sendPage(PAGE_CAL); });
  http.onNotFound([]() { http.sendHeader("Location", "/"); http.send(302); });
  http.begin();
  ws.begin();
  ws.onEvent(onWs);
}
void Web::loop() {
  http.handleClient();
  ws.loop();
}
int Web::clients() { return g_wsClients; }
void Web::pushState(bool force) {
  uint32_t now = millis();
  if (!force && now - g_lastPush < 1000) return;
  g_lastPush = now;
  char b[64];
  snprintf(b, sizeof b, "st %d %.2f %d %d %d", Battery::percent(), Battery::volts(), Battery::lowLatched() ? 1 : 0,
           (int)g_drive, (int)g_gaitType);
  ws.broadcastTXT(b);
}
