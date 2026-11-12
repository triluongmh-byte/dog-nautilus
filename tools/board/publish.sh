#!/bin/zsh
# Sandbox workaround: kicadpy stores snapshots in <project root>/../.kicadpy, which is outside the worktree here.
# So publish from a real copy under build/board/pub (store lands in build/board/.kicadpy), then copy the outputs back.
set -e; cd "$(dirname "$0")/../.."
W=build/board/pub; mkdir -p $W
rsync -a --delete design/ $W/design/; rsync -a --delete engineering/ $W/engineering/
cp product.json parts.json manufacturing.json $W/ 2>/dev/null || true
$KICAD_HARNESS_PYTHON -m kicadpy.publish --manufacturing $W/design/main.kicad_pro | cut -c1-400 | tail -2
mkdir -p boards .harness; rsync -a --delete $W/boards/ boards/; [ -d $W/.harness ] && rsync -a $W/.harness/ .harness/ || true
(cd $W && $KICAD_HARNESS_PYTHON -m kicadpy.verify gate . | tail -30 | cut -c1-260)
