# Off-board harness table and coordinate offset

Contract frame (x forward, y robot-left, z up) -> KiCad: KiCad x = contract x, KiCad y = -contract y. Offset = (0, 0). U1 centre contract (49.25, 0); mounts MH1 (40.5,-23.5) MH2 (57.5,-23.5) MH3 (57.5,23.5) MH4 (40.5,23.5) are mirrored in y in KiCad (the set is symmetric). Outline x 38..60, y -26..26. USB-C of the SuperMini faces +X (right in the viewer).

| Off-board | Pin | Net | Goes to carrier |
|---|---|---|---|
| BUCK1 | OUT+ / OUT- | +5V / GND | J1.1 / J1.2 |
| BUCK1 | IN+ / IN- | VBAT_SW / GND | from SW1 ON / CHG1 P- (not on carrier) |
| SW1 | COM / ON | VBAT_PACK / VBAT_SW | CHG1 P+ -> SW1 -> VBAT_SW also to J2.1 |
| CHG1 | P+ / P- / B+ / BM / B- | VBAT_PACK / GND / cell nodes | P- to J2.2 (GND); cells not on carrier |
| FAN1 | + (red) / - (black) | +5V / GND | J8.1 / J8.2 |
| DISP1 | GND, VCC, SCL, SDA | GND, +3V3, I2C_SCL, I2C_SDA | J7.1 .. J7.4 |
| servo_FL/FR/RL/RR | orange, red, brown | PWM, +5V, GND | J3 / J4 / J5 / J6 pins 1,2,3 |
| expansion pigtail | 1x6 female, same order as J9 | +5V, GND, SDA, SCL, IO_A, IO_B | J9.1 .. J9.6 |
