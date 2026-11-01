# Desk — integration notes (awaiting Sakina's approval; NOT integrated)

## What it replaces

The 43 `Desk_*` meshes of the room's centre desk (v17 collection `Desk`): top, edge band, grooves, joints,
rails, legs, leg blocks, brass caps, drawer, pull, keyhole. Props on the desk (mug, notebook, pens, pad,
rolodex, calculator, CD player, chair) are **not** part of this component and stay as they are.

## Placement

| | |
|---|---|
| Local origin | floor, under the centre of the top; front faces −Y |
| Room transform (v17) | translate **(0.20, 1.65, 0.00)**, no rotation, no scale |
| Footprint | 2.90 × 0.70 m, top surface at **0.720 m** (identical to the room desk) |
| Legs | x = ±1.40, y = ±0.30 (local) — same positions as the room legs |

Props keep resting on z = 0.720, so nothing on the desk moves.

## Files

| File | Use |
|---|---|
| `build_desk.py` | builds everything (deterministic, seeded) |
| `export/desk_source.blend` | **procedural** materials — use this for the room bake (crisp at any lightmap size) |
| `export/desk.glb` | real-time PBR asset (baked base colour / roughness / normal textures, 2048 px) |
| `export/desk.blend` | the same baked version as the GLB |
| `previews/` | Cycles studio renders (neutral studio light, not the room lighting) |

## Objects (one bake group: `Desk`)

`Desk_Top` (planks), `Desk_Frame` (legs, aprons, moulding, stretchers, cock bead, drawer front),
`Desk_DrawerBox` (dark interior), `Desk_Brass` (bail pull, escutcheon, cup feet), `Desk_KeyholeSlot`.

## Proposed integration steps (owned by whoever integrates, after approval)

1. New edit script `pipeline/edits/eNN_desk_detail.py`: delete the 43 `Desk_*` meshes listed above, append the
   collection from `components/desk/export/desk_source.blend`, link the objects into the `Desk` collection,
   translate by (0.20, 1.65, 0).
2. Re-bake the `Desk` group only (192 spp, as per DECISIONS.md), splice into a **new** room GLB filename.
3. The site's raycast picks `Room_Desk` by merged mesh name — unchanged, because the objects stay in the
   `Desk` bake group.
4. Publish to `/preview/` first; verify notepad / desk interactions still work.

## Coordination

The active room session (branch `round3`) does not touch the desk (checked: no `Desk_` references in its
edits e02–e07). Its warm-light pass (e07) changes the lighting only, so this component bakes correctly under it.
