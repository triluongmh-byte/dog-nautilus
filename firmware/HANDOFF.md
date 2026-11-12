# Firmware HANDOFF (read first)
flash.json names the arduino-cli build (sketch ../build/firmware/sketch, bin in arduino-build/).
Fast check: `tools/firmware/check.sh` (all) | `... host` (logic tests + page JS, ~2 s) | `... build` (arduino-cli, ~30 s, skipped if unchanged). Outputs in build/firmware/.
No PlatformIO in cache -> see DEVIATIONS.md #1. Compile via arduino-cli with libs from sketchbook (U8g2, WebSockets).

## Files (firmware/)
- platformio.ini: espressif32@6.5.0, USB-CDC flags, libs U8g2 + WebSockets (QR vendored).
- include/config.h: ALL pins, trims, gait/battery/OLED/net constants (single source).
- src/main.cpp: setup() 30-49 (pins, NVS, AP, OLED, servo start); loop() 51-77 (watchdog, low-batt, 10 ms gait tick); appApplyDrive() 17.
- src/gait.cpp/.h: pure phase engine. update() 63-96 (side masters, feed-forward + P phase correction), nudge() 50, markZero() 59, setDrive() 24, offsets table 4 (trot/walk).
- src/servos.cpp/.h: LEDC 50 Hz, 14-bit. commandToUs() 16 (sign, trim, clamp), begin() 28.
- src/battery.cpp/.h: percentFromVolts 6, update() 23 (EMA, debounced low latch with hysteresis).
- src/settings.cpp/.h: NVS namespace "dog" (n/s/r/p/d per leg, pw). load 25, save 54.
- src/oled.cpp/.h: U8g2 SSD1309/1306 I2C, address probe 25, QR pages (drawQr 43), smiley 61, update 79, low-batt screen.
- src/web.cpp/.h + web_pages.h: HTTP :80 (/ and /cal), WebSocket :81 text protocol. handleCmd() 34 (hb, drive, spd, gait, nudge, spin, trim, sign, zero, rev, save). Telemetry `st bat volts low drive gait`.
- src/nqr.c/.h: vendored QR lib (renamed header).
- tools/firmware/test_gait.cpp (host asserts), check_pages.js (JS syntax), check.sh.
- README.md (user docs), WIRING.md (pins), DEVIATIONS.md.

## Open assumptions
- Servo sign defaults, sec/rev 1.2, neutral 1500 are guesses; calibration page sets them.
- OLED I2C variant/controller/rotation unverified. Divider constant 4.03 must match board.
- Boot assumes legs are where NVS says (saved phase delta); otherwise re-zero.
- Not compiled with PlatformIO itself. Nothing flashed or run on hardware.
