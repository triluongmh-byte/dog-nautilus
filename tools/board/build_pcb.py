"""KiCad python (pcbnew): build design/main.kicad_pcb from design/main.kicad_sch (placement + nets + outline).
Contract frame (x, y up) -> KiCad (x, -y), offset 0. Run: $KICADPY_PYTHON tools/board/build_pcb.py [out.kicad_pcb]"""
import re, sys, json, os
import pcbnew
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'design/main.kicad_pcb')
sch = open(os.path.join(ROOT, 'design/main.kicad_sch')).read()
spec = json.load(open(os.path.join(ROOT, 'build/board/spec.json')))
root = re.search(r'\(uuid "([^"]+)"\)', sch).group(1)
uu = {}
for m in re.finditer(r'\(symbol\s+\(lib_id "[^"]+"\)\s+\(at [^)]*\)\s+\(unit 1\)\s+\(exclude_from_sim no\) \(in_bom \w+\) \(on_board yes\) \(dnp no\)\s+\(uuid "([^"]+)"\)\s+\(property "Reference" "([^"]+)"', sch):
    uu[m.group(2)] = m.group(1)
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
b = pcbnew.BOARD()
b.SetCopperLayerCount(2)
# outline (contract board.outlineMm; y mirrored, symmetric)
for (x1, y1, x2, y2) in [(38, -26, 60, -26), (60, -26, 60, 26), (60, 26, 38, 26), (38, 26, 38, -26)]:
    s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(V(x1, y1)); s.SetEnd(V(x2, y2)); s.SetWidth(mm(0.1)); b.Add(s)
nets = {}
def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(b, name); b.Add(n); nets[name] = n
    return nets[name]
pin2net = {}
for n, pins in spec['nets'].items():
    for ref, pin in pins: pin2net[(ref, pin)] = n
# placement: ref -> (x, y, rot). Passives between the SuperMini pin rows sit under the module (<2.5 mm tall).
P = {'U1': (49.25, 0, 0)}
JROT = 90   # origin of each header is pin 1; rot 90 runs the pins along +x
P['J9'] = (41.4, 11.5, JROT); P['J1'] = (41.4, 15.3, JROT); P['J2'] = (47.6, 15.3, JROT); P['J8'] = (53.8, 15.3, JROT)
P['J3'] = (52.9, -11.5, JROT); P['J4'] = (41.4, -11.5, JROT); P['J5'] = (52.9, -15.3, JROT); P['J6'] = (41.4, -15.3, JROT)
P['J7'] = (41.4, -19.1, JROT)
for k, xy in enumerate([(40.5, 23.5), (57.5, 23.5), (57.5, -23.5), (40.5, -23.5)]): P[f'MH{k+1}'] = (xy[0], xy[1], 0)  # contract MH1 (40.5,-23.5) -> KiCad (40.5,+23.5)
P['C1'] = (46.25, 21.7, 0)   # origin = pad 1; body centre is +1.75 mm in x
P.update({'R1': (53.2, -19.1, 90), 'R2': (55.6, -19.1, 90),
          'R5': (57.9, -3.5, 90), 'R6': (55.6, -3.5, 90), 'R7': (53.2, -3.5, 90), 'R8': (43.6, -3.5, 90),
          'D1': (56.2, 19.2, 180),
          'R3': (40.8, 2.4, 0), 'R4': (44.2, 2.4, 0),
          'C4': (48.9, 4.9, 0), 'C3': (53.2, 4.6, 180), 'C2': (56.8, 4.6, 180)})
for p in spec['parts']:
    if p['ref'].startswith('#'): continue
    lib, name = p['footprint'].split(':')
    fp = pcbnew.FootprintLoad(os.path.join(ROOT, 'design/nautilus.pretty'), name)
    fp.SetFPID(pcbnew.LIB_ID('nautilus', name))
    fp.SetReference(p['ref']); fp.SetValue(p['value'])
    x, y, r = P[p['ref']]
    fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(r)
    if not p['ref'].startswith('U'): fp.Reference().SetLayer(pcbnew.F_Fab)
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_SilkS and hasattr(g, 'SetWidth'): g.SetWidth(mm(0.15))   # JLCPCB silk floor
    fp.SetPath(pcbnew.KIID_PATH('/' + root + '/' + uu[p['ref']]))
    for pad in fp.Pads():
        n = pin2net.get((p['ref'], pad.GetNumber()))
        if n: pad.SetNet(net(n))
        elif p['ref'] == 'U1': pad.SetNet(net('unconnected-(U1-Pin_%s-Pad%s)' % (pad.GetNumber(), pad.GetNumber())))
    b.Add(fp)
b.Save(OUT)
# explicit 2-layer stackup (1.6 mm, 1 oz = 0.035 mm copper) injected as text; the python stackup API is not exposed
txt = open(OUT).read()
stack = ('(stackup (layer "F.SilkS" (type "Top Silk Screen")) (layer "F.Paste" (type "Top Solder Paste")) '
         '(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01)) (layer "F.Cu" (type "copper") (thickness 0.035)) '
         '(layer "dielectric 1" (type "core") (thickness 1.51) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02)) '
         '(layer "B.Cu" (type "copper") (thickness 0.035)) (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01)) '
         '(layer "B.Paste" (type "Bottom Solder Paste")) (layer "B.SilkS" (type "Bottom Silk Screen")) '
         '(copper_finish "None") (dielectric_constraints no))')
assert '(setup' in txt and '(stackup' not in txt
txt = txt.replace('(setup', '(setup\n\t\t' + stack, 1)
open(OUT, 'w').write(txt)
print('saved', OUT)
