"""Desk lamp: red enamel gooseneck lamp, rebuilt around the existing bulb.

Kept: `Lamp_Bulb` (object, material and position) — the room lighting (and round 3's e07) is built around it.
Names the room session looks up are reused: Lamp_Shade, Lamp_Inner, Lamp_Rim, Lamp_Cap, Lamp_Joint, Lamp_Base,
Lamp_Base_Top, Lamp_Switch, plus new Lamp_Arm, Lamp_Socket, Lamp_Cord, Lamp_Foot, Lamp_Vent_*.
Footprint unchanged (base r 8.5 cm at x -0.52, y 1.70), so the plant's keep-out box still holds.
"""
import bpy, math
from mathutils import Vector, Matrix
import geo as G
import mats as M

DESK = 0.720
BASE_C = Vector((-0.520, 1.700))
OLD_PREFIX = ("Lamp_Arm", "Lamp_Base", "Lamp_Cap", "Lamp_Inner", "Lamp_Joint", "Lamp_Rim", "Lamp_Shade", "Lamp_Switch")
AXIS = Vector((0.577, 0.0, -0.817))      # shade axis (cap -> mouth), from the old shade: tilted 35 deg toward the desk
BULB_DEPTH, SHADE_LEN = 0.068, 0.112     # bulb centre sits 6.8 cm inside the 11.2 cm shade


def _frame(origin, axis):
    """Matrix whose local +Z is `axis`, placed at `origin`."""
    q = axis.to_track_quat('Z', 'Y')
    return Matrix.Translation(origin) @ q.to_matrix().to_4x4()


def build(coll):
    D = bpy.data
    bulb = D.objects["Lamp_Bulb"]
    bulb_c = bulb.matrix_world.translation.copy()
    if bulb.type == 'MESH':
        pts = [bulb.matrix_world @ Vector(c) for c in bulb.bound_box]
        bulb_c = sum(pts, Vector()) / 8
    for o in [o for o in D.objects if o.name.startswith(OLD_PREFIX)]:
        D.objects.remove(o, do_unlink=True)

    red = M.enamel("#8f1d14", "#a8281b", "R_LampRed")
    white = M.flat("#ece5d6", "R_LampInnerWhite", 0.55)
    chrome, rubber = M.chrome(), M.flat("#141313", "R_Rubber", 0.85)
    made = []

    # base: cast, domed, enamelled; rubber foot ring; rocker switch on the slope
    bx, by = BASE_C
    base = G.lathe("Lamp_Base", [(0.0, 0.0), (0.081, 0.0), (0.085, 0.003), (0.085, 0.011), (0.081, 0.016), (0.066, 0.021),
                                 (0.040, 0.025), (0.024, 0.027), (0.0, 0.027)], coll, red, 64,
                   matrix=Matrix.Translation((bx, by, DESK + 0.002)), cap=False)
    made.append(base)
    made.append(G.lathe("Lamp_Foot", [(0.074, 0.0), (0.080, 0.0), (0.080, 0.002), (0.074, 0.002)], coll, rubber, 48,
                        matrix=Matrix.Translation((bx, by, DESK))))
    made.append(G.lathe("Lamp_Base_Top", [(0.024, 0.0), (0.024, 0.006), (0.017, 0.012), (0.0105, 0.016), (0.0, 0.016)], coll, chrome, 40,
                        matrix=Matrix.Translation((bx, by, DESK + 0.027))))
    sw = Matrix.Translation((bx + 0.045, by - 0.048, DESK + 0.019)) @ Matrix.Rotation(math.radians(-44), 4, 'Z') @ Matrix.Rotation(math.radians(14), 4, 'Y')
    made.append(G.extrude_outline("Lamp_Switch", G.rounded_rect(0.016, 0.026, 0.004), 0.0, 0.004, coll, M.flat("#1a1817", "R_SwitchBlack", 0.45), 0.001, 2, matrix=sw))
    made.append(G.extrude_outline("Lamp_Switch_Rocker", G.rounded_rect(0.011, 0.019, 0.003), 0.004, 0.0065, coll, M.flat("#1a1817", "R_SwitchBlack", 0.45), 0.001, 2,
                                  matrix=sw @ Matrix.Rotation(math.radians(6), 4, 'Y')))

    # shade geometry placed so the existing bulb is on the axis, 6.8 cm deep
    cap_c = bulb_c - AXIS * BULB_DEPTH
    F = _frame(cap_c, AXIS)
    prof = [(0.0, -0.004), (0.020, -0.004), (0.026, 0.002), (0.029, 0.012), (0.036, 0.030), (0.052, 0.055), (0.068, 0.078),
            (0.081, 0.097), (0.089, SHADE_LEN - 0.004), (0.091, SHADE_LEN)]
    made.append(G.lathe("Lamp_Shade", prof, coll, red, 64, matrix=F))
    inner = [(r - 0.0012 if r > 0 else 0.0, z + 0.0012) for r, z in prof]
    inner_o = G.lathe("Lamp_Inner", inner, coll, white, 64, matrix=F)
    for p in inner_o.data.polygons:
        p.flip()
    made.append(inner_o)
    # rolled rim: small torus at the mouth
    rim = []
    for k in range(13):
        a = math.pi * 2 * k / 12
        rim.append((0.0915 + 0.0022 * math.cos(a), SHADE_LEN + 0.0022 * math.sin(a)))
    made.append(G.lathe("Lamp_Rim", rim, coll, red, 64, matrix=F))
    # rear cap ring and vent slots around the back of the shade
    made.append(G.lathe("Lamp_Cap", [(0.0, -0.010), (0.016, -0.010), (0.022, -0.006), (0.023, 0.0), (0.021, 0.004)], coll, red, 48, matrix=F))
    vent = M.flat("#120c0b", "R_VentDark", 0.7)
    for k in range(10):
        a = 2 * math.pi * k / 10
        R = F @ Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation((0.032, 0, 0.022)) @ Matrix.Rotation(math.radians(-24), 4, 'Y')
        made.append(G.box(f"Lamp_Vent_{k}", (-0.0012, -0.0025, -0.006), (0.0012, 0.0025, 0.006), coll, vent))
        made[-1].matrix_world = R
    # socket holding the bulb
    made.append(G.lathe("Lamp_Socket", [(0.0, 0.0), (0.014, 0.0), (0.014, 0.022), (0.0125, 0.026), (0.010, 0.030), (0.0, 0.030)],
                        coll, M.flat("#2a2522", "R_SocketBakelite", 0.4), 32, matrix=F @ Matrix.Translation((0, 0, 0.012))))

    # knuckle joint behind the cap, gooseneck down to the base
    joint_c = cap_c - AXIS * 0.016
    made.append(G.lathe("Lamp_Joint", [(0.0, -0.011), (0.0095, -0.011), (0.0105, -0.006), (0.0105, 0.006), (0.0095, 0.011), (0.0, 0.011)],
                        coll, chrome, 32, matrix=_frame(joint_c, Vector((0, 1, 0)))))
    p0 = Vector((bx, by, DESK + 0.040)); p3 = joint_c + Vector((0, 0, -0.004))
    path = G.bezier(p0, p0 + Vector((0.0, 0.0, 0.17)), p3 + Vector((-0.07, 0.0, -0.03)), p3, 180)
    made.append(G.tube("Lamp_Arm", path, 0.0068, coll, chrome, 14,
                       radius_fn=lambda t, i: 0.0066 + (0.0007 if i % 2 == 0 else -0.0005)))   # ribbed gooseneck
    made.append(G.lathe("Lamp_ArmCollar", [(0.0, 0.0), (0.0105, 0.0), (0.0105, 0.012), (0.0085, 0.016), (0.0, 0.016)],
                        coll, chrome, 32, matrix=Matrix.Translation((bx, by, DESK + 0.036))))

    # power cord: out of the back of the base, across the desk, over the back edge
    c0 = Vector((bx + 0.004, by + 0.083, DESK + 0.004))
    cord = G.bezier(c0, c0 + Vector((0.02, 0.07, -0.002)), Vector((bx + 0.09, 1.96, DESK + 0.0025)), Vector((bx + 0.11, 2.005, DESK - 0.01)), 40)
    cord += G.bezier(cord[-1], cord[-1] + Vector((0.01, 0.02, -0.03)), Vector((bx + 0.13, 2.04, DESK - 0.25)), Vector((bx + 0.14, 2.05, DESK - 0.45)), 20)[1:]
    made.append(G.tube("Lamp_Cord", cord, 0.0025, coll, rubber, 10))
    for o in made:
        if o.type == 'MESH' and o.modifiers:
            G.apply_modifiers(o)
    return made
