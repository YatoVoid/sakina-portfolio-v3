import math, numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageChops
from adlib import W, H, eo3, eio, clamp, lerp, put, text_img, F
def fade_black(a, T, total, secs=1.9):
    u = clamp((total - T) / secs); k = u * u * (3 - 2 * u)
    return a if k >= 1 else (a.astype(np.float32) * k).astype(np.uint8)
def logo_intro(t, logo, size, base, glow, dur=3.5, cy=360):
    """Only the logo: soft glow, slow rise, one light sheen, dip to dark at the end."""
    im = Image.new("RGB", (W, H), base); g = Image.new("RGB", (W, H), (0, 0, 0)); gd = ImageDraw.Draw(g); pulse = 0.75 + 0.25 * math.sin(t * 2.2); a0 = eo3(t / 1.4) * pulse
    gd.ellipse([W / 2 - size * .8, cy - size * .55, W / 2 + size * .8, cy + size * .55], fill=tuple(int(c * a0) for c in glow)); g = g.filter(ImageFilter.GaussianBlur(70)); im = ImageChops.add(im, g)
    sc = lerp(0.88, 1.0, eo3(t / 2.2)); lw = int(size * sc); lay = logo.resize((lw, int(lw * logo.height / logo.width)), Image.LANCZOS); al = clamp(t / 1.1)
    arr = np.array(lay).astype(np.float32); sx = lerp(-200, lay.width + 200, eio((t - 1.3) / 1.4))
    if 1.3 < t < 2.7:
        xs = np.arange(lay.width)[None, :] + np.arange(lay.height)[:, None] * 0.6; band = np.exp(-((xs - sx) / 40.0) ** 2)[..., None]; arr[..., :3] = np.clip(arr[..., :3] + band * 90, 0, 255)
    lay = Image.fromarray(arr.astype(np.uint8)); lay.putalpha(lay.getchannel("A").point(lambda v: int(v * al))); put(im, lay, W / 2, cy)
    if t > dur - 0.5: im = ImageEnhance.Brightness(im).enhance(max(0.0, 1 - (t - (dur - 0.5)) / 0.5))
    return im
