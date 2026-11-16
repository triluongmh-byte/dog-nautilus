# Bring-up (nothing has been powered; bench steps for the person)

All steps with no battery and no servos first.
1. Visual: with a multimeter in continuity mode (unpowered) confirm GND to J1.2, J2.2, J3.3 ... J9.2 and no short between +5V and GND (>= 1 kOhm because of C1 charge time) and VBAT_SW to GND reads ~133 kOhm.
2. GIA DINH checks: hold the SuperMini unpowered against the two male header rows (do not solder yet), USB toward the USB mark: every module pin label must match engineering/pinout.md. Measure the real row spacing (15.24 mm assumed) and the module length (22.5 mm assumed).
3. Feed 5.0 V from a current-limited bench supply (200 mA limit) into J1: expect +5V_MCU 4.5-4.7 V at U1 pad 9 and 3.3 V at J7.2. Current < 120 mA with Wi-Fi idle.
4. With the OLED on J7: SDA and SCL must idle at 3.3 V (not held low) before reset is released.
5. Divider: apply 8.4 V to J2: VBAT_SENSE must read 2.08 V +/- 0.05 V.
6. Add the fan on J8, then each servo one at a time (signal on J3-J6 pin 1, red/brown on the buck splice, harness.md): servo signal idle at 0 V (pull-down) during reset; limit 1 A. Then all four starting together from the real buck: scope or min-hold meter on U1 pad 9 (+5V_MCU); it must stay >= 4.3 V and the ESP32 must not reset. If it resets, solder a 100-220 uF >= 10 V electrolytic across the SuperMini 5V and GND pins (+5V_MCU, behind D1, so it does not count against the +5V 1200 uF limit) and repeat.
7. Plug height: with the real servo, fan, OLED and expansion plugs fitted, measure the highest point above the board top; it must stay <= 14 mm (zone z 6.6..20.6) and the OLED underside is at z 22.4. If a plug is taller, use right-angle headers (see DEVIATIONS.md #3). Confirm C1 body height <= 14 mm above the board top and the real part is rated >= 10 V.
8. Flash over USB-C with +5V present: confirm the servo rail does not back-feed (D1). Remeasure with the real buck: inrush into C1 < the buck's current limit.
9. Power budget check (power.md): with the real pack, measure pack current walking and with one leg held (stall) for < 2 s. Record against 2.65 A worst case; fit cells only after CHG1a (USB, no cells) measures 8.4 V +-0.1 V at its output, with CHG1b and PTC1 wired; first charge supervised.
