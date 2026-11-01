import sys, subprocess
sys.path.insert(0, "/tmp/claude-0/-home-claude/a669872b-7781-59a2-a8ce-5629bed69569/scratchpad/s")
from adlib import *
SP = '/tmp/claude-0/-home-claude/a669872b-7781-59a2-a8ce-5629bed69569/scratchpad'
PG=""

random.seed(3); np.random.seed(3)

def hdr(im, T, show=True):
    if not show: return
    d = ImageDraw.Draw(im, "RGBA")
    if int(T * 2) % 2 == 0: d.ellipse([34, 30, 50, 46], fill=RED + (255,))
    d.text((60, 24), "REC", font=F("mono", 22), fill=CREAM); d.text((W - 230, 24), "SP 0:%02d:%02d" % (int(T) // 60, int(T) % 60), font=F("mono", 22), fill=GREEN)
    for (x, y, sx, sy) in ((24, 70, 1, 1), (W - 24, 70, -1, 1), (24, H - 24, 1, -1), (W - 24, H - 24, -1, -1)):   # viewfinder corners
        d.line([(x, y), (x + 40 * sx, y)], fill=CREAM + (200,), width=3); d.line([(x, y), (x, y + 40 * sy)], fill=CREAM + (200,), width=3)



import math
def card(im, x, y, w, h, fill=(10, 34, 46, 235), outline=AMBER, width=3):
    d = ImageDraw.Draw(im, "RGBA"); d.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=fill, outline=outline + (255,), width=width)
LINE = (20, 70, 80); TEAL = (6, 20, 30)
CUR = [(6, 20, 30), (20, 70, 80), 0]
def bg(t):
    base, line, wave = CUR; im = grid_bg(t, line, base)
    if wave:
        d = ImageDraw.Draw(im, "RGBA")
        for k in range(5):
            pts = [(x, 600 + k * 26 + 10 * math.sin(x / 70 + t * 2 + k)) for x in range(0, W + 20, 20)]; d.line(pts, fill=(70, 150, 255, 70 - k * 10), width=3)
    return im
def themed(fn, base, line, wave=0, orig=None, new=None):
    def g(t, T):
        CUR[0], CUR[1], CUR[2] = base, line, wave; return fn(t * orig / new if orig else t, T)
    return g
def title(im, t, txt, y=90, size=80, col=CREAM, t0=0.1):
    k = eob((t - t0) / 0.4); put(im, text_img(txt, F("bebas", size), col, scale=lerp(1.4, 1, k), alpha=clamp(k * 2)), W / 2, y)
def arrow(im, x0, x1, y, k, col=AMBER):
    d = ImageDraw.Draw(im, "RGBA"); x = lerp(x0, x1, clamp(k))
    if k > 0: d.line([(x0, y), (x, y)], fill=col + (255,), width=5)
    if k >= 1: d.polygon([(x1, y), (x1 - 18, y - 12), (x1 - 18, y + 12)], fill=col + (255,))


from adkit import *
HOUSE = Image.open(SP + "/ads/Logo_caniownahome.png").convert("RGBA")
def s_intro(t, T): return logo_intro(t, HOUSE, 360, (5, 22, 30), (20, 120, 110), 3.5)

def s_stack(t, T):
    im = bg(t); title(im, t, "SAKINA BUILT IT WITH", 80, 76); d = ImageDraw.Draw(im, "RGBA")
    chips = [("NEXT.JS", 0, 0), ("PYTHON", 1, 0), ("SCIKIT-LEARN", 2, 0), ("AWS LAMBDA", 0, 1), ("GEMINI", 1, 1), ("VERCEL", 2, 1)]
    for n, (nm, cx, cy) in enumerate(chips):
        k = eob((t - 1.7 - n * 0.55) / 0.4); x = 50 + cx * 300; y = 190 + cy * 150
        if k > 0:
            w = max(4, 280 * min(k, 1)); d.rounded_rectangle([x, y, x + w, y + 110], radius=14, fill=(10, 40, 52, 245), outline=AMBER + (255,), width=4)
            if k > 0.9: put(im, text_img(nm, F("bebas", 56 if len(nm) < 11 else 46), CREAM), x + 140, y + 55)
    put(im, text_img("A HOUSTON HOUSING TOOL FOR RENTERS", F("mono", 20), AMBER, alpha=eo3((t - 5.2) / 0.5)), W / 2, 520)
    return im

def s_hard(t, T):
    im = bg(t); title(im, t, "THE HARD PART", 70, 84, AMBER); d = ImageDraw.Draw(im, "RGBA")
    def box(x, y, w, h, lab, col, k=1.0):
        d.rounded_rectangle([x, y, x + w * k, y + h], radius=10, fill=(10, 36, 48, 245), outline=col + (255,), width=3)
        if k > .9: put(im, text_img(lab, F("bebas", 38), CREAM), x + w / 2, y + h / 2)
    box(60, 160, 220, 80, "BROWSER", CREAM, eo3((t - 0.3) / 0.3)); box(700, 160, 220, 80, "AWS MODEL", AMBER, eo3((t - 0.5) / 0.3))
    k = clamp((t - 1.0) / 0.8)
    if k > 0:
        x1 = lerp(280, 700, k); d.line([(280, 200), (x1, 200)], fill=RED + (255,), width=5)
        if k >= 1:
            d.line([(450, 170), (530, 230)], fill=RED + (255,), width=8); d.line([(530, 170), (450, 230)], fill=RED + (255,), width=8)
            put(im, text_img("NO CORS HEADERS", F("bebas", 44), RED, alpha=eo3((t - 1.8) / 0.3)), 490, 270)
    box(60, 340, 220, 80, "BROWSER", CREAM, eo3((t - 2.6) / 0.3)); box(370, 340, 220, 80, "SERVER ROUTE", GREEN, eo3((t - 2.8) / 0.3)); box(700, 340, 220, 80, "AWS MODEL", AMBER, eo3((t - 3.0) / 0.3))
    for a, b, t0 in ((280, 370, 3.3), (590, 700, 3.7)):
        kk = clamp((t - t0) / 0.3)
        if kk > 0: d.line([(a, 380), (lerp(a, b, kk), 380)], fill=GREEN + (255,), width=5)
    put(im, text_img("SAKINA ROUTED EVERY CALL THROUGH THE SERVER", F("bebas", 56), GREEN, alpha=eo3((t - 4.3) / 0.4)), W / 2, 510)
    put(im, text_img("EACH API ROUTE CALLS THE LAMBDA FROM THE SERVER", F("mono", 19), CREAM, alpha=eo3((t - 5.0) / 0.4)), W / 2, 570)
    return im

def s_end(t, T):
    im = bg(t); d = ImageDraw.Draw(im, "RGBA")
    k = eob(t / 0.5); put(im, text_img("LIVE NOW", F("bebas", 200), AMBER, scale=lerp(1.5, 1, k), alpha=clamp(k * 2)), W / 2, 260)
    put(im, text_img("FOR HOUSTON RENTERS", F("bebas", 80), CREAM, alpha=eo3((t - 0.8) / 0.4)), W / 2, 400)
    put(im, text_img("caniownahome.vercel.app", F("mono", 30), GREEN, alpha=eo3((t - 1.4) / 0.4)), W / 2, 500)
    return im

def s_hook(t, T):
    im = bg(t)
    if t < 1.9:
        k = eob((t - 0.15) / 0.35); put(im, text_img("YOU PAY RENT", F("bebas", 160), CREAM, scale=lerp(1.6, 1, k), alpha=clamp(k * 2)), W / 2, 270)
        k2 = eob((t - 0.6) / 0.35); put(im, text_img("EVERY MONTH.", F("bebas", 190), RED, scale=lerp(1.6, 1, k2), alpha=clamp((t - .6) * 4)), W / 2, 460)
    else:
        k = eob((t - 2.0) / 0.35); put(im, text_img("WHAT IF IT", F("bebas", 170), CREAM, scale=lerp(1.6, 1, k), alpha=clamp(k * 2)), W / 2, 260)
        k2 = eob((t - 2.4) / 0.35); put(im, text_img("BOUGHT A HOME?", F("bebas", 170), AMBER, scale=lerp(1.6, 1, k2), alpha=clamp((t - 2.4) * 4)), W / 2, 460)
    return im

def s_input(t, T):
    im = bg(t); title(im, t, "ZIP + RENT. THAT'S IT.", 80, 78)
    k = eo3((t - 0.2) / 0.4); card(im, int(120 - (1 - k) * 900), 150, 720, 420); d = ImageDraw.Draw(im, "RGBA")
    if k > 0.95:
        d.text((170, 185), "ZIP CODE", font=F("bebas", 36), fill=AMBER); d.rectangle([170, 230, 790, 290], fill=(4, 14, 20, 255), outline=LINE + (255,), width=2)
        d.text((190, 238), typed(["77044"], t - 0.5, 9)[0] + ("_" if int(t * 3) % 2 == 0 and t < 1.6 else ""), font=F("mono", 40), fill=CREAM)
        d.text((170, 315), "MONTHLY RENT", font=F("bebas", 36), fill=AMBER); d.rectangle([170, 360, 790, 420], fill=(4, 14, 20, 255), outline=LINE + (255,), width=2)
        d.text((190, 368), typed(["$2,200"], t - 1.4, 9)[0] + ("_" if int(t * 3) % 2 == 0 and 1.4 < t < 2.5 else ""), font=F("mono", 40), fill=CREAM)
        pulse = 1 if t < 2.4 else 1 + 0.05 * math.sin((t - 2.4) * 14)
        col = GREEN if t >= 2.4 else (80, 150, 110); d.rounded_rectangle([170, 465, 790, 535], radius=10, fill=col + (255,))
        put(im, text_img("SHOW MY HOMES", F("bebas", 52), (8, 24, 16), scale=pulse), W / 2, 500)
    put(im, text_img("EXAMPLE SEARCH", F("mono", 18), CREAM, alpha=0.7), W / 2, 612)
    return im

def s_how(t, T):
    im = bg(t); title(im, t, "RENT BECOMES A HOME BUDGET", 80, 70); d = ImageDraw.Draw(im, "RGBA")
    boxes = [(160, "YOUR RENT", None, 0.3), (480, "A LOAN", "6.5%  \u00B7  30 YEARS", 1.1), (800, "YOUR BUDGET", "+ DOWN PAYMENT", 1.9)]
    for cx, head, sub, t0 in boxes:
        k = eob((t - t0) / 0.4)
        if k > 0:
            w, h = 250 * min(k, 1), 150 * min(k, 1); card(im, int(cx - w / 2), int(260 - h / 2), int(w), int(h))
            if k > 0.9:
                put(im, text_img(head, F("bebas", 52), CREAM), cx, 245 if sub else 260)
                if sub: put(im, text_img(sub, F("mono", 18), AMBER), cx, 295)
    arrow(im, 295, 345, 260, (t - 0.8) / 0.3); arrow(im, 615, 665, 260, (t - 1.6) / 0.3)
    k = eob((t - 2.9) / 0.5)
    if k > 0:
        card(im, 90, 400, 780, 170, outline=GREEN)
        if k > 0.9:
            put(im, text_img("HOMES IN YOUR ZIP", F("bebas", 64), CREAM), W / 2, 450); put(im, text_img("PRICED UP TO 110% OF THE BUDGET", F("bebas", 64), GREEN), W / 2, 525)
    return im

FEATS = ["BEDS", "BATHS", "SQFT", "LOT SQFT", "DAYS ON ZILLOW", "RENT ESTIMATE", "TAX VALUE", "LAT", "LON", "LOG SQFT", "BEDS PER BATH", "TOTAL ROOMS", "SINGLE-FAMILY", "CONDO", "TOWNHOUSE"]
def s_model(t, T):
    im = bg(t); title(im, t, "A MODEL PRICES EVERY HOME", 70, 64); d = ImageDraw.Draw(im, "RGBA")
    for i, nm in enumerate(FEATS):
        k = eob((t - 0.3 - i * 0.14) / 0.3)
        if k > 0:
            x = 40 + (i % 3) * 160; y = 140 + (i // 3) * 76; w = 150 * min(k, 1)
            d.rounded_rectangle([x, y, x + w, y + 60], radius=8, fill=(10, 40, 52, 240), outline=AMBER + (255,), width=2)
            if k > 0.9: put(im, text_img(nm, F("bebas", 26 if len(nm) < 11 else 21), CREAM), x + 75, y + 30)
    k = eo3((t - 2.6) / 0.4)
    if k > 0:
        card(im, int(540 + (1 - k) * 500), 140, 390, 190, outline=GREEN); d = ImageDraw.Draw(im, "RGBA")
        d.text((560, 152), "HISTGRADIENTBOOSTING", font=F("mono", 20), fill=GREEN); d.text((560, 190), "15 FEATURES", font=F("bebas", 56), fill=CREAM)
        v = int(111529 * clamp((t - 3.0) / 0.9)); d.text((560, 250), "RMSE", font=F("bebas", 34), fill=AMBER); d.text((650, 238), "$%s" % format(v, ","), font=F("bebas", 66), fill=CREAM)
    k = eo3((t - 3.9) / 0.4)
    if k > 0:
        d.text((545, 355), "FAIR PRICE  \u00B1 RMSE", font=F("mono", 20), fill=AMBER); d.rectangle([545, 395, 925, 415], fill=(30, 60, 70, 255))
        d.rectangle([675, 395, 675 + 120 * k, 415], fill=AMBER + (255,)); mx = 545 + 190 + math.sin(t * 2.2) * 60 * k; d.polygon([(mx, 392), (mx - 10, 372), (mx + 10, 372)], fill=CREAM + (255,))
    for i, (lab, col) in enumerate((("GOOD BUY", GREEN), ("NEGOTIATE", AMBER), ("OVERPRICED", RED))):
        k = eob((t - 4.5 - i * 0.25) / 0.3)
        if k > 0:
            w = 120 * min(k, 1); x = 545 + i * 130; d.rounded_rectangle([x, 470, x + w, 530], radius=8, fill=col + (255,))
            if k > 0.9: put(im, text_img(lab, F("bebas", 30), (12, 16, 12)), x + 60, 500)
    return im

def s_flood(t, T):
    im = bg(t); title(im, t, "FLOOD RISK, ZIP BY ZIP", 90, 80); d = ImageDraw.Draw(im, "RGBA")
    x0, x1, y = 120, 840, 300
    for i in range(720):
        u = i / 720; c = (int(lerp(90, 255, clamp(u * 2))), int(lerp(230, 70, clamp(u * 1.4 - 0.1))), 90); d.line([(x0 + i, y), (x0 + i, y + 50)], fill=c + (255,))
    k = eo3((t - 0.3) / 0.4)
    mx = x0 + 720 * (0.5 + 0.45 * math.sin(t * 1.9 + 0.6)) * k + 0.0; d.polygon([(mx, y - 6), (mx - 16, y - 40), (mx + 16, y - 40)], fill=CREAM + (255,))
    for lab, ux in (("LOW", 0.12), ("MEDIUM", 0.5), ("HIGH", 0.88)): put(im, text_img(lab, F("bebas", 44), CREAM), x0 + 720 * ux, y + 80)
    d.text((120, 410), "SCORE 0 TO 1  \u00B7  BUILT FROM FLOOD-INSURANCE CLAIMS", font=F("mono", 20), fill=AMBER)
    k = eob((t - 1.8) / 0.4)
    if k > 0:
        w = 560 * min(k, 1); d.rounded_rectangle([W / 2 - w / 2, 480, W / 2 + w / 2, 570], radius=10, fill=RED + (255,))
        if k > 0.9: put(im, text_img("FLOOD TRAP FLAGGED", F("bebas", 62), (20, 8, 8)), W / 2, 525)
    return im

def s_chat(t, T):
    im = bg(t); title(im, t, "JUST TALK TO IT", 80, 80); d = ImageDraw.Draw(im, "RGBA")
    k = eo3((t - 0.2) / 0.4); card(im, int(60 - (1 - k) * 700), 150, 360, 400, outline=BLUE)
    if k > 0.95:
        d.text((85, 165), "GEMINI CHAT", font=F("bebas", 38), fill=BLUE)
        for i, (w_, yy, side) in enumerate(((220, 230, 0), (190, 300, 1), (240, 370, 0))):
            kk = eo3((t - 0.7 - i * 0.5) / 0.3)
            if kk > 0:
                x = 85 if side == 0 else 395 - w_
                d.rounded_rectangle([x, yy, x + w_ * kk, yy + 46], radius=18, fill=(40, 80, 140, 255) if side == 0 else (20, 50, 70, 255))
        if t > 2.2:
            for j in range(3): d.ellipse([100 + j * 26, 455 + math.sin(t * 8 + j) * 6, 114 + j * 26, 469 + math.sin(t * 8 + j) * 6], fill=CREAM + (255,))
    d.text((470, 160), "FILTERS FOUND", font=F("mono", 22), fill=AMBER)
    for i, nm in enumerate(("BEDROOMS", "BATHROOMS", "SIZE", "YARD", "HOME TYPE")):
        kk = eob((t - 1.6 - i * 0.28) / 0.35)
        if kk > 0:
            w = 400 * min(kk, 1); y = 200 + i * 66; d.rounded_rectangle([470, y, 470 + w, y + 54], radius=10, fill=(10, 40, 52, 240), outline=GREEN + (255,), width=3)
            if kk > 0.9: d.text((492, y + 6), nm, font=F("bebas", 40), fill=CREAM)
    if t > 3.6: put(im, text_img("PLUS A WRITTEN \"WHAT IT'S LIKE\" FOR EVERY HOME", F("mono", 19), AMBER, alpha=eo3((t - 3.6) / 0.4)), 665, 560)
    return im

def s_cost(t, T):
    im = bg(t); title(im, t, "THE REAL MONTHLY COST", 80, 78); d = ImageDraw.Draw(im, "RGBA")
    segs = [("LOAN", 300, AMBER), ("TAX", 120, BLUE), ("INSURANCE", 140, GREEN), ("PMI", 80, RED), ("HOA", 80, (190, 130, 255))]
    x = 90
    for i, (nm, w, col) in enumerate(segs):
        k = eo3((t - 0.4 - i * 0.28) / 0.35)
        if k > 0:
            d.rectangle([x, 210, x + w * 1.0 * k, 300], fill=col + (255,))
            if k > 0.95: put(im, text_img(nm, F("bebas", 30), (14, 14, 14)), x + w / 2, 255)
        x += w
    put(im, text_img("VS YOUR RENT", F("bebas", 56), CREAM, alpha=eo3((t - 1.9) / 0.4)), W / 2, 380)
    for i, (lab, col) in enumerate((("LESS THAN YOUR RENT", GREEN), ("MORE THAN YOUR RENT", RED))):
        k = eob((t - 2.2 - i * 0.35) / 0.35)
        if k > 0:
            w = 400 * min(k, 1); xx = 60 + i * 440; d.rounded_rectangle([xx, 450, xx + w, 540], radius=12, fill=col + (255,))
            if k > 0.9: put(im, text_img(lab, F("bebas", 44), (12, 12, 12)), xx + 200, 495)
    return im


SCENES = [("intro", 3.5, s_intro, "cut"),
 ("hook", 6.3, themed(s_hook, (4, 18, 28), (18, 64, 76), 0, orig=4, new=6.3), "flash"), ("input", 5.2, themed(s_input, (6, 26, 36), (20, 76, 90), 0, orig=4, new=5.2), "whip"), ("how", 7.0, themed(s_how, (10, 24, 28), (40, 80, 60), 0, orig=5, new=7.0), "whip"), ("stack", 6.5, themed(s_stack, (8, 20, 40), (30, 60, 120), 0), "zoom"), ("model", 6.4, themed(s_model, (4, 24, 26), (16, 90, 86), 0, orig=6, new=6.4), "glitch"),
 ("flood", 5.3, themed(s_flood, (3, 14, 40), (20, 50, 120), 1, orig=4, new=5.3), "whip"), ("chat", 3.4, themed(s_chat, (16, 16, 46), (60, 60, 140), 0, orig=5, new=3.4), "whip"), ("cost", 3.6, themed(s_cost, (32, 18, 8), (90, 56, 16), 0, orig=4, new=3.6), "whip"), ("hard", 7.1, themed(s_hard, (12, 14, 22), (50, 60, 80), 0), "glitch"), ("end", 4.2, themed(s_end, (6, 24, 32), (20, 80, 90), 0), "cut")]
TOTAL = sum(s[1] for s in SCENES)
STARTS = [sum(s[1] for s in SCENES[:i]) for i in range(len(SCENES))]
TR = 0.12

def scene_at(T):
    for i in range(len(SCENES) - 1, -1, -1):
        if T >= STARTS[i]: return i

def render(T):
    i = scene_at(T); name, dur, fn, trn = SCENES[i]; t = T - STARTS[i]; glitch = 0.0
    A = fn(t, T)
    # outgoing/incoming transition windows
    nxt = STARTS[i] + dur
    show_hdr = name not in ("intro", "end")
    if i < len(SCENES) - 1 and SCENES[i][3] != "cut" and T > nxt - TR:
        p = (T - (nxt - TR)) / (2 * TR); B = SCENES[i + 1][2](0.0, T)
        return _mix(A, B, p, trn, T, show_hdr)
    if i > 0 and SCENES[i - 1][3] != "cut" and T < STARTS[i] + TR:
        p = 0.5 + (T - STARTS[i]) / (2 * TR); Aprev = SCENES[i - 1][2](SCENES[i - 1][1], T)
        return _mix(Aprev, A, p, SCENES[i - 1][3], T, show_hdr)
    if show_hdr: hdr(A, T)
    return post(np.asarray(A), T, 0.0)

def _mix(A, B, p, kind, T, hdr_on):
    a = np.asarray(A).astype(np.float32); b = np.asarray(B).astype(np.float32); g = 0.0
    if kind == "whip":
        off = int(eio(p) * W); a2 = np.concatenate([a, b], axis=1)[:, off:off + W]; out = hblur(a2.astype(np.uint8), 50 * math.sin(math.pi * p)).astype(np.float32); g = 0.15
    elif kind == "flash":
        out = (a if p < .5 else b) * 1.0; out = out + 255 * max(0, 1 - abs(p - .5) * 5) * 0.9; g = 0.7
    elif kind == "zoom":
        z = 1 + p * 0.6; w = W / z; h = H / z; Az = A.resize((W, H), Image.BILINEAR, box=((W - w) / 2, (H - h) / 2, (W + w) / 2, (H + h) / 2))
        out = np.asarray(Az).astype(np.float32) * (1 - p) + b * p; g = 0.3
    else:
        out = a if p < .5 else b; g = 1.0
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    if hdr_on: hdr(im, T)
    return post(np.asarray(im), T, g)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "part":
        a, b = int(sys.argv[3]), int(sys.argv[4]); out = sys.argv[2]
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-vf", "gblur=sigma=0.5:steps=1",
                              "-c:v", "libx264", "-crf", "22", "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for f in range(a, b): p.stdin.write(fade_black(render(f / FPS), f / FPS, TOTAL).tobytes())
        p.stdin.close(); p.wait(); print("part done", a, b); sys.exit()
    if mode == "sheet":
        ts = [float(x) for x in sys.argv[3].split(",")]; cols = 4; rows = (len(ts) + cols - 1) // cols
        sh = Image.new("RGB", (cols * 480, rows * 360))
        for i, T in enumerate(ts):
            fr = Image.fromarray(render(T)).resize((480, 360)); ImageDraw.Draw(fr).text((6, 6), "%.1fs" % T, fill=(255, 255, 0)); sh.paste(fr, ((i % cols) * 480, (i // cols) * 360))
        sh.save(sys.argv[2], quality=88)
    else:
        out = sys.argv[2]; N = int(TOTAL * FPS)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-vf", "gblur=sigma=0.5:steps=1",
                              "-c:v", "libx264", "-crf", "24", "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for f in range(N): p.stdin.write(fade_black(render(f / FPS), f / FPS, TOTAL).tobytes())
        p.stdin.close(); p.wait(); print("video done")
