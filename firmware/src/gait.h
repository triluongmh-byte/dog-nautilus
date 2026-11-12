#pragma once
#include "config.h"
// Open-loop phase/timing gait engine. Pure C++ (host-testable, no Arduino deps).
enum Drive : uint8_t { DRV_STOP = 0, DRV_FWD, DRV_BACK, DRV_LEFT, DRV_RIGHT };
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
  bool moving() const { return drive_ != DRV_STOP && speedPct_ > 0; }
  // Advance dt seconds; fills cmd[] (-1..1, before servo sign).
  void update(float dt, float cmd[LEG_COUNT]);
  bool nudge(int leg, int dir, int ms = NUDGE_MS, float cmd = NUDGE_CMD);  // timed pulse, only when not moving
  void cancelNudge() { nudgeMs_ = 0; }
  bool nudging() const { return nudgeMs_ > 0; }
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
  float est_[LEG_COUNT] = {0, 0, 0, 0};
  int nudgeLeg_ = -1, nudgeDir_ = 0, nudgeMs_ = 0;
  float nudgeCmd_ = NUDGE_CMD;
  float sideRate(bool left) const;
};
