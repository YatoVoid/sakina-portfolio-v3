"""Open leather notebook, rebuilt in place of `Notebook` (same position, orientation, 35 x 26 cm footprint).

This is the site's "Currently" notepad (key N): it stays in the Desk collection at the same spot.
Cover: leather boards with rounded corners and a soft spine. Two page blocks whose top sheets curve down into
the gutter, layered page edges, ruled paper with pencil handwriting, red ribbon bookmark, elastic band.
The existing detailed pencil (Notebook_Pencil + ferrule + eraser) is kept and laid back on the right page.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix
import geo as G
import mats as M

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CW, CH, CT = 0.176, 0.264, 0.0028       # one cover board (width, height, thickness)
PW, PH = 0.168, 0.256                    # page size
BLOCK = {"L": 0.0055, "R": 0.0075}       # page-block thickness (opened a little before the middle)


def _page_block(name, side, coll, top_mat, edge_mat):
    """Closed page block. Local x from the gutter (0) outward; side 'R' builds +x, 'L' mirrors to -x."""
    t = BLOCK[side]
    nx, ny = 28, 6
    s = 1 if side == "R" else -1
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")

    def top_z(u):                         # sheet rises out of the gutter and flattens; tiny lift at the fore-edge
        g = 1 - math.exp(-u * PW / 0.018)
        return CT + 0.0012 + (t - 0.0012) * g + 0.0006 * max(0.0, (u - 0.85) / 0.15) ** 2
    top, bot = {}, {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            u = (i / nx) ** 1.6                # denser near the gutter where the curve is
            x, y = s * u * PW, -PH / 2 + j / ny * PH
            top[i, j] = (bm.verts.new((x, y, top_z(u))), u)
            bot[i, j] = bm.verts.new((x, y, CT))
    faces_top = []
    for j in range(ny):
        for i in range(nx):
            q = [top[i, j], top[i + 1, j], top[i + 1, j + 1], top[i, j + 1]]
            vs = [a for a, _ in q] if s > 0 else [a for a, _ in reversed(q)]
            f = bm.faces.new(vs); f.material_index = 0
            for loop in f.loops:
                (ii, jj) = next(k for k, (vv, _) in top.items() if vv is loop.vert)
                uu = top[ii, jj][1]
                loop[uvl].uv = ((uu if s > 0 else 1 - uu) if False else (uu if s > 0 else 1 - uu), jj / ny)
            faces_top.append(f)
    # sides: fore-edge, head, tail (page-edge material); gutter side closed
    def wall(a, b):
        f = bm.faces.new(a + b); f.material_index = 1
    for j in range(ny):
        a = [top[nx, j][0], top[nx, j + 1][0]]; b = [bot[nx, j + 1], bot[nx, j]]
        wall(*(([a[1], a[0]], [b[1], b[0]]) if s < 0 else (a, b)))
    for i in range(nx):
        for jj, flip in ((0, s > 0), (ny, s < 0)):
            a = [top[i + 1, jj][0], top[i, jj][0]]; b = [bot[i, jj], bot[i + 1, jj]]
            if (jj == ny) ^ (s < 0):
                a, b = [a[1], a[0]], [b[1], b[0]]
            wall(a, b)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = G.mesh_obj(name, bm, coll, None, smooth=True)
    o.data.materials.append(top_mat); o.data.materials.append(edge_mat)
    return o, top_z


def build(coll):
    D = bpy.data
    old = D.objects["Notebook"]
    lo = Vector([min(v.co[i] for v in old.data.vertices) for i in range(3)])
    hi = Vector([max(v.co[i] for v in old.data.vertices) for i in range(3)])
    c = (lo + hi) / 2
    base_world = old.matrix_world @ Matrix.Translation((c.x, c.y, lo.z))
    # keep the detailed pencil: unparent (keep world transform) before the old notebook is removed
    pencil = D.objects.get("Notebook_Pencil")
    if pencil:
        mw = pencil.matrix_world.copy(); pencil.parent = None; pencil.matrix_world = mw
    G.remove(["Notebook"])

    import handwriting
    hw_l, hw_r = handwriting.build()
    leather = M.leather()
    made = []
    # cover: two boards + spine, rounded corners
    for side, s in (("L", -1), ("R", 1)):
        b = G.extrude_outline(f"Notebook_Cover{side}", G.rounded_rect(CW, CH, 0.007, 6), 0.0, CT, coll, leather, 0.0011, 3,
                              matrix=Matrix.Translation((s * (CW / 2 + 0.002), 0, 0)))
        made.append(b)
    made.append(G.box("Notebook_Spine", (-0.004, -CH / 2 + 0.001, -0.0004), (0.004, CH / 2 - 0.001, CT * 0.7), coll, leather, 0.0015, 3))
    root = made[1]                                            # right cover = parent of the notebook
    root.name = "Notebook"; root.data.name = "Notebook"
    # page blocks
    edge = M.page_edges()
    left, ztl = _page_block("Notebook_PagesL", "L", coll, M.ruled_paper("R_PageLeft", hw_l), edge)
    right, ztr = _page_block("Notebook_PagesR", "R", coll, M.ruled_paper("R_PageRight", hw_r), edge)
    made += [left, right]
    # ribbon bookmark: lies across the right page from the gutter, hangs over the tail edge
    rib = []                                                   # ribbon: out of the gutter, diagonally across the right page
    for i in range(25):
        t = i / 24
        x = 0.004 + 0.085 * t ** 1.3
        y = CH * 0.40 - (CH * 0.40 + PH / 2) * t
        rib.append(Vector((x, y, ztr(x / PW) + 0.0005)))
    rib += [Vector((0.091, -PH / 2 - 0.004, CT + 0.004)), Vector((0.094, -PH / 2 - 0.012, 0.0012)),
            Vector((0.100, -PH / 2 - 0.030, 0.0007)), Vector((0.110, -PH / 2 - 0.048, 0.0006))]
    bm = bmesh.new()                                           # flat 6 mm satin strip following the path
    pairs = []
    for i, p in enumerate(rib):
        tng = (rib[min(i + 1, len(rib) - 1)] - rib[max(i - 1, 0)]).normalized()
        side = tng.cross(Vector((0, 0, 1))).normalized() * 0.0042
        pairs.append((bm.verts.new(p - side), bm.verts.new(p + side)))
    for (a1, b1), (a2, b2) in zip(pairs, pairs[1:]):
        bm.faces.new([a1, b1, b2, a2])
    r = G.mesh_obj("Notebook_Ribbon", bm, coll, M.satin("#7d1c1d"), smooth=True)
    so = r.modifiers.new("Solidify", 'SOLIDIFY'); so.thickness = 0.0004
    made.append(r)
    # elastic band along the right board's outer edge
    made.append(G.box("Notebook_Elastic", (CW + 0.0005, -CH / 2 - 0.004, CT - 0.0004), (CW + 0.0065, CH / 2 + 0.004, CT + 0.0016),
                      coll, M.flat("#1b1513", "R_Elastic", 0.7), 0.0008, 2))

    for o in made:
        if o.type == 'MESH' and o.modifiers:
            G.apply_modifiers(o)
        if o is not root:
            mw = o.matrix_world.copy(); o.parent = root; o.matrix_world = mw
    root.matrix_world = base_world
    # pencil back on the right page: lower it so it rests on the new sheet surface
    if pencil:
        bpy.context.view_layer.update()
        pts = [pencil.matrix_world @ Vector(cc) for cc in pencil.bound_box]
        pc = sum(pts, Vector()) / 8
        local = base_world.inverted() @ pc
        rest = ztr(max(0.0, min(1.0, local.x / PW))) if local.x > 0 else ztl(max(0.0, min(1.0, -local.x / PW)))
        page_top_world = (base_world @ Vector((local.x, local.y, rest))).z
        dz = page_top_world + 0.0003 - min(p.z for p in pts)
        pencil.matrix_world = Matrix.Translation((0, 0, dz)) @ pencil.matrix_world
        mw = pencil.matrix_world.copy(); pencil.parent = root; pencil.matrix_world = mw
        made.append(pencil)
    return made
