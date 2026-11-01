"""Mesh helpers for the room refresh parts. Everything is real geometry (bevels, profiles, tubes), with
modifiers applied at the end so the lightmap bake and the web export see exactly what the preview shows."""
import bpy, bmesh, math
from mathutils import Vector, Matrix

D = bpy.data


def link(o, coll, mat=None):
    coll.objects.link(o)
    if mat is not None and o.type == 'MESH':
        o.data.materials.append(mat)
    return o


def mesh_obj(name, bm, coll, mat=None, smooth=False):
    me = D.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return link(D.objects.new(name, me), coll, mat)


def box(name, lo, hi, coll, mat=None, bevel=0.0, seg=2, smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]; s = [hi[i] - lo[i] for i in range(3)]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(c) @ Matrix.Diagonal((*s, 1)), verts=bm.verts)
    o = mesh_obj(name, bm, coll, mat, smooth=False)
    if bevel > 0:
        bevel_mod(o, bevel, seg)
        if smooth:
            shade_auto(o)
    return o


def bevel_mod(o, width, seg=2, angle=30):
    m = o.modifiers.new("Bevel", 'BEVEL'); m.width = width; m.segments = seg
    m.limit_method = 'ANGLE'; m.angle_limit = math.radians(angle); m.harden_normals = False
    return m


def shade_auto(o, angle=35):
    for p in o.data.polygons:
        p.use_smooth = True
    try:
        o.data.set_sharp_from_angle(angle=math.radians(angle))
    except Exception:
        pass


def subsurf(o, levels=2):
    m = o.modifiers.new("Subsurf", 'SUBSURF'); m.levels = levels; m.render_levels = levels
    return m


def rounded_rect(w, h, r, n=6):
    """2D outline (counter-clockwise) of a w x h rectangle with corner radius r, centred at 0."""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def extrude_outline(name, pts, z0, z1, coll, mat=None, bevel=0.0, seg=3, matrix=None):
    """Prism from a 2D outline (XY) between z0 and z1, optional bevel on the edges."""
    bm = bmesh.new()
    bot = [bm.verts.new((x, y, z0)) for x, y in pts]
    top = [bm.verts.new((x, y, z1)) for x, y in pts]
    bm.faces.new(list(reversed(bot))); bm.faces.new(top)
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([bot[i], bot[j], top[j], top[i]])
    if matrix is not None:
        bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    o = mesh_obj(name, bm, coll, mat)
    if bevel > 0:
        bevel_mod(o, bevel, seg, angle=40)
    shade_auto(o, 40)
    return o


def tube(name, path, radius, coll, mat=None, ring=16, radius_fn=None, closed_ends=True):
    """Tube along a polyline `path` (list of Vector). radius_fn(t, i) -> radius allows ribs / taper."""
    bm = bmesh.new()
    rings = []
    n = len(path)
    prev_side = None
    for i, p in enumerate(path):
        t = path[min(i + 1, n - 1)] - path[max(i - 1, 0)]
        t.normalize()
        if prev_side is None:
            up = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            side = t.cross(up).normalized()
        else:   # parallel transport keeps the rings from twisting
            side = (prev_side - t * prev_side.dot(t)).normalized()
        prev_side = side
        up2 = side.cross(t).normalized()
        r = radius_fn(i / (n - 1), i) if radius_fn else radius
        rings.append([bm.verts.new(p + (side * math.cos(a) + up2 * math.sin(a)) * r)
                      for a in (2 * math.pi * k / ring for k in range(ring))])
    for i in range(n - 1):
        for k in range(ring):
            k2 = (k + 1) % ring
            bm.faces.new([rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]])
    if closed_ends:
        bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    return mesh_obj(name, bm, coll, mat, smooth=True)


def bezier(p0, p1, p2, p3, n):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append(p0 * u ** 3 + p1 * 3 * u * u * t + p2 * 3 * u * t * t + p3 * t ** 3)
    return out


def lathe(name, profile, coll, mat=None, seg=48, matrix=None, smooth=True, cap=False):
    """Surface of revolution around local Z from profile [(r, z), ...]."""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        if r < 1e-6:
            rings.append([bm.verts.new((0, 0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), z)) for k in range(seg)])
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for k in range(seg):
                bm.faces.new([a[0], b[k], b[(k + 1) % seg]])
        elif len(b) == 1:
            for k in range(seg):
                bm.faces.new([a[k], b[0], a[(k + 1) % seg]])
        else:
            for k in range(seg):
                k2 = (k + 1) % seg
                bm.faces.new([a[k], a[k2], b[k2], b[k]])
    if cap and len(rings[-1]) > 1:
        bm.faces.new(rings[-1])
    if matrix is not None:
        bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    bm.normal_update()
    return mesh_obj(name, bm, coll, mat, smooth=smooth)


def apply_modifiers(o):
    """Bake modifiers into the mesh (bevels, subsurf, solidify)."""
    if not o.modifiers:
        return o
    dg = bpy.context.evaluated_depsgraph_get()
    me = D.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    old = o.data
    o.modifiers.clear(); o.data = me
    if old.users == 0:
        D.meshes.remove(old)
    return o


def place(objs, matrix):
    """Apply a world transform to freshly built objects (built around the origin)."""
    for o in objs:
        if o.parent is None:
            o.matrix_world = matrix @ o.matrix_world


def text(name, body, size, coll, mat, align='CENTER', extrude=0.0):
    cu = D.curves.new(name, 'FONT'); cu.body = body; cu.size = size
    cu.align_x = align; cu.align_y = 'CENTER'; cu.extrude = extrude
    o = D.objects.new(name, cu); link(o, coll)
    o.data.materials.append(mat)
    return o


def remove(names):
    gone = 0
    for n in names:
        o = D.objects.get(n)
        if o is None:
            continue
        for c in list(o.children_recursive):
            D.objects.remove(c, do_unlink=True); gone += 1
        D.objects.remove(o, do_unlink=True); gone += 1
    return gone
