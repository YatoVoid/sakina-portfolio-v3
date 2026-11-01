"""Shared helpers for standalone components (components/<name>/).

Isolated from the room: no room lights, no bake groups, no renderer settings are read or written.
Units: metres. Blender is Z-up; the glTF exporter converts to Y-up.
"""
import json
import math
import os
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]          # components/


def comp_dir(name):
    d = ROOT / name
    for sub in ("export", "previews", "refs"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------- scene
def new_scene(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.name = name
    scn.unit_settings.system = "METRIC"
    scn.unit_settings.scale_length = 1.0
    col = bpy.data.collections.new(name)
    scn.collection.children.link(col)
    return col


def link(obj, col):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    col.objects.link(obj)
    return obj


def hex_lin(h):
    """sRGB hex -> linear RGBA."""
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


# ---------------------------------------------------------------- mesh helpers
def mesh_obj(name, bm, col, smooth=False):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def box(name, size, loc, col, bevel=0.0, segments=2, mat=None):
    """Axis-aligned box, size=(x,y,z) full extents, loc = centre. Optional real bevel."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=segments,
                        affect="EDGES", profile=0.5, clamp_overlap=True)
    ob = mesh_obj(name, bm, col)
    ob.location = loc
    if mat:
        ob.data.materials.append(mat)
    shade_auto(ob)
    return ob


def shade_auto(ob, angle=35):
    me = ob.data
    for p in me.polygons:
        p.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(angle))
    except Exception:
        pass


def apply_all(ob):
    bpy.context.view_layer.objects.active = ob
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def smart_uv(ob, island_margin=0.003, scale_to_m=True):
    """Box-projected UVs in world metres (1 UV unit = 1 m) so tiling textures keep real scale."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    mw = ob.matrix_world
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            co = mw @ l.vert.co
            if ax == 0:
                l[uv].uv = (co.y, co.z)
            elif ax == 1:
                l[uv].uv = (co.x, co.z)
            else:
                l[uv].uv = (co.x, co.y)
    bm.to_mesh(me)
    bm.free()


# ---------------------------------------------------------------- export + checks
def stats(col):
    tris = verts = 0
    mats = set()
    dg = bpy.context.evaluated_depsgraph_get()
    lo = Vector((1e9,) * 3)
    hi = Vector((-1e9,) * 3)
    for ob in col.all_objects:
        if ob.type != "MESH":
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        verts += len(me.vertices)
        for v in me.vertices:
            w = ob.matrix_world @ v.co
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
        for s in ob.material_slots:
            if s.material:
                mats.add(s.material.name)
        ev.to_mesh_clear()
    return {"triangles": tris, "vertices": verts, "materials": sorted(mats),
            "bbox_min_m": [round(x, 4) for x in lo], "bbox_max_m": [round(x, 4) for x in hi],
            "size_m": [round(h - l, 4) for l, h in zip(lo, hi)]}


def export(name, col, bake_px=1024):
    d = comp_dir(name)
    blend = d / "export" / f"{name}.blend"
    glb = d / "export" / f"{name}.glb"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)
    for ob in bpy.context.view_layer.objects:
        ob.select_set(ob.name in col.all_objects)
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True, export_image_format="JPEG",
                              export_jpeg_quality=88)
    st = stats(col)
    st["glb_bytes"] = glb.stat().st_size
    (d / "export" / f"{name}.stats.json").write_text(json.dumps(st, indent=2))
    print(f"[{name}] {json.dumps(st)}")
    return st
