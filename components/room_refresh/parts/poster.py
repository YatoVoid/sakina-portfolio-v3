"""Move the blue DATA / LOVE poster off the right curtain onto the wall surface right of it.

The wall right of the curtain is the dark wooden post `Wood_Post` (x 1.12..1.42, front face y = 2.35); the
plaster between the post and the bookshelf is only 13 cm wide, too narrow for the 31 cm poster. The poster is
taped flat to the post's front face, centred on it, scaled 0.92 so 1.2 cm of wood shows each side.
All Poster* objects (sheet, text, dots, tape) move together; nothing is re-modelled.
"""
import bpy
from mathutils import Vector, Matrix

K = 0.92


def build(coll=None):
    D = bpy.data
    post = D.objects["Wood_Post"]
    pts = [post.matrix_world @ Vector(c) for c in post.bound_box]
    px = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    face_y = min(p.y for p in pts)
    parts = [o for o in D.objects if o.name.startswith("Poster")]
    sheet = D.objects["Poster"]
    sp = [sheet.matrix_world @ Vector(c) for c in sheet.bound_box]
    c_old = Vector(((min(p.x for p in sp) + max(p.x for p in sp)) / 2, max(p.y for p in sp),
                    (min(p.z for p in sp) + max(p.z for p in sp)) / 2))
    c_new = Vector((px, face_y - 0.0015, c_old.z))
    m = Matrix.Translation(c_new) @ Matrix.Diagonal((K, K, K, 1)) @ Matrix.Translation(-c_old)
    for o in parts:
        if o.parent is None or not o.parent.name.startswith("Poster"):
            o.matrix_world = m @ o.matrix_world
    return parts
