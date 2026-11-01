"""Edit #2 (user request 2026-11-01): replace the armchair against the right wall with the oversized
English-style club chair from the Attic-Ease reference photo (attic-ease.com, "Oversized English-Style Club Chair").

Reference analysis (see DECISIONS.md for what is certain vs. inferred):
  certain  - one-piece tight-seat/loose-cushion club chair, big rolled arms with round scroll fronts, loose box seat
             cushion and pillowy loose back cushion, welted (piped) seams, antique-brass nailhead trim,
             crocodile-embossed honey-brown leather with a web of light tan veins.
  inferred - real dimensions (photo has no scale; "oversized" club chair -> ~1.02 x 0.96 x 0.92 m), exact nailhead
             rows (rows follow scroll rim, front edge of each arm, bottom rail front/sides, top + sides of back).

Placement: same footprint as the old armchair, back against the right wall (x = 3.58 baseboard), centred at y = 1.40,
facing the room (-x). The old chair (all objects named Arm_*, including its pillow) is removed.
All parts go into the Right_Nook collection, so only that bake group has to be re-baked.
Leather is fully procedural in chair-local coordinates (no UVs needed; the bake unwraps a separate Lightmap UV).
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

# ---------------------------------------------------------------- dimensions (metres, chair-local: +Y front, +Z up)
BACK_X, CENTRE_Y = 3.575, 1.40            # world position of the chair's back / centre line
HW, HD = 0.51, 0.48                       # half width / half depth of the base
BASE_Z0, BASE_Z1 = 0.07, 0.30             # base (front rail) from feet up to the seat deck
SEAT_HALF = (0.30, 0.29, 0.085)           # seat cushion half extents x, y, z
SEAT_C = (0.0, 0.17, 0.385)
BACK_Y0, BACK_Y1 = -0.48, -0.26           # back shell thickness
BACK_TOP = 0.92
ARM_Y0, ARM_Y1 = -0.30, 0.48
ARM_C = (0.405, 0.56)                     # roll centre (x, z) of the right arm
ARM_R = 0.115
NAIL_R, NAIL_STEP = 0.0098, 0.0270

D = bpy.data


# ================================================================ materials
def _n(nt, typ, x, y, **props):
    n = nt.nodes.new(typ); n.location = (x * 220, y * 180)
    for k, v in props.items():
        setattr(n, k, v)
    return n


def _s(node, ident, outputs=False):
    for s in (node.outputs if outputs else node.inputs):
        if s.identifier == ident:
            return s
    raise KeyError(ident)


def leather_material(name, root, tone=1.0):
    """Crocodile-embossed leather: 3 scales of cracked-cell veins (3D Voronoi distance-to-edge, domain-warped),
    raised ridges (bump), light tan veins over honey-brown cells with per-cell tone variation."""
    m = D.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = _n(nt, "ShaderNodeOutputMaterial", 9, 0)
    bsdf = _n(nt, "ShaderNodeBsdfPrincipled", 8, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tc = _n(nt, "ShaderNodeTexCoord", 0, 0); tc.object = root
    warp_n = _n(nt, "ShaderNodeTexNoise", 1, 1, noise_dimensions='3D')
    warp_n.inputs["Scale"].default_value = 9.0
    warp_n.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], warp_n.inputs["Vector"])
    amp = 0.014
    ma = _n(nt, "ShaderNodeVectorMath", 2, 1, operation='MULTIPLY_ADD')
    nt.links.new(warp_n.outputs["Color"], ma.inputs[0])
    ma.inputs[1].default_value = (amp, amp, amp)
    ma.inputs[2].default_value = (-amp / 2, -amp / 2, -amp / 2)
    warped = _n(nt, "ShaderNodeVectorMath", 3, 1, operation='ADD')
    nt.links.new(tc.outputs["Object"], warped.inputs[0]); nt.links.new(ma.outputs["Vector"], warped.inputs[1])

    def vein(scale, width, weight, x, y):
        v = _n(nt, "ShaderNodeTexVoronoi", x, y, voronoi_dimensions='3D', feature='DISTANCE_TO_EDGE')
        v.inputs["Scale"].default_value = scale
        v.inputs["Randomness"].default_value = 1.0
        nt.links.new(warped.outputs["Vector"], v.inputs["Vector"])
        r = _n(nt, "ShaderNodeMapRange", x + 1, y, interpolation_type='SMOOTHSTEP')
        r.inputs["From Min"].default_value = 0.0; r.inputs["From Max"].default_value = width
        r.inputs["To Min"].default_value = weight; r.inputs["To Max"].default_value = 0.0
        nt.links.new(v.outputs["Distance"], r.inputs["Value"])
        return r.outputs["Result"]

    big = vein(52.0, 0.060, 1.00, 4, 2)
    mid = vein(105.0, 0.075, 0.62, 4, 1)
    fin = vein(210.0, 0.100, 0.30, 4, 0)
    mx1 = _n(nt, "ShaderNodeMath", 6, 1, operation='MAXIMUM'); mx2 = _n(nt, "ShaderNodeMath", 7, 1, operation='MAXIMUM')
    nt.links.new(big, mx1.inputs[0]); nt.links.new(mid, mx1.inputs[1])
    nt.links.new(mx1.outputs[0], mx2.inputs[0]); nt.links.new(fin, mx2.inputs[1])
    veins = mx2.outputs[0]

    # per-cell tone (random per ~2 cm cell) + slow mottling
    cell = _n(nt, "ShaderNodeTexVoronoi", 4, -1, voronoi_dimensions='3D', feature='F1')
    cell.inputs["Scale"].default_value = 52.0
    nt.links.new(warped.outputs["Vector"], cell.inputs["Vector"])
    bw = _n(nt, "ShaderNodeRGBToBW", 5, -1)
    nt.links.new(cell.outputs["Color"], bw.inputs["Color"])
    ct = _n(nt, "ShaderNodeMapRange", 6, -1)
    ct.inputs["From Min"].default_value = 0.15; ct.inputs["From Max"].default_value = 0.85
    nt.links.new(bw.outputs["Val"], ct.inputs["Value"])
    mot = _n(nt, "ShaderNodeTexNoise", 5, -2, noise_dimensions='3D')
    mot.inputs["Scale"].default_value = 3.0; mot.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], mot.inputs["Vector"])

    k = tone
    dark = (0.118 * k, 0.038 * k, 0.012 * k, 1)       # deep cell tone  (photo: sRGB ~ 98,53,26 mid-shadow)
    light = (0.240 * k, 0.088 * k, 0.029 * k, 1)      # lighter cell tone (photo: sRGB ~ 125,74,40)
    vcol = (0.520 * k, 0.265 * k, 0.118 * k, 1)       # raised vein colour (photo: sRGB ~ 170,125,90 lit)
    body = _n(nt, "ShaderNodeMix", 7, -1, data_type='RGBA')
    _s(body, "A_Color").default_value = dark; _s(body, "B_Color").default_value = light
    nt.links.new(ct.outputs["Result"], _s(body, "Factor_Float"))
    mott = _n(nt, "ShaderNodeMix", 8, -1, data_type='RGBA', blend_type='MULTIPLY')
    _s(mott, "Factor_Float").default_value = 0.55
    nt.links.new(_s(body, "Result_Color", True), _s(mott, "A_Color"))
    mr = _n(nt, "ShaderNodeMapRange", 7, -2)
    mr.inputs["To Min"].default_value = 0.60; mr.inputs["To Max"].default_value = 1.30
    nt.links.new(mot.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], _s(mott, "B_Color"))   # float -> colour (grey)
    vmix = _n(nt, "ShaderNodeMix", 9, -1, data_type='RGBA')
    nt.links.new(_s(mott, "Result_Color", True), _s(vmix, "A_Color"))
    _s(vmix, "B_Color").default_value = vcol
    vf = _n(nt, "ShaderNodeMath", 8, -2, operation='MULTIPLY'); vf.inputs[1].default_value = 0.80
    nt.links.new(veins, vf.inputs[0])
    nt.links.new(vf.outputs[0], _s(vmix, "Factor_Float"))
    nt.links.new(_s(vmix, "Result_Color", True), bsdf.inputs["Base Color"])

    # roughness: satin body, glossier raised veins
    rr = _n(nt, "ShaderNodeMapRange", 9, 1)
    rr.inputs["To Min"].default_value = 0.54; rr.inputs["To Max"].default_value = 0.40
    nt.links.new(veins, rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
    bsdf.inputs["Coat Weight"].default_value = 0.05
    bsdf.inputs["Coat Roughness"].default_value = 0.40

    bump = _n(nt, "ShaderNodeBump", 9, 2)
    bump.inputs["Strength"].default_value = 0.55; bump.inputs["Distance"].default_value = 0.0010
    nt.links.new(veins, bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


TEX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                       "assets", "textures", "leather")
SHEET_M = 1.40            # one 1024 px sheet = 1.40 m (about 1.4 mm per pixel, same scale as the reference photo)


def photo_leather_material(name, root, kind, tone=1.0, bump=1.0):
    """Leather from the REAL photo pixels (pipeline/tools/leather_from_photo.py): de-lit, quilted sheets of the
    reference's own veins. Box-projected in chair-local space, so no UVs are needed and nothing repeats on the chair.
    kind = 'crackle' (fine tan crackle, seat/arms/base) or 'croc' (large crocodile scales, back cushion)."""
    m = D.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = _n(nt, "ShaderNodeOutputMaterial", 9, 0)
    bsdf = _n(nt, "ShaderNodeBsdfPrincipled", 8, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tc = _n(nt, "ShaderNodeTexCoord", 0, 0); tc.object = root
    mp = _n(nt, "ShaderNodeMapping", 1, 0)
    k = 1.0 / SHEET_M
    mp.inputs["Scale"].default_value = (k, k, k)
    mp.inputs["Location"].default_value = (0.5, 0.5, 0.5)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    def img(fname, cs, x, y):
        t = _n(nt, "ShaderNodeTexImage", x, y)
        t.image = D.images.load(os.path.join(TEX_DIR, fname), check_existing=True)
        t.image.colorspace_settings.name = cs
        t.projection = 'BOX'; t.projection_blend = 0.18; t.interpolation = 'Cubic'; t.extension = 'REPEAT'
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t
    alb = img(f"leather_{kind}_albedo.png", "sRGB", 3, 1)
    hgt = img(f"leather_{kind}_height.png", "Non-Color", 3, -1)
    tint = _n(nt, "ShaderNodeMix", 5, 1, data_type='RGBA', blend_type='MULTIPLY')
    _s(tint, "Factor_Float").default_value = 1.0
    nt.links.new(alb.outputs["Color"], _s(tint, "A_Color"))
    _s(tint, "B_Color").default_value = (tone, tone, tone, 1)
    nt.links.new(_s(tint, "Result_Color", True), bsdf.inputs["Base Color"])
    rr = _n(nt, "ShaderNodeMapRange", 5, -1)
    rr.inputs["From Min"].default_value = 0.35; rr.inputs["From Max"].default_value = 0.75
    rr.inputs["To Min"].default_value = 0.58; rr.inputs["To Max"].default_value = 0.40     # raised veins a bit glossier
    nt.links.new(hgt.outputs["Color"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
    bsdf.inputs["Coat Weight"].default_value = 0.06
    bsdf.inputs["Coat Roughness"].default_value = 0.35
    bm = _n(nt, "ShaderNodeBump", 6, -2)
    bm.inputs["Strength"].default_value = bump; bm.inputs["Distance"].default_value = 0.0018
    nt.links.new(hgt.outputs["Color"], bm.inputs["Height"])
    nt.links.new(bm.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def metal_material(name, col, rough, metallic):
    m = D.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    return m


# ================================================================ geometry helpers
def _scene_tmp(o):
    bpy.context.scene.collection.objects.link(o)


def _evaluated_mesh(o):
    dg = bpy.context.evaluated_depsgraph_get()
    return D.meshes.new_from_object(o.evaluated_get(dg))


def bevelled_box(half, centre, bevel, seg=4, cuts=0):
    """Box (optionally grid-subdivided so it can be displaced later), bevelled on its 12 original edges."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * 2 * half[0], v.co.y * 2 * half[1], v.co.z * 2 * half[2]))
    if cuts:
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
    me = D.meshes.new("tmp_box"); bm.to_mesh(me); bm.free()
    o = D.objects.new("tmp_box", me); _scene_tmp(o)
    md = o.modifiers.new("Bevel", 'BEVEL')
    md.width = bevel; md.segments = seg; md.limit_method = 'ANGLE'; md.angle_limit = math.radians(60)
    out = _evaluated_mesh(o)
    D.objects.remove(o, do_unlink=True); D.meshes.remove(me)
    out.transform(Matrix.Translation(centre))
    return out


def finish(me, smooth_angle=38):
    """Smooth shading with sharp edges above smooth_angle (Blender 4.1+ model: smooth faces + sharp edges)."""
    bm = bmesh.new(); bm.from_mesh(me)
    for e in bm.edges:
        e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(smooth_angle))
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me); bm.free()
    me.update()


def displace(me, fn):
    bm = bmesh.new(); bm.from_mesh(me)
    for v in bm.verts:
        v.co = fn(v.co.copy())
    bm.to_mesh(me); bm.free()


def poly_tube(name, pts, radius, closed=True, res=3):
    cu = D.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts):
        p.co = (c[0], c[1], c[2], 1.0)
    sp.use_cyclic_u = closed
    cu.bevel_depth = radius; cu.bevel_resolution = res; cu.use_fill_caps = False
    o = D.objects.new(name, cu); _scene_tmp(o)
    me = _evaluated_mesh(o)
    D.objects.remove(o, do_unlink=True); D.curves.remove(cu)
    return me


def rounded_rect(cx, cz, hx, hz, r, y, n=5, y_fn=None):
    """Closed polyline of a rounded rectangle in the XZ plane at depth y (corner radius r)."""
    pts = []
    corners = [(cx + hx - r, cz + hz - r, 0), (cx - hx + r, cz + hz - r, 90),
               (cx - hx + r, cz - hz + r, 180), (cx + hx - r, cz - hz + r, 270)]
    for (px, pz, a0) in corners:
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            x, z = px + r * math.cos(a), pz + r * math.sin(a)
            pts.append((x, y_fn(x, z) if y_fn else y, z))
    return pts


def rounded_rect_xy(cx, cy, hx, hy, r, z, n=5):
    pts = []
    corners = [(cx + hx - r, cy + hy - r, 0), (cx - hx + r, cy + hy - r, 90),
               (cx - hx + r, cy - hy + r, 180), (cx + hx - r, cy - hy + r, 270)]
    for (px, py, a0) in corners:
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((px + r * math.cos(a), py + r * math.sin(a), z))
    return pts


# ---- nailheads
def _dome():
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=NAIL_R)
    for v in bm.verts:
        v.co.z = max(v.co.z, 0.0) * 0.62 - 0.0005
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
    keep = [f for f in bm.faces if sum(v.co.z for v in f.verts) / len(f.verts) > -0.0004]
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in keep], context='FACES')
    return [(tuple(v.co) ) for v in bm.verts], bm


class Nails:
    def __init__(self):
        self.bm = bmesh.new()
        _, tmpl = _dome()
        self.tmpl = tmpl

    def add(self, pos, normal):
        n = Vector(normal).normalized()
        rot = n.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        M = Matrix.Translation(Vector(pos)) @ rot
        vmap = {}
        for f in self.tmpl.faces:
            for v in f.verts:
                if v not in vmap:
                    vmap[v] = self.bm.verts.new(M @ v.co)
            try:
                self.bm.faces.new([vmap[v] for v in f.verts])
            except ValueError:
                pass

    def row(self, a, b, normal, step=NAIL_STEP):
        a, b = Vector(a), Vector(b)
        L = (b - a).length
        n = max(1, int(round(L / step)))
        for i in range(n + 1):
            self.add(a.lerp(b, i / n), normal)

    def ring_y(self, cx, cz, r, y, a0=0, a1=360, step=NAIL_STEP):
        n = max(3, int(round(math.radians(a1 - a0) * r / step)))
        for i in range(n):
            a = math.radians(a0 + (a1 - a0) * i / n)
            self.add((cx + r * math.cos(a), y, cz + r * math.sin(a)), (0, 1, 0))

    def mesh(self):
        me = D.meshes.new("Chair_Nails_mesh"); self.bm.to_mesh(me); self.bm.free(); self.tmpl.free()
        for p in me.polygons:
            p.use_smooth = True
        return me


# ---- arm
def arm_mesh(sign):
    """Rolled arm: profile (panel + roll) extruded front to back, bevelled. sign = +1 right arm, -1 left arm."""
    cx, cz = ARM_C
    prof = [(0.31, BASE_Z0), (0.50, BASE_Z0), (0.50, 0.47)]
    for a in range(-35, 216, 10):
        prof.append((cx + ARM_R * math.cos(math.radians(a)), cz + ARM_R * math.sin(math.radians(a))))
    prof.append((0.31, 0.47))
    bm = bmesh.new()
    back = [bm.verts.new((sign * x, ARM_Y0, z)) for x, z in prof]
    front = [bm.verts.new((sign * x, ARM_Y1, z)) for x, z in prof]
    n = len(prof)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([back[i], back[j], front[j], front[i]])
    bm.faces.new(front); bm.faces.new(back[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = D.meshes.new("tmp_arm"); bm.to_mesh(me); bm.free()
    o = D.objects.new("tmp_arm", me); _scene_tmp(o)
    md = o.modifiers.new("Bevel", 'BEVEL'); md.width = 0.030; md.segments = 4
    md.limit_method = 'ANGLE'; md.angle_limit = math.radians(45)
    out = _evaluated_mesh(o)
    D.objects.remove(o, do_unlink=True); D.meshes.remove(me)
    return out


# ================================================================ the edit
def apply():
    coll = D.collections["Right_Nook"]

    # 1. remove the old armchair (and its pillow)
    old = [o for o in D.objects if o.name.startswith("Arm_")]
    for o in old:
        me = o.data if o.type == 'MESH' else None
        D.objects.remove(o, do_unlink=True)
        if me is not None and me.users == 0:
            D.meshes.remove(me)
    print("e02: removed", len(old), "objects of the old armchair", flush=True)

    # 2. chair root (also the texture-coordinate object, so leather flows across all parts)
    root = D.objects.new("Chair_Root", None); coll.objects.link(root)
    root.empty_display_type = 'PLAIN_AXES'; root.empty_display_size = 0.1
    root.location = (BACK_X - HD, CENTRE_Y, 0.0)          # back of the chair (local y = -HD) lands on BACK_X
    root.rotation_euler = (0.0, 0.0, math.pi / 2)         # local +Y (front) -> world -X (into the room)

    leather = photo_leather_material("Chair_Leather", root, "crackle", 1.0, 1.0)
    croc = photo_leather_material("Chair_LeatherCroc", root, "croc", 1.0, 1.1)
    piping = photo_leather_material("Chair_Piping", root, "crackle", 1.22, 0.7)
    brass = metal_material("Chair_Brass", (0.42, 0.27, 0.10, 1), 0.34, 1.0)
    foot_m = metal_material("Chair_FootWood", (0.045, 0.022, 0.010, 1), 0.42, 0.0)

    def add(name, me, mat, smooth=True):
        if smooth:
            finish(me)
        me.materials.append(mat)
        o = D.objects.new(name, me); coll.objects.link(o)
        o.parent = root
        return o

    # 3. base, back shell, feet
    add("Chair_Base", bevelled_box((HW, HD, (BASE_Z1 - BASE_Z0) / 2), (0, 0, (BASE_Z0 + BASE_Z1) / 2), 0.022), leather)
    zc = (BASE_Z1 + BACK_TOP) / 2
    add("Chair_BackShell", bevelled_box((HW, (BACK_Y1 - BACK_Y0) / 2, (BACK_TOP - BASE_Z1) / 2),
                                        (0, (BACK_Y0 + BACK_Y1) / 2, zc), 0.065, 6), croc)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=0.034, radius2=0.044, depth=BASE_Z0 + 0.01)
            me = D.meshes.new("foot"); bm.to_mesh(me); bm.free()
            me.transform(Matrix.Translation((sx * 0.42, sy * 0.38, (BASE_Z0 + 0.01) / 2)))
            add(f"Chair_Foot_{sx}{sy}", me, foot_m)

    # 4. arms
    add("Chair_Arm_R", arm_mesh(1), leather)
    add("Chair_Arm_L", arm_mesh(-1), leather)

    # 4b. rounded scroll face on each arm front (the reference arms end in a domed round scroll)
    for sx, nm in ((1, "R"), (-1, "L")):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=36, v_segments=14, radius=1.0)
        for v in bm.verts:
            v.co = Vector((v.co.x * 0.099, v.co.y * 0.099, v.co.z * 0.024))
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-6], context='VERTS')
        for f in bm.faces:
            f.smooth = True
        me = D.meshes.new("scroll"); bm.to_mesh(me); bm.free()
        me.transform(Matrix.Rotation(math.radians(-90), 4, 'X'))      # dome axis +Z -> +Y (towards the room)
        me.transform(Matrix.Translation((sx * ARM_C[0], ARM_Y1 + 0.0005, ARM_C[1])))
        add(f"Chair_Scroll_{nm}", me, leather, smooth=False)

    # 5. seat cushion (loose box cushion, crowned) + welts
    sh = SEAT_HALF
    seat = bevelled_box(sh, SEAT_C, 0.050, 5, cuts=10)

    def crown(p):
        nx, ny = (p.x - SEAT_C[0]) / sh[0], (p.y - SEAT_C[1]) / sh[1]
        if p.z > SEAT_C[2] + sh[2] * 0.55:
            p.z += 0.038 * max(0.0, 1 - nx * nx) * max(0.0, 1 - ny * ny)
        return p
    displace(seat, crown)
    add("Chair_SeatCushion", seat, leather)
    for zt in (SEAT_C[2] + sh[2] - 0.020, SEAT_C[2] - sh[2] + 0.020):
        pts = rounded_rect_xy(SEAT_C[0], SEAT_C[1], sh[0] + 0.0015, sh[1] + 0.0015, 0.05, zt)
        add("Chair_SeatWelt", poly_tube("w", pts, 0.0052), piping)

    # 6. back cushion (pillowy, leaning back ~8 deg) + welt
    bh = (0.285, 0.085, 0.235)
    bcush = bevelled_box(bh, (0, 0, 0), 0.080, 6, cuts=14)

    def pillow(p):
        nx, nz = p.x / bh[0], p.z / bh[2]
        b = max(0.0, 1 - nx * nx) * max(0.0, 1 - nz * nz)
        if p.y > 0:
            p.y += 0.105 * (b ** 0.6)
            p.y -= 0.016 * math.exp(-(p.x / 0.030) ** 2) * max(0.0, 1 - nz * nz) * (0.6 + 0.4 * nz)   # centre crease
            p.z -= 0.012 * b * (1 - nz) * 0.5                                                          # soft sag
        else:
            p.y -= 0.014 * b
        return p
    displace(bcush, pillow)
    lean = Matrix.Translation((0, -0.165, 0.600)) @ Matrix.Rotation(math.radians(8), 4, 'X')   # top leans back
    bcush.transform(lean)
    add("Chair_BackCushion", bcush, croc)
    pts = rounded_rect(0, 0, bh[0] + 0.0015, bh[2] + 0.0015, 0.08, 0.0)
    wmesh = poly_tube("bw", pts, 0.0052)
    wmesh.transform(lean)
    add("Chair_BackWelt", wmesh, piping)

    # 7. nailheads (antique brass)
    nl = Nails()
    cx, cz = ARM_C
    yf = ARM_Y1 + 0.0005
    for sx in (-1, 1):
        # C-shaped nail ring on the scroll face (open at the bottom), then two rows down the arm front (as in the photo)
        rr_ = 0.080
        a0, a1 = -25, 205
        nring = int(round(math.radians(a1 - a0) * rr_ / NAIL_STEP))
        for i in range(nring + 1):
            a = math.radians(a0 + (a1 - a0) * i / nring)
            dz = 0.024 * math.sqrt(max(0.0, 1 - (rr_ / 0.099) ** 2))       # height of the scroll dome at this radius
            nl.add((sx * (cx + rr_ * math.cos(a)), yf + dz - 0.002, cz + rr_ * math.sin(a)), (0, 1, 0))
        zlow = cz + rr_ * math.sin(math.radians(a0)) - 0.03
        nl.row((sx * (cx + rr_ * math.cos(math.radians(a0))), yf, zlow), (sx * 0.488, yf, BASE_Z0 + 0.06), (0, 1, 0))
        nl.row((sx * (cx - rr_ * math.cos(math.radians(a0))), yf, zlow), (sx * 0.322, yf, BASE_Z0 + 0.06), (0, 1, 0))
        # bottom rail, sides (follow the base edge)
        nl.row((sx * (HW + 0.0005), -HD + 0.04, BASE_Z0 + 0.05), (sx * (HW + 0.0005), HD - 0.04, BASE_Z0 + 0.05), (sx, 0, 0))
        # back: sides of the top rail, running down toward the arms
        nl.row((sx * 0.485, BACK_Y1 + 0.0005, BACK_TOP - 0.05), (sx * 0.485, BACK_Y1 + 0.0005, 0.69), (0, 1, 0))
    nl.row((-0.475, HD + 0.0005, BASE_Z0 + 0.05), (0.475, HD + 0.0005, BASE_Z0 + 0.05), (0, 1, 0))
    nl.row((-0.485, BACK_Y1 + 0.0005, BACK_TOP - 0.05), (0.485, BACK_Y1 + 0.0005, BACK_TOP - 0.05), (0, 1, 0))
    add("Chair_Nails", nl.mesh(), brass, smooth=False)

    # 8. report placement conflicts (bounding boxes, other furniture only)
    parts = [o for o in coll.objects if o.name.startswith("Chair_") and o.type == 'MESH']
    bpy.context.view_layer.update()
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in parts:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    print("e02: chair world bbox", tuple(round(v, 3) for v in lo), "->", tuple(round(v, 3) for v in hi), flush=True)
    for o in D.objects:
        if o.type != 'MESH' or o.name.startswith(("Chair_", "Wall_", "Floor", "Ceiling", "Baseboard")):
            continue
        if any(c.name in ("Outside", "Camera", "Lights") for c in o.users_collection):
            continue
        ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
        omin = [min(w[i] for w in ws) for i in range(3)]; omax = [max(w[i] for w in ws) for i in range(3)]
        if all(omin[i] < hi[i] - 0.005 and omax[i] > lo[i] + 0.005 for i in range(3)):
            print("e02: OVERLAP with", o.name, [round(v, 2) for v in omin], [round(v, 2) for v in omax], flush=True)
