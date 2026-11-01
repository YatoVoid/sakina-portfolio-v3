"""Edit #6c (user request 2026-11-01): keep only the Iqra University degree frame and centre it under the two clocks
(midway between the Karachi and Houston clock centres, x = -1.815); the University of Houston frame is removed.
Frames are told apart by their x centre (Iqra < -1.815 < Houston). All Degree_* objects are in the Keepsakes group.
"""
import bpy
from mathutils import Vector, Matrix

D = bpy.data
SPLIT_X = -1.815
IQRA_OLD_CX = -2.11
TARGET_CX = -1.815


def _cx(o):
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return (min(w.x for w in ws) + max(w.x for w in ws)) / 2


def apply():
    keep, drop = [], []
    for o in list(D.objects):
        if o.name.startswith("Degree_"):
            (keep if _cx(o) < SPLIT_X else drop).append(o)
    for o in drop:
        D.objects.remove(o, do_unlink=True)
    T = Matrix.Translation((TARGET_CX - IQRA_OLD_CX, 0, 0))
    for o in keep:
        o.matrix_world = T @ o.matrix_world
    bpy.context.view_layer.update()
    print(f"e08: removed {len(drop)} Houston-degree objects, moved {len(keep)} Iqra-degree objects by {TARGET_CX - IQRA_OLD_CX:+.3f} m", flush=True)
