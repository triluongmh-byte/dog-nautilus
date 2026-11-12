# Protection

* Reverse polarity: carrier headers are unkeyed 2.54 mm pins. Mitigation: pin 1 is the square pad of every header; the harness table (engineering/harness.md) lists wire colours; use keyed (polarised) female housings. No reverse diode is added in the +5V trunk: 0.45 V drop at 2.4 A (1.1 W) would waste the servo supply. A wrong +5V/GND swap would be caught by the buck/charger-side protection, not by this dummy board.
* Back-feed: D1 (SS14, 40 V, 1 A) isolates the SuperMini USB-C from the servo rail (contract requirement). Worst case current through D1 is the module's own draw (< 0.5 A).
* Overcurrent: the all-in-one 2S charger/protection module (CHG1) provides the cell protection (assumption GIA DINH: it has OCP/short protection >= 3 A as in the contract). No fuse on the carrier; a 3 A PTC in the harness would be a case/user choice - recorded as an open assumption.
* Servo regeneration: micro servos have internal H-bridges; no flyback needed. 1000 uF C1 absorbs servo current steps; rated 10 V on 5 V.
* ADC pin: VBAT_SENSE maximum 2.084 V, divider values keep it below 3.3 V even if the cells overshoot 9 V (9.0 V -> 2.23 V).
* Watchdog/disable: 1 s command watchdog and low-battery stop are firmware (contract), not copper. The carrier has no hardware disable.
