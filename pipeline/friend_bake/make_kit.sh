#!/bin/bash
# Build the zip to send to the friend:  pipeline/friend_bake/make_kit.sh <pre-bake blend> <out.zip>
set -e
BLEND="$1"; ZIP="$2"; ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
K=$(mktemp -d)/v3-bake-kit; mkdir -p "$K/pipeline/bake" "$K/pipeline/tools"
cp "$ROOT/pipeline/friend_bake/"{run_bake.py,run_bake.bat,README.txt} "$K/"
cp "$ROOT/pipeline/bake/bake_lightmaps.py" "$K/pipeline/bake/"
cp "$ROOT/pipeline/tools/oidn.py" "$K/pipeline/tools/"
cp "$BLEND" "$K/v3-integrated.blend"
(cd "$(dirname "$K")" && zip -qr "$ZIP" v3-bake-kit)
ls -la "$ZIP"
