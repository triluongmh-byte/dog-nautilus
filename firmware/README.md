# Nautilus Dog V0 firmware (ESP32-C3 SuperMini)

Compile-only. Nothing in this repo flashes or touches hardware.

## Build
- PlatformIO: `pio run -d firmware` (env `esp32c3_supermini`, not available in the offline cache).
- Offline check used by the team: `tools/firmware/check.sh` (host logic tests + arduino-cli compile).
- Flashing later (by the user): USB-C service slot on the front wall, hold BOOT while plugging in if the port is missing.

## Pin map
Servos FL=GPIO5, FR=GPIO6, RL=GPIO7, RR=GPIO10 (50 Hz LEDC, 1000-2000 us). I2C SDA=GPIO8, SCL=GPIO9 (400 kHz). Battery sense GPIO3 (ADC1, 11 dB, 16-sample average). Expansion GPIO4/GPIO1 (inputs, untouched). GPIO0/2/20/21 unused. See WIRING.md.

## Defaults (include/config.h)
Neutral 1500 us per servo; direction sign FL/RL +1, FR/RR -1 (mirrored sides; verify); 1.2 s per revolution; battery 6.4 V = 0 %, 8.4 V = 100 %; low-battery cutoff 6.6 V (2 s debounce, resume 6.9 V); command watchdog 1 s; divider ratio 4.03; OLED SSD1309 at 0x3C, rotation R0.

## Use
1. Power on. Wi-Fi `NautilusDog-XXXX`, WPA2, per-device password (random, stored in NVS, shown on OLED).
2. OLED alternates a Wi-Fi-join QR and a URL QR (http://192.168.4.1). After a phone joins it shows a smiley and battery %.
3. Control page: Forward/Back/Left/Right/Stop, speed slider, gait (trot / walk), battery %. The page sends a heartbeat every 0.3 s; closing it or losing Wi-Fi stops the robot within 1 s.

## Calibration (http://192.168.4.1/cal) - lift the robot first
1. **Stop trim**: if a servo creeps at stop, press Trim +/-2 us until it is still.
2. **Direction**: Nudge +/-; if "forward" drives the crank backwards, press Flip dir. Do this for every leg until all four rotate the same way for Forward.
3. **Speed**: press "Spin 5 s", count revolutions, set sec/rev = 5 / turns.
4. **Phase zero**: nudge each leg to the same reference pose (foot at the start of its step), press Phase zero.
5. **Save to NVS**. The phase error of each leg is saved too. If a leg is moved by hand after power-off, redo step 4.
Servos are open-loop, so phase drifts a little over time; re-zero when the gait looks off.

## Assumptions to confirm
OLED is the I2C variant; servos accept 3.3 V signal; divider resistors match the constant; sec/rev and sign values need real measurement.
