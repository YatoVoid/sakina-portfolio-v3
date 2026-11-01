# Mug + coaster — integration notes (awaiting Sakina's approval; NOT integrated)

## What it replaces

In the room's `Desk` collection (v17): `Mug`, `Mug_Handle`, `Coffee`, `Mug_Stain_A`.
Not replaced: `Mug_Stain_B` (a ring stain on the desk top, kept), `Steam` (separate lighting effect, kept).

## Placement

| | |
|---|---|
| Local origin | centre of the coaster bottom, on the desk surface; handle toward +X; front faces −Y |
| Room transform (v17) | translate **(−0.2305, 1.3995, 0.720)** (the old mug centre is x = −0.2405; shifted 1 cm toward +X because the wider coaster would otherwise clip the notebook edge at x = −0.294) |
| Handle side | The room's mug has its handle on −X → add a **180° rotation about Z** to keep that side. Without it the handle is on the right, as in the reference photo. |
| Footprint | coaster Ø 11.5 cm (+ handle: 14.3 × 11.4 cm), total height 10.3 cm with handle ring and rim wobble |

The coaster is 1.4 cm thick, so the rim ends 1.4 cm above the old mug base level. Checked against the v17 object list: with the 1 cm shift the coaster clears the notebook (edge x = −0.294 vs. coaster edge x = −0.288)
and `Note_Stack` (y ≥ 1.494 vs. coaster y ≤ 1.457). With the handle on −X the ring passes above the notebook (ring bottom is about 2 cm above the desk,
the notebook is 1.4 cm thick).

## Files

| File | Use |
|---|---|
| `build_mug.py`, `materials_mug.py` | deterministic build (fixed phases, no random seeds) |
| `export/mug_source.blend` | procedural materials — use this for the room bake |
| `export/mug.glb` | real-time asset: 3 meshes, baked base colour / roughness / normal (body 2048, coaster 1536, coffee 512) |
| `export/mug.blend` | the same baked version as the GLB |
| `refs/` | reference photo and the certain/inferred analysis |
| `previews/` | Cycles studio renders (neutral studio light, not the room lighting) |

## Objects (bake group: `Desk`)

`Mug_Body` (mug + handle, one fused mesh, about 32 k triangles), `Mug_Coffee`, `Mug_Coaster` (wood top/bottom + bark side).

## Budget

About 35 k triangles and 3 textures in total. For the baked room this does not matter (the room is lightmapped),
but if the mug is ever used as a real-time prop the body can be decimated further (`MUG_TRIS` env var).

## Proposed integration steps (after approval)

1. New edit script `pipeline/edits/eNN_mug.py`: delete the four room objects above, append the collection from
   `mug_source.blend`, link into `Desk`, apply the transform.
2. Re-bake the `Desk` group only (192 spp), splice into a new room GLB filename, publish to `/preview/` first.
3. The speckles are tiny (0.3 mm radius). In the room's lightmap pipeline the material is evaluated procedurally,
   but the baked room textures are limited by the lightmap resolution, so check the close-up view on the real site.

## Coordination

The room session (branch `round3`) does not edit `Mug*`, `Coffee` or `Mug_Stain_A` (checked: no references in
`e02`–`e07`).
