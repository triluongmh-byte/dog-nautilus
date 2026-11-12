"""Host python: write design rules + netclasses into design/main.kicad_pro (before routing)."""
import json, copy, sys
p = sys.argv[1] if len(sys.argv) > 1 else 'design/main.kicad_pro'
d = json.load(open(p))
ns = d['net_settings']
base = [c for c in ns['classes'] if c['name'] == 'Default'][0]
base.update(clearance=0.2, track_width=0.3, via_diameter=0.6, via_drill=0.3)
pw = copy.deepcopy(base); pw.update(name='Power', track_width=0.3, priority=0)
mid = copy.deepcopy(base); mid.update(name='Power_mid', track_width=0.3, priority=1)
ns['classes'] = [base, pw, mid]
ns['netclass_patterns'] = ([{'netclass': 'Power', 'pattern': n} for n in ('+5V',)] +
                           [{'netclass': 'Power_mid', 'pattern': n} for n in ('GND', '+5V_MCU', 'VBAT_SW', '+3V3')])
ds = d['board']['design_settings']
r = ds.setdefault('rules', {})
r.update(min_clearance=0.2, min_copper_edge_clearance=0.3, min_through_hole_diameter=0.3, min_via_diameter=0.5, min_track_width=0.2, min_hole_clearance=0.25, min_hole_to_hole=0.25)
json.dump(d, open(p, 'w'), indent=2)
print('rules set')
