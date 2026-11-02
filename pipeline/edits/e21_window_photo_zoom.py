"""Edit #21 (round 5d, Sakina approved the preview): enlarge the Berlin photo patch in angle space about the horizon / vanishing point.

Same maths as pipeline/tools/zoom_view_photo.mjs (three.js side). Blender world = (x, y, z) with y = -three z. The patch sits on an
80 m cylinder around the hero eye; a bigger angular size means steep camera angles still see real photo (no invented extension).
Zoom factor: env V3_VIEW_ZOOM (default 5.2).
"""
import bpy, math, os

C = (-0.02, 1.12, -0.25)          # hero eye, three.js
S = float(os.environ.get("V3_VIEW_ZOOM", "1.3"))
ANCHOR_PX = float(os.environ.get("V3_VIEW_ANCHOR_PX", "1680"))   # photo column kept in place = the METRO sign
TH0 = math.radians(-2.5) + math.atan((ANCHOR_PX - 1288) / 3200)
H0 = 79.75 * math.tan(math.radians(4))


def apply():
    o = bpy.data.objects.get("WindowView_Photo")
    if o is None:
        print("e21: no WindowView_Photo, skipped", flush=True); return
    me = o.data
    mw = o.matrix_world
    inv = mw.inverted()
    for v in me.vertices:
        w = mw @ v.co                                   # Blender world
        xv, yv = w.x - C[0], w.z - C[1]                 # view space: right, up
        zv = w.y + C[2]                                 # forward (three -z = Blender +y): blender y - 0.25
        r, th = math.hypot(xv, zv), math.atan2(xv, zv)
        th2, y2 = TH0 + S * (th - TH0), H0 + S * (yv - H0)
        nw = type(w)((C[0] + r * math.sin(th2), -C[2] + r * math.cos(th2), C[1] + y2))
        v.co = inv @ nw
    me.update()
    print(f"e21: WindowView_Photo zoomed x{S}", flush=True)
