import sys, subprocess
sys.path.insert(0, "/tmp/claude-0/-home-claude/a669872b-7781-59a2-a8ce-5629bed69569/scratchpad/s")
from adlib import *
SP = '/tmp/claude-0/-home-claude/a669872b-7781-59a2-a8ce-5629bed69569/scratchpad'
PG = "/home/claude/ask-sakina-portfolio/public/project-evidence/powerguard360/"
P = lambda n: load(PG + n)
random.seed(3); np.random.seed(3)

def hdr(im, T, show=True):
    if not show: return
    d = ImageDraw.Draw(im, "RGBA")
    if int(T * 2) % 2 == 0: d.ellipse([34, 30, 50, 46], fill=RED + (255,))
    d.text((60, 24), "REC", font=F("mono", 22), fill=CREAM); d.text((W - 230, 24), "SP 0:%02d:%02d" % (int(T) // 60, int(T) % 60), font=F("mono", 22), fill=GREEN)
    for (x, y, sx, sy) in ((24, 70, 1, 1), (W - 24, 70, -1, 1), (24, H - 24, 1, -1), (W - 24, H - 24, -1, -1)):   # viewfinder corners
        d.line([(x, y), (x + 40 * sx, y)], fill=CREAM + (200,), width=3); d.line([(x, y), (x, y + 40 * sy)], fill=CREAM + (200,), width=3)


from adkit import *
LOGOIMG = Image.open(SP + "/ads/Logo_powerguard360.png").convert("RGBA")
def s_intro(t, T): return logo_intro(t, LOGOIMG, 380, (7, 12, 34), (40, 90, 230), 4.0)
def S(fn, orig, new): return lambda t, T: fn(t * orig / new, T)
def s_hook(t, T):
    bg = kenburns(P("hw-7-physical-model.jpg"), t, 4.6, (.5, .5), (.62, .45), 1.05, 1.35, dim=0.4)
    im = bg.copy()
    if t < 1.9:
        k = eob((t - 0.15) / 0.35); l1 = text_img("ONE TURBINE", F("bebas", 170), CREAM, scale=lerp(1.6, 1, k), alpha=clamp(k * 2)); l2 = text_img("FAILS.", F("bebas", 220), RED, scale=lerp(1.6, 1, eob((t - 0.55) / 0.35)), alpha=clamp((t - .55) * 4))
        put(im, l1, W / 2, 270); put(im, l2, W / 2, 470)
    else:
        k = eob((t - 1.95) / 0.35); l1 = text_img("THE AI", F("bebas", 190), CREAM, scale=lerp(1.6, 1, k), alpha=clamp(k * 2)); l2 = text_img("GOES DARK.", F("bebas", 200), AMBER, scale=lerp(1.6, 1, eob((t - 2.3) / 0.35)), alpha=clamp((t - 2.3) * 4))
        put(im, l1, W / 2, 260); put(im, l2, W / 2, 470)
    if t > 3.2:                                                       # lights out, flicker
        f = 0.0 if t > 4.0 else (1.0 if int(t * 24) % 4 < 2 else 0.25) * (1 - (t - 3.2) / 0.8)
        im = ImageEnhance.Brightness(im).enhance(max(0.0, f))
    return im

def s_problem(t, T):
    im = kenburns(P("hw-7-physical-model.jpg"), t, 5.1, (.3, .55), (.62, .5), 1.1, 1.0, dim=0.9)
    lower_third(im, t, "THE PROBLEM", ["Gas turbines power an AI data center directly.", "If one fails without warning, the computers go dark."], 0.25, 440)
    k = eob((t - 2.8) / 0.4)
    if k > 0:
        d = ImageDraw.Draw(im, "RGBA"); w = 400 * k; d.rectangle([W - 30 - w, 90, W - 30, 150], fill=(8, 8, 16, 220)); d.rectangle([W - 30 - w, 90, W - 20 - w + 0, 150], fill=AMBER + (255,))
        if k > 0.9: d.text((W - 410, 98), "BUILT IN 24 HRS", font=F("bebas", 44), fill=AMBER)
    return im

def s_title(t, T):
    k = eo3(t / 3.0)
    im = cover(P("devpost-thumbnail-3x2.jpg"), (W, H), (.5, .5), lerp(1.8, 1.0, k))
    if t < 0.4: im = ImageEnhance.Brightness(im).enhance(1 + (0.4 - t) * 4)
    l = text_img("CodeRED ORION HACKATHON", F("bebas", 46), AMBER, alpha=eo3((t - 1.0) / 0.4), spacing=6); put(im, l, W / 2, 640 - (1 - eo3((t - 1.0) / 0.4)) * -20)
    return im

def s_loop(t, T):
    im = grid_bg(t, (22, 44, 100), (7, 12, 34)); d = ImageDraw.Draw(im, "RGBA")
    l = text_img("WHY 360? IT COVERS THE WHOLE LOOP", F("bebas", 64), CREAM, alpha=eo3(t / 0.4)); put(im, l, W / 2, 110)
    names = ["SENSE", "PREDICT", "PROTECT", "SEE", "ACT", "FIX"]; bw, gap = 128, 22; x0 = (W - (6 * bw + 5 * gap)) / 2
    for i, n in enumerate(names):
        k = eob((t - 0.4 - i * 0.38) / 0.4)
        if k > 0:
            cx = x0 + i * (bw + gap) + bw / 2; cy = 330; s = k
            d.rounded_rectangle([cx - bw / 2 * s, cy - 70 * s, cx + bw / 2 * s, cy + 70 * s], radius=int(16 * s), fill=(250, 250, 255, 255), outline=BLUE + (255,), width=4)
            if k > .6:
                d.text((cx - F("bebas", 40).getlength(n) / 2, cy - 22), n, font=F("bebas", 40), fill=(20, 40, 110)); d.ellipse([cx - 16, cy - 62, cx + 16, cy - 30], fill=BLUE + (255,)); d.text((cx - 6, cy - 61), str(i + 1), font=F("mono", 22), fill=(255, 255, 255))
            if i < 5 and k > .8:
                ax = cx + bw / 2 + 2; d.polygon([(ax, 330), (ax + gap - 4, 330), (ax + gap - 12, 322), (ax + gap - 12, 338)], fill=AMBER + (255,))
    lk = clamp((t - 3.0) / 0.7)
    if lk > 0:
        yb = 450; d.line([(x0 + bw / 2, yb - 60), (x0 + bw / 2, yb), (x0 + bw / 2 + lk * (5 * (bw + gap)), yb), (x0 + bw / 2 + lk * (5 * (bw + gap)), yb - 60 * (1 if lk > .95 else 0))], fill=AMBER + (255,), width=6)
        if lk > .9:
            l = text_img("A COMPLETE SOLUTION", F("bebas", 60), AMBER, scale=eob((t - 3.6) / 0.3)); put(im, l, W / 2, 540)
    return im

def s_team(t, T):
    im = kenburns(P("leading-the-team.jpg"), t, 3.1, (.35, .55), (.55, .5), 1.0, 1.35)
    lower_third(im, t, "SAKINA LED THE TEAM", ["Undergraduates, split by each person's strengths."], 0.3, 520)
    return im

def s_models(t, T):
    bgi = kenburns(P("live-03-maintenance.png"), t, 7.1, (.5, .5), (.5, .5), 1.0, 1.1, dim=0.25).filter(ImageFilter.GaussianBlur(6))
    im = bgi.copy(); k = eob(t / 0.6)
    card = kenburns(P("live-03-maintenance.png"), t, 7.1, (.28, .30), (.22, .30), 2.6, 2.2, size=(620, 400))
    sh = Image.new("RGBA", (660, 440), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([20, 20, 640, 420], fill=(0, 0, 0, 140)); sh = sh.filter(ImageFilter.GaussianBlur(10))
    x = lerp(-600, 36, k); y = 150 + math.sin(t * 1.3) * 5
    im.paste(sh, (int(x - 10), int(y - 10)), sh); im.paste(card, (int(x), int(y)))
    ImageDraw.Draw(im).rectangle([x - 2, y - 2, x + 621, y + 401], outline=AMBER, width=3)
    l = text_img("TWO MODELS THAT EXPLAIN THEMSELVES", F("bebas", 70), CREAM, alpha=eo3(t / 0.4)); put(im, l, W / 2, 80)
    chip(im, t, 1.0, 560, "MODEL 1 · FAILURE RISK", "A calibrated risk for each turbine", GREEN, 760)
    chip(im, t, 2.6, 560 - 0, "MODEL 2 · FAILURE TYPE", "Heat, power, overstrain or tool wear", AMBER, 760) if 2.6 <= t < 4.2 else None
    if t >= 4.2: chip(im, t, 4.2, 560, "SHAP · WHY IT ALERTS", "The 3 readings behind each alert", BLUE, 760)
    return im

def s_hw(t, T):
    im = Image.new("RGB", (W, H), (10, 10, 16)); names = ["hw-1-sensor-board-setup.jpg", "hw-3-gas-leak-test.jpg", "hw-4-gas-alert-in-app.jpg"]
    labels = ["SENSOR BOARD", "GAS TEST", "ALERT IN THE APP"]; foc = [(.55, .5), (.5, .5), (.5, .45)]
    for i in range(3):
        k = eo3((t - 0.15 - i * 0.3) / 0.5)
        strip = kenburns(P(names[i]), t, 5.1, foc[i], (foc[i][0], foc[i][1]), 1.3, 1.6, size=(316, H))
        im.paste(strip, (int(i * 322), int((1 - k) * H)))
        if k > .9:
            l = text_img(labels[i], F("bebas", 40), CREAM); d = ImageDraw.Draw(im, "RGBA"); d.rectangle([i * 322, 90, i * 322 + 316, 140], fill=(8, 8, 14, 200)); put(im, l, i * 322 + 158, 116)
    lower_third(im, t, "REAL SENSORS TO LIVE ALERT", ["Readings twice a second.", "Low air quality raises a gas leak alert."], 1.4, 470, 54)
    return im

def s_3d(t, T):
    items = [("live-01-plant-3d-twin.png", (.35, .45), "Built with a Blender script."), ("live-05-turbines.png", (.5, .5), "Click any turbine: readings + diagnosis."), ("live-06-control-room.png", (.5, .5), "The control room watches the engineer walk to the turbine.")]
    k = min(2, int(t // 2)); lt = t - k * 2
    im = kenburns(P(items[k][0]), lt, 2.0, items[k][1], items[k][1], 1.0 + 0.12 * k, 1.35 + 0.1 * k)
    if lt < 0.2:                                                       # whip in
        a = np.asarray(im); off = int((1 - eio(lt / 0.2)) * W); a = hblur(np.roll(a, off, axis=1), off / 6); im = Image.fromarray(a)
    d = ImageDraw.Draw(im, "RGBA"); d.rectangle([0, 440, W, 720], fill=(6, 8, 18, 150))
    l = text_img("THE WHOLE PLANT IN 3D", F("bebas", 80), AMBER, alpha=1.0); im.paste(l, (40, 480), l)
    for i, ln in enumerate(typed([items[k][2]], lt - 0.2, 44)): d.text((46, 580 + i * 34), ln, font=F("mono", 24), fill=CREAM)
    for j in range(3): d.rectangle([46 + j * 46, 650, 46 + j * 46 + 36, 656], fill=(AMBER if j == k else (90, 90, 100)) + (255,))
    return im

def s_phone(t, T):
    im = kenburns(P("hw-6-engineer-phone-app.jpg"), t, 3.1, (.5, .5), (.5, .45), 1.1, 1.35, dim=0.8)
    sh = 6 * math.sin(t * 60) * clamp(1 - (t - 0.3) / 0.8) if 0.3 < t < 1.1 else 0
    k = eob((t - 0.25) / 0.35); d = ImageDraw.Draw(im, "RGBA")
    if k > 0:
        y = lerp(-120, 70, k); d.rectangle([40 + sh, y, W - 40 + sh, y + 100], fill=(210, 40, 40, 235)); d.text((70 + sh, y + 10), "ENGINEER ALERT", font=F("bebas", 66), fill=(255, 255, 255))
    lower_third(im, t, "FROM ALERT TO ENGINEER", ["The manager approves a repair.", "The engineer's phone buzzes with the job."], 0.9, 470, 54)
    return im

def s_results(t, T):
    bg = kenburns(P("live-05-turbines.png"), t, 6.1, (.5, .5), (.5, .5), 1.0, 1.1, dim=0.18)
    im = Image.blend(grid_bg(t, (24, 30, 60), (8, 10, 20)), bg, 0.5); d = ImageDraw.Draw(im, "RGBA")
    l = text_img("TESTED ON 2,000 READINGS IT NEVER SAW", F("bebas", 62), CREAM, alpha=eo3(t / 0.4)); put(im, l, W / 2, 90)
    stats = [("96", "%", "PRECISION", 0.96, GREEN), ("78", "%", "RECALL", 0.78, AMBER), ("0.90", "", "PR-AUC", 0.90, BLUE), ("0.93", "", "MACRO F1 · FAILURE TYPE", 0.93, (255, 120, 160))]
    for i, (v, u, lab, frac, col) in enumerate(stats):
        k = clamp((t - 0.6 - i * 0.5) / 1.3)
        if k <= 0: continue
        x = 60 + (i % 2) * 450; y = 170 + (i // 2) * 270
        val = float(v) * eo3(k); txt = ("%d" % round(val) + u) if u else "%.2f" % val
        sc = 1 + 0.12 * (1 - clamp((t - 0.6 - i * 0.5 - 1.3) / 0.3)) if k >= 1 else 1
        lay = text_img(txt, F("bebas", int(170 * sc)), col); im.paste(lay, (x, y), lay)
        d.text((x + 8, y + 175), lab, font=F("mono", 22), fill=CREAM)
        d.rectangle([x + 8, y + 214, x + 8 + 380, y + 224], fill=(60, 60, 80, 255)); d.rectangle([x + 8, y + 214, x + 8 + 380 * frac * eo3(k), y + 224], fill=col + (255,))
    return im

def s_award(t, T):
    im = kenburns(P("award-500-best-pitch.jpg"), t, 4.1, (.5, .5), (.5, .5), 1.55, 1.0, dim=1.0)
    if t < 0.3: im = ImageEnhance.Brightness(im).enhance(1 + (0.3 - t) * 6)
    d = ImageDraw.Draw(im, "RGBA"); d.rectangle([0, 500, W, 720], fill=(6, 6, 14, 190))
    k1 = eob((t - 0.5) / 0.4); k2 = eob((t - 1.2) / 0.4)
    put(im, text_img("2ND OF 70+ TEAMS", F("bebas", 110), AMBER, scale=lerp(1.5, 1, k1), alpha=clamp(k1 * 2)), W / 2, 570)
    put(im, text_img("$500 · BEST PITCH/DEMO", F("bebas", 64), CREAM, scale=lerp(1.5, 1, k2), alpha=clamp(k2 * 2)), W / 2, 660)
    rng = random.Random(11)                                            # confetti
    for i in range(60):
        x0 = rng.random() * W; sp = 120 + rng.random() * 220; ph = rng.random() * 6; col = [AMBER, GREEN, BLUE, RED, CREAM][i % 5]
        y = ((t * sp + rng.random() * 800) % 900) - 120; x = x0 + 30 * math.sin(t * 3 + ph)
        if t > 0.4: d.rectangle([x, y, x + 9, y + 16 * abs(math.sin(t * 6 + ph)) + 3], fill=col + (230,))
    return im

def s_pitch(t, T):
    im = Image.new("RGB", (W, H), (8, 8, 14))
    for i, (n, f) in enumerate((("pitching-to-judges.jpg", (.5, .4)), ("presenting-demo.jpg", (.5, .42)))):
        k = eo3((t - 0.1 - i * 0.2) / 0.4); p = kenburns(P(n), t, 2.1, f, f, 1.0, 1.2, size=(476, H))
        im.paste(p, (int(i * 484 + (1 - k) * (-1 if i == 0 else 1) * 600), 0))
    d = ImageDraw.Draw(im, "RGBA"); d.rectangle([0, 600, W, 700], fill=(6, 6, 14, 200)); put(im, text_img("PITCHING TO THE JUDGES", F("bebas", 70), CREAM), W / 2, 650)
    return im


SCENES = [("intro", 4.0, s_intro, "cut"), ("hook", 4.0, s_hook, "flash"), ("problem", 6.0, S(s_problem, 5, 6.0), "whip"), ("title", 3.2, S(s_title, 3, 3.2), "glitch"),
          ("loop", 4.4, S(s_loop, 4, 4.4), "whip"), ("team", 3.4, S(s_team, 3, 3.4), "whip"), ("models", 7.2, S(s_models, 7, 7.2), "zoom"), ("hw", 5.0, s_hw, "whip"),
          ("3d", 5.6, S(s_3d, 6, 5.6), "flash"), ("phone", 3.0, s_phone, "whip"), ("results", 6.5, S(s_results, 6, 6.5), "glitch"), ("award", 4.6, S(s_award, 4, 4.6), "whip"),
          ("pitch", 3.0, S(s_pitch, 2, 3.0), "cut")]
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
