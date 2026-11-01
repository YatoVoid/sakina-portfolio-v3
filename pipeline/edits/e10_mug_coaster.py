"""Edit #10 (integration): speckled mug with espresso and wooden coaster replaces the room's mug.

Replaces `Mug`, `Mug_Handle`, `Coffee` and `Mug_Stain_A` (collection `Desk`) with the 3 meshes of
`components/mug/export/mug_source.blend` (procedural materials). Kept: `Mug_Stain_B` (a ring stain on the desk top)
and `Steam` (separate lighting effect).

Placement (components/mug/INTEGRATION.md): translate (-0.2305, 1.3995, 0.720), rotate 180 deg about Z so the handle
stays on the -X side as in the room. The old mug centre was x = -0.2405; the 1 cm shift keeps the wider coaster clear of
the notebook edge (x = -0.294) and `Note_Stack`.
"""
import bpy, os, math
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "components", "mug", "export", "mug_source.blend")
OLD = ["Mug", "Mug_Handle", "Coffee", "Mug_Stain_A"]
PLACE = Vector((-0.2305, 1.3995, 0.720))


def apply():
    desk = bpy.data.collections["Desk"]
    old = [bpy.data.objects[n] for n in OLD]
    assert all(o.name in desk.objects for o in old), "old mug objects not all in Desk"
    old_set = set(old)
    assert not [o.name for o in bpy.data.objects if o.parent in old_set and o not in old_set]
    meshes = {o.data for o in old if o.type == 'MESH'}
    mats = {s.material for o in old for s in o.material_slots if s.material}
    for o in old:
        bpy.data.objects.remove(o, do_unlink=True)
    for m in meshes:
        if m.users == 0:
            bpy.data.meshes.remove(m)

    with bpy.data.libraries.load(SRC, link=False) as (src, dst):
        dst.objects = list(src.objects)
    new = [o for o in dst.objects if o is not None]
    assert len(new) == 3, [o.name for o in new]
    for o in new:
        desk.objects.link(o)
        o.parent = None
        o.location = PLACE
        o.rotation_euler = (0.0, 0.0, math.pi)
        o.scale = (1.0, 1.0, 1.0)
    for m in mats:
        if m.users == 0:
            bpy.data.materials.remove(m)
    # `Steam` is left untouched: it is an effect mesh skipped by the bake and the web export. Its column is wider than
    # the new mug's opening, so it overlaps the rim (tested: lifting it does not remove that, it only adds a coffee overlap).
    bpy.context.view_layer.update()
    print(f"e10: removed {OLD}, added {[o.name for o in new]} at {tuple(round(x, 4) for x in PLACE)} rotZ 180", flush=True)
