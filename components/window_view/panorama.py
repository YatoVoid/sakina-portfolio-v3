"""Build the low-resolution extension panorama that surrounds the native photo.

Inside the photo's frame the panorama holds a downsampled copy of the photo (hidden behind the native patch;
it only guarantees a seamless edge). Outside the frame the city continues as a mirrored, progressively
blurred and darkened copy of the nearest photo edge; above the photo the sky gradient continues upward.
Film grain matching the photo is added so the transition is not a smooth smear.

    python3 components/window_view/panorama.py   -> components/window_view/export/window_view_pano.jpg
"""
import math, os, sys
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import view as V  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DS = 2                                   # work on a half-resolution copy (the extension is blurred anyway)
BLUR_SIGMAS = [0.8, 5, 14, 34]           # half-res px
BLUR_STEP = 260.0                        # full-res px outside the frame per blur level
GRAIN_STD = 3.2                          # 8-bit units, measured sky noise is ~5-7 at full res


def build(seed=7):
    photo = Image.open(os.path.join(HERE, "refs", "berlin-railyard-night.jpg")).convert("RGB")
    assert photo.size == (V.PHOTO_W, V.PHOTO_H), photo.size
    small = np.asarray(photo.resize((V.PHOTO_W // DS, V.PHOTO_H // DS), Image.LANCZOS)).astype(np.float32) / 255.0
    lin = np.where(small <= 0.04045, small / 12.92, ((small + 0.055) / 1.055) ** 2.4)   # blur in linear light
    levels = [np.stack([gaussian_filter(lin[..., c], s, mode="mirror") for c in range(3)], -1) for s in BLUR_SIGMAS]

    W, H = V.PANO_SIZE
    y0, y1 = math.radians(V.PANO_YAW[0]), math.radians(V.PANO_YAW[1])
    t0, t1 = math.tan(math.radians(V.PANO_PITCH[0])), math.tan(math.radians(V.PANO_PITCH[1]))
    yaw = y0 + (np.arange(W) + 0.5) / W * (y1 - y0)
    tanp = t1 - (np.arange(H) + 0.5) / H * (t1 - t0)          # row 0 = top
    YAW, TAN = np.meshgrid(yaw, tanp)
    wx, wy, wz = np.sin(YAW), TAN, np.cos(YAW)                # view-space directions on the cylinder

    r, u, f = V.basis()
    a = wx * r[0] + wy * r[1] + wz * r[2]
    b = wx * u[0] + wy * u[1] + wz * u[2]
    c = wx * f[0] + wy * f[1] + wz * f[2]
    # angles in the photo camera's frame; extension is folded in ANGLE space so mirrored tiles keep their size
    th = np.arctan2(a, c)                                    # horizontal angle
    ph = np.arctan2(b, np.hypot(a, c))                       # vertical angle
    th_e = math.atan(V.CX / V.F_PX)                          # left/right photo edges (constant angle)

    def fold(x, lo, hi):                                     # mirror x back into [lo, hi]
        n = hi - lo
        p = np.mod(x - lo, 2 * n)
        return lo + np.where(p > n, 2 * n - p, p)
    thf = fold(th, -th_e, th_e)
    ph_top = np.arctan(V.CY * np.cos(thf) / V.F_PX)                       # top / bottom edge at this column
    ph_bot = -np.arctan((V.PHOTO_H - 1 - V.CY) * np.cos(thf) / V.F_PX)
    phf = np.clip(ph, ph_bot, ph_top)                        # above/below: clamp to the edge row (then heavy blur)

    # distances outside the frame, expressed in full-res photo pixels
    dx = np.maximum(0, np.abs(th) - th_e) * V.F_PX
    dy_top = np.maximum(0, ph - ph_top) * V.F_PX
    dy_bot = np.maximum(0, ph_bot - ph) * V.F_PX
    dist = np.sqrt(dx ** 2 + (dy_top + dy_bot) ** 2)

    px = V.CX + V.F_PX * np.tan(thf)
    py = V.CY - V.F_PX * np.tan(phf) / np.cos(thf)
    sx = np.clip(px, 0, V.PHOTO_W - 1) / DS
    sy = np.clip(py, 0, V.PHOTO_H - 1) / DS

    lev = np.clip(dist / BLUR_STEP, 0, len(levels) - 1)
    vert = dy_top + dy_bot                                   # above/below the frame: reach full blur within ~3 deg
    lev = np.where(vert > 0, np.maximum(lev, np.clip(2 + vert / 60.0, 0, len(levels) - 1)), lev)
    out = np.zeros((H, W, 3), np.float32)
    for i, L in enumerate(levels):
        w = np.clip(1 - np.abs(lev - i), 0, 1)
        if not w.any():
            continue
        samp = np.stack([map_coordinates(L[..., ch], [sy, sx], order=1, mode="nearest") for ch in range(3)], -1)
        out += samp * w[..., None]

    # darkening away from the photo: sides drift to a dimmer city haze, the sky keeps getting darker upward
    k_side = np.maximum(0.62, np.exp(-dx / 5200.0))
    k_up = np.maximum(0.50, np.exp(-dy_top / 2600.0))
    k_down = np.maximum(0.30, np.exp(-dy_bot / 1400.0))
    out *= (k_side * k_up * k_down)[..., None]

    # far from the frame: smooth horizontally (hides mirror seams and the photo's corner vignetting) ...
    soft = np.stack([gaussian_filter(out[..., ch], (2, 40), mode="wrap") for ch in range(3)], -1)
    t = np.clip(dist / 1500.0, 0, 1)[..., None]
    out = out * (1 - t) + soft * t
    # ... and below the photo fade to an even dark ground instead of streaks of the bottom row
    ground = lin[-lin.shape[0] // 7:].reshape(-1, 3).mean(0) * 0.55
    tg = np.clip(dy_bot / 1500.0, 0, 1)[..., None]
    out = out * (1 - tg) + ground * tg

    srgb = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.power(np.maximum(out, 0), 1 / 2.4) - 0.055)
    rng = np.random.default_rng(seed)
    grain = rng.normal(0, GRAIN_STD / 255.0, (H, W, 1)) * np.clip(dist / 200.0, 0, 1)[..., None]
    img = np.clip(srgb + grain, 0, 1)
    os.makedirs(os.path.join(HERE, "export"), exist_ok=True)
    path = os.path.join(HERE, "export", "window_view_pano.jpg")
    Image.fromarray((img * 255 + 0.5).astype(np.uint8)).save(path, quality=88, optimize=True)
    return path


if __name__ == "__main__":
    print(build())
