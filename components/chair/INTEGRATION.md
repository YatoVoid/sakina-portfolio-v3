# Chair — integration notes (awaiting Sakina's approval; NOT integrated)

Reference: Ashley Havalance upholstered dining chair (`refs/ref_havalance_chair.png`).

## What it replaces
The room's `WhiteChair` empty and its `Chair_*` child meshes (collection `Chair`/`Desk`; 17 meshes found in v17:
ladder back with 3 rails, solid seat, stretchers). `chair_before.blend` holds them for before/after renders.

## Placement
Local origin = floor centre, front faces **−Y**. The v17 chair faces +Y locally and sits at (−0.950, 0.900, 0) with rotZ −22°.
Use the same location with **rotZ = −22° + 180°** (the v17 mesh is built facing the other way). Height 0.963 m = same as v17;
footprint 0.47 x 0.57 m (rear legs flare back). Check the clearance to the desk and the keep-out of neighbouring props in the room before baking.

## Objects (bake group: same as v17 chair)
`Chair_Wood` (whitewash, baked 2048), `Chair_Seat` (woven fabric, baked 2048), `Chair_Nails` (59 studs, flat material). About 40 k triangles.

## Files
`build_chair.py`, `materials_chair.py` (deterministic); `export/chair_source.blend` (procedural, bake from this);
`export/chair.glb` / `chair.blend` (baked); `previews/` (studio Cycles, not room lighting).

## Steps after approval
New edit script `pipeline/edits/eNN_chair.py`: delete the old chair, append the collection from `chair_source.blend`, apply transform; re-bake only that group; new GLB filename; `/preview/` first.
The room has warm low light, so the white paint will bake much darker/warmer than in these studio renders — check it in the real scene before approving.
