"""Shared geometry for the window view: how the photo is placed around the viewer.

Frame used here ("view space"): x = right, y = up, z = forward = into the window (three.js -Z, Blender +Y).
Origin = CENTRE, the round-3 hero camera eye (three.js (-0.02, 1.12, -0.25)), so the opening shot sees the
photo with no distortion. Other viewpoints see slight, natural parallax because the backdrop is 80 m away.

Photo analysis (refs/berlin-railyard-night.jpg, 2576 x 1718):
- certain:  the rails converge at about (1080, 960) -> the photographer's eye level (horizon) is row 960.
- measured: rail gauge 1.435 m spans 232 px at the bottom row (758 px below the horizon) -> the photo was
            taken ~4.7 m above the tracks (a footbridge).
- chosen:   focal length 3200 px (43.8 deg across the photo). This frames the Mercedes-Benz Arena building
            (left) to the TV tower (right) inside the window as seen from the opening camera.
- chosen:   LIFT = 4 deg: the photo's horizon sits 4 deg above the camera's eye, i.e. just above the CRT,
            so the lit skyline shows behind the monitor instead of being hidden by it.
"""
import math

PHOTO_W, PHOTO_H = 2576, 1718
CX, CY = PHOTO_W / 2, PHOTO_H / 2
HORIZON_ROW = 960
F_PX = 3200.0
YAW_DEG = -2.5            # photo centre direction, + = right. Window centre from the hero camera is -2 deg.
LIFT_DEG = 4.0

CENTRE_THREE = (-0.02, 1.12, -0.25)
RADIUS = 80.0             # backdrop distance, metres
PATCH_RADIUS = RADIUS - 0.25   # native-resolution photo sits just in front of the extension panorama

# Extension panorama coverage (cylindrical: u linear in yaw, v linear in tan(pitch)).
PANO_YAW = (-85.0, 85.0)
PANO_PITCH = (-55.0, 50.0)
PANO_SIZE = (2048, 1024)

ALPHA = math.atan((HORIZON_ROW - CY) / F_PX)          # camera pitch in the original photo (looked slightly up)
PITCH = ALPHA + math.radians(LIFT_DEG)
YAW = math.radians(YAW_DEG)


def basis():
    st, ct, sp, cp = math.sin(YAW), math.cos(YAW), math.sin(PITCH), math.cos(PITCH)
    fwd = (st * cp, sp, ct * cp)
    right = (ct, 0.0, -st)
    up = (-st * sp, cp, -ct * sp)
    return right, up, fwd


def photo_dir(px, py):
    """Direction (view space, not normalised) of photo pixel (px, py)."""
    r, u, f = basis()
    a, b = (px - CX) / F_PX, -(py - CY) / F_PX
    return tuple(a * r[i] + b * u[i] + f[i] for i in range(3))


def on_cylinder(d, radius):
    h = math.hypot(d[0], d[2])
    k = radius / h
    return (d[0] * k, d[1] * k, d[2] * k)


def view_to_blender(p):
    """view (right, up, forward) -> Blender world (x, y, z), including the CENTRE offset."""
    cx, cy, cz = CENTRE_THREE          # three (x, y, z) -> Blender (x, -z, y)
    return (p[0] + cx, p[2] - cz, p[1] + cy)
