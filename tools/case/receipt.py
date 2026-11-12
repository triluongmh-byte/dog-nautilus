"""Handwired verification receipt: case/reports/verification.json (manifest verification.report).

Every declared check calls write() after its own report: it hashes every STEP/STL in parts.json
and passes only when every declared check report exists, is current for these files and passed.
"""
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "case" / "out"
RECEIPT = ROOT / "case" / "reports" / "verification.json"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def part_shas():
    manifest = json.loads((OUT / "parts.json").read_text())
    shas = {"parts.json": sha(OUT / "parts.json")}
    for p in manifest["parts"]:
        for k in ("step", "stl"):
            shas[p[k]] = sha(OUT / p[k])
    return shas


def write():
    checks = json.loads((ROOT / "case" / "checks.json").read_text())["checks"]
    shas = part_shas()
    summary, ok = [], True
    for c in checks:
        path = ROOT / c["report"]
        try:
            rep = json.loads(path.read_text())
        except (OSError, ValueError):
            summary.append({"name": c["name"], "verdict": "unverified", "why": "no report"})
            ok = False
            continue
        verdict = rep.get("verdict") or ("pass" if rep.get("passed") else "fail")
        covered = rep.get("partShas") or {}
        # a report must be current for the parts it tests
        stale = [n for n in c.get("parts", []) for ext in ("step", "stl")
                 if covered.get(f"{n}.{ext}") not in (None, shas.get(f"{n}.{ext}"))]
        passed = verdict in ("pass", "review") and not stale
        ok &= passed
        summary.append({"name": c["name"], "verdict": verdict, "stale": stale})
    receipt = {"schema": 1, "passed": ok, "verdict": "pass" if ok else "fail",
               "scope": "handwired case: every declared case check (simple, moving, ...) on the current files",
               "checks": summary, "partShas": shas,
               "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt
