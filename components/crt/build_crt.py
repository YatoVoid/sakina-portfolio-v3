"""Center CRT TV — detailed standalone component.

Reference: the approved room's centre CRT (assets/sakina-v17.blend, collection "Monitor", objects CRT_*/Scr_*),
kept to its exact footprint so it can replace it 1:1. No photo reference was supplied for this pass.

Certain (measured from the room): bezel 0.36 x 0.36 m, front plane y = 1.600, bottom z = 0.813 (sits on the VCR),
  housing back y = 1.900; 4:3 picture 0.28 x 0.21 m centred 0.197 m above the bottom; control row under the
  picture (power LED, 6 push buttons, 3 rotary knobs); black plastic; top vents.
Inferred (typical 1990s 14" CRT construction): rounded bezel with a sloped funnel to the glass, curved faceplate
  (9 mm bulge), tapered rear "bell" with a seam step, side vents, speaker perforations on the bezel flanks,
  rear neck block with rating label, rubber feet, textured (EDM) ABS with dust and grime.

Local frame: origin = bottom centre of the bezel front plane, front faces -Y, metres.
Room placement (v17): translate (-0.02, 1.600, 0.813), no rotation.
Run: python3 components/crt/build_crt.py -> export/crt_source.blend, crt.blend, crt.glb, crt.stats.json
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
import common as C          # noqa: E402
import materials as M       # noqa: E402
import materials_crt as MC  # noqa: E402

NAME = "crt"
TEX_PX = int(os.environ.get("TEX_PX", 2048))
SCREEN_ON = os.environ.get("SCREEN_ON", "1") == "1"

W, H = 0.360, 0.360                   # bezel
SC_Z = 0.197                          # picture centre height
OPEN = (0.300, 0.226, 0.014)          # opening in the bezel face (w, h, corner r)
FUN = (0.284, 0.212, 0.010)           # funnel end = picture edge
FUN_Y, BEZ_D = 0.016, 0.085
BACK_Y = 0.300


# ---------------------------------------------------------------- loops
def rrect(cx, cz, w, h, r, k=6):
    """Rounded rectangle in the XZ plane, CCW seen from the front (-Y), 4*(k+1) points."""
    pts = []
    corners = ((cx + w / 2 - r, cz - h / 2 + r, -90), (cx + w / 2 - r, cz + h / 2 - r, 0),
               (cx - w / 2 + r, cz + h / 2 - r, 90), (cx - w / 2 + r, cz - h / 2 + r, 180))
    for (x, z, a0) in corners:
        for i in range(k + 1):
            a = math.radians(a0 + 90 * i / k)
            pts.append((x + r * math.cos(a), z + r * math.sin(a)))
    return pts


def loop(bm, pts, y):
    return [bm.verts.new((x, y, z)) for x, z in pts]


def bridge(bm, a, b, flip=False):
    n = len(a)
    for i in range(n):
        q = (a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])
        try:
            bm.faces.new(reversed(q) if flip else q)
        except ValueError:
            pass


# ---------------------------------------------------------------- parts
def bezel(col, mat):
    bm = bmesh.new()
    o_f = loop(bm, rrect(0, H / 2 + 0.002, W, H - 0.004, 0.016), 0.0)
    op = loop(bm, rrect(0, SC_Z, *OPEN), 0.0)
    fu = loop(bm, rrect(0, SC_Z, *FUN), FUN_Y)
    o_b = loop(bm, rrect(0, H / 2 + 0.002, W - 0.004, H - 0.008, 0.015), BEZ_D)
    bridge(bm, o_f, op)          # front face ring
    bridge(bm, op, fu)           # funnel
    bridge(bm, o_b, o_f)         # outer sides
    bm.faces.new(list(reversed(o_b)))     # back cap (hidden by the housing)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    front_edges = [e for e in bm.edges if all(v in o_f for v in e.verts)]
    bmesh.ops.bevel(bm, geom=front_edges, offset=0.0045, segments=4, affect="EDGES", clamp_overlap=True)
    op_edges = [e for e in bm.edges if all(v.is_valid and v in op for v in e.verts)]
    bmesh.ops.bevel(bm, geom=op_edges, offset=0.0016, segments=2, affect="EDGES", clamp_overlap=True)
    ob = C.mesh_obj("CRT_Bezel", bm, col)
    ob.data.materials.append(mat)
    C.shade_auto(ob, 40)
    return ob


def housing(col, mat):
    bm = bmesh.new()
    zb = 0.004
    specs = [(0.0805, 0.338, 0.338, 0.020), (0.120, 0.336, 0.336, 0.022),
             (0.245, 0.236, 0.272, 0.040), (BACK_Y, 0.206, 0.250, 0.042)]
    loops = [loop(bm, rrect(0, zb + h / 2, w, h, r), y) for (y, w, h, r) in specs]
    for a, b in zip(loops, loops[1:]):
        bridge(bm, b, a)
    bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    back = [e for e in bm.edges if all(v in loops[-1] for v in e.verts)]
    bmesh.ops.bevel(bm, geom=back, offset=0.010, segments=4, affect="EDGES", clamp_overlap=True)
    # rear neck block (holds the tube neck / sockets)
    nb = bmesh.new()
    bmesh.ops.create_cube(nb, size=1.0)
    for v in nb.verts:
        v.co = Vector((v.co.x * 0.130, BACK_Y + 0.012 + v.co.y * 0.040, zb + 0.105 + v.co.z * 0.150))
    bmesh.ops.bevel(nb, geom=list(nb.edges), offset=0.008, segments=3, affect="EDGES", clamp_overlap=True)
    tmp = bpy.data.meshes.new("_t"); nb.to_mesh(tmp); nb.free(); bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
    ob = C.mesh_obj("CRT_Housing", bm, col)
    ob.data.materials.append(mat)
    C.shade_auto(ob, 32)
    return ob


def faceplate(col, mat):
    """Curved glass: spherical-ish bulge of 9 mm toward the viewer, UV 0..1 over the picture."""
    hw, hh = 0.145, 0.109
    nx, nz = 32, 24
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    grid = []
    for j in range(nz + 1):
        row = []
        for i in range(nx + 1):
            x = -hw + 2 * hw * i / nx
            z = -hh + 2 * hh * j / nz
            y = FUN_Y + 0.002 - 0.009 * (1 - 0.5 * ((x / hw) ** 2 + (z / hh) ** 2))
            row.append(bm.verts.new((x, y, SC_Z + z)))
        grid.append(row)
    for j in range(nz):
        for i in range(nx):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            for l in f.loops:
                p = l.vert.co
                l[uv].uv = ((p.x + 0.140) / 0.280, (p.z - SC_Z + 0.105) / 0.210)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.y > 0:
            f.normal_flip()
    ob = C.mesh_obj("CRT_Screen", bm, col, smooth=True)
    ob.data.materials.append(mat)
    return ob


def rbox(size, loc, bevel, seg=3):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0] + loc[0], v.co.y * size[1] + loc[1], v.co.z * size[2] + loc[2]))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=seg, affect="EDGES", clamp_overlap=True)
    return bm


def join(name, bms, col, mat, smooth_angle=40):
    out = bmesh.new()
    tmp = bpy.data.meshes.new("_t")
    for bm in bms:
        bm.to_mesh(tmp); bm.free(); out.from_mesh(tmp)
    bpy.data.meshes.remove(tmp)
    ob = C.mesh_obj(name, out, col)
    ob.data.materials.append(mat)
    C.shade_auto(ob, smooth_angle)
    return ob


def knob(x, z):
    """Knurled rotary knob: 24 ridges, chamfered face."""
    bm = bmesh.new()
    n, r0, r1, d = 48, 0.0100, 0.0093, 0.011
    rings = []
    for yy, scale in ((0.0, 1.0), (-d + 0.002, 1.0), (-d, 0.82)):
        ring = []
        for i in range(n):
            a = 2 * math.pi * i / n
            r = (r0 if i % 2 == 0 else r1) * scale if scale == 1.0 else r0 * scale
            ring.append(bm.verts.new((x + r * math.cos(a), yy, z + r * math.sin(a))))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        bridge(bm, a, b)
    bm.faces.new(rings[-1])
    bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def text_obj(name, body, size, loc, col, mat, extrude=0.0003, align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body; cu.size = size; cu.extrude = extrude; cu.align_x = align; cu.align_y = "CENTER"
    tmp = bpy.data.objects.new(name + "_c", cu)
    col.objects.link(tmp)
    tmp.rotation_euler = (math.radians(90), 0, 0)
    tmp.location = loc
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    me.transform(tmp.matrix_world)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    bpy.data.objects.remove(tmp)
    ob.data.materials.append(mat)
    return ob


# ---------------------------------------------------------------- images
def make_images(d):
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    d.mkdir(parents=True, exist_ok=True)
    def font(px, mono=True):
        for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if mono else
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                  "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"):
            if os.path.exists(p):
                return ImageFont.truetype(p, px)
        return ImageFont.load_default(size=px)
    # phosphor screen: dark blue-grey field, soft vignette, warm-white prompt (scanlines are added by the site)
    w, h = 1024, 768
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        for x in range(w):
            u, v = (x / w - 0.5) * 2, (y / h - 0.5) * 2
            k = max(0.0, 1 - 0.55 * (u * u + v * v)) ** 1.6
            px[x, y] = (int(10 + 20 * k), int(17 + 33 * k), int(28 + 52 * k))
    dr = ImageDraw.Draw(im)
    f = font(44)
    lines = ["PORTFOLIO SYSTEM  V3.0", "", "READY.", "", "C:\\>_"]
    for i, t in enumerate(lines):
        dr.text((96, 120 + i * 62), t, font=f, fill=(226, 214, 186))
    glow = im.filter(ImageFilter.GaussianBlur(6))
    im = Image.blend(im, glow, 0.35)
    screen_p = d / "crt_screen.png"
    im.save(screen_p)
    # rating label on the rear neck
    lab = Image.new("RGB", (512, 320), (214, 208, 192))
    dl = ImageDraw.Draw(lab)
    dl.rectangle((8, 8, 503, 311), outline=(40, 38, 34), width=3)
    fs, fb = font(26, False), font(34, False)
    dl.text((30, 26), "COLOR TELEVISION", font=fb, fill=(30, 28, 25))
    for i, t in enumerate(["MODEL  SV-1400", "120V ~ 60Hz  70W", "SERIAL  0219974",
                           "CAUTION: RISK OF ELECTRIC SHOCK", "DO NOT OPEN"]):
        dl.text((30, 90 + i * 40), t, font=fs, fill=(45, 42, 38))
    lab = lab.filter(ImageFilter.GaussianBlur(0.6))
    label_p = d / "crt_label.png"
    lab.save(label_p)
    return screen_p, label_p


# ---------------------------------------------------------------- build
def build():
    col = C.new_scene(NAME)
    tex = C.comp_dir(NAME) / "export" / "tex_src"
    screen_p, label_p = make_images(tex)
    m_bezel = MC.abs_plastic("CRT_Plastic_Bezel", rough=0.46, dust=0.22)
    m_house = MC.abs_plastic("CRT_Plastic_Housing", rough=0.58, dust=0.40)
    m_screen = MC.screen("CRT_Faceplate", screen_p, strength=1.4 if SCREEN_ON else 0.0)
    flat = lambda n, c, r, met=0.0: _flat(n, c, r, met)
    m_plate = flat("CRT_ControlPlate", "#0c0c0c", 0.38)
    m_btn = flat("CRT_Buttons", "#1d1d1c", 0.42)
    m_knob = flat("CRT_Knobs", "#121212", 0.34)
    m_ink = flat("CRT_PanelInk", "#c9c3b6", 0.6)
    m_badge = flat("CRT_Badge", "#b9b7b2", 0.28, 1.0)
    m_rubber = flat("CRT_Rubber", "#090909", 0.92)
    m_led = M.emissive("CRT_LED_Green", "#3dff6b", 8.0)

    bez = bezel(col, m_bezel)
    hou = housing(col, m_house)
    scr = faceplate(col, m_screen)

    # control strip under the picture
    zc = 0.048
    join("CRT_ControlPlate", [rbox((0.334, 0.0024, 0.054), (0, -0.0009, zc), 0.0011, 2)], col, m_plate)
    btns = [rbox((0.030, 0.006, 0.013), (-0.133, -0.003, zc), 0.0018)]          # power
    for i in range(6):
        btns.append(rbox((0.016, 0.0055, 0.0095), (-0.086 + i * 0.0205, -0.0028, zc), 0.0014))
    join("CRT_Buttons", btns, col, m_btn)
    join("CRT_Knobs", [knob(x, zc) for x in (0.064, 0.096, 0.128)], col, m_knob, 25)
    ink = []
    for i in range(6):                                           # tick marks under the buttons
        ink.append(rbox((0.008, 0.0003, 0.0012), (-0.086 + i * 0.0205, -0.0025, zc - 0.0115), 0.0001, 1))
    for x in (0.064, 0.096, 0.128):                              # knob index lines
        ink.append(rbox((0.0012, 0.0004, 0.0055), (x, -0.0112, zc + 0.0045), 0.0001, 1))
        for a in range(-135, 136, 45):                           # scale dots around each knob
            r = 0.0138
            ink.append(rbox((0.0009, 0.0003, 0.0009),
                            (x + r * math.sin(math.radians(a)), -0.0025, zc + r * math.cos(math.radians(a))),
                            0.0001, 1))
    join("CRT_PanelInk", ink, col, m_ink, 60)
    led = bmesh.new()
    bmesh.ops.create_uvsphere(led, u_segments=16, v_segments=8, radius=0.0024)
    bmesh.ops.scale(led, vec=(1, 0.5, 1), verts=led.verts)
    bmesh.ops.translate(led, vec=(-0.108, -0.0024, zc), verts=led.verts)
    led_ob = C.mesh_obj("CRT_LED", led, col, smooth=True); led_ob.data.materials.append(m_led)
    text_obj("CRT_Badge", "SAKINA", 0.0075, (0, -0.0004, 0.0795), col, m_badge, 0.0004)
    text_obj("CRT_Model", "SV-1400  STEREO", 0.0042, (0.118, -0.0004, 0.0795), col, m_ink, 0.0002)
    # rubber feet under the housing (bezel bottom sits flush on the VCR)
    feet = [rbox((0.026, 0.026, 0.004), (sx * 0.085, y, 0.002), 0.0012, 2)
            for sx in (-1, 1) for y in (0.11, 0.24)]
    join("CRT_Feet", feet, col, m_rubber)
    # rating label on the rear neck
    lb = bmesh.new()
    uvl = lb.loops.layers.uv.new("UVMap")
    vs = [lb.verts.new(p) for p in ((0.04, BACK_Y + 0.0325, 0.08), (-0.04, BACK_Y + 0.0325, 0.08),
                                     (-0.04, BACK_Y + 0.0325, 0.13), (0.04, BACK_Y + 0.0325, 0.13))]
    f = lb.faces.new(vs)
    for l, uvv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        l[uvl].uv = uvv
    lob = C.mesh_obj("CRT_Label", lb, col)
    lob.data.materials.append(M.image_mat("CRT_Label", label_p, rough=0.7))
    return col, bez, hou


def _flat(name, color, rough, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = C.hex_lin(color)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    return m


def main():
    col, bez, hou = build()
    bpy.context.scene["preview_views"] = json.dumps({
        "controls": [0.02, -0.004, 0.06, -12, 6, 0.30, 85],
        "screen":   [0.0, 0.0, 0.20, -28, 6, 0.52, 70],
        "vents":    [0.0, 0.20, 0.27, 145, 38, 0.62, 60],
    })
    bpy.ops.wm.save_as_mainfile(filepath=str(C.comp_dir(NAME) / "export" / f"{NAME}_source.blend"),
                                compress=True)
    if os.environ.get("SKIP_BAKE") == "1":                 # position/look preview only; bake later
        return
    tex = C.comp_dir(NAME) / "export" / "tex"
    M.bake_to_images([bez], str(tex), px=TEX_PX, prefix="crt_bezel")
    M.bake_to_images([hou], str(tex), px=TEX_PX, prefix="crt_housing")
    C.export(NAME, col)


if __name__ == "__main__":
    main()
