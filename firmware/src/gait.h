#pragma once
#include "config.h"
// Open-loop phase/timing gait engine. Pure C++ (host-testable, no Arduino deps).
// LEFT/RIGHT = pivot in place (sides opposite); FL/FR/BL/BR = forward/back arcs (inner side slower).
// JOY = continuous left/right side rates from the on-screen joystick (setJoy).
enum Drive : uint8_t { DRV_STOP = 0, DRV_FWD, DRV_BACK, DRV_LEFT, DRV_RIGHT, DRV_FL, DRV_FR, DRV_BL, DRV_BR, DRV_JOY };
Drive driveFromCode(const char* code);  // "F","B","L","R","FL","FR","BL","BR"; anything else -> STOP
// Joystick mix: x right +, y forward +, both -1..1. Per-axis dead zone (JOY_DEADZONE), then
// left = y + x*k, right = y - x*k with k = PIVOT_SCALE at y = 0 rising to 1 at |y| = 1; clamped to +-1.
void joyMix(float x, float y, float* left, float* right);
enum GaitType : uint8_t { GAIT_TROT = 0, GAIT_WALK, GAIT_COUNT };

struct GaitConfig {
  float secPerRev[LEG_COUNT];     // seconds per revolution at 100% command
  float phaseTrim[LEG_COUNT];     // per-leg extra phase offset (rev)
  float savedDelta[LEG_COUNT];    // est - target at save time (restored at boot)
};

class Gait {
 public:
  void begin(const GaitConfig* cfg);
  void setDrive(Drive d, int speedPct, GaitType g);
  void stop() { drive_ = DRV_STOP; }
  void setJoy(float left, float right) { joy_[0] = left; joy_[1] = right; }  // used when drive is DRV_JOY
  bool moving() const { return drive_ != DRV_STOP && speedPct_ > 0; }
  // Advance dt seconds; fills cmd[] (-1..1, before servo sign).
  void update(float dt, float cmd[LEG_COUNT]);
  bool nudge(int leg, int dir, int ms = NUDGE_MS, float cmd = NUDGE_CMD);  // timed pulse, only when not moving
  void cancelNudge() { nudgeMs_ = 0; }
  bool nudging() const { return nudgeMs_ > 0; }
  // "Love" sway: short alternating pivots, net heading ~0. Only from standstill; any move/stop cancels.
  bool wiggle();
  void cancelWiggle() { wiggling_ = false; }
  bool wiggling() const { return wiggling_; }
  void markZero(int leg);                  // current pose = reference pose for this leg
  float estimate(int leg) const { return est_[leg]; }
  float target(int leg) const;
  float delta(int leg) const;              // wrapped est - target
  Drive drive() const { return drive_; }
  static float wrap(float x);              // -> [-0.5, 0.5)
  static float offset(GaitType g, int leg);
 private:
  const GaitConfig* cfg_ = nullptr;
  Drive drive_ = DRV_STOP;
  int speedPct_ = 0;
  GaitType gait_ = GAIT_TROT;
  float phase_[2] = {0, 0};  // [0]=left side master, [1]=right side master
  bool wiggling_ = false;
  float wiggleT_ = 0;        // seconds into the sway
  float joy_[2] = {0, 0};    // joystick side rates -1..1 before the speed limit
  float est_[LEG_COUNT] = {0, 0, 0, 0};
  int nudgeLeg_ = -1, nudgeDir_ = 0, nudgeMs_ = 0;
  float nudgeCmd_ = NUDGE_CMD;
  float sideRate(bool left) const;
};
