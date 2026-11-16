# Protection

* Reverse polarity: carrier headers are unkeyed 2.54 mm pins. Mitigation: pin 1 is the square pad of every header; the harness table (engineering/harness.md) lists wire colours; use keyed (polarised) female housings. No reverse diode is added in the +5V trunk: 0.45 V drop at 2.4 A (1.1 W) would waste the servo supply. A wrong +5V/GND swap would be caught by the buck/charger-side protection, not by this dummy board.
* Back-feed: D1 (SS14, 40 V, 1 A) isolates the SuperMini USB-C from the servo rail (contract requirement). Worst case current through D1 is the module's own draw (< 0.5 A).
* Overcurrent: CHG1b (HX-2S-JH20, 10 A listed) provides the cell protection; CHG1a only charges (sources.md, parts.json). Harness PTC1 in P+ -> SW1: resettable fuse with hold current >= 3.5 A at 23 C (4 A class). A 3 A-hold PTC derates in a warm closed body and could trip at the 2.65 A worst-case pack current (power.md); 4 A hold still protects the AWG24 wiring from a short. Exact part and derating curve not sourced (GIA DINH). No fuse on the carrier. Do not fit cells until CHG1a's output has been measured at 8.4 V +-0.1 V with no cells.
* Servo regeneration: micro servos have internal H-bridges; no flyback needed. 1000 uF C1 absorbs servo current steps; rated 10 V on 5 V.
* ADC pin: VBAT_SENSE maximum 2.084 V, divider values keep it below 3.3 V even if the cells overshoot 9 V (9.0 V -> 2.23 V).
* Watchdog/disable: 1 s command watchdog and low-battery stop are firmware (contract), not copper. The carrier has no hardware disable.
