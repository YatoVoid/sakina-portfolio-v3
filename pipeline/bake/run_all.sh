#!/bin/bash
set -e
B=/home/wali/sakina-polish/v2
F="flatpak run org.blender.Blender -b"
$F $B/source/sakina-v17.blend --python $B/pipeline/sakina_v19.py
$F $B/source/sakina-v19.blend --python $B/pipeline/sakina_v20.py
flatpak run --env=SPP=192 --env=SAVE=$B/source/sakina-v21-baked.blend org.blender.Blender -b $B/source/sakina-v20.blend --python $B/pipeline/bake_lightmaps.py
$F $B/source/sakina-v21-baked.blend --python $B/pipeline/fix_baked21.py
flatpak run --env=EXPORT_DIR=$B/web org.blender.Blender -b $B/source/sakina-v21-baked.blend --python $B/pipeline/export_web.py
