"""Edit #3 (user, 2026-10-31): IBM corner.

a) Slide the IBM desk/cabinet, the computer, the postcards and clock above it along the left wall toward the
   window wall (user: "slide IBM desk to corner"). The screen light, wall socket and the station's cables move
   with it so nothing is left behind. DY = 0.70 m keeps the postcard collage 6 cm from the back wall.
b) Rebuild the computer from the reference photo (IBM PC/AT-style): flat system unit with floppy drive, vented bay,
   keylock and red power switch; beige monitor on a swivel base with recessed dark screen and IBM badge; separate
   Model M keyboard in front with a coiled cord. The old keyboard intersected the system unit (cabinet too shallow
   for both); the new parts fit fully on the 48 cm cabinet: unit 27 cm + 1 cm gap + keyboard 19 cm.
   The existing green terminal text (Term_*) stays on the new screen. The polaroid taped to the old monitor is removed
   (not in the reference).
Front of the computer faces +X (into the room). Viewer's left = -Y.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

DY = 0.70
MOVE = ["Station_Root", "Socket_Left", "Socket_LeftPlug", "Wire_PC_Power", "Wire_CRT2_Power", "Wire_PC_Monitor",
        "Wire_PC_Keyboard", "L5_IBM_Screen"]
MOVE_PREFIX_WALL = ("Postcard", "Clock")           # Wall_Decor collection


def _mat(name, rgb, rough=0.45, emit=None, strength=0.0, bump=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (*rgb, 1); bs.inputs["Roughness"].default_value = rough
    if emit:
        bs.inputs["Emission Color"].default_value = (*emit, 1); bs.inputs["Emission Strength"].default_value = strength
    if bump:
        tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 900.0; bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
    return m


def _srgb(h):
    h = h.lstrip("#"); out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


class Builder:
    def __init__(self, coll, parent):
        self.coll, self.parent, self.objs = coll, parent, []

    def box(self, name, mn, mx, mat, bevel=0.0, seg=2):
        me = bpy.data.meshes.new(name); bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(name, me); self.coll.objects.link(o)
        o.location = [(a + b) / 2 for a, b in zip(mn, mx)]
        o.scale = [b - a for a, b in zip(mn, mx)]
        o.data.materials.append(mat)
        if bevel:
            bpy.context.view_layer.update()
            me.transform(Matrix.Diagonal((*o.scale, 1))); o.scale = (1, 1, 1)
            mod = o.modifiers.new("Bevel", 'BEVEL'); mod.width = bevel; mod.segments = seg; mod.limit_method = 'ANGLE'
        self.objs.append(o)
        return o

    def mesh(self, name, verts, faces, mat):
        me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
        o = bpy.data.objects.new(name, me); self.coll.objects.link(o); o.data.materials.append(mat)
        self.objs.append(o)
        return o

    def cyl(self, name, centre, r, depth, axis, mat, verts=24):
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=centre)
        o = bpy.context.active_object; o.name = name
        if axis == 'X':
            o.rotation_euler = (0, math.pi / 2, 0)
        for c in o.users_collection:
            c.objects.unlink(o)
        self.coll.objects.link(o); o.data.materials.append(mat); self.objs.append(o)
        return o

    def finish(self):
        bpy.context.view_layer.update()
        for o in self.objs:
            mw = o.matrix_world.copy(); o.parent = self.parent; o.matrix_world = mw


def _slide():
    D = bpy.data
    for n in MOVE:
        D.objects[n].location.y += DY
    for o in D.collections["Wall_Decor"].all_objects:
        if o.parent is None and o.name.startswith(MOVE_PREFIX_WALL):
            o.location.y += DY
    bpy.context.view_layer.update()


def _rebuild():
    D = bpy.data
    root = D.objects["Station_Root"]
    coll = D.collections["Station"]
    screen_mat = D.objects["CRT2_Screen"].material_slots[0].material if D.objects.get("CRT2_Screen") else None
    term = [o for o in root.children_recursive if o.name.startswith("Term")]
    tb = [o.matrix_world @ Vector(c) for o in term for c in o.bound_box]
    sy = (min(v.y for v in tb) + max(v.y for v in tb)) / 2
    sz = (min(v.z for v in tb) + max(v.z for v in tb)) / 2
    for o in list(root.children_recursive):
        if o.name.startswith(("PC", "KB", "Keyboard2", "CRT2", "Pin")):   # Polaroid kept: e04 sticks it on the new monitor
            D.objects.remove(o, do_unlink=True)
    cab = D.objects["Cabinet_Top"]
    cb = [cab.matrix_world @ Vector(c) for c in cab.bound_box]
    top, front = max(v.z for v in cb), max(v.x for v in cb)
    cy = (min(v.y for v in cb) + max(v.y for v in cb)) / 2

    beige = _mat("IBMBeige", _srgb("cfc7b2"), 0.5, bump=0.04)
    beige2 = _mat("IBMBeigeDark", _srgb("b7af9b"), 0.55)
    keyl = _mat("IBMKeyLight", _srgb("d9d2c0"), 0.5)
    keyd = _mat("IBMKeyDark", _srgb("8d8b84"), 0.5)
    black = _mat("IBMBlack", _srgb("1b1a19"), 0.6)
    red = _mat("IBMRed", _srgb("c2301f"), 0.4)
    badge = _mat("IBMBadge", _srgb("2b3a66"), 0.35)
    led = _mat("IBMLed", _srgb("6be36b"), 0.3, emit=_srgb("6be36b"), strength=2.0)
    # Dark green-black CRT glass with a faint phosphor glow (the old screen material needs UVs this glass does not have).
    glass = _mat("IBMScreen", (0.006, 0.014, 0.010), 0.30, emit=(0.010, 0.045, 0.022), strength=1.0)
    glass.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.25
    B = Builder(coll, root)

    # --- system unit -------------------------------------------------------------------------------------------
    ux0, ux1 = -2.99, -2.72                      # back, front (x)
    uy0, uy1 = cy - 0.25, cy + 0.25
    uz0, uz1 = top, top + 0.12
    B.box("IBM_Unit", (ux0, uy0, uz0), (ux1, uy1, uz1), beige, bevel=0.006)
    B.box("IBM_Unit_Groove", (ux1 - 0.001, uy0 + 0.01, uz0 + 0.024), (ux1 + 0.0005, uy1 - 0.01, uz0 + 0.026), beige2)
    fz = uz0 + 0.06                              # front panel centre height
    B.cyl("IBM_Unit_Badge", (ux1 + 0.002, uy0 + 0.035, fz), 0.017, 0.004, 'X', badge)
    B.box("IBM_Floppy_Bay", (ux1 - 0.002, uy0 + 0.075, fz - 0.025), (ux1 + 0.002, uy0 + 0.225, fz + 0.022), beige2, bevel=0.002)
    B.box("IBM_Floppy_Slot", (ux1 + 0.0015, uy0 + 0.09, fz - 0.002), (ux1 + 0.0035, uy0 + 0.20, fz + 0.004), black)
    B.box("IBM_Floppy_Latch", (ux1 + 0.002, uy0 + 0.205, fz - 0.012), (ux1 + 0.009, uy0 + 0.215, fz + 0.012), beige, bevel=0.001)
    B.box("IBM_Bay2", (ux1 - 0.002, uy0 + 0.235, fz - 0.025), (ux1 + 0.002, uy0 + 0.385, fz + 0.022), beige2, bevel=0.002)
    for i in range(7):
        z = fz - 0.018 + i * 0.006
        B.box(f"IBM_Bay2_Vent_{i}", (ux1 + 0.0018, uy0 + 0.25, z), (ux1 + 0.0028, uy0 + 0.37, z + 0.002), black)
    B.cyl("IBM_Keylock", (ux1 + 0.003, uy0 + 0.41, fz + 0.012), 0.007, 0.006, 'X', beige2)
    B.box("IBM_PowerSwitch", (ux1 + 0.0, uy1 - 0.055, fz - 0.016), (ux1 + 0.010, uy1 - 0.03, fz + 0.016), red, bevel=0.002)

    # --- monitor on swivel base --------------------------------------------------------------------------------
    B.box("IBM_Mon_Base", (-2.93, sy - 0.11, uz1), (-2.76, sy + 0.11, uz1 + 0.012), beige, bevel=0.005)
    B.box("IBM_Mon_Neck", (-2.89, sy - 0.07, uz1 + 0.012), (-2.80, sy + 0.07, uz1 + 0.034), beige2, bevel=0.004)
    bz0 = uz1 + 0.034
    hw, hh = 0.18, 0.16                          # bezel half-width / half-height
    zc = max(sz, bz0 + hh)                       # keep the bezel on the neck
    bx1, bx0 = -2.690, -2.722                    # bezel front / back
    sw, sh = 0.150, 0.110                        # screen opening half sizes
    # bezel as a frame around the screen opening
    B.box("IBM_Bezel_T", (bx0, sy - hw, zc + sh), (bx1, sy + hw, zc + hh), beige, bevel=0.006)
    B.box("IBM_Bezel_B", (bx0, sy - hw, zc - hh), (bx1, sy + hw, zc - sh), beige, bevel=0.006)
    B.box("IBM_Bezel_L", (bx0, sy - hw, zc - sh), (bx1, sy - sw, zc + sh), beige, bevel=0.004)
    B.box("IBM_Bezel_R", (bx0, sy + sw, zc - sh), (bx1, sy + hw, zc + sh), beige, bevel=0.004)
    # inner lip sits BEHIND the glass (a solid lip in front hid the screen in the first render)
    B.box("IBM_Bezel_Lip", (bx0 - 0.004, sy - sw - 0.006, zc - sh - 0.006), (bx1 - 0.0125, sy + sw + 0.006, zc + sh + 0.006), beige2)
    # slightly curved CRT glass, recessed 1 cm
    verts, faces, nu, nv = [], [], 16, 12
    for i in range(nu + 1):
        for j in range(nv + 1):
            u, v = -1 + 2 * i / nu, -1 + 2 * j / nv
            verts.append((bx1 - 0.010 + 0.005 * (1 - u * u) * (1 - v * v), sy + u * sw, zc + v * sh))
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j
            faces.append((a, a + nv + 1, a + nv + 2, a + 1))
    B.mesh("IBM_Screen", verts, faces, glass)
    B.box("IBM_Mon_Back", (-2.94, sy - 0.15, zc - 0.13), (bx0, sy + 0.15, zc + 0.135), beige, bevel=0.02, seg=3)
    B.box("IBM_Mon_Back2", (-2.985, sy - 0.10, zc - 0.09), (-2.94, sy + 0.10, zc + 0.09), beige2, bevel=0.012, seg=3)
    B.box("IBM_Mon_Badge", (bx1, sy - hw + 0.02, zc + hh - 0.03), (bx1 + 0.002, sy - hw + 0.055, zc + hh - 0.018), badge)
    B.box("IBM_Mon_Led", (bx1, sy + hw - 0.03, zc - hh + 0.012), (bx1 + 0.002, sy + hw - 0.022, zc - hh + 0.02), led)
    for o in [o for o in root.children_recursive if o.name.startswith("Term")]:   # terminal text onto the glass
        mw = o.matrix_world.copy(); mw.translation.x = bx1 - 0.0045; o.matrix_world = mw

    # --- Model M keyboard --------------------------------------------------------------------------------------
    kx_front, kx_back = front - 0.004, front - 0.194
    ky0 = cy - 0.23; ky1 = cy + 0.23
    zb, zf = top + 0.045, top + 0.025           # case top height at back / front (slope)
    case_top = lambda x: zf + (zb - zf) * (kx_front - x) / (kx_front - kx_back)
    cv = [(kx_back, ky0, top), (kx_front, ky0, top), (kx_front, ky1, top), (kx_back, ky1, top),
          (kx_back, ky0, zb), (kx_front, ky0, zf), (kx_front, ky1, zf), (kx_back, ky1, zb)]
    cf = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    case = B.mesh("IBM_KB_Case", cv, cf, beige)
    m = case.modifiers.new("Bevel", 'BEVEL'); m.width = 0.004; m.segments = 2
    B.box("IBM_KB_Badge", (kx_back + 0.006, ky0 + 0.012, zb - 0.0005), (kx_back + 0.016, ky0 + 0.045, zb + 0.001), badge)
    U, gap = 0.0188, 0.0016
    rows_x = [kx_front - 0.020 - r * U for r in range(5)] + [kx_front - 0.020 - 5 * U - 0.010]   # 0 = space row ... 5 = F row
    light, dark = [], []

    def key(row, y_left, w_units, dark_key=False, h_units=1):
        x = rows_x[row]; w = w_units * U - gap; d = h_units * U - gap
        xc = x + (h_units - 1) * U / 2                      # tall keys extend toward the front row
        z0 = case_top(xc); h = 0.010
        (dark if dark_key else light).append(((xc - d / 2, y_left + gap / 2, z0), (xc + d / 2, y_left + gap / 2 + w, z0 + h)))

    y = ky0 + 0.012
    main = [  # row: [(units, dark), ...] left -> right
        [(1.5, 1), (1, None), (1.5, 1), (7, 0), (1.5, 1), (1, None), (1.5, 1)],
        [(2.25, 1)] + [(1, 0)] * 10 + [(2.75, 1)],
        [(1.75, 1)] + [(1, 0)] * 11 + [(2.25, 1)],
        [(1.5, 1)] + [(1, 0)] * 12 + [(1.5, 1)],
        [(1, 0)] * 13 + [(2, 1)],
        [(1, 1), (1, None)] + [(1, 1)] * 4 + [(0.5, None)] + [(1, 1)] * 4 + [(0.5, None)] + [(1, 1)] * 4,
    ]
    for r, row in enumerate(main):
        yy = y
        for units, dk in row:
            if dk is not None:
                key(r, yy, units, bool(dk))
            yy += units * U
    nav_y = y + 15 * U + 0.009
    for r, cols in {5: [0, 1, 2], 4: [0, 1, 2], 3: [0, 1, 2], 1: [1], 0: [0, 1, 2]}.items():
        for c in cols:
            key(r, nav_y + c * U, 1, True)
    num_y = nav_y + 3 * U + 0.009
    for r, cols in {4: [0, 1, 2, 3], 3: [0, 1, 2], 2: [0, 1, 2], 1: [0, 1, 2]}.items():
        for c in cols:
            key(r, num_y + c * U, 1, r == 4)
    key(0, num_y, 2, False); key(0, num_y + 2 * U, 1, False)
    key(3, num_y + 3 * U, 1, True, h_units=2)                        # numpad +  (rows 3-2)
    key(1, num_y + 3 * U, 1, True, h_units=2)                        # numpad Enter (rows 1-0)
    for i in range(3):                                               # lock LEDs above the numpad
        B.box(f"IBM_KB_Led_{i}", (rows_x[5] - 0.004, num_y + 0.012 + i * 0.02, case_top(rows_x[5]) - 0.0005),
              (rows_x[5] + 0.004, num_y + 0.018 + i * 0.02, case_top(rows_x[5]) + 0.001), led)

    def keys_mesh(name, boxes, mat):
        verts, faces = [], []
        for (x0, y0, z0), (x1, y1, z1) in boxes:
            i = len(verts); t = 0.0022                               # tapered key cap
            verts += [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                      (x0 + t, y0 + t, z1), (x1 - t, y0 + t, z1 - 0.002), (x1 - t, y1 - t, z1 - 0.002), (x0 + t, y1 - t, z1)]
            faces += [(i + 4, i + 5, i + 6, i + 7), (i, i + 1, i + 5, i + 4), (i + 1, i + 2, i + 6, i + 5),
                      (i + 2, i + 3, i + 7, i + 6), (i + 3, i, i + 4, i + 7)]
        return B.mesh(name, verts, faces, mat)
    keys_mesh("IBM_KB_KeysLight", light, keyl)
    keys_mesh("IBM_KB_KeysDark", dark, keyd)

    # coiled cord from the keyboard's left side to the unit
    p0, p1 = Vector((kx_back + 0.03, ky0 - 0.004, top + 0.012)), Vector((ux1 - 0.10, uy0 - 0.012, top + 0.03))
    cu = bpy.data.curves.new("IBM_KB_Cord", 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.0016; cu.resolution_u = 2
    sp = cu.splines.new('POLY'); n = 120; sp.points.add(n - 1)
    axis = (p1 - p0); side = Vector((0, 0, 1)).cross(axis.normalized()); up = axis.normalized().cross(side)
    for i, p in enumerate(sp.points):
        t = i / (n - 1); a = t * 2 * math.pi * 16
        q = p0 + axis * t + side * 0.005 * math.cos(a) + up * 0.005 * math.sin(a)
        p.co = (q.x, q.y, q.z, 1)
    co = bpy.data.objects.new("IBM_KB_Cord", cu); co.data.materials.append(black); coll.objects.link(co); B.objs.append(co)

    B.finish()
    # screen light: centred on the new glass, just in front of it
    lt = D.objects["L5_IBM_Screen"]; lt.location = (bx1 + 0.10, sy, zc - 0.12)   # below centre: no hotspot reflected in the glass
    print("IBM rebuilt: objects", len(B.objs), "keys", len(light) + len(dark))


def apply():
    _slide()
    _rebuild()
