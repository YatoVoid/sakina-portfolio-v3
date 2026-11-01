"""Build the club-chair leather maps from the Attic-Ease reference photo (Edit #2).

Input : the product photo (argv[1]) = IMG_9274.png cropped to (77,458)-(1096,1477); patch boxes are in that crop.
Output: <out_dir>/leather_crackle_{albedo,height}.png   fine tan crackle over honey brown (seat, arms, base, shell)
        <out_dir>/leather_croc_{albedo,height}.png      large crocodile-scale grid (back cushion)

Method (real photo pixels, not a procedural guess):
  1. crop a clean, evenly lit patch of leather from the photo,
  2. remove the lighting (divide by a heavy blur of the patch), keep the vein/scale structure and cell colour,
  3. grow a 1024 x 1024 sheet from the patch with min-error-boundary quilting (Efros & Freeman), so the sheet is
     built from the photo's own veins but is much larger than the crop. ~1.4 mm per pixel => ~1.4 m per sheet, so the
     box projection on the chair never has to repeat it.
  4. height map = high-passed luminance (veins are the raised tan ridges in the photo).
"""
import sys, os
import numpy as np, cv2
from PIL import Image

SRC = sys.argv[1]
OUT = sys.argv[2]
N, B, O = 1024, 44, 14          # sheet size, block size, overlap
S = B - O
rng = np.random.default_rng(7)

# name: (boxes in photo coords (photo.png = product image cropped from the screenshot), mean sRGB, blur sigma)
PATCHES = {
    "crackle": (((327, 782, 667, 845), (350, 600, 670, 680), (300, 440, 440, 520)), (108, 62, 31), 14),
    "croc":    (((470, 285, 625, 415), (690, 290, 850, 400), (470, 415, 600, 470)), (146, 90, 46), 20),
}


def delight(img, sigma, target):
    f = img.astype(np.float32) / 255.0
    lo = cv2.GaussianBlur(f, (0, 0), sigma, borderType=cv2.BORDER_REFLECT)
    r = f / np.maximum(lo, 1e-3)
    r = np.clip(r, 0.35, 2.2)
    hi = cv2.GaussianBlur(r, (0, 0), 2.0)
    r = np.clip(1.0 + (r - 1.0) * 1.0 + (r - hi) * 0.6, 0.3, 2.4)         # slight vein sharpening
    out = r * (np.array(target, np.float32) / 255.0)
    return np.clip(out, 0, 1)


def quilt(srcs, N, B, O):
    used = [np.zeros((x.shape[0] - B + 1, x.shape[1] - B + 1), np.float32) for x in srcs]
    S = B - O
    n = (N - O) // S + 1
    big = np.zeros(((n - 1) * S + B, (n - 1) * S + B, 3), np.float32)
    for i in range(n):
        for j in range(n):
            y, x = i * S, j * S
            if i == 0 and j == 0:
                src = srcs[0]
                ys, xs = rng.integers(0, src.shape[0] - B), rng.integers(0, src.shape[1] - B)
                big[y:y + B, x:x + B] = src[ys:ys + B, xs:xs + B]
                continue
            # error surface over all candidate positions
            errs = []
            for src in srcs:
                h, w, _ = src.shape
                err = np.zeros((h - B + 1, w - B + 1), np.float32)
                if j > 0:
                    err += cv2.matchTemplate(src, big[y:y + B, x:x + O], cv2.TM_SQDIFF)[:, :w - B + 1]
                if i > 0:
                    err += cv2.matchTemplate(src, big[y:y + O, x:x + B], cv2.TM_SQDIFF)[:h - B + 1, :]
                errs.append(err)
            errs = [e * (1.0 + 4.0 * u) for e, u in zip(errs, used)]      # penalise re-using the same spot
            best = min(e.min() for e in errs) * 1.35 + 1e-6
            cand = [(si, yy, xx) for si, e in enumerate(errs) for yy, xx in zip(*np.where(e <= best))]
            si, yy, xx = cand[rng.integers(0, len(cand))]
            blk = srcs[si][yy:yy + B, xx:xx + B].copy()
            used[si][max(0, yy - 10):yy + 11, max(0, xx - 10):xx + 11] += 1.0
            # min-cut on the left overlap
            mask = np.ones((B, B), bool)
            if j > 0:
                d = ((big[y:y + B, x:x + O] - blk[:, :O]) ** 2).sum(2)
                cut = mincut(d, vertical=True)
                for r in range(B):
                    mask[r, :cut[r]] = False
            if i > 0:
                d = ((big[y:y + O, x:x + B] - blk[:O, :]) ** 2).sum(2)
                cut = mincut(d, vertical=False)
                for c in range(B):
                    mask[:cut[c], c] = False
            reg = big[y:y + B, x:x + B]
            reg[mask] = blk[mask]
    return big[:N, :N]


def mincut(d, vertical):
    if not vertical:
        return mincut(d.T, True)
    h, w = d.shape
    E = d.copy()
    for r in range(1, h):
        for c in range(w):
            E[r, c] += E[r - 1, max(0, c - 1):c + 2].min()
    cut = np.zeros(h, int)
    c = int(E[-1].argmin()); cut[-1] = c
    for r in range(h - 2, -1, -1):
        lo = max(0, c - 1)
        c = lo + int(E[r, lo:c + 2].argmin()); cut[r] = c
    return cut + 1       # columns left of the cut keep the old pixels


photo = np.array(Image.open(SRC).convert("RGB"))
os.makedirs(OUT, exist_ok=True)
for name, (boxes, target, sigma) in PATCHES.items():
    crops = [photo[y0:y1, x0:x1] for (x0, y0, x1, y1) in boxes]
    dl = [delight(c, sigma, target) for c in crops]
    crop = crops[0]
    sheet = quilt(dl, N + 0, B, O)
    sheet = sheet[:N, :N]
    # height = high-passed luminance (tan ridges raised)
    lum = sheet @ np.array([0.30, 0.59, 0.11], np.float32)
    hp = lum - cv2.GaussianBlur(lum, (0, 0), 9)
    hp = (hp - hp.min()) / (hp.max() - hp.min() + 1e-6)
    Image.fromarray((np.clip(sheet, 0, 1) * 255).astype(np.uint8)).save(f"{OUT}/leather_{name}_albedo.png")
    Image.fromarray((hp * 255).astype(np.uint8)).save(f"{OUT}/leather_{name}_height.png")
    print(name, crop.shape, "->", sheet.shape, flush=True)
