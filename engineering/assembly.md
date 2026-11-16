# Assembly (all MANUAL — the board is a dummy, never ordered)

Method: hand soldering, iron + flux. Order: 0805 resistors/capacitors and D1 (SMD), then pin headers J1-J9 and the two 1x8 MALE headers for U1 (module is soldered on top of their 2.5 mm plastic base: seat height 2.5 mm per contract, USB-C centre z 11.9), then C1. No factory (JLCPCB) assembly, hence no LCSC codes and no rotation offsets are claimed; every populated reference is `manual` in manufacturing.json.
Polarity: D1 cathode (bar) = pad 1 toward the right (USB) side; C1 + (square pad 1) toward J2; headers pin 1 square; U1 pin 1/pin 9 at the USB (+X) end.
Footprint-orientation evidence: the local footprints are KiCad stock (copied to design/nautilus.pretty) plus the custom ESP32C3_SuperMini_2x8_P2.54; manual parts need no factory rotation comparison.
Identity: parts.json lists real catalogue MPNs as reference parts (not live-checked). The part set contains one assumption: C1 8 x 11.5 mm.
Plug height (DEVIATIONS.md #3): every plug on J1-J9 must stay <= 11.5 mm above the header plastic base (zone 14 mm above the board top). Use low-profile 2.54 mm housings (body <= 9 mm) with wires bent sideways at once, or solder the wires straight onto the pins, heat-shrink and bend them flat. Servo signal leads use 1-pin housings on J3-J6 pin 1; pins 2-3 stay bare.

