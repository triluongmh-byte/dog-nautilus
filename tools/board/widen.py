"""KiCad python: widen power tracks of a routed board. Each track is tried alone (in parallel over all CPUs) at the widest
target that adds no DRC finding; the passing set is then applied together and re-checked (fallback: sequential).
Usage: widen.py in.kicad_pcb out.kicad_pcb"""
import sys, os, subprocess, json, tempfile, shutil, pcbnew
from concurrent.futures import ThreadPoolExecutor
mm = pcbnew.FromMM
src, dst = sys.argv[1], sys.argv[2]
CLI = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
D = os.path.dirname(os.path.abspath(dst))
TARGETS = {'+5V': [0.6, 0.5, 0.4], 'GND': [0.5, 0.4, 0.3], '+5V_MCU': [0.5, 0.4, 0.3], 'VBAT_SW': [0.5, 0.4, 0.3], '+3V3': [0.4, 0.3]}
def drc(f):
    o = tempfile.mktemp(suffix='.json')
    subprocess.run(['timeout', '180', CLI, 'pcb', 'drc', '--severity-all', '--format', 'json', '-o', o, f], capture_output=True)
    d = json.load(open(o)); return len(d['violations']) + len(d['unconnected_items'])
def variant(widths, name):
    """widths: {track index: width mm} -> saved copy path (tracks addressed by index in this identical source)."""
    b = pcbnew.LoadBoard(src); tr = list(b.GetTracks())
    for i, w in widths.items(): tr[i].SetWidth(mm(w))
    f = os.path.join(D, name + '.kicad_pcb'); b.Save(f); return f
b = pcbnew.LoadBoard(src); tracks = list(b.GetTracks())
cand = [(i, t.GetNetname(), t.GetWidth() / 1e6) for i, t in enumerate(tracks) if t.GetClass() == 'PCB_TRACK' and t.GetNetname() in TARGETS]
base = drc(src); print('base findings', base)
def best(item):
    i, net, w0 = item
    for tw in TARGETS[net]:
        if tw <= w0 + 1e-6: return i, None
        f = variant({i: tw}, 'w_%d_%s' % (i, tw))
        ok = drc(f) <= base
        os.remove(f)
        if ok: return i, tw
    return i, None
with ThreadPoolExecutor(max_workers=os.cpu_count()) as ex: res = dict(ex.map(best, cand))
good = {i: w for i, w in res.items() if w}
f = variant(good, 'w_all')
n = drc(f)
print('individually widenable', len(good), 'of', len(cand), 'combined findings', n)
if n > base:   # interactions: add tracks one by one, widest nets first
    good2 = {}
    for i in sorted(good, key=lambda k: -good[k]):
        t = dict(good2); t[i] = good[i]
        g = variant(t, 'w_try')
        if drc(g) <= base: good2 = t
        os.remove(g)
    good = good2; f = variant(good, 'w_all'); print('after sequential', len(good))
shutil.move(f, dst)
for p in os.listdir(D):
    if p.startswith('w_'): os.remove(os.path.join(D, p))
