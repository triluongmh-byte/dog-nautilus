"""Host python: writes build/board/spec.json (net table) and design/nautilus.pretty (local footprints)."""
import json, shutil, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
FP = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
LOC = ROOT / 'design' / 'nautilus.pretty'
LOC.mkdir(parents=True, exist_ok=True)
COPY = ['Connector_PinHeader_2.54mm.pretty/PinHeader_1x02_P2.54mm_Vertical', 'Connector_PinHeader_2.54mm.pretty/PinHeader_1x03_P2.54mm_Vertical',
        'Connector_PinHeader_2.54mm.pretty/PinHeader_1x04_P2.54mm_Vertical', 'Connector_PinHeader_2.54mm.pretty/PinHeader_1x06_P2.54mm_Vertical',
        'Resistor_SMD.pretty/R_0805_2012Metric', 'Capacitor_SMD.pretty/C_0805_2012Metric', 'Diode_SMD.pretty/D_SMA',
        'Capacitor_THT.pretty/CP_Radial_D8.0mm_P3.50mm', 'MountingHole.pretty/MountingHole_2.2mm_M2']
for c in COPY:
    shutil.copy(FP / (c + '.kicad_mod'), LOC / (Path(c).name + '.kicad_mod'))

def u1_fp():
    # ESP32-C3 SuperMini: 2 rows x 8, 2.54 pitch, rows 15.24 apart, long axis X, USB-C at +X (pin 1 / pin 9 at the USB end).
    # Origin = module centre. Left row (pads 1-8) at y=-7.62, right row (9-16) at y=+7.62 (KiCad y down).
    L = ['(footprint "ESP32C3_SuperMini_2x8_P2.54" (version 20240108) (generator "nautilus") (layer "F.Cu")',
         '\t(descr "ESP32-C3 SuperMini on 2x8 2.54 pins, rows 15.24 mm apart (GIA DINH: unmeasured). USB-C at +X.")',
         '\t(attr through_hole)',
         '\t(fp_text reference "REF**" (at 0 -11.5) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
         '\t(fp_text value "ESP32-C3 SuperMini" (at 0 11.5) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))']
    for (x1, y1, x2, y2, lay, w) in [(-11.25, -9, 11.25, 9, 'F.Fab', 0.1), (-10.5, -9, 10.5, 9, 'F.SilkS', 0.12)]:
        L.append(f'\t(fp_rect (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type default)) (fill none) (layer "{lay}"))')
    L.append('\t(fp_poly (pts (xy -11.5 -9.25) (xy 11.5 -9.25) (xy 11.5 -5.9) (xy -10.4 -5.9) (xy -10.4 5.9) (xy 11.5 5.9) (xy 11.5 9.25) (xy -11.5 9.25)) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))')  # C-shaped: pin-row bands + spine; the space between the rows is free for flat passives (<2.5 mm)
    L.append('\t(fp_text user "USB-C >" (at 7 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))')
    for i in range(16):
        row, k = divmod(i, 8)
        x = 8.89 - 2.54 * k
        y = -7.62 if row == 0 else 7.62
        shape = 'rect' if i in (0, 8) else 'circle'
        L.append(f'\t(pad "{i+1}" thru_hole {shape} (at {x:.2f} {y}) (size 1.7 1.7) (drill 1.0) (layers "*.Cu" "*.Mask"))')
    L.append(')')
    (LOC / 'ESP32C3_SuperMini_2x8_P2.54.kicad_mod').write_text('\n'.join(L) + '\n')
u1_fp()

PH = lambda n: f'nautilus:PinHeader_1x0{n}_P2.54mm_Vertical'
U1MAP = {  # pad -> net (contract pins). 1-8 left row, 9-16 right row
 1:'SERVO_FL_PWM',2:'SERVO_FR_PWM',3:'SERVO_RL_PWM',4:'I2C_SDA',5:'I2C_SCL',6:'SERVO_RR_PWM',9:'+5V_MCU',10:'GND',11:'+3V3',12:'EXP_IO_A',13:'VBAT_SENSE',14:None,15:'EXP_IO_B',16:None}
# pads 7,8 (GPIO20/21), 14 (GPIO2), 16 (GPIO0) are no-connect
nets = {}
def add(n, ref, pin): nets.setdefault(n, []).append([ref, str(pin)])
for p, n in U1MAP.items():
    if n: add(n, 'U1', p)
parts = []
def part(ref, value, symbol, fp, at, **kw): parts.append(dict(ref=ref, value=value, symbol=symbol, footprint=fp, at=at, **kw))
part('U1', 'ESP32-C3 SuperMini', 'Conn_02x08_Counter_Clockwise', 'nautilus:ESP32C3_SuperMini_2x8_P2.54', [30, 30])
conns = {'J1': ('POWER_IN', ['+5V', 'GND']), 'J2': ('VBAT_IN', ['VBAT_SW', 'GND']),
 'J3': ('SERVO_FL', ['SERVO_FL_PWM', '+5V', 'GND']), 'J4': ('SERVO_FR', ['SERVO_FR_PWM', '+5V', 'GND']),
 'J5': ('SERVO_RL', ['SERVO_RL_PWM', '+5V', 'GND']), 'J6': ('SERVO_RR', ['SERVO_RR_PWM', '+5V', 'GND']),
 'J7': ('OLED', ['GND', '+3V3', 'I2C_SCL', 'I2C_SDA']), 'J8': ('FAN', ['+5V', 'GND']),
 'J9': ('EXPANSION', ['+5V', 'GND', 'I2C_SDA', 'I2C_SCL', 'EXP_IO_A', 'EXP_IO_B'])}
for i, (ref, (val, ns)) in enumerate(conns.items()):
    n = len(ns)
    part(ref, val, f'Conn_01x0{n}', PH(n), [80 + 25.4 * (i % 5), 30 + 40.64 * (i // 5)])
    for k, net in enumerate(ns): add(net, ref, k + 1)
def R(ref, v, a, b, at):
    part(ref, v, 'R', 'nautilus:R_0805_2012Metric', at); add(a, ref, 1); add(b, ref, 2)
def C(ref, v, a, b, at):
    part(ref, v, 'C', 'nautilus:C_0805_2012Metric', at); add(a, ref, 1); add(b, ref, 2)
R('R1', '4.7k', '+3V3', 'I2C_SDA', [30, 80]); R('R2', '4.7k', '+3V3', 'I2C_SCL', [55, 80])
R('R3', '100k', 'VBAT_SW', 'VBAT_SENSE', [80, 80]); R('R4', '33k', 'VBAT_SENSE', 'GND', [105, 80])
for i, s in enumerate(['FL', 'FR', 'RL', 'RR']):
    R(f'R{5+i}', '10k', f'SERVO_{s}_PWM', 'GND', [30 + 25 * i, 105])
C('C2', '100nF', '+5V_MCU', 'GND', [30, 130]); C('C3', '100nF', '+3V3', 'GND', [55, 130]); C('C4', '100nF', 'VBAT_SENSE', 'GND', [80, 130])
part('C1', '1000uF 10V', 'C_Polarized', 'nautilus:CP_Radial_D8.0mm_P3.50mm', [130, 130]); add('+5V', 'C1', 1); add('GND', 'C1', 2)
part('D1', 'SS14 Schottky', 'D', 'nautilus:D_SMA', [155, 130]); add('+5V', 'D1', 2); add('+5V_MCU', 'D1', 1)   # D: pin1 K, pin2 A
for i, n in enumerate(['+5V', 'GND', 'VBAT_SW', '+3V3']):
    part(f'#FLG0{i+1}', 'PWR_FLAG', 'PWR_FLAG', '', [30 + 25 * i, 155], in_bom=False); add(n, f'#FLG0{i+1}', 1)
for k in range(4): part(f'MH{k+1}', 'M2 post', 'MountingHole', 'nautilus:MountingHole_2.2mm_M2', [30 + 25 * k, 180], in_bom=False)
spec = dict(title='nautilus-dog-carrier', rev='1', company='', lib='nautilus', stem='main', paper='A1',
            libraries=['Connector_Generic', 'Device', 'power', 'Mechanical'], parts=parts, nets=nets, keep_uuids_from=str(ROOT / 'design/main.kicad_sch'))
(ROOT / 'build/board').mkdir(parents=True, exist_ok=True)
(ROOT / 'build/board/spec.json').write_text(json.dumps(spec, indent=1))
print('spec ok', len(parts), 'parts', len(nets), 'nets')
