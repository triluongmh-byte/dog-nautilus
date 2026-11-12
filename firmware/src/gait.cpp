#include "gait.h"
#include <math.h>

static const float OFFS[GAIT_COUNT][LEG_COUNT] = {
    /* trot: FL+RR together, FR+RL 180 deg apart */ {0.0f, 0.5f, 0.5f, 0.0f},
    /* walk: FL, RR, FR, RL quarter-cycle apart  */ {0.0f, 0.5f, 0.75f, 0.25f}};

float Gait::wrap(float x) {
  x = x - floorf(x);       // [0,1)
  return x >= 0.5f ? x - 1.0f : x;
}
float Gait::offset(GaitType g, int leg) { return OFFS[g][leg]; }

void Gait::begin(const GaitConfig* cfg) {
  cfg_ = cfg;
  for (int i = 0; i < LEG_COUNT; i++) est_[i] = target(i) + cfg_->savedDelta[i];
}

float Gait::target(int leg) const {
  return phase_[legIsLeft(leg) ? 0 : 1] + OFFS[gait_][leg] + cfg_->phaseTrim[leg];
}
float Gait::delta(int leg) const { return wrap(est_[leg] - target(leg)); }

void Gait::setDrive(Drive d, int pct, GaitType g) {
  if (pct < 0) pct = 0;
  if (pct > 100) pct = 100;
  if (g != gait_) {
    // Keep each leg's estimate-vs-target error unchanged across gait switch.
    float dl[LEG_COUNT];
    for (int i = 0; i < LEG_COUNT; i++) dl[i] = delta(i);
    gait_ = g;
    for (int i = 0; i < LEG_COUNT; i++) est_[i] = target(i) + dl[i];
  }
  drive_ = d;
  speedPct_ = pct;
}

float Gait::sideRate(bool left) const {
  if (drive_ == DRV_STOP || speedPct_ <= 0) return 0;
  float mag = (GAIT_MIN_SPEED_PCT + (100 - GAIT_MIN_SPEED_PCT) * speedPct_ / 100.0f) / 100.0f;
  switch (drive_) {
    case DRV_FWD: return mag;
    case DRV_BACK: return -mag;
    case DRV_LEFT: return left ? mag * TURN_INNER_SCALE : mag;
    case DRV_RIGHT: return left ? mag : mag * TURN_INNER_SCALE;
    default: return 0;
  }
}

bool Gait::nudge(int leg, int dir, int ms, float cmd) {
  if (moving() || leg < 0 || leg >= LEG_COUNT || dir == 0) return false;
  nudgeLeg_ = leg;
  nudgeDir_ = dir > 0 ? 1 : -1;
  nudgeMs_ = ms;
  nudgeCmd_ = cmd;
  return true;
}

void Gait::markZero(int leg) {
  if (leg >= 0 && leg < LEG_COUNT) est_[leg] = target(leg);
}

void Gait::update(float dt, float cmd[LEG_COUNT]) {
  for (int i = 0; i < LEG_COUNT; i++) cmd[i] = 0;
  if (nudgeMs_ > 0) {
    int ms = (int)(dt * 1000.0f + 0.5f);
    float step = fminf((float)nudgeMs_, (float)(ms > 0 ? ms : 1)) / 1000.0f;
    cmd[nudgeLeg_] = nudgeDir_ * nudgeCmd_;
    est_[nudgeLeg_] += cmd[nudgeLeg_] * step / cfg_->secPerRev[nudgeLeg_];
    nudgeMs_ -= (ms > 0 ? ms : 1);
    if (nudgeMs_ < 0) nudgeMs_ = 0;
    return;
  }
  float rate[2] = {sideRate(true), sideRate(false)};
  if (rate[0] == 0 && rate[1] == 0) return;  // standing: neutral pulses
  float meanSpr = 0.1f;
  for (int i = 0; i < LEG_COUNT; i++) meanSpr = fmaxf(meanSpr, cfg_->secPerRev[i]);  // slowest servo sets pace
  phase_[0] += rate[0] * dt / meanSpr;
  phase_[1] += rate[1] * dt / meanSpr;
  if (rate[0] == rate[1]) {  // straight line: gently re-sync the two sides
    float d = wrap(phase_[0] - phase_[1]);
    phase_[1] += 0.5f * d * dt * 4.0f;
  }
  for (int s = 0; s < 2; s++) phase_[s] -= floorf(phase_[s]);
  for (int i = 0; i < LEG_COUNT; i++) {
    float r = rate[legIsLeft(i) ? 0 : 1];
    float corr = PHASE_KP * wrap(target(i) - est_[i]);
    if (corr > PHASE_CMD_TRIM_MAX) corr = PHASE_CMD_TRIM_MAX;
    if (corr < -PHASE_CMD_TRIM_MAX) corr = -PHASE_CMD_TRIM_MAX;
    float c = r == 0 ? 0 : r * cfg_->secPerRev[i] / meanSpr + corr;  // feed-forward + phase P
    if (c > 1) c = 1;
    if (c < -1) c = -1;
    cmd[i] = c;
    est_[i] += c * dt / cfg_->secPerRev[i];
  }
}
