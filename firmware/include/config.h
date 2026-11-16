// Pin map and tunables. Pins come only from PILOT_CONTRACT.json (interfaces.pins).
#pragma once
#include <stdint.h>

// ---- Pins (contract) ----
#define PIN_SERVO_FL 5
#define PIN_SERVO_FR 6
#define PIN_SERVO_RL 7
#define PIN_SERVO_RR 10
#define PIN_I2C_SDA 8   // shares the on-board LED: never drive it as GPIO
#define PIN_I2C_SCL 9
#define PIN_VBAT_SENSE 3  // ADC1_CH3
#define PIN_EXP_IO_A 4    // high-Z input at boot, firmware never drives
#define PIN_EXP_IO_B 1
// GPIO0/2/20/21 are no-connect: never touched.
#define I2C_FREQ_HZ 400000

// ---- Legs: index order FL, FR, RL, RR ----
enum Leg { LEG_FL = 0, LEG_FR, LEG_RL, LEG_RR, LEG_COUNT };
static const uint8_t SERVO_PINS[LEG_COUNT] = {PIN_SERVO_FL, PIN_SERVO_FR, PIN_SERVO_RL, PIN_SERVO_RR};
static const char* const LEG_NAMES[LEG_COUNT] = {"FL", "FR", "RL", "RR"};
static inline bool legIsLeft(int i) { return i == LEG_FL || i == LEG_RL; }

// ---- Servo pulses (us) ----
#define SERVO_FREQ_HZ 50
#define SERVO_PULSE_MIN_US 1000
#define SERVO_PULSE_MAX_US 2000
#define SERVO_NEUTRAL_DEFAULT_US 1500
#define SERVO_TRIM_LIMIT_US 150        // |trim| clamp
#define SERVO_FULL_SPEED_DELTA_US 400  // pulse offset from neutral at 100% command
#define SERVO_LEDC_BITS 14
// Left-side servos are mirrored: default direction sign +1 left, -1 right (calibrate!).
static const int8_t SERVO_SIGN_DEFAULT[LEG_COUNT] = {+1, -1, +1, -1};

// ---- Gait ----
#define DEFAULT_SEC_PER_REV 1.2f   // seconds per crank revolution at 100% command (calibrate)
#define GAIT_MIN_SPEED_PCT 20      // slider 0 stops; >0 maps to this..100 command
#define PHASE_KP 3.0f              // phase-error gain (rev/s per rev)
#define PHASE_CMD_TRIM_MAX 0.35f   // max correction added to command
#define GAIT_TICK_MS 10
#define TURN_INNER_SCALE 0.35f     // inner side speed factor in a diagonal (arc) move
#define JOY_DEADZONE 0.10f         // joystick: centre 10 % of each axis does nothing
#define JOY_SEND_MS 100            // page resends joystick / held button this often
#define WIGGLE_COUNT 6             // "love" emote: number of left-right sways
#define WIGGLE_HALF_MS 250         // each swing direction lasts this long (first/last are half)
#define WIGGLE_SPEED 0.45f         // pivot command during the sway, fraction of full speed
#define LOVE_FACE_HOLD_MS 2000     // heart-eyes face stays this long after the sway
#define PIVOT_SCALE 0.7f           // both sides at this fraction of the speed when spinning in place
#define NUDGE_MS 120               // calibration nudge pulse length
#define NUDGE_CMD 0.5f             // nudge command (fraction of full)

// ---- Safety ----
#define WATCHDOG_MS 1000  // stop if the driving phone sends no move command for this long
#define LOW_BATT_CUTOFF_V 6.6f
#define LOW_BATT_RESUME_V 6.9f
#define LOW_BATT_DEBOUNCE_MS 2000   // servo current sags VBAT; require sustained low

// ---- Battery ----
#define VBAT_DIVIDER_RATIO ((100.0f + 33.0f) / 33.0f)  // 100k top / 33k bottom (board target)
#define VBAT_OFFSET_V 0.0f
#define VBAT_EMPTY_V 6.4f
#define VBAT_FULL_V 8.4f
#define VBAT_SAMPLES 16

// ---- OLED ----
#define OLED_I2C_ADDR 0x3C        // 0x3D alternative; boot probes the other one if absent
#define OLED_I2C_ADDR_ALT 0x3D
#define OLED_USE_SSD1309 1        // 1 = SSD1309, 0 = SSD1306
#define OLED_ROTATION U8G2_R0     // U8G2_R0 / R1 / R2 / R3
#define QR_PHASE_MS 6000          // each QR page duration

// ---- Network ----
#define AP_SSID_PREFIX "NautilusDog-"
#define AP_CHANNEL 6
#define AP_MAX_CLIENTS 4
#define HTTP_PORT 80
#define WS_PORT 81
