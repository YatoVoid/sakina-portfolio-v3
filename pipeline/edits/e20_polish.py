"""Edit #20 (2026-11-01, "improve anything which is bad before baking"): three small corrections found while combining the branches.

  1. Gallery wall (8 photos + ledge, `Gallery_*`) was centred for the narrow cabinet; the cabinet was widened 30 cm by e15, so it sat 19 cm
     off-centre. It is now centred on the cabinet (`Cabinet_Body`).
  2. Standing lamp (`SLamp_*` + its light): the pole stood 2 cm from the armchair's scroll arm and the shade read as "in front of the chair".
     Moved 30 cm along the wall (+y), away from the chair, clear of the carton.
  3. (floor) the darkest weathered boards were near-black in the shadow: lightened in e09_floor.py (not here).
"""
import bpy
from mathutils import Vector


def _bb(o):
    ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [min(w[i] for w in ws) for i in range(3)], [max(w[i] for w in ws) for i in range(3)]


def _move(o, dx=0.0, dy=0.0):
    m = o.matrix_world.copy()
    m.translation += Vector((dx, dy, 0.0))
    o.matrix_world = m


def apply():
    D = bpy.data
    cab = D.objects["Cabinet_Body"]
    lo, hi = _bb(cab)
    cab_c = (lo[1] + hi[1]) / 2
    gal = [o for o in D.objects if o.name.startswith("Gallery") and o.parent is None]
    glo = min(_bb(o)[0][1] for o in gal)
    ghi = max(_bb(o)[1][1] for o in gal)
    dy = cab_c - (glo + ghi) / 2
    for o in gal:
        _move(o, dy=dy)
    print(f"e20: gallery ({len(gal)} objects) centred on the cabinet: moved {dy:+.2f} m (cabinet centre y {cab_c:.2f})", flush=True)

    pole = D.objects["SLamp_Pole"]
    plo, phi = _bb(pole)
    px, py = (plo[0] + phi[0]) / 2, (plo[1] + phi[1]) / 2
    parts = [o for o in D.objects if o.name.startswith("SLamp_") and o.parent is None]
    lights = [o for o in D.objects if o.type == 'LIGHT' and abs(o.matrix_world.translation.x - px) < 0.35 and abs(o.matrix_world.translation.y - py) < 0.35]
    for o in parts + lights:
        _move(o, dy=0.30)
    print(f"e20: standing lamp moved +0.30 y ({len(parts)} parts, {len(lights)} light(s): {[l.name for l in lights]})", flush=True)
