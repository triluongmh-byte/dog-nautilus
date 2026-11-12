// Host test of the pure logic (gait + servo pulse math). Run via tools/firmware/check.sh host.
#define HOST_TEST 1
#include "../../firmware/src/gait.h"
#include "../../firmware/src/servos.h"
#include <cassert>
#include <cmath>
#include <cstdio>
int main() {
  GaitConfig c;
  for (int i = 0; i < 4; i++) { c.secPerRev[i] = 1.0f + 0.1f * i; c.phaseTrim[i] = 0; c.savedDelta[i] = 0; }
  c.savedDelta[2] = 0.3f;  // RL starts out of phase; controller must pull it in
  Gait g; g.begin(&c);
  g.setDrive(DRV_FWD, 80, GAIT_TROT);
  float cmd[4];
  for (int t = 0; t < 1500; t++) g.update(0.01f, cmd);  // 15 s
  for (int i = 0; i < 4; i++) assert(fabsf(g.delta(i)) < 0.02f);
  // trot: FL vs FR 180 deg apart, FL vs RR together
  assert(fabsf(fabsf(Gait::wrap(g.estimate(0) - g.estimate(1))) - 0.5f) < 0.03f);
  assert(fabsf(Gait::wrap(g.estimate(0) - g.estimate(3))) < 0.03f);
  // reverse
  g.setDrive(DRV_BACK, 50, GAIT_TROT); g.update(0.01f, cmd);
  for (int i = 0; i < 4; i++) assert(cmd[i] < 0);
  // turn left: left side slower
  g.setDrive(DRV_LEFT, 100, GAIT_TROT); g.update(0.01f, cmd);
  assert(cmd[0] < cmd[1] && cmd[2] < cmd[3]);
  // stop -> zero command
  g.setDrive(DRV_STOP, 100, GAIT_TROT); g.update(0.01f, cmd);
  for (int i = 0; i < 4; i++) assert(cmd[i] == 0);
  // nudge only when stopped, lasts ~NUDGE_MS
  assert(g.nudge(1, +1));
  int n = 0; do { g.update(0.01f, cmd); n++; } while (g.nudging() && n < 100);
  assert(n >= NUDGE_MS / 10 - 1 && n <= NUDGE_MS / 10 + 1);
  g.markZero(1); assert(fabsf(g.delta(1)) < 1e-4f);
  // servo math
  ServoSettings s; for (int i = 0; i < 4; i++) { s.neutralUs[i] = 1500; s.sign[i] = (i & 1) ? -1 : 1; }
  assert(Servos::commandToUs(s, 0, 0) == 1500);
  assert(Servos::commandToUs(s, 0, 1) == 1900 && Servos::commandToUs(s, 1, 1) == 1100);
  assert(Servos::commandToUs(s, 0, 5) == 1900);
  s.neutralUs[0] = 1980; assert(Servos::commandToUs(s, 0, 1) == 2000);
  assert(Servos::usToDuty(1500) == (16383ull * 1500) / 20000);
  puts("host tests OK");
}
