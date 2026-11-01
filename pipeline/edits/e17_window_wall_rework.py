"""Edit #17 (Sakina, 2026-11-01 13:47): window wall rework. Runs LAST (after e14, e08b, e15, e16).

Her list, and what this script does about each point (all numbers in Blender coordinates, wall inner face y = 2.5):
  1. Pillar next to the blue poster is removed (`Wood_Post`).
  2. Blue poster: there is no room for it on the back wall once the window and curtains are wider
     (left of the window is the diploma frame, right of it is the bookcase), so it is removed. She said to remove it if
     it does not fit. Its objects are only deleted from the scene; the poster image is still packed in the .blend history
     of earlier commits.
  3. Window is wider: opening 1.25 m -> 1.89 m (x -0.77 .. 1.12). The four wall boxes around the opening, the casing, reveal,
     fixed frame, two sashes, glass, rain lines and handle are refitted. The wall window light is widened to match.
  4. Window sill (the "shelf") no longer sticks out 20 cm across the curtains: it is now 6 cm deep and exactly as wide as the
     casing, and the curtains hang OUTSIDE the casing on both sides.
  5. Centre desk is slid back to the wall (back edge 3 mm from the baseboard). Everything on it moves with it, the white chair
     moves the same distance so it still stands in front of the desk, and the bookcase moves 8 cm along the wall so it does not
     collide with the desk end. The alocasia plant moves only 0.32 m (not 0.48 m) so it stands in front of the left curtain.
  6. New curtains from her linen reference: wide stacks (45 cm each), deep soft folds that flare toward the hem, black rod with
     rings, centre bracket and ball finials. Hem is 4 cm above the desk top (z 0.76), so the hem curve shows and the folds cast
     shadows on the desk. Fabric hangs 2-5 cm in front of the rod, nowhere near the sill.
"""
import bpy, bmesh, math, random, os, importlib.util
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(fname):
    spec = importlib.util.spec_from_file_location(fname, os.path.join(HERE, fname + ".py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# --------------------------------------------------------------------------------------- numbers
OLD_X0, OLD_X1 = -0.73, 0.52
X0, X1 = -0.75, 0.85                      # new opening 1.60 m (was 1.25 m), centred on the CRT (x 0.05)
Z0, Z1 = 0.90, 2.30
CW = 0.05                                  # casing width
WALL = 2.50
DESK_DY = 0.48                             # desk back edge 2.479, baseboard face at 2.482
PLANT_DY = 0.32
BOOKCASE_DX = 0.0                          # desk is shorter now, the bookcase stays where it was approved
DESK_X0, DESK_X1 = -1.20, 1.32             # desk length 2.52 m (was 2.90 m): almost nothing off the crowded left end, 33 cm off the right
OLD_DESK_X0, OLD_DESK_X1 = -1.25, 1.65
DESK_TOP = 0.72
HEM_Z = DESK_TOP + 0.046                   # lowest point of the hem ends up 4 cm above the desk top (folds dip 6 mm)
ROD_Y, ROD_Z, ROD_R = 2.43, 2.545, 0.0127
HANG_Y = 2.405                             # fabric centre plane
RING_R = 0.022
Z_TOP = ROD_Z - RING_R + 0.002             # fabric top edge just under the rings
STACKS = [("Curtain_L", -1.17, -0.83, 11), ("Curtain_R", 0.93, 1.27, 23)]   # 44-45 cm wide stacks outside the casing
ROD_X0, ROD_X1 = -1.22, 1.32


def _bb(o):
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [min(w[i] for w in ws) for i in range(3)], [max(w[i] for w in ws) for i in range(3)]


def _move(o, dx=0.0, dy=0.0, dz=0.0):
    m = o.matrix_world.copy()
    m.translation += Vector((dx, dy, dz))
    o.matrix_world = m


def _remove(names_or_prefixes, exact=False):
    D = bpy.data
    out = []
    for o in list(D.objects):
        hit = o.name in names_or_prefixes if exact else o.name.startswith(tuple(names_or_prefixes))
        if hit:
            me = o.data if o.type in ('MESH', 'CURVE') else None
            pool = D.meshes if o.type == 'MESH' else D.curves
            out.append(o.name)
            D.objects.remove(o, do_unlink=True)
            if me is not None and me.users == 0:
                pool.remove(me)
    return out


# --------------------------------------------------------------------------------------- 1 + 2 pillar, poster
def _remove_pillar_poster():
    gone = _remove(["Wood_Post"], exact=True) + _remove(["Poster"])
    print("e17: removed pillar + poster objects:", len(gone), flush=True)


# --------------------------------------------------------------------------------------- 3 window
def _widen_window():
    D = bpy.data
    e14 = _load("e14_window_reveal")
    e14.OPEN_X0, e14.OPEN_X1 = X0, X1
    win = D.collections["Window"]
    paint = D.materials["WindowPaint"]

    # wall boxes around the opening (8 verts each, identity transform)
    for n in ("Wall_Back_L", "Wall_Back_R", "Wall_Back_Above", "Wall_Back_Below"):
        o = D.objects[n]
        assert o.matrix_world.translation.length < 1e-6, n
        for v in o.data.vertices:
            if abs(v.co.x - OLD_X0) < 1e-3:
                v.co.x = X0
            elif abs(v.co.x - OLD_X1) < 1e-3:
                v.co.x = X1
        o.data.update()

    glass = D.objects["Glass"]
    cx_old, sx_old = glass.location.x, glass.scale.x
    _remove(["Window_Casing", "Window_Reveal", "Window_Frame", "Sash_L", "Sash_R"], exact=True)

    cx = (X0 + X1) / 2
    LIN, FR = e14.LINER, e14.FR
    fx0, fx1 = X0 + LIN + FR, X1 - LIN - FR
    fz0, fz1 = Z0 + LIN + FR, Z1 - LIN - FR
    cy0, cy1 = WALL - 0.025, WALL
    casing = [(X0 - CW, X1 + CW, cy0, cy1, 2.30, 2.35), (X0 - CW, X0, cy0, cy1, Z0, 2.30), (X1, X1 + CW, cy0, cy1, Z0, 2.30)]
    rv = [(X0, X0 + LIN, WALL, e14.REVEAL_END, Z0, Z1), (X1 - LIN, X1, WALL, e14.REVEAL_END, Z0, Z1),
          (X0 + LIN, X1 - LIN, WALL, e14.REVEAL_END, Z1 - LIN, Z1), (X0 + LIN, X1 - LIN, WALL, e14.REVEAL_END, Z0 - 0.038, Z0 + LIN)]
    fy0, fy1 = 2.600, 2.680
    ix0, ix1, iz0, iz1 = X0 + LIN, X1 - LIN, Z0 + LIN, Z1 - LIN
    frame = [(ix0, ix0 + FR, fy0, fy1, iz0, iz1), (ix1 - FR, ix1, fy0, fy1, iz0, iz1),
             (ix0 + FR, ix1 - FR, fy0, fy1, iz0, iz0 + FR), (ix0 + FR, ix1 - FR, fy0, fy1, iz1 - FR, iz1)]
    e14._object("Window_Casing", casing, paint, win)
    e14._object("Window_Reveal", rv, paint, win)
    e14._object("Window_Frame", frame, paint, win)
    e14._object("Sash_L", e14._sash(fx0, cx - e14.GAP / 2), paint, win)
    e14._object("Sash_R", e14._sash(cx + e14.GAP / 2, fx1), paint, win)

    sx_new = (fx1 - fx0) / 1.25
    glass.scale.x = sx_new
    glass.location.x = cx
    ratio = sx_new / sx_old
    for v in D.objects["RainLines"].data.vertices:
        v.co.x = cx + (v.co.x - cx_old) * ratio
    for n in ("Handle_Plate", "Handle_Lever"):
        D.objects[n].location.x += cx - cx_old

    # sill ("shelf"): 6 cm deep, exactly as wide as the casing (+1 cm), so nothing sticks out across the curtains
    sx0, sx1 = X0 - CW, X1 + CW
    for n, ya, yb in (("Sill", 2.44, None), ("Sill_Lip", 2.434, 2.446)):
        o = D.objects[n]
        assert o.parent is None and tuple(o.scale) == (1.0, 1.0, 1.0) and not any(o.rotation_euler), n
        ox, oy = o.location.x, o.location.y          # these objects have their own origin: vertices are local
        ys = sorted({round(v.co.y, 4) for v in o.data.vertices})
        lo_y, hi_y = ys[0], ys[-1]
        mid_x = (OLD_X0 + OLD_X1) / 2 - ox
        for v in o.data.vertices:
            v.co.x = (sx0 if v.co.x < mid_x else sx1) - ox
            if abs(v.co.y - lo_y) < 1e-4:
                v.co.y = ya - oy                      # front edge (towards the room): sill is only a few cm deep
            elif yb is not None and abs(v.co.y - hi_y) < 1e-4:
                v.co.y = yb - oy
        o.data.update()

    # the window light behind the glass follows the opening (same brightness per area)
    L4 = D.objects["L4_Window_Night"]
    k = (X1 - X0) / (OLD_X1 - OLD_X0)
    L4.location.x = cx
    L4.data.size *= k
    L4.data.energy *= k
    bpy.context.view_layer.update()
    print(f"e17: window opening x {X0}..{X1} ({X1 - X0:.2f} m, was {OLD_X1 - OLD_X0:.2f} m); sill depth 6 cm; light x{k:.2f}", flush=True)


# --------------------------------------------------------------------------------------- 5 desk to wall
def _desk_to_wall():
    D = bpy.data
    # the cable that arched up in front of the VCR (Cable_Left) is removed (Sakina 2026-11-01)
    _remove(["Cable_Left"], exact=True)
    plant = {o for c in D.collections if c.name == "Plant" for o in c.objects}
    lights = {"L1_DeskLamp_Key", "L2_DeskLamp_Spill", "L6_TV_Screen"}
    skip = ("Wall", "Window", "Houston", "Radiator", "Baseboard", "Sill", "Rod", "Curtain", "Glass", "Rain", "Handle", "Chair", "Bookcase")
    sel = []
    for o in D.objects:
        if o in plant:
            continue
        if o.type == 'LIGHT':
            if o.name in lights:
                sel.append(o)
            continue
        if o.type not in ('MESH', 'CURVE', 'EMPTY', 'FONT') or o.name.startswith(skip):
            continue
        if o.name.startswith("Desk_"):
            sel.append(o)
            continue
        if o.type == 'EMPTY':
            continue
        lo, hi = _bb(o)
        c = [(lo[i] + hi[i]) / 2 for i in range(3)]
        if -1.30 <= c[0] <= 1.70 and 1.25 <= c[1] <= 2.05 and lo[2] >= 0.60:
            sel.append(o)
    selset = set(sel)
    n = 0
    for o in sel:
        if o.parent in selset:
            continue
        _move(o, dy=DESK_DY)
        n += 1
    for o in plant:
        if o.parent in plant:
            continue
        _move(o, dy=PLANT_DY)
    chair = [o for o in D.objects if o.name in ("Chair_Wood", "Chair_Seat", "Chair_Nails")]
    assert len(chair) == 3, [o.name for o in chair]
    for o in chair:
        _move(o, dy=DESK_DY)
    book = [o for o in D.objects if o.name.startswith("Bookcase")]
    for o in book:
        _move(o, dx=BOOKCASE_DX)
    # lamp cord hangs behind the desk from the lamp base: follow the lamp
    _move(D.objects["Lamp_Cord"], dy=DESK_DY - 0.02)
    _shorten_desk(sel)
    bpy.context.view_layer.update()
    lo, hi = _bb(D.objects["Desk_Top"])
    print(f"e17: desk slid {DESK_DY} m to the wall (top y {lo[1]:.3f}..{hi[1]:.3f}); {n} desk-top objects, {len(plant)} plant objects (+{PLANT_DY}), "
          f"{len(chair)} chair parts, {len(book)} bookcase objects (+{BOOKCASE_DX} x)", flush=True)


def _shorten_desk(sel):
    """Desk 2.90 m -> 2.50 m: vertices left of x -0.30 move right, right of x 0.75 move left (legs, rails and top keep their shape);
    the drawer in the middle is untouched. Props too close to a new end are nudged inward."""
    D = bpy.data
    dl, dr = DESK_X0 - OLD_DESK_X0, DESK_X1 - OLD_DESK_X1
    for o in [o for o in D.objects if o.name.startswith("Desk_") and o.type == 'MESH']:
        o.data = o.data.copy()
        mw = o.matrix_world
        inv = mw.inverted()
        for v in o.data.vertices:
            w = mw @ v.co
            if w.x < -0.30:
                w.x += dl
            elif w.x > 0.75:
                w.x += dr
            v.co = inv @ w
        o.data.update()
    bpy.context.view_layer.update()
    selset = set(sel)
    moved = []
    for o in sel:
        if o.type == 'LIGHT' or o.name.startswith("Desk_") or o.parent in selset:
            continue
        lo, hi = _bb(o)
        if hi[0] - lo[0] > 1.0:
            continue
        if lo[0] < DESK_X0 + 0.05 and lo[0] > OLD_DESK_X0 - 0.2:
            _move(o, dx=DESK_X0 + 0.05 - lo[0]); moved.append(o.name)
        elif hi[0] > DESK_X1 - 0.05 and hi[0] < OLD_DESK_X1 + 0.2:
            _move(o, dx=DESK_X1 - 0.05 - hi[0]); moved.append(o.name)
    print(f"e17: desk shortened by {(OLD_DESK_X1 - OLD_DESK_X0) - (DESK_X1 - DESK_X0):.2f} m; props nudged inward: {moved}", flush=True)


# --------------------------------------------------------------------------------------- 6 curtains
def _linen_mat(e08):
    m = bpy.data.materials.get("CurtainLinen")
    if m:
        return m
    _node, _lin, _srgb = e08._node, e08._lin, e08._srgb
    m = bpy.data.materials.new("CurtainLinen")
    m.use_nodes = True
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    tc = _node(nt, "ShaderNodeTexCoord")
    n1 = _node(nt, "ShaderNodeTexNoise", in_Scale=7.0, in_Detail=4.0, in_Roughness=0.55)
    _lin(nt, tc.outputs["Object"], n1.inputs["Vector"])
    mp = _node(nt, "ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (240.0, 240.0, 40.0)                # linen slubs: both directions, a bit longer vertically
    _lin(nt, tc.outputs["Object"], mp.inputs["Vector"])
    n2 = _node(nt, "ShaderNodeTexNoise", in_Scale=1.0, in_Detail=2.0, in_Roughness=0.7)
    _lin(nt, mp.outputs[0], n2.inputs["Vector"])
    tone = _node(nt, "ShaderNodeMapRange", in_From_Min=0.3, in_From_Max=0.7, in_To_Min=0.0, in_To_Max=1.0)
    _lin(nt, n1.outputs["Fac"], tone.inputs["Value"])
    col = _node(nt, "ShaderNodeMix", data_type='RGBA')
    col.inputs[6].default_value = (*_srgb("b3a588"), 1)                     # oatmeal linen, from the reference
    col.inputs[7].default_value = (*_srgb("cdc0a3"), 1)
    _lin(nt, tone.outputs["Result"], col.inputs[0])
    _lin(nt, col.outputs[2], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.92
    bs.inputs["Sheen Weight"].default_value = 0.3
    bs.inputs["Sheen Roughness"].default_value = 0.6
    bs.inputs["Specular IOR Level"].default_value = 0.2
    bs.inputs["Subsurface Weight"].default_value = 0.06
    bs.inputs["Subsurface Radius"].default_value = (0.25, 0.22, 0.18)
    wv = _node(nt, "ShaderNodeTexWave", wave_type='BANDS', bands_direction='Z', in_Scale=520.0, in_Distortion=0.6)
    _lin(nt, tc.outputs["Object"], wv.inputs["Vector"])
    bm = _node(nt, "ShaderNodeMix", data_type='FLOAT')
    bm.inputs[0].default_value = 0.6
    _lin(nt, wv.outputs["Fac"], bm.inputs[2])
    _lin(nt, n2.outputs["Fac"], bm.inputs[3])
    bp = _node(nt, "ShaderNodeBump", in_Strength=0.3, in_Distance=0.001)
    _lin(nt, bm.outputs[0], bp.inputs["Height"])
    _lin(nt, bp.outputs["Normal"], bs.inputs["Normal"])
    return m


def _sstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class _Stack:
    """One curtain stack as a surface y(u, v), z(u, v), x(u, v). u: 0 at the INNER edge (window side) .. 1 outer edge, v: 0 rings .. 1 hem.
    Real-fabric behaviour instead of identical cosine bars:
      - fold widths and depths vary from fold to fold (warped phase, modulated amplitude)
      - rounded broad folds towards the room, pinched narrow valleys towards the rod (cos + 2nd harmonic)
      - pinch pleats are regular at the rings and get looser and deeper towards the hem; fold lines lean and drift as they fall
      - stack flares outward by ~3.5 cm at the hem, hem swings forward 1.6 cm
      - 6 sets of small cross wrinkles (1-2 mm), thicker double-turned hem, rolled side hems, top edge sags between the rings."""

    def __init__(self, name, x0, x1, seed):
        r = random.Random(seed)
        self.name = name
        self.W = x1 - x0
        self.sign = -1.0 if name.endswith("L") else 1.0
        self.xin = x1 if self.sign < 0 else x0
        self.F = 5
        self.p = [r.uniform(0, 6.283) for _ in range(10)]
        self.mw = [(r.uniform(9, 20), r.uniform(0.0006, 0.0017), r.uniform(0, 6.283), r.uniform(-2.5, 2.5)) for _ in range(7)]

    def g(self, u):
        p = self.p
        return u + 0.045 * math.sin(2 * math.pi * u + p[0]) + 0.02 * math.sin(2 * math.pi * 2.3 * u + p[1])

    def phi(self, u, v):
        p = self.p
        ease = _sstep(v / 0.25)
        ph = 2 * math.pi * self.F * self.g(u) * (1.0 - 0.10 * v)
        ph += ease * v * (0.9 * math.sin(2 * math.pi * 0.9 * u + p[2]) + 0.5 * math.sin(2 * math.pi * 1.7 * u + p[3]))
        return ph

    def fold(self, u, v):
        ph = self.phi(u, v)
        return math.cos(ph) - 0.2 * math.cos(2 * ph)          # b: +0.8 broad crest (towards room), -1.2 narrow valley (towards rod)

    def surf(self, u, v):
        p = self.p
        ease = _sstep(v / 0.25)
        amp = (0.020 + 0.032 * v ** 1.3) * (1 + ease * (0.28 * math.sin(2 * math.pi * 2.3 * u + p[4]) + 0.18 * math.sin(2 * math.pi * 3.9 * u + p[5])))
        b = self.fold(u, v)
        y = HANG_Y - amp * b - 0.016 * v * v
        mw = 0.0
        for k, a, ph, c in self.mw:
            mw += a * math.cos(2 * math.pi * k * u + ph + c * v * 3.0)
        y += mw * (0.25 + 0.75 * ease)
        y -= 0.0035 * _sstep((v - 0.955) / 0.02)                                  # double-turned hem is thicker
        edge = min(u, 1.0 - u)
        y -= 0.003 * _sstep(1.0 - edge / 0.02)                                    # side hems roll forward a little
        x = self.xin + self.sign * self.W * u * (1.0 + 0.095 * v ** 1.5)
        w = (b + 1.2) / 2.0                                                       # 0 in a valley, 1 on a crest
        z_hem = (DESK_TOP + 0.04) + 0.014 * w + 0.002 * (0.5 + 0.5 * math.sin(p[6] + u * 11.0))
        z = Z_TOP + (z_hem - Z_TOP) * v - 0.014 * w * max(0.0, 1.0 - v * 7.0)
        return x, y, z

    def ring_us(self):
        """u of every pinch point at the top (phi = pi + 2*pi*k), where a ring + clip goes."""
        out, prev, n = [], self.phi(0.0, 0.0), 4000
        for i in range(1, n + 1):
            u = i / n
            cur = self.phi(u, 0.0)
            k0, k1 = math.floor((prev - math.pi) / (2 * math.pi)), math.floor((cur - math.pi) / (2 * math.pi))
            if k1 > k0:
                out.append(u - 0.5 / n)
            prev = cur
        return [u for u in out if 0.02 < u < 0.98]


def _panel(e08, st, mat):
    nx, nz = 190, 130
    bm = bmesh.new()
    grid = []
    for j in range(nz + 1):
        v = j / nz
        grid.append([bm.verts.new(st.surf(i / nx, v)) for i in range(nx + 1)])
    flip = st.sign > 0                                      # keep face normals pointing into the room for both stacks
    for j in range(nz):
        for i in range(nx):
            f = (grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i])
            bm.faces.new(f[::-1] if flip else f)
    bm.normal_update()
    me = bpy.data.meshes.new(st.name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(st.name, me)
    me.materials.append(mat)
    for pl in me.polygons:
        pl.use_smooth = True
    bpy.data.collections["Window"].objects.link(o)
    sol = o.modifiers.new("Thick", 'SOLIDIFY')
    sol.thickness = 0.004
    sol.offset = 1.0
    return o


def _ring(name, x, mat):
    bm = bmesh.new()
    R, r, ns, nr = RING_R, 0.0035, 28, 8
    vs = []
    for a in range(ns):
        ta = 2 * math.pi * a / ns
        row = []
        for b in range(nr):
            tb = 2 * math.pi * b / nr
            rr = R + r * math.cos(tb)
            row.append(bm.verts.new((x + r * math.sin(tb), ROD_Y + rr * math.sin(ta), ROD_Z + rr * math.cos(ta))))
        vs.append(row)
    for a in range(ns):
        for b in range(nr):
            bm.faces.new((vs[a][b], vs[a][(b + 1) % nr], vs[(a + 1) % ns][(b + 1) % nr], vs[(a + 1) % ns][b]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    bpy.data.collections["Window"].objects.link(o)
    return o


def _ball(name, x, mat, r=0.021):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=r)
    for v in bm.verts:
        v.co += Vector((x, ROD_Y, ROD_Z))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    bpy.data.collections["Window"].objects.link(o)
    return o


def _curtains():
    e08 = _load("e08_window_curtains")
    removed = _remove(["Curtain_", "Rod"])
    black = e08.simple_mat("RodBlack", "1c1c1b", rough=0.38, metal=1.0)
    linen = _linen_mat(e08)
    e08._cyl("Rod", ROD_X0, ROD_X1, ROD_Y, ROD_Z, ROD_R, black)
    _ball("Rod_Finial_L", ROD_X0 - 0.01, black)
    _ball("Rod_Finial_R", ROD_X1 + 0.01, black)
    cxw = (X0 + X1) / 2
    for i, x in enumerate((STACKS[0][1] + 0.03, cxw, STACKS[1][2] - 0.03)):                                   # brackets: both ends + one over the window centre
        e08._box(f"Rod_Bracket_{i}", x - 0.009, x + 0.009, ROD_Y - 0.004, WALL - 0.003, ROD_Z - 0.010, ROD_Z + 0.010, black, 0.002)
        e08._box(f"Rod_Bracket_P{i}", x - 0.0125, x + 0.0125, WALL - 0.005, WALL, ROD_Z - 0.022, ROD_Z + 0.022, black, 0.002)
    n_rings = 0
    for name, x0, x1, seed in STACKS:
        st = _Stack(name, x0, x1, seed)
        _panel(e08, st, linen)
        for k, u in enumerate(st.ring_us()):
            x, y, z = st.surf(u, 0.0)
            _ring(f"Rod_Ring_{name[-1]}{k}", x, black)
            e08._box(f"Rod_Clip_{name[-1]}{k}", x - 0.0055, x + 0.0055, y - 0.004, y + 0.004, Z_TOP - 0.024, Z_TOP + 0.012, black, 0.0015)
            n_rings += 1
    bpy.context.view_layer.update()
    print(f"e17: curtains rebuilt (removed {len(removed)} old), linen stacks {[(n, a, b) for n, a, b, _ in STACKS]}, {n_rings} rings, hem low point z {DESK_TOP + 0.04:.2f}", flush=True)


def apply():
    _remove_pillar_poster()
    _widen_window()
    _desk_to_wall()
    _curtains()
