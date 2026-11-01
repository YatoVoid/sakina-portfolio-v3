"""Generate pencil 'handwriting' masks for the notebook pages (white strokes on black, used as a mix factor).

The strokes are illegible cursive-like scribbles (no real text), sitting on the ruled lines of
mats.ruled_paper (37 lines per page, lines in the bottom 6 % of each band, top 10 % of the page blank).
Deterministic (seeded) so rebuilds are identical.
    python3 components/room_refresh/handwriting.py  -> tex/handwriting_left.png, tex/handwriting_right.png
"""
import math, os, random
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 840, 1280                      # page aspect 0.168 x 0.256 m
LINES = 37


def _word(draw, x, base, rnd, xh, intensity):
    n = rnd.randint(3, 9)                       # letters
    pts = []
    for i in range(n * 8 + 1):
        t = i / 8
        k = int(t)
        tall = (k * 7 + rnd.randint(0, 0)) % 5 == 0 and rnd.random() < 0.6
        amp = xh * (1.9 if tall else 1.0)
        y = base - amp * (0.5 - 0.5 * math.cos(2 * math.pi * t))
        y += rnd.uniform(-0.6, 0.6)
        pts.append((x + t * xh * 0.95 + math.sin(2 * math.pi * t) * xh * 0.25, y))
    draw.line(pts, fill=intensity, width=3, joint="curve")
    return pts[-1][0]


def page(seed, lines_used, heading=False):
    rnd = random.Random(seed)
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    band = H / LINES
    first = int(LINES * 0.10) + 1
    for li in range(first, first + lines_used):
        base = (li + 0.94) * band              # baseline just above the printed line (image row 0 = page top)
        x = 0.17 * W if li > first or not heading else 0.20 * W
        end = W * rnd.uniform(0.80, 0.93) if li != first + lines_used - 1 else W * rnd.uniform(0.35, 0.6)
        xh = band * 0.30
        intensity = rnd.randint(225, 255)
        while x < end:
            x = _word(d, x, base, rnd, xh, intensity) + xh * rnd.uniform(1.0, 1.8)
        if heading and li == first:
            d.line([(0.20 * W, base + 4), (x - xh, base + 5)], fill=180, width=2)   # underline
    return img.filter(ImageFilter.GaussianBlur(0.6))


def build():
    os.makedirs(os.path.join(HERE, "tex"), exist_ok=True)
    out = []
    for name, seed, n, head in (("left", 3, 17, True), ("right", 9, 9, False)):
        p = os.path.join(HERE, "tex", f"handwriting_{name}.png")
        page(seed, n, head).save(p, optimize=True)
        out.append(p)
    return out


if __name__ == "__main__":
    print(build())
