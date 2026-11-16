# Nautilus Dog V0 firmware (ESP32-C3 SuperMini)

Compile-only. Nothing in this repo flashes or touches hardware.

## Build
- PlatformIO: `pio run -d firmware` (env `esp32c3_supermini`, not available in the offline cache).
- Offline check used by the team: `tools/firmware/check.sh` (host logic tests + arduino-cli compile).
- Flashing (by you, later): connect a USB-C data cable through the front-wall service slot to the SuperMini. With arduino-cli: `arduino-cli upload --fqbn esp32:esp32:esp32c3:CDCOnBoot=cdc,PartitionScheme=default -p <port> --input-dir build/firmware/arduino-build`. If no port appears, hold BOOT while plugging in. The battery switch can be on or off (D1 blocks back-feed), but lift the robot: servos may twitch at boot.

## Pin map
Servos FL=GPIO5, FR=GPIO6, RL=GPIO7, RR=GPIO10 (50 Hz LEDC, 1000-2000 us). I2C SDA=GPIO8, SCL=GPIO9 (400 kHz). Battery sense GPIO3 (ADC1, 11 dB, 16-sample average). Expansion GPIO4/GPIO1 (inputs, untouched). GPIO0/2/20/21 unused. See WIRING.md.

## Defaults (include/config.h)
Neutral 1500 us per servo; direction sign FL/RL +1, FR/RR -1 (mirrored sides; verify); 1.2 s per revolution; battery 6.4 V = 0 %, 8.4 V = 100 %; low-battery cutoff 6.6 V (2 s debounce, resume 6.9 V); command watchdog 1 s; divider ratio 4.03; OLED SSD1309 at 0x3C, rotation R0.

## Use
1. Power on. Wi-Fi `NautilusDog-XXXX`, WPA2, per-device password (random, stored in NVS, shown on OLED).
2. OLED alternates a Wi-Fi-join QR and a URL QR (http://192.168.4.1). After a phone joins it shows a smiley and battery %.
   The dog also answers every DNS name with 192.168.4.1 (captive portal), so most phones pop the control page up by themselves.
3. Drive like an RC car (works upright or sideways):
   - **Joystick** (big circle): push up = forward, down = back, sideways = spin in place (0.7 x), diagonal = curve. Further = faster, up to the "Max speed" slider. Centre 10 % does nothing. **Let go = stop.**
   - **Buttons** ↖ ▲ ↗ / ⟲ ▼ ⟳ / ↙ ↘: hold to move, release to stop. Big red STOP always stops.
   - Trot / Walk buttons, battery %, link state and "Moving:" are on the same page.
   | Button | Code | Legs |
   |---|---|---|
   | ▲ / ▼ | F / B | both sides forward / back |
   | ⟲ / ⟳ | L / R | spin in place: one side back, the other forward, at 0.7 x speed (`PIVOT_SCALE`) |
   | ↖ / ↗ | FL / FR | forward arc: inner side at 0.35 x speed (`TURN_INNER_SCALE`) |
   | ↙ / ↘ | BL / BR | backward arc, same inner-side scale |
   The legs cannot step sideways (one motor per leg), so "diagonal" means a curved path.
4. **❤ Love:** from standstill the dog sways left-right 6 times (~3 s, short alternating pivots that cancel out, so it ends roughly facing the same way) and the OLED shows heart eyes until 2 s after. While moving, ❤ only changes the face. Any move, STOP, lost link or low battery cancels the sway. Tune `WIGGLE_COUNT`, `WIGGLE_HALF_MS`, `WIGGLE_SPEED` in config.h after a real test.
5. **Safety:** the page resends the joystick/held button every 0.1 s (`JOY_SEND_MS`). If the dog hears no move command from the driving phone for 1 s (Wi-Fi lost, phone locked, page closed) it stops. Low battery (< 6.6 V) stops it too.
6. **One driver at a time:** the phone that connected last drives. Others see "Someone else is driving" and a "Take control" button; taking control stops the dog first.
7. **Phone keeps leaving the dog's Wi-Fi?** It has no Internet, so phones may switch back to mobile data:
   - Android: when asked, choose "Stay connected" / "Keep Wi-Fi connection"; or turn mobile data off while driving.
   - iPhone: in the pop-up page tap "Cancel" -> "Use Other Network"/"Use Without Internet" if offered, or just open Safari at http://192.168.4.1 . Turn off mobile data if it still drops.
   - Range: on-board antenna, typically 10-30 m indoors (not measured).

## Calibration (http://192.168.4.1/cal) - lift the robot first
1. **Stop trim**: if a servo creeps at stop, press Trim +/-2 us until it is still.
2. **Direction**: Nudge +/-; if "forward" drives the crank backwards, press Flip dir. Do this for every leg until all four rotate the same way for Forward.
3. **Speed**: press "Spin 5 s", count revolutions, set sec/rev = 5 / turns.
4. **Phase zero**: nudge each leg to the same reference pose (foot at the start of its step), press Phase zero.
5. **Save to NVS**. The phase error of each leg is saved too. If a leg is moved by hand after power-off, redo step 4.
Servos are open-loop, so phase drifts a little over time; re-zero when the gait looks off.

## Assumptions to confirm
OLED is the I2C variant; servos accept 3.3 V signal; divider resistors match the constant; sec/rev and sign values need real measurement.
