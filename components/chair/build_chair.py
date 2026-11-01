"""Havalance-style whitewashed slat-back dining chair (reference: refs/ref_havalance_chair.png).

Local frame: origin = centre of the floor footprint, front faces -Y (same as the other components), Z up.
Room placement is described in INTEGRATION.md.

Objects: Chair_Wood (all painted parts), Chair_Seat (upholstered cushion), Chair_Nails (nailhead trim).
Env: TEX_PX (default 2048), SKIP_BAKE=1 to stop after the procedural source.
"""
import json
import math
import os
import random
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, noise

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_lib"))
sys.path.insert(0, str(HERE))
import common as C  # noqa: E402
import materials as M  # noqa: E402
import woodgrain as W  # noqa: E402
from materials_chair import paint_material, fabric_material, nail_material  # noqa: E402

NAME = "chair"
TEX_PX = int(os.environ.get("TEX_PX", "2048"))
rnd = random.Random(31)

# ------------------------------------------------------------------ dimensions (m)
HX = 0.205            # leg / post centre x
FY = -0.215           # front leg centre y
APR_Z0, APR_Z1 = 0.340, 0.405      # seat apron
BLK_Z0 = 0.325        # bottom of the square block on the front legs
BLK = 0.058           # block section
APR_T = 0.024
SEAT_TOP = APR_Z1     # cushion sits on the apron
POST_TOP = 0.935
MID_Z0, MID_Z1 = 0.520, 0.585
CREST_Z0, CREST_ZE, CREST_ZC = 0.875, 0.930, 0.963   # bottom, top at the posts, top at the centre

# rear leg + back post: one continuous curved piece, (y, z) control points; foot sweeps back, post leans back
POST_PTS = [(0.302, 0.0), (0.262, 0.17), (0.226, 0.34), (0.209, 0.47), (0.216, 0.62), (0.233, 0.78),
            (0.250, 0.935)]


# ------------------------------------------------------------------ small geometry helpers
def catmull(pts, per=14):
    P = [pts[0]] + pts + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            t = k / per
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(pts[-1])
    return out


_POST_PATH = catmull([Vector((0, y, z)) for y, z in POST_PTS], 16)


def yp(z):
    """y of the post centre line at height z."""
    p = _POST_PATH
    if z <= p[0].z:
        return p[0].y
    for a, b in zip(p[:-1], p[1:]):
        if a.z <= z <= b.z:
            t = (z - a.z) / max(b.z - a.z, 1e-9)
            return a.y + (b.y - a.y) * t
    return p[-1].y


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def box_bm(size, center, bevel=0.002, shear=None):
    """Box with chamfered edges. shear(z)->dy lets slats / rails lean with the back."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0] + center[0], v.co.y * size[1] + center[1], v.co.z * size[2] + center[2]))
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=2, affect="EDGES", profile=0.5,
                        clamp_overlap=True)
    if shear:
        for v in bm.verts:
            v.co.y += shear(v.co.z)
    return bm


def sweep_bm(path, sec, ring_c=0.22):
    """Rounded-rectangle section swept along a path (lateral axis = X)."""
    bm = bmesh.new()
    rings = []
    X = Vector((1, 0, 0))
    for i, p in enumerate(path):
        a, b = path[max(i - 1, 0)], path[min(i + 1, len(path) - 1)]
        T = (b - a).normalized()
        N = X.cross(T).normalized()
        w, t = sec(p.z)
        hw, ht = w / 2, t / 2
        c = min(hw, ht) * ring_c * 2
        pts = [(-hw + c, -ht), (hw - c, -ht), (hw, -ht + c), (hw, ht - c), (hw - c, ht), (-hw + c, ht),
               (-hw, ht - c), (-hw, -ht + c)]
        rings.append([bm.verts.new(p + X * u + N * v) for u, v in pts])
    for r0, r1 in zip(rings[:-1], rings[1:]):
        n = len(r0)
        for k in range(n):
            bm.faces.new((r0[k], r0[(k + 1) % n], r1[(k + 1) % n], r1[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


# turned front leg profile (z, radius): double bead foot, long taper, vase, collar rings, cove into the block
LEG_PROFILE = [
    (0.000, 0.0150), (0.004, 0.0178), (0.011, 0.0188), (0.017, 0.0172), (0.021, 0.0165), (0.026, 0.0190),
    (0.032, 0.0188), (0.038, 0.0155), (0.050, 0.0160), (0.080, 0.0180), (0.115, 0.0205), (0.148, 0.0235),
    (0.176, 0.0275), (0.200, 0.0305), (0.222, 0.0308), (0.243, 0.0285), (0.261, 0.0230), (0.272, 0.0190),
    (0.279, 0.0170), (0.285, 0.0232), (0.291, 0.0242), (0.297, 0.0215), (0.303, 0.0175), (0.309, 0.0182),
    (0.318, 0.0230), (0.328, 0.0262), (0.340, 0.0268),
]


def lathe_bm(cx, cy, seg=28):
    bm = bmesh.new()
    rings = []
    for z, r in LEG_PROFILE:
        rings.append([bm.verts.new((cx + r * math.cos(2 * math.pi * k / seg),
                                    cy + r * math.sin(2 * math.pi * k / seg), z)) for k in range(seg)])
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(seg):
            bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def crest_bm():
    """Arched crest rail: flat bottom, arched top, leaning with the posts."""
    xs = [-0.205 + 0.41 * i / 28 for i in range(29)]
    top = [CREST_ZE + (CREST_ZC - CREST_ZE) * (1 - (x / 0.205) ** 2) ** 0.8 for x in xs]
    th = 0.024
    bm = bmesh.new()
    # explicit polygon (counter-clockwise seen from -Y): bottom-left, bottom-right, up the right side, over the arch
    poly = [(xs[0], CREST_Z0), (xs[-1], CREST_Z0)] + [(x, z) for x, z in zip(xs[::-1], top[::-1])]
    vs = [bm.verts.new((x, -th / 2, z)) for x, z in poly]
    face = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[face])
    nv = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, th, 0), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.0025, segments=2, affect="EDGES", profile=0.5,
                    clamp_overlap=True)
    for v in bm.verts:
        v.co.y += yp(v.co.z)
    return bm


class Part:
    def __init__(self):
        self.bms = []

    def add(self, bm, axis="Z", seed=None):
        c = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
        W.tag_grain(bm, axis, seed if seed is not None else rnd.randint(0, 99999), c)
        self.bms.append(bm)

    def build(self, name, col, mat, angle=42):
        out = bmesh.new()
        me = bpy.data.meshes.new(name)
        tmp = bpy.data.meshes.new("_t")
        for bm in self.bms:
            bm.to_mesh(tmp)
            bm.free()
            out.from_mesh(tmp)
        out.to_mesh(me)
        out.free()
        bpy.data.meshes.remove(tmp)
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        me.materials.append(mat)
        C.shade_auto(ob, angle)
        return ob


# ------------------------------------------------------------------ cushion + nails
CA, CB, CC, CR = 0.232, 0.2215, 0.026, 0.019     # half extents + edge radius
CCY = -0.0335
CCZ = SEAT_TOP + CC
DOME = 0.015


def cushion_bm():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=46, use_grid_fill=True)
    inner = Vector((CA - CR, CB - CR, CC - CR))
    for v in bm.verts:
        t = [math.copysign(1 - (1 - abs(c)) ** 1.6, c) for c in v.co]
        p = Vector((t[0] * CA, t[1] * CB, t[2] * CC))
        q = Vector((max(-inner.x, min(inner.x, p.x)), max(-inner.y, min(inner.y, p.y)),
                    max(-inner.z, min(inner.z, p.z))))
        d = p - q
        p = q + d.normalized() * CR
        if p.z > 0:
            w = min(1.0, p.z / CC) ** 2
            dome = DOME * max(0.0, 1 - (p.x / CA) ** 2) * max(0.0, 1 - (p.y / CB) ** 2)
            lump = 0.0016 * (noise.noise(Vector((p.x * 18, p.y * 18, 3.0))) + 0.6 * noise.noise(Vector((p.x * 45, p.y * 45, 9.0))))
            p.z += w * (dome + lump)
        v.co = p
    bm.normal_update()
    uv = bm.loops.layers.uv.new("FabricUV")
    zref = CC - CR
    for f in bm.faces:
        n = f.normal
        for l in f.loops:
            p = l.vert.co
            if abs(n.z) > 0.5:
                l[uv].uv = (p.x, p.y)
            elif abs(n.y) >= abs(n.x):
                s = math.copysign(1, n.y)
                l[uv].uv = (p.x, p.y + s * (zref - p.z))
            else:
                s = math.copysign(1, n.x)
                l[uv].uv = (p.x + s * (zref - p.z), p.y)
    for v in bm.verts:
        v.co += Vector((0, CCY, CCZ))
    return bm


def nails_bm():
    bm = bmesh.new()
    zn = SEAT_TOP + CC               # middle of the cushion's vertical edge band
    pitch = 0.0215

    def stud(pos, axis):
        ret = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.0042)
        sc = [1, 1, 1]
        sc["xyz".index(axis)] = 0.5
        for v in ret["verts"]:
            v.co = Vector((v.co.x * sc[0], v.co.y * sc[1], v.co.z * sc[2])) + Vector(pos)

    y_front = CCY - CB
    n = int((2 * (CA - 0.024)) / pitch)
    for i in range(n + 1):
        x = -(CA - 0.024) + i * 2 * (CA - 0.024) / n
        stud((x, y_front, zn), "y")
    m = int((2 * CB - 0.075) / pitch)
    for sx in (-1, 1):
        for i in range(m + 1):
            y = CCY - CB + 0.028 + i * (2 * CB - 0.075) / m
            stud((sx * CA, y, zn), "x")
    return bm


# ------------------------------------------------------------------ build
def build():
    col = C.new_scene(NAME)
    m_paint, m_fab, m_nail = paint_material(), fabric_material(), nail_material()
    P = Part()

    # turned front legs + square blocks
    for sx in (-1, 1):
        P.add(lathe_bm(sx * HX, FY), "Z")
        P.add(box_bm((BLK, BLK, APR_Z1 - BLK_Z0), (sx * HX, FY, (APR_Z1 + BLK_Z0) / 2), bevel=0.0025), "Z")

    # rear legs / back posts (one curved piece)
    def sec(z):
        k = smooth(0.0, 0.30, z)
        return 0.030 + 0.010 * k, 0.026 + 0.008 * k
    for sx in (-1, 1):
        path = [Vector((sx * 0.200, p.y, p.z)) for p in _POST_PATH]
        P.add(sweep_bm(path, sec), "Z")

    zc = (APR_Z0 + APR_Z1) / 2
    zh = APR_Z1 - APR_Z0
    P.add(box_bm((0.40, APR_T, zh), (0, FY - BLK / 2 + APR_T / 2 + 0.008, zc), 0.002), "X")            # front apron
    yb = yp(zc)
    P.add(box_bm((0.40, 0.022, zh), (0, yb, zc), 0.002), "X")                                         # rear apron
    for sx in (-1, 1):
        y0, y1 = FY, yb
        P.add(box_bm((APR_T, y1 - y0, zh), (sx * (HX + BLK / 2 - APR_T / 2 - 0.008), (y0 + y1) / 2, zc), 0.002),
              "Y")                                                                                   # side aprons

    # back: mid rail, slats, crest rail
    zm = (MID_Z0 + MID_Z1) / 2
    P.add(box_bm((0.40, 0.026, MID_Z1 - MID_Z0), (0, yp(zm), zm), 0.0025), "X")
    P.add(crest_bm(), "X")
    n, sw = 5, 0.056
    gap = (0.36 - n * sw) / (n - 1)
    ya, yb2 = yp(MID_Z1 - 0.01), yp(CREST_Z0 + 0.01)
    za, zb = MID_Z1 - 0.01, CREST_Z0 + 0.01
    for i in range(n):
        x = -0.18 + sw / 2 + i * (sw + gap)
        P.add(box_bm((sw, 0.014, zb - za), (x, 0, (za + zb) / 2), 0.0016,
                     shear=lambda z: ya + (yb2 - ya) * (z - za) / (zb - za) + 0.001), "Z")
    wood = P.build("Chair_Wood", col, m_paint)

    # upholstered seat
    seat = C.mesh_obj("Chair_Seat", cushion_bm(), col, smooth=True)
    seat.data.materials.append(m_fab)

    nails = C.mesh_obj("Chair_Nails", nails_bm(), col, smooth=True)
    nails.data.materials.append(m_nail)
    return col, wood, seat, nails


def views():
    return {
        # name: target xyz, azimuth, elevation, distance, lens
        "ref":   [0, 0.02, 0.50, 52, 9, 2.3, 75],
        "ref2":  [0, 0.02, 0.50, -52, 9, 2.3, 75],
        "seat":  [0, -0.03, 0.46, -25, 36, 0.85, 85],
        "leg":   [0.20, -0.22, 0.18, -30, 8, 0.7, 85],
        "crest": [0, 0.24, 0.84, -28, 10, 0.9, 85],
        "nails": [0.15, -0.25, 0.43, -25, 18, 0.5, 100],
    }


def main():
    col, wood, seat, nails = build()
    bpy.context.scene["preview_views"] = json.dumps(views())
    bpy.ops.wm.save_as_mainfile(filepath=str(C.comp_dir(NAME) / "export" / f"{NAME}_source.blend"), compress=True)
    if os.environ.get("SKIP_BAKE"):
        return
    tex = C.comp_dir(NAME) / "export" / "tex"
    M.bake_to_images([wood], str(tex), px=TEX_PX, prefix="chair_wood")
    M.bake_to_images([seat], str(tex), px=TEX_PX, prefix="chair_seat")
    C.export(NAME, col)


if __name__ == "__main__":
    main()
