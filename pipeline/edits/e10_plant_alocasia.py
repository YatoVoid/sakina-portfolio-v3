"""Edit #10 (round 4, user reference photo 2026-11-01, JayDeeMahs 'vintage planter with houseplant'):
dark-leaf Alocasia (elephant-ear / arrowhead leaves) in a round terracotta bowl pot.

Reference, read from the photo:
- Pot: terracotta bowl, widest about 70 % of the way up, narrowing to a small foot, a thin outward-flared lip; matte,
  warm orange-brown, mottled with darker rust patches low on the body and a few dark specks. No saucer.
- Plant: ~9 big arrowhead leaves on long, pale yellow-green, slightly curved petioles that rise from one clump:
  three large leaves (about as long as the pot is wide), smaller ones below and in front. Blades are dark grey-green
  with a silvery sheen, pale yellow-green veins (thick midrib, herringbone side veins), slightly rippled margins,
  cupped and drooping at the tip. The two tallest leaves lean out to the left and up to the right.
Inferred (not visible): the leaf backs (lighter grey-green), exact leaf count at the back.

Replaces the golden pothos (round 2) at the user's request. Position (x -0.90, y 1.72 on the desk) is unchanged.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

SEED = 5
DESK_Z = 0.7205
CX, CY = -0.90, 1.72
R_RIM, H_POT = 0.135, 0.215                       # rim radius, pot height (reference: height / width = 0.84)
# (z fraction, radius / rim radius): outer wall from the foot up to the lip
OUTER = [(0.000, 0.40), (0.020, 0.43), (0.090, 0.52), (0.220, 0.72), (0.380, 0.90), (0.540, 0.985),
         (0.660, 1.000), (0.770, 0.985), (0.860, 0.945), (0.925, 0.935), (0.955, 0.965), (0.985, 1.020), (1.000, 1.010)]
WALL_T = 0.010
SOIL_DROP = 0.028                                 # soil surface below the rim top

# leaves: (azimuth deg [0 = +x, 90 = back/+y, 180 = -x, 270 = front], petiole height above the soil, blade length,
#          tip pitch deg above horizontal, droop, roll deg, base offset from clump centre)
LEAVES = [
    (178, 0.215, 0.360, 24, 0.30, -10, 0.020),    # tall left leaf, leans out and arches over
    (20, 0.250, 0.290, 52, 0.18, 8, 0.015),       # tallest, up and to the right
    (352, 0.165, 0.250, 14, 0.32, 12, 0.025),     # right, mid height
    (158, 0.150, 0.235, 6, 0.30, -14, 0.028),     # left, mid height
    (88, 0.215, 0.230, 46, 0.20, 0, 0.010),       # back, upright
    (322, 0.105, 0.210, 4, 0.28, 14, 0.030),      # low right-front
    (222, 0.090, 0.190, -4, 0.26, -12, 0.030),    # low left-front
    (58, 0.195, 0.150, 70, 0.12, 20, 0.010),      # young leaf, right
    (128, 0.170, 0.165, 38, 0.18, 0, 0.010),      # back-left
    (265, 0.075, 0.150, -8, 0.24, 6, 0.030),      # small front
    (118, 0.250, 0.140, 62, 0.14, -8, 0.010),     # small tall, back
    (300, 0.140, 0.175, 22, 0.28, 0, 0.026),      # right-front mid
]

# leaf outline: (angle from the tip direction in degrees, radius / blade length) measured from the petiole attachment
OUTLINE = [(0, 1.00), (5, 0.94), (12, 0.80), (25, 0.62), (45, 0.50), (70, 0.445), (95, 0.43), (120, 0.41),
           (145, 0.375), (162, 0.28), (173, 0.14), (180, 0.07)]


def _r_of(deg, asym):
    a = abs(deg)
    for (a0, r0), (a1, r1) in zip(OUTLINE, OUTLINE[1:]):
        if a0 <= a <= a1:
            t = 0.5 - 0.5 * math.cos(math.pi * (a - a0) / (a1 - a0))
            r = r0 + (r1 - r0) * t
            return r * (1 + asym * (1 if deg > 0 else -1) * math.sin(math.radians(a)))
    return OUTLINE[-1][1]


def _leaf_mesh(name, L, droop, rng):
    n_ang, n_ring = 72, 16
    fold = rng.uniform(0.14, 0.24)                       # cup along the midrib
    asym = rng.uniform(-0.05, 0.05)
    wave_k = rng.choice((7, 8, 9)); wave_ph = rng.uniform(0, 6.28)
    wave_a = rng.uniform(0.020, 0.032) * L               # rippled margin
    twist = rng.uniform(-0.18, 0.18)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap")
    maxw = 0.46 * L
    centre = bm.verts.new((0, 0, 0)); uvs = {centre: (0.5, 0.30 / 1.30)}
    rings = []
    for k in range(1, n_ring + 1):
        f = k / n_ring; ring = []
        for j in range(n_ang):
            th = -180 + 360 * j / n_ang
            r = _r_of(th, asym) * L * f
            x, y = r * math.sin(math.radians(th)), r * math.cos(math.radians(th))
            yy = max(y, 0.0) / L
            z = (fold * abs(x) * (1.0 - 0.45 * yy)                              # V cup, flatter toward the tip
                 - droop * 0.55 * L * yy * yy                                    # arched / drooping tip
                 + wave_a * (f ** 2.4) * math.sin(math.radians(th) * wave_k + wave_ph)
                 + twist * x * yy)
            ring.append(bm.verts.new((x, y, z)))
            uvs[ring[-1]] = (0.5 + x / (2 * maxw), (y + 0.30 * L) / (1.30 * L))
        rings.append(ring)
    for j in range(n_ang):
        bm.faces.new((centre, rings[0][j], rings[0][(j + 1) % n_ang]))
    for k in range(n_ring - 1):
        for j in range(n_ang):
            bm.faces.new((rings[k][j], rings[k][(j + 1) % n_ang], rings[k + 1][(j + 1) % n_ang], rings[k + 1][j]))
    for f in bm.faces:
        for lp in f.loops:
            lp[uv].uv = uvs[lp.vert]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if sum(f.normal.z for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me


# ------------------------------------------------------------------------------------------ materials
def _N(nt, t, **kw):
    n = nt.nodes.new(t)
    for k, v in kw.items():
        if k.startswith("in_"):
            n.inputs[k[3:].replace("_", " ")].default_value = v
        else:
            setattr(n, k, v)
    return n


def _L(nt, a, b):
    nt.links.new(a, b)


def _hex(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c) + (1.0,)


def _math(nt, op, a, b=None, clamp=False):
    n = _N(nt, "ShaderNodeMath", operation=op)
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            _L(nt, v, n.inputs[i])
    n.use_clamp = clamp
    return n.outputs[0]


def alocasia_mat():
    m = bpy.data.materials.get("AlocasiaLeaf")
    if m:
        return m
    m = bpy.data.materials.new("AlocasiaLeaf"); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    tc = _N(nt, "ShaderNodeTexCoord"); oi = _N(nt, "ShaderNodeObjectInfo")
    sp = _N(nt, "ShaderNodeSeparateXYZ"); _L(nt, tc.outputs["UV"], sp.inputs[0])
    lx = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', sp.outputs["X"], 0.5), 0.92)      # across, in blade lengths
    ly = _math(nt, 'SUBTRACT', _math(nt, 'MULTIPLY', sp.outputs["Y"], 1.30), 0.30)     # along, notch = 0, tip = 1
    ax = _math(nt, 'ABSOLUTE', lx)
    rnd = _math(nt, 'MULTIPLY', oi.outputs["Random"], 31.0)

    # lateral veins: herringbone, leaving the midrib about 50 deg off the midrib direction; slightly wobbly
    wob = _N(nt, "ShaderNodeTexNoise", in_Scale=7.0, in_Detail=2.0)
    cmb = _N(nt, "ShaderNodeCombineXYZ"); _L(nt, _math(nt, 'MULTIPLY', lx, 1.0), cmb.inputs["X"]); _L(nt, ly, cmb.inputs["Y"]); _L(nt, rnd, cmb.inputs["Z"])
    _L(nt, cmb.outputs[0], wob.inputs["Vector"])
    t = _math(nt, 'MULTIPLY', _math(nt, 'ADD', _math(nt, 'SUBTRACT', ly, _math(nt, 'MULTIPLY', ax, 0.88)),
                                    _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', wob.outputs["Fac"], 0.5), 0.05)), 9.0)
    c = _math(nt, 'FRACT', t)
    dist = _math(nt, 'MINIMUM', c, _math(nt, 'SUBTRACT', 1.0, c))                       # distance to nearest vein (0..0.5)
    vm = _N(nt, "ShaderNodeMapRange", in_From_Min=0.0, in_From_Max=0.085, in_To_Min=1.0, in_To_Max=0.0, clamp=True)
    _L(nt, dist, vm.inputs["Value"])
    # veins fade toward the margin and before the tip
    fade = _N(nt, "ShaderNodeMapRange", in_From_Min=0.19, in_From_Max=0.33, in_To_Min=1.0, in_To_Max=0.18, clamp=True)
    _L(nt, ax, fade.inputs["Value"])
    veins = _math(nt, 'MULTIPLY', vm.outputs["Result"], fade.outputs["Result"])

    # midrib: wide at the notch, thin at the tip
    mw = _N(nt, "ShaderNodeMapRange", in_From_Min=0.0, in_From_Max=1.0, in_To_Min=0.020, in_To_Max=0.0045, clamp=True)
    _L(nt, _math(nt, 'MAXIMUM', ly, 0.0), mw.inputs["Value"])
    mr = _N(nt, "ShaderNodeMath", operation='DIVIDE', use_clamp=True)
    _L(nt, ax, mr.inputs[0]); _L(nt, mw.outputs["Result"], mr.inputs[1])
    mid = _math(nt, 'SUBTRACT', 1.0, _math(nt, 'POWER', _math(nt, 'MINIMUM', mr.outputs[0], 1.0), 3.0))
    # fine reticulate network between the veins
    vo = _N(nt, "ShaderNodeTexVoronoi", feature='DISTANCE_TO_EDGE', in_Scale=70.0)
    _L(nt, tc.outputs["UV"], vo.inputs["Vector"])
    net = _N(nt, "ShaderNodeMapRange", in_From_Min=0.0, in_From_Max=0.07, in_To_Min=0.35, in_To_Max=0.0, clamp=True)
    _L(nt, vo.outputs["Distance"], net.inputs["Value"])

    # blade colour: deep grey-green, slow tone drift + silvery patches
    n1 = _N(nt, "ShaderNodeTexNoise", in_Scale=4.0, in_Detail=4.0)
    _L(nt, cmb.outputs[0], n1.inputs["Vector"])
    base = _N(nt, "ShaderNodeMix", data_type='RGBA')
    base.inputs[6].default_value = _hex("23402b"); base.inputs[7].default_value = _hex("4a6f50")
    _L(nt, n1.outputs["Fac"], base.inputs[0])
    sil = _N(nt, "ShaderNodeMix", data_type='RGBA'); sil.inputs[7].default_value = _hex("86a48c")
    sm = _N(nt, "ShaderNodeMapRange", in_From_Min=0.55, in_From_Max=0.80, in_To_Min=0.0, in_To_Max=0.35, clamp=True)
    _L(nt, n1.outputs["Fac"], sm.inputs["Value"])
    _L(nt, sm.outputs["Result"], sil.inputs[0]); _L(nt, base.outputs[2], sil.inputs[6])
    # veins and midrib: pale yellow-green, midrib lightest
    vcol = _N(nt, "ShaderNodeMix", data_type='RGBA'); vcol.inputs[7].default_value = _hex("a9bf86")
    _L(nt, _math(nt, 'MULTIPLY', veins, 0.80), vcol.inputs[0]); _L(nt, sil.outputs[2], vcol.inputs[6])
    ncol = _N(nt, "ShaderNodeMix", data_type='RGBA'); ncol.inputs[7].default_value = _hex("8fa877")
    _L(nt, net.outputs["Result"], ncol.inputs[0]); _L(nt, vcol.outputs[2], ncol.inputs[6])
    mcol = _N(nt, "ShaderNodeMix", data_type='RGBA'); mcol.inputs[7].default_value = _hex("c1d29d")
    _L(nt, mid, mcol.inputs[0]); _L(nt, ncol.outputs[2], mcol.inputs[6])
    # underside: lighter grey-green, faint purple-ish tint
    geo = _N(nt, "ShaderNodeNewGeometry")
    under = _N(nt, "ShaderNodeMix", data_type='RGBA'); under.inputs[7].default_value = _hex("5f7a62")
    _L(nt, geo.outputs["Backfacing"], under.inputs[0]); _L(nt, mcol.outputs[2], under.inputs[6])
    _L(nt, under.outputs[2], bs.inputs["Base Color"])

    bs.inputs["Roughness"].default_value = 0.30
    bs.inputs["Specular IOR Level"].default_value = 0.62
    bs.inputs["Sheen Weight"].default_value = 0.55; bs.inputs["Sheen Roughness"].default_value = 0.4
    bs.inputs["Coat Weight"].default_value = 0.10; bs.inputs["Coat Roughness"].default_value = 0.2
    bs.inputs["Subsurface Weight"].default_value = 0.05
    # veins sit slightly sunken, the midrib stands proud, tiny blister texture on the blade
    bl = _N(nt, "ShaderNodeTexNoise", in_Scale=60.0, in_Detail=2.0)
    _L(nt, tc.outputs["UV"], bl.inputs["Vector"])
    hgt = _math(nt, 'ADD', _math(nt, 'SUBTRACT', _math(nt, 'MULTIPLY', mid, 0.9), _math(nt, 'MULTIPLY', veins, 0.5)),
                _math(nt, 'MULTIPLY', bl.outputs["Fac"], 0.12))
    bp = _N(nt, "ShaderNodeBump", in_Strength=0.55, in_Distance=0.0015)
    _L(nt, hgt, bp.inputs["Height"]); _L(nt, bp.outputs["Normal"], bs.inputs["Normal"])
    return m


def petiole_mat():
    m = bpy.data.materials.get("AlocasiaPetiole")
    if m:
        return m
    m = bpy.data.materials.new("AlocasiaPetiole"); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    tc = _N(nt, "ShaderNodeTexCoord")
    n = _N(nt, "ShaderNodeTexNoise", in_Scale=3.0, in_Detail=3.0)
    mp = _N(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = (30.0, 30.0, 4.0)
    _L(nt, tc.outputs["Object"], mp.inputs["Vector"]); _L(nt, mp.outputs[0], n.inputs["Vector"])
    mix = _N(nt, "ShaderNodeMix", data_type='RGBA')
    mix.inputs[6].default_value = _hex("6c8c43"); mix.inputs[7].default_value = _hex("94b05c")
    _L(nt, n.outputs["Fac"], mix.inputs[0]); _L(nt, mix.outputs[2], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.42; bs.inputs["Specular IOR Level"].default_value = 0.45
    return m


def terracotta_mat():
    m = bpy.data.materials.get("TerracottaBowl")
    if m:
        return m
    m = bpy.data.materials.new("TerracottaBowl"); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    tc = _N(nt, "ShaderNodeTexCoord")
    sep = _N(nt, "ShaderNodeSeparateXYZ"); _L(nt, tc.outputs["Object"], sep.inputs[0])
    # base: warm orange-brown with soft tone drift
    n1 = _N(nt, "ShaderNodeTexNoise", in_Scale=14.0, in_Detail=5.0, in_Roughness=0.6)
    _L(nt, tc.outputs["Object"], n1.inputs["Vector"])
    base = _N(nt, "ShaderNodeMix", data_type='RGBA')
    base.inputs[6].default_value = _hex("b86a38"); base.inputs[7].default_value = _hex("d08d55")
    _L(nt, n1.outputs["Fac"], base.inputs[0])
    # big dark rust blotches, stronger low on the body (object z is relative to the pot origin, 0 at the foot)
    n2 = _N(nt, "ShaderNodeTexNoise", in_Scale=9.0, in_Detail=3.0, in_Roughness=0.6)
    _L(nt, tc.outputs["Object"], n2.inputs["Vector"])
    bm = _N(nt, "ShaderNodeMapRange", in_From_Min=0.56, in_From_Max=0.66, in_To_Min=0.0, in_To_Max=0.75, clamp=True)
    _L(nt, n2.outputs["Fac"], bm.inputs["Value"])
    low = _N(nt, "ShaderNodeMapRange", in_From_Min=0.10, in_From_Max=0.0, in_To_Min=0.35, in_To_Max=1.0, clamp=True)
    _L(nt, _math(nt, 'MULTIPLY', sep.outputs["Z"], 1.0), low.inputs["Value"])
    # (z in metres: 0 at foot, 0.215 at rim) -> use blotch strength that fades upward
    zf = _N(nt, "ShaderNodeMapRange", in_From_Min=0.03, in_From_Max=0.17, in_To_Min=1.0, in_To_Max=0.25, clamp=True)
    _L(nt, sep.outputs["Z"], zf.inputs["Value"])
    bl = _math(nt, 'MULTIPLY', bm.outputs["Result"], zf.outputs["Result"])
    mixb = _N(nt, "ShaderNodeMix", data_type='RGBA'); mixb.inputs[7].default_value = _hex("6e3a20")
    _L(nt, bl, mixb.inputs[0]); _L(nt, base.outputs[2], mixb.inputs[6])
    # specks and tiny pits
    vo = _N(nt, "ShaderNodeTexVoronoi", in_Scale=210.0, feature='F1')
    _L(nt, tc.outputs["Object"], vo.inputs["Vector"])
    spk = _N(nt, "ShaderNodeMapRange", in_From_Min=0.07, in_From_Max=0.03, in_To_Min=0.0, in_To_Max=0.9, clamp=True)
    _L(nt, vo.outputs["Distance"], spk.inputs["Value"])
    sx = _N(nt, "ShaderNodeSeparateColor"); _L(nt, vo.outputs["Color"], sx.inputs["Color"])
    act = _N(nt, "ShaderNodeMath", operation='GREATER_THAN'); act.inputs[1].default_value = 0.86
    _L(nt, sx.outputs["Red"], act.inputs[0])
    spm = _math(nt, 'MULTIPLY', spk.outputs["Result"], act.outputs[0])
    mixs = _N(nt, "ShaderNodeMix", data_type='RGBA'); mixs.inputs[7].default_value = _hex("55291a")
    _L(nt, spm, mixs.inputs[0]); _L(nt, mixb.outputs[2], mixs.inputs[6])
    # dusty pale top (lip / upper body)
    dz = _N(nt, "ShaderNodeMapRange", in_From_Min=0.15, in_From_Max=0.215, in_To_Min=0.0, in_To_Max=0.35, clamp=True)
    _L(nt, sep.outputs["Z"], dz.inputs["Value"])
    mixd = _N(nt, "ShaderNodeMix", data_type='RGBA'); mixd.inputs[7].default_value = _hex("dba878")
    _L(nt, dz.outputs["Result"], mixd.inputs[0]); _L(nt, mixs.outputs[2], mixd.inputs[6])
    _L(nt, mixd.outputs[2], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.78; bs.inputs["Specular IOR Level"].default_value = 0.25
    gn = _N(nt, "ShaderNodeTexNoise", in_Scale=320.0, in_Detail=3.0)
    _L(nt, tc.outputs["Object"], gn.inputs["Vector"])
    bp = _N(nt, "ShaderNodeBump", in_Strength=0.35, in_Distance=0.0008)
    _L(nt, gn.outputs["Fac"], bp.inputs["Height"]); _L(nt, bp.outputs["Normal"], bs.inputs["Normal"])
    return m


# ------------------------------------------------------------------------------------------ pot
def _pot_mesh(mat):
    bm = bmesh.new()
    prof = [(R_RIM * r, DESK_Z + H_POT * f - (DESK_Z)) for f, r in OUTER]               # local z: 0 at the foot
    # lip top, then the inner wall down to the soil, then the soil floor (closed, so light cannot leak)
    inner = [(R_RIM * 0.935 - 0.002, H_POT), (R_RIM * 0.905, H_POT - 0.012), (R_RIM * 0.86, H_POT - 0.045),
             (R_RIM * 0.80, H_POT - 0.085), (R_RIM * 0.70, H_POT - 0.14), (0.0, H_POT - 0.14)]
    pts = [(0.0, 0.0)] + prof + inner
    seg = 64
    rings = []
    for (r, z) in pts:
        if r == 0.0:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * j / seg), r * math.sin(2 * math.pi * j / seg), z)) for j in range(seg)])
    for k in range(len(rings) - 1):
        A, B = rings[k], rings[k + 1]
        if len(A) == 1:
            for j in range(seg):
                bm.faces.new((A[0], B[(j + 1) % seg], B[j]))
        elif len(B) == 1:
            for j in range(seg):
                bm.faces.new((A[j], A[(j + 1) % seg], B[0]))
        else:
            for j in range(seg):
                bm.faces.new((A[j], A[(j + 1) % seg], B[(j + 1) % seg], B[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("Pot"); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    return me


def _curve(name, pts, coll, mat, r0, r1):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = 1.0; cu.bevel_resolution = 3; cu.resolution_u = 10
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
    for i, (bp, q) in enumerate(zip(sp.bezier_points, pts)):
        bp.co = q; bp.handle_left_type = bp.handle_right_type = 'AUTO'
        bp.radius = r0 + (r1 - r0) * i / (len(pts) - 1)
    o = bpy.data.objects.new(name, cu); o.data.materials.append(mat); coll.objects.link(o)
    return o


def _frame(tip_dir, roll):
    zt = Vector((0, 0, 1)) - tip_dir * tip_dir.z
    zt = zt.normalized() if zt.length > 1e-6 else Vector((1, 0, 0))
    xt = tip_dir.cross(zt).normalized()
    return Matrix((xt, tip_dir, zt)).transposed().to_4x4() @ Matrix.Rotation(roll, 4, 'Y')


def apply():
    D = bpy.data
    coll = D.collections["Plant"]
    rng = random.Random(SEED)
    soil_mat = D.objects["Pot_Soil"].data.materials[0] if "Pot_Soil" in D.objects and D.objects["Pot_Soil"].data.materials else None
    for o in list(coll.all_objects):
        if o.name.startswith(("Pothos", "Pebble", "Saucer", "Pot", "Leaf", "Stem")):
            me = o.data if o.type in ('MESH', 'CURVE') else None
            D.objects.remove(o, do_unlink=True)
            if me is not None and me.users == 0:
                (D.meshes if isinstance(me, bpy.types.Mesh) else D.curves).remove(me)
    # pot
    pot = D.objects.new("Pot", _pot_mesh(terracotta_mat()))
    pot.location = (CX, CY, DESK_Z); coll.objects.link(pot)
    # soil: shallow mound just under the lip
    soil_z = DESK_Z + H_POT - SOIL_DROP
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=R_RIM * 0.90, radius2=R_RIM * 0.86, depth=0.012)
    me = bpy.data.meshes.new("Pot_Soil"); bm.to_mesh(me); bm.free()
    for v in me.vertices:
        v.co.z += rng.uniform(-0.0012, 0.0012) if v.co.z > 0 else 0
    if soil_mat:
        me.materials.append(soil_mat)
    else:
        sm = D.materials.new("PotSoilAlo"); sm.use_nodes = True
        sm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = _hex("2b1d14")
        me.materials.append(sm)
    soil = D.objects.new("Pot_Soil", me); soil.location = (CX, CY, soil_z - 0.006); coll.objects.link(soil)

    leaf_mat, pet_mat = alocasia_mat(), petiole_mat()
    for i, (az, hgt, L, pitch, droop, roll, off) in enumerate(LEAVES):
        a = math.radians(az + rng.uniform(-6, 6)); out = Vector((math.cos(a), math.sin(a), 0))
        base = Vector((CX, CY, soil_z)) + out * off * 0.5 + Vector((rng.uniform(-0.008, 0.008), rng.uniform(-0.008, 0.008), 0))
        # petiole: rises from the clump, bows toward the leaf direction, ends at the blade's notch
        reach = 0.04 + 0.09 * min(1.0, L / 0.36) + off
        attach = Vector((CX, CY, soil_z)) + out * reach + Vector((0, 0, hgt))
        mid1 = base + (attach - base) * 0.35 + out * 0.012
        mid2 = base + (attach - base) * 0.72 + out * 0.012 * 0.5
        _curve(f"Alo_Petiole_{i}", [base, mid1, mid2, attach], coll, pet_mat, 0.0068, 0.0040)
        # blade: tip direction leans outward at the given pitch
        p = math.radians(pitch)
        tip = Vector((out.x * math.cos(p), out.y * math.cos(p), math.sin(p)))
        me = _leaf_mesh(f"Alo_Leaf_{i}", L, droop, rng)
        o = D.objects.new(me.name, me); o.data.materials.append(leaf_mat)
        o.matrix_world = Matrix.Translation(attach) @ _frame(tip, math.radians(roll))
        coll.objects.link(o)
    bpy.context.view_layer.update()
    print("e10 alocasia plant:", len(LEAVES), "leaves")


if __name__ == "__main__":                         # standalone: python3 e10_plant_alocasia.py <in.blend> <out.blend>
    import sys
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    bpy.ops.wm.open_mainfile(filepath=a[0]); apply()
    bpy.ops.wm.save_as_mainfile(filepath=a[1], compress=True)
