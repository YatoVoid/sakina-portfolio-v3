"""Edit #8 (round 4, user 2026-11-01): window + curtains copied from the Crate & Barrel reference
(Organic Cotton Crisp White Window Curtain, back-tab, on a thin nickel rod with a cylinder end cap).

What the reference shows, and what is built here:
- Window: one big pane (no mullions, no glazing beads, no handle) with a light-oak liner all round the reveal,
  a thin oak casing on the wall, a projecting oak sill (stool) with a rounded front edge and a slim apron.
- Rod: brushed-nickel round rod (r 12.7 mm), end caps = short fat cylinders with a slightly smaller neck, wall
  brackets; the rod is wider than the window so the panels stack beside it, as in the reference.
- Curtains: two floor-length (just clear of the floor) white cotton panels, back-tab header with 5 pleat crests per
  panel, soft vertical folds that open slightly toward the hem. Warm-white cotton, matte, light sheen.
- Outside: the city is made easier to read through the glass (see _city): more lit windows, bigger, brighter street
  lamps / beacons, so the lights are clearly visible at night.
All new pieces go in the "Window" bake group so the curtains get their own 2048 px lightmap.
"""
import bpy, bmesh, math, random, os, importlib.util
from mathutils import Vector

_spec = importlib.util.spec_from_file_location("e04", os.path.join(os.path.dirname(os.path.abspath(__file__)), "e04_left_zone.py"))
e04 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(e04)
wood_mat, simple_mat, _node, _lin, _srgb = e04.wood_mat, e04.simple_mat, e04._node, e04._lin, e04._srgb

WALL = 2.50                                        # inner face of the back wall (Blender y)
OPEN_X0, OPEN_X1, OPEN_Z0, OPEN_Z1 = -0.73, 0.52, 0.90, 2.30
ROD_Z, ROD_R, ROD_Y = 2.545, 0.0127, 2.415
HANG_Y = 2.445                                     # fabric centre plane
FLOOR_GAP = 0.012
PANELS = [("Curtain_L", -1.17, -0.67, 11), ("Curtain_R", 0.46, 0.96, 23)]    # x0, x1, seed


def _coll():
    return bpy.data.collections["Window"]


def _link(o):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    _coll().objects.link(o)
    return o


def _box(name, x0, x1, y0, y1, z0, z1, mat, bevel=0.0025):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x0 if v.co.x < 0 else x1
        v.co.y = y0 if v.co.y < 0 else y1
        v.co.z = z0 if v.co.z < 0 else z1
    if bevel:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=2, affect='EDGES')
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    _coll().objects.link(o)
    return o


def _cyl(name, x0, x1, y, z, r, mat, seg=32):
    """Cylinder along X."""
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=abs(x1 - x0))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    o.rotation_euler = (0, math.radians(90), 0)
    o.location = ((x0 + x1) / 2, y, z)
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    _coll().objects.link(o)
    return o


# ----------------------------------------------------------------------------------------------- materials
def _oak():
    cols = ("a9783f", "c99d63", "dcb98a")
    return (wood_mat("WindowOakX", 'X', cols, ring_scale=5.0, rough=(0.45, 0.65), coat=0.08),
            wood_mat("WindowOakZ", 'Z', cols, ring_scale=5.0, rough=(0.45, 0.65), coat=0.08))


def _nickel():
    m = bpy.data.materials.get("RodNickel")
    if m:
        return m
    m = simple_mat("RodNickel", "b9b6b0", rough=0.32, metal=1.0)
    return m


def cotton_mat():
    """Warm white cotton: soft off-white, matte, light sheen, faint slub + weave, lining-tone header band with a
    stitch line (as in the reference)."""
    m = bpy.data.materials.get("CurtainCotton")
    if m:
        return m
    m = bpy.data.materials.new("CurtainCotton"); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    tc = _node(nt, "ShaderNodeTexCoord")
    # slubby cotton: low-frequency tone drift + stretched fibres
    n1 = _node(nt, "ShaderNodeTexNoise", in_Scale=9.0, in_Detail=4.0, in_Roughness=0.55)
    _lin(nt, tc.outputs["Object"], n1.inputs["Vector"])
    mp = _node(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = (260.0, 260.0, 3.0)   # vertical slubs
    _lin(nt, tc.outputs["Object"], mp.inputs["Vector"])
    n2 = _node(nt, "ShaderNodeTexNoise", in_Scale=1.0, in_Detail=2.0, in_Roughness=0.7)
    _lin(nt, mp.outputs[0], n2.inputs["Vector"])
    tone = _node(nt, "ShaderNodeMapRange", in_From_Min=0.3, in_From_Max=0.7, in_To_Min=0.0, in_To_Max=1.0)
    _lin(nt, n1.outputs["Fac"], tone.inputs["Value"])
    col = _node(nt, "ShaderNodeMix", data_type='RGBA')
    col.inputs[6].default_value = (*_srgb("e4dfd1"), 1); col.inputs[7].default_value = (*_srgb("f4f0e6"), 1)
    _lin(nt, tone.outputs["Result"], col.inputs[0])
    # header band (top 0.14 m) a touch warmer + stitch line at its lower edge
    sep = _node(nt, "ShaderNodeSeparateXYZ"); _lin(nt, tc.outputs["Object"], sep.inputs["Vector"])
    hb = _node(nt, "ShaderNodeMapRange", in_From_Min=2.40, in_From_Max=2.43, in_To_Min=0.0, in_To_Max=1.0, clamp=True)
    _lin(nt, sep.outputs["Z"], hb.inputs["Value"])
    hdr = _node(nt, "ShaderNodeMix", data_type='RGBA'); hdr.inputs[7].default_value = (*_srgb("dcd6c6"), 1)
    _lin(nt, hb.outputs["Result"], hdr.inputs[0]); _lin(nt, col.outputs[2], hdr.inputs[6])
    _lin(nt, hdr.outputs[2], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.88
    bs.inputs["Sheen Weight"].default_value = 0.45; bs.inputs["Sheen Roughness"].default_value = 0.5
    bs.inputs["Specular IOR Level"].default_value = 0.25
    bs.inputs["Subsurface Weight"].default_value = 0.08                      # thin cotton passes a little light
    bs.inputs["Subsurface Radius"].default_value = (0.25, 0.22, 0.18)
    # weave + slubs as bump
    wv = _node(nt, "ShaderNodeTexWave", wave_type='BANDS', bands_direction='Z', in_Scale=700.0, in_Distortion=0.4)
    _lin(nt, tc.outputs["Object"], wv.inputs["Vector"])
    bm = _node(nt, "ShaderNodeMix", data_type='FLOAT'); bm.inputs[0].default_value = 0.55
    _lin(nt, wv.outputs["Fac"], bm.inputs[2]); _lin(nt, n2.outputs["Fac"], bm.inputs[3])
    bp = _node(nt, "ShaderNodeBump", in_Strength=0.25, in_Distance=0.001)
    _lin(nt, bm.outputs[0], bp.inputs["Height"]); _lin(nt, bp.outputs["Normal"], bs.inputs["Normal"])
    return m


# ----------------------------------------------------------------------------------------------- window
def _remove_old():
    D = bpy.data
    drop = [o for o in D.objects if o.name.startswith(("Bead_", "Mullion_", "Handle_", "Frame_", "Sill", "Curtain_"))]
    for o in drop:
        me = o.data
        D.objects.remove(o, do_unlink=True)
        if me and me.users == 0:
            D.meshes.remove(me)


def _window():
    ox, oz = _oak()
    x0, x1, z0, z1 = OPEN_X0, OPEN_X1, OPEN_Z0, OPEN_Z1
    glass_y = 2.545
    t = 0.018                                                       # liner thickness
    # liners inside the reveal (wall face -> glass)
    _box("Liner_Top", x0 - 0.001, x1 + 0.001, WALL - 0.002, glass_y, z1 - t, z1 + 0.001, ox, 0.0015)
    _box("Liner_L", x0 - 0.001, x0 + t, WALL - 0.002, glass_y, z0, z1, oz, 0.0015)
    _box("Liner_R", x1 - t, x1 + 0.001, WALL - 0.002, glass_y, z0, z1, oz, 0.0015)
    # casing on the wall face: thin, wide-ish
    cw, cp = 0.058, 0.014
    _box("Casing_Top", x0 - cw, x1 + cw, WALL - cp, WALL, z1, z1 + cw, ox)
    _box("Casing_L", x0 - cw, x0, WALL - cp, WALL, z0, z1, oz)
    _box("Casing_R", x1, x1 + cw, WALL - cp, WALL, z0, z1, oz)
    # sill (stool): projects 0.11 into the room, sits on the apron, runs past the casing
    sx0, sx1 = x0 - cw - 0.04, x1 + cw + 0.04
    _box("Sill", sx0, sx1, WALL - 0.115, glass_y, z0 - 0.002, z0 + 0.034, ox, 0.004)
    _box("Sill_Apron", x0 - cw, x1 + cw, WALL - 0.016, WALL, z0 - 0.002 - 0.055, z0 - 0.002, ox)
    # keep the single glass pane; drop the old multi-light glazing (beads/mullions removed above)
    print("window: oak liners, casing, sill built")


# ----------------------------------------------------------------------------------------------- rod
def _rod():
    nk = _nickel()
    xa, xb = -1.30, 1.09                                            # rod length, wider than the window
    _cyl("Rod", xa, xb, ROD_Y, ROD_Z, ROD_R, nk)
    for side, x in (("L", xa), ("R", xb)):
        sgn = -1 if side == "L" else 1
        # end cap: neck + fat cylinder (as in the reference)
        _cyl(f"Rod_Neck_{side}", x, x + sgn * 0.012, ROD_Y, ROD_Z, ROD_R * 0.8, nk, 24)
        _cyl(f"Rod_Cap_{side}", x + sgn * 0.012, x + sgn * 0.052, ROD_Y, ROD_Z, 0.0215, nk, 40)
    for i, x in enumerate((-1.19, -0.60, 0.50, 0.99)):              # wall brackets
        _box(f"Rod_Bracket_{i}", x - 0.009, x + 0.009, WALL - 0.003, ROD_Y + 0.004, ROD_Z - 0.010, ROD_Z + 0.010, nk, 0.002)
        _box(f"Rod_Bracket_P{i}", x - 0.0125, x + 0.0125, WALL - 0.005, WALL, ROD_Z - 0.022, ROD_Z + 0.022, nk, 0.002)
    print("rod built")


# ----------------------------------------------------------------------------------------------- curtains
def _panel(name, x0, x1, seed):
    """Back-tab panel as one smooth mesh: pleat crests at the top (5), folds that slowly widen toward the hem."""
    rnd = random.Random(seed)
    W = x1 - x0
    nx, nz = 200, 90
    z_top, z_bot = ROD_Z + 0.055, FLOOR_GAP
    pleats = 5
    ph = [rnd.uniform(-0.25, 0.25) for _ in range(3)]
    wob = [rnd.uniform(0, 6.28) for _ in range(4)]
    bm = bmesh.new(); grid = []
    for j in range(nz + 1):
        v = j / nz                                                  # 0 top .. 1 hem
        z = z_top + (z_bot - z_top) * v
        row = []
        # pleats are regular at the top and relax into softer, slightly irregular folds lower down
        reg = max(0.0, 1.0 - v * 1.6)
        amp = 0.020 + 0.012 * v + 0.006 * math.sin(wob[0] + v * 5.0)
        for i in range(nx + 1):
            u = i / nx
            crest = math.cos(2 * math.pi * pleats * u + ph[0])
            fold = (math.cos(2 * math.pi * pleats * u + ph[0] + 0.9 * v * math.sin(wob[1] + u * 4.0)) * 0.75 +
                    0.25 * math.cos(2 * math.pi * (pleats * 2 + 1) * u + wob[2] + v * 2.0))
            f = reg * crest + (1 - reg) * fold
            y = HANG_Y + amp * f
            xx = x0 + W * (u + 0.035 * math.sin(2 * math.pi * pleats * u + ph[0]) / pleats
                           * (1.0 - 0.5 * v))                       # folds bunch the cloth sideways a bit
            # hem lifts a little between the folds; the lining edge on the open side hangs straighter
            zz = z + 0.010 * v * (f * 0.5 + 0.5) * math.sin(wob[3] + u * 7.0)
            row.append(bm.verts.new((xx, y, zz)))
        grid.append(row)
    for j in range(nz):
        for i in range(nx):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    # thickness: second skin 4 mm behind, joined at the borders (a closed cloth edge)
    bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(cotton_mat())
    for p in me.polygons:
        p.use_smooth = True
    _coll().objects.link(o)
    sol = o.modifiers.new("Thick", 'SOLIDIFY'); sol.thickness = 0.004; sol.offset = 1.0
    bpy.context.view_layer.objects.active = o
    return o


def _curtains():
    for name, a, b, seed in PANELS:
        _panel(name, a, b, seed)
    print("curtains built")


# ----------------------------------------------------------------------------------------------- outside
def _city():
    """Make the night city read through the window: lit windows were dim/small. Boost the window emission
    palette and the beacons / street lamps; leave the sky, haze and building bodies as they are."""
    D = bpy.data
    boost = {"Win_Warm": 2.4, "Win_WarmDim": 2.2, "Win_Tungsten": 2.4, "Win_Cool": 2.4, "Win_TV": 2.0, "Win_Green": 2.2}
    for n, k in boost.items():
        m = D.materials.get(n)
        if m:
            em = next((x for x in m.node_tree.nodes if x.type == 'EMISSION'), None)
            if em:
                em.inputs["Strength"].default_value *= k
    mats = {}
    for o in D.objects:
        if o.name in ("Houston_Beacons", "Street_Lamps") or o.name.startswith(("Roof_Beacon", "Car_")):
            for s in o.material_slots:
                if s.material:
                    mats[s.material.name] = s.material            # unique: many objects share one material
    for m in mats.values():
        if m.use_nodes:
            for x in m.node_tree.nodes:
                if x.type == 'EMISSION':
                    x.inputs["Strength"].default_value = min(x.inputs["Strength"].default_value * 2.0, 40.0)
                elif x.type == 'BSDF_PRINCIPLED' and x.inputs["Emission Strength"].default_value > 0:
                    x.inputs["Emission Strength"].default_value = min(x.inputs["Emission Strength"].default_value * 2.0, 40.0)
    print("boosted materials:", sorted(mats))
    # taller downtown: the towers only reached the lower third of the window; stretch them 1.55x about the ground
    k, ground = 1.55, -44.1
    for n in ("Houston_Skyline", "Houston_Windows", "Houston_WindowsCool", "Houston_Beacons"):
        o = D.objects.get(n)
        if o:
            o.scale.z = k; o.location.z = ground * (1 - k)
    print("city lights boosted")


def apply():
    _remove_old()
    _window()
    _rod()
    _curtains()
    _city()
    bpy.context.view_layer.update()
    print("e08 window + curtains done")


if __name__ == "__main__":                         # standalone: python3 e08_window_curtains.py <in.blend> <out.blend>
    import sys
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    bpy.ops.wm.open_mainfile(filepath=a[0]); apply()
    bpy.ops.wm.save_as_mainfile(filepath=a[1], compress=True)
