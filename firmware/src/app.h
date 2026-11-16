#pragma once
#include "config.h"
#include "gait.h"
#include "settings.h"
// Shared runtime state (single-threaded: everything runs from loop()).
extern Settings g_cfg;
extern Gait g_gait;
extern uint32_t g_lastCmdMs;  // last move command (drive/joy) from the driving phone; feeds the watchdog
extern int g_speedPct;
extern GaitType g_gaitType;
extern Drive g_drive;
extern uint32_t g_loveUntilMs;  // heart-eyes face shown until this time (extended while swaying)
bool appLove();
void appApplyDrive();  // push g_drive/g_speedPct/g_gaitType into the gait engine (low-battery aware)
