"""Casement window: two sashes meeting at one vertical stile (no horizontal transom), brass handle and hinges.

Built in room coordinates inside the existing opening (x -0.73..0.52, z 0.902..2.30, wall face y = 2.50).
Keeps the existing Sill / Sill_Lip and the WindowPaint + WindowGlass materials (approved colours; glass stays
out of the bake and the web export by its name prefix "Glass").
Replaces: Frame_Left, Frame_Right, Frame_Top, Mullion_H, Mullion_V, Glass, Handle_Lever, Handle_Plate, Bead_0L..Bead_3B.
Keeps RainLines (rain on the glass).
"""
import bpy, math
from mathutils import Vector, Matrix
import geo as G
import mats as M

OLD = ["Frame_Left", "Frame_Right", "Frame_Top", "Mullion_H", "Mullion_V", "Glass", "Handle_Lever", "Handle_Plate"] + \
    [f"Bead_{p}{s}" for p in range(4) for s in "LRTB"]          # glazing beads of the old four panes
OX0, OX1, OZ0, OZ1 = -0.73, 0.52, 0.902, 2.30      # opening
WALL = 2.50                                         # room-side wall face (room is -Y)
XC = (OX0 + OX1) / 2                                # meeting stile centre (old mullion centre)


def _paint():
    return G.D.materials.get("WindowPaint") or M.flat("#efe4cc", "WindowPaint", 0.55)


def _glass():
    return G.D.materials.get("WindowGlass") or M.flat("#ffffff", "WindowGlass", 0.0)


def _sash(name, x0, x1, z0, z1, coll, paint):
    """Sash ring (stiles + rails) with bevelled edges, glazing beads on the room side, glass pane."""
    y0, y1 = WALL - 0.005, WALL + 0.065           # sash depth, 5 mm proud of the frame
    s, rt, rb = 0.062, 0.062, 0.085               # stile, top rail, bottom rail widths
    parts = [
        G.box(name + "_StileL", (x0, y0, z0), (x0 + s, y1, z1), coll, paint, 0.004, 2),
        G.box(name + "_StileR", (x1 - s, y0, z0), (x1, y1, z1), coll, paint, 0.004, 2),
        G.box(name + "_RailT", (x0 + s, y0, z1 - rt), (x1 - s, y1, z1), coll, paint, 0.004, 2),
        G.box(name + "_RailB", (x0 + s, y0, z0), (x1 - s, y1, z0 + rb), coll, paint, 0.004, 2),
    ]
    ix0, ix1, iz0, iz1 = x0 + s, x1 - s, z0 + rb, z1 - rt
    b, by0, by1 = 0.014, y0 + 0.004, y0 + 0.020    # glazing bead: 14 mm, chamfered toward the glass
    for nm, lo, hi in (("BeadL", (ix0, by0, iz0), (ix0 + b, by1, iz1)), ("BeadR", (ix1 - b, by0, iz0), (ix1, by1, iz1)),
                       ("BeadT", (ix0 + b, by0, iz1 - b), (ix1 - b, by1, iz1)), ("BeadB", (ix0 + b, by0, iz0), (ix1 - b, by1, iz0 + b))):
        parts.append(G.box(f"{name}_{nm}", lo, hi, coll, paint, 0.005, 3, smooth=True))
    glass = G.box("Glass_" + name[-1], (ix0 - 0.008, y0 + 0.032, iz0 - 0.008), (ix1 + 0.008, y0 + 0.036, iz1 + 0.008), coll, _glass())
    return parts, glass


def _handle(coll, at):
    """Brass window handle (closed position, lever pointing down). `at` = centre of the rosette face."""
    brass = M.brass_aged()
    T = Matrix.Translation(at)
    objs = []
    ros = G.extrude_outline("Handle_Rosette", G.rounded_rect(0.032, 0.078, 0.014, 6), 0.0, 0.009, coll, brass, 0.0025, 3,
                            matrix=T @ Matrix.Rotation(math.radians(90), 4, 'X'))
    # rosette: built in XY, rotated so its thickness runs toward the room (-Y)
    objs.append(ros)
    for i, dz in enumerate((0.027, -0.027)):          # slotted screw heads
        sc = G.lathe(f"Handle_Screw_{i}", [(0, 0.003), (0.0035, 0.0026), (0.0042, 0.001), (0.0042, 0)], coll, brass, 20,
                     matrix=T @ Matrix.Translation((0, -0.009, dz)) @ Matrix.Rotation(math.radians(90), 4, 'X'))
        objs.append(sc)
        G.box(f"Handle_Slot_{i}", (-0.0035, -0.0125, dz - 0.0004), (0.0035, -0.0110, dz + 0.0004), coll, M.flat("#2a2016", "R_SlotDark", 0.6))
        G.D.objects[f"Handle_Slot_{i}"].matrix_world = T @ G.D.objects[f"Handle_Slot_{i}"].matrix_world
    neck = G.lathe("Handle_Neck", [(0.0115, 0.0), (0.0115, 0.003), (0.0095, 0.005), (0.0088, 0.020), (0.0098, 0.024), (0.0, 0.026)],
                   coll, brass, 32, matrix=T @ Matrix.Translation((0, -0.009, 0.012)) @ Matrix.Rotation(math.radians(90), 4, 'X'))
    objs.append(neck)
    # lever: tube from the neck front, bending down, flattened to an oval section, rounded end
    p = [Vector(v) for v in ((0, -0.031, 0.012), (0, -0.036, 0.004), (0, -0.040, -0.012))]
    p += G.bezier(Vector((0, -0.040, -0.012)), Vector((0, -0.043, -0.045)), Vector((0, -0.041, -0.080)), Vector((0, -0.036, -0.112)), 14)[1:]
    lever = G.tube("Handle_Lever", p, 0.0085, coll, brass, 20,
                   radius_fn=lambda t, i: 0.0085 * (1.0 - 0.18 * t) * (0.55 + 0.45 * math.sin(min(1, t * 12) * math.pi / 2)))
    lever.data.transform(Matrix.Diagonal((1.45, 1.0, 1.0, 1.0)))       # oval section, wider across
    G.subsurf(lever, 1)
    lever.matrix_world = T
    objs.append(lever)
    return objs


def _hinge(name, x, z, coll):
    brass = M.brass_aged()
    h = G.lathe(name, [(0, -0.052), (0.0045, -0.050), (0.0062, -0.046), (0.0068, -0.040), (0.0068, 0.040), (0.0062, 0.046),
                       (0.0045, 0.050), (0, 0.052)], coll, brass, 24, matrix=Matrix.Translation((x, WALL - 0.010, z)))
    G.box(name + "_Leaf", (x - 0.003, WALL - 0.008, z - 0.035), (x + 0.003, WALL + 0.01, z + 0.035), coll, brass)
    return h


def build(coll):
    G.remove(OLD)
    paint = _paint()
    made = []
    # trim (architrave) on the wall face around the opening
    t, ty0 = 0.065, WALL - 0.018
    made += [G.box("Window_TrimL", (OX0 - t, ty0, OZ0 - 0.035), (OX0, WALL, OZ1 + t), coll, paint, 0.005, 3),
             G.box("Window_TrimR", (OX1, ty0, OZ0 - 0.035), (OX1 + t, WALL, OZ1 + t), coll, paint, 0.005, 3),
             G.box("Window_TrimT", (OX0 - t, ty0, OZ1), (OX1 + t, WALL, OZ1 + t), coll, paint, 0.005, 3)]
    # outer frame inside the reveal
    f, fb, fy0, fy1 = 0.055, 0.045, WALL, WALL + 0.08
    made += [G.box("Window_FrameL", (OX0, fy0, OZ0), (OX0 + f, fy1, OZ1), coll, paint, 0.003),
             G.box("Window_FrameR", (OX1 - f, fy0, OZ0), (OX1, fy1, OZ1), coll, paint, 0.003),
             G.box("Window_FrameT", (OX0 + f, fy0, OZ1 - f), (OX1 - f, fy1, OZ1), coll, paint, 0.003),
             G.box("Window_FrameB", (OX0 + f, fy0, OZ0), (OX1 - f, fy1, OZ0 + fb), coll, paint, 0.003)]
    # two sashes overlapping the frame rebate by 12 mm, 2 mm gap at the meeting stiles
    ov = 0.012
    sx0, sx1, sz0, sz1 = OX0 + f - ov, OX1 - f + ov, OZ0 + fb - ov, OZ1 - f + ov
    pl, gl = _sash("Sash_L", sx0, XC - 0.001, sz0, sz1, coll, paint)
    pr, gr = _sash("Sash_R", XC + 0.001, sx1, sz0, sz1, coll, paint)
    made += pl + pr + [gl, gr]
    # cover strip over the meeting stiles (one vertical bar, room side), fixed to the right sash
    made.append(G.box("Sash_CoverStrip", (XC - 0.024, WALL - 0.016, sz0 + 0.01), (XC + 0.024, WALL - 0.004, sz1 - 0.01), coll, paint, 0.0045, 3))
    # handle at mid-height of the sash on the cover strip, hinges on the outer stiles
    made += _handle(coll, Vector((XC, WALL - 0.016, (sz0 + sz1) / 2 + 0.02)))
    for side, x in (("L", sx0 + 0.004), ("R", sx1 - 0.004)):
        for k, z in enumerate((sz0 + 0.17, sz1 - 0.17)):
            made.append(_hinge(f"Window_Hinge{side}{k}", x, z, coll))
    for o in list(coll.objects):
        if o.type == 'MESH' and o.modifiers:
            G.apply_modifiers(o)
    return made
