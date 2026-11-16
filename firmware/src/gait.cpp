#include "gait.h"
#include <math.h>
#include <string.h>

static const float OFFS[GAIT_COUNT][LEG_COUNT] = {
    /* trot: FL+RR together, FR+RL 180 deg apart */ {0.0f, 0.5f, 0.5f, 0.0f},
    /* walk: FL, RR, FR, RL quarter-cycle apart  */ {0.0f, 0.5f, 0.75f, 0.25f}};

float Gait::wrap(float x) {
  x = x - floorf(x);       // [0,1)
  return x >= 0.5f ? x - 1.0f : x;
}
float Gait::offset(GaitType g, int leg) { return OFFS[g][leg]; }

Drive driveFromCode(const char* c) {
  static const char* const CODES[] = {"F", "B", "L", "R", "FL", "FR", "BL", "BR"};
  static const Drive DRIVES[] = {DRV_FWD, DRV_BACK, DRV_LEFT, DRV_RIGHT, DRV_FL, DRV_FR, DRV_BL, DRV_BR};
  for (int i = 0; i < 8; i++)
    if (strcmp(c, CODES[i]) == 0) return DRIVES[i];
  return DRV_STOP;
}

static float clamp1(float v) { return v > 1 ? 1 : v < -1 ? -1 : v; }
static float deadzone(float v) {
  v = clamp1(v);
  float a = fabsf(v);
  if (a < JOY_DEADZONE) return 0;
  return (v > 0 ? 1 : -1) * (a - JOY_DEADZONE) / (1 - JOY_DEADZONE);
}
void joyMix(float x, float y, float* left, float* right) {
  x = deadzone(x);
  y = deadzone(y);
  float k = PIVOT_SCALE + (1 - PIVOT_SCALE) * fabsf(y);
  *left = clamp1(y + x * k);
  *right = clamp1(y - x * k);
}

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
  if (d != DRV_STOP) wiggling_ = false;  // a move command always wins over the sway
  drive_ = d;
  speedPct_ = pct;
}

bool Gait::wiggle() {
  if (moving() || nudging()) return false;
  wiggling_ = true;
  wiggleT_ = 0;
  return true;
}

float Gait::sideRate(bool left) const {
  if (drive_ == DRV_STOP || speedPct_ <= 0) return 0;
  float mag = (GAIT_MIN_SPEED_PCT + (100 - GAIT_MIN_SPEED_PCT) * speedPct_ / 100.0f) / 100.0f;
  switch (drive_) {
    case DRV_FWD: return mag;
    case DRV_BACK: return -mag;
    case DRV_LEFT: return (left ? -mag : mag) * PIVOT_SCALE;
    case DRV_RIGHT: return (left ? mag : -mag) * PIVOT_SCALE;
    case DRV_FL: return left ? mag * TURN_INNER_SCALE : mag;
    case DRV_FR: return left ? mag : mag * TURN_INNER_SCALE;
    case DRV_BL: return -(left ? mag * TURN_INNER_SCALE : mag);
    case DRV_BR: return -(left ? mag : mag * TURN_INNER_SCALE);
    case DRV_JOY: return mag * joy_[left ? 0 : 1];
    default: return 0;
  }
}

bool Gait::nudge(int leg, int dir, int ms, float cmd) {
  if (moving() || wiggling_ || leg < 0 || leg >= LEG_COUNT || dir == 0) return false;
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
  if (wiggling_) {
    // Square wave of pivots: segment k = round(t / half); even k -> spin left, odd -> spin right.
    // Segment 0 and the last one are half length, so the yaw integral is 0.
    const float half = WIGGLE_HALF_MS / 1000.0f, total = 2 * WIGGLE_COUNT * half;
    if (wiggleT_ >= total - 1e-4f) {
      wiggling_ = false;
      return;
    }
    int k = (int)floorf(wiggleT_ / half + 0.5f);
    float s = (k % 2 == 0) ? 1.0f : -1.0f;
    rate[0] = -s * WIGGLE_SPEED;
    rate[1] = s * WIGGLE_SPEED;
    wiggleT_ += dt;
  }
  if (rate[0] == 0 && rate[1] == 0) return;  // standing: neutral pulses
  float meanSpr = 0.1f;
  for (int i = 0; i < LEG_COUNT; i++) meanSpr = fmaxf(meanSpr, cfg_->secPerRev[i]);  // slowest servo sets pace
  phase_[0] += rate[0] * dt / meanSpr;
  phase_[1] += rate[1] * dt / meanSpr;
  if (fabsf(rate[0] - rate[1]) < 1e-3f) {  // straight line: gently re-sync the two sides
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
