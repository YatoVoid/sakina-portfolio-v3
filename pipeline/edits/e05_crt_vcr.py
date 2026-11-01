"""Edit #5 (round 3, user 2026-10-31): centre CRT + VCR realism (benchmark: Felix ref D).

CRT
- Bezel rebuilt as one mesh with rounded outer edges and a real screen opening: the picture now sits 1.7 cm
  BEHIND the bezel at the end of a sloped funnel (it was a flat plate stuck on the front of a box).
- Rear housing tapers toward the back like a picture tube (flat bottom so it sits on the VCR), seam step behind
  the bezel, vent slots on the top and both flanks, speaker grilles (round holes) on both sides of the bezel.
- The flat blue CRT_Glass plate, the stick-on lips/panel and screws are removed; the existing buttons, lamps,
  knobs, labels and brand text are kept. Power LED moves beside the buttons.
- Screen colours: from saturated neon blue to a dark blue-grey phosphor with warm-white text (not neon).
  The live website adds scanlines, curved-glass vignette and reflection on top (web/main.js), so the baked
  screen stays clean.
VCR
- Vacuum-fluorescent style display (cyan-green, softer), red REC button, "HQ" mark, fascia split line.
"""
import bpy, bmesh, math, os, importlib.util
from mathutils import Vector

_spec = importlib.util.spec_from_file_location("e04", os.path.join(os.path.dirname(os.path.abspath(__file__)), "e04_left_zone.py"))
e04 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(e04)
simple_mat, _wb = e04.simple_mat, e04._wb

F, BK = 1.600, 1.690                     # bezel front / back (y; the CRT faces -Y)
X0, X1, Z0, Z1 = -0.200, 0.160, 0.813, 1.173
OPEN = (-0.170, 0.130, 0.896, 1.128)     # opening in the bezel face
DEPTH = 0.016                            # funnel depth
INNER = (-0.161, 0.121, 0.904, 1.116)    # funnel end = edge of the picture
SCREEN_SHIFT, TEXT_SHIFT = 0.0250, 0.0280


def _link(coll, o, mat):
    coll.objects.link(o); o.data.materials.append(mat); return o


def _mesh(name, verts, faces, coll, mat, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return _link(coll, bpy.data.objects.new(name, me), mat)


def _bevel(o, w, seg=3, angle=35):
    m = o.modifiers.new("Bevel", 'BEVEL'); m.width = w; m.segments = seg; m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle); m.harden_normals = False
    return m


def _bezel(coll, plastic):
    ox0, ox1, oz0, oz1 = OPEN; ix0, ix1, iz0, iz1 = INNER; y2 = F + DEPTH
    v = [(X0, F, Z0), (X1, F, Z0), (X1, F, Z1), (X0, F, Z1),          # 0-3 front outer
         (ox0, F, oz0), (ox1, F, oz0), (ox1, F, oz1), (ox0, F, oz1),  # 4-7 front opening
         (ix0, y2, iz0), (ix1, y2, iz0), (ix1, y2, iz1), (ix0, y2, iz1),  # 8-11 funnel end
         (X0, BK, Z0), (X1, BK, Z0), (X1, BK, Z1), (X0, BK, Z1)]      # 12-15 back
    f = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),         # bezel face
         (4, 5, 9, 8), (5, 6, 10, 9), (6, 7, 11, 10), (7, 4, 8, 11),    # funnel
         (0, 12, 13, 1), (1, 13, 14, 2), (2, 14, 15, 3), (3, 15, 12, 0),  # outer sides
         (12, 15, 14, 13)]                                              # back
    o = _mesh("CRT_Bezel", v, f, coll, plastic)
    # funnel faces get a near-black matte material: the picture lit them up like a white frame (web test)
    o.data.materials.append(simple_mat("CRTFunnel", "0a0a0a", 0.7))
    for p in o.data.polygons[4:8]:
        p.material_index = 1
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    _bevel(o, 0.007, 3)
    return o


def _housing(coll, plastic, vent):
    yb0, yb1 = BK - 0.004, 1.900
    fx0, fx1, fz1 = X0 + 0.012, X1 - 0.012, Z1 - 0.012       # step in from the bezel = visible seam
    bx0, bx1, bz1 = -0.112, 0.072, 1.085
    zb = Z0 + 0.001                                           # flat bottom
    v = [(fx0, yb0, zb), (fx1, yb0, zb), (fx1, yb0, fz1), (fx0, yb0, fz1),
         (bx0, yb1, zb), (bx1, yb1, zb), (bx1, yb1, bz1), (bx0, yb1, bz1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    o = _mesh("CRT_Housing", v, f, coll, plastic)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    _bevel(o, 0.014, 4, 20)
    lerp = lambda a, b, t: a + (b - a) * t
    T = lambda y: (y - yb0) / (yb1 - yb0)
    ztop = lambda y: lerp(fz1, bz1, T(y)); xr = lambda y: lerp(fx1, bx1, T(y)); xl = lambda y: lerp(fx0, bx0, T(y))
    vv, ff = [], []

    def quad(p):
        i = len(vv); vv.extend(p); ff.append((i, i + 1, i + 2, i + 3))
    # top: 11 slots running front-to-back on the sloped top
    for k in range(11):
        x = -0.02 + (k - 5) * 0.012
        ya, yb = 1.745, 1.855
        quad([(x - 0.0032, ya, ztop(ya) + 0.0008), (x + 0.0032, ya, ztop(ya) + 0.0008),
              (x + 0.0032, yb, ztop(yb) + 0.0008), (x - 0.0032, yb, ztop(yb) + 0.0008)])
    # flanks: 13 vertical slots each side, near the back (ref A)
    for k in range(13):
        ya = 1.752 + k * 0.0085; yb = ya + 0.0042
        for side, xf in ((1, xr), (-1, xl)):
            off = side * 0.0008
            quad([(xf(ya) + off, ya, 0.875), (xf(yb) + off, yb, 0.875), (xf(yb) + off, yb, 1.030), (xf(ya) + off, ya, 1.030)])
    _mesh("CRT_Vents", vv, ff, coll, vent)
    return o


def _speakers(coll, vent):
    vv, ff = [], []
    for side, x in ((1, X1 + 0.0007), (-1, X0 - 0.0007)):
        for a in range(5):
            for b in range(12):
                cy = F + 0.018 + a * 0.0125; cz = 0.872 + b * 0.0205
                i = len(vv)
                for s in range(8):
                    ang = 2 * math.pi * s / 8
                    vv.append((x, cy + 0.0026 * math.cos(ang), cz + 0.0026 * math.sin(ang)))
                ff.append(tuple(range(i, i + 8)) if side > 0 else tuple(reversed(range(i, i + 8))))
    _mesh("CRT_Speaker", vv, ff, coll, vent)


def _screen_colours():
    D = bpy.data
    m = D.materials["CRT_Screen"]
    ramp = next(n for n in m.node_tree.nodes if n.type == 'VALTORGB')
    ramp.color_ramp.elements[0].color = (0.010, 0.016, 0.026, 1)   # dark blue-grey phosphor, not neon blue
    ramp.color_ramp.elements[1].color = (0.040, 0.058, 0.085, 1)
    st = D.materials["ScreenText"].node_tree.nodes["Emission"]
    st.inputs["Color"].default_value = (0.93, 0.90, 0.80, 1); st.inputs["Strength"].default_value = 2.2
    on = D.materials["BarOn"].node_tree.nodes["Emission"]
    on.inputs["Color"].default_value = (0.95, 0.88, 0.70, 1); on.inputs["Strength"].default_value = 2.4
    off = D.materials["BarOff"].node_tree.nodes["Emission"]
    off.inputs["Color"].default_value = (0.035, 0.045, 0.06, 1); off.inputs["Strength"].default_value = 1.0
    led = D.materials["LEDGreen"].node_tree.nodes["Emission"]
    led.inputs["Strength"].default_value = 8.0                       # was 20: glowing dots, not lasers


def _crt_plastic():
    """Charcoal TV plastic: darker than the shared BlackPlastic (which read mid-grey with heavy speckle on the bezel),
    fine stipple texture, satin gloss."""
    m = bpy.data.materials.get("CRTPlastic")
    if m:
        return m
    m = simple_mat("CRTPlastic", "121211", 0.58)   # darker + rougher: baked sheen made it read grey
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1500.0
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.04; bp.inputs["Distance"].default_value = 0.0003
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
    return m


def _crt():
    D = bpy.data
    coll = D.collections["Monitor"]
    for o in list(coll.all_objects):
        if o.name in ("CRT_Front", "CRT_Back", "CRT_Glass", "CRT_Panel", "CRT_PanelRim") or \
                o.name.startswith(("CRT_Lip_", "CRT_Screw_", "CRT_TopVent_")):
            D.objects.remove(o, do_unlink=True)
    plastic = _crt_plastic()
    vent = simple_mat("VentBlack", "060606", 0.9)
    _bezel(coll, plastic)
    _housing(coll, plastic, vent)
    _speakers(coll, vent)
    # controls/labels were mounted on the old 3 mm panel plate: seat them on the new bezel face
    for o in coll.all_objects:
        if o.name.startswith("CRT_") and o.parent is None and o.name not in (
                "CRT_Bezel", "CRT_Housing", "CRT_Vents", "CRT_Speaker", "CRT_Screen"):
            o.location.y += 0.003
    # picture + its content move back into the funnel
    D.objects["CRT_Screen"].location.y += SCREEN_SHIFT
    for o in coll.all_objects:
        if o.name.startswith("Scr_") and o.parent is None:
            o.location.y += TEXT_SHIFT
    # power LED + label beside the buttons (the old spot is now the screen opening)
    for n, (x, z) in (("CRT_LED", (-0.188, 0.873)), ("CRT_PwrLabel", (-0.190, 0.862))):
        o = D.objects.get(n)
        if o:
            b0, b1 = _wb(o)
            o.location.x += x - (b0.x + b1.x) / 2; o.location.z += z - (b0.z + b1.z) / 2
    _screen_colours()


def _vcr():
    D = bpy.data
    coll = D.collections["Monitor"]
    vfd = D.materials["LCDText"].node_tree.nodes["Emission"]
    vfd.inputs["Color"].default_value = (0.30, 0.95, 0.82, 1); vfd.inputs["Strength"].default_value = 3.5
    ghost = D.materials["LCDGhost"].node_tree.nodes["Emission"]
    ghost.inputs["Color"].default_value = (0.01, 0.07, 0.06, 1); ghost.inputs["Strength"].default_value = 0.6
    red = simple_mat("VCRRec", "a3241b", 0.35)
    btn = D.objects["VCR_Btn_5"]; btn.data = btn.data.copy(); btn.data.materials.clear(); btn.data.materials.append(red)
    b0, b1 = _wb(D.objects["VCR"])
    ink = D.materials.get("PanelText")
    cu = bpy.data.curves.new("VCR_HQ", 'FONT'); cu.body = "HQ"; cu.size = 0.007; cu.align_x = 'RIGHT'
    o = bpy.data.objects.new("VCR_HQ", cu); coll.objects.link(o); o.data.materials.append(ink)
    o.location = (b1.x - 0.016, b0.y - 0.0004, b1.z - 0.012); o.rotation_euler = (math.pi / 2, 0, 0)
    for n, txt, x in (("VCR_Mode", "PLAY", 0.090), ("VCR_Ch", "CH 03", 0.124)):
        cu = bpy.data.curves.new(n, 'FONT'); cu.body = txt; cu.size = 0.0042
        o = bpy.data.objects.new(n, cu); coll.objects.link(o); o.data.materials.append(D.materials["LCDText"])
        o.location = (x, 1.5668, 0.7855); o.rotation_euler = (math.pi / 2, 0, 0)
    # fascia split line across the front, just above the buttons
    me = bpy.data.meshes.new("VCR_Split")
    y = b0.y - 0.0003
    me.from_pydata([(b0.x + 0.006, y, 0.8045), (b1.x - 0.006, y, 0.8045), (b1.x - 0.006, y, 0.8055), (b0.x + 0.006, y, 0.8055)], [], [(0, 1, 2, 3)])
    o = bpy.data.objects.new("VCR_Split", me); coll.objects.link(o); o.data.materials.append(D.materials["VCRRecess"])


def apply():
    _crt()
    _vcr()
    bpy.context.view_layer.update()
    print("e05 CRT/VCR done")
