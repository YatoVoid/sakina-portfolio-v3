"""Plain white curtains with real folds, flaring and curving at the bottom, on a slim rod with rings.

Same footprint as the old panels (left x -1.107..-0.712, right x 0.503..1.128; wall side y <= 2.487), so the
room session's keepsakes layout (which fits between the left wall corner and the curtain) is unaffected.
The right panel tucks behind the wooden post (x >= 1.12) exactly as before.
Fabric: 2.2x fullness, folds ~11 cm apart at the top; fold depth grows toward the floor; the hem curves out
into the room and breaks 3 cm on the floor; header gathered into pinch pleats on rings.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
import geo as G
import mats as M

OLD = ["Curtain_L", "Curtain_R"]
TOP, ROD_Z = 2.70, 2.735
Y_BACK = 2.470                      # fabric centre plane at the top (in front of the window trim at 2.482)
PANELS = {"L": (-1.107, -0.712), "R": (0.503, 1.118)}


def _panel(name, x0, x1, coll, mat, seed, inner_right):
    rnd = random.Random(seed)
    w = x1 - x0
    nf = max(4, round(w / 0.105))                     # number of folds across the panel
    nu, nv = nf * 10, 72
    phases = [rnd.uniform(-0.25, 0.25) for _ in range(nf + 2)]
    depths = [rnd.uniform(0.75, 1.25) for _ in range(nf + 2)]
    bm = bmesh.new()
    grid = []
    def interp(arr, k):                               # smooth (cosine) interpolation between fold values
        i = int(min(k, len(arr) - 2)); f = k - i
        f = (1 - math.cos(f * math.pi)) / 2
        return arr[i] * (1 - f) + arr[i + 1] * f
    for j in range(nv + 1):
        v = j / nv                                   # 0 = top, 1 = floor
        z = TOP * (1 - v)
        amp = 0.020 + (0.058 - 0.020) * v ** 1.5     # fold half-depth: shallow at the header, deep at the hem
        flare = 0.06 * v ** 2.4                       # panel spreads at the bottom
        sweep = 0.065 * max(0.0, (v - 0.86) / 0.14) ** 2   # bottom 38 cm curves out into the room
        row = []
        for i in range(nu + 1):
            u = i / nu
            k = u * nf
            ph, d = interp(phases, k), interp(depths, k)
            wave = math.sin(2 * math.pi * (k + ph * v))
            y = Y_BACK - 0.004 - amp * d * (0.5 + 0.5 * wave) - sweep * (0.75 + 0.25 * wave)
            edge = u if inner_right else 1 - u        # inner edge (toward the window) swings out most
            x = x0 + u * w + (1 if inner_right else -1) * flare * edge
            zz = z + (0.012 * (0.5 + 0.5 * wave) if v > 0.97 else 0.0)   # hem rests on the floor, crests lift a little
            row.append(bm.verts.new((x, y, max(0.0, zz))))
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            bm.faces.new([grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]])
    o = G.mesh_obj(name, bm, coll, mat, smooth=True)
    so = o.modifiers.new("Solidify", 'SOLIDIFY'); so.thickness = 0.0025; so.offset = 0.0
    G.apply_modifiers(o)
    return o, nf


def _pleats_and_rings(name, x0, x1, nf, coll):
    """Pinch pleats at the header and one ring per pleat on the rod."""
    bronze = M.dark_bronze()
    made = []
    for i in range(nf + 1):
        x = x0 + (x1 - x0) * i / nf
        made.append(G.lathe(f"{name}_Ring{i}", [(0.016, -0.002), (0.016, 0.002)], coll, bronze, 20,
                            matrix=Matrix.Translation((x, Y_BACK - 0.012, ROD_Z)) @ Matrix.Rotation(math.radians(90), 4, 'Y')))
        # ring = torus-like thin band around the rod; small hook down to the fabric
        made.append(G.tube(f"{name}_Hook{i}", [Vector((x, Y_BACK - 0.012, ROD_Z - 0.016)), Vector((x, Y_BACK - 0.010, TOP + 0.003))],
                           0.0015, coll, bronze, 8))
    return made


def build(coll):
    G.remove(OLD)
    fabric = M.curtain_white()
    made = []
    for side, (x0, x1) in PANELS.items():
        o, nf = _panel(f"Curtain_{side}", x0, x1, coll, fabric, 11 if side == "L" else 23, inner_right=(side == "L"))
        made.append(o)
        made += _pleats_and_rings(f"Curtain_{side}", x0 + 0.01, x1 - 0.01, nf, coll)
    # rod with end finials and two wall brackets; stops short of the wooden post on the right
    bronze = M.dark_bronze()
    rx0, rx1, ry = -1.16, 1.075, Y_BACK - 0.012
    made.append(G.tube("Curtain_Rod", [Vector((rx0, ry, ROD_Z)), Vector((rx1, ry, ROD_Z))], 0.011, coll, bronze, 20))
    for i, x in enumerate((rx0, rx1)):
        s = -1 if i == 0 else 1
        made.append(G.lathe(f"Curtain_Finial{i}", [(0.012, 0), (0.016, 0.006), (0.018, 0.016), (0.013, 0.026), (0.006, 0.032), (0, 0.034)],
                            coll, bronze, 24, matrix=Matrix.Translation((x, ry, ROD_Z)) @ Matrix.Rotation(math.radians(90 * s), 4, 'Y')))
    for i, x in enumerate((-1.06, 0.99)):
        made.append(G.tube(f"Curtain_Bracket{i}", [Vector((x, ry, ROD_Z)), Vector((x, 2.495, ROD_Z + 0.004))], 0.005, coll, bronze, 12))
        made.append(G.lathe(f"Curtain_BracketPlate{i}", [(0.018, 0), (0.018, 0.004), (0.0, 0.005)], coll, bronze, 20,
                            matrix=Matrix.Translation((x, 2.499, ROD_Z + 0.004)) @ Matrix.Rotation(math.radians(90), 4, 'X')))
    return made
