#!/bin/bash
# Copy the site from the current branch's web/ into a main-branch worktree's web/preview/ (the candidate page).
#   pipeline/tools/publish_preview.sh <main_worktree> <room.glb>
# The room GLB is copied next to the preview page; the outside GLB is shared with the main page (../).
set -euo pipefail
MAIN=$1; GLB=$2
SRC="$(cd "$(dirname "$0")/../.." && pwd)/web"
DST="$MAIN/web/preview"
mkdir -p "$DST"
for f in index.html style.css main.js look-controls.js content.js audio.js tapes.json; do
  cp "$SRC/$f" "$DST/$f"
done
cp "$GLB" "$DST/$(basename "$GLB")"
# outside GLB lives at the site root
sed -i 's#loader.load("sakina-outside.glb"#loader.load("../sakina-outside.glb"#' "$DST/main.js"
grep -n 'load("' "$DST/main.js"
