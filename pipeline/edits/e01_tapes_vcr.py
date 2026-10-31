"""Edit #1 (user request 2026-10-31): shorter VHS tapes stacked at a slant, smaller VCR under the CRT.

Tapes: bodies rebuilt to real VHS proportions (was 33.6 x 19.2 x 3.0 cm; real cassette 18.7 x 10.3 x 2.5 cm).
       Thickness is kept, so stack heights and the click rows stay the same.
       Labels are scaled uniformly (never squashed) and re-laid out to fit the shorter spine.
       Each stack becomes a staircase: every tape shifts sideways from the one below it.
VCR:   width 59 cm -> 40 cm, re-centred under the CRT. Height and depth unchanged, so the CRT and the cables
       plugged into the VCR back stay where they are.
"""
import bpy, math
from mathutils import Matrix, Vector

TAPE_L, TAPE_W = 0.200, 0.112        # new length (spine) and depth, metres
LABEL_K = 0.80                        # uniform scale for spine labels
TOP_K = 0.62                          # uniform scale for the sticker/text on top of the Dental-X tape
STEP_X = 0.013                        # sideways shift per tape going up the stack (the slant)
YAW_DEG = [-3.0, 2.5, -2.0, 3.5, -2.5, 2.0, -3.0]   # small per-tape twist, bottom -> top, for a hand-stacked look

STACKS = {   # bottom -> top
    "left":  ["Tape_The", "Tape_Softsyncdev", "Tape_Blutech", "Tape_University", "Tape_Tmac", "Tape_Dental-X"],
    "right": ["PTape_7", "PTape_6", "PTape_5", "PTape_4", "PTape_3", "PTape_2", "PTape_1"],
}

VCR_WIDTH, VCR_CENTRE_X = 0.40, -0.02   # CRT_Front is centred at x = -0.02


def _single_user_mesh(o):
    if o.data.users > 1:
        o.data = o.data.copy()


def _local_bounds(o):
    xs = [v.co.x for v in o.data.vertices]; ys = [v.co.y for v in o.data.vertices]
    return min(xs), max(xs), min(ys), max(ys)


def _rebuild_tape(root, centre_xy, yaw):
    D = bpy.data
    x0, x1, y0, y1 = _local_bounds(root)
    half_l_old, half_w_old = (x1 - x0) / 2, (y1 - y0) / 2
    sx, sy = TAPE_L / (x1 - x0), TAPE_W / (y1 - y0)
    hl = TAPE_L / 2

    # Children relative to the tape (captured before anything moves).
    rel = {c.name: root.matrix_world.inverted() @ c.matrix_world for c in root.children}

    # Body: scale mesh data (keeps bevel width uniform).
    _single_user_mesh(root)
    root.data.transform(Matrix.Diagonal((sx, sy, 1.0, 1.0)))
    root.data.update()

    # Place the tape: keep its front face where it was, slide sideways for the slant, small twist.
    front_y_world = (root.matrix_world @ Vector((0, y0, 0))).y
    z = root.matrix_world.translation.z
    new_world = Matrix.Translation((centre_xy, front_y_world + TAPE_W / 2, z)) @ Matrix.Rotation(math.radians(yaw), 4, 'Z')
    root.matrix_world = new_world

    def xspan(c):                                         # child's x extent in tape-local coords
        xs = [(rel[c.name] @ Vector(b)).x for b in c.bound_box]
        return min(xs), max(xs)

    # Right end of the label strip = just left of the number (which stays anchored to the right end).
    no = next((c for c in root.children if c.name.endswith("_No") and not c.name.startswith("Tape_Top_")), None)
    no_left = hl + LABEL_K * (xspan(no)[0] - half_l_old) if no else hl - 0.02
    strip_end = no_left - 0.006
    text_end = strip_end - 0.004

    for c in root.children:
        m = rel[c.name]
        p = m.translation.copy()
        lin = m.to_3x3().to_4x4()
        n = c.name
        if n.startswith("Tape_Top_"):                     # sticker + text on the top face
            k = TOP_K
            newp = Vector((p.x * k, p.y * k, p.z))
            S = Matrix.Diagonal((k, k, 1.0, 1.0))
        elif n.endswith("_No"):                           # number: anchored to the right end of the spine
            newp = Vector((hl + LABEL_K * (p.x - half_l_old), p.y * (TAPE_W / 2) / half_w_old, p.z * LABEL_K))
            S = Matrix.Diagonal((LABEL_K, LABEL_K, LABEL_K, 1.0))
        elif n.endswith(("_Strip", "_StripEdge")):        # colour band: from after the logo to before the number
            bx = [ (m @ Vector(b)).x for b in c.bound_box ]
            a_old, b_old = min(bx), max(bx)
            a_new = -hl + LABEL_K * (a_old + half_l_old)
            b_new = strip_end                             # stop short of the number
            fx = (b_new - a_new) / (b_old - a_old)
            # map x linearly [a_old,b_old] -> [a_new,b_new]; y onto the new face; z uniform
            newp = Vector((a_new + (p.x - a_old) * fx, p.y * (TAPE_W / 2) / half_w_old, p.z * LABEL_K))
            S = Matrix.Diagonal((fx, LABEL_K, LABEL_K, 1.0))
        elif c.type == 'FONT' and n.endswith(("_Name", "_Site")):   # text: anchored left, shrunk only if too long
            a_old, b_old = xspan(c)
            a_new = -hl + LABEL_K * (a_old + half_l_old)
            k = min(LABEL_K, (text_end - a_new) / (b_old - a_old))
            newp = Vector((a_new + k * (p.x - a_old), p.y * (TAPE_W / 2) / half_w_old, p.z * LABEL_K))
            S = Matrix.Diagonal((k, k, k, 1.0))
        else:                                             # logo, panel, icons: anchored left
            newp = Vector((-hl + LABEL_K * (p.x + half_l_old), p.y * (TAPE_W / 2) / half_w_old, p.z * LABEL_K))
            S = Matrix.Diagonal((LABEL_K, LABEL_K, LABEL_K, 1.0))
        c.matrix_world = root.matrix_world @ Matrix.Translation(newp) @ S @ lin


def _tapes():
    D = bpy.data
    for stack, names in STACKS.items():
        roots = [D.objects[n] for n in names]
        cx = sum(r.matrix_world.translation.x for r in roots) / len(roots)
        n = len(roots)
        for i, r in enumerate(roots):
            x = cx + (i - (n - 1) / 2) * STEP_X
            _rebuild_tape(r, x, YAW_DEG[i % len(YAW_DEG)])


def _vcr():
    D = bpy.data
    vcr = [o for o in D.collections["Monitor"].all_objects if o.name.startswith("VCR")]
    body = D.objects["VCR"]
    x0 = min((body.matrix_world @ Vector(b)).x for b in body.bound_box)
    x1 = max((body.matrix_world @ Vector(b)).x for b in body.bound_box)
    cx_old, fx = (x0 + x1) / 2, VCR_WIDTH / (x1 - x0)
    for o in vcr:
        loc = o.matrix_world.translation.copy()
        new_x = VCR_CENTRE_X + (loc.x - cx_old) * fx
        flat = all(abs(a) < 1e-4 for a in o.matrix_world.to_euler())
        if o.type == 'MESH' and flat:                     # boxes/panels: narrow the geometry itself
            _single_user_mesh(o)
            o.data.transform(Matrix.Diagonal((fx, 1.0, 1.0, 1.0)))
            o.data.update()
        # text, jacks (round) and anything rotated: move only, never squash
        mw = o.matrix_world.copy(); mw.translation.x = new_x; o.matrix_world = mw


def apply():
    _tapes()
    _vcr()
    bpy.context.view_layer.update()
