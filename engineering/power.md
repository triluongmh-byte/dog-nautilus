# Power (carrier "nautilus-dog-carrier", dummy ERC board — never ordered, nothing powered)

Sources: contract rails (PILOT_CONTRACT.json powerRails), ESP32-C3 SuperMini module card (KICAD_HARNESS_BLOCKS/../modules/esp32-c3-supermini), SS14 datasheet (Vishay), SG90/FS90R class servo figures (GIA DINH: stall ~0.55-0.65 A each, idle ~10 mA).

## Rails as built
| Rail | Where | Value |
|---|---|---|
| +5V | J1 pin 1 in; J3-J6 pin 2, J8 pin 1, J9 pin 1, D1 anode, C1 | 5.0 V from the off-board buck |
| +5V_MCU | D1 cathode -> U1 pad 9 (module 5V pin), C2 100 nF | 5.0 V - Vf(SS14 @ <=0.5 A, ~0.45 V) = 4.5-4.7 V |
| +3V3 | U1 pad 11 (module LDO out) -> J7 pin 2, R1/R2 pull-ups, C3 100 nF | 3.3 V, load = OLED + 2 x 0.7 mA pull-up current (<= 25 mA total, GIA DINH OLED 20 mA) |
| VBAT_SW | J2 pin 1 -> R3 100k -> VBAT_SENSE | 6.0-8.4 V, 63 uA through the divider |

## Capacitance (kicadpy.verify power)
+5V: C1 1000 uF (sealed bulk, 10 V rating on a 5 V rail = 50 % derating) + 0 other. Limit declared in product.json `railLimitsUF` +5V = 1200 uF. Inrush is set by the off-board buck soft-start (bench check in bringup.md).

## Battery sense divider
Vsense = VBAT_SW x 33k/(100k+33k): 8.4 V -> 2.084 V, 7.4 V -> 1.836 V, 6.0 V -> 1.489 V. ADC1_CH3 (GPIO3) at 11 dB attenuation reads to ~2.5-3.1 V, so full-scale never clips. Source impedance 25 kOhm with C4 100 nF -> tau 2.5 ms: fine for a 1 Hz battery task. The divider is always connected downstream of switch SW1, so it draws 0 when the robot is off.

## Reset / default state (reasoned, not "firmware handles it")
* Servo PWM GPIO5/6/7/10 are high-impedance while the C3 is in reset, in ROM boot and with empty flash. R5-R8 (10 k to GND) hold the lines low: a servo that sees no pulses does not move (a continuous-rotation servo with a floating input can creep or jitter). Cost: 0.33 mA per line when the pin drives high.
* GPIO8 (I2C_SDA) and GPIO9 (I2C_SCL) are strapping pins: 4.7 k pull-ups to +3V3 are the level the chip wants at boot (GPIO9 high = SPI boot, GPIO8 high is the recommended default). Nothing on the carrier pulls them low. The OLED/expansion modules must not hold SDA/SCL low during reset (bringup step 4).
* GPIO2 left floating (strapping, module has its own pull), GPIO0/20/21 no-connect. GPIO4/GPIO1 (EXP_IO_A/B) float to J9 only; an expansion module must not drive them during reset.
* The fan (J8) is always on whenever +5V exists: by contract, no switching device exists on the carrier, so there is no switch with a reset state.
* USB flashing while the robot is on: the module 5V pin is raw VBUS on clones. D1 blocks +5V -> USB direction for the servos' rail; the opposite direction (USB VBUS -> +5V_MCU) cannot reach +5V because D1 is reverse biased. Writing on the silkscreen is not possible on this dummy; recorded here and in bringup.md.

## Copper (measured on the routed board, tools/board/widen.py)
+5V supply run J1 -> D1/C1/J3..J6/J8/J9 is routed at 0.6 mm wherever the clearance allowed (18 segments), short stubs at pads at 0.3-0.4 mm. 0.6 mm / 1 oz carries about 1.5 A at 10 C rise. Four servos at stall (4 x 0.6 A = 2.4 A) plus fan 0.1 A exceed that on the shared trunk - a LIMITATION of this 22 x 52 mm dummy board. The contract says the carrier is a hand-wired build representation: the real servo power return must go with wire (>= AWG24 from the buck to J3-J6) or the board must be 2 oz with a pour. Servos stall only when the leg jams; the firmware has a watchdog (firmware team).
GND is routed at 0.3-0.5 mm tracks (no pour: a B.Cu pour was not added because the dummy board has no EMC requirement); the same current limit applies.
