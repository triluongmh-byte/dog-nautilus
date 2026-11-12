"""Host python: run Freerouting on build/board/cand/main.dsn until it reports 0 unrouted (the router is not deterministic), max 8 tries."""
import sys
from pathlib import Path
from circuitpy import toolchain
dsn, ses = Path(sys.argv[1]), Path(sys.argv[2])
for k in range(8):
    r = toolchain.run_freerouting(dsn, ses, passes=25, threads=4, timeout=600)
    line = [l for l in r.output.splitlines() if 'Auto-routing stage completed' in l]
    ok = bool(line) and '(0 unrouted' in line[-1]
    print('try', k + 1, 'ok' if ok else 'unrouted left')
    if ok: break
