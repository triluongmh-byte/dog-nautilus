# Wiring (from PILOT_CONTRACT.json, interfaces.pins)

Firmware pin map (include/config.h). Nets/pins are sealed by the contract; nothing here changes them.

| Function | ESP32-C3 SuperMini pin | Net | Carrier connector |
|---|---|---|---|
| Servo FL signal | GPIO5 | SERVO_FL_PWM | J3.1 (signal only) |
| Servo FR signal | GPIO6 | SERVO_FR_PWM | J4.1 |
| Servo RL signal | GPIO7 | SERVO_RL_PWM | J5.1 |
| Servo RR signal | GPIO10 | SERVO_RR_PWM | J6.1 |
| I2C SDA (OLED + expansion) | GPIO8 (shares on-board LED, never driven) | I2C_SDA | J7.4, J9.3 |
| I2C SCL | GPIO9 | I2C_SCL | J7.3, J9.4 |
| Battery sense | GPIO3 (ADC1_CH3) | VBAT_SENSE | divider from VBAT_SW (J2.1) |
| Expansion A / B | GPIO4 / GPIO1 | EXP_IO_A / EXP_IO_B | J9.5 / J9.6 (high-Z inputs at boot) |
| Unused | GPIO0, GPIO2, GPIO20, GPIO21 | NC | untouched by firmware |
| Power in | 5V pin (4.7 V via OR-ing diode), GND, 3V3 out | +5V_MCU, GND, +3V3 | |

Servo power: red/brown servo leads go to the +5V/GND splice at the buck output (AWG24, <= 0.3 m), not to J3-J6 pins 2-3; only the orange signal lead plugs onto pin 1 with a 1-pin housing (engineering/power.md, engineering/harness.md). No firmware change.

Other connectors: J1 = +5V/GND from buck, J2 = VBAT_SW/GND (sense), J7 = GND/+3V3/SCL/SDA (OLED, 4-pin order as contract), J8 = fan +5V/GND (always on, no firmware control), J9 = +5V/GND/SDA/SCL/IO_A/IO_B.

Firmware assumptions that depend on the board/hand wiring:
- Servo signal levels are 3.3 V into 5 V servos (unverified).
- Divider ratio constant `VBAT_DIVIDER_RATIO = (100k+33k)/33k = 4.03` (VBAT 8.4 V -> 2.08 V at GPIO3). If the board team picks other resistors, change that one constant.
- OLED must be the **I2C** variant at 0x3C (0x3D probed as fallback). Many 1.54in SSD1309 modules ship in SPI mode; a resistor/jumper change may be needed. Controller `OLED_USE_SSD1309`, rotation `OLED_ROTATION` and address are compile-time constants in config.h.
- I2C pull-ups (4.7 k to +3V3) live on the carrier; firmware enables none.
- Servo wire colours: orange = signal (J3-J6 pin 1), red = +5V and brown = GND (both to the buck splice).
