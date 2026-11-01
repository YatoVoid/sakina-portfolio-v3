"""Edit #4 (round 3, user 2026-10-31): left zone realism + spacing.

Reference: Felix Laurent's room, ref B (beige computer on a wooden dresser, keyboard beside the unit, photo stuck
on the monitor corner, postcard collage + wall clock above). Used as a quality benchmark, not copied 1:1.

a) Spacing: the left wall moves 0.70 m toward the centre (x -3.00 -> -2.30). The gap between the left furniture
   and the desk's left end (x -1.25) drops from ~1.3 m to ~0.55 m ("moderate, not a huge gap"). Floor, ceiling,
   back/front walls and baseboards are trimmed to the new wall; the socket moves with it.
b) Dresser: replaces the small two-drawer cabinet. 1.05 m wide, 0.47 m deep, 0.76 m tall; framed front with
   3 short + 2x2 deep drawers, brass bail pulls, overhanging top with a rounded edge, plinth base. Procedural
   wood grain that follows each board (top/drawers/rails horizontal, stiles/sides vertical), per-board tone
   variation, varnish coat.
c) Computer: the IBM unit + monitor (e03) moves to the right end of the dresser, the keyboard to its left (as in
   ref B). Added: vent grille on the monitor top, aged plastic (yellowed, grime in crevices via AO, stipple
   texture), the polaroid restored on the bezel corner with a piece of tape, new cables.
d) Postcards: 20 real-looking postcards (white borders, aged photos with vignette, curled corners standing off
   the wall so they cast contact shadows, irregular tilt and spacing, some taped) in a 5 x 4 collage above the
   computer. Same photos as before.
e) Wall clock: chrome rim, numerals, minute ticks, red second hand.
f) Back-wall keepsakes (degrees, flags) slide right so they still fit between the new corner and the curtain.
Front of the left furniture faces +X (into the room).
"""
import bpy, bmesh, math, random, os, importlib.util
from mathutils import Vector, Matrix

_spec = importlib.util.spec_from_file_location("e03", os.path.join(os.path.dirname(os.path.abspath(__file__)), "e03_ibm_corner.py"))
e03 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(e03)
Builder, _mat, _srgb = e03.Builder, e03._mat, e03._srgb

OLD_WALL, WALL_X = -3.00, -2.30
DX = WALL_X - OLD_WALL

# Dresser box (world, metres)
DR_BACK, DR_FRONT = WALL_X + 0.025, WALL_X + 0.485
DR_Y0, DR_Y1, DR_TOP = 1.40, 2.45, 0.76
UNIT_CY, UNIT_FRONT = 2.18, DR_FRONT - 0.05
KB_CY, KB_FRONT = 1.665, DR_FRONT - 0.025


# ----------------------------------------------------------------------------------------------- helpers
def _wb(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return Vector([min(p[k] for p in pts) for k in range(3)]), Vector([max(p[k] for p in pts) for k in range(3)])


def _wb_many(objs):
    bs = [_wb(o) for o in objs]
    return (Vector([min(b[0][k] for b in bs) for k in range(3)]), Vector([max(b[1][k] for b in bs) for k in range(3)]))


def _single_user(o):
    if o.data.users > 1:
        o.data = o.data.copy()


def _translate(o, d):
    mw = o.matrix_world.copy(); mw.translation += d; o.matrix_world = mw


def _node(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        if k.startswith("in_"):
            n.inputs[k[3:].replace("_", " ")].default_value = v
        else:
            setattr(n, k, v)
    return n


def _lin(nt, a, b):
    nt.links.new(a, b)


# ----------------------------------------------------------------------------------------------- materials
def wood_mat(name, axis, cols, ring_scale=7.0, rough=(0.38, 0.62), coat=0.15):
    """Procedural board: rings around `axis` (so the grain runs along it), distorted; fine pores stretched
    along the axis; per-object random offset/tone so neighbouring boards differ."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    tc = _node(nt, "ShaderNodeTexCoord"); oi = _node(nt, "ShaderNodeObjectInfo")
    rv = _node(nt, "ShaderNodeVectorMath", operation='MULTIPLY'); rv.inputs[1].default_value = (13.1, 7.3, 11.7)
    _lin(nt, oi.outputs["Random"], rv.inputs[0])
    add = _node(nt, "ShaderNodeVectorMath", operation='ADD')
    _lin(nt, tc.outputs["Object"], add.inputs[0]); _lin(nt, rv.outputs[0], add.inputs[1])
    ax = "XYZ".index(axis)
    s1 = [1.0, 1.0, 1.0]; s1[ax] = 0.18
    mp = _node(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = s1
    _lin(nt, add.outputs[0], mp.inputs["Vector"])
    wv = _node(nt, "ShaderNodeTexWave", wave_type='RINGS', rings_direction=axis,
               in_Scale=ring_scale, in_Distortion=7.0, in_Detail=4.0, in_Detail_Scale=1.3, in_Detail_Roughness=0.55)
    _lin(nt, mp.outputs[0], wv.inputs["Vector"])
    s2 = [70.0, 70.0, 70.0]; s2[ax] = 0.9
    mp2 = _node(nt, "ShaderNodeMapping"); mp2.inputs["Scale"].default_value = s2
    _lin(nt, add.outputs[0], mp2.inputs["Vector"])
    fn = _node(nt, "ShaderNodeTexNoise", in_Scale=1.0, in_Detail=3.0, in_Roughness=0.6)
    _lin(nt, mp2.outputs[0], fn.inputs["Vector"])
    mix = _node(nt, "ShaderNodeMix", data_type='FLOAT'); mix.inputs[0].default_value = 0.32
    _lin(nt, wv.outputs["Fac"], mix.inputs[2]); _lin(nt, fn.outputs["Fac"], mix.inputs[3])
    ramp = _node(nt, "ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.25, (*_srgb(cols[0]), 1)
    el[1].position, el[1].color = 0.75, (*_srgb(cols[2]), 1)
    e = el.new(0.52); e.color = (*_srgb(cols[1]), 1)
    _lin(nt, mix.outputs[0], ramp.inputs["Fac"])
    # per-board tone: lerp toward a slightly darker/redder version by the object's random value
    tone = _node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY')
    tone.inputs[7].default_value = (0.82, 0.74, 0.68, 1)
    mr = _node(nt, "ShaderNodeMath", operation='MULTIPLY'); mr.inputs[1].default_value = 0.8
    _lin(nt, oi.outputs["Random"], mr.inputs[0]); _lin(nt, mr.outputs[0], tone.inputs[0])
    _lin(nt, ramp.outputs["Color"], tone.inputs[6])
    # wear: big soft blotches slightly lighter/duller (handled, sun-faded wood)
    wn = _node(nt, "ShaderNodeTexNoise", in_Scale=3.5, in_Detail=2.0)
    _lin(nt, tc.outputs["Object"], wn.inputs["Vector"])
    wr = _node(nt, "ShaderNodeMapRange", in_From_Min=0.45, in_From_Max=0.75, in_To_Min=0.0, in_To_Max=0.22)
    _lin(nt, wn.outputs["Fac"], wr.inputs["Value"])
    wear = _node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MIX')
    wear.inputs[7].default_value = (*_srgb("a77b52"), 1)
    _lin(nt, wr.outputs["Result"], wear.inputs[0]); _lin(nt, tone.outputs[2], wear.inputs[6])
    _lin(nt, wear.outputs[2], bs.inputs["Base Color"])
    rr = _node(nt, "ShaderNodeMapRange", in_To_Min=rough[0], in_To_Max=rough[1])
    _lin(nt, fn.outputs["Fac"], rr.inputs["Value"])
    radd = _node(nt, "ShaderNodeMath", operation='ADD', use_clamp=True)
    _lin(nt, rr.outputs["Result"], radd.inputs[0]); _lin(nt, wr.outputs["Result"], radd.inputs[1])
    _lin(nt, radd.outputs[0], bs.inputs["Roughness"])
    bp = _node(nt, "ShaderNodeBump", in_Strength=0.08, in_Distance=0.0015)
    _lin(nt, mix.outputs[0], bp.inputs["Height"]); _lin(nt, bp.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Coat Weight"].default_value = coat; bs.inputs["Coat Roughness"].default_value = 0.3
    return m


def aged_plastic(name, base_hex, yellow_hex, rough=0.5, grime=0.55):
    """Rebuild a plastic material as aged beige: uneven yellowing, darker grime in crevices (AO),
    fine stipple texture, slightly uneven gloss."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    bs = _node(nt, "ShaderNodeBsdfPrincipled"); _lin(nt, bs.outputs[0], out.inputs["Surface"])
    tc = _node(nt, "ShaderNodeTexCoord")
    ny = _node(nt, "ShaderNodeTexNoise", in_Scale=6.0, in_Detail=3.0)
    _lin(nt, tc.outputs["Object"], ny.inputs["Vector"])
    yr = _node(nt, "ShaderNodeMapRange", in_From_Min=0.35, in_From_Max=0.7)
    _lin(nt, ny.outputs["Fac"], yr.inputs["Value"])
    col = _node(nt, "ShaderNodeMix", data_type='RGBA')
    col.inputs[6].default_value = (*_srgb(base_hex), 1); col.inputs[7].default_value = (*_srgb(yellow_hex), 1)
    _lin(nt, yr.outputs["Result"], col.inputs[0])
    ao = _node(nt, "ShaderNodeAmbientOcclusion", samples=8, in_Distance=0.015)
    gr = _node(nt, "ShaderNodeMapRange", in_From_Min=0.0, in_From_Max=1.0, in_To_Min=grime, in_To_Max=1.0)
    _lin(nt, ao.outputs["AO"], gr.inputs["Value"])
    dirt = _node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); dirt.inputs[0].default_value = 1.0
    _lin(nt, col.outputs[2], dirt.inputs[6])
    cg = _node(nt, "ShaderNodeCombineColor")
    for i in range(3):
        _lin(nt, gr.outputs["Result"], cg.inputs[i])
    _lin(nt, cg.outputs[0], dirt.inputs[7])
    _lin(nt, dirt.outputs[2], bs.inputs["Base Color"])
    rn = _node(nt, "ShaderNodeTexNoise", in_Scale=25.0, in_Detail=2.0)
    _lin(nt, tc.outputs["Object"], rn.inputs["Vector"])
    rr = _node(nt, "ShaderNodeMapRange", in_To_Min=rough - 0.08, in_To_Max=rough + 0.12)
    _lin(nt, rn.outputs["Fac"], rr.inputs["Value"]); _lin(nt, rr.outputs["Result"], bs.inputs["Roughness"])
    st = _node(nt, "ShaderNodeTexNoise", in_Scale=1800.0, in_Detail=1.0)
    _lin(nt, tc.outputs["Object"], st.inputs["Vector"])
    bp = _node(nt, "ShaderNodeBump", in_Strength=0.035, in_Distance=0.0004)
    _lin(nt, st.outputs["Fac"], bp.inputs["Height"]); _lin(nt, bp.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Specular IOR Level"].default_value = 0.45
    return m


def simple_mat(name, hexcol, rough=0.5, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    bs = m.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*_srgb(hexcol), 1)
    bs.inputs["Roughness"].default_value = rough; bs.inputs["Metallic"].default_value = metal
    if emit:
        bs.inputs["Emission Color"].default_value = (*_srgb(emit), 1); bs.inputs["Emission Strength"].default_value = strength
    return m


def brass_mat():
    m = bpy.data.materials.get("AgedBrass")
    if m:
        return m
    m = bpy.data.materials.new("AgedBrass"); m.use_nodes = True; nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]; bs.inputs["Metallic"].default_value = 1.0
    tc = _node(nt, "ShaderNodeTexCoord"); nz = _node(nt, "ShaderNodeTexNoise", in_Scale=220.0, in_Detail=4.0)
    _lin(nt, tc.outputs["Object"], nz.inputs["Vector"])
    c = _node(nt, "ShaderNodeMix", data_type='RGBA'); c.inputs[6].default_value = (*_srgb("b08d4a"), 1)
    c.inputs[7].default_value = (*_srgb("6b5328"), 1)
    _lin(nt, nz.outputs["Fac"], c.inputs[0]); _lin(nt, c.outputs[2], bs.inputs["Base Color"])
    r = _node(nt, "ShaderNodeMapRange", in_To_Min=0.28, in_To_Max=0.55)
    _lin(nt, nz.outputs["Fac"], r.inputs["Value"]); _lin(nt, r.outputs["Result"], bs.inputs["Roughness"])
    return m


def paper_mat():
    m = bpy.data.materials.get("PostcardPaper")
    if m:
        return m
    m = bpy.data.materials.new("PostcardPaper"); m.use_nodes = True; nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]; bs.inputs["Roughness"].default_value = 0.85
    tc = _node(nt, "ShaderNodeTexCoord"); nz = _node(nt, "ShaderNodeTexNoise", in_Scale=40.0, in_Detail=6.0)
    _lin(nt, tc.outputs["Object"], nz.inputs["Vector"])
    c = _node(nt, "ShaderNodeMix", data_type='RGBA'); c.inputs[6].default_value = (*_srgb("ece4d0"), 1)
    c.inputs[7].default_value = (*_srgb("d4c29c"), 1)
    r = _node(nt, "ShaderNodeMapRange", in_From_Min=0.4, in_From_Max=0.8)
    _lin(nt, nz.outputs["Fac"], r.inputs["Value"]); _lin(nt, r.outputs["Result"], c.inputs[0])
    _lin(nt, c.outputs[2], bs.inputs["Base Color"])
    return m


def aged_photo(src):
    """Copy of a postcard photo material: faded, warmer, slightly desaturated, vignetted print."""
    name = "PC_" + src.name
    m = bpy.data.materials.get(name)
    if m:
        return m
    img = next(n.image for n in src.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image)
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]; bs.inputs["Roughness"].default_value = 0.55
    bs.inputs["Specular IOR Level"].default_value = 0.35
    uv = _node(nt, "ShaderNodeUVMap", uv_map="UVMap"); tx = _node(nt, "ShaderNodeTexImage", image=img)
    _lin(nt, uv.outputs["UV"], tx.inputs["Vector"])
    hs = _node(nt, "ShaderNodeHueSaturation", in_Saturation=0.72, in_Value=0.92)
    _lin(nt, tx.outputs["Color"], hs.inputs["Color"])
    warm = _node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); warm.inputs[0].default_value = 0.55
    warm.inputs[7].default_value = (1.0, 0.86, 0.66, 1)
    _lin(nt, hs.outputs["Color"], warm.inputs[6])
    fade = _node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MIX'); fade.inputs[0].default_value = 0.12
    fade.inputs[7].default_value = (*_srgb("d8cfb8"), 1)
    _lin(nt, warm.outputs[2], fade.inputs[6])
    cuv = _node(nt, "ShaderNodeUVMap", uv_map="Card")
    dist = _node(nt, "ShaderNodeVectorMath", operation='DISTANCE'); dist.inputs[1].default_value = (0.5, 0.5, 0)
    _lin(nt, cuv.outputs["UV"], dist.inputs[0])
    vg = _node(nt, "ShaderNodeMapRange", in_From_Min=0.35, in_From_Max=0.75, in_To_Min=1.0, in_To_Max=0.72)
    _lin(nt, dist.outputs["Value"], vg.inputs["Value"])
    vm = _node(nt, "ShaderNodeMix", data_type='RGBA', blend_type='MULTIPLY'); vm.inputs[0].default_value = 1.0
    cc = _node(nt, "ShaderNodeCombineColor")
    for i in range(3):
        _lin(nt, vg.outputs["Result"], cc.inputs[i])
    _lin(nt, fade.outputs[2], vm.inputs[6]); _lin(nt, cc.outputs[0], vm.inputs[7])
    _lin(nt, vm.outputs[2], bs.inputs["Base Color"])
    return m


# ----------------------------------------------------------------------------------------------- a) wall
def _move_wall():
    D = bpy.data
    for n in ("Wall_Left", "Baseboard_Left", "Baseboard_LeftCap", "Socket_Left", "Socket_LeftPlug"):
        D.objects[n].location.x += DX
    for n in ("Floor_Planks", "Floor_Under", "Ceiling", "Wall_Back_L", "Baseboard_Back", "Baseboard_BackCap",
              "Wall_Front", "Room_Volume"):
        o = D.objects[n]; _single_user(o)
        mw = o.matrix_world; inv = mw.inverted()
        for v in o.data.vertices:
            w = mw @ v.co
            if w.x <= OLD_WALL + 0.002:          # outer boundary: shift with the wall
                w.x += DX
            elif w.x < WALL_X:                   # interior verts now behind the wall (plank joints): clamp
                w.x = WALL_X
            else:
                continue
            v.co = inv @ w
        o.data.update()
    for n in ("Wire_PC_Power", "Wire_CRT2_Power", "Wire_PC_Monitor", "Wire_PC_Keyboard"):
        if D.objects.get(n):
            D.objects.remove(D.objects[n], do_unlink=True)


# ----------------------------------------------------------------------------------------------- b) dresser
def _dresser(B):
    wy = wood_mat("DresserWoodY", 'Y', ("5a3119", "7d4526", "98603a"))
    wz = wood_mat("DresserWoodZ", 'Z', ("5a3119", "7d4526", "98603a"))
    wx = wood_mat("DresserWoodX", 'X', ("5a3119", "7d4526", "98603a"))
    dark = wood_mat("DresserWoodDark", 'Y', ("2a160b", "3b2112", "4d2c18"), coat=0.0)
    brass = brass_mat()
    F, K = DR_FRONT, DR_BACK
    y0, y1, top = DR_Y0, DR_Y1, DR_TOP
    slab = 0.032
    # carcass core (seen only through the drawer gaps)
    B.box("Dresser_Core", (K, y0 + 0.02, 0.075), (F - 0.021, y1 - 0.02, top - slab), dark)
    # sides (vertical grain), top (overhang, rounded front edge), moulding under the top, plinth
    B.box("Dresser_Side_L", (K, y0, 0.06), (F, y0 + 0.022, top - slab), wz, bevel=0.002)
    B.box("Dresser_Side_R", (K, y1 - 0.022, 0.06), (F, y1, top - slab), wz, bevel=0.002)
    B.box("Dresser_Top", (K - 0.004, y0 - 0.014, top - slab), (F + 0.016, y1 + 0.014, top), wy, bevel=0.009, seg=4)
    B.box("Dresser_TopMould", (K, y0 - 0.004, top - slab - 0.012), (F + 0.007, y1 + 0.004, top - slab), wy, bevel=0.004, seg=3)
    B.box("Dresser_Plinth", (K + 0.01, y0 + 0.012, 0.0), (F - 0.022, y1 - 0.012, 0.062), dark, bevel=0.003)
    B.box("Dresser_BaseMould", (K, y0 - 0.003, 0.052), (F + 0.004, y1 + 0.003, 0.075), wy, bevel=0.005, seg=3)
    # face frame: rails (horizontal grain) and stiles (vertical grain), 2 cm thick
    fx0 = F - 0.02
    rails = [(0.075, 0.097), (0.307, 0.329), (0.534, 0.556), (top - slab - 0.022, top - slab)]
    for i, (za, zb) in enumerate(rails):
        B.box(f"Dresser_Rail_{i}", (fx0, y0 + 0.022, za), (F, y1 - 0.022, zb), wy, bevel=0.0015)
    st = 0.03
    B.box("Dresser_Stile_L", (fx0, y0, 0.075), (F + 0.0005, y0 + st, top - slab), wz, bevel=0.0015)
    B.box("Dresser_Stile_R", (fx0, y1 - st, 0.075), (F + 0.0005, y1, top - slab), wz, bevel=0.0015)
    iy0, iy1 = y0 + st, y1 - st
    rows = [((0.097, 0.307), 2), ((0.329, 0.534), 2), ((0.556, top - slab - 0.022), 3)]   # bottom -> top
    n = 0
    for (za, zb), cols in rows:
        sw = 0.022
        w = (iy1 - iy0 - sw * (cols - 1)) / cols
        for c in range(cols):
            ya = iy0 + c * (w + sw); yb = ya + w
            if c < cols - 1:
                B.box(f"Dresser_Mullion_{n}_{c}", (fx0, yb, za), (F, yb + sw, zb), wz, bevel=0.0015)
            cl = 0.0028
            B.box(f"Dresser_Drawer_{n}", (F - 0.024, ya + cl, za + cl), (F - 0.0025, yb - cl, zb - cl), wy, bevel=0.004, seg=2)
            # brass bail pull, centred (slightly above centre on deep drawers)
            cy, cz = (ya + yb) / 2, (za + zb) / 2 + (0.012 if zb - za > 0.18 else 0.0)
            fx = F - 0.0025
            B.box(f"Dresser_PullPlate_{n}", (fx - 0.001, cy - 0.046, cz - 0.013), (fx + 0.0018, cy + 0.046, cz + 0.017), brass, bevel=0.0012)
            for s in (-1, 1):
                B.cyl(f"Dresser_PullPost_{n}_{s}", (fx + 0.006, cy + s * 0.034, cz + 0.007), 0.0035, 0.009, 'X', brass, verts=12)
            cu = bpy.data.curves.new(f"Dresser_Bail_{n}", 'CURVE'); cu.dimensions = '3D'
            cu.bevel_depth = 0.0026; cu.bevel_resolution = 2; cu.resolution_u = 6
            sp = cu.splines.new('NURBS'); pts = [(fx + 0.009, cy - 0.034, cz + 0.007), (fx + 0.013, cy - 0.034, cz - 0.006),
                                                 (fx + 0.015, cy - 0.026, cz - 0.014), (fx + 0.015, cy + 0.026, cz - 0.014),
                                                 (fx + 0.013, cy + 0.034, cz - 0.006), (fx + 0.009, cy + 0.034, cz + 0.007)]
            sp.points.add(len(pts) - 1)
            for p, q in zip(sp.points, pts):
                p.co = (*q, 1)
            sp.order_u = 3; sp.use_endpoint_u = True
            bo = bpy.data.objects.new(f"Dresser_Bail_{n}", cu); bo.data.materials.append(brass)
            B.coll.objects.link(bo); B.objs.append(bo)
            if cols == 3 and c == 1:                      # keyhole escutcheon on the middle top drawer
                B.box(f"Dresser_Escutcheon", (fx - 0.0005, cy - 0.007, cz - 0.040), (fx + 0.0012, cy + 0.007, cz - 0.020), brass, bevel=0.001)
                B.box(f"Dresser_Keyhole", (fx + 0.0011, cy - 0.0018, cz - 0.034), (fx + 0.0016, cy + 0.0018, cz - 0.025), simple_mat("KeyholeBlack", "0b0907", 0.8))
            n += 1


# ----------------------------------------------------------------------------------------------- c) computer
def _computer(B, root):
    D = bpy.data
    kids = list(root.children_recursive)
    if D.objects.get("IBM_KB_Cord"):
        D.objects.remove(D.objects["IBM_KB_Cord"], do_unlink=True)
    kids = [o for o in root.children_recursive]
    kb = [o for o in kids if o.name.startswith("IBM_KB_")]
    unit = [o for o in kids if (o.name.startswith("IBM_") and not o.name.startswith("IBM_KB_")) or o.name.startswith("Term")]
    u0, u1 = _wb(D.objects["IBM_Unit"])
    d_unit = Vector((UNIT_FRONT - u1.x, UNIT_CY - (u0.y + u1.y) / 2, DR_TOP - u0.z))
    for o in unit:
        if o.parent not in unit:                          # children of moved parents follow them
            _translate(o, d_unit)
    D.objects["L5_IBM_Screen"].location += d_unit
    k0, k1 = _wb(D.objects["IBM_KB_Case"])
    d_kb = Vector((KB_FRONT - k1.x, KB_CY - (k0.y + k1.y) / 2, DR_TOP - k0.z))
    for o in kb:
        if o.parent not in kb:
            _translate(o, d_kb)
    bpy.context.view_layer.update()

    # aged plastic on every beige part, darker keys aged too
    aged_plastic("IBMBeige", "cdc2a5", "bfae86", rough=0.5)
    aged_plastic("IBMBeigeDark", "b3a98f", "a4946f", rough=0.55)
    aged_plastic("IBMKeyLight", "d6cdb6", "c9b88f", rough=0.45, grime=0.5)
    aged_plastic("IBMKeyDark", "8b877d", "7f786a", rough=0.45, grime=0.5)

    black = D.materials["IBMBlack"]; beige2 = D.materials["IBMBeigeDark"]
    mb0, mb1 = _wb(D.objects["IBM_Mon_Back"]); bz0, bz1 = _wb(D.objects["IBM_Bezel_T"])
    sy = (mb0.y + mb1.y) / 2
    # vent grille on the monitor's top (ref B): recessed plate + 15 dark slots
    ztop = mb1.z
    gx0, gx1 = bz0.x - 0.17, bz0.x - 0.045
    B.box("IBM_Mon_VentPlate", (gx0 - 0.006, sy - 0.112, ztop - 0.002), (gx1 + 0.006, sy + 0.112, ztop + 0.0012), beige2, bevel=0.002)
    for i in range(15):
        y = sy - 0.098 + i * 0.014
        B.box(f"IBM_Mon_Vent_{i}", (gx0, y - 0.0028, ztop + 0.0008), (gx1, y + 0.0028, ztop + 0.0016), black)
    # side vents on the monitor's left flank (visible from the room)
    for i in range(9):
        z = (mb0.z + mb1.z) / 2 - 0.05 + i * 0.012
        B.box(f"IBM_Mon_SideVent_{i}", (mb0.x + 0.05, mb0.y - 0.0016, z), (mb0.x + 0.15, mb0.y + 0.0005, z + 0.004), black)
    # front-panel seam + rear seam on the system unit, two screws on the side
    u0, u1 = _wb(D.objects["IBM_Unit"])
    B.box("IBM_Unit_SideSeam", (u0.x + 0.02, u0.y - 0.0012, u0.z + 0.004), (u1.x - 0.035, u0.y + 0.0005, u0.z + 0.0055), beige2)
    B.box("IBM_Unit_FrontSeam", (u1.x - 0.036, u0.y - 0.0012, u0.z + 0.004), (u1.x - 0.034, u0.y + 0.0005, u1.z - 0.004), beige2)
    # rubber feet so the unit and keyboard sit ON the dresser (visible contact shadow line)
    feet = simple_mat("RubberFoot", "1a1816", 0.9)
    for fx in (u0.x + 0.03, u1.x - 0.03):
        for fy in (u0.y + 0.03, u1.y - 0.03):
            B.cyl(f"IBM_Unit_Foot_{fx:.2f}_{fy:.2f}", (fx, fy, DR_TOP + 0.002), 0.008, 0.004, 'Z', feet, verts=12)
    return d_unit, d_kb, sy


def _polaroid(B, root):
    D = bpy.data
    pol = D.objects.get("Polaroid")
    if not pol:
        return
    for o in list(D.objects):
        if o.name.startswith("Pin_"):
            D.objects.remove(o, do_unlink=True)
    bt0, bt1 = _wb(D.objects["IBM_Bezel_T"]); br0, br1 = _wb(D.objects["IBM_Bezel_R"])
    front = bt1.x
    # face +X (it faced +Y on the old monitor), small tilt, overlapping the bezel's top-right corner
    old_rot = pol.matrix_world.to_3x3().normalized().to_4x4()   # it already faced +X on the old monitor
    tilt = Matrix.Rotation(math.radians(-7), 4, 'X')
    pos = Vector((front + 0.0015, br1.y - 0.028, bt1.z - 0.072))
    ph = D.objects["Polaroid_Photo"]; bd = D.objects["Polaroid_Border"]
    for ang in (0, 180):
        pol.matrix_world = Matrix.Translation(pos) @ tilt @ Matrix.Rotation(math.radians(ang), 4, 'Z') @ old_rot
        bpy.context.view_layer.update()
        if _wb(ph)[1].x >= _wb(bd)[1].x - 1e-5:          # photo in front of the card, facing the room
            break
    p0, p1 = _wb_many([ph, bd])
    tape = D.materials.get("PosterTape") or simple_mat("PosterTape", "e8e2c8", 0.4)
    B.box("Polaroid_Tape", (p1.x - 0.0002, (p0.y + p1.y) / 2 - 0.02, p1.z - 0.008), (p1.x + 0.0008, (p0.y + p1.y) / 2 + 0.02, p1.z + 0.01), tape)
    print("polaroid at", tuple(round(v, 3) for v in p0), tuple(round(v, 3) for v in p1))


def _cables(B, d_unit, d_kb, sy):
    D = bpy.data
    black = D.materials["IBMBlack"]
    u0, u1 = _wb(D.objects["IBM_Unit"]); k0, k1 = _wb(D.objects["IBM_KB_Case"])
    sk0, sk1 = _wb(D.objects["Socket_Left"])

    def curve(name, pts, r, coil=0.0, turns=0):
        cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.resolution_u = 3
        sp = cu.splines.new('NURBS')
        if coil:
            dense = []
            for i in range(len(pts) - 1):
                a, b = Vector(pts[i]), Vector(pts[i + 1])
                for j in range(40):
                    dense.append(a.lerp(b, j / 40))
            dense.append(Vector(pts[-1]))
            out = []
            for i, p in enumerate(dense):
                t = i / (len(dense) - 1); ang = t * 2 * math.pi * turns
                nxt = dense[min(i + 1, len(dense) - 1)] - dense[max(i - 1, 0)]
                side = Vector((0, 0, 1)).cross(nxt).normalized(); up = nxt.normalized().cross(side)
                out.append(p + side * coil * math.cos(ang) + up * coil * math.sin(ang))
            pts = out
        sp.points.add(len(pts) - 1)
        for p, q in zip(sp.points, pts):
            p.co = (*q, 1)
        sp.order_u = 3; sp.use_endpoint_u = True
        o = bpy.data.objects.new(name, cu); o.data.materials.append(black); B.coll.objects.link(o); B.objs.append(o)

    z = DR_TOP + 0.006
    # coiled keyboard cord: from the keyboard's back edge, along the dresser top, into the unit's left side
    curve("IBM_KB_Cord", [(k0.x + 0.01, k1.y - 0.06, z), (k0.x - 0.05, k1.y - 0.02, z), (u0.x + 0.03, u0.y - 0.035, z),
                          (u0.x + 0.06, u0.y - 0.004, z + 0.02)], 0.0016, coil=0.0045, turns=40)
    # power cable: unit back -> over the dresser's back edge -> down behind it -> wall socket
    curve("IBM_Power_Cable", [(u0.x + 0.004, u1.y - 0.05, u0.z + 0.04), (u0.x - 0.03, u1.y - 0.04, u0.z + 0.03),
                              (DR_BACK - 0.004, sk1.y - 0.04, DR_TOP - 0.05), (WALL_X + 0.012, sk1.y - 0.04, 0.42),
                              (sk1.x + 0.012, (sk0.y + sk1.y) / 2, (sk0.z + sk1.z) / 2)], 0.0035)
    # monitor cable: monitor back -> unit back
    mb0, mb1 = _wb(D.objects["IBM_Mon_Back2"])
    curve("IBM_Mon_Cable", [(mb0.x + 0.01, sy + 0.04, mb0.z + 0.03), (mb0.x - 0.04, sy + 0.06, mb0.z - 0.02),
                            (u0.x - 0.02, sy + 0.09, u0.z + 0.06), (u0.x + 0.004, sy + 0.12, u0.z + 0.05)], 0.003)


# ----------------------------------------------------------------------------------------------- d) postcards
def _postcards():
    D = bpy.data
    coll = D.collections["Wall_Decor"]
    old = sorted([o for o in coll.all_objects if o.parent is None and o.name.startswith("Postcard_")], key=lambda o: o.name)
    photos = []
    for o in old:
        ph = next((c for c in o.children if c.material_slots and c.material_slots[0].material), None)
        photos.append(ph.material_slots[0].material if ph else None)
    for o in old:
        for c in list(o.children_recursive):
            D.objects.remove(c, do_unlink=True)
        D.objects.remove(o, do_unlink=True)
    paper = paper_mat()
    tape = D.materials.get("PosterTape") or simple_mat("PosterTape", "e8e2c8", 0.4)
    rng = random.Random(1994)
    COLS, ROWS = 5, 4
    cw, ch = 0.190, 0.130
    y_start, z_top = 1.468, 1.925
    nu, nv = 10, 7
    order = 0
    for r in range(ROWS):
        for c in range(COLS):
            i = r * COLS + c
            src = photos[i % len(photos)]
            w = cw * rng.uniform(0.94, 1.04); h = ch * rng.uniform(0.94, 1.04)
            cy = y_start + c * (cw + 0.006) + cw / 2 + rng.uniform(-0.007, 0.007) + (0.012 if r % 2 else 0.0)
            cz = z_top - r * (ch + 0.012) - ch / 2 + rng.uniform(-0.006, 0.006)
            rot = math.radians(rng.uniform(-3.2, 3.2))
            border = 0.0055 if rng.random() < 0.75 else 0.0018
            su, sv = rng.choice((-1, 1)), rng.choice((-1, 1))
            curl = rng.uniform(0.002, 0.009); bow = rng.uniform(0.0, 0.0025)
            base = WALL_X + 0.0012 + order * 0.00025
            order += 1

            def pos(u, v, lift=0.0):
                t = max(0.0, (u * su + v * sv) / 2)
                off = base + curl * t ** 3 + bow * (1 - u * u) + lift
                y = cy + (u * w / 2) * math.cos(rot) - (v * h / 2) * math.sin(rot)
                z = cz + (u * w / 2) * math.sin(rot) + (v * h / 2) * math.cos(rot)
                return (off, y, z)

            def grid(name, umin, umax, vmin, vmax, lift, mat, uvcrop=None):
                verts, faces, uvs, cuv = [], [], [], []
                for a in range(nu + 1):
                    for b in range(nv + 1):
                        u = umin + (umax - umin) * a / nu; v = vmin + (vmax - vmin) * b / nv
                        verts.append(pos(u, v, lift))
                        s, t = a / nu, b / nv
                        cuv.append((s, t))
                        if uvcrop:
                            (s0, s1), (t0, t1) = uvcrop
                            uvs.append((s0 + (s1 - s0) * s, t0 + (t1 - t0) * t))
                for a in range(nu):
                    for b in range(nv):
                        k = a * (nv + 1) + b
                        faces.append((k, k + nv + 1, k + nv + 2, k + 1))
                me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
                if uvcrop:
                    for layer, data in (("UVMap", uvs), ("Card", cuv)):
                        uvl = me.uv_layers.new(name=layer)
                        for poly in me.polygons:
                            for li in poly.loop_indices:
                                uvl.data[li].uv = data[me.loops[li].vertex_index]
                me.update()
                for p in me.polygons:
                    p.use_smooth = True
                o = bpy.data.objects.new(name, me); coll.objects.link(o); o.data.materials.append(mat)
                return o

            card = grid(f"Postcard_{i:02d}", -1, 1, -1, 1, 0.0, paper)
            if src:
                img = next(n.image for n in src.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image)
                bu, bv = border / (w / 2), border / (h / 2)
                a_in = (w - 2 * border) / (h - 2 * border); A = img.size[0] / img.size[1]
                crop = ((0.5 - a_in / A / 2, 0.5 + a_in / A / 2), (0, 1)) if A > a_in else ((0, 1), (0.5 - A / a_in / 2, 0.5 + A / a_in / 2))
                ph = grid(f"Postcard_{i:02d}_Photo", -1 + bu, 1 - bu, -1 + bv, 1 - bv, 0.0004, aged_photo(src), crop)
                ph.parent = card
            if rng.random() < 0.4:                       # a strip of yellowed tape across the top edge
                tw = rng.uniform(0.028, 0.04); ty = cy + rng.uniform(-0.03, 0.03)
                tz = cz + h / 2 * math.cos(rot) + (ty - cy) * math.sin(rot)
                me = bpy.data.meshes.new(f"Postcard_{i:02d}_Tape")
                x = pos(0, 1)[0] + 0.0009
                me.from_pydata([(x, ty - tw / 2, tz - 0.009), (x, ty + tw / 2, tz - 0.009), (x, ty + tw / 2, tz + 0.011), (x, ty - tw / 2, tz + 0.011)], [], [(0, 1, 2, 3)])
                to = bpy.data.objects.new(me.name, me); coll.objects.link(to); to.data.materials.append(tape); to.parent = card
    print("postcards:", ROWS * COLS)


# ----------------------------------------------------------------------------------------------- e) clock
def _clock():
    D = bpy.data
    coll = D.collections["Wall_Decor"]
    for o in [o for o in coll.all_objects if o.name.startswith("Clock")]:
        D.objects.remove(o, do_unlink=True)
    chrome = simple_mat("ClockChrome", "cfccc6", 0.22, metal=1.0)
    face_m = simple_mat("ClockFace", "efebdf", 0.6)
    ink = simple_mat("ClockInk", "1b1a18", 0.5)
    red = simple_mat("ClockRed", "b3261c", 0.45)
    cy, cz, R = 2.255, 2.165, 0.125
    x0 = WALL_X
    objs = []

    def cyl(name, x, r, depth, mat, verts=64):
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=(x, cy, cz), rotation=(0, math.pi / 2, 0))
        o = bpy.context.active_object; o.name = name
        for c in o.users_collection:
            c.objects.unlink(o)
        coll.objects.link(o); o.data.materials.append(mat); objs.append(o)
        for p in o.data.polygons:
            p.use_smooth = len(p.vertices) == 4
        return o
    cyl("Clock_Body", x0 + 0.016, R, 0.032, chrome)
    xf = x0 + 0.0335
    cyl("Clock_Face", xf - 0.0006, R - 0.011, 0.0012, face_m)
    bpy.ops.mesh.primitive_torus_add(major_radius=R - 0.006, minor_radius=0.0075, major_segments=72, minor_segments=12,
                                     location=(x0 + 0.033, cy, cz), rotation=(0, math.pi / 2, 0))
    t = bpy.context.active_object; t.name = "Clock_Rim"
    for c in t.users_collection:
        c.objects.unlink(t)
    coll.objects.link(t); t.data.materials.append(chrome); objs.append(t)
    for p in t.data.polygons:
        p.use_smooth = True

    def radial(name, ang, r0, r1, wd, x, mat, back=0.0):
        d = Vector((0, math.sin(ang), math.cos(ang))); n = Vector((0, math.cos(ang), -math.sin(ang)))
        c = Vector((x, cy, cz))
        a, b = c + d * r0 - d * back, c + d * r1
        me = bpy.data.meshes.new(name)
        me.from_pydata([a - n * wd / 2, a + n * wd / 2, b + n * wd * 0.3, b - n * wd * 0.3], [], [(0, 3, 2, 1)])
        o = bpy.data.objects.new(name, me); coll.objects.link(o); o.data.materials.append(mat); objs.append(o)
        return o
    # minute ticks merged into one mesh for fewer objects
    tv, tf = [], []
    for k in range(60):
        ang = math.radians(k * 6); big = k % 5 == 0
        d = Vector((0, math.sin(ang), math.cos(ang))); n = Vector((0, math.cos(ang), -math.sin(ang)))
        r1 = R - 0.016; r0 = r1 - (0.011 if big else 0.005); wd = 0.0032 if big else 0.0011
        c = Vector((xf + 0.0002, cy, cz)); i = len(tv)
        tv += [c + d * r0 - n * wd / 2, c + d * r0 + n * wd / 2, c + d * r1 + n * wd / 2, c + d * r1 - n * wd / 2]
        tf.append((i, i + 3, i + 2, i + 1))
    me = bpy.data.meshes.new("Clock_Ticks"); me.from_pydata(tv, [], tf)
    o = bpy.data.objects.new("Clock_Ticks", me); coll.objects.link(o); o.data.materials.append(ink); objs.append(o)
    for h in range(1, 13):
        cu = bpy.data.curves.new(f"Clock_Num_{h}", 'FONT'); cu.body = str(h); cu.size = 0.019
        cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
        o = bpy.data.objects.new(f"Clock_Num_{h}", cu); coll.objects.link(o); o.data.materials.append(ink)
        ang = math.radians(h * 30); r = R - 0.042
        o.location = (xf + 0.0003, cy + r * math.sin(ang), cz + r * math.cos(ang))
        o.rotation_euler = (math.pi / 2, 0, math.pi / 2); objs.append(o)
    # 11:52:20 -- late-night study
    radial("Clock_Hour", math.radians((11 + 52 / 60) * 30), 0.0, 0.056, 0.0075, xf + 0.0012, ink, back=0.012)
    radial("Clock_Minute", math.radians(52 * 6 + 20 / 10), 0.0, 0.088, 0.0055, xf + 0.0022, ink, back=0.014)
    radial("Clock_Second", math.radians(20 * 6), 0.0, 0.096, 0.0014, xf + 0.0032, red, back=0.024)
    cyl("Clock_Cap", xf + 0.0035, 0.0045, 0.003, red, verts=20)
    print("clock rebuilt", len(objs))


# ----------------------------------------------------------------------------------------------- f) keepsakes
def _keepsakes():
    D = bpy.data
    ks = [o for o in D.collections["Keepsakes"].all_objects if o.parent is None]
    for o in ks:
        n = o.name
        if n.startswith("Degree_"):
            b0, b1 = _wb(o); cx = (b0.x + b1.x) / 2
            o.location.x += 0.09 if cx < -1.815 else 0.05
        elif n.startswith("Flag_PK"):
            o.location.x += 0.45
        elif n.startswith("Flag_US"):
            o.location.x += 0.278
    arrow = D.objects["Flag_Arrow"]; _single_user(arrow)
    a0, a1 = _wb(arrow); mw = arrow.matrix_world; inv = mw.inverted()
    na, nb = -1.855, -1.685
    for v in arrow.data.vertices:
        w = mw @ v.co; w.x = na + (w.x - a0.x) * (nb - na) / (a1.x - a0.x); v.co = inv @ w
    arrow.data.update()
    cap = D.objects["Flag_Caption"]; c0, c1 = _wb(cap)
    cap.location.x += (na + nb) / 2 - (c0.x + c1.x) / 2


def apply():
    D = bpy.data
    _move_wall()
    root = D.objects["Station_Root"]
    root.location.x += 0.0
    for o in list(root.children_recursive):
        if o.name.startswith(("Cabinet", "Drawer")):
            D.objects.remove(o, do_unlink=True)
    B = Builder(D.collections["Station"], root)
    _dresser(B)
    d_unit, d_kb, sy = _computer(B, root)
    _polaroid(B, root)
    _cables(B, d_unit, d_kb, sy)
    B.finish()
    _postcards()
    _clock()
    _keepsakes()
    bpy.context.view_layer.update()
    print("e04 left zone done; wall at x", WALL_X)
