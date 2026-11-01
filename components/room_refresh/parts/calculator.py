"""Desk calculator, rebuilt in place of `Calculator` (same position, orientation, 9 x 12.4 cm footprint).

Local frame of the old object: display at +Y (away from the viewer), keys toward -Y, top +Z.
Wedge body (10 mm at the front, 18 mm under the display), brushed faceplate, recessed LCD with real
seven-segment digits, solar strip, 5 x 5 bevelled keys with printed legends following the slope.
"""
import bpy, math
from mathutils import Vector, Matrix
import geo as G
import mats as M

W, LEN = 0.088, 0.122
ZF, ZB = 0.010, 0.016            # top height at the front edge / at the start of the display section
SLOPE = math.atan((ZB - ZF) / 0.090)

SEG = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
       "8": "abcdefg", "9": "abcfgd"}


def _face_z(y):
    """Height of the key face at local y (front edge y = -LEN/2)."""
    return ZF + (y + LEN / 2) * math.tan(SLOPE)


def build(coll):
    D = bpy.data
    old = D.objects["Calculator"]
    lo = Vector([min(v.co[i] for v in old.data.vertices) for i in range(3)])
    hi = Vector([max(v.co[i] for v in old.data.vertices) for i in range(3)])
    c = (lo + hi) / 2
    base_world = old.matrix_world @ Matrix.Translation((c.x, c.y, lo.z))
    G.remove(["Calculator"])

    body_m = M.plastic("#2a2a2d", "#323236", "R_CalcBody", (0.38, 0.55), 0.06)
    plate_m = M.brass_aged() if False else M.flat("#5d5e62", "R_CalcFaceplate", 0.35, 0.8)
    key_light = M.plastic("#cfccc4", "#d8d5cd", "R_CalcKeyLight", (0.45, 0.6), 0.03)
    key_dark = M.plastic("#45464b", "#4d4e53", "R_CalcKeyDark", (0.45, 0.6), 0.03)
    key_red = M.flat("#c4462a", "R_CalcKeyRed", 0.45)
    ink_dark, ink_light = M.flat("#1f1f22", "R_CalcInkDark", 0.6), M.flat("#e9e6de", "R_CalcInkLight", 0.6)
    seg_m = M.flat("#1c211b", "R_CalcSegment", 0.5)
    made = []

    # body: side profile (y, z) extruded across x, bevelled
    prof = [(-LEN / 2, 0.0), (LEN / 2, 0.0), (LEN / 2, 0.0175), (LEN / 2 - 0.030, 0.019), (LEN / 2 - 0.032, ZB), (-LEN / 2, ZF)]
    rot = Matrix.Rotation(math.radians(90), 4, 'Y') @ Matrix.Rotation(math.radians(90), 4, 'Z')
    body = G.extrude_outline("Calculator", [(y, z) for y, z in prof], -W / 2, W / 2, coll, body_m, 0.0022, 3,
                             matrix=Matrix.Rotation(math.radians(90), 4, 'Z') @ Matrix.Rotation(math.radians(90), 4, 'X'))
    # outline (u, v) -> rotate so u = y, v = z, extrusion = x
    made.append(body)
    # faceplate on the key slope
    yk0, yk1 = -LEN / 2 + 0.006, LEN / 2 - 0.036
    plate = G.box("Calc_Faceplate", (-W / 2 + 0.004, yk0, -0.0004), (W / 2 - 0.004, yk1, 0.0004), coll, plate_m, 0.0004, 1)
    plate.matrix_world = Matrix.Translation((0, 0, _face_z((yk0 + yk1) / 2))) @ Matrix.Translation((0, (yk0 + yk1) / 2, 0)) @ \
        Matrix.Rotation(SLOPE, 4, 'X') @ Matrix.Translation((0, -(yk0 + yk1) / 2, 0))
    made.append(plate)
    # display: black bezel recess, LCD glass, digits "31415.92"
    dz = 0.019
    made.append(G.box("Calc_Bezel", (-0.040, LEN / 2 - 0.027, dz - 0.0008), (0.040, LEN / 2 - 0.006, dz + 0.0003), coll,
                      M.flat("#0d0d0e", "R_CalcBezel", 0.3), 0.001, 2))
    made.append(G.box("Calc_LCD", (-0.035, LEN / 2 - 0.024, dz + 0.0003), (0.035, LEN / 2 - 0.0095, dz + 0.0006), coll, M.lcd()))
    digits = "31415.92"
    cw, ch, t = 0.0062, 0.0098, 0.0007
    x = 0.031
    zt = dz + 0.00065
    yc = LEN / 2 - 0.0167
    for chr_ in reversed(digits):
        if chr_ == ".":
            made.append(G.box("Calc_Seg_dp", (x + 0.0006, yc - ch / 2, zt), (x + 0.0013, yc - ch / 2 + 0.0008, zt + 0.0001), coll, seg_m))
            continue
        x0 = x - cw
        segs = {"a": ((x0 + t, yc + ch / 2 - t), (x - t, yc + ch / 2)), "g": ((x0 + t, yc - t / 2), (x - t, yc + t / 2)),
                "d": ((x0 + t, yc - ch / 2), (x - t, yc - ch / 2 + t)), "f": ((x0, yc + t / 2), (x0 + t, yc + ch / 2 - t)),
                "b": ((x - t, yc + t / 2), (x, yc + ch / 2 - t)), "e": ((x0, yc - ch / 2 + t), (x0 + t, yc - t / 2)),
                "c": ((x - t, yc - ch / 2 + t), (x, yc - t / 2))}
        for s_ in SEG[chr_]:
            (a, b2), (c2, d2) = segs[s_]
            sk = 0.0006   # italic slant like real LCD digits
            made.append(G.box(f"Calc_Seg_{len(made)}", (a, b2, zt), (c2, d2, zt + 0.0001), coll, seg_m))
        x -= cw + 0.0021
    # solar strip and model text above the display
    made.append(G.box("Calc_Solar", (0.004, LEN / 2 - 0.0058, 0.0186), (0.036, LEN / 2 - 0.0012, 0.0192), coll, M.solar()))
    lbl = G.text("Calc_Model", "SOLAR  MC-12", 0.0028, coll, ink_light, align='LEFT')
    lbl.location = (-0.039, LEN / 2 - 0.0036, 0.0191); made.append(lbl)

    # keys: 5 x 5 on the slope
    rows = [["MC", "MR", "M-", "M+", "÷"], ["%", "7", "8", "9", "×"], ["√", "4", "5", "6", "−"], ["C", "1", "2", "3", "+"], ["AC", "0", "00", ".", "="]]
    kw, kd, px, py = 0.0128, 0.0094, 0.0162, 0.0136
    for r, row in enumerate(rows):
        y = yk1 - 0.009 - r * py
        z = _face_z(y) + 0.0004
        for cidx, lab in enumerate(row):
            xk = (cidx - 2) * px
            dark = r == 0 or cidx in (0, 4)
            mat = key_red if lab in ("AC", "C") else key_dark if dark else key_light
            k = G.extrude_outline(f"Calc_Key_{r}{cidx}", G.rounded_rect(kw, kd, 0.0022, 4), 0.0, 0.0032, coll, mat, 0.0011, 3)
            k.matrix_world = Matrix.Translation((xk, y, z)) @ Matrix.Rotation(SLOPE, 4, 'X')
            made.append(k)
            t_ = G.text(f"Calc_KeyLbl_{r}{cidx}", lab, 0.0042 if len(lab) == 1 else 0.0032, coll,
                        ink_dark if mat is key_light else ink_light)
            t_.matrix_world = Matrix.Translation((xk, y, z)) @ Matrix.Rotation(SLOPE, 4, 'X') @ Matrix.Translation((0, 0, 0.00325))
            made.append(t_)

    for o in made:
        if o.type == 'MESH' and o.modifiers:
            G.apply_modifiers(o)
    for o in made:
        if o is not body:
            mw = o.matrix_world.copy(); o.parent = body; o.matrix_world = mw
    body.matrix_world = base_world
    return made
