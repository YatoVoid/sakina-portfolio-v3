#!/bin/bash
# Bake several groups in sequence (each in its own process), V3 round 3 settings by default:
#   SPP=64 DENOISE=1 pipeline/bake_groups.sh <scene.blend> <out_dir> Desk Monitor ...
# Logs: <out_dir>/bake_<Group>.log ; a line "ALLDONE <groups>" is appended to <out_dir>/progress.log at the end.
set -u
SCENE=$1; OUT=$2; shift 2
export SPP=${SPP:-64} DENOISE=${DENOISE:-1} V3_WORK=${V3_WORK:-/tmp/v3work}
mkdir -p "$OUT"
cd "$(dirname "$0")/.."
for G in "$@"; do
  t=$(date +%s)
  python3 pipeline/bake_group.py "$G" "$SCENE" "$OUT" > "$OUT/bake_$G.log" 2>&1
  rc=$?
  echo "$G rc=$rc $(( $(date +%s) - t ))s" >> "$OUT/progress.log"
done
echo "ALLDONE $*" >> "$OUT/progress.log"
