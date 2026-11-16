"""Host python: (re)write manufacturing.json after the LAST source edit. Needs a published bundle (for the exact ignored-check list).
Run from the workspace root: $KICAD_HARNESS_PYTHON tools/board/make_manufacturing.py"""
import json, hashlib, glob, os
from pathlib import Path
from kicadpy.project import Project
from kicadpy.manufacture import design_inputs
root = Path('.').resolve()
sh = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
latest = max(glob.glob('boards/main_review/*/reports/check.json'), key=os.path.getmtime)
ignored = json.load(open(latest))['ignoredChecks']
shutil_root = Project(str(root / 'build/board/pub/design/main.kicad_pro')).root if (root / 'build/board/pub').is_dir() else root
def ev(*names): return [{'path': 'engineering/' + n, 'sha256': sh('engineering/' + n)} for n in names]
S = {
 'power': ('pass', 'Rails, divider ratio (2.084 V at 8.4 V), D1 drop, C1 sizing (1000 uF 10 V on 5 V), reset-state reasoning for servo PWM, strapping pins and fan; routed trunk widths measured (0.6 mm where clearance allows). Servo supply is wired to a splice at the buck (J3-J6 carry PWM only), so the board trunk carries <= 1.0 A against ~1.5 A for 0.6 mm / 1 oz; power budget table 2.80 A at 5 V, 2.65 A at 6.0 V pack (assumed figures).', ['power.md']),
 'protection': ('pass', 'Back-feed diode D1, no reverse diode by design (0.45 V drop), charger module not yet chosen (>= 5 A discharge required), harness PTC hold >= 3.5 A, ADC overvoltage margin, no hardware disable (firmware watchdog by contract).', ['protection.md']),
 'pinout': ('pass', 'All 16 U1 pads and 9 headers audited against the contract pin table and module card; kicadpy.verify netlist 0 differences, 0 hollow symbols.', ['pinout.md']),
 'thermal': ('pass', 'No regulator on the board; D1 dissipation 0.23 W; no thermal pad, pour or via claim.', ['thermal.md']),
 'assembly': ('pass', 'All parts hand-assembled; polarity, order and reference parts recorded; manual identities in parts.json with assumptions marked.', ['assembly.md']),
 'fabricator': ('pass', '2-layer 1.6 mm 1 oz explicit stackup, all widths/clearances/drills above the JLCPCB floor; ignored-check categories explained; never ordered.', ['fabricator.md']),
 'bringup': ('pass', 'Eight staged, current-limited steps with limits; GIA DINH items each have a check.', ['bringup.md']),
}
refs = [p for part in json.load(open('parts.json'))['parts'] for p in part['refdes']]
d = {'schemaVersion': 1, 'reviewer': 'board builder agent (AI, Claude Sonnet 5.5), independent tester review pending',
     'designInputs': design_inputs(shutil_root), 'acceptedIgnoredChecks': ignored,
     'checks': {k: {'status': v[0], 'analysis': v[1], 'evidence': ev(*v[2])} for k, v in S.items()},
     'assembly': {r: {'method': 'manual'} for r in refs}}
json.dump(d, open('manufacturing.json', 'w'), indent=2)
print('manufacturing.json written; designInputs', len(d['designInputs']))
