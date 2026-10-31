#!/usr/bin/env bash
# V3 Pipeline — compress_assets.sh
# Post-process GLB files with Draco mesh + KTX2 texture compression.
# Requires: @gltf-transform/cli  (npm install -g @gltf-transform/cli)
#
# Usage:
#   bash pipeline/compress_assets.sh              # compress all *.glb in assets/models/
#   bash pipeline/compress_assets.sh desk.glb     # compress one file
#
# Output: assets/models/<name>.compressed.glb  (keeps original alongside)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$REPO_ROOT/assets/models"

# ── Dependency check ───────────────────────────────────────────────────────
if ! command -v gltf-transform &>/dev/null; then
  echo "[ERROR] gltf-transform not found."
  echo "        Run: npm install -g @gltf-transform/cli"
  exit 1
fi
echo "gltf-transform $(gltf-transform --version 2>/dev/null || echo '(version unknown)')"

# ── Target files ───────────────────────────────────────────────────────────
if [[ $# -gt 0 ]]; then
  TARGETS=("$MODELS_DIR/$1")
else
  mapfile -t TARGETS < <(find "$MODELS_DIR" -maxdepth 1 -name "*.glb" ! -name "*.compressed.glb")
fi

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  echo "[WARN] No .glb files found in $MODELS_DIR"
  echo "       Run: python pipeline/build_model.py all"
  exit 0
fi

# ── Compress ───────────────────────────────────────────────────────────────
for SRC in "${TARGETS[@]}"; do
  BASE="$(basename "$SRC" .glb)"
  OUT="$MODELS_DIR/${BASE}.compressed.glb"
  BEFORE=$(stat -c%s "$SRC" 2>/dev/null || stat -f%z "$SRC")

  echo ""
  echo "── Compressing: $BASE.glb ──────────────────────────────────────"
  gltf-transform draco \
    --method edgebreaker \
    --quantize-position 14 \
    --quantize-normal 10 \
    --quantize-texcoord 12 \
    "$SRC" "$OUT"

  AFTER=$(stat -c%s "$OUT" 2>/dev/null || stat -f%z "$OUT")
  PCT=$(( (BEFORE - AFTER) * 100 / BEFORE ))
  echo "  Before: $((BEFORE / 1024)) KB  →  After: $((AFTER / 1024)) KB  (${PCT}% smaller)"
done

echo ""
echo "✓ Done. Compressed files:"
ls -lh "$MODELS_DIR"/*.compressed.glb 2>/dev/null || echo "  (none produced)"
