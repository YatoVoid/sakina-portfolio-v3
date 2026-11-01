"""Edit #6b (user request 2026-11-01): shorten the centre desk and re-place everything on it so the items sit close together
(about one hand-width apart) but none touches or overlaps another.

How it works
  1. every group of objects standing on the desk top is found by name (a "group" = one real-world item with all its parts);
  2. the VCR + CRT monitor (with its cables) and the plant stay where they are (they anchor the cables / the left end);
  3. the other items are packed on the desk top by a randomised bottom-left packer on a 5 mm grid. Each item keeps a GAP
     clear border; tall items (pencil holder, trophy, lamp) go in the back half, so they never hide the flat items in front;
  4. the desk is shortened to just fit the packed items: planks / rails are stretched from their left end, the right-hand legs and
     side rails move with the new right end, the drawer is re-centred; the left end stays at x = -1.25;
  5. an independent check prints the smallest gap between every pair of items (must be >= GAP - 1 mm) and flags anything
     hanging over the desk edge.
"""
import bpy, math, random
from mathutils import Vector, Matrix
import numpy as np

D = bpy.data
GAP = 0.030                       # clear space around every item (m)
DESK_X0, DESK_X1_OLD, DESK_Y0, DESK_Y1 = -1.25, 1.65, 1.30, 2.00
TOP_PAD_X, TOP_PAD_FRONT, TOP_PAD_BACK = 0.05, 0.040, 0.065      # keep-out at the left end / front edge / back (cables run at y>1.95)
TALL_Y_MIN = 1.62                 # tall things stand in the back half
RES = 0.005

# group name -> (name tokens, may be rotated by 90 degrees, tall)
GROUPS = {
    "Notepad":  (("Notepad",), True, False),
    "CD":       (("CD",), True, False),
    "Pencil":   (("PencilHolder", "Holder"), False, True),
    "Calc":     (("Calculator", "Calc"), True, False),
    "Notebook": (("Notebook",), True, False),
    "Lamp":     (("Lamp",), False, True),
    "Rolodex":  (("Rolodex",), False, False),
    "Pad":      (("Pad",), True, False),
    "Mug":      (("Mug", "Steam", "Coffee", "SteamCurve"), True, False),
    "Note":     (("Note",), True, False),
    "Remote":   (("Remote",), True, False),
    "Tape":     (("Tape",), True, False),
    "PaperY":   (("Paper",), True, False),          # yellow pad + its ruling / handwriting (everything named Paper_* except Paper_White)
    "PaperW":   ((), True, False),                  # the white sheet (Paper_White)
    "Floppy":   (("Floppy",), True, False),
    "PTape":    (("PTape",), True, False),
    "Rec":      (("Rec", "Recorder"), False, False),
    "Trophy":   (("Trophy",), False, True),
    "Phone":    (("Phone",), False, False),
}
FOLLOW_LIGHTS = {"Lamp": ("L1_DeskLamp_Key", "L2_DeskLamp_Spill")}
FOOTPRINT_EXCLUDE = {"Mug": ("Steam", "SteamCurve", "Coffee")}      # steam is a puff of smoke, not an obstacle
FIXED = {                                                             # stay put; kept as obstacles
    "Plant":   (("Saucer", "Pot", "Pebble", "Stem"), None),
    "Monitor": (("VCR", "CRT", "Scr"), None),
}
LEAF_TOKENS = ("Leaf",)


def tok(name):
    return name.replace(".", "_").split("_")[0]


def on_desk(o):
    if o.type == 'EMPTY':
        p = o.matrix_world.translation
        return -1.40 < p.x < 1.75 and 1.2 < p.y < 2.1 and 0.6 < p.z < 1.3
    if o.type not in ('MESH', 'CURVE'):
        return False
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    cx = sum(w.x for w in ws) / 8; cy = sum(w.y for w in ws) / 8; zl = min(w.z for w in ws)
    return -1.40 < cx < 1.75 and 1.2 < cy < 2.1 and 0.66 < zl < 1.35


def world_box(o):
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [min(w[i] for w in ws) for i in range(3)], [max(w[i] for w in ws) for i in range(3)]


def collect():
    """group -> list of objects (roots and children); skips desk parts"""
    allg = {}
    for key, (toks, _, _) in GROUPS.items():
        allg[key] = toks
    for key, (toks, _) in FIXED.items():
        allg[key] = toks
    allg["Leaf"] = LEAF_TOKENS
    found = {k: [] for k in allg}
    for o in D.objects:
        if o.name.startswith(("Desk_", "Radiator_", "Wall_", "WClock_", "Degree")) or o.type == 'LIGHT':
            continue
        t = tok(o.name)
        if o.name == "Paper_White":
            if on_desk(o):
                found["PaperW"].append(o)
            continue
        for key, toks in allg.items():
            if t in toks and on_desk(o):
                found[key].append(o)
                break
    for key, names in FOLLOW_LIGHTS.items():
        found[key] += [D.objects[n] for n in names if n in D.objects]
    return found


def footprint(key, objs):
    lo = [1e9] * 3; hi = [-1e9] * 3
    skip = FOOTPRINT_EXCLUDE.get(key, ())
    for o in objs:
        if o.type not in ('MESH', 'CURVE') or tok(o.name) in skip:
            continue
        a, b = world_box(o)
        for i in range(3):
            lo[i] = min(lo[i], a[i]); hi[i] = max(hi[i], b[i])
    return lo, hi


# ------------------------------------------------------------------ packer
def pack(items, fixed_rects, air_rects, seed, allow_rot, x_max=1.90):
    """items: list of dict(key, w, d, rot, tall, zhi). Returns (R, placement) or None."""
    rnd = random.Random(seed)
    xmin = DESK_X0 + TOP_PAD_X; ymin = DESK_Y0 + TOP_PAD_FRONT; ymax = DESK_Y1 - TOP_PAD_BACK
    nx = int(round((x_max - xmin) / RES)); ny = int(round((ymax - ymin) / RES))
    occ = np.zeros((ny, nx), np.int32); air = np.zeros((ny, nx), np.int32)

    def mark(grid, x0, y0, x1, y1, g=GAP):
        j0 = max(0, int(math.floor((x0 - g - xmin) / RES))); j1 = min(nx, int(math.ceil((x1 + g - xmin) / RES)))
        i0 = max(0, int(math.floor((y0 - g - ymin) / RES))); i1 = min(ny, int(math.ceil((y1 + g - ymin) / RES)))
        if j1 > j0 and i1 > i0:
            grid[i0:i1, j0:j1] = 1

    for r in fixed_rects:
        mark(occ, *r)
    for r in air_rects:
        mark(air, *r)
    order = list(items)
    if seed == 0:
        order.sort(key=lambda it: -it["w"] * it["d"])
    else:
        order.sort(key=lambda it: -it["w"] * it["d"] * rnd.uniform(0.5, 1.5))
    placed = {}
    for it in order:
        best = None
        for rot in ((False, True) if (allow_rot and it["rot"]) else (False,)):
            w, d = (it["d"], it["w"]) if rot else (it["w"], it["d"])
            wc = int(math.ceil(w / RES)); dc = int(math.ceil(d / RES))
            if wc >= nx or dc >= ny:
                continue
            g = occ | air if it["zhi"] > 0.89 else occ
            S = np.zeros((ny + 1, nx + 1), np.int32); S[1:, 1:] = g.cumsum(0).cumsum(1)
            tot = S[dc:, wc:] - S[:ny + 1 - dc, wc:] - S[dc:, :nx + 1 - wc] + S[:ny + 1 - dc, :nx + 1 - wc]
            ok = tot == 0
            if it["tall"]:
                ok[:int(round((TALL_Y_MIN - ymin) / RES)), :] = False
            if not ok.any():
                continue
            ii, jj = np.nonzero(ok)
            cost = (jj + wc) * 1000.0 + ii
            if seed:
                cost = cost + np.random.default_rng(seed * 7919 + len(placed)).random(len(ii)) * 2500.0
            k = int(np.argmin(cost))
            c = (cost[k], ii[k], jj[k], rot, w, d)
            if best is None or c[0] < best[0]:
                best = c
        if best is None:
            if seed == 0:
                print('e07: packer could not place', it['key'], round(it['w'], 3), round(it['d'], 3), 'after', list(placed), flush=True)
            return None
        _, i, j, rot, w, d = best
        x0 = xmin + j * RES; y0 = ymin + i * RES
        placed[it["key"]] = (x0, y0, w, d, rot)
        mark(occ, x0, y0, x0 + w, y0 + d)
    R = max([x0 + w for (x0, y0, w, d, r) in placed.values()] + [r[2] for r in fixed_rects])
    return R, placed


# ------------------------------------------------------------------ moves
def move_group(objs, M):
    ids = set(objs)
    for o in objs:
        if o.parent in ids:
            continue
        o.matrix_world = M @ o.matrix_world


def own_mesh(o):
    if o.data.users > 1:
        o.data = o.data.copy()
    return o.data


def warp_x(o, fn):
    me = own_mesh(o)
    M = o.matrix_world.copy(); Mi = M.inverted()
    for v in me.vertices:
        w = M @ v.co
        w.x = fn(w.x)
        v.co = Mi @ w
    me.update()


def shorten_desk(x1_new):
    dL = x1_new - DESK_X1_OLD                       # negative
    old_len = DESK_X1_OLD - DESK_X0
    f_joint = lambda x: DESK_X0 + (x - DESK_X0) * (old_len + dL) / old_len
    drawer_shift = dL / 2
    n_planks = n_right = n_drawer = n_joint = 0
    for o in list(D.objects):
        if not o.name.startswith("Desk_") or o.type != 'MESH':
            continue
        a, b = world_box(o)
        n = o.name
        if n.startswith(("Desk_Drawer", "Desk_Pull", "Desk_Key")):
            o.matrix_world = Matrix.Translation((drawer_shift, 0, 0)) @ o.matrix_world; n_drawer += 1
        elif n.startswith("Desk_Joint"):
            o.matrix_world = Matrix.Translation((f_joint((a[0] + b[0]) / 2) - (a[0] + b[0]) / 2, 0, 0)) @ o.matrix_world; n_joint += 1
        elif b[0] - a[0] > 1.0:                      # long planks / rails: stretch from the left end so the right end moves by dL
            k = (b[0] - a[0] + dL) / (b[0] - a[0])
            warp_x(o, lambda x, a0=a[0], k=k: a0 + (x - a0) * k); n_planks += 1
        elif (a[0] + b[0]) / 2 > 1.0:                # right-hand legs / blocks / caps / side rails
            o.matrix_world = Matrix.Translation((dL, 0, 0)) @ o.matrix_world; n_right += 1
    print(f"e07: desk shortened by {-dL:.3f} m (x -1.25 .. {x1_new:.2f}); stretched {n_planks} planks, moved {n_right} right-side parts, "
          f"{n_joint} joints, {n_drawer} drawer parts", flush=True)


# ------------------------------------------------------------------ validation
def validate(rects, x1_new):
    names = list(rects)
    worst = 9.0; bad = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = rects[names[i]]; b = rects[names[j]]
            dx = max(a[0] - b[2], b[0] - a[2], 0.0); dy = max(a[1] - b[3], b[1] - a[3], 0.0)
            gap = math.hypot(dx, dy) if dx > 0 and dy > 0 else max(dx, dy)
            if dx == 0 and dy == 0:
                gap = -1.0
            worst = min(worst, gap)
            if gap < GAP - 0.001:
                bad.append((names[i], names[j], round(gap, 3)))
    edge = []
    for n, r in rects.items():
        if r[0] < DESK_X0 + 0.02 or r[2] > x1_new - 0.02 or r[1] < DESK_Y0 + 0.02 or r[3] > DESK_Y1 - 0.02:
            edge.append(n)
    return worst, bad, edge


def apply():
    found = collect()
    for k, v in found.items():
        print(f"e07: group {k:9s} {len(v):3d} objects", flush=True)
    fp = {k: footprint(k, v) for k, v in found.items() if v}
    fixed_rects = []
    for k in FIXED:
        lo, hi = fp[k]
        fixed_rects.append((lo[0], lo[1], hi[0], hi[1]))
    leaf_lo, leaf_hi = fp["Leaf"]
    air_rects = [(leaf_lo[0], leaf_lo[1], leaf_hi[0], leaf_hi[1])]
    items = []
    for key, (toks, rot, tall) in GROUPS.items():
        lo, hi = fp[key]
        items.append(dict(key=key, w=hi[0] - lo[0], d=hi[1] - lo[1], rot=rot, tall=tall, zhi=hi[2]))
        print(f"e07:   {key:9s} {hi[0]-lo[0]:.3f} x {hi[1]-lo[1]:.3f}  at x {lo[0]:.3f}..{hi[0]:.3f} y {lo[1]:.3f}..{hi[1]:.3f}", flush=True)

    print('e07: fixed rects', [tuple(round(v, 3) for v in r) for r in fixed_rects], 'air', [tuple(round(v, 3) for v in r) for r in air_rects], flush=True)
    best = None
    for allow_rot in (False, True):
        for seed in range(0, 500 if not allow_rot else 1600):
            res = pack(items, fixed_rects, air_rects, seed, allow_rot)
            if res and (best is None or res[0] < best[0] - 1e-9):
                best = (res[0], res[1], allow_rot, seed)
        if best:
            print(f"e07: after rotation={allow_rot}: best right edge {best[0]:.3f} (seed {best[3]})", flush=True)
    R, placed, allow_rot, seed = best
    x1_new = math.ceil((R + 0.06) / 0.01 - 1e-9) * 0.01
    print(f"e07: layout right edge {R:.3f} -> new desk right end {x1_new:.2f} (length {x1_new - DESK_X0:.2f} m, was 2.90)", flush=True)

    # move the items
    rects = {}
    for k, (lo, hi) in fp.items():
        if k in FIXED:
            rects[k] = (lo[0], lo[1], hi[0], hi[1])
    for key, (x0, y0, w, d, rot) in placed.items():
        lo, hi = fp[key]
        c_old = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, 0.0))
        c_new = Vector((x0 + w / 2, y0 + d / 2, 0.0))
        M = Matrix.Translation(c_new) @ (Matrix.Rotation(math.radians(90), 4, 'Z') if rot else Matrix.Identity(4)) @ Matrix.Translation(-c_old)
        move_group(found[key], M)
        rects[key] = (x0, y0, x0 + w, y0 + d)
    shorten_desk(x1_new)
    bpy.context.view_layer.update()

    # independent check from the real, moved geometry
    real = {}
    for k in list(GROUPS) + list(FIXED):
        lo, hi = footprint(k, found[k])
        real[k] = (lo[0], lo[1], hi[0], hi[1])
    worst, bad, edge = validate(real, x1_new)
    print(f"e07: smallest gap between any two items = {worst*100:.1f} cm; pairs closer than {GAP*100:.1f} cm: {bad or 'none'}", flush=True)
    print("e07: items near/over the desk edge:", edge or "none", flush=True)
    for k in sorted(real, key=lambda k: real[k][0]):
        r = real[k]; print(f"e07:   {k:9s} x {r[0]:.3f}..{r[2]:.3f}  y {r[1]:.3f}..{r[3]:.3f}", flush=True)
    # plant leaves vs items that are tall enough to meet them
    llo, lhi = footprint("Leaf", found["Leaf"])
    for k in real:
        lo, hi = footprint(k, found[k])
        if k not in ("Plant", "Leaf") and hi[2] > 0.89 and not (real[k][2] < llo[0] or real[k][0] > lhi[0] or real[k][3] < llo[1] or real[k][1] > lhi[1]):
            print("e07: leaf footprint overlaps tall item", k, flush=True)
