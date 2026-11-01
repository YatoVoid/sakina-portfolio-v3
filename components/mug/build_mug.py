"""Speckled stoneware mug on a wooden-slice coaster (standalone component).

Reference: Sakina's photo (components/mug/refs/ref_speckled_mug.png) — "irregular ceramic coffee mug, speckled".
Copied from the photo (certain): hand-thrown, slightly squared body that flares toward an uneven rim; thick rounded
  rim; white glaze with fine black speckles (mostly tiny, a few larger); chunky round "donut" handle attached on
  the right at mid-height; espresso with crema ~1 cm below the rim; wooden-slice coaster a little wider than the
  mug base, with a bark edge and a pale cambium line.
Inferred (not visible in the photo): exact dimensions (mug about 10 cm wide x 8.5 cm tall, handle 4 cm), wall
  thickness (4.2 mm), the base of the mug (hidden by the coaster), the underside of the coaster, ring count of the slice.

Replaces in the room (v17 collection "Desk"): Mug, Mug_Handle, Coffee, Mug_Stain_A. Steam (Mug's steam plane) is a
  separate lighting effect and is NOT part of this component.
Local frame: origin = centre of the coaster bottom, on the desk surface; handle toward +X; front faces -Y; metres.
Room placement (v17): translate (-0.2405, 1.3995, 0.720). The room's mug has its handle on -X, so add a 180 deg
  rotation about Z to keep the same side (or leave it as in the reference photo, handle on the right).
Run: python3 components/mug/build_mug.py -> export/mug_source.blend, mug.blend, mug.glb, mug.stats.json
"""
import json
import math
import os
import random
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_lib"))
sys.path.insert(0, str(HERE))
import common as C          # noqa: E402
import materials as M       # noqa: E402
import materials_mug as MM  # noqa: E402

NAME = "mug"
TEX_PX = int(os.environ.get("TEX_PX", 2048))
TARGET_TRIS = int(os.environ.get("MUG_TRIS", 32000))

H = 0.085                   # mug height
R_BASE, R_RIM = 0.037, 0.050
WALL, FLOOR = 0.0042, 0.009
COAST_T, COAST_R = 0.014, 0.0575
ZB = COAST_T - 0.0002       # mug base height (rests on the coaster)
AX, AY = 0.002, -0.002      # mug axis offset on the coaster
COFFEE_Z = ZB + H - 0.013
P = dict(p4=0.9, p3=2.1, p2=4.0, p5=0.3, q2=1.2, q3=3.3)   # fixed phases = deterministic hand-thrown shape


def r_out(z):
    s = min(max(z / H, 0.0), 1.0)
    return R_BASE + (R_RIM - R_BASE) * s ** 1.15 + 0.0015 * math.sin(math.pi * s)


def sstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def warp(r, th, z):
    """Hand-thrown irregularity: low-order radial harmonics growing toward the rim, wavy rim height, slight lean."""
    s = min(max(z / H, 0.0), 1.05)
    amp = 0.25 + 0.75 * s
    f = (0.030 * math.cos(4 * th + P["p4"]) + 0.017 * math.cos(3 * th + P["p3"])
         + 0.013 * math.cos(2 * th + P["p2"]) + 0.007 * math.cos(5 * th + P["p5"]))
    r2 = r * (1 + amp * f)
    w = sstep(0.7, 1.0, s)
    dz = w * (0.0026 * math.sin(2 * th + P["q2"]) + 0.0015 * math.sin(3 * th + P["q3"]))
    return Vector((AX + r2 * math.cos(th) + 0.004 * s, AY + r2 * math.sin(th) - 0.002 * s, ZB + z + dz))


def profile():
    pts = [(0.0, 0.0)]
    rf = 0.004
    for i in range(1, 6):
        pts.append(((R_BASE - rf) * i / 5, 0.0))
    for k in range(1, 6):                                   # foot fillet
        a = math.radians(90 * k / 5)
        pts.append((R_BASE - rf + rf * math.sin(a), rf - rf * math.cos(a)))
    for i in range(1, 17):                                  # outer wall
        z = rf + (H - rf) * i / 16
        pts.append((r_out(z), z))
    rm = r_out(H) - WALL / 2                                # rounded rim
    for k in range(1, 9):
        a = math.pi * k / 9
        pts.append((rm + WALL / 2 * math.cos(a), H + WALL / 2 * math.sin(a)))
    zi0 = FLOOR + 0.005
    for i in range(1, 15):                                  # inner wall, going down
        z = H - (H - zi0) * i / 14
        pts.append((r_out(z) - WALL, z))
    cx = r_out(zi0) - WALL - 0.005                          # inner floor fillet
    for k in range(1, 6):
        a = -math.radians(90 * k / 5)
        pts.append((cx + 0.005 * math.cos(a), zi0 + 0.005 * math.sin(a)))
    for i in range(1, 5):
        pts.append((cx * (1 - i / 4), FLOOR))
    return pts


def body_bm(n=96):
    bm = bmesh.new()
    rows = []
    for (r, z) in profile():
        if r <= 1e-9:
            rows.append([bm.verts.new(warp(0.0, 0.0, z))])
        else:
            rows.append([bm.verts.new(warp(r, 2 * math.pi * i / n, z)) for i in range(n)])
    for a, b in zip(rows, rows[1:]):
        if len(a) == 1:
            for i in range(n):
                bm.faces.new((a[0], b[(i + 1) % n], b[i]))
        elif len(b) == 1:
            for i in range(n):
                bm.faces.new((a[i], a[(i + 1) % n], b[0]))
        else:
            for i in range(n):
                bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def handle_bm():
    """Chunky round donut handle at mid-height on +X, fused to the wall with a small blob (like a pressed-on ring)."""
    Rm, rt, cz = 0.0150, 0.0064, 0.047
    wall_x = warp(r_out(cz), 0.0, cz).x
    cx = wall_x - 0.0035 + Rm + rt
    bm = bmesh.new()
    nu, nv = 44, 16
    rows = []
    for i in range(nu):
        ph = 2 * math.pi * i / nu
        rr = rt * (1 + 0.10 * math.sin(2 * ph + 0.7) + 0.05 * math.sin(3 * ph))
        n = Vector((math.cos(ph), 0, math.sin(ph) * 1.10))
        c = Vector((cx + Rm * math.cos(ph), 0.0, ZB + cz + Rm * 1.10 * math.sin(ph)))
        row = []
        for j in range(nv):
            ps = 2 * math.pi * j / nv
            off = (n.normalized() * math.cos(ps) + Vector((0, 1, 0)) * math.sin(ps)) * rr
            row.append(bm.verts.new(c + off))
        rows.append(row)
    for i in range(nu):
        a, b = rows[i], rows[(i + 1) % nu]
        for j in range(nv):
            bm.faces.new((a[j], a[(j + 1) % nv], b[(j + 1) % nv], b[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # twist a few degrees about Z so it is not perfectly in-plane
    bmesh.ops.rotate(bm, cent=(wall_x, 0, ZB + cz), matrix=Matrix.Rotation(math.radians(2.0), 3, "Z"),
                     verts=bm.verts)
    # blob at the tangent point
    bl = bmesh.new()
    bmesh.ops.create_uvsphere(bl, u_segments=20, v_segments=12, radius=0.0062)
    bmesh.ops.scale(bl, vec=(1.0, 0.95, 1.25), verts=bl.verts)
    bmesh.ops.translate(bl, vec=(wall_x + 0.0003, 0.0, ZB + cz - Rm * 0.2), verts=bl.verts)
    tmp = bpy.data.meshes.new("_t")
    bl.to_mesh(tmp); bl.free(); bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    return bm


def coffee_bm(n=96, nr=9):
    bm = bmesh.new()
    rin = lambda z: r_out(z) - WALL
    rows = [[bm.verts.new((AX + 0.004 * COFFEE_Z / H, AY, COFFEE_Z))]]
    z0 = COFFEE_Z - ZB
    for k in range(1, nr + 1):
        t = k / nr
        row = []
        for i in range(n):
            th = 2 * math.pi * i / n
            rim = warp(rin(z0) + 0.0015, th, z0)
            ctr = Vector((AX + 0.004 * z0 / H, AY - 0.002 * z0 / H, rim.z))
            p = ctr + (rim - ctr) * t
            p.z = COFFEE_Z + 0.0009 * t ** 4 + 0.0003 * math.sin(3 * th) * t     # meniscus
            row.append(bm.verts.new(p))
        rows.append(row)
    for i in range(n):
        bm.faces.new((rows[0][0], rows[1][(i + 1) % n], rows[1][i]))
    for a, b in zip(rows[1:], rows[2:]):
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.z < 0:
            bm.faces.ensure_lookup_table()
            bmesh.ops.reverse_faces(bm, faces=[f])
    return bm


def coaster_bm(n=120):
    bm = bmesh.new()
    top, bot = [], []
    for i in range(n):
        th = 2 * math.pi * i / n
        R = COAST_R * (1 + 0.022 * math.cos(2 * th + 1.1) + 0.017 * math.cos(3 * th + 0.4)
                       + 0.010 * math.cos(5 * th + 2.0) + 0.006 * math.cos(7 * th + 0.9))
        T = COAST_T * (1 + 0.04 * math.cos(th - 0.5))
        bot.append(bm.verts.new((R * math.cos(th), R * math.sin(th), 0.0)))
        top.append(bm.verts.new((R * math.cos(th), R * math.sin(th), T)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    bm.faces.new(top)
    bm.faces.new(list(reversed(bot)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ring = [e for e in bm.edges if (all(v in top for v in e.verts) or all(v in bot for v in e.verts))]
    bmesh.ops.bevel(bm, geom=ring, offset=0.0013, segments=2, affect="EDGES", clamp_overlap=True)
    return bm


def build():
    col = C.new_scene(NAME)
    m_glaze = MM.speckled_glaze("Mug_SpeckledGlaze", COFFEE_Z, (AX, AY))
    m_crema = MM.crema("Mug_Crema")
    m_wood = MM.wood_slice("Mug_Coaster_Wood")
    m_bark = MM.bark("Mug_Coaster_Bark", COAST_T)

    # --- mug: body + handle + blob fused by a voxel remesh (a pressed-on handle, no hard intersection line),
    #          then decimated to the web budget
    bm = body_bm()
    tmp = bpy.data.meshes.new("_t")
    hb = handle_bm(); hb.to_mesh(tmp); hb.free(); bm.from_mesh(tmp)
    bpy.data.meshes.remove(tmp)
    mug = C.mesh_obj("Mug_Body", bm, col)
    bpy.context.view_layer.objects.active = mug
    rm = mug.modifiers.new("Remesh", "REMESH")
    rm.mode, rm.voxel_size, rm.use_smooth_shade = "VOXEL", 0.0011, True
    bpy.ops.object.modifier_apply(modifier="Remesh")
    quads = len(mug.data.polygons)
    dm = mug.modifiers.new("Decimate", "DECIMATE")
    dm.ratio = min(1.0, TARGET_TRIS / (2.0 * quads))
    bpy.ops.object.modifier_apply(modifier="Decimate")
    for p in mug.data.polygons:
        p.use_smooth = True
    mug.data.materials.append(m_glaze)
    print(f"[mug] remesh quads={quads} -> tris={sum(len(p.vertices) - 2 for p in mug.data.polygons)}")

    cof = C.mesh_obj("Mug_Coffee", coffee_bm(), col, smooth=True)
    cof.data.materials.append(m_crema)

    cs = C.mesh_obj("Mug_Coaster", coaster_bm(), col)
    cs.data.materials.append(m_wood)
    cs.data.materials.append(m_bark)
    for p in cs.data.polygons:
        p.material_index = 0 if abs(p.normal.z) > 0.6 else 1
    C.shade_auto(cs, 38)
    return col, mug, cof, cs


def main():
    col, mug, cof, cs = build()
    bpy.context.scene["preview_views"] = json.dumps({
        # name: target xyz, azimuth, elevation, distance, lens
        "ref":     [0.0, 0.0, 0.050, -18, 28, 0.36, 85],      # like the reference photo (3/4, slightly above)
        "inside":  [0.0, 0.0, 0.080, -10, 62, 0.30, 85],
        "handle":  [0.055, 0.0, 0.058, 55, 14, 0.26, 85],
        "coaster": [0.0, -0.040, 0.012, -8, 16, 0.24, 85],
    })
    bpy.ops.wm.save_as_mainfile(filepath=str(C.comp_dir(NAME) / "export" / f"{NAME}_source.blend"),
                                compress=True)
    tex = C.comp_dir(NAME) / "export" / "tex"
    M.bake_to_images([mug], str(tex), px=TEX_PX, prefix="mug_body")
    M.bake_to_images([cof], str(tex), px=512, prefix="mug_coffee")
    M.bake_to_images([cs], str(tex), px=max(1024, TEX_PX * 3 // 4), prefix="mug_coaster")
    C.export(NAME, col)


if __name__ == "__main__":
    main()
