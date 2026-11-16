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

## Servo supply path (decided 2026-11-16)
Servo power does NOT pass through the carrier. BUCK1 OUT+/OUT- go to one +5V and one GND splice point (soldered and heat-shrunk, or a screw/lever terminal block) right at the buck. From that point:
* each servo red (+5V) and brown (GND) lead, extended with AWG24, <= 0.3 m;
* the carrier feed to J1.1/J1.2 (AWG24).
Only the orange signal lead of each servo goes to J3-J6 pin 1, in a 1-pin 2.54 mm female housing. J3-J6 pins 2 and 3 stay empty (they are still +5V/GND on the copper; nothing is plugged onto them). GND is common at the splice point, so the PWM reference is shared.
AWG24 0.084 Ohm/m: 0.3 m out and back at 0.6 A = 0.03 V; the buck-to-splice stub carries the full 2.4 A over a few cm (< 0.02 V).
Result: the board trunk J1 -> D1/C1/J8/J9 carries only fan + MCU + expansion (<= 1.0 A), under the ~1.5 A that 0.6 mm / 1 oz takes at 10 C rise.
C1 (1000 uF) now sits one J1 wire (~0.2 m) away from the servo splice; servo current steps are served by the buck directly. Brown-out at the MCU is a bench item (bringup.md step 6).

## Power budget (assumed figures; only a bench measurement settles them)
| Load (5 V rail) | Current | Basis |
|---|---|---|
| 4 servos at stall | 4 x 0.60 = 2.40 A | FEETECH FS90R spec 550 mA @ 4.8 V, 650 mA @ 6 V (sources.md) |
| Fan 30x30 5 V | 0.10 A | GIA DINH, fan not sourced |
| ESP32-C3 SuperMini incl. Wi-Fi AP peak + OLED through its 3.3 V LDO | 0.30 A | GIA DINH |
| **Total** | **2.80 A = 14.0 W** | BUCK1 rating 3 A (Pololu S13V30F5) |

Battery side, efficiency assumed 0.88: 14.0 / 0.88 = 15.9 W.
| Pack voltage | Pack current |
|---|---|
| 6.0 V (empty) | 2.65 A |
| 7.4 V (nominal) | 2.15 A |
| 8.4 V (full) | 1.89 A |
Firmware low-battery stop is 6.6 V (2.41 A there). CHG1 must state >= 5 A continuous discharge (2.65 A worst case plus margin).
Worse case: at Pololu's 0.8 A stall figure, 4 x 0.8 + 0.4 = 3.6 A, above the 3 A buck. This is a fault state (legs jammed): the buck current-limits and the firmware stops all servos 1 s after the last command. Normal walking is ~4 x 0.15-0.25 A.
Expansion header J9: <= 0.5 A in normal running (board trunk total <= 1.0 A); not guaranteed while all four servos stall.

## Copper (measured on the routed board, tools/board/widen.py)
+5V supply run J1 -> D1/C1/J3..J6/J8/J9 is routed at 0.6 mm wherever the clearance allowed (18 segments), short stubs at pads at 0.3-0.4 mm (publisher warning `power_entry_narrow`, kept: those stubs carry <= 1.0 A with the wired servo supply). 0.6 mm / 1 oz carries about 1.5 A at 10 C rise. GND is routed at 0.3-0.5 mm tracks (no pour: the dummy board has no EMC requirement). Copper is unchanged in this revision.
