"""Edit #3 (user request 2026-11-01): replace the wall-mounted half bookshelf on the back wall with the tall antique
glazed bookcase from the "Antiques Boutique" reference photo (floor-standing, touches the floor), and re-arrange the
nook: side table, floor lamp and club chair move right to make room; chair turned toward the desk.

Reference analysis (what is CERTAIN from the photo vs INFERRED):
  certain  - two-door glazed mahogany bookcase; free-standing fluted columns at both front corners with gilt capitals,
             gilt acanthus collar + gilt reeds on the lower third of each column; heavy stepped cornice with a gilt
             garland (6 swags) on the frieze, gilt rosette on each corner block, small gilt finials on the cornice ends;
             square gilt rosette plates at the corners of each glass opening; thick centre stile with keyhole + a
             hanging tag; 4 shelves + a tall bottom compartment full of leather books (red / orange / green / navy / tan,
             gold bands); plinth base with a recessed panel carrying a gilt scroll ornament, bun-less square feet.
  inferred - real size (cornice 1.50 m wide, 2.17 m tall, 0.56 m deep: from the photo's 0.70 width/height ratio and a
             ~2.2 m ceiling-friendly height), wood tone/figure, exact shelf heights, the individual books, the side/back.
Everything is parametric (metres, bookcase-local: +X right, +Y front, +Z up; root rotated so the front faces the room).
"""
import bpy, bmesh, math, os, random, importlib.util
from mathutils import Vector, Matrix

D = bpy.data
_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "e02_club_chair.py")
_s = importlib.util.spec_from_file_location("e02_club_chair", _p)
E2 = importlib.util.module_from_spec(_s); _s.loader.exec_module(E2)

# ------------------------------------------------------------------ placement (world, metres; back wall y=2.5, right wall x=3.58)
CASE_X, CASE_Y = 2.35, 2.475           # centre of the bookcase back; back sits on the back-wall baseboard
TABLE_DX = 0.52                         # side table slides to the corner (x 3.20 .. 3.54)
CHAIR_TURN_DEG = 18.0                   # chair front turned toward the desk (toward the back wall / image-left)
CHAIR_WALL_X = 3.565                    # chair's rearmost corner x
CHAIR_YMAX = 1.98                       # chair's +y extent stays in front of the bookcase base (front y ~2.0)
LAMP_GAP = 0.04                         # lamp base edge to chair front
LAMP_LATERAL = -0.32                    # lamp offset toward the room-front side of the chair (negative = away from the table)
CARTON_SHIFT = (-0.35, -1.45)           # floor carton moves out of the bookcase footprint

# ------------------------------------------------------------------ bookcase dimensions (local)
CORN_W, CORN_D = 1.50, 0.56
BODY_HW = 0.635                         # half width of the carcass
COL_X, COL_R = 0.585, 0.043             # column centre x, radius
BODY_D = 0.44
Z_FEET, Z_PLINTH, Z_BASE = 0.08, 0.17, 0.33
Z_GLASS0, Z_GLASS1 = 0.40, 1.78
Z_FRIEZE0, Z_FRIEZE1 = 1.84, 1.99
Z_TOP = 2.10
SHELF_Z = [0.46, 0.94, 1.16, 1.40, 1.61]          # top surfaces of the bottom board and the 4 shelves
Z_INT_TOP = 1.80
DOOR_Y = 0.41


# ================================================================ primitives
class Acc:
    """Accumulates many small meshes that share a material into one mesh."""
    def __init__(self):
        self.v, self.f = [], []

    def add(self, me, M=None):
        if M is not None:
            me.transform(M)
        o = len(self.v)
        self.v += [tuple(v.co) for v in me.vertices]
        self.f += [tuple(i + o for i in p.vertices) for p in me.polygons]
        D.meshes.remove(me)

    def add_box(self, hx, hy, hz, c):
        x, y, z = c
        o = len(self.v)
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    self.v.append((x + sx * hx, y + sy * hy, z + sz * hz))
        # vertex index = 4*ix + 2*iy + iz  (ix,iy,iz in {0,1})
        q = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        self.f += [tuple(o + i for i in face) for face in q]

    def mesh(self, name, smooth_angle=35):
        me = D.meshes.new(name)
        me.from_pydata(self.v, [], self.f); me.update()
        E2.finish(me, smooth_angle)
        return me


def bbox(half, c, bevel=0.003, seg=2):
    bevel = min(bevel, min(half) * 0.9)
    return E2.bevelled_box(half, c, bevel, seg)


def lathe(profile, seg=24, cx=0.0, cy=0.0, rfun=None, cap=True):
    bm = bmesh.new(); rings = []
    for (r, z) in profile:
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            rr = r * (rfun(a, z) if rfun else 1.0)
            ring.append(bm.verts.new((cx + rr * math.cos(a), cy + rr * math.sin(a), z)))
        rings.append(ring)
    for k in range(len(rings) - 1):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new([rings[k][i], rings[k][j], rings[k + 1][j], rings[k + 1][i]])
    if cap:
        for ring in (rings[0], rings[-1]):
            bm.faces.new(ring)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = D.meshes.new("lathe"); bm.to_mesh(me); bm.free()
    return me


def sphere(r, scale, c, seg=10, rings=6):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0] * r, v.co.y * scale[1] * r, v.co.z * scale[2] * r)) + Vector(c)
    me = D.meshes.new("sph"); bm.to_mesh(me); bm.free()
    return me


# ================================================================ materials
def wood_material(name, root, tone=1.0, light=False):
    """Dark mahogany: stretched noise grain (vertical) + slow mottling, polished satin."""
    m = D.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    n = E2._n
    out = n(nt, "ShaderNodeOutputMaterial", 9, 0)
    bsdf = n(nt, "ShaderNodeBsdfPrincipled", 8, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tc = n(nt, "ShaderNodeTexCoord", 0, 0); tc.object = root
    mp = n(nt, "ShaderNodeMapping", 1, 0)
    mp.inputs["Scale"].default_value = (9.0, 70.0, 5.0)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    grain = n(nt, "ShaderNodeTexNoise", 2, 1, noise_dimensions='3D')
    grain.inputs["Scale"].default_value = 3.0; grain.inputs["Detail"].default_value = 7.0
    nt.links.new(mp.outputs["Vector"], grain.inputs["Vector"])
    mot = n(nt, "ShaderNodeTexNoise", 2, -1, noise_dimensions='3D')
    mot.inputs["Scale"].default_value = 2.2; mot.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], mot.inputs["Vector"])
    ramp = n(nt, "ShaderNodeValToRGB", 4, 0)
    ramp.color_ramp.elements[0].position = 0.30; ramp.color_ramp.elements[1].position = 0.70
    k = tone
    ramp.color_ramp.elements[0].color = (0.050 * k, 0.014 * k, 0.005 * k, 1)     # deep mahogany
    ramp.color_ramp.elements[1].color = (0.165 * k, 0.050 * k, 0.017 * k, 1)     # warm red-brown figure
    nt.links.new(grain.outputs["Fac"], ramp.inputs["Fac"])
    mix = n(nt, "ShaderNodeMix", 5, 0, data_type='RGBA', blend_type='MULTIPLY')
    mix.inputs["Factor"].default_value = 0.6
    nt.links.new(ramp.outputs["Color"], E2._s(mix, "A_Color"))
    mr = n(nt, "ShaderNodeMapRange", 4, -1)
    mr.inputs["To Min"].default_value = 0.55; mr.inputs["To Max"].default_value = 1.25
    nt.links.new(mot.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], E2._s(mix, "B_Color"))
    nt.links.new(E2._s(mix, "Result_Color", True), bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.36
    bsdf.inputs["Coat Weight"].default_value = 0.22; bsdf.inputs["Coat Roughness"].default_value = 0.18
    bump = n(nt, "ShaderNodeBump", 6, -2)
    bump.inputs["Strength"].default_value = 0.06; bump.inputs["Distance"].default_value = 0.002
    nt.links.new(grain.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def solid(name, col, rough, metallic=0.0, coat=0.0):
    m = D.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Coat Weight"].default_value = coat
    return m


def glass_material(name):
    """Thin glazing: real glass for the camera, transparent for shadow rays so the books inside stay lit."""
    m = D.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear(); n = E2._n
    out = n(nt, "ShaderNodeOutputMaterial", 6, 0)
    g = n(nt, "ShaderNodeBsdfPrincipled", 3, 1)
    g.inputs["Base Color"].default_value = (0.92, 0.96, 0.95, 1)
    g.inputs["Roughness"].default_value = 0.03
    g.inputs["IOR"].default_value = 1.45
    g.inputs["Transmission Weight"].default_value = 1.0
    t = n(nt, "ShaderNodeBsdfTransparent", 3, -1)
    lp = n(nt, "ShaderNodeLightPath", 1, 0)
    mx = n(nt, "ShaderNodeMixShader", 5, 0)
    nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs["Fac"])
    nt.links.new(g.outputs["BSDF"], mx.inputs[1]); nt.links.new(t.outputs["BSDF"], mx.inputs[2])
    nt.links.new(mx.outputs["Shader"], out.inputs["Surface"])
    return m


BOOK_COLOURS = {   # linear RGB (reference spines: reds, oranges, greens, navy/blue, tan, oxblood)
    "red":     ((0.30, 0.040, 0.025), 5), "orange": ((0.46, 0.15, 0.04), 4), "oxblood": ((0.12, 0.018, 0.016), 3),
    "tan":     ((0.34, 0.20, 0.09), 4), "cream":  ((0.55, 0.45, 0.28), 1), "mustard": ((0.40, 0.26, 0.05), 2),
    "green":   ((0.025, 0.12, 0.07), 4), "teal":  ((0.03, 0.14, 0.15), 2), "navy":   ((0.018, 0.04, 0.14), 4),
    "blue":    ((0.08, 0.17, 0.36), 3), "brown": ((0.12, 0.06, 0.025), 3), "olive":  ((0.17, 0.15, 0.05), 2),
}


# ================================================================ build
def build_bookcase(coll):
    root = D.objects.new("Bookcase_Root", None); coll.objects.link(root)
    root.empty_display_type = 'PLAIN_AXES'; root.empty_display_size = 0.1
    root.location = (CASE_X, CASE_Y, 0.0); root.rotation_euler = (0.0, 0.0, math.pi)   # local +Y (front) -> world -Y

    M = {
        "wood": wood_material("BC_Mahogany", root, 1.0),
        "wood_in": wood_material("BC_MahoganyInterior", root, 0.55),
        "gilt": solid("BC_Gilt", (0.80, 0.52, 0.15, 1), 0.27, 1.0),
        "brass": solid("BC_Brass", (0.50, 0.33, 0.12, 1), 0.30, 1.0),
        "glass": glass_material("BC_Glass"),
        "paper": solid("BC_PaperTag", (0.62, 0.58, 0.50, 1), 0.8),
        "label": solid("BC_BookLabel", (0.50, 0.42, 0.26, 1), 0.7),
    }
    for nm, (c, _w) in BOOK_COLOURS.items():
        M["bk_" + nm] = solid("BC_Book_" + nm, (c[0], c[1], c[2], 1), 0.48, 0.0, 0.05)
    A = {k: Acc() for k in M}
    rng = random.Random(11)

    # ---- carcass ------------------------------------------------------------------------------------------------
    def put(key, me, T=None):
        A[key].add(me, T)

    # base: feet, plinth, base body
    for sx in (-1, 1):
        for y in (0.07, 0.45):
            A["wood"].add(bbox((0.045, 0.045, Z_FEET / 2), (sx * 0.60, y, Z_FEET / 2), 0.004))
    put("wood", bbox((0.69, 0.265, (Z_PLINTH - Z_FEET) / 2), (0, 0.265, (Z_PLINTH + Z_FEET) / 2), 0.012, 3))
    put("wood", bbox((0.655, 0.25, (Z_BASE - Z_PLINTH) / 2), (0, 0.25, (Z_PLINTH + Z_BASE) / 2), 0.010, 3))
    # recessed carved panel in the base front (certain: gilt scroll ornament on a centre panel)
    put("wood", bbox((0.265, 0.004, 0.058), (0, 0.502, 0.255), 0.004))
    for sx in (-1, 1):                       # raised side panels + gilt reed pairs at the outer ends
        put("wood", bbox((0.15, 0.004, 0.058), (sx * 0.46, 0.502, 0.255), 0.004))
        for dx in (-0.012, 0.012):
            A["gilt"].add(E2.poly_tube("reed", [(sx * 0.595 + dx, 0.506, 0.20), (sx * 0.595 + dx, 0.506, 0.31)], 0.0045, False, 2))
    for sx in (-1, 1):                       # gilt border lines of the centre panel
        A["gilt"].add_box(0.0025, 0.0018, 0.058, (sx * 0.262, 0.5075, 0.255))
    A["gilt"].add_box(0.265, 0.0018, 0.0025, (0, 0.5075, 0.311)); A["gilt"].add_box(0.265, 0.0018, 0.0025, (0, 0.5075, 0.199))
    # scroll ornament: mirrored spirals + centre flourish
    for sx in (-1, 1):
        for (cx0, r0) in ((0.10, 0.034), (0.20, 0.028)):
            pts = []
            for i in range(30):
                t = i / 29
                a = math.pi * (0.3 + 2.6 * t) * (1 if sx > 0 else -1)
                r = r0 * (1 - 0.78 * t)
                pts.append((sx * cx0 + r * math.cos(a), 0.5085, 0.255 + r * math.sin(a)))
            A["gilt"].add(E2.poly_tube("scroll", pts, 0.0035, False, 2))
        A["gilt"].add(E2.poly_tube("vine", [(sx * (0.005 + 0.28 * i / 20), 0.5085, 0.255 + 0.020 * math.sin(i * 0.9)) for i in range(21)], 0.0028, False, 2))
    A["gilt"].add(sphere(0.012, (1, 0.5, 1), (0, 0.508, 0.255)))

    # side panels, back, top of carcass, bottom board (interior wood on the inside)
    put("wood", bbox((0.012, BODY_D / 2, (Z_FRIEZE0 - Z_BASE) / 2), (-BODY_HW + 0.012, BODY_D / 2, (Z_FRIEZE0 + Z_BASE) / 2), 0.002))
    put("wood", bbox((0.012, BODY_D / 2, (Z_FRIEZE0 - Z_BASE) / 2), (BODY_HW - 0.012, BODY_D / 2, (Z_FRIEZE0 + Z_BASE) / 2), 0.002))
    A["wood_in"].add_box(BODY_HW - 0.02, 0.01, (Z_FRIEZE0 - Z_BASE) / 2, (0, 0.012, (Z_FRIEZE0 + Z_BASE) / 2))
    A["wood_in"].add_box(BODY_HW - 0.02, BODY_D / 2 - 0.02, 0.01, (0, BODY_D / 2, SHELF_Z[0] - 0.01))
    A["wood_in"].add_box(BODY_HW - 0.02, BODY_D / 2 - 0.02, 0.01, (0, BODY_D / 2, Z_INT_TOP + 0.01))
    for z in SHELF_Z[1:]:
        A["wood_in"].add_box(BODY_HW - 0.03, 0.18, 0.009, (0, 0.19, z - 0.009))
    # frieze body
    put("wood", bbox((BODY_HW, BODY_D / 2, (Z_FRIEZE1 - Z_FRIEZE0) / 2), (0, BODY_D / 2, (Z_FRIEZE0 + Z_FRIEZE1) / 2), 0.004))
    put("wood", bbox((0.52, 0.004, 0.055), (0, BODY_D + 0.003, 1.915), 0.004))    # raised frieze panel behind the garland

    # ---- cornice (certain: heavy stepped crown, wider than the body) ----------------------------------------------
    put("wood", bbox((0.69, 0.26, 0.015), (0, 0.26, Z_FRIEZE1 + 0.015), 0.006, 3))
    put("wood", bbox((0.72, 0.27, 0.02), (0, 0.27, Z_FRIEZE1 + 0.060), 0.014, 4))
    put("wood", bbox((CORN_W / 2, CORN_D / 2, 0.02), (0, CORN_D / 2, Z_TOP - 0.02), 0.012, 3))
    for i in range(-30, 31):                                  # dentil row under the crown
        A["wood"].add_box(0.0085, 0.006, 0.007, (i * 0.0215, 0.275, Z_FRIEZE1 + 0.027))
    # corner blocks over the columns, each with a gilt rosette (certain)
    for sx in (-1, 1):
        put("wood", bbox((0.065, 0.032, (Z_FRIEZE1 - Z_FRIEZE0) / 2), (sx * COL_X, BODY_D + 0.035, (Z_FRIEZE0 + Z_FRIEZE1) / 2), 0.004))
    # finials on the cornice ends (certain)
    for sx in (-1, 1):
        prof = [(0.020, Z_TOP), (0.022, Z_TOP + 0.01), (0.012, Z_TOP + 0.025), (0.016, Z_TOP + 0.040), (0.007, Z_TOP + 0.058), (0.0, Z_TOP + 0.064)]
        prof[-1] = (0.0008, Z_TOP + 0.064)
        A["gilt"].add(lathe(prof, 16, sx * 0.69, 0.30))

    # ---- columns (certain: fluted wood shaft + gilt capital/base, gilt acanthus collar and reeds in the lower third) --
    def flute(a, z):
        fade = min(1.0, max(0.0, (z - 0.40) / 0.05), max(0.0, (1.74 - z) / 0.05))
        s = abs(math.cos(6 * a))
        return 1.0 - 0.06 * fade * (1 - s) ** 5
    shaft_prof = [(COL_R, z) for z in (Z_BASE + 0.02, 0.40, 0.45, 1.05, 1.70, 1.74, 1.78)]
    for sx in (-1, 1):
        put("wood", lathe(shaft_prof, 72, sx * COL_X, 0.425, rfun=flute))
        A["gilt"].add(lathe([(0.050, Z_BASE), (0.054, Z_BASE + 0.012), (0.046, Z_BASE + 0.026), (0.044, Z_BASE + 0.04)], 28, sx * COL_X, 0.425))
        A["gilt"].add(lathe([(0.046, 1.74), (0.050, 1.765), (0.058, 1.800), (0.060, 1.832), (0.052, 1.842)], 28, sx * COL_X, 0.425))
        A["gilt"].add(lathe([(0.044, 0.62), (0.052, 0.65), (0.054, 0.68), (0.047, 0.72), (0.044, 0.74)], 28, sx * COL_X, 0.425))
        for k in range(9):                                    # gilt reeds on the visible (front) half
            a = math.radians(-85 + k * 21)
            A["gilt"].add(E2.poly_tube("reed", [(sx * COL_X + (COL_R + 0.001) * math.cos(a), 0.425 + (COL_R + 0.001) * math.sin(a), 0.82),
                                                (sx * COL_X + (COL_R + 0.001) * math.cos(a), 0.425 + (COL_R + 0.001) * math.sin(a), 0.97)], 0.0034, False, 2))
        for k in range(10):                                   # acanthus leaf hints on the collar
            a = math.radians(-100 + k * 22)
            A["gilt"].add(sphere(0.011, (1, 1, 2.2), (sx * COL_X + 0.052 * math.cos(a), 0.425 + 0.052 * math.sin(a), 0.69)))
        for k in range(10):                                   # capital leaves
            a = math.radians(-100 + k * 22)
            A["gilt"].add(sphere(0.013, (1, 1, 2.4), (sx * COL_X + 0.056 * math.cos(a), 0.425 + 0.056 * math.sin(a), 1.80)))

    # ---- doors: frames, glass, inner beads, corner rosettes -------------------------------------------------------
    gz0, gz1 = Z_GLASS0, Z_GLASS1
    for sx in (-1, 1):
        x_in, x_out = 0.05, 0.54                  # door spans x from the centre stile edge to the column
        gx0, gx1 = x_in, x_out - 0.05             # glass opening (0.44 wide)
        xc = sx * (gx0 + gx1) / 2; hw = (gx1 - gx0) / 2
        zc = (gz0 + gz1) / 2; hh = (gz1 - gz0) / 2
        # stiles and rails (door frame, 0.03 thick at y=DOOR_Y..)
        put("wood", bbox((0.05, 0.015, (Z_FRIEZE0 - Z_BASE) / 2), (sx * 0.05, DOOR_Y + 0.015, (Z_FRIEZE0 + Z_BASE) / 2 - 0.0), 0.004))  # meeting stile half
        put("wood", bbox((0.025, 0.015, (Z_FRIEZE0 - Z_BASE) / 2), (sx * (x_out - 0.025), DOOR_Y + 0.015, (Z_FRIEZE0 + Z_BASE) / 2), 0.004))
        put("wood", bbox(((x_out - 0.0) / 2 - 0.0, 0.015, (gz0 - Z_BASE) / 2), (sx * (x_out / 2), DOOR_Y + 0.015, (gz0 + Z_BASE) / 2), 0.004))
        put("wood", bbox((x_out / 2, 0.015, (Z_FRIEZE0 - gz1) / 2), (sx * (x_out / 2), DOOR_Y + 0.015, (gz1 + Z_FRIEZE0) / 2), 0.004))
        # glass
        A["glass"].add_box(hw + 0.004, 0.002, hh + 0.004, (xc, DOOR_Y + 0.016, zc))
        # inner bead (stepped "frame in frame")
        b = 0.013
        A["wood"].add_box(hw + 0.004, 0.008, b / 2, (xc, DOOR_Y + 0.026, gz1 - b / 2 + 0.002))
        A["wood"].add_box(hw + 0.004, 0.008, b / 2, (xc, DOOR_Y + 0.026, gz0 + b / 2 - 0.002))
        A["wood"].add_box(b / 2, 0.008, hh + 0.004, (xc - hw + b / 2 - 0.002, DOOR_Y + 0.026, zc))
        A["wood"].add_box(b / 2, 0.008, hh + 0.004, (xc + hw - b / 2 + 0.002, DOOR_Y + 0.026, zc))
        # gilt corner rosettes (certain: square plates at the glass corners)
        for (rx, rz) in ((xc - hw - 0.002, gz1 + 0.012), (xc + hw + 0.002, gz1 + 0.012), (xc - hw - 0.002, gz0 - 0.012), (xc + hw + 0.002, gz0 - 0.012)):
            A["gilt"].add_box(0.019, 0.003, 0.019, (rx, DOOR_Y + 0.033, rz))
            A["gilt"].add(sphere(0.0105, (1, 0.45, 1), (rx, DOOR_Y + 0.036, rz)))
            for (ox, oz) in ((-0.011, -0.011), (0.011, -0.011), (-0.011, 0.011), (0.011, 0.011)):
                A["gilt"].add(sphere(0.0048, (1, 0.5, 1), (rx + ox, DOOR_Y + 0.036, rz + oz), 8, 4))
    # keyhole + tag on the centre stile (certain)
    A["brass"].add_box(0.007, 0.002, 0.016, (0.0, DOOR_Y + 0.032, 1.07))
    A["brass"].add(sphere(0.0065, (1, 0.5, 1), (0.0, DOOR_Y + 0.034, 1.09), 8, 4))
    A["paper"].add_box(0.017, 0.0016, 0.027, (0.012, DOOR_Y + 0.034, 0.93))
    A["paper"].add(E2.poly_tube("string", [(0.0, DOOR_Y + 0.034, 1.065), (0.008, DOOR_Y + 0.035, 0.99), (0.012, DOOR_Y + 0.035, 0.958)], 0.0008, False, 2))

    # ---- gilt frieze garland: 6 swags with leaves + tassels (certain) -----------------------------------------------
    nsw, span = 6, 0.52
    ys = BODY_D + 0.008
    for k in range(nsw):
        x0 = -span + k * (2 * span / nsw); x1 = x0 + 2 * span / nsw
        pts = []
        for i in range(19):
            t = i / 18
            pts.append((x0 + (x1 - x0) * t, ys, 1.935 - 0.028 * math.sin(math.pi * t)))
        A["gilt"].add(E2.poly_tube("swag", pts, 0.0048, False, 2))
        for i in range(1, 18):
            px, py, pz = pts[i]
            A["gilt"].add(sphere(0.010, (1.6, 0.7, 0.9), (px, py + 0.002, pz + (0.003 if i % 2 else -0.003))))
        A["gilt"].add(sphere(0.0075, (1, 0.8, 1), (x0, ys, 1.935)))          # rosette knot at the swag top
        A["gilt"].add(E2.poly_tube("tassel", [(x0, ys, 1.930), (x0, ys, 1.885)], 0.0028, False, 2))
        A["gilt"].add(sphere(0.0055, (1, 0.8, 1.6), (x0, ys, 1.882)))
    A["gilt"].add(sphere(0.0075, (1, 0.8, 1), (span, ys, 1.935)))
    A["gilt"].add(E2.poly_tube("tassel", [(span, ys, 1.930), (span, ys, 1.885)], 0.0028, False, 2))
    A["gilt"].add(sphere(0.0055, (1, 0.8, 1.6), (span, ys, 1.882)))
    for sx in (-1, 1):                                                        # corner-block rosettes
        rx, rz = sx * COL_X, 1.915
        A["gilt"].add_box(0.026, 0.003, 0.026, (rx, BODY_D + 0.069, rz))
        A["gilt"].add(sphere(0.016, (1, 0.5, 1), (rx, BODY_D + 0.072, rz)))
        for (ox, oz) in ((-0.017, 0), (0.017, 0), (0, -0.017), (0, 0.017)):
            A["gilt"].add(sphere(0.0065, (1, 0.5, 1), (rx + ox, BODY_D + 0.072, rz + oz), 8, 4))

    # ---- books (inferred individually, certain in palette/arrangement: dense rows, gold bands, a few leaning) ---------
    bag = [nm for nm, (_c, w) in BOOK_COLOURS.items() for _ in range(w)]
    x_lo, x_hi, y_front = -0.575, 0.575, 0.325
    for ci in range(len(SHELF_Z)):
        zb = SHELF_Z[ci]
        zt = SHELF_Z[ci + 1] - 0.018 if ci + 1 < len(SHELF_Z) else Z_INT_TOP
        clear = zt - zb
        tall = (ci == 0)
        x = x_lo + rng.uniform(0, 0.02)
        while x < x_hi - 0.03:
            w = rng.uniform(0.017, 0.040) if not tall else rng.uniform(0.022, 0.050)
            h = clear * (rng.uniform(0.60, 0.92) if tall else rng.uniform(0.72, 0.96))
            d = rng.uniform(0.17, 0.25)
            nm = rng.choice(bag)
            yb = y_front - d + rng.uniform(-0.015, 0.0)
            key = "bk_" + nm
            lean = rng.random() < 0.05
            if lean:
                me = bbox((w / 2, d / 2, h / 2), (0, 0, 0), 0.0008, 1)
                me.transform(Matrix.Translation((x + w / 2 + 0.02, yb + d / 2, zb + h / 2)) @
                             Matrix.Translation((0, 0, -h / 2)) @ Matrix.Rotation(math.radians(-rng.uniform(8, 16)), 4, 'Y') @ Matrix.Translation((0, 0, h / 2)))
                A[key].add(me); x += w + 0.045
                continue
            A[key].add_box(w / 2, d / 2, h / 2, (x + w / 2, yb + d / 2, zb + h / 2))
            yfront = yb + d + 0.0008
            nb = rng.choice((0, 2, 2, 3))
            if h > 0.13:
                for j in range(nb):
                    zz = zb + h * (0.82 - j * 0.07 - (0.03 if nb == 3 else 0))
                    A["gilt"].add_box(w / 2 + 0.0004, 0.0009, 0.0016, (x + w / 2, yfront, zz))
                if rng.random() < 0.4:
                    A["label"].add_box(w * 0.38, 0.0008, h * 0.09, (x + w / 2, yfront + 0.0004, zb + h * 0.62))
            x += w + rng.choice((0, 0, 0.001, 0.002))
            if tall and rng.random() < 0.03:
                x += rng.uniform(0.03, 0.10)            # a gap in the tall compartment, as in the photo

    # ---- turn the accumulators into objects ----------------------------------------------------------------------------
    for key, acc in A.items():
        if not acc.v:
            continue
        me = acc.mesh("Bookcase_" + key)
        me.materials.append(M[key])
        o = D.objects.new("Bookcase_" + key, me); coll.objects.link(o)
        o.parent = root
    return root


# ================================================================ moving things
def _world_bbox(objs):
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in objs:
        if o.type != 'MESH':
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return lo, hi


def move_group(objs, T):
    """Apply world transform T to a set of objects (children of members follow their parents)."""
    s = set(objs)
    for o in objs:
        if o.parent in s:
            continue
        o.matrix_world = T @ o.matrix_world


def apply():
    coll = D.collections["Right_Nook"]
    bpy.context.view_layer.update()

    # 1. remove the old half shelf (Shelf_*, ShelfBook_*, ShelfStack_* and their title text)
    old = [o for o in D.objects if o.name.startswith("Shelf")]
    for o in sorted(old, key=lambda o: o.parent is not None, reverse=True):
        data = o.data
        D.objects.remove(o, do_unlink=True)
        if data is not None and getattr(data, "users", 1) == 0:
            (D.meshes if isinstance(data, bpy.types.Mesh) else D.curves).remove(data)
    print("e03: removed", len(old), "objects of the old wall shelf", flush=True)

    # 2. the new bookcase
    build_bookcase(coll)

    # 3. side table (+ its books) -> back-right corner
    table = [o for o in D.objects if o.name.startswith(("SideTable", "TableBook"))]
    move_group(table, Matrix.Translation((TABLE_DX, 0, 0)))

    # 4. club chair: turned toward the desk, back corner on the right wall, in front of the bookcase base
    root = D.objects["Chair_Root"]
    root.rotation_euler = (0.0, 0.0, math.pi / 2 - math.radians(CHAIR_TURN_DEG))
    bpy.context.view_layer.update()
    parts = [o for o in root.children_recursive if o.type == 'MESH']      # the club chair only (the desk chair is also Chair_*)
    lo, hi = _world_bbox(parts)
    root.location.x += CHAIR_WALL_X - hi.x
    root.location.y += CHAIR_YMAX - hi.y
    bpy.context.view_layer.update()
    lo, hi = _world_bbox(parts)
    print("e03: chair bbox", [round(v, 3) for v in lo], [round(v, 3) for v in hi], flush=True)

    # 5. floor lamp: 4 cm in front of the chair front (base edge to the chair's front plane), on the table side
    th = root.rotation_euler.z
    fwd = Vector((-math.sin(th), math.cos(th), 0.0))          # chair front direction (world)
    side = Vector((math.cos(th), math.sin(th), 0.0))          # chair local +X (table side)
    front_extent = 0.48 + 0.024                               # arm-scroll front plane in chair-local y
    base_r = 0.13
    base_c = Vector((root.location.x, root.location.y, 0.0))
    target = base_c + fwd * (front_extent + LAMP_GAP + base_r) + side * LAMP_LATERAL
    lamp = [o for o in D.objects if o.name.startswith("SLamp")]
    cur = Vector((3.30, 2.28, 0.0))                           # lamp pole centre in the V2 scene
    d = target - cur
    move_group(lamp, Matrix.Translation(d))
    L3 = D.objects.get("L3_FloorLamp")
    if L3 is not None:
        L3.location += d
    print("e03: lamp centre", tuple(round(v, 3) for v in target), flush=True)

    # 6. floor carton leaves the bookcase footprint
    carton = [o for o in D.objects if o.name.startswith("Carton")]
    move_group(carton, Matrix.Translation((CARTON_SHIFT[0], CARTON_SHIFT[1], 0)))

    # 7. report overlaps of the new/moved things with other furniture (bounding boxes, informational)
    bpy.context.view_layer.update()
    mine = [o for o in D.objects if o.name.startswith(("Bookcase_", "SideTable", "TableBook", "SLamp", "Carton")) and o.type == 'MESH']
    mine += parts
    groups = {}
    for o in mine:
        g = "ClubChair" if o in parts else o.name.split("_")[0]
        groups.setdefault(g, []).append(o)
    gb = {g: _world_bbox(v) for g, v in groups.items()}
    names = list(gb)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            (a0, a1), (b0, b1) = gb[names[i]], gb[names[j]]
            if all(a0[k] < b1[k] - 0.005 and a1[k] > b0[k] + 0.005 for k in range(3)):
                print("e03: bbox overlap", names[i], names[j], flush=True)
    for g, (lo, hi) in gb.items():
        print("e03:", g, [round(v, 2) for v in lo], [round(v, 2) for v in hi], flush=True)
    for o in D.objects:
        if o.type != 'MESH' or o in mine or o.name.startswith(("Wall_", "Floor", "Ceiling", "Baseboard", "Room")):
            continue
        if any(c.name in ("Outside", "Camera", "Lights") for c in o.users_collection):
            continue
        for g, (lo, hi) in gb.items():
            ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
            omin = [min(w[i] for w in ws) for i in range(3)]; omax = [max(w[i] for w in ws) for i in range(3)]
            if all(omin[i] < hi[i] - 0.01 and omax[i] > lo[i] + 0.01 for i in range(3)):
                print("e03: OVERLAP", g, "with", o.name, [round(v, 2) for v in omin], [round(v, 2) for v in omax], flush=True)
                break
