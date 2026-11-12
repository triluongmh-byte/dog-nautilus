"""KiCad python: DSN export -> Freerouting (host python helper called by shell) -> SES import, on a copy. Usage: route.py dsn|ses cand.kicad_pcb"""
import sys, os, pcbnew
mm = pcbnew.FromMM
mode, f = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(f)
if mode == 'dsn':
    pcbnew.ExportSpecctraDSN(b, f.replace('.kicad_pcb', '.dsn'))
else:
    pcbnew.ImportSpecctraSES(b, f.replace('.kicad_pcb', '.ses'))
    for t in b.GetTracks():
        if t.GetWidth() < mm(0.2): t.SetWidth(mm(0.2))   # router pad-stub necking -> board minimum
    b.Save(f.replace('.kicad_pcb', '_routed.kicad_pcb'))
print(mode, 'done', len(b.GetTracks()), 'tracks')
