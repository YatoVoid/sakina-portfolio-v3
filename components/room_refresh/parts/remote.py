"""VCR remote control, rebuilt in place of `Remote` (same position, orientation and footprint).

Local frame of the old remote: length along local X (IR / power end at -X), width Y, top +Z.
Body: soft rounded slab (19 x 5.2 cm), thicker toward the battery end, mould seam, IR window.
Buttons: raised rubber keys with real bevels: power, 12-key number pad, transport cluster, channel rocker,
with small printed legends.
"""
import bpy, math
from mathutils import Vector, Matrix
import geo as G
import mats as M

L, W, H = 0.190, 0.052, 0.0175


def _top_z(x):
    """Top surface height along the length: thicker at the back (+X) where the batteries sit."""
    return H * (0.86 + 0.14 * (x / L + 0.5))


def build(coll):
    D = bpy.data
    old = D.objects["Remote"]
    lo = Vector([min(v.co[i] for v in old.data.vertices) for i in range(3)])
    hi = Vector([max(v.co[i] for v in old.data.vertices) for i in range(3)])
    centre_local = (lo + hi) / 2
    base_world = old.matrix_world @ Matrix.Translation((centre_local.x, centre_local.y, lo.z))
    G.remove(["Remote"])

    body_m = M.plastic("#141414", "#1d1c1c", "R_RemoteABS", (0.32, 0.5), 0.07)
    key_m = M.plastic("#3b3b3e", "#45454a", "R_RubberKeyGrey", (0.55, 0.7), 0.04)
    dark_m = M.plastic("#232325", "#2a2a2d", "R_RubberKeyDark", (0.5, 0.65), 0.04)
    red_m = M.flat("#a51d16", "R_KeyRed", 0.45)
    ink = M.flat("#d8d4ca", "R_PrintInk", 0.6)
    ir = M.flat("#2a0605", "R_IRWindow", 0.08)
    made = []

    body = G.extrude_outline("Remote", G.rounded_rect(L, W, 0.014, 8), 0.0, H, coll, body_m, 0.0045, 4)
    for v in body.data.vertices:          # taper
        if v.co.z > H * 0.5:
            v.co.z = _top_z(v.co.x) - (H - v.co.z)
    made.append(body)
    seam = G.extrude_outline("Remote_Seam", G.rounded_rect(L + 0.0006, W + 0.0006, 0.0143, 8), 0.0072, 0.0080, coll,
                             M.flat("#050505", "R_SeamBlack", 0.9))
    made.append(seam)
    made.append(G.box("Remote_IR", (-L / 2 - 0.0012, -0.011, 0.0045), (-L / 2 + 0.004, 0.011, 0.0115), coll, ir, 0.0015, 2))

    def key(name, x, y, w, d, mat, h=0.0016, r=None, label=None, lsize=0.0026, ldy=-0.0062):
        z = _top_z(x) - 0.0005
        o = G.extrude_outline(name, G.rounded_rect(w, d, r or min(w, d) * 0.45, 5), z, z + h, coll, mat, min(w, d) * 0.22, 3,
                              matrix=Matrix.Translation((x, y, 0)))
        made.append(o)
        if label:
            t = G.text(name + "_Lbl", label, lsize, coll, ink)
            t.location = (x - ldy, y, _top_z(x) + 0.00005); t.rotation_euler = (0, 0, math.radians(90))   # text 'up' = IR end (-X)
            made.append(t)
        return o

    # power + eject at the IR end
    key("Remote_Power", -0.074, -0.013, 0.010, 0.010, red_m, label="POWER", ldy=-0.0085)
    key("Remote_Eject", -0.074, 0.013, 0.010, 0.010, dark_m, label="EJECT", ldy=-0.0085)
    # number pad 3 x 4
    labels = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "TV", "0", "+10"]
    for r in range(4):
        for c in range(3):
            n = r * 3 + c
            key(f"Remote_Num_{n:02d}", -0.050 + r * 0.0135, (c - 1) * 0.0145, 0.0105, 0.0085, key_m)
            t = G.text(f"Remote_Num_{n:02d}_Lbl", labels[n], 0.0034 if len(labels[n]) == 1 else 0.0024, coll, ink)
            t.location = (-0.050 + r * 0.0135, (c - 1) * 0.0145, _top_z(-0.05 + r * 0.0135) + 0.0012); t.rotation_euler = (0, 0, math.radians(90))
            made.append(t)
    # transport cluster: REW  PLAY  FF  /  REC  STOP  PAUSE
    key("Remote_Play", 0.022, 0.0, 0.012, 0.016, key_m, label="PLAY", ldy=-0.0105)
    key("Remote_Rew", 0.022, -0.0175, 0.011, 0.012, dark_m, label="REW", ldy=-0.0085)
    key("Remote_FF", 0.022, 0.0175, 0.011, 0.012, dark_m, label="FF", ldy=-0.0085)
    key("Remote_Rec", 0.041, -0.0175, 0.010, 0.012, red_m, label="REC", ldy=-0.0085)
    key("Remote_Stop", 0.041, 0.0, 0.010, 0.016, dark_m, label="STOP", ldy=-0.0105)
    key("Remote_Pause", 0.041, 0.0175, 0.010, 0.012, dark_m, label="PAUSE", ldy=-0.0085)
    # channel rocker and two small keys near the battery end
    key("Remote_Channel", 0.067, -0.012, 0.022, 0.010, key_m, h=0.0022, label="CH", ldy=-0.0078)
    key("Remote_Menu", 0.064, 0.014, 0.009, 0.009, dark_m, label="MENU", ldy=-0.008)
    key("Remote_Timer", 0.077, 0.014, 0.009, 0.009, dark_m, label="TIMER", ldy=-0.008)

    for o in made:
        if o.type == 'MESH' and o.modifiers:
            G.apply_modifiers(o)
        if o is not body:
            o.parent = body
    body.matrix_world = base_world
    return made
