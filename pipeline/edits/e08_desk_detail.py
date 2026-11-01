"""Edit #8 (integration, Sakina approved 2026-10-31): detailed walnut desk replaces the room's centre desk.

Replaces the 43 `Desk_*` meshes of the `Desk` collection with the 5 meshes of the approved component
`components/desk/export/desk_source.blend` (procedural materials, so the lightmap bake stays crisp at any size).
Everything else in the `Desk` collection (mug, notebook, pens, pad, rolodex, calculator, CD player, chair) is
left exactly where it is: the component keeps the old footprint (2.90 x 0.70 m) and the top surface height
(0.720 m), so nothing on the desk has to move.

Placement (from components/desk/INTEGRATION.md): translate (0.20, 1.65, 0.00), no rotation, no scale.
Bake group: `Desk` (unchanged), so the site's picking of `Room_Desk` keeps working.
"""
import bpy, os
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "components", "desk", "export", "desk_source.blend")
PLACE = Vector((0.20, 1.65, 0.0))
EXPECT_OLD = 43


def apply():
    desk = bpy.data.collections["Desk"]
    old = [o for o in desk.objects if o.name.startswith("Desk_")]
    assert len(old) == EXPECT_OLD, f"expected {EXPECT_OLD} Desk_* objects, found {len(old)}"

    # Nothing outside the old desk may hang off the old desk (it would be deleted with it).
    old_set = set(old)
    orphans = [o.name for o in bpy.data.objects if o.parent in old_set and o not in old_set]
    assert not orphans, f"objects parented to the old desk: {orphans}"

    old_mats = {s.material for o in old for s in o.material_slots if s.material}
    old_meshes = {o.data for o in old if o.type == 'MESH'}
    for o in old:
        bpy.data.objects.remove(o, do_unlink=True)
    for m in old_meshes:
        if m.users == 0:
            bpy.data.meshes.remove(m)

    # Append the component (copied into this file, no link back to components/ at bake time).
    with bpy.data.libraries.load(SRC, link=False) as (src, dst):
        dst.objects = list(src.objects)
    new = [o for o in dst.objects if o is not None]
    assert len(new) == 5, [o.name for o in new]
    for o in new:
        desk.objects.link(o)
        o.parent = None
        o.location = PLACE
        o.rotation_euler = (0.0, 0.0, 0.0)
        o.scale = (1.0, 1.0, 1.0)

    for m in old_mats:                      # drop materials only the old desk used
        if m.users == 0:
            bpy.data.materials.remove(m)
    bpy.context.view_layer.update()
    print(f"e08: removed {len(old)} Desk_* objects, added {[o.name for o in new]} at {tuple(PLACE)}", flush=True)
