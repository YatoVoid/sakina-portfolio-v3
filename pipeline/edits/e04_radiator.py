"""Edit #4 (user request 2026-11-01): a cast-iron column radiator under the centre desk / window, as in the
reference (Felix Rieseberg-style render: dark bronze radiator with many vertical sections, a slightly wider top cap and
bottom manifold, two short cream pipes dropping from the right end to the floor with a ring at the floor).

Reference analysis:
  certain  - 20+ closely spaced vertical sections, top cap + bottom rail, small feet, two vertical pipes at the right end
             going into the floor, dark warm-brown satin paint, sits in the wall gap below the window, under the desk.
  inferred - real size (1.10 m wide x 0.53 m high x 0.12 m deep so it fits between the curtains, x -0.71 .. 0.50, and under
             the desk underside z 0.67), section pitch 4.6 cm, double-row depth, exact paint colour, valve shape.
Placement: back against the back-wall baseboard (wall y 2.48), centred in the open wall gap between Curtain_L and Curtain_R.
All parts go to the Desk collection (that is the bake group that already contains the desk).
"""
import bpy, bmesh, math, os, importlib.util
from mathutils import Vector, Matrix

D = bpy.data
_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "e02_club_chair.py")
_s = importlib.util.spec_from_file_location("e02_club_chair", _p)
E2 = importlib.util.module_from_spec(_s); _s.loader.exec_module(E2)

CX = -0.105                 # centre of the radiator (centre of the gap between the curtains)
WALL_Y = 2.475              # back of the radiator (back wall baseboard at y 2.48)
W, DEPTH = 1.10, 0.12
N_SECTIONS = 24
Z_FEET, Z_RAIL0, Z_RAIL1, Z_TOP = 0.06, 0.06, 0.105, 0.585   # feet height, bottom rail span, top of body


def paint_material(name):
    """Satin cast-iron paint: dark warm bronze with a fine casting grain."""
    m = D.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear(); n = E2._n
    out = n(nt, "ShaderNodeOutputMaterial", 6, 0)
    b = n(nt, "ShaderNodeBsdfPrincipled", 5, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = (0.085, 0.060, 0.042, 1)
    b.inputs["Roughness"].default_value = 0.52
    b.inputs["Coat Weight"].default_value = 0.08; b.inputs["Coat Roughness"].default_value = 0.3
    tc = n(nt, "ShaderNodeTexCoord", 0, 0)
    ns = n(nt, "ShaderNodeTexNoise", 2, 0, noise_dimensions='3D')
    ns.inputs["Scale"].default_value = 420.0; ns.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
    bm = n(nt, "ShaderNodeBump", 4, -1)
    bm.inputs["Strength"].default_value = 0.35; bm.inputs["Distance"].default_value = 0.0006
    nt.links.new(ns.outputs["Fac"], bm.inputs["Height"])
    nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    return m


def solid(name, col, rough, metallic=0.0):
    m = D.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    return m


def apply():
    coll = D.collections["Desk"]
    paint = paint_material("Radiator_Paint")
    pipe_m = solid("Radiator_Pipe", (0.52, 0.47, 0.37, 1), 0.42)
    brass = solid("Radiator_Brass", (0.50, 0.33, 0.12, 1), 0.32, 1.0)

    def put(name, me, mat):
        E2.finish(me, 40)
        me.materials.append(mat)
        o = D.objects.new(name, me); coll.objects.link(o)
        return o

    y_back = WALL_Y - DEPTH / 2            # centre line of the radiator in y (it spans WALL_Y-DEPTH .. WALL_Y)
    y_c = y_back
    x0 = CX - W / 2
    pitch = W / N_SECTIONS

    # sections: two rows (front / back) of rounded vertical ribs
    ribs = bmesh.new()
    z0, z1 = Z_RAIL1 - 0.004, Z_TOP - 0.020
    for row, (yc, hd) in enumerate(((y_c + 0.030, 0.027), (y_c - 0.030, 0.027))):
        for i in range(N_SECTIONS):
            xc = x0 + pitch * (i + 0.5)
            me = E2.bevelled_box((pitch * 0.5 - 0.0045, hd, (z1 - z0) / 2), (xc, yc, (z0 + z1) / 2), 0.0115, 3)
            ribs.from_mesh(me); D.meshes.remove(me)
    rme = D.meshes.new("Radiator_Sections"); ribs.to_mesh(rme); ribs.free()
    put("Radiator_Sections", rme, paint)

    # top cap (slightly wider, with a rounded edge) and bottom manifold
    put("Radiator_Top", E2.bevelled_box((W / 2 + 0.006, DEPTH / 2 + 0.006, 0.0125), (CX, y_c, Z_TOP - 0.0125), 0.009, 3), paint)
    put("Radiator_Bottom", E2.bevelled_box((W / 2, DEPTH / 2 - 0.012, (Z_RAIL1 - Z_RAIL0) / 2), (CX, y_c, (Z_RAIL0 + Z_RAIL1) / 2), 0.008, 3), paint)
    # end sections (taller, wider) close the two ends like real cast-iron radiators
    for sx in (-1, 1):
        put("Radiator_End", E2.bevelled_box((0.012, DEPTH / 2 - 0.004, (Z_TOP - Z_RAIL0) / 2 - 0.002),
                                            (CX + sx * (W / 2 - 0.006), y_c, (Z_TOP + Z_RAIL0) / 2), 0.008, 3), paint)
    # feet
    for sx in (-1, 1):
        for sy in (-1, 1):
            put("Radiator_Foot", E2.bevelled_box((0.022, 0.022, Z_FEET / 2), (CX + sx * 0.45, y_c + sy * 0.035, Z_FEET / 2), 0.006, 2), paint)

    # two cream pipes from the bottom rail at the right end down into the floor, with floor rings (certain)
    px = [CX + W / 2 - 0.075, CX + W / 2 - 0.032]
    for x in px:
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.0095, radius2=0.0095, depth=Z_RAIL0 + 0.01)
        me = D.meshes.new("pipe"); bm.to_mesh(me); bm.free()
        me.transform(Matrix.Translation((x, y_c, (Z_RAIL0 + 0.01) / 2)))
        put("Radiator_Pipe", me, pipe_m)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.021, radius2=0.017, depth=0.006)
        me = D.meshes.new("ring"); bm.to_mesh(me); bm.free()
        me.transform(Matrix.Translation((x, y_c, 0.003)))
        put("Radiator_FloorRing", me, pipe_m)
    # small brass valve body + hand wheel on the right end of the bottom rail, bleed screw top left
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=0.013, radius2=0.013, depth=0.030)
    me = D.meshes.new("valve"); bm.to_mesh(me); bm.free()
    me.transform(Matrix.Rotation(math.radians(90), 4, 'Y') @ Matrix.Identity(4))
    me.transform(Matrix.Translation((CX + W / 2 + 0.018, y_c, Z_RAIL0 + 0.022)))
    put("Radiator_Valve", me, brass)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.007, radius2=0.007, depth=0.016)
    me = D.meshes.new("bleed"); bm.to_mesh(me); bm.free()
    me.transform(Matrix.Translation((CX - W / 2 + 0.05, y_c, Z_TOP + 0.008)))
    put("Radiator_Bleed", me, brass)

    bpy.context.view_layer.update()
    parts = [o for o in D.objects if o.name.startswith("Radiator_")]
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in parts:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    print("e04: radiator bbox", [round(v, 3) for v in lo], [round(v, 3) for v in hi], flush=True)
    for o in D.objects:
        if o.type != 'MESH' or o in parts or o.name.startswith(("Wall_", "Floor", "Ceiling", "Room")):
            continue
        if any(c.name in ("Outside", "Camera", "Lights") for c in o.users_collection):
            continue
        ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
        omin = [min(w[i] for w in ws) for i in range(3)]; omax = [max(w[i] for w in ws) for i in range(3)]
        if all(omin[i] < hi[i] - 0.005 and omax[i] > lo[i] + 0.005 for i in range(3)):
            print("e04: OVERLAP with", o.name, [round(v, 2) for v in omin], [round(v, 2) for v in omax], flush=True)
