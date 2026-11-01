"""Center desk — detailed walnut writing table (standalone component).

Reference: the approved room's desk (assets/sakina-v17.blend, collection "Desk", objects Desk_*), kept to its
exact footprint so it can replace it 1:1. No photo reference was supplied for this pass; details below are the
standard construction of a vintage plank-top walnut writing table (inferred, not measured from a photo).

Certain (measured from the room):  top 2.90 x 0.70 m, 40 mm thick, top surface 0.720 m; 5 planks of 140 mm with
  staggered butt joints at the same x positions; legs 64 mm at x = +-1.40, y = +-0.30; one centre drawer
  0.66 m wide x 0.10 m; brass bail pull + keyhole; low side stretchers at 0.175-0.225 m; brass feet.
Inferred (construction detail): inside-tapered legs (62 -> 44 mm), 123 mm aprons, cove moulding under the top,
  cock-beaded drawer opening, drawer box behind the front, square brass cup feet, eased plank edges, 1 mm gaps.

Local frame: origin = floor under the centre of the top, front faces -Y, metres.
Room placement (v17): translate (0.20, 1.65, 0.00), no rotation.
Run: python3 components/desk/build_desk.py   -> export/desk.blend, export/desk.glb, export/desk.stats.json
"""
import json
import math
import random
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_lib"))
import common as C       # noqa: E402
import materials as M    # noqa: E402
import woodgrain as W    # noqa: E402

NAME = "desk"
TEX_PX = int(__import__("os").environ.get("TEX_PX", 2048))
rnd = random.Random(7)

# ---------------------------------------------------------------- dimensions (m)
TOP_W, TOP_D, TOP_T, TOP_Z = 2.90, 0.70, 0.040, 0.720
PLANK_W, GAP = 0.140, 0.0012
JOINTS = {0: [-1.00, 0.65], 1: [-0.67, 0.98], 2: [-0.34], 3: [-0.01], 4: [0.32]}  # plank index (front=0)
LEG_X, LEG_Y, LEG_TOP, LEG_FOOT = 1.40, 0.30, 0.062, 0.044
APRON_T, APRON_Z0, APRON_Z1 = 0.022, 0.545, 0.668
DR_W, DR_H, DR_Z0 = 0.660, 0.100, 0.555
STR_Z0, STR_H, STR_T = 0.175, 0.050, 0.032
FOOT_H = 0.024


# ---------------------------------------------------------------- geometry helpers
def bm_box(size, center, bevel=0.0, seg=2, profile=0.5, only_edges=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0] + center[0], v.co.y * size[1] + center[1],
                       v.co.z * size[2] + center[2]))
    if bevel > 0:
        edges = [e for e in bm.edges if (only_edges is None or only_edges(e))]
        bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=seg, affect="EDGES",
                        profile=profile, clamp_overlap=True)
    return bm


def edge_on(e, axis, sign, along):
    """Edge lying on the face at extreme `sign` of `axis` and running along `along`."""
    a, b = e.verts[0].co, e.verts[1].co
    i = "XYZ".index(axis); j = "XYZ".index(along)
    return abs(a[j] - b[j]) > 1e-6 and (a[i] * sign > 0 and b[i] * sign > 0)


class Part:
    def __init__(self):
        self.bms = []

    def add(self, bm, grain_axis="X", seed=None, center=None):
        if grain_axis:
            c = center or sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
            W.tag_grain(bm, grain_axis, seed if seed is not None else rnd.randint(0, 99999), c)
        self.bms.append(bm)

    def build(self, name, col, mat):
        out = bmesh.new()
        me = bpy.data.meshes.new(name)
        tmp = bpy.data.meshes.new("_t")
        for bm in self.bms:
            bm.to_mesh(tmp)
            bm.free()
            out.from_mesh(tmp)          # appends (keeps custom layers with matching names)
        out.to_mesh(me)
        out.free()
        bpy.data.meshes.remove(tmp)
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        me.materials.append(mat)
        C.shade_auto(ob, 30)
        return ob


def plank_segments(i):
    x0, x1 = -TOP_W / 2, TOP_W / 2
    cuts = [x0] + JOINTS.get(i, []) + [x1]
    return list(zip(cuts[:-1], cuts[1:]))


# ---------------------------------------------------------------- build
def build():
    col = C.new_scene(NAME)
    wood = W.wood_material("Desk_Walnut", coat=0.0, rough=0.50)
    wood_top = W.wood_material("Desk_Walnut_Top", coat=0.0, rough=0.46, wear=0.25, grime=0.25)
    brass = M.pbr("Desk_AgedBrass", ["#5c4520", "#a78446"], rough=0.32, metal=1.0, var=0.12,
                  var_scale=60, rough_var=0.12, bump=0.05, bump_scale=900)
    dark = M.pbr("Desk_DrawerInterior", ["#1d140d", "#2b1e14"], rough=0.8, var=0.05, bump=0.0)

    # --- top: 5 planks, each split at the room's butt joints; eased edges; 1.2 mm gaps
    top = Part()
    z_mid = TOP_Z - TOP_T / 2
    for i in range(5):
        y0 = -TOP_D / 2 + i * PLANK_W + GAP / 2
        y1 = y0 + PLANK_W - GAP
        for (x0, x1) in plank_segments(i):
            ex0 = x0 + (GAP / 2 if x0 > -TOP_W / 2 + 1e-6 else 0)
            ex1 = x1 - (GAP / 2 if x1 < TOP_W / 2 - 1e-6 else 0)
            dz = rnd.uniform(-0.0003, 0.0003)
            bm = bm_box((ex1 - ex0, y1 - y0, TOP_T), ((ex0 + ex1) / 2, (y0 + y1) / 2, z_mid + dz),
                        bevel=0.0018, seg=2)
            # rounded outer edge on the front and back plank, and on the table ends
            outer = []
            for e in bm.edges:
                a, b = e.verts[0].co, e.verts[1].co
                top_or_bottom = abs(a.z - b.z) < 1e-6
                if i == 0 and top_or_bottom and a.y < y0 + 0.003 and b.y < y0 + 0.003 and a.z > z_mid - 0.005:
                    outer.append(e)
            # (the 1.8 mm ease is already on every edge; a larger radius on the front lip reads as a real edge)
            if outer:
                bmesh.ops.bevel(bm, geom=outer, offset=0.004, segments=3, affect="EDGES",
                                clamp_overlap=True)
            # underside is never visible (covered by aprons/moulding): drop it to save texture space
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.9], context="FACES")
            top.add(bm, "X")
    top_ob = top.build("Desk_Top", col, wood_top)

    # --- cove moulding under the top (front + both ends), sits under the overhang
    frame = Part()
    mz0, mz1, mo = TOP_Z - TOP_T - 0.022, TOP_Z - TOP_T + 0.0015, 0.016   # top tucked 1.5 mm into the top
    af = LEG_Y + LEG_TOP / 2 - 0.004          # apron outer face (front: y = -af, ends: x = +-ex)
    ex = LEG_X + LEG_TOP / 2 - 0.004
    yb = TOP_D / 2 - 0.002                    # end mouldings run to the back edge

    def cove(size, center, out_axis, out_sign, grain, mitre):
        bm = bm_box(size, center)
        sel = [e for e in bm.edges
               if all(v.co.z < center[2] - size[2] / 2 + 1e-6 for v in e.verts)
               and all((v.co["XYZ".index(out_axis)] - center["XYZ".index(out_axis)]) * out_sign > 1e-6
                       for v in e.verts)]
        bmesh.ops.bevel(bm, geom=sel, offset=size["XYZ".index(out_axis)] * 0.85, segments=6,
                        profile=0.12, affect="EDGES", clamp_overlap=True)
        for v in bm.verts:
            mitre(v)
        frame.add(bm, grain)

    def mitre_front(v):                       # 45 deg cut at both ends
        if abs(v.co.x) > ex - 1e-4:
            v.co.x = math.copysign(ex + (-af - v.co.y), v.co.x)

    def mitre_end(v):
        if v.co.y < -af + 1e-4:
            v.co.y = -(af + (abs(v.co.x) - ex))

    cove((2 * (ex + mo), mo, mz1 - mz0), (0, -af - mo / 2, (mz0 + mz1) / 2), "Y", -1, "X", mitre_front)
    for s in (-1, 1):
        cove((mo, yb + af + mo, mz1 - mz0), (s * (ex + mo / 2), (yb - af - mo) / 2, (mz0 + mz1) / 2),
             "X", s, "Y", mitre_end)

    # --- legs: square, tapered on the two inside faces, chamfered arrises
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * LEG_X, sy * LEG_Y
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            for v in bm.verts:
                t = v.co.z + 0.5                                     # 0 at foot, 1 at top
                w = LEG_FOOT + (LEG_TOP - LEG_FOOT) * t
                # outside faces stay plumb, inside faces taper
                x = cx + (sx * LEG_TOP / 2 if v.co.x * sx > 0 else sx * (LEG_TOP / 2 - w))
                y = cy + (sy * LEG_TOP / 2 if v.co.y * sy > 0 else sy * (LEG_TOP / 2 - w))
                v.co = Vector((x, y, FOOT_H - 0.004 + t * (APRON_Z1 - FOOT_H + 0.004)))
            vert_edges = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.1]
            bmesh.ops.bevel(bm, geom=vert_edges, offset=0.003, segments=1, affect="EDGES")
            bmesh.ops.bevel(bm, geom=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-6],
                            offset=0.0012, segments=1, affect="EDGES", clamp_overlap=True)
            frame.add(bm, "Z")

    # --- aprons (front with drawer opening, back, sides)
    fy = -LEG_Y - LEG_TOP / 2 + APRON_T / 2 + 0.004            # set 4 mm back from the leg face
    ah = APRON_Z1 - APRON_Z0
    ax0, ax1 = -LEG_X + LEG_TOP / 2, LEG_X - LEG_TOP / 2
    for (x0, x1) in ((ax0, -DR_W / 2), (DR_W / 2, ax1)):
        frame.add(bm_box((x1 - x0, APRON_T, ah), ((x0 + x1) / 2, fy, (APRON_Z0 + APRON_Z1) / 2),
                         bevel=0.001, seg=1), "X")
    dz1 = DR_Z0 + DR_H
    frame.add(bm_box((DR_W, APRON_T, APRON_Z1 - dz1), (0, fy, (dz1 + APRON_Z1) / 2), bevel=0.001, seg=1), "X")
    frame.add(bm_box((DR_W, APRON_T, DR_Z0 - APRON_Z0), (0, fy, (APRON_Z0 + DR_Z0) / 2), bevel=0.001, seg=1), "X")
    frame.add(bm_box((ax1 - ax0, APRON_T, ah), (0, LEG_Y + LEG_TOP / 2 - APRON_T / 2 - 0.004,
                                                (APRON_Z0 + APRON_Z1) / 2), bevel=0.001, seg=1), "X")
    for sx in (-1, 1):
        ay0, ay1 = -LEG_Y + LEG_TOP / 2, LEG_Y - LEG_TOP / 2
        frame.add(bm_box((APRON_T, ay1 - ay0, ah), (sx * (LEG_X + LEG_TOP / 2 - APRON_T / 2 - 0.004), 0,
                                                    (APRON_Z0 + APRON_Z1) / 2), bevel=0.001, seg=1), "Y")
        # low side stretcher (room: z 0.175-0.225)
        frame.add(bm_box((STR_T, 2 * LEG_Y - LEG_TOP * 0.8, STR_H),
                         (sx * LEG_X, 0, STR_Z0 + STR_H / 2), bevel=0.003, seg=2), "Y")

    # --- cock bead around the drawer opening (half-round 5 mm, proud of the apron)
    bead = 0.005
    by = fy - APRON_T / 2 - bead / 2 + 0.0015
    for (sz, cz) in ((DR_W + 2 * bead, DR_Z0 - bead / 2), (DR_W + 2 * bead, dz1 + bead / 2)):
        frame.add(bm_box((sz, bead, bead), (0, by, cz), bevel=bead * 0.49, seg=4), "X")
    for sx in (-1, 1):
        frame.add(bm_box((bead, bead, DR_H), (sx * (DR_W / 2 + bead / 2), by, DR_Z0 + DR_H / 2),
                         bevel=bead * 0.49, seg=4), "Z")

    # --- drawer front: slightly recessed, ovolo edge; drawer box behind it
    df_y = fy - APRON_T / 2 + 0.010
    dfront = bm_box((DR_W - 0.004, 0.020, DR_H - 0.004), (0, df_y, DR_Z0 + DR_H / 2),
                    bevel=0.003, seg=3)
    frame.add(dfront, "X")
    frame_ob = frame.build("Desk_Frame", col, wood)

    inner = Part()
    dy0, dy1 = df_y + 0.010, df_y + 0.010 + 0.50
    for sx in (-1, 1):   # drawer sides
        inner.add(bm_box((0.012, dy1 - dy0, DR_H - 0.020), (sx * (DR_W / 2 - 0.012), (dy0 + dy1) / 2,
                                                            DR_Z0 + DR_H / 2 - 0.004)), None)
    inner.add(bm_box((DR_W - 0.02, dy1 - dy0, 0.006), (0, (dy0 + dy1) / 2, DR_Z0 + 0.008)), None)
    inner.add(bm_box((DR_W - 0.004, 0.24, 0.006), (0, fy + 0.13, APRON_Z1 - 0.004)), None)  # dust board
    inner_ob = inner.build("Desk_DrawerBox", col, dark)
    C.smart_uv(inner_ob)

    # --- brass: bail pull, keyhole escutcheon, cup feet, screws
    hw = Part()
    face_y = df_y - 0.010
    pz = DR_Z0 + DR_H * 0.42
    for sx in (-1, 1):
        x = sx * 0.050
        hw.add(_disc(0.0085, 0.0025, (x, face_y - 0.00125, pz), "Y"), None)      # rosette
        hw.add(_disc(0.0040, 0.0060, (x, face_y - 0.0050, pz), "Y"), None)       # post
    hw.add(_bail(0.050, 0.020, 0.0028, (0, face_y - 0.008, pz)), None)
    kz = DR_Z0 + DR_H * 0.78
    hw.add(_escutcheon((0, face_y - 0.0008, kz)), None)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * LEG_X, sy * LEG_Y
            # foot centred on the tapered leg's foot
            fx = cx + sx * (LEG_TOP / 2 - LEG_FOOT / 2)
            fyy = cy + sy * (LEG_TOP / 2 - LEG_FOOT / 2)
            cup = bm_box((LEG_FOOT + 0.004, LEG_FOOT + 0.004, FOOT_H), (fx, fyy, FOOT_H / 2),
                         bevel=0.0025, seg=2)
            hw.add(cup, None)
            hw.add(bm_box((LEG_FOOT + 0.007, LEG_FOOT + 0.007, 0.004), (fx, fyy, FOOT_H - 0.002),
                          bevel=0.0012, seg=2), None)   # collar
    hw_ob = hw.build("Desk_Brass", col, brass)
    C.smart_uv(hw_ob)

    return col, [top_ob, frame_ob, inner_ob, hw_ob]


def _disc(r, h, loc, axis):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r, radius2=r, depth=h)
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges if e.is_boundary or len(e.link_faces) == 2 and
                              abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-7 and e.verts[0].co.z < 0],
                    offset=min(r, h) * 0.3, segments=2, affect="EDGES", clamp_overlap=True)
    R = Matrix.Rotation(math.radians(90), 4, "X") if axis == "Y" else Matrix.Identity(4)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(loc) @ R, verts=bm.verts)
    return bm


def _bail(half_w, drop, r, loc):
    """Swan-neck style bail: a bent round bar hanging from the two posts."""
    bm = bmesh.new()
    pts = []
    n = 28
    for i in range(n + 1):
        t = i / n
        x = -half_w + 2 * half_w * t
        z = -drop * (1 - (2 * t - 1) ** 4) ** 0.5
        pts.append(Vector((x, 0, z)))
    prev = None
    rings = []
    for i, p in enumerate(pts):
        tan = (pts[min(i + 1, n)] - pts[max(i - 1, 0)]).normalized()
        side = tan.cross(Vector((0, 1, 0))).normalized()
        up = Vector((0, 1, 0))
        ring = [bm.verts.new(p + (side * math.cos(a) + up * math.sin(a)) * r)
                for a in (k * 2 * math.pi / 10 for k in range(10))]
        if prev:
            for k in range(10):
                bm.faces.new((prev[k], prev[(k + 1) % 10], ring[(k + 1) % 10], ring[k]))
        prev = ring
        rings.append(ring)
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    return bm


def _escutcheon(loc):
    """Keyhole plate: thin oval with a keyhole-shaped dark recess (recess modelled as a small inset)."""
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=28, radius=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * 0.010, 0, v.co.y * 0.014))
    f = [f for f in bm.faces][0]
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=Vector((0, -0.0016, 0)), verts=nv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    front = max(bm.faces, key=lambda fc: -fc.calc_center_median().y if len(fc.verts) > 4 else -1)
    ins = bmesh.ops.inset_region(bm, faces=[front], thickness=0.0016, depth=0.0004)
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    return bm


def keyhole_slot(col, loc):
    mat = M.pbr("Desk_Keyhole", "#060403", rough=0.9, var=0.0, bump=0.0)
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=16, radius=0.0022)
    for v in bm.verts:
        v.co = Vector((v.co.x, 0, v.co.y + 0.002))
    for x, z in ((-0.0011, 0.0015), (0.0011, 0.0015), (0.0008, -0.004), (-0.0008, -0.004)):
        pass
    slot = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
    for v in slot["verts"]:
        v.co = Vector((v.co.x * 0.0011, 0, v.co.y * 0.003 - 0.001))
    for v in bm.verts:
        v.co = Matrix.Rotation(0, 3, "X") @ v.co
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.y > 0:
            f.normal_flip()
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    ob = C.mesh_obj("Desk_KeyholeSlot", bm, col)
    ob.data.materials.append(mat)
    return ob


def main():
    col, objs = build()
    # keyhole slot just in front of the escutcheon recess
    df_y = (-LEG_Y - LEG_TOP / 2 + APRON_T / 2 + 0.004) - APRON_T / 2 + 0.010
    keyhole_slot(col, (0, df_y - 0.010 - 0.0021, DR_Z0 + DR_H * 0.78))
    _preview_views()
    # procedural source (room integration bakes from this; previews render it)
    bpy.ops.wm.save_as_mainfile(filepath=str(C.comp_dir(NAME) / "export" / f"{NAME}_source.blend"),
                                compress=True)
    tex = C.comp_dir(NAME) / "export" / "tex"
    M.bake_to_images([objs[0]], str(tex), px=TEX_PX, prefix="desk_top")
    M.bake_to_images([objs[1]], str(tex), px=TEX_PX, prefix="desk_frame")
    M.bake_to_images([objs[2], objs[3]], str(tex), px=max(512, TEX_PX // 4), prefix="desk")
    C.export(NAME, col)


def _preview_views():
    scn = bpy.context.scene
    scn["preview_views"] = json.dumps({
        # name: target xyz, azimuth, elevation, distance, lens
        "drawer":  [0.0, -0.34, 0.60, -14, 10, 0.55, 85],
        "corner":  [-1.40, -0.30, 0.55, -40, 18, 0.95, 70],
        "topgrain": [-0.45, -0.20, 0.72, -10, 32, 0.55, 90],
        "foot":    [-1.40, -0.30, 0.06, -35, 12, 0.42, 85],
    })


if __name__ == "__main__":
    main()
