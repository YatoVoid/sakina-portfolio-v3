"""Edit #11 (integration): upholstered whitewash chair (Havalance reference) replaces the room's white ladder-back chair.

Removes the `WhiteChair` empty and its 17 `Chair_*` child meshes and appends the 3 meshes of
`components/chair/export/chair_source.blend` (procedural: whitewash wood, woven seat, nail studs) into `Desk`, the
collection the old chair meshes live in.

Placement (components/chair/INTEGRATION.md): same location as the v17 chair (-0.950, 0.900, 0) with rotZ = -22 deg + 180 deg
(the component faces -Y, the v17 chair was built facing +Y). Height 0.963 m, same as before.
"""
import bpy, os, math
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "components", "chair", "export", "chair_source.blend")
EXPECT_OLD = 17


def apply():
    wc = bpy.data.objects["WhiteChair"]
    old = [o for o in bpy.data.objects if o.name.startswith("Chair_") and o.parent == wc]
    assert len(old) == EXPECT_OLD, f"expected {EXPECT_OLD} chair meshes under WhiteChair, found {len(old)}"
    loc, rot = wc.location.copy(), wc.rotation_euler.copy()
    assert abs(rot.z - math.radians(-22)) < 0.01 and loc.z == 0.0, (tuple(loc), tuple(rot))
    others = [o.name for o in bpy.data.objects if o.parent in set(old) | {wc} and o not in old]
    assert not others, others
    dest = old[0].users_collection[0]
    meshes = {o.data for o in old}
    mats = {s.material for o in old for s in o.material_slots if s.material}
    for o in old:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.objects.remove(wc, do_unlink=True)
    for m in meshes:
        if m.users == 0:
            bpy.data.meshes.remove(m)

    with bpy.data.libraries.load(SRC, link=False) as (src, dst):
        dst.objects = list(src.objects)
    new = [o for o in dst.objects if o is not None]
    assert len(new) == 3, [o.name for o in new]
    for o in new:
        dest.objects.link(o)
        o.parent = None
        o.location = loc
        o.rotation_euler = (0.0, 0.0, rot.z + math.pi)
        o.scale = (1.0, 1.0, 1.0)
    for m in mats:
        if m.users == 0:
            bpy.data.materials.remove(m)
    bpy.context.view_layer.update()
    print(f"e11: removed {EXPECT_OLD} Chair_* meshes + WhiteChair, added {[o.name for o in new]} in '{dest.name}' "
          f"at {tuple(round(x, 3) for x in loc)} rotZ {math.degrees(rot.z) + 180:.0f}", flush=True)
