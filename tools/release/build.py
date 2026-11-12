"""Release rebuild from checked sources, with no downloads or hardware actions."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
HOST = os.environ.get("KICAD_HARNESS_PYTHON", "")
CASE = os.environ.get("KICAD_CASE_PYTHON", "")


def need_exe(value, label):
    if not value or not (Path(value).is_file() or shutil.which(value)):
        raise RuntimeError(f"Missing {label}: install/configure the existing toolchain first (no automatic installs).")


def run(args, timeout=1800):
    print("+ " + " ".join(str(a) for a in args), flush=True)
    subprocess.run([str(a) for a in args], check=True, timeout=timeout)


def report(path):
    value = json.loads(Path(path).read_text())
    if not value.get("passed", value.get("verdict") == "pass"):
        raise RuntimeError(f"Check failed: {path}; inspect this report before publishing.")
    return value


def board():
    # Export the already checked native board; do not re-route or replace its copper.
    from kicadpy import toolchain
    cli = toolchain.executable("cli")
    need_exe(str(cli), "KiCad CLI")
    run(["zsh", "tools/board/publish.sh"])
    run([HOST, "tools/board/make_manufacturing.py"])
    run(["zsh", "tools/board/publish.sh"])
    sidecar = json.loads(Path("boards/main.board.json").read_text())
    checks = sorted(Path("boards/main_review").glob("*/reports/check.json"), key=lambda p: p.stat().st_mtime)
    current = checks[-1]
    report(current)
    manufacturing = json.loads((current.parent.parent / "manufacturing/manufacturing-report.json").read_text())
    if not manufacturing.get("prototypeReady") or not sidecar.get("fab", {}).get("ready"):
        raise RuntimeError("Manufacturing review is not current/passed; see the published report.")
    Path("build/board-validation.json").write_text(json.dumps({"native": json.loads(current.read_text()), "manufacturing": manufacturing, "hardwareTested": False}, indent=2) + "\n")
    run([str(cli), "pcb", "export", "step", "--force", "--board-only", "-o", "boards/main.step", "design/main.kicad_pcb"], 180)
    run([HOST, "-m", "kicadpy.verify", "stale", "."])


def case():
    need_exe(CASE, "KICAD_CASE_PYTHON (CadQuery + kicadpy)")
    need_exe("node", "Node.js")
    need_exe("/Applications/BambuStudio.app/Contents/MacOS/BambuStudio", "Bambu Studio 2.7 macOS CLI/profiles")
    if not Path("PILOT_CONTRACT.json").is_file():
        raise RuntimeError("Missing sealed PILOT_CONTRACT.json source input")
    run([CASE, "case/build.py"])
    run([CASE, "-m", "kicadpy.case_drawing", "."])
    run([CASE, "tools/case/docs/profiles.py"])
    run([CASE, "tools/case/docs/make_plates.py"])
    run([CASE, "tools/case/docs/slice_and_verify.py"])
    report("case/print/production-check.json")
    report("case/print/test-only-check.json")
    manifest_path = Path("case/out/parts.json")
    manifest = json.loads(manifest_path.read_text())
    manifest["overview"] = "../overview.html"
    manifest["revision"] = "r2"
    manifest["printProject"] = {"file": "../print/production.3mf", "report": "../print/production-check.json"}
    manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")
    # Checks hash the current exported geometry/manifest, rather than frozen output hashes.
    for check in json.loads(Path("case/checks.json").read_text())["checks"]:
        run([CASE, check["script"], *check.get("args", [])], check.get("timeoutSeconds", 1800))
        report(check["report"])
    report("case/reports/verification.json")
    run([CASE, "-m", "kicadpy.case", "check-print", "."])
    report("case/reports/print-check.json")
    run([CASE, "tools/case/docs/write_docs.py"])
    run([CASE, "-m", "kicadpy.case_overview", "."])
    run([CASE, "tools/render_readme.py"])


def firmware():
    for exe in ("arduino-cli", "c++", "node"):
        need_exe(exe, exe)
    if not os.environ.get("ARDUINO_DIRECTORIES_DATA"):
        raise RuntimeError("Missing ARDUINO_DIRECTORIES_DATA: set it to the installed ESP32 Arduino data directory.")
    run(["bash", "tools/firmware/check.sh", "all"])
    if not Path("build/firmware/arduino-build/sketch.ino.bin").is_file():
        raise RuntimeError("Firmware binary missing after compilation")


if __name__ == "__main__":
    try:
        stages = sys.argv[1:] or ["board", "case", "firmware"]
        unknown = set(stages) - {"board", "case", "firmware"}
        if unknown:
            raise RuntimeError("Unknown stage(s): " + ", ".join(sorted(unknown)))
        if "case" in stages and not Path("boards/main.enclosure.json").exists() and "board" not in stages:
            stages.insert(0, "board")
        need_exe(HOST, "KICAD_HARNESS_PYTHON")
        for name in ("board", "case", "firmware"):
            if name in stages:
                print(f"=== {name} ===", flush=True)
                globals()[name]()
        Path("build").mkdir(exist_ok=True)
        git = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
        Path("build/release-proof.json").write_text(json.dumps({"passed": True, "stages": stages, "sourceCommit": git.stdout.strip() if git.returncode == 0 else None, "hardwareTested": False}, indent=2) + "\n")
    except (RuntimeError, subprocess.SubprocessError, OSError, ValueError) as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
