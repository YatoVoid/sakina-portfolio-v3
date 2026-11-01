# Retro PC (left-wall computer) — integration notes (awaiting Sakina's approval; NOT integrated)

Reference: `refs/ref_retro_pc.jpg` (beige desktop PC + CRT monitor on a swivel plate, keyboard, mouse).
The reference's brand text is not copied; the badges say SAKINA.

## What it replaces (v17, collection `Station`, parent `Station_Root`)
`PC_Unit`, `PC_Bay_*`, `PC_Slot_*`, `PC_Lever_*`, `PC_LED`, `PC_Button*`, `PC_Lock*`, `PC_Reset`, `PC_Panel*`, `PC_Vent_*`,
`PC_SideVent_*`, `PC_TopVent_*`, `CRT2_*` (front, back, vents, screen, glass, lips, power), `Term_Key_*` and the room's old keyboard `KB_*` (case, keys, plate, feet, lamps, cables; NOT parented to `Station_Root`).
Kept: `Cabinet_*`, `Drawer_*`, `Polaroid`.

## Round 2 changes (requested after the position preview)
- **Polaroid** (Sakina's photo): stuck on the monitor's RIGHT-side bezel like the reference, facing straight into the room (+X), upright. World matrix translation (-2.682, 1.354, 0.870) after the 4 cm shift and the 4 cm photo move left, rotation_euler 0 (set via matrix_world after view_layer.update(); the empty has a parent-inverse rotation). The old Term_* text lines, CRT2_* and the L5_IBM_Screen light are not used with the new PC (remove/disable them at integration). Round 3: the white Polaroid_Border is kept but shrunk to a 3 mm frame (8.0 x 8.6 cm), Polaroid_Photo is resized to 7.4 x 8.0 cm with UVs cropped to u 0.14-0.88, v 0.00-0.80 of profile.jpg, and the photo plane is at world x -2.650 (in front of the bezel), y 1.354. See place_preview.py.
- **Wider cabinet**: +0.30 m toward the viewer's left (-Y), so the keyboard can stand to the left of the PC. Cabinet body/top/plinth/crown/drawer fronts/mouldings are stretched, feet moved to the new corners, handle bars/escutcheons/keyholes re-centred. See `place_preview.py: widen()`; the 20 wall postcards and the clock are NOT moved (they now sit over the right two thirds of the cabinet; say if they should follow).
- **Keyboard** at room (x -2.68, y 0.78) beside the case (`KB_X, KB_Y` in `build_retro_pc.py`); mouse stays right of the case.

## Placement (parent `Station_Root` at (-2.775, 1.25, 0); cabinet top z = 0.55)
| | |
|---|---|
| Local frame | origin = centre of the case footprint, front faces -Y, +X = viewer's right |
| Room transform | translate **(-2.675, 1.25, 0.55)**, rotate **Z +90 deg** (local front -> room +X, towards the room) |
| Footprint | case 44 x 30 cm; monitor 38.5 cm wide, 28 cm deep; keyboard 39 x 11 cm; mouse right of it |
| Wall clearance | rear of the monitor housing reaches x = -2.978 (wall at -3.000); keyboard front reaches x = -2.533 (cabinet top ends -2.535) |
| Monitor | swivelled **16 deg toward the viewer's left** (SWIVEL_DEG env, default -16; set 0 for straight). Viewer = standing in the room looking at the left wall, i.e. toward room -Y. |

## Desk move (requested: whole cabinet 4 cm to the left)
Edit: `Station_Root.location.y -= 0.04` (applied after the widening) (moves cabinet, drawers, PC and Polaroid together; wall postcards/clock stay).
**Open question for Sakina:** the cabinet is already flush with the left wall (x = -3.0), so "left" cannot mean into the wall.
Assumed here: toward the viewer's left when facing the wall = room -Y. If she meant a different direction it is the same one-line change.

## Files
`build_retro_pc.py`, `materials_pc.py` (deterministic); `export/retro_pc_source.blend` (procedural, bake from this);
`export/retro_pc.glb` / `.blend` (baked: case, monitor, keyboard+mouse, stand; flat materials for dark parts, emissive screen); `previews/` (studio light, not room light).

## Steps after approval
New edit script `pipeline/edits/eNN_station_pc.py` (delete the objects above, append the collection, apply transform, shift `Station_Root`),
re-bake the `Station` group only, new GLB filename, `/preview/` first. Coordinate with `round3` (it must be merged first).
The monitor screen image is a placeholder (green code). The site's IBM panel/`ibm` camera view uses the `Room_Station` bounding box, which changes slightly.
