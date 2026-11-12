"""KiCad python, in place on design/main.kicad_pcb: mount holes follow contract labels under (x,-y); C1 value 10V. Keeps copper."""
import pcbnew
mm = pcbnew.FromMM
f = 'design/main.kicad_pcb'; b = pcbnew.LoadBoard(f)
pos = {'MH1': (40.5, 23.5), 'MH2': (57.5, 23.5), 'MH3': (57.5, -23.5), 'MH4': (40.5, -23.5)}
for fp in b.GetFootprints():
    r = fp.GetReference()
    if r in pos: fp.SetPosition(pcbnew.VECTOR2I(mm(pos[r][0]), mm(pos[r][1])))
    if r == 'C1': fp.SetValue('1000uF 10V')
b.Save(f)
