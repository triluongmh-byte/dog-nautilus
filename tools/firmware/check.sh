#!/bin/bash
# Usage: tools/firmware/check.sh [host|build|all]   (default all). Compile-only; never flashes.
# Skips work when inputs are unchanged (hash stamps in build/firmware/).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
B="$ROOT/build/firmware"; mkdir -p "$B"
MODE="${1:-all}"
NCPU="$(sysctl -n hw.ncpu 2>/dev/null || nproc)"
hashof() { find "$@" -type f \( -name "*.cpp" -o -name "*.c" -o -name '*.h' -o -name '*.ini' -o -name '*.sh' \) -print0 | sort -z | xargs -0 shasum | shasum | cut -d' ' -f1; }

host() {
  local h; h="$(hashof "$ROOT/firmware/src" "$ROOT/firmware/include" "$ROOT/tools/firmware")"
  if [ -f "$B/host.stamp" ] && [ "$(cat "$B/host.stamp")" = "$h" ]; then echo "host: unchanged, skipped"; return; fi
  c++ -std=c++17 -DHOST_TEST=1 -Wall -Wextra -I"$ROOT/firmware/include" \
    "$ROOT/tools/firmware/test_gait.cpp" "$ROOT/firmware/src/gait.cpp" "$ROOT/firmware/src/servos.cpp" \
    "$ROOT/firmware/src/battery.cpp" -o "$B/test_gait"
  "$B/test_gait"; node "$ROOT/tools/firmware/check_pages.js" "$ROOT/firmware/src/web_pages.h"; echo "$h" > "$B/host.stamp"
}

build() {
  local h; h="$(hashof "$ROOT/firmware/src" "$ROOT/firmware/include" "$ROOT/firmware/platformio.ini")"
  if [ -f "$B/build.stamp" ] && [ "$(cat "$B/build.stamp")" = "$h" ]; then echo "build: unchanged, skipped"; return; fi
  rm -rf "$B/sketch"; mkdir -p "$B/sketch"
  cp "$ROOT"/firmware/src/*.c "$ROOT"/firmware/src/*.cpp "$ROOT"/firmware/src/*.h "$ROOT"/firmware/include/*.h "$B/sketch/"
  mv "$B/sketch/main.cpp" "$B/sketch/sketch.ino"
  arduino-cli compile --fqbn esp32:esp32:esp32c3:CDCOnBoot=cdc,PartitionScheme=default \
    --libraries "${ARDUINO_DIRECTORIES_DATA%/arduino}/sketchbook/libraries" --jobs "$NCPU" --build-path "$B/arduino-build" --warnings default "$B/sketch" 2>&1 | tail -25
  [ "${PIPESTATUS[0]}" = 0 ] && echo "$h" > "$B/build.stamp"
}

case "$MODE" in host) host;; build) build;; all) host; build;; *) echo "usage: $0 [host|build|all]"; exit 2;; esac
