"""Usage: drc_summary.py file.kicad_pcb  -> kicad-cli DRC at all severities, one line per type with count and first example."""
import json, subprocess, sys, tempfile, collections
f = sys.argv[1]; out = tempfile.mktemp(suffix='.json')
subprocess.run(['timeout', '180', '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli', 'pcb', 'drc', '--severity-all', '--format', 'json', '-o', out, f], capture_output=True)
d = json.load(open(out)); c = collections.OrderedDict()
for k in ('violations', 'unconnected_items', 'schematic_parity'):
    for v in d.get(k, []): c.setdefault(v['type'], []).append([i['description'][:50] for i in v['items']])
for t, l in c.items(): print(len(l), t, l[0])
if not c: print('DRC clean')
