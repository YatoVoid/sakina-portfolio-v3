"""Edit #2 v3 (user reference photo, 2026-10-31): golden pothos (Epipremnum aureum) in the terracotta pot.

Reference: dense mound of small heart-shaped, glossy leaves, bright green with yellow-cream variegation,
plus several vines spilling over the rim, hanging down the pot and trailing onto the table.
Inferred (not visible in the photo): exact leaf count, vine lengths at the back.

Built here:
- crown: ~70 leaves on short petioles forming a dome over the soil (covers the soil like the photo)
- 7 trailing vines over the rim (left / back / front-left; kept away from the lamp, pencil cup, calculator),
  alternating leaves every ~5 cm, ending on the desk
- leaf: radial mesh (pointed tip, shallow heart base), V-fold, droop, slight asymmetry
- material PothosLeaf: green-to-lime base with stretched yellow-cream variegation streaks, lighter midrib,
  glossy; per-leaf random pattern offset. UVs: u=0.5 on the midrib, v base->tip.
Pot, soil, pebbles, saucer kept; moved 10 cm toward the lamp (+x) as approved in round 2.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

SHIFT_X = 0.10
SEED = 23
N_CROWN = 72
VINES = [  # (azimuth deg: 0 = +x/lamp, 90 = back, 180 = left, 270 = front), length m, leaves
    (125, 0.34, 6), (160, 0.48, 8), (190, 0.42, 7), (215, 0.55, 9), (240, 0.30, 5), (100, 0.26, 4), (175, 0.24, 4)]
# Keep-out boxes (world, Blender coords): lamp, pencil cup, calculator, CD player. (xmin,ymin,zmin, xmax,ymax,zmax)
KEEP_OUT = [(-0.635, 1.55, 0.70, -0.30, 1.85, 1.30), (-0.86, 1.40, 0.70, -0.74, 1.52, 0.95),
            (-0.75, 1.51, 0.70, -0.61, 1.67, 0.77), (-1.10, 1.30, 0.70, -0.91, 1.50, 0.78)]
OUTLINE = [(0, 1.00), (8, 0.88), (20, 0.74), (40, 0.63), (65, 0.57), (90, 0.53), (115, 0.49),
           (140, 0.41), (158, 0.31), (170, 0.19), (180, 0.10)]


def _r_of(theta_deg, asym):
    a = abs(theta_deg)
    for (a0, r0), (a1, r1) in zip(OUTLINE, OUTLINE[1:]):
        if a0 <= a <= a1:
            t = 0.5 - 0.5 * math.cos(math.pi * (a - a0) / (a1 - a0))
            r = r0 + (r1 - r0) * t
            return r * (1 + asym * (1 if theta_deg > 0 else -1) * math.sin(math.radians(a)))
    return OUTLINE[-1][1]


def _leaf_mesh(name, L, rng):
    n_ang, n_ring = 40, 6
    fold, droop = rng.uniform(0.06, 0.16), rng.uniform(0.08, 0.30)
    asym, wave, twist = rng.uniform(-0.06, 0.06), rng.uniform(0.001, 0.003), rng.uniform(-0.2, 0.2)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap")
    maxw = L * 0.58
    centre = bm.verts.new((0, 0, 0)); uvs = {centre: (0.5, 0.25 / 1.25)}
    rings = []
    for k in range(1, n_ring + 1):
        f = k / n_ring; ring = []
        for j in range(n_ang):
            th = -180 + 360 * j / n_ang
            r = _r_of(th, asym) * L * f
            x, y = r * math.sin(math.radians(th)), r * math.cos(math.radians(th))
            z = fold * abs(x) - droop * max(y, 0) ** 2 / L + wave * f * math.sin(math.radians(th) * 7) \
                + twist * x * max(y, 0) / L
            v = bm.verts.new((x, y, z)); ring.append(v)
            uvs[v] = (0.5 + x / (2 * maxw), (y + 0.25 * L) / (1.25 * L))
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


def _pothos_material():
    m = bpy.data.materials.get("PothosLeaf")
    if m:
        return m
    m = bpy.data.materials.new("PothosLeaf"); m.use_nodes = True
    nt = m.node_tree; N, Lk = nt.nodes, nt.links
    bs = N["Principled BSDF"]
    bs.inputs["Roughness"].default_value = 0.32
    bs.inputs["Specular IOR Level"].default_value = 0.55
    tc = N.new("ShaderNodeTexCoord"); oi = N.new("ShaderNodeObjectInfo")
    sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs["UV"], sep.inputs[0])
    # per-leaf offset so leaves do not share one pattern
    off = N.new("ShaderNodeMath"); off.operation = 'MULTIPLY'; off.inputs[1].default_value = 37.0
    Lk.new(oi.outputs["Random"], off.inputs[0])
    # streak coordinates: stretched along the leaf (v), narrow across (u)
    comb = N.new("ShaderNodeCombineXYZ")
    sx = N.new("ShaderNodeMath"); sx.operation = 'MULTIPLY'; sx.inputs[1].default_value = 7.0
    Lk.new(sep.outputs["X"], sx.inputs[0]); Lk.new(sx.outputs[0], comb.inputs["X"])
    sy = N.new("ShaderNodeMath"); sy.operation = 'MULTIPLY'; sy.inputs[1].default_value = 1.4
    Lk.new(sep.outputs["Y"], sy.inputs[0]); Lk.new(sy.outputs[0], comb.inputs["Y"])
    Lk.new(off.outputs[0], comb.inputs["Z"])
    streak = N.new("ShaderNodeTexNoise"); streak.inputs["Scale"].default_value = 2.2
    streak.inputs["Detail"].default_value = 6.0; streak.inputs["Roughness"].default_value = 0.65
    Lk.new(comb.outputs[0], streak.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")            # variegation mask: ~25% of the leaf is yellow-cream streaks
    ramp.color_ramp.elements[0].position = 0.56; ramp.color_ramp.elements[1].position = 0.66
    Lk.new(streak.outputs["Fac"], ramp.inputs["Fac"])
    tone = N.new("ShaderNodeTexNoise"); tone.inputs["Scale"].default_value = 3.0
    Lk.new(comb.outputs[0], tone.inputs["Vector"])
    green = N.new("ShaderNodeMix"); green.data_type = 'RGBA'
    green.inputs[6].default_value = (0.055, 0.20, 0.025, 1)      # deep green
    green.inputs[7].default_value = (0.16, 0.42, 0.05, 1)        # lime green
    Lk.new(tone.outputs["Fac"], green.inputs["Factor"])
    vari = N.new("ShaderNodeMix"); vari.data_type = 'RGBA'
    vari.inputs[7].default_value = (0.62, 0.66, 0.20, 1)         # yellow-cream variegation
    Lk.new(green.outputs[2], vari.inputs[6]); Lk.new(ramp.outputs["Color"], vari.inputs["Factor"])
    # lighter midrib
    mid = N.new("ShaderNodeMath"); mid.operation = 'SUBTRACT'; mid.inputs[1].default_value = 0.5
    Lk.new(sep.outputs["X"], mid.inputs[0])
    ab = N.new("ShaderNodeMath"); ab.operation = 'ABSOLUTE'; Lk.new(mid.outputs[0], ab.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 0.025
    mr.inputs["To Min"].default_value = 0.45; mr.inputs["To Max"].default_value = 0.0
    Lk.new(ab.outputs[0], mr.inputs["Value"])
    rib = N.new("ShaderNodeMix"); rib.data_type = 'RGBA'; rib.inputs[7].default_value = (0.45, 0.58, 0.18, 1)
    Lk.new(vari.outputs[2], rib.inputs[6]); Lk.new(mr.outputs["Result"], rib.inputs["Factor"])
    Lk.new(rib.outputs[2], bs.inputs["Base Color"])
    return m


def _stem_material():
    m = bpy.data.materials.get("PothosStem")
    if m:
        return m
    m = bpy.data.materials.new("PothosStem"); m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.14, 0.30, 0.05, 1); bs.inputs["Roughness"].default_value = 0.45
    return m


def _curve(name, pts, coll, mat, radius=0.0022):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    cu.bevel_depth = radius; cu.bevel_resolution = 2; cu.resolution_u = 6
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts):
        p.co = (q.x, q.y, q.z, 1)
    sp.use_smooth = True
    o = bpy.data.objects.new(name, cu); o.data.materials.append(mat); coll.objects.link(o)
    return o


def _blocked(pts):
    for p in pts:
        for b in KEEP_OUT:
            if b[0] - 0.01 < p.x < b[3] + 0.01 and b[1] - 0.01 < p.y < b[4] + 0.01 and b[2] < p.z < b[5]:
                return True
    return False


def _frame(tip_dir, roll):
    zt = (Vector((0, 0, 1)) - tip_dir * tip_dir.z)
    zt = zt.normalized() if zt.length > 1e-6 else Vector((1, 0, 0))
    xt = tip_dir.cross(zt).normalized()
    return Matrix((xt, tip_dir, zt)).transposed().to_4x4() @ Matrix.Rotation(roll, 4, 'Y')


def apply():
    D = bpy.data
    coll = D.collections["Plant"]
    rng = random.Random(SEED)
    for o in list(coll.all_objects):
        if o.name.startswith(("Leaf", "Stem", "PlantLeaf", "PlantStem")):
            D.objects.remove(o, do_unlink=True)
    for o in coll.all_objects:
        if o.parent is None:
            o.location.x += SHIFT_X
    bpy.context.view_layer.update()
    soil, rim = D.objects["Pot_Soil"], D.objects["Pot_Rim"]
    sb = [soil.matrix_world @ Vector(c) for c in soil.bound_box]
    rb = [rim.matrix_world @ Vector(c) for c in rim.bound_box]
    cx, cy = sum(v.x for v in sb) / 8, sum(v.y for v in sb) / 8
    top = max(v.z for v in sb); rim_top = max(v.z for v in rb)
    rim_r = (max(v.x for v in rb) - min(v.x for v in rb)) / 2
    desk = 0.72
    leaf_mat, stem_mat = _pothos_material(), _stem_material()
    n_leaf = 0

    def add_leaf(attach, tip_dir, L, roll, stem_from=None, stem_pts=None):
        nonlocal n_leaf
        me = _leaf_mesh(f"Pothos_Leaf_{n_leaf}", L, rng)
        mw = Matrix.Translation(attach) @ _frame(tip_dir, roll)
        pts = [mw @ v.co for v in me.vertices]
        if _blocked(pts) or min(p.z for p in pts) < desk + 0.004:
            D.meshes.remove(me); return False
        o = D.objects.new(me.name, me); o.data.materials.append(leaf_mat); o.matrix_world = mw
        coll.objects.link(o)
        if stem_from is not None:
            mid = (stem_from + attach) / 2 + Vector((0, 0, 0.02))
            _curve(f"Pothos_Petiole_{n_leaf}", [stem_from, mid, attach], coll, stem_mat, 0.0017)
        n_leaf += 1
        return True

    # Crown: dome of leaves covering the soil.
    tries = 0; placed = 0
    while placed < N_CROWN and tries < 3000:
        tries += 1
        az = rng.uniform(-math.pi, math.pi); out = Vector((math.cos(az), math.sin(az), 0))
        u = rng.random()
        reach = rim_r * (0.15 + 0.95 * u ** 0.6)
        height = 0.03 + 0.17 * (1 - u ** 1.3) + rng.uniform(-0.02, 0.02)
        attach = Vector((cx, cy, top)) + out * reach + Vector((0, 0, height))
        pitch = math.radians(rng.uniform(-15, 20) - 40 * u)          # outer leaves tip outward and down
        tip = Vector((out.x * math.cos(pitch), out.y * math.cos(pitch), math.sin(pitch)))
        base = Vector((cx, cy, top)) + out * reach * 0.5
        if add_leaf(attach, tip, rng.uniform(0.055, 0.095), math.radians(rng.uniform(-25, 25)), base):
            placed += 1

    # Trailing vines: over the rim, down the pot, onto the desk.
    for i, (az_deg, length, n) in enumerate(VINES):
        az = math.radians(az_deg + rng.uniform(-8, 8)); out = Vector((math.cos(az), math.sin(az), 0))
        side = Vector((-out.y, out.x, 0))
        p0 = Vector((cx, cy, top)) + out * rim_r * 0.6
        p1 = Vector((cx, cy, rim_top + 0.025)) + out * (rim_r + 0.01)
        drop = rim_top - desk
        path = [p0, p1]
        # hang down the pot side with a slight outward bow, then lie on the desk
        hang = min(length * 0.7, drop + 0.02)
        steps = 8
        for s in range(1, steps + 1):
            t = s / steps
            z = rim_top + 0.02 - hang * t
            bow = 0.035 * math.sin(math.pi * t) + 0.02 * t
            path.append(Vector((cx, cy, max(z, desk + 0.004))) + out * (rim_r + 0.015 + bow)
                        + side * 0.02 * math.sin(3 * t + i))
        rest = max(0.0, length - hang)
        for s in range(1, 4):
            path.append(path[-1] + out * rest / 3 + side * rng.uniform(-0.015, 0.015) + Vector((0, 0, 0)))
            path[-1].z = desk + 0.004
        if _blocked(path):
            continue
        _curve(f"Pothos_Vine_{i}", path, coll, stem_mat)
        # leaves along the vine, alternating sides, getting smaller toward the tip
        seg = [(path[k], path[k + 1]) for k in range(1, len(path) - 1)]
        for j in range(n):
            a, b = seg[min(len(seg) - 1, int((j + 0.6) / n * len(seg)))]
            along = (b - a).normalized()
            sgn = 1 if j % 2 else -1
            tipdir = (out * 0.6 + side * sgn * 0.7 + Vector((0, 0, -0.15 if a.z > desk + 0.03 else 0.05))).normalized()
            attach = a + side * sgn * 0.008 + out * 0.012
            add_leaf(attach, tipdir, rng.uniform(0.05, 0.075) * (1 - 0.3 * j / n), math.radians(rng.uniform(-30, 30)))
    print("PLANT pothos leaves", n_leaf)
