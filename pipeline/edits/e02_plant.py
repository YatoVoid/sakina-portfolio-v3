"""Edit #2 (user request 2026-10-31): a more realistic desk plant, fully inside the new home frame.

Replaces the 26 flat card leaves and 104 stem segments with heart/arrow-shaped leaves (Syngonium/pothos-like)
on curved petioles. Each leaf: radial mesh (no jagged edges), acuminate tip, rounded basal lobes and sinus,
V-fold along the midrib, droop toward the tip, gentle wavy margin. UVs follow the existing LeafDark material
(u = 0.5 on the midrib, v = base -> tip), so its veins and colour variation are kept.
Pot, soil, pebbles and saucer are kept and moved 10 cm toward the lamp (+x) with the plant.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

SHIFT_X = 0.10
LAMP_CLEAR_X = -0.635          # no leaf vertex right of this above the desk clutter height (lamp arm/shade)
SEED = 17
N_LEAVES = 34
POT_R = 0.155                 # pot radius at the rim; draping leaves must stay outside it below the rim
VEIN_STRENGTH = 0.22          # was 0.7 in LeafDark: the regular stripes read as artificial

# Leaf outline: radius (fraction of length) vs angle from the tip direction, degrees. 180 = basal sinus.
OUTLINE = [(0, 1.00), (6, 0.92), (15, 0.80), (30, 0.68), (50, 0.61), (75, 0.57), (100, 0.54),
           (125, 0.50), (145, 0.43), (160, 0.31), (172, 0.15), (180, 0.04)]


def _r_of(theta_deg):
    a = abs(theta_deg)
    for (a0, r0), (a1, r1) in zip(OUTLINE, OUTLINE[1:]):
        if a0 <= a <= a1:
            t = (a - a0) / (a1 - a0)
            t = 0.5 - 0.5 * math.cos(math.pi * t)          # smooth
            return r0 + (r1 - r0) * t
    return OUTLINE[-1][1]


def _leaf_mesh(name, L, rng):
    """Leaf in local space: petiole joins at origin, tip along +Y, upper surface facing +Z."""
    n_ang, n_ring = 48, 7
    fold = rng.uniform(0.04, 0.10)                      # V along midrib
    droop = rng.uniform(0.10, 0.28)                     # tip bends down
    wave = rng.uniform(0.002, 0.005)
    twist = rng.uniform(-0.15, 0.15)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    centre = bm.verts.new((0, 0, 0))
    rings, uvs = [], {centre: (0.5, 0.4 / 0.35)}
    maxw = L * 0.55
    for k in range(1, n_ring + 1):
        f = k / n_ring
        ring = []
        for j in range(n_ang):
            th = -180 + 360 * j / n_ang
            r = _r_of(th) * L * f
            x, y = r * math.sin(math.radians(th)), r * math.cos(math.radians(th))
            z = fold * abs(x) - droop * max(y, 0) ** 2 / L + wave * f ** 2 * math.sin(math.radians(th) * 9) \
                + twist * x * max(y, 0) / L
            v = bm.verts.new((x, y, z))
            ring.append(v)
            uvs[v] = (0.5 + x / (2 * maxw), (y + 0.4 * L) / (0.35 * L))   # v scale sets vein angle ~45 deg off the midrib
        rings.append(ring)
    for j in range(n_ang):
        a, b = rings[0][j], rings[0][(j + 1) % n_ang]
        if j != n_ang // 2 - 1 and True:
            bm.faces.new((centre, a, b))
    for k in range(n_ring - 1):
        for j in range(n_ang):
            a, b = rings[k][j], rings[k][(j + 1) % n_ang]
            c, d = rings[k + 1][(j + 1) % n_ang], rings[k + 1][j]
            bm.faces.new((a, b, c, d))
    for f in bm.faces:
        for lp in f.loops:
            lp[uv].uv = uvs[lp.vert]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if sum(f.normal.z for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    return me


def _petiole(name, p0, p1, tangent_out, coll, mat):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'; cu.bevel_depth = 0.0028; cu.bevel_resolution = 2; cu.resolution_u = 8
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(1)
    a, b = sp.bezier_points
    a.co, b.co = p0, p1
    a.handle_left_type = a.handle_right_type = b.handle_left_type = b.handle_right_type = 'FREE'
    up = Vector((0, 0, 1))
    a.handle_right = p0 + up * (p1 - p0).length * 0.55
    a.handle_left = p0 - up * 0.01
    b.handle_left = p1 - tangent_out * (p1 - p0).length * 0.35
    b.handle_right = p1 + tangent_out * 0.01
    b.radius = 0.7
    o = bpy.data.objects.new(name, cu)
    o.data.materials.append(mat)
    coll.objects.link(o)
    return o


def apply():
    D = bpy.data
    coll = D.collections["Plant"]
    rng = random.Random(SEED)
    for o in list(coll.all_objects):
        if o.name.startswith(("Leaf", "Stem")):
            D.objects.remove(o, do_unlink=True)
    for o in coll.all_objects:                           # pot, rim, soil, pebbles, saucer
        if o.parent is None:
            o.location.x += SHIFT_X
    bpy.context.view_layer.update()
    soil = D.objects["Pot_Soil"]
    sb = [soil.matrix_world @ Vector(c) for c in soil.bound_box]
    cx = sum(v.x for v in sb) / 8; cy = sum(v.y for v in sb) / 8; top = max(v.z for v in sb)
    leaf_mat, stem_mat = D.materials["LeafDark"], D.materials["Stem"]

    # Leaf vein contrast (LeafDark is used only by the plant).
    for n in leaf_mat.node_tree.nodes:
        if n.type == 'MATH' and n.operation == 'MULTIPLY' and abs(n.inputs[1].default_value - 0.7) < 1e-6:
            n.inputs[1].default_value = VEIN_STRENGTH

    placed = 0; attempt = 0
    while placed < N_LEAVES and attempt < 1500:
        attempt += 1
        tier = placed / N_LEAVES                         # 0 = outer, draping over the rim; 1 = crown
        az = rng.uniform(-math.pi, math.pi)
        out = Vector((math.cos(az), math.sin(az), 0))
        if tier < 0.3:                                   # outer ring: short stalks arching over the rim
            reach, height = rng.uniform(0.15, 0.22), rng.uniform(0.00, 0.06)
            pitch = math.radians(rng.uniform(-45, -20)); L = rng.uniform(0.11, 0.15)
        elif tier < 0.75:                                # body: overlapping leaves at mid height
            reach, height = rng.uniform(0.07, 0.17), rng.uniform(0.07, 0.18)
            pitch = math.radians(rng.uniform(-25, 5)); L = rng.uniform(0.10, 0.145)
        else:                                            # crown: younger, more upright leaves
            reach, height = rng.uniform(0.02, 0.09), rng.uniform(0.17, 0.27)
            pitch = math.radians(rng.uniform(-5, 30)); L = rng.uniform(0.085, 0.12)
        base = Vector((cx, cy, top - 0.005)) + out * rng.uniform(0.0, 0.07) \
            + Vector((rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02), 0))
        attach = Vector((cx, cy, top)) + out * reach + Vector((0, 0, height))
        roll = math.radians(rng.uniform(-25, 25))
        tip_dir = Vector((out.x * math.cos(pitch), out.y * math.cos(pitch), math.sin(pitch)))
        zt = (Vector((0, 0, 1)) - tip_dir * tip_dir.z).normalized()
        xt = tip_dir.cross(zt).normalized()
        R = Matrix((xt, tip_dir, zt)).transposed().to_4x4() @ Matrix.Rotation(roll, 4, 'Y')
        me = _leaf_mesh(f"PlantLeaf_{placed}", L, rng)
        mw = Matrix.Translation(attach) @ R
        pts = [mw @ v.co for v in me.vertices]
        clash_lamp = any(p.x > LAMP_CLEAR_X and p.z > 0.80 for p in pts)
        in_pot = any(p.z < top - 0.003 and (Vector((p.x - cx, p.y - cy)).length < POT_R) for p in pts)
        if clash_lamp or in_pot or min(p.z for p in pts) < 0.80:
            D.meshes.remove(me); continue
        lf = D.objects.new(f"PlantLeaf_{placed}", me)
        lf.data.materials.append(leaf_mat)
        lf.matrix_world = mw
        coll.objects.link(lf)
        _petiole(f"PlantStem_{placed}", base, attach, tip_dir, coll, stem_mat)
        placed += 1
    print("PLANT leaves", placed, "attempts", attempt)
