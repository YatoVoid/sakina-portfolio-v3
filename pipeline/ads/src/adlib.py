"""Small motion-graphics engine for the vintage ads (PIL + numpy, rendered to ffmpeg)."""
import numpy as np, math, random
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
W, H, FPS = 960, 720, 24
SP = "/tmp/claude-0/-home-claude/a669872b-7781-59a2-a8ce-5629bed69569/scratchpad"
FONTS = {"bebas": SP + "/fonts/BebasNeue-Regular.ttf", "dm": SP + "/fonts/DMSerifDisplay-Regular.ttf",
         "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"}
_fc = {}
def F(name, size):
    k = (name, int(size))
    if k not in _fc: _fc[k] = ImageFont.truetype(FONTS[name], int(size))
    return _fc[k]
AMBER = (255, 190, 90); CREAM = (242, 236, 224); GREEN = (120, 255, 160); DARK = (23, 19, 16); RED = (255, 70, 60); BLUE = (90, 150, 255)
clamp = lambda x: max(0.0, min(1.0, x))
def eo3(x): x = clamp(x); return 1 - (1 - x) ** 3
def eob(x): x = clamp(x); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
lerp = lambda a, b, k: a + (b - a) * k

_imgs = {}
def load(path):
    if path not in _imgs: _imgs[path] = Image.open(path).convert("RGB")
    return _imgs[path]

def cover(img, size=(W, H), focus=(.5, .5), zoom=1.0):
    w, h = img.size; tw, th = size
    s = max(tw / w, th / h) * zoom; cw, ch = tw / s, th / s
    cx = min(max(focus[0] * w, cw / 2), w - cw / 2); cy = min(max(focus[1] * h, ch / 2), h - ch / 2)
    return img.resize(size, Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

def kenburns(img, t, dur, f0=(.5, .5), f1=(.5, .5), z0=1.0, z1=1.15, size=(W, H), dim=1.0):
    k = eio(t / dur)
    p = cover(img, size, (lerp(f0[0], f1[0], k), lerp(f0[1], f1[1], k)), lerp(z0, z1, k))
    return ImageEnhance.Brightness(p).enhance(dim) if dim != 1.0 else p

def text_img(txt, font, fill, scale=1.0, rot=0.0, alpha=1.0, spacing=0):
    if spacing:
        widths = [font.getlength(c) for c in txt]; tw = int(sum(widths) + spacing * (len(txt) - 1))
        bb = font.getbbox("Hg"); th = bb[3] + 8
        im = Image.new("RGBA", (tw + 8, th + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 4
        for c, w_ in zip(txt, widths): d.text((x, 4), c, font=font, fill=fill + (255,)); x += w_ + spacing
    else:
        bb = font.getbbox(txt); im = Image.new("RGBA", (bb[2] + 12, bb[3] + 12), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((6, 6), txt, font=font, fill=fill + (255,))
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot: im = im.rotate(rot, expand=True, resample=Image.BILINEAR)
    if alpha < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * alpha)); im.putalpha(a)
    return im

def put(im, layer, cx, cy):
    im.paste(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)), layer)

def typed(lines, t, cps=48):
    n = int(max(0, t) * cps); out = []
    for ln in lines:
        out.append(ln[:max(0, n)]); n -= len(ln) + 3
    return out

def lower_third(im, t, head, lines, t0=0.3, y=470, hsize=58):
    k = eo3((t - t0) / 0.35)
    if k <= 0: return
    d = ImageDraw.Draw(im, "RGBA")
    hw = int(F("bebas", hsize).getlength(head)) + 56
    x = -(1 - k) * (hw + 40)
    d.rectangle([x, y, x + hw, y + hsize + 22], fill=AMBER + (255,))
    d.text((x + 28, y + 4), head, font=F("bebas", hsize), fill=(20, 16, 12))
    if lines:
        bh = 24 + 34 * len(lines)
        d.rectangle([x, y + hsize + 22, x + 880, y + hsize + 22 + bh], fill=(8, 8, 14, 190))
        for i, ln in enumerate(typed(lines, t - t0 - 0.35)):
            if ln: d.text((x + 28, y + hsize + 34 + i * 34), ln, font=F("mono", 22), fill=CREAM)

def chip(im, t, t0, y, label, text, color=AMBER, w=640):
    k = eob((t - t0) / 0.45)
    if k <= 0: return
    x = W - (w + 30) * k + 30 * 0 + (0)
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([x, y, x + w, y + 86], fill=(8, 8, 16, 220)); d.rectangle([x, y, x + 10, y + 86], fill=color + (255,))
    d.text((x + 28, y + 6), label, font=F("bebas", 38), fill=color); d.text((x + 28, y + 50), text, font=F("mono", 20), fill=CREAM)

def vignette_grad():
    yy, xx = np.mgrid[0:H, 0:W]
    return (1 - 0.5 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) ** 1.2)[..., None], \
           (0.84 + 0.16 * np.cos(yy * math.pi * 0.9))[..., None]
VIG, SCAN = vignette_grad()

def post(a, T, glitch=0.0, rng=None):
    a = a.astype(np.float32)
    a = a * np.array([1.05, 0.99, 0.93]) * SCAN * VIG
    band = int((T * 150) % (H + 140)) - 70
    for y in range(max(0, band), min(H, band + 26)): a[y] = np.roll(a[y], int(8 * math.sin(y * 0.4 + T * 20)), axis=0) * 1.18
    if glitch > 0:
        for _ in range(int(3 + 10 * glitch)):
            y0 = random.randrange(0, H - 12); hh = random.randrange(4, 28)
            a[y0:y0 + hh] = np.roll(a[y0:y0 + hh], random.randrange(-int(60 * glitch) - 4, int(60 * glitch) + 5), axis=1)
        a += np.random.rand(H, W, 1) * 60 * glitch
    a[..., 0] = np.roll(a[..., 0], 2 + int(5 * glitch), axis=1); a[..., 2] = np.roll(a[..., 2], -2 - int(5 * glitch), axis=1)
    a += np.random.randn(H, W, 1) * 7.5; a *= 0.975 + 0.025 * math.sin(T * 37)
    return np.clip(a, 0, 255).astype(np.uint8)

def hblur(a, px):
    if px < 1: return a
    out = np.zeros_like(a, dtype=np.float32); n = 7
    for i in range(n): out += np.roll(a, int((i - n // 2) * px / (n // 2)), axis=1)
    return (out / n).astype(np.uint8)

def grid_bg(t, color=(20, 40, 90), base=(8, 10, 22)):
    im = Image.new("RGB", (W, H), base); d = ImageDraw.Draw(im)
    off = (t * 40) % 60
    for x in range(-60, W + 60, 60): d.line([(x - off, 0), (x - off, H)], fill=color, width=1)
    for y in range(-60, H + 60, 60): d.line([(0, y + off), (W, y + off)], fill=color, width=1)
    return im

# ---------------- logo (monogram + wordmark), the site's brand ----------------
def monogram(size, glow=0.0):
    S = int(size); pad = int(S * 0.5)
    im = Image.new("RGBA", (S + pad * 2, S + pad * 2), (0, 0, 0, 0))
    if glow > 0:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).rounded_rectangle([pad, pad, pad + S, pad + S], radius=int(S * .25), fill=(255, 215, 150, int(150 * glow)))
        im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(S * 0.18)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([pad, pad, pad + S, pad + S], radius=int(S * .25), fill=DARK + (255,), outline=(70, 60, 50, 255), width=max(2, S // 60))
    f = F("dm", S * 0.78); bb = f.getbbox("S")
    d.text((pad + (S - (bb[2] - bb[0])) / 2 - bb[0], pad + (S - (bb[3] - bb[1])) / 2 - bb[1] - S * 0.02), "S", font=f, fill=CREAM + (255,))
    return im

def logo_frame(t, hold=False):
    """Logo sequence on its own 960x720 frame. t in seconds from 0; settles at ~3.0 s."""
    im = Image.new("RGB", (W, H), (14, 11, 9)); d = ImageDraw.Draw(im, "RGBA")
    yy, xx = np.mgrid[0:H, 0:W]
    glow = np.clip(1 - np.sqrt(((xx - W / 2) / 520) ** 2 + ((yy - 300) / 380) ** 2), 0, 1)[..., None] * np.array([60, 36, 16])
    im = Image.fromarray(np.clip(np.asarray(im).astype(np.float32) + glow, 0, 255).astype(np.uint8))
    k = eob((t - 0.55) / 0.7)
    if k > 0:
        S = 230 * max(0.05, k); m = monogram(S, glow=min(1, k) * (0.8 + 0.2 * math.sin(t * 9)))
        im.paste(m, (int(W / 2 - m.width / 2), int(250 - m.height / 2)), m)
        sw = (t - 1.2) / 0.9                                  # light sweep across the monogram
        if 0 < sw < 1:
            x0 = W / 2 - 160 + sw * 320
            sweep = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sweep).polygon([(x0, 130), (x0 + 36, 130), (x0 - 24, 370), (x0 - 60, 370)], fill=(255, 245, 220, 150))
            mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).rounded_rectangle([W / 2 - 115, 135, W / 2 + 115, 365], radius=57, fill=255)
            sweep.putalpha(Image.fromarray(np.minimum(np.asarray(sweep.getchannel("A")), np.asarray(mask))))
            im.paste(sweep, (0, 0), sweep)
    word = "SAKINA SAIFUDDIN"
    wk = clamp((t - 1.5) / 1.3)
    if wk > 0:
        sp = lerp(46, 7, eo3(wk)); f = F("dm", 62); n = len(word)
        widths = [f.getlength(c) for c in word]; total = sum(widths) + sp * (n - 1); x = (W - total) / 2
        for i, c in enumerate(word):
            la = clamp((t - 1.5 - i * 0.045) / 0.35)
            if c != " " and la > 0:
                lay = text_img(c, f, CREAM, alpha=la); im.paste(lay, (int(x - 6), int(430 - (1 - eo3(la)) * 24)), lay)
            x += widths[i] + sp
    sk = clamp((t - 2.5) / 0.6)
    if sk > 0:
        lay = text_img("DATA SCIENTIST  ·  UNIVERSITY OF HOUSTON", F("mono", 20), (176, 166, 150), alpha=sk, spacing=4)
        put(im, lay, W / 2, 530 + (1 - sk) * 14)
    return im

# ---------------- project / company logo intro (reusable for every ad) ----------------
def project_logo_frame(t, logo_path, parts, tagline=None, bg=(10, 26, 64), accent=(255, 190, 90), tint=(127, 168, 240), seed=1):
    """Animated logo sequence for a project or company. Settles at ~3.0 s. parts = [(text, colour), ...] for the wordmark."""
    yy, xx = np.mgrid[0:H, 0:W]
    g = np.clip(1 - np.sqrt(((xx - W / 2) / 560) ** 2 + ((yy - 300) / 420) ** 2), 0, 1)[..., None]
    base = np.array(bg, dtype=np.float32) * (0.35 + 0.9 * g) + g * np.array([10, 18, 40])
    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im, "RGBA")
    off = (t * 30) % 48                                                   # faint moving circuit grid
    for x in range(-48, W + 48, 48): d.line([(x - off, 0), (x - off, H)], fill=tint + (22,), width=1)
    for y in range(-48, H + 48, 48): d.line([(0, y + off), (W, y + off)], fill=tint + (22,), width=1)
    logo = load_rgba(logo_path)
    k = eob((t - 0.45) / 0.6)
    if k > 0:
        pat = [1, .25, 1, .5, 1, .15, 1] if t < 1.25 else [1]
        flick = pat[min(len(pat) - 1, int((t - 0.45) / 0.11))] if t < 1.25 else 1.0
        s = 300 * max(0.05, k); lg = logo.copy(); lg.thumbnail((int(s), int(s)))
        r = (t - 0.5) / 0.9                                               # energy ring
        if 0 < r < 1: d.ellipse([W / 2 - 40 - 380 * r, 250 - 40 - 380 * r, W / 2 + 40 + 380 * r, 250 + 40 + 380 * r], outline=tint + (int(200 * (1 - r)),), width=4)
        gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([W / 2 - s * .55, 250 - s * .55, W / 2 + s * .55, 250 + s * .55], fill=tint + (int(110 * min(1, k) * (0.8 + 0.2 * math.sin(t * 8))),))
        im.paste(gl.filter(ImageFilter.GaussianBlur(40)), (0, 0), gl.filter(ImageFilter.GaussianBlur(40)))
        a = lg.getchannel("A").point(lambda v: int(v * flick)); lg.putalpha(a)
        im.paste(lg, (int(W / 2 - lg.width / 2), int(250 - lg.height / 2)), lg)
        d = ImageDraw.Draw(im, "RGBA")
        if 0.95 < t < 1.7:                                                # electric arcs
            rr = random.Random(int(t * 24) + seed)
            for _ in range(3):
                dx = rr.choice([-1, 1]); x, y = W / 2 + dx * s * .46, 250 + rr.uniform(-s * .3, s * .3); pts = [(x, y)]
                for _ in range(6): x += dx * rr.uniform(12, 28); y += rr.uniform(-22, 22); pts.append((x, y))
                d.line(pts, fill=(200, 230, 255, 230), width=3)
    f = F("bebas", 120); words = []; total = 0
    for txt, col in parts:
        words.append((txt, col, f.getlength(txt))); total += f.getlength(txt) + 44
    total -= 44; x = (W - total) / 2; ci = 0
    for txt, col, w_ in words:
        cx = x
        for c in txt:
            la = clamp((t - 1.5 - ci * 0.05) / 0.3); cw = f.getlength(c) + 2
            if c != " " and la > 0:
                lay = text_img(c, f, col, alpha=la); im.paste(lay, (int(cx - 6 - (1 - eo3(la)) * 60), int(380 - 8)), lay)
            cx += cw; ci += 1
        x += w_ + 44
    if tagline:
        n = int(max(0, t - 2.4) * 34); lay = text_img(tagline[:n] + ("_" if n < len(tagline) and int(t * 3) % 2 == 0 else ""), F("mono", 24), tint)
        put(im, lay, W / 2, 560)
    return im

_rgba = {}
def load_rgba(path):
    if path not in _rgba: _rgba[path] = Image.open(path).convert("RGBA")
    return _rgba[path]
