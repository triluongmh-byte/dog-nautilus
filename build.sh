#!/usr/bin/env bash
# Rebuild outputs only; never flash, print, upload or install dependencies.
set -euo pipefail
cd "$(dirname "$0")"
if [[ -z "${KICAD_HARNESS_PYTHON:-}" || ! -x "$KICAD_HARNESS_PYTHON" ]]; then
  echo 'Missing KICAD_HARNESS_PYTHON: select the Harness KiCad toolchain host Python.' >&2
  exit 2
fi
exec "$KICAD_HARNESS_PYTHON" tools/release/build.py "$@"
