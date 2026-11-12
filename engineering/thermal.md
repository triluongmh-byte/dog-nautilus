# Thermal

No regulator, LDO or switching device is on the carrier (the buck is off-board, the 3.3 V LDO is inside the SuperMini). The only dissipators: D1 SS14 at <= 0.5 A x 0.45 V = 0.23 W (SMA package, ~100 C/W without pour -> ~23 C rise, fine) and the 100k/33k divider (0.5 mW). No thermal claim needs a copper pour; `kicadpy.verify thermal` is not applicable (no thermal pad). Power-trace heating is addressed in power.md (trunk current limit of the dummy board).
