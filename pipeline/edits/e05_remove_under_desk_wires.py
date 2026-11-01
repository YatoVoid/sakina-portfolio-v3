"""Edit #5 (user request 2026-11-01): "remove the wires, they are overlapping, from underneath the desk only".

Four cables run from the equipment on the desk over the back edge and hang down to the floor / wall socket, in front of
the new radiator when seen from under the desk: Cable_Left, Cable_Power, Wire_CRT_Power, Wire_VCR_Power.
Each curve is cut at desk-top height: every control point below Z_CUT (world z) is dropped, the part on and above the
desk is kept exactly as it was (shape, thickness, material). Nothing else is touched (Cable_VCR, Wire_Coax, Wire_Video,
the phone cord, the other desks' cables and the wall sockets stay).
"""
import bpy
from mathutils import Vector

Z_CUT = 0.70                      # desk top is z 0.68-0.72; below this a wire is "underneath the desk"
WIRES = ("Cable_Left", "Cable_Power", "Wire_CRT_Power", "Wire_VCR_Power")


def apply():
    D = bpy.data
    for name in WIRES:
        o = D.objects.get(name)
        if o is None or o.type != 'CURVE':
            print("e05: missing", name, flush=True); continue
        cu = o.data
        for sp in list(cu.splines):
            if sp.type != 'BEZIER':
                print("e05: skip non-bezier spline in", name, flush=True); continue
            pts = [(Vector(p.co), Vector(p.handle_left), Vector(p.handle_right)) for p in sp.bezier_points]
            keep = [p for p in pts if (o.matrix_world @ p[0]).z >= Z_CUT]
            if len(keep) == len(pts):
                continue
            res_u, cyc = sp.resolution_u, sp.use_cyclic_u
            cu.splines.remove(sp)
            if len(keep) < 2:
                print("e05: removed whole wire", name, flush=True); continue
            ns = cu.splines.new('BEZIER')
            ns.bezier_points.add(len(keep) - 1)
            ns.resolution_u = res_u; ns.use_cyclic_u = cyc
            for bp, (co, hl, hr) in zip(ns.bezier_points, keep):
                bp.handle_left_type = bp.handle_right_type = 'FREE'
                bp.co = co; bp.handle_left = hl; bp.handle_right = hr
            last = ns.bezier_points[-1]
            last.handle_right = last.co          # clean end at desk-top height
            print("e05:", name, "kept", len(keep), "of", len(pts), "points", flush=True)
