"""Edit #6a (user request 2026-11-01): replace the Pakistan + USA flags on the back wall with two antique bronze
wall clocks (Karachi on the left, Houston on the right, each with its name written above it), above the two
degree frames that stay where they are. The old small clock on the left wall is removed.

Reference analysis (ornate bronze antique wall clock photo):
  certain  - round case with a thick moulded bezel, aged cream dial, black Roman numerals, minute track, spade hands,
             a fleur-de-lis crest with scrolls on top, a small pendant at the bottom, dark-bronze patina.
  inferred - real size (dial 38 cm, overall 0.62 m tall), exact scroll shape, hand shape, patina pattern, glass (omitted,
             a bake cannot hold glass; the web build adds a faint reflective pane).
Time zones: Houston is 10 h behind Karachi, so the static poses are Houston 10:10 and Karachi 8:10 (= 20:10).
Lettering is raised aged-brass letters fixed to the wall, written with a serif font (FreeSerif Bold).
All parts go to the Wall_Decor collection (the bake group that held the old clock).
"""
import bpy, bmesh, math, os, importlib.util
from mathutils import Vector, Matrix

D = bpy.data
_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "e02_club_chair.py")
_s = importlib.util.spec_from_file_location("e02_club_chair", _p)
E2 = importlib.util.module_from_spec(_s); _s.loader.exec_module(E2)

WALL_Y = 2.498
ZC = 2.06                       # dial centre height
CLOCKS = [("Karachi", -2.11, (8, 10)), ("Houston", -1.52, (10, 10))]    # name, x centre (= centre of its degree frame), (h, m)
LABEL_Z = 2.52
FONT = "/usr/share/fonts/truetype/freefont/FreeSerif.ttf"
FONT_B = "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf"
OLD_CLOCK = {"Clock_Cap", "Clock_Face", "Clock_Frame", "Clock_Hour", "Clock_Minute"} | {f"Clock_Tick_{i}" for i in range(12)}
RX90 = Matrix.Rotation(math.radians(90), 4, 'X')        # local +Z (out of the dial) -> world -Y (into the room), local +Y -> world +Z


# ------------------------------------------------------------------ materials
def bronze_material(name, metallic=0.55, dark=(0.20, 0.12, 0.05), light=(0.70, 0.47, 0.20)):
    m = D.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear(); n = E2._n
    out = n(nt, "ShaderNodeOutputMaterial", 9, 0)
    b = n(nt, "ShaderNodeBsdfPrincipled", 7, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    tc = n(nt, "ShaderNodeTexCoord", 0, 0)
    ns = n(nt, "ShaderNodeTexNoise", 1, 0, noise_dimensions='3D')
    ns.inputs["Scale"].default_value = 60.0; ns.inputs["Detail"].default_value = 7.0; ns.inputs["Roughness"].default_value = 0.65
    nt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
    cr = n(nt, "ShaderNodeValToRGB", 3, 0)
    e = cr.color_ramp.elements
    e[0].position = 0.34; e[0].color = dark + (1,)
    e[1].position = 0.66; e[1].color = light + (1,)
    nt.links.new(ns.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = metallic
    rr = n(nt, "ShaderNodeMapRange", 3, -2)
    rr.inputs["To Min"].default_value = 0.30; rr.inputs["To Max"].default_value = 0.55
    nt.links.new(ns.outputs["Fac"], rr.inputs["Value"]); nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    ns2 = n(nt, "ShaderNodeTexNoise", 1, -3, noise_dimensions='3D')
    ns2.inputs["Scale"].default_value = 380.0; ns2.inputs["Detail"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], ns2.inputs["Vector"])
    bm = n(nt, "ShaderNodeBump", 5, -3)
    bm.inputs["Strength"].default_value = 0.18; bm.inputs["Distance"].default_value = 0.0004
    nt.links.new(ns2.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    return m


def dial_material(name):
    """Aged ivory enamel/paper: darker, stained toward the rim."""
    m = D.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear(); n = E2._n
    out = n(nt, "ShaderNodeOutputMaterial", 9, 0)
    b = n(nt, "ShaderNodeBsdfPrincipled", 7, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    tc = n(nt, "ShaderNodeTexCoord", 0, 0)
    ln = n(nt, "ShaderNodeVectorMath", 1, 1, operation='LENGTH')
    nt.links.new(tc.outputs["Object"], ln.inputs[0])
    rr = n(nt, "ShaderNodeMapRange", 2, 1)
    rr.inputs["From Min"].default_value = 0.05; rr.inputs["From Max"].default_value = 0.20
    nt.links.new(ln.outputs["Value"], rr.inputs["Value"])
    ns = n(nt, "ShaderNodeTexNoise", 1, -1, noise_dimensions='3D')
    ns.inputs["Scale"].default_value = 16.0; ns.inputs["Detail"].default_value = 8.0; ns.inputs["Roughness"].default_value = 0.62
    nt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
    sub = n(nt, "ShaderNodeMath", 3, -1, operation='SUBTRACT'); sub.inputs[1].default_value = 0.5
    nt.links.new(ns.outputs["Fac"], sub.inputs[0])
    mul = n(nt, "ShaderNodeMath", 4, -1, operation='MULTIPLY'); mul.inputs[1].default_value = 0.45
    nt.links.new(sub.outputs["Value"], mul.inputs[0])
    add = n(nt, "ShaderNodeMath", 5, 0, operation='ADD')
    nt.links.new(rr.outputs["Result"], add.inputs[0]); nt.links.new(mul.outputs["Value"], add.inputs[1])
    cr = n(nt, "ShaderNodeValToRGB", 6, 0)
    e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.74, 0.66, 0.47, 1)
    e[1].position = 1.0; e[1].color = (0.20, 0.14, 0.06, 1)
    e.new(0.42).color = (0.70, 0.61, 0.42, 1)
    e.new(0.78).color = (0.48, 0.37, 0.20, 1)
    nt.links.new(add.outputs["Value"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.72
    return m


def plain(name, col, rough, metallic=0.0):
    m = D.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    return m


# ------------------------------------------------------------------ geometry accumulator (one mesh per material)
class Acc:
    def __init__(self):
        self.b = {}

    def bm(self, mat):
        return self.b.setdefault(mat, bmesh.new())

    def _xf(self, bm, n0, M):
        bm.verts.ensure_lookup_table()
        for v in bm.verts[n0:]:
            v.co = M @ v.co

    def mesh(self, mat, me, M=Matrix.Identity(4)):
        bm = self.bm(mat); n0 = len(bm.verts)
        bm.from_mesh(me); self._xf(bm, n0, M)

    def cube(self, mat, hx, hy, hz, M):
        bm = self.bm(mat)
        bmesh.ops.create_cube(bm, size=2.0, matrix=M @ Matrix.Diagonal(Vector((hx, hy, hz, 1.0))))

    def flat(self, mat, pts, z0, th, M=Matrix.Identity(4)):
        """Extrude a 2D outline (list of (x, y), no duplicate points) from z0 up by th."""
        bm = self.bm(mat); n0 = len(bm.verts)
        vs = [bm.verts.new((x, y, z0)) for x, y in pts]
        f = bm.faces.new(vs)
        ret = bmesh.ops.extrude_face_region(bm, geom=[f])
        vv = [e for e in ret["geom"] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0, 0, th), verts=vv)
        self._xf(bm, n0, M)

    def build(self, prefix, coll, T):
        out = []
        for mat, bm in self.b.items():
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            me = D.meshes.new(f"{prefix}_{mat.name}"); bm.to_mesh(me); bm.free()
            E2.finish(me, 40)
            me.materials.append(mat)
            o = D.objects.new(f"{prefix}_{mat.name}", me); coll.objects.link(o)
            o.matrix_world = T
            out.append(o)
        self.b = {}
        return out


def lathe(profile, seg=72, close=False):
    """Solid of revolution about Z from an (r, z) profile (profile touching the axis, or closed with close=True)."""
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0, z)) for r, z in profile]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    if close:
        es.append(bm.edges.new((vs[-1], vs[0])))
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1), angle=math.tau, steps=seg)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = D.meshes.new("lathe"); bm.to_mesh(me); bm.free()
    return me


def text_mesh(body, size, extrude, font):
    cu = D.curves.new("txt", 'FONT'); cu.body = body; cu.size = size; cu.extrude = extrude
    cu.font = font; cu.font_bold = font; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    o = D.objects.new("txt", cu); E2._scene_tmp(o)
    bpy.context.view_layer.update()
    me = E2._evaluated_mesh(o)
    D.objects.remove(o, do_unlink=True); D.curves.remove(cu)
    return me


def lens(l, w, bend=0.0, n=14):
    """Pointed leaf outline from (0,0) to (bend, l); returns a polygon without duplicate points."""
    right, left = [], []
    for i in range(n + 1):
        t = i / n
        hw = w * math.sin(math.pi * t) ** 0.85
        cx = bend * t * t
        right.append((cx + hw, l * t)); left.append((cx - hw, l * t))
    return right + left[-2:0:-1]


def rot_pts(pts, ang, ox=0.0, oy=0.0):
    c, s = math.cos(ang), math.sin(ang)
    return [(ox + x * c - y * s, oy + x * s + y * c) for x, y in pts]


def volute_pts(s=1.0, fx=1.0, fy=1.0, ox=0.0, oy=0.0, z=0.036):
    """Scroll that rises from the bezel then curls inward (spiral), as 3D points."""
    r0, r1, turns = 0.060, 0.012, 2.3
    cx, cy = 0.060, 0.030                       # spiral centre relative to its start point
    pts = [(0.0, -0.010), (0.0, 0.0)]
    n = 40
    for i in range(n + 1):
        u = i / n
        th = math.pi - turns * math.pi * u
        r = r0 + (r1 - r0) * u
        pts.append((cx + r * math.cos(th), cy + r * math.sin(th)))
    return [Vector((ox + fx * s * x, oy + fy * s * y, z)) for x, y in pts]


def hand_outline(half, sx=1.0):
    return [(x, y) for x, y in half] + [(-x, y) for x, y in reversed(half[:-1])]


HOUR_HALF = [(0.0035, -0.030), (0.0045, -0.010), (0.0035, 0.020), (0.0030, 0.043), (0.0120, 0.056), (0.0165, 0.068),
             (0.0100, 0.082), (0.0, 0.100)]
MIN_HALF = [(0.0060, -0.040), (0.0035, -0.026), (0.0030, 0.030), (0.0022, 0.092), (0.0030, 0.104), (0.0085, 0.116),
            (0.0105, 0.128), (0.0060, 0.143), (0.0, 0.162)]


# ------------------------------------------------------------------ one clock
def build_clock(name, cx, hm, mats, coll):
    T = Matrix.Translation((cx, WALL_Y, ZC)) @ RX90
    A = Acc()
    bronze, dial, ink, hands = mats["bronze"], mats["dial"], mats["ink"], mats["hands"]

    # case + bezel + dial
    A.mesh(bronze, lathe([(0, 0), (0.205, 0), (0.214, 0.006), (0.217, 0.02), (0.214, 0.050), (0.205, 0.056), (0.192, 0.046), (0, 0.0452)]))   # open front: the dial sits in this cavity
    A.mesh(bronze, lathe([(0.190, 0.050), (0.204, 0.047), (0.226, 0.048), (0.236, 0.056), (0.238, 0.066), (0.232, 0.074),
                          (0.220, 0.078), (0.205, 0.074), (0.198, 0.066), (0.190, 0.060)], close=True))
    A.mesh(bronze, lathe([(0.2335, 0.040), (0.2395, 0.040), (0.2395, 0.047), (0.2335, 0.047)], seg=96, close=True))
    A.mesh(dial, lathe([(0, 0.0455), (0.192, 0.0455), (0.192, 0.049), (0, 0.049)]))
    A.mesh(ink, lathe([(0.1805, 0.0489), (0.1822, 0.0489), (0.1822, 0.0497), (0.1805, 0.0497)], seg=96, close=True))

    # minute track
    zt = 0.0496
    for i in range(60):
        a = math.radians(i * 6)
        R = Matrix.Rotation(-a, 4, 'Z')
        if i % 5 == 0:
            A.cube(ink, 0.0022, 0.0105, 0.0006, R @ Matrix.Translation((0, 0.1705, zt)))
        else:
            A.cube(ink, 0.0007, 0.0058, 0.0005, R @ Matrix.Translation((0, 0.1740, zt)))

    # Roman numerals (upright)
    numerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
    fnt = D.fonts.load(FONT)
    for k, txt in enumerate(numerals, start=1):
        a = math.radians(k * 30)
        me = text_mesh(txt, 0.031, 0.0009, fnt)
        A.mesh(ink, me, Matrix.Translation((0.126 * math.sin(a), 0.126 * math.cos(a), 0.0497 + 0.0009)))
        D.meshes.remove(me)

    # hands: hour below minute, brass cap on top
    h, m = hm
    for half, ang, z0, th, nm in ((HOUR_HALF, math.radians((h % 12) * 30 + m * 0.5), 0.0525, 0.0022, "h"),
                                  (MIN_HALF, math.radians(m * 6), 0.0550, 0.0022, "m")):
        A.flat(hands, hand_outline(half), z0, th, Matrix.Rotation(-ang, 4, 'Z'))
    A.mesh(bronze, lathe([(0, 0.0572), (0.0105, 0.0572), (0.0105, 0.0585), (0.0070, 0.0605), (0.0035, 0.0630), (0, 0.0635)], seg=32))

    # crest: plinth, band, fleur-de-lis (centre petal + two curling petals)
    A.mesh(bronze, E2.bevelled_box((0.030, 0.010, 0.010), (0, 0.246, 0.040), 0.004, 2))
    y0 = 0.256
    A.flat(bronze, lens(0.092, 0.0115), 0.032, 0.013, Matrix.Translation((0, y0, 0)))
    for sgn in (-1, 1):
        pet = rot_pts(lens(0.062, 0.0085, bend=sgn * 0.020), -sgn * math.radians(36), sgn * 0.004, y0 + 0.006)
        A.flat(bronze, pet, 0.032, 0.013)
    A.mesh(bronze, E2.bevelled_box((0.016, 0.0045, 0.0105), (0, y0 + 0.021, 0.0385), 0.0025, 2))
    # side scrolls flanking the crest, and smaller scrolls at the bottom
    for fx in (1, -1):
        A.mesh(bronze, E2.poly_tube("v", volute_pts(1.0, fx, 1.0, fx * 0.040, 0.224, 0.036), 0.0042, False, 4))
        A.mesh(bronze, E2.poly_tube("v", volute_pts(0.55, fx, -1.0, fx * 0.050, -0.226, 0.036), 0.0034, False, 4))
    # pendant under the case
    A.mesh(bronze, lathe([(0, 0), (0.013, 0), (0.021, 0.010), (0.024, 0.024), (0.015, 0.042), (0.008, 0.054), (0.010, 0.064),
                          (0, 0.072)], seg=40), Matrix.Translation((0, -0.236, 0.040)) @ Matrix.Rotation(math.radians(90), 4, 'X'))

    objs = A.build(f"WClock_{name}", coll, T)
    return objs


def build_label(name, cx, mat, coll):
    me = text_mesh(name, 0.075, 0.0035, D.fonts.load(FONT_B))
    A = Acc()
    A.mesh(mat, me, Matrix.Translation((0, 0, 0.0035 + 0.0005)))
    D.meshes.remove(me)
    return A.build(f"WClock_Label_{name}", coll, Matrix.Translation((cx, WALL_Y, LABEL_Z)) @ RX90)


def apply():
    coll = D.collections["Wall_Decor"]
    gone = [o for o in D.objects if o.name.startswith("Flag_") or o.name in OLD_CLOCK]
    print("e06: removing", len(gone), "objects (flags + old left-wall clock)", flush=True)
    for o in gone:
        D.objects.remove(o, do_unlink=True)

    mats = {
        "bronze": bronze_material("WClock_Bronze"),
        "dial": dial_material("WClock_Dial"),
        "ink": plain("WClock_Ink", (0.026, 0.020, 0.016, 1), 0.55),
        "hands": plain("WClock_Hands", (0.018, 0.016, 0.016, 1), 0.32, 0.6),
    }
    brass = bronze_material("WClock_LetterBrass", metallic=0.35, dark=(0.45, 0.30, 0.10), light=(0.88, 0.66, 0.30))
    parts = []
    for name, cx, hm in CLOCKS:
        parts += build_clock(name, cx, hm, mats, coll)
        parts += build_label(name, cx, brass, coll)

    bpy.context.view_layer.update()
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in parts:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    print("e06: clocks+labels bbox", [round(v, 3) for v in lo], [round(v, 3) for v in hi], flush=True)
    for o in D.objects:
        if o.type != 'MESH' or o in parts or o.name.startswith(("Wall_", "Floor", "Ceiling", "Room")):
            continue
        if any(c.name in ("Outside", "Camera", "Lights") for c in o.users_collection):
            continue
        ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
        omin = [min(w[i] for w in ws) for i in range(3)]; omax = [max(w[i] for w in ws) for i in range(3)]
        if all(omin[i] < hi[i] - 0.002 and omax[i] > lo[i] + 0.002 for i in range(3)):
            print("e06: OVERLAP with", o.name, [round(v, 2) for v in omin], [round(v, 2) for v in omax], flush=True)
