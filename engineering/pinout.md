# Pinout audit (contract pins vs schematic nets vs footprint pads)

U1 module card: left row (pad 1-8, pin 1 at the USB end) IO5, IO6, IO7, IO8, IO9, IO10, IO20, IO21; right row (pad 9-16) 5V, GND, 3V3, IO4, IO3, IO2, IO1, IO0. GIA DINH: orientation from the card, unmeasured module.

| Pad | Module pin | Net (contract) |
|---|---|---|
| 1 | GPIO5 | SERVO_FL_PWM |
| 2 | GPIO6 | SERVO_FR_PWM |
| 3 | GPIO7 | SERVO_RL_PWM |
| 4 | GPIO8 | I2C_SDA |
| 5 | GPIO9 | I2C_SCL |
| 6 | GPIO10 | SERVO_RR_PWM |
| 7 | GPIO20 | no-connect flag (NC_GPIO20) |
| 8 | GPIO21 | no-connect flag (NC_GPIO21) |
| 9 | 5V | +5V_MCU |
| 10 | GND | GND |
| 11 | 3V3 | +3V3 |
| 12 | GPIO4 | EXP_IO_A |
| 13 | GPIO3 | VBAT_SENSE |
| 14 | GPIO2 | no-connect flag (NC_GPIO2) |
| 15 | GPIO1 | EXP_IO_B |
| 16 | GPIO0 | no-connect flag (NC_GPIO0) |

Headers (all 1xN 2.54, pin 1 = square pad): J1 +5V,GND; J2 VBAT_SW,GND; J3-J6 PWM,+5V,GND (FL,FR,RL,RR); J7 GND,+3V3,I2C_SCL,I2C_SDA; J8 +5V,GND; J9 +5V,GND,I2C_SDA,I2C_SCL,EXP_IO_A,EXP_IO_B. Sealed orders unchanged.
Checks run: `kicadpy.verify netlist design/main.kicad_pro` -> 0 differences, 0 hollow symbols (70 pins = 70 pads); `kicadpy.author check`-equivalent via the netlist export; `kicadpy.verify modules` has no card for the 1x4 OLED header (module card is the 0.96 in; same GND/VCC/SCL/SDA order used by the contract).
