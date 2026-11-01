"""Retro beige desktop PC with CRT monitor, keyboard and mouse (left-wall computer).

Reference: refs/ref_retro_pc.jpg (a game-style render of a 1980s/90s beige desktop PC; its on-case brand
text is not copied, the badge here says SAKINA).
Certain from the photo: low desktop case with ribbed grille at the left, black display strip above it, drive
bezel with two floppy slots at the right, label plate below it, side vent slits; deep-bezel CRT monitor on a
tilt/swivel plate, turned a little to the left of the case; separate compact keyboard with darker modifier /
function keys; two-button mouse with a cable running back to the case; yellowed cream plastic.
Inferred: absolute sizes, key layout, rear panel, wear.

Local frame: origin = centre of the case footprint on the desk surface, front faces -Y, +X = viewer's right.
Room placement (left-wall cabinet): see INTEGRATION.md.
Env: TEX_PX (default 2048), SKIP_BAKE=1.
"""
import json
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_lib"))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "crt"))
import common as C            # noqa: E402
import materials as M         # noqa: E402
import materials_pc as MP     # noqa: E402
from build_crt import rrect, loop, bridge, rbox, join, text_obj   # noqa: E402  (helpers only; no side effects)

NAME = "retro_pc"
TEX_PX = int(os.environ.get("TEX_PX", "2048"))
SWIVEL_DEG = float(os.environ.get("SWIVEL_DEG", "-16"))       # negative = monitor turned toward the viewer's left (-X)

# case (front plane y = 0, body extends to +Y)
CW, CD, CH = 0.440, 0.300, 0.115
HW = CW / 2
# monitor (built facing -Y with its front plane at y = MY0, then swivelled about the stand axis)
STAND_Y = 0.150
MZ0 = CH + 0.030                  # underside of the monitor housing
MW, MH = 0.385, 0.335             # bezel outer size
MY0 = 0.050                       # bezel front plane
BEZ_D = 0.060
BACK = 0.280                      # housing back plane (before swivel)
OPEN = (0.300, 0.224, 0.018)      # opening in the bezel face
FUN = (0.282, 0.208, 0.012)       # end of the funnel = picture edge
FUN_Y = 0.036                     # funnel depth behind the bezel face
SC_Z = MZ0 + 0.178                # picture centre height


def tm(bm, fn):
    for v in bm.verts:
        v.co = fn(v.co)
    return bm


def merge_into(dst, src):
    tmp = bpy.data.meshes.new("_t")
    src.to_mesh(tmp)
    src.free()
    dst.from_mesh(tmp)
    bpy.data.meshes.remove(tmp)


def box(size, loc, bevel=0.002, seg=2):
    return rbox(size, loc, bevel, seg)


# ------------------------------------------------------------------ images
def make_images(d):
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    d.mkdir(parents=True, exist_ok=True)
    def font(px):
        for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                  "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"):
            if os.path.exists(p):
                return ImageFont.truetype(p, px)
        return ImageFont.load_default(size=px)
    w, h = 1024, 768
    im = Image.new("RGB", (w, h), (3, 7, 4))
    px = im.load()
    for y in range(h):                       # CRT vignette
        for x in range(w):
            u, v = (x / w - 0.5) * 2, (y / h - 0.5) * 2
            k = max(0.0, 1 - 0.50 * (u * u + v * v)) ** 1.4
            px[x, y] = (int(3 + 3 * k), int(8 + 9 * k), int(5 + 5 * k))
    dr = ImageDraw.Draw(im)
    f = font(25)
    lines = [
        "/* portfolio boot: show the selected project, or null */",
        "public Project getProject(int id) {",
        "    return projects.get(id);",
        "}",
        "",
        "/* Simple main program to start it running */",
        "public static void main(String[] args) {",
        "    final JFrame f = new JFrame(\"Sakina\");",
        "    final Panel   p = new Panel(rooms);",
        "    Container c = f.getContentPane();",
        "    c.add(p, BorderLayout.CENTER);",
        "",
        "    Button tapes = new Button(\"Open tapes\");",
        "    c.add(tapes);",
        "",
        "    Label hi = new Label(\"hello, world\", CENTER);",
        "    c.add(hi);",
        "",
        "    // Now that the button and the label are ready,",
        "    tapes.addActionListener(play);",
    ]
    for i, t in enumerate(lines):
        dr.text((60, 46 + i * 31), t, font=f, fill=(96, 236, 120))
    glow = im.filter(ImageFilter.GaussianBlur(5))
    im = Image.blend(im, glow, 0.45)
    p = d / "pc_screen.png"
    im.save(p)
    return p


# ------------------------------------------------------------------ case
def case_parts(col, mats):
    m_beige, m_dark, m_glass, m_led, m_rubber = mats
    bm = box((CW, CD, CH), (0, CD / 2, CH / 2 + 0.004), 0.006, 3)          # sits on 4 mm feet
    # ribs of the front grille (left)
    gx0, gx1 = -0.205, -0.040
    for i in range(13):
        merge_into(bm, box(((gx1 - gx0), 0.0024, 0.0030), ((gx0 + gx1) / 2, -0.0010, 0.026 + 0.0054 * i), 0.0007, 1))
    # side vent surround ribs (right side, +X)
    case = join("PC_Case", [bm], col, m_beige, 38)

    dark = []
    dark.append(box(((gx1 - gx0), 0.0008, 0.074), ((gx0 + gx1) / 2, -0.0002, 0.058), 0.0002, 1))     # grille backing
    dark.append(box((0.088, 0.0016, 0.019), (-0.160, -0.0006, 0.099), 0.0012, 2))                 # display strip
    dark.append(box((0.168, 0.0030, 0.062), (0.124, -0.0006, 0.080), 0.0016, 2))                  # drive bezel
    dark.append(box((0.130, 0.0034, 0.0075), (0.114, -0.0014, 0.091), 0.0010, 1))                 # upper slot
    dark.append(box((0.112, 0.0034, 0.0060), (0.108, -0.0014, 0.066), 0.0010, 1))                 # lower slot
    for i in range(11):                                                                           # right side vent slits
        dark.append(box((0.0007, 0.0042, 0.070), (HW + 0.0001, 0.070 + i * 0.0125, 0.062), 0.0002, 1))
    join("PC_Dark", dark, col, m_dark, 50)

    # lighter detail: label plate, eject lever + button
    det = []
    det.append(box((0.168, 0.0016, 0.026), (0.124, -0.0012, 0.032), 0.0010, 2))                   # label plate (beige)
    det.append(box((0.020, 0.0036, 0.0045), (0.168, -0.0020, 0.091), 0.0008, 2))                  # upper latch
    det.append(box((0.012, 0.0036, 0.0045), (0.160, -0.0020, 0.066), 0.0008, 2))                  # eject button
    join("PC_Detail", det, col, m_beige, 40)

    leds = []
    for i, x in enumerate((-0.190, -0.178, -0.166)):
        b = bmesh.new()
        bmesh.ops.create_uvsphere(b, u_segments=10, v_segments=6, radius=0.0016)
        tm(b, lambda p, x=x: Vector((x + p.x, -0.0016 + p.y * 0.4, 0.099 + p.z)))
        leds.append(b)
    join("PC_LED", leds, col, m_led, 60)

    feet = [box((0.030, 0.030, 0.006), (sx * 0.175, y, 0.003), 0.0016, 2) for sx in (-1, 1) for y in (0.035, 0.265)]
    join("PC_Feet", feet, col, m_rubber, 40)

    # badge text on the label plate
    ink = flat_mat("PC_Ink", "#4d4638", 0.7)
    t = text_obj("PC_LabelText", "SAKINA  PC", 0.0105, (0.124, -0.0022, 0.032), col, ink, 0.0004)
    t.scale = (1, 1, 1)
    return case


def flat_mat(name, color, rough=0.5, metal=0.0, coat=0.0):
    return MP.flat(name, color, rough, metal, coat)


# ------------------------------------------------------------------ monitor
def monitor_parts(col, mats, screen_p):
    m_beige, m_dark, m_glass, m_led, m_rubber = mats
    zb = MZ0
    zc = SC_Z
    # bezel: front ring + funnel
    bm = bmesh.new()
    o_f = loop(bm, rrect(0, zb + MH / 2, MW, MH, 0.026), MY0)
    op = loop(bm, rrect(0, zc, *OPEN), MY0)
    fu = loop(bm, rrect(0, zc, *FUN), MY0 + FUN_Y)
    o_b = loop(bm, rrect(0, zb + MH / 2, MW - 0.006, MH - 0.010, 0.024), MY0 + BEZ_D)
    bridge(bm, o_f, op)
    bridge(bm, op, fu)
    bridge(bm, o_b, o_f)
    bm.faces.new(list(reversed(o_b)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    front = [e for e in bm.edges if all(v in o_f for v in e.verts)]
    bmesh.ops.bevel(bm, geom=front, offset=0.006, segments=4, affect="EDGES", clamp_overlap=True)
    opn = [e for e in bm.edges if all(v.is_valid and v in op for v in e.verts)]
    bmesh.ops.bevel(bm, geom=opn, offset=0.0022, segments=2, affect="EDGES", clamp_overlap=True)
    # housing: tapering funnel behind the bezel
    specs = [(MY0 + BEZ_D - 0.002, MW - 0.006, MH - 0.010, 0.024), (MY0 + 0.095, MW - 0.012, MH - 0.020, 0.030),
             (MY0 + 0.150, 0.300, 0.270, 0.045), (BACK - 0.040, 0.235, 0.215, 0.050), (BACK, 0.205, 0.185, 0.050)]
    loops = [loop(bm, rrect(0, zb + 0.5 * (MH - 0.010) + 0.005 - (MH - 0.010 - h) * 0.40, w, h, r), y)
             for (y, w, h, r) in specs]
    for a, b in zip(loops, loops[1:]):
        bridge(bm, b, a)
    bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    back = [e for e in bm.edges if all(v in loops[-1] for v in e.verts)]
    bmesh.ops.bevel(bm, geom=back, offset=0.012, segments=3, affect="EDGES", clamp_overlap=True)
    bez = C.mesh_obj("PC_Monitor", bm, col)
    bez.data.materials.append(m_beige)
    C.shade_auto(bez, 38)

    # curved glass
    hw, hh = FUN[0] / 2, FUN[1] / 2
    nx, nz = 32, 24
    g = bmesh.new()
    uv = g.loops.layers.uv.new("UVMap")
    grid = []
    for j in range(nz + 1):
        row = []
        for i in range(nx + 1):
            x = -hw + 2 * hw * i / nx
            z = -hh + 2 * hh * j / nz
            y = MY0 + FUN_Y + 0.003 - 0.008 * (1 - 0.5 * ((x / hw) ** 2 + (z / hh) ** 2))
            row.append(g.verts.new((x, y, zc + z)))
        grid.append(row)
    for j in range(nz):
        for i in range(nx):
            f = g.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for l in f.loops:
                p = l.vert.co
                l[uv].uv = ((p.x + hw) / (2 * hw), (p.z - zc + hh) / (2 * hh))
    bmesh.ops.recalc_face_normals(g, faces=g.faces)
    for f in g.faces:
        if f.normal.y > 0:
            f.normal_flip()
    scr = C.mesh_obj("PC_Screen", g, col, smooth=True)
    scr.data.materials.append(MP.screen("PC_Glass", screen_p))

    # badge under the bezel, left; power LED + button right
    ink = flat_mat("PC_Ink", "#4d4638", 0.7)
    t = text_obj("PC_Badge", "SAKINA", 0.0085, (-0.120, MY0 - 0.0022, zb + 0.0115), col, ink, 0.0004)
    # power button, bottom right of the bezel, 4 cm above the bottom edge: square red cap in a dark square recess, green LED to its left
    PWX, PWZ = 0.150, zb + 0.0115 + 0.040
    def cylY(r, depth, x, y, z, seg=40):                      # cylinder along the Y axis, centred at (x, y, z)
        c = bmesh.new()
        bmesh.ops.create_cone(c, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=depth)
        tm(c, lambda q: Vector((x + q.x, y + q.z, z + q.y)))
        return c
    ring = join("PC_MonPwrRing", [box((0.025, 0.003, 0.025), (PWX, MY0 - 0.0005, PWZ), 0.0015, 2)], col, m_dark, 40)
    cap = join("PC_MonPwrButton", [box((0.017, 0.006, 0.017), (PWX, MY0 - 0.0030, PWZ), 0.0020, 3)], col,
               flat_mat("PC_RedButton", "#a8231c", 0.35, 0.0, 0.3), 40)
    led = join("PC_MonPwrLED", [cylY(0.0021, 0.0020, PWX - 0.0225, MY0 - 0.0011, PWZ, 16)], col, M.emissive("PC_LED_Green", "#5dff7a", 4.0), 40)
    pw = ring
    pw_extra = [cap, led]
    # stand: fixed foot plate + pivot + swivel plate (rotates with the monitor)
    foot = join("PC_StandFoot", [box((0.300, 0.230, 0.007), (0, STAND_Y, CH + 0.004 + 0.0035), 0.0035, 3)], col, m_beige, 40)
    cyl = bmesh.new()
    bmesh.ops.create_cone(cyl, cap_ends=True, segments=36, radius1=0.070, radius2=0.060, depth=0.014)
    tm(cyl, lambda p: Vector((p.x, STAND_Y + p.y, CH + 0.011 + 0.007 + p.z)))
    pivot = join("PC_StandPivot", [cyl], col, m_beige, 50)
    swivel = join("PC_StandSwivel", [box((0.245, 0.200, 0.010), (0, STAND_Y, MZ0 - 0.005), 0.004, 3)], col, m_beige, 40)
    return bez, scr, [t, pw, cap, led, swivel], foot, pivot


# ------------------------------------------------------------------ keyboard + mouse
KB_P = 0.0168
KB_ROWS = [
    # (fn keys, main widths, numpad widths)
    ([1, 1], [1] * 13 + [2], [1, 1, 1, 1]),
    ([1, 1], [1.5] + [1] * 12 + [1.5], [1, 1, 1, 1]),
    ([1, 1], [1.75] + [1] * 11 + [2.25], [1, 1, 1, 1]),
    ([1, 1], [2.25] + [1] * 10 + [2.75], [1, 1, 1, 1]),
    ([1, 1], [1.5, 1.5, 1.5, 6, 1.5, 1.5, 1.5], [2, 1, 1]),
]
KB_X, KB_Y = -0.47, 0.005   # keyboard stands to the LEFT of the case (-X local), roughly level with it; mouse stays right of the case
KB_TILT = 5.0


def key_bm(w, d, h):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        top = v.co.z > 0
        s = 0.82 if top else 1.0
        v.co = Vector((v.co.x * w * s, v.co.y * d * s, 0.0105 + (0.5 + v.co.z) * h))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.0013, segments=1, affect="EDGES", clamp_overlap=True)
    return bm


def keyboard(col, m_beige, m_keydark):
    caps, darks = [], []
    rows = len(KB_ROWS)
    total_u = 2 + 0.5 + 15 + 0.5 + 4
    x0 = -total_u * KB_P / 2
    for r, (fn, main, num) in enumerate(KB_ROWS):
        y = ((rows - 1) / 2 - r) * KB_P                    # row 0 at the back (+y)
        x = x0
        groups = ((fn, True, 0.5), (main, False, 0.5), (num, None, 0))
        for widths, kind, gap in groups:
            for wi, w in enumerate(widths):
                cx = x + w * KB_P / 2
                dark = (kind is True) or (kind is None and (wi == len(widths) - 1 or r == 0)) or \
                       (kind is False and (w >= 1.5) and w != 6)
                kb = key_bm(w * KB_P - 0.0030, KB_P - 0.0030, 0.0075 if r < 4 else 0.0070)
                tm(kb, lambda p, cx=cx, y=y: Vector((p.x + cx, p.y + y, p.z)))
                (darks if dark else caps).append(kb)
                x += w * KB_P
            x += gap * KB_P
    base_w, base_d = total_u * KB_P + 0.026, rows * KB_P + 0.030
    base = box((base_w, base_d, 0.012), (0, 0, 0.006), 0.0035, 3)
    # tilt about the front-bottom edge so the back is higher; then drop to the desk
    R = Matrix.Rotation(math.radians(KB_TILT), 4, "X")
    piv = Vector((0, -base_d / 2, 0))
    allb = [base] + caps + darks
    for bm in allb:
        tm(bm, lambda p: piv + (R @ (p - piv)).to_3d())
        tm(bm, lambda p: Vector((p.x + KB_X, p.y + KB_Y, p.z + 0.001)))
    kbd = join("PC_Keyboard", [base], col, m_beige, 40)
    k1 = join("PC_KeysCream", caps, col, m_beige, 40)
    k2 = join("PC_KeysDark", darks, col, m_keydark, 40)
    return kbd, k1, k2


def mouse(col, m_beige, m_dark):
    cx, cy = 0.255, -0.085
    b = bmesh.new()
    bmesh.ops.create_uvsphere(b, u_segments=40, v_segments=20, radius=1.0)
    for v in b.verts:
        z = max(v.co.z, -0.12)
        v.co = Vector((v.co.x * 0.0295, v.co.y * 0.0475, z * 0.0165))
        # narrower toward the cable end, rounder at the palm
        v.co.x *= 1.0 - 0.16 * max(0.0, v.co.y / 0.0475)
    tm(b, lambda p: Vector((p.x + cx, p.y + cy, p.z + 0.0021)))
    mo = join("PC_Mouse", [b], col, m_beige, 80)
    # button split + two buttons' front edge groove
    pts = []
    for i in range(9):
        y = -0.0455 + i * 0.0050
        zt = 0.0165 * math.sqrt(max(0.0, 1 - (y / 0.0475) ** 2)) * 1.0
        pts.append(box((0.0012, 0.0050, 0.0012), (cx, cy + y, 0.0021 + zt - 0.0002), 0.0002, 1))
    join("PC_MouseSplit", pts, col, m_dark, 80)
    # cable: from the back of the mouse, a lazy S to the case's right side
    P = [Vector(p) for p in ((cx, cy + 0.046, 0.004), (cx + 0.004, cy + 0.075, 0.0025), (cx - 0.012, 0.000, 0.0025),
                             (cx - 0.032, 0.070, 0.0025), (cx - 0.020, 0.150, 0.0025), (HW + 0.004, 0.185, 0.020),
                             (HW - 0.001, 0.200, 0.032))]
    cu = bpy.data.curves.new("PC_Cable_c", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.0017
    cu.bevel_resolution = 3
    sp = cu.splines.new("POLY")
    sp.points.add(len(P) - 1)
    # Catmull-Rom resample for smoothness
    from itertools import chain
    pp = [P[0]] + P + [P[-1]]
    smooth = []
    for i in range(1, len(pp) - 2):
        p0, p1, p2, p3 = pp[i - 1], pp[i], pp[i + 1], pp[i + 2]
        for k in range(12):
            t = k / 12
            smooth.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    smooth.append(P[-1])
    cu.splines.clear()
    sp = cu.splines.new("POLY")
    sp.points.add(len(smooth) - 1)
    for pt, v in zip(sp.points, smooth):
        pt.co = (v.x, v.y, v.z, 1.0)
    tmp = bpy.data.objects.new("PC_Cable_c", cu)
    col.objects.link(tmp)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp)
    cab = bpy.data.objects.new("PC_Cable", me)
    col.objects.link(cab)
    cab.data.materials.append(m_beige)
    C.shade_auto(cab, 60)
    return mo, cab


# ------------------------------------------------------------------ build
def build():
    col = C.new_scene(NAME)
    tex = C.comp_dir(NAME) / "export" / "tex_src"
    screen_p = make_images(tex)
    m_beige = MP.beige_abs("PC_Beige")
    m_keydark = MP.beige_abs("PC_KeyDark", base="#8b8576", aged="#6f6a5c", rough=0.46, dust=0.2)
    m_dark = MP.flat("PC_DarkPlastic", "#0f0f0e", 0.42)
    m_glass = MP.flat("PC_DisplayGlass", "#050606", 0.12, 0.0, 1.0)
    m_led = M.emissive("PC_LED_Amber", "#ff9a2a", 5.0)
    m_rubber = MP.flat("PC_Rubber", "#0a0a0a", 0.9)
    m_cable = MP.flat("PC_CableMat", "#cfc9ae", 0.55)
    mats = (m_beige, m_dark, m_glass, m_led, m_rubber)

    case = case_parts(col, mats)
    mon, scr, mon_extra, foot, pivot = monitor_parts(col, mats, screen_p)
    kbd, k1, k2 = keyboard(col, m_beige, m_keydark)
    mo, cab = mouse(col, m_beige, m_dark)
    cab.data.materials.clear()
    cab.data.materials.append(m_cable)

    # swivel the monitor group about the stand axis
    pivot_pt = Vector((0, STAND_Y, 0))
    R = Matrix.Rotation(math.radians(SWIVEL_DEG), 4, "Z")
    for ob in [mon, scr] + mon_extra:
        me = ob.data
        me.transform(Matrix.Translation(pivot_pt) @ R @ Matrix.Translation(-pivot_pt))
    return col, case, mon, k1, k2, kbd


def views():
    return {
        "ref":    [0.02, 0.10, 0.18, 38, 14, 1.45, 60],
        "refL":   [0.02, 0.10, 0.18, -38, 14, 1.45, 60],
        "front":  [0.0, 0.10, 0.18, 0, 6, 1.5, 60],
        "keys":   [0.0, -0.095, 0.012, 25, 38, 0.55, 85],
        "drive":  [0.12, 0.0, 0.07, 18, 8, 0.55, 85],
        "screen": [0.0, 0.05, 0.29, -16, 4, 0.95, 70],
    }


def main():
    col, case, mon, k1, k2, kbd = build()
    bpy.context.scene["preview_views"] = json.dumps(views())
    bpy.ops.wm.save_as_mainfile(filepath=str(C.comp_dir(NAME) / "export" / f"{NAME}_source.blend"), compress=True)
    if os.environ.get("SKIP_BAKE"):
        return
    tex = C.comp_dir(NAME) / "export" / "tex"
    objs = {o.name: o for o in col.all_objects}
    M.bake_to_images([objs["PC_Case"], objs["PC_Detail"]], str(tex), px=TEX_PX, prefix="pc_case")
    M.bake_to_images([objs["PC_Monitor"]], str(tex), px=TEX_PX, prefix="pc_monitor")
    M.bake_to_images([objs["PC_Keyboard"], objs["PC_KeysCream"], objs["PC_KeysDark"], objs["PC_Mouse"]],
                     str(tex), px=max(1024, TEX_PX // 2), prefix="pc_kb")
    M.bake_to_images([objs["PC_StandFoot"], objs["PC_StandPivot"], objs["PC_StandSwivel"], objs["PC_Cable"]],
                     str(tex), px=1024, prefix="pc_misc")
    C.export(NAME, col)


if __name__ == "__main__":
    main()
