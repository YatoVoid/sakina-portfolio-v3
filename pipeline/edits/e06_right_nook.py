"""Edit #6 (round 3, user 2026-10-31): right nook like Felix ref F.

- Lounge chair replaces the green club armchair: moulded walnut-veneer plywood shells (seat, back, headrest)
  holding puffy brown leather cushions, leather arm pads on wooden arms, black five-star swivel base.
  Same spot by the right wall, turned toward the desk.
- Painted side table replaces the walnut one: worn blue-grey paint with bare wood showing through on chips,
  one drawer with a wooden knob, tapered square legs; a framed photo and a stack of three cloth books on top.
- Floor lamp: white linen drum shade that glows (translucent), slimmer brass pole, a little taller.
- Framed picture (dark frame, white mat, aged landscape print) on the right wall above the chair.
"""
import bpy, bmesh, math, os, importlib.util
from mathutils import Vector, Matrix

_spec = importlib.util.spec_from_file_location("e04", os.path.join(os.path.dirname(os.path.abspath(__file__)), "e04_left_zone.py"))
e04 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(e04)
wood_mat, simple_mat, aged_photo, _srgb, _node, _lin = e04.wood_mat, e04.simple_mat, e04.aged_photo, e04._srgb, e04._node, e04._lin

CHAIR_AT, CHAIR_YAW = (3.04, 1.38), -53.0          # faces toward the desk
TABLE = (2.70, 3.06, 2.07, 2.43, 0.58)             # x0, x1, y0, y1, height (against the back wall)
RIGHT_WALL = 3.60


# ----------------------------------------------------------------------------------------------- materials
def leather_mat():
    m = bpy.data.materials.get("LoungeLeather")
    if m:
        return m
    m = bpy.data.materials.new("LoungeLeather"); m.use_nodes = True; nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    tc = _node(nt, "ShaderNodeTexCoord")
    big = _node(nt, "ShaderNodeTexNoise", in_Scale=7.0, in_Detail=4.0, in_Roughness=0.55)
    _lin(nt, tc.outputs["Object"], big.inputs["Vector"])
    c = _node(nt, "ShaderNodeMix", data_type='RGBA'); c.inputs[6].default_value = (*_srgb("4e2a16"), 1)
    c.inputs[7].default_value = (*_srgb("7d4728"), 1)
    r = _node(nt, "ShaderNodeMapRange", in_From_Min=0.35, in_From_Max=0.7)
    _lin(nt, big.outputs["Fac"], r.inputs["Value"]); _lin(nt, r.outputs["Result"], c.inputs[0])
    _lin(nt, c.outputs[2], bs.inputs["Base Color"])
    grain = _node(nt, "ShaderNodeTexVoronoi", in_Scale=420.0)
    _lin(nt, tc.outputs["Object"], grain.inputs["Vector"])
    wr = _node(nt, "ShaderNodeTexNoise", in_Scale=18.0, in_Detail=6.0, in_Distortion=1.5)
    _lin(nt, tc.outputs["Object"], wr.inputs["Vector"])
    h = _node(nt, "ShaderNodeMath", operation='MULTIPLY_ADD'); h.inputs[1].default_value = 0.35
    _lin(nt, grain.outputs["Distance"], h.inputs[0]); _lin(nt, wr.outputs["Fac"], h.inputs[2])
    bp = _node(nt, "ShaderNodeBump", in_Strength=0.18, in_Distance=0.002)
    _lin(nt, h.outputs[0], bp.inputs["Height"]); _lin(nt, bp.outputs["Normal"], bs.inputs["Normal"])
    rr = _node(nt, "ShaderNodeMapRange", in_To_Min=0.32, in_To_Max=0.55)
    _lin(nt, wr.outputs["Fac"], rr.inputs["Value"]); _lin(nt, rr.outputs["Result"], bs.inputs["Roughness"])
    bs.inputs["Coat Weight"].default_value = 0.25; bs.inputs["Coat Roughness"].default_value = 0.3
    return m


def painted_mat():
    """Worn blue-grey paint; chips and rubbed patches reveal the wood underneath."""
    m = bpy.data.materials.get("PaintedTable")
    if m:
        return m
    m = bpy.data.materials.new("PaintedTable"); m.use_nodes = True; nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    tc = _node(nt, "ShaderNodeTexCoord")
    pv = _node(nt, "ShaderNodeTexNoise", in_Scale=9.0, in_Detail=3.0)
    _lin(nt, tc.outputs["Object"], pv.inputs["Vector"])
    paint = _node(nt, "ShaderNodeMix", data_type='RGBA'); paint.inputs[6].default_value = (*_srgb("5a6a70"), 1)
    paint.inputs[7].default_value = (*_srgb("72838a"), 1)
    _lin(nt, pv.outputs["Fac"], paint.inputs[0])
    chips = _node(nt, "ShaderNodeTexNoise", in_Scale=26.0, in_Detail=8.0, in_Roughness=0.7)
    _lin(nt, tc.outputs["Object"], chips.inputs["Vector"])
    mask = _node(nt, "ShaderNodeMapRange", in_From_Min=0.66, in_From_Max=0.70)
    _lin(nt, chips.outputs["Fac"], mask.inputs["Value"])
    col = _node(nt, "ShaderNodeMix", data_type='RGBA'); col.inputs[7].default_value = (*_srgb("6e4a2c"), 1)
    _lin(nt, mask.outputs["Result"], col.inputs[0]); _lin(nt, paint.outputs[2], col.inputs[6])
    _lin(nt, col.outputs[2], bs.inputs["Base Color"])
    rr = _node(nt, "ShaderNodeMapRange", in_To_Min=0.62, in_To_Max=0.45)
    _lin(nt, mask.outputs["Result"], rr.inputs["Value"]); _lin(nt, rr.outputs["Result"], bs.inputs["Roughness"])
    bp = _node(nt, "ShaderNodeBump", in_Strength=0.25, in_Distance=0.0006, invert=True)
    _lin(nt, mask.outputs["Result"], bp.inputs["Height"]); _lin(nt, bp.outputs["Normal"], bs.inputs["Normal"])
    return m


def linen_shade_mat():
    m = bpy.data.materials.get("ShadeLinen")
    if m:
        return m
    m = bpy.data.materials.new("ShadeLinen"); m.use_nodes = True; nt = m.node_tree
    out = nt.nodes["Material Output"]; bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*_srgb("efe7d6"), 1); bs.inputs["Roughness"].default_value = 0.9
    tr = _node(nt, "ShaderNodeBsdfTranslucent"); tr.inputs["Color"].default_value = (*_srgb("f3dcb4"), 1)
    mx = _node(nt, "ShaderNodeMixShader"); mx.inputs[0].default_value = 0.45
    _lin(nt, bs.outputs[0], mx.inputs[1]); _lin(nt, tr.outputs[0], mx.inputs[2]); _lin(nt, mx.outputs[0], out.inputs["Surface"])
    return m


# ----------------------------------------------------------------------------------------------- builders
class Parts:
    def __init__(self, coll, root):
        self.coll, self.root = coll, root

    def _obj(self, name, me, mat, local):
        o = bpy.data.objects.new(name, me); self.coll.objects.link(o); o.data.materials.append(mat)
        o.parent = self.root; o.matrix_parent_inverse = Matrix.Identity(4); o.matrix_basis = local
        return o

    def rbox(self, name, size, centre, mat, tilt=0.0, bevel=0.0, seg=3, open_face=None, shell=0.0, yaw=0.0):
        me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=size, verts=bm.verts)
        if open_face:
            ax, sg = {"+z": (2, 1), "-y": (1, -1), "+y": (1, 1)}[open_face]
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal[ax] * sg > 0.9], context='FACES')
        bm.to_mesh(me); bm.free()
        local = Matrix.Translation(centre) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(tilt), 4, 'X')
        o = self._obj(name, me, mat, local)
        if shell:
            s = o.modifiers.new("Shell", 'SOLIDIFY'); s.thickness = shell; s.offset = 1.0
        if bevel:
            b = o.modifiers.new("Bevel", 'BEVEL'); b.width = bevel; b.segments = seg
            if open_face:
                b.limit_method = 'ANGLE'
        for p in me.polygons:
            p.use_smooth = True
        return o

    def box_at(self, name, size, local, mat, bevel=0.0015):
        me = bpy.data.meshes.new(name); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=size, verts=bm.verts); bm.to_mesh(me); bm.free()
        o = self._obj(name, me, mat, local)
        b = o.modifiers.new("Bevel", 'BEVEL'); b.width = bevel; b.segments = 2
        return o

    def mesh(self, name, verts, faces, mat, local=Matrix.Identity(4), smooth=False):
        me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
        if smooth:
            for p in me.polygons:
                p.use_smooth = True
        return self._obj(name, me, mat, local)

    def cyl(self, name, centre, r, depth, mat, verts=24, rot=(0, 0, 0)):
        me = bpy.data.meshes.new(name); bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=depth)
        bm.to_mesh(me); bm.free()
        local = Matrix.Translation(centre) @ Matrix.Rotation(rot[2], 4, 'Z') @ Matrix.Rotation(rot[1], 4, 'Y') @ Matrix.Rotation(rot[0], 4, 'X')
        o = self._obj(name, me, mat, local)
        for p in me.polygons:
            p.use_smooth = len(p.vertices) == 4
        return o


def _lounge_chair(coll):
    D = bpy.data
    old = D.objects.get("Armchair")
    if old:
        for o in list(old.children_recursive):
            D.objects.remove(o, do_unlink=True)
        D.objects.remove(old, do_unlink=True)
    root = D.objects.new("LoungeChair", None); coll.objects.link(root)
    root.location = (*CHAIR_AT, 0.0); root.rotation_euler = (0, 0, math.radians(CHAIR_YAW))
    P = Parts(coll, root)
    leather = leather_mat()
    shell = wood_mat("ShellWalnut", 'X', ("2e170b", "4a2814", "6a3d22"), ring_scale=11.0, coat=0.35)
    metal = simple_mat("ChairBaseBlack", "1d1c1b", 0.38, metal=0.6)
    # seat: tray-shaped plywood shell (open on top) + puffy cushion
    P.rbox("Lounge_SeatShell", (0.66, 0.58, 0.07), (0, 0.0, 0.365), shell, tilt=-7, bevel=0.012, seg=3, open_face="+z", shell=0.014)
    P.rbox("Lounge_SeatCushion", (0.63, 0.57, 0.13), (0, -0.012, 0.425), leather, tilt=-7, bevel=0.056, seg=6)
    # back + headrest: shells open toward the sitter, cushions in front
    P.rbox("Lounge_BackShell", (0.62, 0.07, 0.38), (0, 0.348, 0.637), shell, tilt=-26, bevel=0.012, seg=3, open_face="-y", shell=0.014)
    bc = P.rbox("Lounge_BackCushion", (0.59, 0.13, 0.36), (0, 0.300, 0.660), leather, tilt=-26, bevel=0.055, seg=6)
    P.rbox("Lounge_HeadShell", (0.56, 0.07, 0.21), (0, 0.477, 0.904), shell, tilt=-30, bevel=0.012, seg=3, open_face="-y", shell=0.014)
    P.rbox("Lounge_HeadCushion", (0.53, 0.12, 0.19), (0, 0.431, 0.930), leather, tilt=-30, bevel=0.05, seg=6)
    # stitched pleats: shallow dark seams pressed into the cushion faces (placed in each cushion's own frame)
    seam = simple_mat("LeatherSeam", "1f1008", 0.6)
    sc = bpy.data.objects["Lounge_SeatCushion"]
    for k, zl in enumerate((-0.07, 0.07)):
        P.box_at(f"Lounge_BackPleat_{k}", (0.48, 0.004, 0.010), bc.matrix_basis @ Matrix.Translation((0, -0.0648, zl)), seam)
    for k, yl in enumerate((-0.11, 0.09)):
        P.box_at(f"Lounge_SeatPleat_{k}", (0.50, 0.010, 0.004), sc.matrix_basis @ Matrix.Translation((0, yl, 0.0648)), seam)
    # arms: bent plywood arm + leather pad, cast support
    for s in (-1, 1):
        P.rbox(f"Lounge_ArmWood_{s}", (0.052, 0.50, 0.022), (s * 0.356, 0.03, 0.555), shell, tilt=-4, bevel=0.008, seg=3)
        P.rbox(f"Lounge_ArmPad_{s}", (0.062, 0.40, 0.042), (s * 0.356, 0.0, 0.585), leather, tilt=-4, bevel=0.018, seg=4)
        P.rbox(f"Lounge_ArmPost_{s}", (0.028, 0.07, 0.15), (s * 0.345, 0.14, 0.47), metal, bevel=0.006, seg=2)
    # five-star swivel base
    P.cyl("Lounge_Column", (0, 0.04, 0.19), 0.034, 0.27, metal, verts=24)
    P.cyl("Lounge_ColumnCap", (0, 0.04, 0.33), 0.06, 0.02, metal, verts=24)
    for k in range(5):
        a = math.radians(90 + k * 72)
        dirv = Vector((math.cos(a), math.sin(a), 0))
        c = Vector((0, 0.04, 0.05)) + dirv * 0.18
        verts, faces = [], []
        L, W0, W1 = 0.36, 0.05, 0.03
        for t, w, h in ((0.0, W0, 0.045), (1.0, W1, 0.025)):
            p = Vector((0, 0.04, 0.0)) + dirv * (t * L)
            side = Vector((-dirv.y, dirv.x, 0))
            for sx, z in ((-1, 0.02), (1, 0.02), (1, 0.02 + h), (-1, 0.02 + h)):
                verts.append(tuple(p + side * sx * w / 2 + Vector((0, 0, z - 0.01 * t))))
        faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        lg = P.mesh(f"Lounge_Leg_{k}", verts, faces, metal)
        b = lg.modifiers.new("Bevel", 'BEVEL'); b.width = 0.006; b.segments = 2
        tip = Vector((0, 0.04, 0)) + dirv * (L - 0.02)
        P.cyl(f"Lounge_Glide_{k}", (tip.x, tip.y, 0.012), 0.016, 0.022, metal, verts=16)
    return root


def _side_table(coll):
    D = bpy.data
    for o in list(coll.all_objects):
        if o.name.startswith(("SideTable_", "TableBook_")):
            D.objects.remove(o, do_unlink=True)
    root = D.objects.new("PaintedTable", None); coll.objects.link(root)
    P = Parts(coll, root)
    paint = painted_mat()
    knobw = wood_mat("KnobWood", 'Z', ("6b4326", "8a5a35", "a87449"))
    x0, x1, y0, y1, H = TABLE
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    top_t = 0.024
    P.rbox("PTable_Top", (x1 - x0, y1 - y0, top_t), (cx, cy, H - top_t / 2), paint, bevel=0.005, seg=3)
    # apron with a drawer at the front (-Y, facing the room)
    ah, ai = 0.085, 0.025
    for nm, sz, c in (("Back", (x1 - x0 - 2 * ai, 0.018, ah), (cx, y1 - ai, H - top_t - ah / 2)),
                      ("L", (0.018, y1 - y0 - 2 * ai, ah), (x0 + ai, cy, H - top_t - ah / 2)),
                      ("R", (0.018, y1 - y0 - 2 * ai, ah), (x1 - ai, cy, H - top_t - ah / 2))):
        P.rbox(f"PTable_Apron{nm}", sz, c, paint, bevel=0.002, seg=1)
    P.rbox("PTable_DrawerGap", (x1 - x0 - 2 * ai, 0.016, ah), (cx, y0 + ai + 0.004, H - top_t - ah / 2), simple_mat("KeyholeBlack", "0b0907", 0.8))
    P.rbox("PTable_Drawer", (x1 - x0 - 2 * ai - 0.008, 0.02, ah - 0.008), (cx, y0 + ai - 0.002, H - top_t - ah / 2), paint, bevel=0.003, seg=2)
    P.cyl("PTable_KnobStem", (cx, y0 + ai - 0.018, H - top_t - ah / 2), 0.005, 0.016, knobw, verts=12, rot=(math.pi / 2, 0, 0))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=0.013, location=(0, 0, 0))
    kb = bpy.context.active_object; kb.name = "PTable_Knob"
    for c in kb.users_collection:
        c.objects.unlink(kb)
    coll.objects.link(kb); kb.data.materials.append(knobw); kb.parent = root; kb.location = (cx, y0 + ai - 0.03, H - top_t - ah / 2)
    kb.scale = (1, 0.75, 1)
    for p in kb.data.polygons:
        p.use_smooth = True
    # tapered square legs
    for sx, xx in ((-1, x0 + ai), (1, x1 - ai)):
        for sy, yy in ((-1, y0 + ai), (1, y1 - ai)):
            v = []
            for z, w in ((H - top_t, 0.034), (0.0, 0.022)):
                for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    v.append((xx + dx * w / 2, yy + dy * w / 2, z))
            f = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
            lg = P.mesh(f"PTable_Leg_{sx}_{sy}", v, f, paint)
            b = lg.modifiers.new("Bevel", 'BEVEL'); b.width = 0.003; b.segments = 2
    # books (stack, slightly rotated) + framed photo
    cloth = [simple_mat("BookRed", "7a2219", 0.7), simple_mat("BookNavy", "22304c", 0.7), simple_mat("BookGreen", "2f4d36", 0.7)]
    page = simple_mat("BookPages", "e3d8bf", 0.85)
    z = H
    for k, (w, d, t, yaw, m) in enumerate(((0.21, 0.15, 0.028, 4, cloth[1]), (0.20, 0.14, 0.024, -3, cloth[0]), (0.18, 0.13, 0.03, 7, cloth[2]))):
        c = (cx + 0.04, cy - 0.04, z + t / 2)
        P.rbox(f"PTable_Book_{k}", (w, d, t), c, m, bevel=0.002, seg=1, yaw=yaw)
        P.rbox(f"PTable_BookPages_{k}", (w - 0.012, d - 0.006, t - 0.006), (c[0] + 0.0, c[1] - 0.004, c[2]), page, yaw=yaw)
        z += t
    frame = simple_mat("PhotoFrameSilver", "b9b5ad", 0.3, metal=0.8)
    src = D.materials.get("Photo_06_lake") or D.materials.get("Photo_04_lake")
    fw, fh, fd = 0.13, 0.17, 0.014
    fl = Matrix.Translation((cx - 0.085, cy + 0.06, H + fh / 2 * math.cos(math.radians(12)) + 0.002)) @ \
        Matrix.Rotation(math.radians(20), 4, 'Z') @ Matrix.Rotation(math.radians(-12), 4, 'X')
    fr = P.mesh("PTable_Frame", [], [], frame, local=fl)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(fw, fd, fh), verts=bm.verts)
    bm.to_mesh(fr.data); bm.free()
    b = fr.modifiers.new("Bevel", 'BEVEL'); b.width = 0.004; b.segments = 2
    if src:
        pm = aged_photo(src)
        img = next(n.image for n in src.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image)
        iw, ih = fw - 0.03, fh - 0.03; A = img.size[0] / img.size[1]; a = iw / ih
        (s0, s1), (t0, t1) = ((0.5 - a / A / 2, 0.5 + a / A / 2), (0, 1)) if A > a else ((0, 1), (0.5 - A / a / 2, 0.5 + A / a / 2))
        y = -fd / 2 - 0.0006
        me = bpy.data.meshes.new("PTable_FramePhoto")
        me.from_pydata([(-iw / 2, y, -ih / 2), (iw / 2, y, -ih / 2), (iw / 2, y, ih / 2), (-iw / 2, y, ih / 2)], [], [(0, 1, 2, 3)])
        for nm, uv in (("UVMap", [(s0, t0), (s1, t0), (s1, t1), (s0, t1)]), ("Card", [(0, 0), (1, 0), (1, 1), (0, 1)])):
            l = me.uv_layers.new(name=nm)
            for li, lo in enumerate(me.loops):
                l.data[li].uv = uv[lo.vertex_index]
        po = bpy.data.objects.new("PTable_FramePhoto", me); coll.objects.link(po); po.data.materials.append(pm)
        po.parent = fr
        mat_m = simple_mat("PhotoMat", "ece6d6", 0.85)
        me2 = bpy.data.meshes.new("PTable_FrameMat"); y2 = -fd / 2 - 0.0003
        me2.from_pydata([(-fw / 2 + 0.008, y2, -fh / 2 + 0.008), (fw / 2 - 0.008, y2, -fh / 2 + 0.008), (fw / 2 - 0.008, y2, fh / 2 - 0.008), (-fw / 2 + 0.008, y2, fh / 2 - 0.008)], [], [(0, 1, 2, 3)])
        mo = bpy.data.objects.new("PTable_FrameMat", me2); coll.objects.link(mo); mo.data.materials.append(mat_m); mo.parent = fr


def _floor_lamp():
    D = bpy.data
    lin = linen_shade_mat()
    for n in ("SLamp_Shade", "SLamp_ShadeInner"):
        o = D.objects[n]; o.data.materials.clear(); o.data.materials.append(lin)
    pole = D.objects["SLamp_Pole"]; pole.scale.x *= 0.7; pole.scale.y *= 0.7
    for o in D.objects:
        if o.name.startswith("SLamp_") and o.name not in ("SLamp_Base", "SLamp_BaseTop", "SLamp_Pole") and o.parent is None:
            o.location.z += 0.14
    pole.scale.z *= (1.53 + 0.14) / 1.53
    # pole origin may be centred: keep its foot on the base
    bpy.context.view_layer.update()
    pts = [pole.matrix_world @ Vector(c) for c in pole.bound_box]
    pole.location.z += 0.03 - min(p.z for p in pts)
    L3 = D.objects["L3_FloorLamp"]; L3.location.z += 0.14


def _wall_picture(coll):
    D = bpy.data
    root = D.objects.new("WallPicture", None); coll.objects.link(root)
    P = Parts(coll, root)
    frame = wood_mat("FrameDarkWood", 'Y', ("1c120b", "2a1a10", "3a2617"), ring_scale=14.0, coat=0.2)
    mat_m = simple_mat("PhotoMat", "ece6d6", 0.85)
    W, H, d, fwid = 0.64, 0.48, 0.03, 0.032
    cy, cz, x = 1.40, 1.52, RIGHT_WALL - d / 2
    for nm, sz, c in (("T", (d, W, fwid), (x, cy, cz + H / 2 - fwid / 2)), ("B", (d, W, fwid), (x, cy, cz - H / 2 + fwid / 2)),
                      ("L", (d, fwid, H - 2 * fwid), (x, cy - W / 2 + fwid / 2, cz)), ("R", (d, fwid, H - 2 * fwid), (x, cy + W / 2 - fwid / 2, cz))):
        P.rbox(f"WallPic_Frame{nm}", sz, c, frame, bevel=0.004, seg=2)
    xm = RIGHT_WALL - 0.012
    P.mesh("WallPic_Mat", [(xm, cy - W / 2 + fwid, cz - H / 2 + fwid), (xm, cy + W / 2 - fwid, cz - H / 2 + fwid),
                           (xm, cy + W / 2 - fwid, cz + H / 2 - fwid), (xm, cy - W / 2 + fwid, cz + H / 2 - fwid)], [(0, 3, 2, 1)], mat_m)
    src = D.materials.get("Photo_00_mountains") or D.materials.get("Photo_03_mountains")
    if src:
        img = next(n.image for n in src.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image)
        iw, ih = W - 2 * fwid - 0.10, H - 2 * fwid - 0.10
        A = img.size[0] / img.size[1]; a = iw / ih
        (s0, s1), (t0, t1) = ((0.5 - a / A / 2, 0.5 + a / A / 2), (0, 1)) if A > a else ((0, 1), (0.5 - A / a / 2, 0.5 + A / a / 2))
        xp = xm - 0.0008
        # facing -X: viewer's left is +Y, so u runs from +Y to -Y
        me = bpy.data.meshes.new("WallPic_Print")
        me.from_pydata([(xp, cy + iw / 2, cz - ih / 2), (xp, cy - iw / 2, cz - ih / 2), (xp, cy - iw / 2, cz + ih / 2), (xp, cy + iw / 2, cz + ih / 2)], [], [(0, 1, 2, 3)])
        for nm, uv in (("UVMap", [(s0, t0), (s1, t0), (s1, t1), (s0, t1)]), ("Card", [(0, 0), (1, 0), (1, 1), (0, 1)])):
            l = me.uv_layers.new(name=nm)
            for li, lo in enumerate(me.loops):
                l.data[li].uv = uv[lo.vertex_index]
        o = bpy.data.objects.new("WallPic_Print", me); coll.objects.link(o); o.data.materials.append(aged_photo(src)); o.parent = root


def apply():
    coll = bpy.data.collections["Right_Nook"]
    _lounge_chair(coll)
    _side_table(coll)
    _floor_lamp()
    _wall_picture(coll)
    bpy.context.view_layer.update()
    print("e06 right nook done")
