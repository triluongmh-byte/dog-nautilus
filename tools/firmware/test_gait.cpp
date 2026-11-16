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
  // direction table: legs 0=FL 1=FR 2=RL 3=RR, left = 0,2
  auto run = [&](Drive d) { g.setDrive(d, 100, GAIT_TROT); g.update(0.01f, cmd); };
  auto L = [&]() { return cmd[0] + cmd[2]; };
  auto R = [&]() { return cmd[1] + cmd[3]; };
  run(DRV_LEFT);  assert(L() < 0 && R() > 0);                 // spin left in place
  run(DRV_RIGHT); assert(L() > 0 && R() < 0);                 // spin right in place
  run(DRV_FL);    assert(L() > 0 && R() > 0 && L() < R());    // forward arc, left inner
  run(DRV_FR);    assert(L() > 0 && R() > 0 && R() < L());
  run(DRV_BL);    assert(L() < 0 && R() < 0 && L() > R());    // back arc, left inner (slower)
  run(DRV_BR);    assert(L() < 0 && R() < 0 && R() > L());
  // joystick mix
  float jl, jr;
  joyMix(0, 1, &jl, &jr);    assert(jl == 1 && jr == 1);                         // push up: straight ahead
  joyMix(-1, 0, &jl, &jr);   assert(fabsf(jl + PIVOT_SCALE) < 1e-5f && fabsf(jr - PIVOT_SCALE) < 1e-5f);  // full left: pivot
  joyMix(0.05f, -0.08f, &jl, &jr); assert(jl == 0 && jr == 0);                   // dead zone
  joyMix(3, 3, &jl, &jr);    assert(jl == 1 && jr == 0);                         // clamped, right arc
  joyMix(0.5f, -1, &jl, &jr); assert(jl < 0 && jr < 0);                          // back arc
  g.setDrive(DRV_JOY, 100, GAIT_TROT); g.setJoy(1, 1); g.update(0.01f, cmd);
  for (int i = 0; i < 4; i++) assert(cmd[i] > 0);
  g.setJoy(-0.7f, 0.7f); g.update(0.01f, cmd); assert(L() < 0 && R() > 0);
  g.setJoy(0, 0); g.update(0.01f, cmd); for (int i = 0; i < 4; i++) assert(cmd[i] == 0);
  // love sway: sides always opposite, ends by itself, net leg turns ~0, F cancels, refused while moving
  g.setDrive(DRV_STOP, 100, GAIT_TROT); g.update(0.01f, cmd);
  assert(g.wiggle());
  float e0[4]; for (int i = 0; i < 4; i++) e0[i] = g.estimate(i);
  int steps = 0, flips = 0; float prev = 0;
  while (g.wiggling() && steps < 1000) {
    g.update(0.01f, cmd); steps++;
    if (!g.wiggling()) break;
    assert(L() * R() < 0);
    if (prev != 0 && (L() > 0) != (prev > 0)) flips++;
    prev = L();
  }
  int expect = 2 * WIGGLE_COUNT * WIGGLE_HALF_MS / 10;
  assert(steps >= expect - 2 && steps <= expect + 2);
  assert(flips == 2 * WIGGLE_COUNT);  // 6 sways = 12 direction changes (incl. the final half swing)
  for (int i = 0; i < 4; i++) assert(fabsf(g.estimate(i) - e0[i]) < 0.02f);
  g.update(0.01f, cmd); for (int i = 0; i < 4; i++) assert(cmd[i] == 0);
  assert(g.wiggle()); g.update(0.01f, cmd); g.setDrive(DRV_FWD, 50, GAIT_TROT); assert(!g.wiggling());
  assert(!g.wiggle());  // moving: no sway
  g.setDrive(DRV_STOP, 50, GAIT_TROT);
  // command parsing
  assert(driveFromCode("F") == DRV_FWD && driveFromCode("B") == DRV_BACK && driveFromCode("L") == DRV_LEFT &&
         driveFromCode("R") == DRV_RIGHT && driveFromCode("FL") == DRV_FL && driveFromCode("FR") == DRV_FR &&
         driveFromCode("BL") == DRV_BL && driveFromCode("BR") == DRV_BR && driveFromCode("S") == DRV_STOP &&
         driveFromCode("X") == DRV_STOP && driveFromCode("") == DRV_STOP);
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
