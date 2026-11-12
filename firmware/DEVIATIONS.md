# Deviations (firmware)

| # | Contract text | Change | Evidence | Cross-team impact |
|---|---|---|---|---|
| 1 | "Arduino-ESP32 core via PlatformIO ... compile only if a toolchain is present" | `platformio.ini` is provided (espressif32@6.5.0 = Arduino-ESP32 2.0.14) but PlatformIO is not installed in the shared cache, so it was not run. `tools/firmware/check.sh` compiles the same sources with the cached `arduino-cli` + esp32 core 2.0.14 for `esp32c3`. | `build/firmware/arduino-build`; 63% flash, 12% RAM | none; a PlatformIO build may differ in warnings only |
| 2 | Library "QRCode" (ricmoo) | Vendored as `src/nqr.c/.h` (MIT, licence copied) because the Arduino-ESP32 SDK ships its own `qrcode.h` that shadows the library header. | compile error `qr not declared` before vendoring | none |
| 3 | "servo PWM outputs stay off until the gait engine starts" | The engine starts at the end of `setup()` (after Wi-Fi/OLED), then drives neutral (stop) pulses until a command arrives. | main.cpp setup() | A badly trimmed neutral may creep a servo; trim in the calibration page. |
