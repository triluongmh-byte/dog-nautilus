# Off-board harness table and coordinate offset

Contract frame (x forward, y robot-left, z up) -> KiCad: KiCad x = contract x, KiCad y = -contract y. Offset = (0, 0). U1 centre contract (49.25, 0); mounts MH1 (40.5,-23.5) MH2 (57.5,-23.5) MH3 (57.5,23.5) MH4 (40.5,23.5) are mirrored in y in KiCad (the set is symmetric). Outline x 38..60, y -26..26. USB-C of the SuperMini faces +X (right in the viewer).

Servo power is wired, not routed through the carrier (power.md "Servo supply path"). SPL+ / SPL- are the two splice points right at BUCK1's output.

| Off-board | Pin | Net | Goes to |
|---|---|---|---|
| CHG1a (USB-C charger) | OUT+ / OUT- / BM | charge | CHG1b P+ / P- / cell midpoint |
| CHG1b (HX-2S-JH20) | P+ | VBAT_PACK | PTC1 (hold >= 3.5 A @ 23 C) -> SW1 COM |
| SW1 | ON | VBAT_SW | BUCK1 VIN+ and J2.1 |
| CHG1b | P- | GND | BUCK1 VIN- and J2.2 |
| BUCK1 (Pololu S13V30F5) | VOUT / GND | +5V / GND | SPL+ / SPL- |
| SPL+ / SPL- | AWG24 | +5V / GND | J1.1 / J1.2 |
| servo_FL/FR/RL/RR | red / brown | +5V / GND | SPL+ / SPL- (AWG24, <= 0.3 m each) |
| servo_FL/FR/RL/RR | orange | PWM | J3 / J4 / J5 / J6 pin 1 only, 1-pin housing; pins 2-3 left empty |
| FAN1 | + (red) / - (black) | +5V / GND | J8.1 / J8.2 |
| DISP1 | GND, VCC, SCL, SDA | GND, +3V3, I2C_SCL, I2C_SDA | J7.1 .. J7.4 |
| expansion pigtail | 1x6 female, same order as J9 | +5V, GND, SDA, SCL, IO_A, IO_B | J9.1 .. J9.6 (<= 0.5 A) |
| CHG1b | B+ / BM / B- | cell nodes | cells only, not on carrier |
