"""Edit #14 (Sakina request 2026-11-01): the window becomes a deep, recessed double casement (two sashes in a box).

Reference (top-down phone shot): the window sits well back in the wall. You see the thick reveal (the painted
lining of the opening) and the sill ledge, and two separate sashes with their own chunky frames meeting in the middle.

Before: everything (frame, mullion, beads, glass) lived in 9 cm around the wall's inner face; the sashes were flat strips.
After (Blender coords, wall inner face y = 2.5, outer face y = 2.6, opening x -0.73..0.52, z 0.90..2.30):
  - Window_Casing   : 2.5 cm proud interior trim around the opening (kept at the old 5 cm width, same top/left/right)
  - Window_Reveal   : 2 cm paint-grade lining of the opening that runs from the wall face to y = 2.74 (24 cm deep box);
                      the bottom board (4 cm) continues the existing sill into the reveal
  - Window_Frame    : fixed outer frame ring (3 cm wide, 8 cm deep) at y 2.60..2.68
  - Sash_L, Sash_R  : two casement sashes (5 cm stiles, 5.5 cm top rail, 7.5 cm bottom rail, 5 cm transom at the old
                      height z 1.405..1.455, 12 mm glazing beads on the room side), 4 mm gap between them,
                      sash front face y = 2.615 = 11.5 cm behind the wall face
  - Glass / RainLines: same objects, re-fitted to the new opening and moved back to y = 2.640
  - Handle_*        : same brass handle, moved onto the right sash's meeting stile (it used to float 4 cm off the old mullion)
Removed: Frame_*, Mullion_V/H, Bead_* (rebuilt as above). Kept: Sill, Sill_Lip, Glass, RainLines, Handle_*.
Material for all new wood: `WindowPaint` (object-space procedural, no UVs needed). No lights are touched; the window area
light `L4_Window_Night` sits at y = 3.05, outside the 2.74 m reveal.
"""
import bpy, bmesh
from mathutils import Vector

WALL_IN, REVEAL_END = 2.50, 2.74
OPEN_X0, OPEN_X1, OPEN_Z0, OPEN_Z1 = -0.73, 0.52, 0.90, 2.30
LINER = 0.02
FR = 0.03                                    # fixed frame ring width
SASH_Y0, SASH_Y1 = 2.615, 2.660
GLASS_Y = 2.640
STILE, RAIL_T, RAIL_B, TRANSOM = 0.05, 0.055, 0.075, 0.05
TRANSOM_Z0 = 1.405
BEAD_W, BEAD_D = 0.012, 0.010
GAP = 0.004
OLD_PREFIX = ("Frame_", "Mullion_", "Bead_")


def _box(bm, x0, x1, y0, y1, z0, z1, bevel=0.001):
    v = {}
    for i, x in enumerate((x0, x1)):
        for j, y in enumerate((y0, y1)):
            for k, z in enumerate((z0, z1)):
                v[i, j, k] = bm.verts.new((x, y, z))
    q = lambda *c: bm.faces.new([v[i] for i in c])
    f = [q((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)), q((1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0)),
         q((0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, 0)), q((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)),
         q((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), q((0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1))]
    bmesh.ops.recalc_face_normals(bm, faces=f)
    if bevel:
        bmesh.ops.bevel(bm, geom=list({e for fc in f for e in fc.edges}), offset=bevel, segments=1, affect='EDGES')


def _object(name, boxes, mat, coll):
    bm = bmesh.new()
    for b in boxes:
        _box(bm, *b)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    return o


def _sash(x0, x1):
    """Boxes of one casement sash occupying x0..x1 (z from the fixed frame's inner edge)."""
    z0, z1 = OPEN_Z0 + LINER + FR, OPEN_Z1 - LINER - FR
    y0, y1 = SASH_Y0, SASH_Y1
    b = [(x0, x0 + STILE, y0, y1, z0, z1), (x1 - STILE, x1, y0, y1, z0, z1),                       # stiles
         (x0 + STILE, x1 - STILE, y0, y1, z0, z0 + RAIL_B), (x0 + STILE, x1 - STILE, y0, y1, z1 - RAIL_T, z1),
         (x0 + STILE, x1 - STILE, y0, y1, TRANSOM_Z0, TRANSOM_Z0 + TRANSOM)]
    panes = [(z0 + RAIL_B, TRANSOM_Z0), (TRANSOM_Z0 + TRANSOM, z1 - RAIL_T)]
    ix0, ix1 = x0 + STILE, x1 - STILE
    for pz0, pz1 in panes:                                                                           # room-side glazing beads
        by0, by1 = y0 - BEAD_D, y0
        b += [(ix0, ix1, by0, by1, pz0, pz0 + BEAD_W), (ix0, ix1, by0, by1, pz1 - BEAD_W, pz1),
              (ix0, ix0 + BEAD_W, by0, by1, pz0 + BEAD_W, pz1 - BEAD_W),
              (ix1 - BEAD_W, ix1, by0, by1, pz0 + BEAD_W, pz1 - BEAD_W)]
    return b


def apply():
    D = bpy.data
    win = D.collections["Window"]
    paint = D.materials["WindowPaint"]
    old = [o for o in win.objects if o.name.startswith(OLD_PREFIX)]
    assert len(old) == 3 + 2 + 16 - 0 or len(old) == 21, f"unexpected old window parts: {len(old)}"
    for n in ("Sill", "Sill_Lip", "Glass", "RainLines", "Handle_Plate", "Handle_Lever"):
        assert n in win.objects, n
    glass = D.objects["Glass"]
    gx = glass.location.x
    assert abs(gx + 0.105) < 1e-6 and abs(glass.location.y - 2.545) < 1e-6, "glass moved; re-check e14"
    meshes = {o.data for o in old}
    for o in old:
        D.objects.remove(o, do_unlink=True)
    for m in meshes:
        if m.users == 0:
            D.meshes.remove(m)

    cx = (OPEN_X0 + OPEN_X1) / 2                                   # -0.105
    fx0, fx1 = OPEN_X0 + LINER + FR, OPEN_X1 - LINER - FR          # clear width for the sashes
    fz0, fz1 = OPEN_Z0 + LINER + FR, OPEN_Z1 - LINER - FR
    # interior casing (proud of the wall)
    cy0, cy1 = WALL_IN - 0.025, WALL_IN
    casing = [(-0.78, 0.57, cy0, cy1, 2.30, 2.35), (-0.78, OPEN_X0, cy0, cy1, OPEN_Z0, 2.30), (OPEN_X1, 0.57, cy0, cy1, OPEN_Z0, 2.30)]
    # reveal lining
    rv = [(OPEN_X0, OPEN_X0 + LINER, WALL_IN, REVEAL_END, OPEN_Z0, OPEN_Z1),
          (OPEN_X1 - LINER, OPEN_X1, WALL_IN, REVEAL_END, OPEN_Z0, OPEN_Z1),
          (OPEN_X0 + LINER, OPEN_X1 - LINER, WALL_IN, REVEAL_END, OPEN_Z1 - LINER, OPEN_Z1),
          (OPEN_X0 + LINER, OPEN_X1 - LINER, WALL_IN, REVEAL_END, OPEN_Z0 - 0.038, OPEN_Z0 + LINER)]
    # fixed frame ring
    fy0, fy1 = 2.600, 2.680
    ix0, ix1, iz0, iz1 = OPEN_X0 + LINER, OPEN_X1 - LINER, OPEN_Z0 + LINER, OPEN_Z1 - LINER
    frame = [(ix0, ix0 + FR, fy0, fy1, iz0, iz1), (ix1 - FR, ix1, fy0, fy1, iz0, iz1),
             (ix0 + FR, ix1 - FR, fy0, fy1, iz0, iz0 + FR), (ix0 + FR, ix1 - FR, fy0, fy1, iz1 - FR, iz1)]
    _object("Window_Casing", casing, paint, win)
    _object("Window_Reveal", rv, paint, win)
    _object("Window_Frame", frame, paint, win)
    _object("Sash_L", _sash(fx0, cx - GAP / 2), paint, win)
    _object("Sash_R", _sash(cx + GAP / 2, fx1), paint, win)

    # glass + rain lines: refit to the clear opening, move back into the sash rebate
    sx, sz = (fx1 - fx0) / 1.25, (fz1 - fz0) / 1.40
    zc_new = (fz0 + fz1) / 2
    glass.scale = (sx, 1.0, sz)
    glass.location = (cx, GLASS_Y, zc_new)
    rain = D.objects["RainLines"]
    for v in rain.data.vertices:
        v.co.x = cx + (v.co.x - cx) * sx
        v.co.z = zc_new + (v.co.z - 1.6) * sz
        v.co.y += GLASS_Y - 0.001 - 2.542
    # handle on the right sash's meeting stile (stile front face y = SASH_Y0)
    for n in ("Handle_Plate", "Handle_Lever"):
        D.objects[n].location.y += (SASH_Y0 - 0.006) - 2.442
    bpy.context.view_layer.update()
    print("e14: window rebuilt as recessed double casement: reveal to y", REVEAL_END, "sashes at y", SASH_Y0, "-", SASH_Y1, flush=True)
