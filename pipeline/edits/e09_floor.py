"""Edit #9 (round 4, user 2026-11-01): floor copied from the 'Antique Oak - Boardwalk Hardwood Floors' photo.

What the reference shows, and what is built here:
- Wide reclaimed oak planks (about 13-22 cm), long (0.9-2.6 m), running away from the viewer, butt joints staggered.
- Every board is its own colour: pale honey, orange honey, amber, a few weathered grey-brown ones; dark wormy streaks
  and splits, small knots, strong open cathedral grain with fine pores, tight dark seams between boards.
- Satin finish (soft broad highlights, never mirror-like).

Geometry: one mesh of real boards (1.5 mm gaps over the black Floor_Under slab). Per-board randomness is stored in
float attributes (br1..3 = randoms, um/wm = across-board position/width, vm/lm = along-board position/length) that the
material reads, so the one merged mesh still shows 140 different boards. Float attributes are not exported to the GLB.
The floor gets its own bake group "Floor" (4096 px lightmap) so the grain stays sharp.
"""
import bpy, bmesh, math, random, os, importlib.util
from mathutils import Vector

_spec = importlib.util.spec_from_file_location("e04", os.path.join(os.path.dirname(os.path.abspath(__file__)), "e04_left_zone.py"))
e04 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(e04)
_node, _lin, _srgb = e04._node, e04._lin, e04._srgb

GAP = 0.0016
THICK = 0.019
Z_TOP = 0.001
WIDTHS = (0.13, 0.15, 0.17, 0.19, 0.22)
ATTRS = ("br1", "br2", "br3", "um", "wm", "vm", "lm")


def _bounds(o):
    xs = [v.co.x for v in o.data.vertices]; ys = [v.co.y for v in o.data.vertices]
    return min(xs), max(xs), min(ys), max(ys)


def _layout(x0, x1, y0, y1, seed=7):
    """Return boards: (bx0,bx1,by0,by1,r1,r2,r3)."""
    rnd = random.Random(seed)
    boards = []
    x = x0
    while x < x1 - 0.004:
        w = min(rnd.choice(WIDTHS), x1 - x)
        if x1 - (x + w) < 0.07:                     # no sliver at the last row
            w = x1 - x
        y = y0 - rnd.uniform(0.0, 1.4)
        while y < y1 - 0.004:
            L = rnd.uniform(0.9, 2.6)
            ya, yb = max(y, y0), min(y + L, y1)
            if yb - ya > 0.12:
                u = rnd.random()
                if u < 0.10:
                    r1 = rnd.uniform(0.86, 1.0)             # weathered dark board
                elif u < 0.28:
                    r1 = rnd.uniform(0.0, 0.18)             # pale honey
                elif u < 0.62:
                    r1 = rnd.uniform(0.28, 0.5)             # honey-orange
                else:
                    r1 = rnd.uniform(0.5, 0.78)             # amber / brown
                boards.append((x, x + w, ya, yb, r1, rnd.random(), rnd.random()))
            y += L
        x += w
    return boards


def _build_mesh(boards):
    bm = bmesh.new()
    lay = {a: bm.loops.layers.float.new(a) for a in ATTRS}
    z0, z1 = Z_TOP - THICK, Z_TOP
    for (bx0, bx1, by0, by1, r1, r2, r3) in boards:
        ax0, ax1, ay0, ay1 = bx0 + GAP / 2, bx1 - GAP / 2, by0 + GAP / 2, by1 - GAP / 2
        W, L = ax1 - ax0, ay1 - ay0
        P = {}
        for i, (x, y) in enumerate(((ax0, ay0), (ax1, ay0), (ax1, ay1), (ax0, ay1))):
            P[i] = (bm.verts.new((x, y, z1)), bm.verts.new((x, y, z0)))
        faces = [bm.faces.new([P[i][0] for i in (0, 1, 2, 3)])]
        for a, b in ((0, 1), (1, 2), (2, 3), (3, 0)):
            faces.append(bm.faces.new((P[a][0], P[a][1], P[b][1], P[b][0])))
        for f in faces:
            f.smooth = False
            for l in f.loops:
                p = l.vert.co
                l[lay["br1"]], l[lay["br2"]], l[lay["br3"]] = r1, r2, r3
                l[lay["um"]], l[lay["wm"]] = p.x - ax0, W
                l[lay["vm"]], l[lay["lm"]] = p.y - ay0, L
    bm.normal_update()
    me = bpy.data.meshes.new("Floor_Planks")
    bm.to_mesh(me); bm.free()
    for a in ATTRS:                                  # float CORNER attributes created above come across by name
        assert a in me.attributes, a
    return me


def _attr(nt, name):
    n = _node(nt, "ShaderNodeAttribute"); n.attribute_type = 'GEOMETRY'; n.attribute_name = name
    return n.outputs["Fac"]


def _math(nt, op, a, b=None, clamp=False):
    n = _node(nt, "ShaderNodeMath", operation=op)
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            _lin(nt, v, n.inputs[i])
    n.use_clamp = clamp
    return n.outputs[0]


def _vec(nt, x, y, z):
    n = _node(nt, "ShaderNodeCombineXYZ")
    for k, v in zip("XYZ", (x, y, z)):
        if isinstance(v, (int, float)):
            n.inputs[k].default_value = v
        else:
            _lin(nt, v, n.inputs[k])
    return n.outputs[0]


def _ramp(nt, fac, stops):
    n = _node(nt, "ShaderNodeValToRGB")
    el = n.color_ramp.elements
    while len(el) > len(stops):
        el.remove(el[-1])
    while len(el) < len(stops):
        el.new(0.5)
    for e, (p, c) in zip(el, stops):
        e.position = p; e.color = (*_srgb(c), 1) if isinstance(c, str) else c
    _lin(nt, fac, n.inputs["Fac"])
    return n.outputs["Color"]


def floor_mat():
    m = bpy.data.materials.get("FloorReclaimedOak")
    if m:
        return m
    m = bpy.data.materials.new("FloorReclaimedOak"); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    r1, r2, r3 = _attr(nt, "br1"), _attr(nt, "br2"), _attr(nt, "br3")
    um, wm, vm, lm = _attr(nt, "um"), _attr(nt, "wm"), _attr(nt, "vm"), _attr(nt, "lm")

    # ---- board tone
    tone = _ramp(nt, r1, [(0.00, "ecc277"), (0.22, "e2a444"), (0.45, "d68a2a"), (0.68, "b86a1e"),
                          (0.84, "8a5628"), (1.00, "755538")])

    # ---- cathedral grain: rings about the board's long axis, distorted, centre offset per board
    cx = _math(nt, 'ADD', _math(nt, 'MULTIPLY', um, 60.0), _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', r2, 0.5), 14.0))
    cz = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', r3, 0.5), 9.0)
    cy = _math(nt, 'ADD', _math(nt, 'MULTIPLY', vm, 4.5), _math(nt, 'MULTIPLY', r3, 40.0))
    wv = _node(nt, "ShaderNodeTexWave", wave_type='RINGS', rings_direction='Y', in_Scale=0.55, in_Distortion=11.0,
               in_Detail=3.5, in_Detail_Scale=1.2, in_Detail_Roughness=0.6)
    _lin(nt, _vec(nt, cx, cy, cz), wv.inputs["Vector"])
    grain = wv.outputs["Fac"]

    # ---- fine pores / fibre streaks, very stretched along the board
    px = _math(nt, 'MULTIPLY', um, 900.0)
    py = _math(nt, 'MULTIPLY', vm, 22.0)
    pz = _math(nt, 'MULTIPLY', r2, 60.0)
    fn = _node(nt, "ShaderNodeTexNoise", in_Scale=1.0, in_Detail=4.0, in_Roughness=0.62)
    _lin(nt, _vec(nt, px, py, pz), fn.inputs["Vector"])
    fine = fn.outputs["Fac"]

    gmix = _node(nt, "ShaderNodeMix", data_type='FLOAT'); gmix.inputs[0].default_value = 0.30
    _lin(nt, grain, gmix.inputs[2]); _lin(nt, fine, gmix.inputs[3])
    g = gmix.outputs[0]

    # grain darkens the board: multiply tone by (0.62 .. 1.08)
    gr = _node(nt, "ShaderNodeMapRange", in_From_Min=0.25, in_From_Max=0.78, in_To_Min=0.46, in_To_Max=1.18)
    _lin(nt, g, gr.inputs["Value"])
    mulc = _node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); mulc.inputs[0].default_value = 1.0
    _lin(nt, tone, mulc.inputs[6])
    gc = _node(nt, "ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"):
        _lin(nt, gr.outputs["Result"], gc.inputs[k])
    _lin(nt, gc.outputs["Color"], mulc.inputs[7])
    col = mulc.outputs[2]

    # ---- sapwood streak: a lighter, yellower band along some boards
    sw = _node(nt, "ShaderNodeTexNoise", in_Scale=1.0, in_Detail=2.0, in_Roughness=0.5)
    _lin(nt, _vec(nt, _math(nt, 'MULTIPLY', um, 9.0), _math(nt, 'MULTIPLY', vm, 0.9), _math(nt, 'MULTIPLY', r3, 30.0)), sw.inputs["Vector"])
    swm = _node(nt, "ShaderNodeMapRange", in_From_Min=0.55, in_From_Max=0.72, in_To_Min=0.0, in_To_Max=0.45)
    _lin(nt, sw.outputs["Fac"], swm.inputs["Value"])
    s1 = _node(nt, "ShaderNodeMix", data_type='RGBA'); s1.inputs[7].default_value = (*_srgb("e1b878"), 1)
    _lin(nt, swm.outputs["Result"], s1.inputs[0]); _lin(nt, col, s1.inputs[6])
    col = s1.outputs[2]

    # ---- dark wormy streaks and splits: thresholded noise stretched along the board
    wn = _node(nt, "ShaderNodeTexNoise", in_Scale=1.0, in_Detail=5.0, in_Roughness=0.6)
    _lin(nt, _vec(nt, _math(nt, 'MULTIPLY', um, 55.0), _math(nt, 'MULTIPLY', vm, 3.0), _math(nt, 'MULTIPLY', r2, 80.0)), wn.inputs["Vector"])
    wnm = _node(nt, "ShaderNodeMapRange", in_From_Min=0.62, in_From_Max=0.72, in_To_Min=0.0, in_To_Max=0.9, clamp=True)
    _lin(nt, wn.outputs["Fac"], wnm.inputs["Value"])
    s2 = _node(nt, "ShaderNodeMix", data_type='RGBA'); s2.inputs[7].default_value = (*_srgb("2a1a0e"), 1)
    _lin(nt, wnm.outputs["Result"], s2.inputs[0]); _lin(nt, col, s2.inputs[6])
    col = s2.outputs[2]

    # ---- small knots: a few per board, from a Voronoi distance field in board-local metres (z = r2 offset)
    vo = _node(nt, "ShaderNodeTexVoronoi", feature='F1', in_Scale=1.0)
    _lin(nt, _vec(nt, _math(nt, 'MULTIPLY', um, 5.5), _math(nt, 'MULTIPLY', vm, 1.7), _math(nt, 'MULTIPLY', r3, 90.0)), vo.inputs["Vector"])
    vk = _node(nt, "ShaderNodeMapRange", in_From_Min=0.17, in_From_Max=0.05, in_To_Min=0.0, in_To_Max=1.0, clamp=True)
    _lin(nt, vo.outputs["Distance"], vk.inputs["Value"])
    # knots only where the random cell is "active": cell colour channel decides (about 1 in 5)
    sx = _node(nt, "ShaderNodeSeparateColor"); _lin(nt, vo.outputs["Color"], sx.inputs["Color"])
    act = _node(nt, "ShaderNodeMath", operation='GREATER_THAN'); act.inputs[1].default_value = 0.8
    _lin(nt, sx.outputs["Red"], act.inputs[0])
    kn = _math(nt, 'MULTIPLY', vk.outputs["Result"], act.outputs[0])
    s3 = _node(nt, "ShaderNodeMix", data_type='RGBA'); s3.inputs[7].default_value = (*_srgb("3a2410"), 1)
    _lin(nt, kn, s3.inputs[0]); _lin(nt, col, s3.inputs[6])
    col = s3.outputs[2]

    # ---- seams: dark line along every board edge (the 1.5 mm gaps are narrower than a lightmap texel)
    ex = _math(nt, 'MINIMUM', um, _math(nt, 'SUBTRACT', wm, um))
    ey = _math(nt, 'MINIMUM', vm, _math(nt, 'SUBTRACT', lm, vm))
    ed = _math(nt, 'MINIMUM', ex, ey)
    sm = _node(nt, "ShaderNodeMapRange", in_From_Min=0.0, in_From_Max=0.0035, in_To_Min=0.12, in_To_Max=1.0, clamp=True)
    _lin(nt, ed, sm.inputs["Value"])
    s4 = _node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); s4.inputs[0].default_value = 1.0
    sg = _node(nt, "ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"):
        _lin(nt, sm.outputs["Result"], sg.inputs[k])
    _lin(nt, col, s4.inputs[6]); _lin(nt, sg.outputs["Color"], s4.inputs[7])
    col = s4.outputs[2]

    # ---- gentle large-scale wear: foot-traffic dulls and slightly greys a few areas
    tc = _node(nt, "ShaderNodeTexCoord")
    wr = _node(nt, "ShaderNodeTexNoise", in_Scale=0.8, in_Detail=4.0, in_Roughness=0.6)
    _lin(nt, tc.outputs["Object"], wr.inputs["Vector"])
    wrm = _node(nt, "ShaderNodeMapRange", in_From_Min=0.5, in_From_Max=0.85, in_To_Min=0.0, in_To_Max=0.14)
    _lin(nt, wr.outputs["Fac"], wrm.inputs["Value"])
    s5 = _node(nt, "ShaderNodeMix", data_type='RGBA'); s5.inputs[7].default_value = (*_srgb("8a6a48"), 1)
    _lin(nt, wrm.outputs["Result"], s5.inputs[0]); _lin(nt, col, s5.inputs[6])
    _lin(nt, s5.outputs[2], bs.inputs["Base Color"])

    # ---- surface: satin, broader and softer where worn; grain + seams as bump
    rough = _node(nt, "ShaderNodeMapRange", in_From_Min=0.0, in_From_Max=1.0, in_To_Min=0.36, in_To_Max=0.55)
    _lin(nt, _math(nt, 'ADD', _math(nt, 'MULTIPLY', fine, 0.6), wrm.outputs["Result"]), rough.inputs["Value"])
    _lin(nt, rough.outputs["Result"], bs.inputs["Roughness"])
    bs.inputs["Specular IOR Level"].default_value = 0.55
    bs.inputs["Coat Weight"].default_value = 0.18; bs.inputs["Coat Roughness"].default_value = 0.25
    bm = _node(nt, "ShaderNodeBump", in_Strength=0.45, in_Distance=0.0015)
    _lin(nt, _math(nt, 'MULTIPLY', _math(nt, 'ADD', g, sm.outputs["Result"]), 0.5), bm.inputs["Height"])
    _lin(nt, bm.outputs["Normal"], bs.inputs["Normal"])
    return m


def apply():
    D = bpy.data
    old = D.objects["Floor_Planks"]
    x0, x1, y0, y1 = _bounds(old)
    boards = _layout(x0, x1, y0, y1)
    me = _build_mesh(boards)
    me.materials.append(floor_mat())
    mw = old.matrix_world.copy()
    D.objects.remove(old, do_unlink=True)
    new = D.objects.new("Floor_Planks", me); new.matrix_world = mw
    for p in me.polygons:
        p.use_smooth = False
    coll = D.collections.get("Floor")
    if not coll:
        coll = D.collections.new("Floor")
        bpy.context.scene.collection.children.link(coll)
    coll.objects.link(new)
    bpy.context.view_layer.update()
    print("e09: floor rebuilt with", len(boards), "boards, polys", len(me.polygons))


if __name__ == "__main__":                         # standalone: python3 e09_floor.py <in.blend> <out.blend>
    import sys
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    bpy.ops.wm.open_mainfile(filepath=a[0]); apply()
    bpy.ops.wm.save_as_mainfile(filepath=a[1], compress=True)
