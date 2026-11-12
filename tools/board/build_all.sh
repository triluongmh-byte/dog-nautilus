#!/bin/zsh
# Rebuild everything from scratch: spec -> schematic -> pcb -> rules -> route -> install to design/. Usage: tools/board/build_all.sh
set -e; cd "$(dirname "$0")/../.."
P=$KICAD_HARNESS_PYTHON; KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
$P tools/board/gen_spec.py
$P -m kicadpy.author write build/board/spec.json design/ >/dev/null
$P tools/board/set_rules.py
mkdir -p build/board/cand; rm -f build/board/cand/*
cp design/main.kicad_pro design/fp-lib-table design/sym-lib-table build/board/cand/; ln -s ../../../design/nautilus.pretty build/board/cand/nautilus.pretty
$KP tools/board/build_pcb.py build/board/cand/main.kicad_pcb 2>&1 | tail -1
cp design/main.kicad_pro build/board/cand/main.kicad_pro   # pcbnew rewrites the .pro on save; restore our rules
$KP tools/board/route.py dsn build/board/cand/main.kicad_pcb 2>&1 | tail -1
$P tools/board/freeroute.py build/board/cand/main.dsn build/board/cand/main.ses
$KP tools/board/route.py ses build/board/cand/main.kicad_pcb 2>&1 | tail -1
$KP tools/board/widen.py build/board/cand/main_routed.kicad_pcb build/board/cand/main_final.kicad_pcb | tail -6
cp build/board/cand/main_final.kicad_pcb design/main.kicad_pcb
