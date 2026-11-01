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



EV = "/home/claude/ask-sakina-portfolio/public/project-evidence/"
UHRED = (200, 16, 46); DK = (16, 6, 9); LN = (70, 22, 30)
def bg(t): return grid_bg(t, LN, DK)
def title(im, t, txt, y=90, size=80, col=CREAM, t0=0.1):
    k = eob((t - t0) / 0.4); put(im, text_img(txt, F("bebas", size), col, scale=lerp(1.4, 1, k), alpha=clamp(k * 2)), W / 2, y)
def rgb(p): return Image.open(p).convert("RGBA").convert("RGB")
SHOT = {n: rgb(EV + n) for n in ("cost-center-verification/manager-review.png", "cost-center-verification/dba-resolve.png", "financial-reconciliation/power-automate-notifications.png")}
UHL = Image.open(SP + "/ads/Logo_uh_card.png").convert("RGBA").resize((792, 255), Image.LANCZOS)
def mosaic(im, px):
    if px <= 1: return im
    w, h = im.size; return im.resize((max(1, int(w / px)), max(1, int(h / px))), Image.BILINEAR).resize((w, h), Image.NEAREST)
def uh_card(t, base=None):                                          # logo resolves from big pixels to sharp, with a red scan sweep
    im = base if base is not None else bg(t)
    k = clamp(t / 1.5); px = lerp(46, 1, eo3(k)); card_ = Image.new("RGBA", UHL.size, (0, 0, 0, 0)); card_.alpha_composite(UHL)
    lay = mosaic(card_, px); a = clamp(t / 0.35)
    lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    d = ImageDraw.Draw(im, "RGBA"); cx, cy = W / 2, 250
    sweep = lerp(-80, W + 80, eio((t - 0.3) / 1.2))
    if 0 < t < 1.7: d.rectangle([sweep - 14, 80, sweep + 14, 420], fill=UHRED + (150,)); d.rectangle([sweep - 3, 80, sweep + 3, 420], fill=(255, 200, 205, 230))
    put(im, lay, cx, cy); return im


from PIL import ImageFilter, ImageChops
TOTAL = 59.5
def fade(a, T):
    u = clamp((TOTAL - T) / 1.9); k = u * u * (3 - 2 * u)
    return a if k >= 1 else (a.astype(np.float32) * k).astype(np.uint8)
def s_intro(t, T):                                                   # just the UH logo: soft glow, slow rise, one light sheen
    im = Image.new("RGB", (W, H), DK); d = ImageDraw.Draw(im, "RGBA")
    g = Image.new("RGB", (W, H), (0, 0, 0)); gd = ImageDraw.Draw(g); pulse = 0.75 + 0.25 * math.sin(t * 2.2)
    gd.ellipse([W / 2 - 330, 360 - 150, W / 2 + 330, 360 + 150], fill=(int(120 * pulse * eo3(t / 1.4)), 8, 22)); g = g.filter(ImageFilter.GaussianBlur(70)); im = ImageChops.add(im, g)
    k = eo3(t / 2.2); sc = lerp(0.88, 1.0, k); lay = UHL.resize((int(UHL.width * sc), int(UHL.height * sc)), Image.LANCZOS); a = clamp(t / 1.1)
    arr = np.array(lay).astype(np.float32); sx = lerp(-200, lay.width + 200, eio((t - 1.3) / 1.4))
    if 1.3 < t < 2.7:
        xs = np.arange(lay.width)[None, :] + np.arange(lay.height)[:, None] * 0.6; band = np.exp(-((xs - sx) / 40.0) ** 2)[..., None]; arr[..., :3] = np.clip(arr[..., :3] + band * 90, 0, 255)
    lay = Image.fromarray(arr.astype(np.uint8)); lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a))); put(im, lay, W / 2, 360)
    if t > 3.0: im = ImageEnhance.Brightness(im).enhance(max(0.0, 1 - (t - 3.0) / 0.5))
    return im

def s_hook(t, T):
    im = bg(t)
    if t < 4.2:
        put(im, text_img("SAKINA SAIFUDDIN", F("bebas", 150), CREAM, scale=lerp(1.4, 1, eob((t - 0.3) / 0.4)), alpha=clamp((t - 0.3) * 4)), W / 2, 250)
        put(im, text_img("RESEARCH ASSISTANT", F("bebas", 100), AMBER, scale=lerp(1.4, 1, eob((t - 1.2) / 0.4)), alpha=clamp((t - 1.2) * 4)), W / 2, 380)
        put(im, text_img("UNIVERSITY OF HOUSTON", F("mono", 28), (255, 120, 135), alpha=eo3((t - 2.2) / 0.5), spacing=4), W / 2, 480)
    else:
        u = t - 4.4; put(im, text_img("THE PROFESSORS", F("bebas", 150), CREAM, scale=lerp(1.5, 1, eob(u / 0.35)), alpha=clamp(u * 4)), W / 2, 250)
        put(im, text_img("HAD A PROBLEM.", F("bebas", 170), RED, scale=lerp(1.5, 1, eob((u - 0.7) / 0.35)), alpha=clamp((u - 0.7) * 4)), W / 2, 430)
        put(im, text_img("EVERY MONTH.", F("mono", 30), AMBER, alpha=eo3((u - 2.0) / 0.4), spacing=4), W / 2, 560)
    return im

def s_policy(t, T):
    im = bg(t); d = ImageDraw.Draw(im, "RGBA")
    if t < 3.4:
        k = eo3((t - 0.15) / 0.4); d.rounded_rectangle([int(80 - (1 - k) * 900), 130, int(880 - (1 - k) * 900), 600], radius=16, fill=(30, 10, 14, 235), outline=UHRED + (255,), width=4)
        if k > 0.95:
            put(im, text_img("UH POLICY  MAPP 05.04.02", F("mono", 30), (255, 120, 135), alpha=eo3((t - 0.5) / 0.3)), W / 2, 190)
            put(im, text_img("EVERY ACTIVE COST CENTER.", F("bebas", 100), CREAM, alpha=eo3((t - 0.8) / 0.3)), W / 2, 310)
            put(im, text_img("VERIFIED. EVERY MONTH.", F("bebas", 112), AMBER, alpha=eo3((t - 1.5) / 0.3)), W / 2, 450)
    elif t < 6.6:
        u = t - 3.4
        for i, w_ in enumerate(("REPORTS.", "EMAILS.", "FOLLOW-UPS.")):
            k = eob((u - 0.1 - i * 0.7) / 0.35); put(im, text_img(w_, F("bebas", 130), CREAM, scale=lerp(1.5, 1, k), alpha=clamp(k * 2)), W / 2, 190 + i * 150)
            if u > 2.5 + i * 0.1: ww = 520 * eo3((u - 2.5 - i * 0.1) / 0.2); d.rectangle([W / 2 - ww / 2, 190 + i * 150 - 4, W / 2 + ww / 2, 190 + i * 150 + 6], fill=UHRED + (255,))
    else:
        u = t - 6.6
        for i, (w_, t0, col) in enumerate((("WHO HAD FINISHED?", 0.2, CREAM), ("WHAT WAS FLAGGED?", 2.0, AMBER), ("WAS IT FIXED?", 3.2, RED))):
            k = eob((u - t0) / 0.35); put(im, text_img(w_, F("bebas", 120), col, scale=lerp(1.4, 1, k), alpha=clamp(k * 2)), W / 2, 200 + i * 150)
    return im

def shot(name, t, dur, c0, c1, y=70, vw=880, vh=380):
    s = SHOT[name]; u = eio(t / dur); x0, y0, w0 = [lerp(a, b, u) for a, b in zip(c0, c1)]; h0 = w0 * vh / vw
    cr = s.resize((vw, vh), Image.LANCZOS, box=(x0, y0, x0 + w0, y0 + h0)); im = bg(t); ImageDraw.Draw(im, "RGBA").rounded_rectangle([W / 2 - vw / 2 - 8, y - 8, W / 2 + vw / 2 + 8, y + vh + 8], radius=12, fill=UHRED + (255,))
    im.paste(cr, (int(W / 2 - vw / 2), y)); return im

def s_stack(t, T):
    im = bg(t); title(im, t, "SAKINA BUILT IT WITH", 80, 76); d = ImageDraw.Draw(im, "RGBA")
    rows = [(170, [("POWER APPS", 280), ("POWER FX", 280), ("SHAREPOINT", 280)]), (290, [("POWER AUTOMATE", 420), ("POWER BI", 420)]), (410, [("PEOPLESOFT", 420), ("JSON", 420)])]
    n = 0
    for y, chips in rows:
        tot = sum(w for _, w in chips) + 20 * (len(chips) - 1); x = W / 2 - tot / 2
        for nm, w in chips:
            k = eob((t - 0.4 - n * 0.3) / 0.35); n += 1
            if k > 0:
                ww = max(4, w * min(k, 1)); d.rounded_rectangle([x, y, x + ww, y + 92], radius=12, fill=(30, 10, 14, 245), outline=UHRED + (255,), width=4)
                if k > 0.9: put(im, text_img(nm, F("bebas", 56), CREAM), x + w / 2, y + 46)
            x += w + 20
    put(im, text_img("A ROLE-BASED CANVAS APP FOR THE CULLEN COLLEGE OF ENGINEERING", F("mono", 19), AMBER, alpha=eo3((t - 3.0) / 0.5)), W / 2, 560)
    return im

def _chips(t, T):
    im = bg(t); title(im, t, "SAKINA BUILT IT WITH", 80, 76); d = ImageDraw.Draw(im, "RGBA")
    rows = [(170, [("POWER APPS", 280), ("POWER FX", 280), ("SHAREPOINT", 280)]), (290, [("POWER AUTOMATE", 420), ("POWER BI", 420)]), (410, [("PEOPLESOFT", 420), ("JSON", 420)])]
    n = 0
    for y, chips in rows:
        tot = sum(w for _, w in chips) + 20 * (len(chips) - 1); x = W / 2 - tot / 2
        for nm, w in chips:
            k = eob((t - 0.4 - n * 0.3) / 0.35); n += 1
            if k > 0:
                ww = max(4, w * min(k, 1)); d.rounded_rectangle([x, y, x + ww, y + 92], radius=12, fill=(30, 10, 14, 245), outline=UHRED + (255,), width=4)
                if k > 0.9: put(im, text_img(nm, F("bebas", 56), CREAM), x + w / 2, y + 46)
            x += w + 20
    put(im, text_img("A ROLE-BASED CANVAS APP FOR THE CULLEN COLLEGE OF ENGINEERING", F("mono", 19), AMBER, alpha=eo3((t - 3.0) / 0.5)), W / 2, 560)
    return im


def s_stack(t, T):
    if t < 2.5:
        im = bg(t); k = eob((t - 0.1) / 0.4); put(im, text_img("SO SAKINA SUGGESTED", F("bebas", 120), CREAM, scale=lerp(1.5, 1, k), alpha=clamp(k * 2)), W / 2, 270)
        k2 = eob((t - 0.6) / 0.4); put(im, text_img("A BETTER WAY.", F("bebas", 190), AMBER, scale=lerp(1.5, 1, k2), alpha=clamp((t - 0.6) * 4)), W / 2, 450)
        return im
    return _chips(t - 2.5, T)

def s_manager(t, T):
    im = shot("cost-center-verification/manager-review.png", t, 5.0, (0, 5, 1300), (60, 110, 780))
    lower_third(im, t, "SAKINA DESIGNED THE MANAGER SCREEN", ["Yes or No on every cost center.", "A No needs a comment."], 0.4, 470)
    return im
def s_dba(t, T):
    im = shot("cost-center-verification/dba-resolve.png", t, 4.0, (0, 0, 1320), (420, 60, 800))
    lower_third(im, t, "AND THE DBA SCREEN", ["Only the flagged cost centers.", "Records how each one was fixed."], 0.3, 470)
    return im

def s_flow(t, T):
    im = bg(t); title(im, t, "SAKINA BUILT THE RULES IN.", 80, 72); d = ImageDraw.Draw(im, "RGBA")
    names = [("INITIATED", ""), ("PENDING", "CCM REVIEW"), ("PENDING", "DBA REVIEW"), ("VERIFY/CERTIFY", "COMPLETE")]
    for i, (a, b) in enumerate(names):
        k = eob((t - 0.3 - i * 0.45) / 0.4); x = 20 + i * 240
        if k > 0:
            w = 200 * min(k, 1); col = GREEN if i == 3 else UHRED
            d.rounded_rectangle([x, 200, x + w, 340], radius=12, fill=(30, 10, 14, 245), outline=col + (255,), width=4)
            if k > 0.9:
                put(im, text_img(a, F("bebas", 34), CREAM), x + 100, 250 if b else 270)
                if b: put(im, text_img(b, F("bebas", 34), CREAM), x + 100, 292)
        if i < 3 and t > 0.6 + i * 0.45:
            kk = clamp((t - 0.8 - i * 0.55) / 0.3); d.line([(x + 205, 270), (x + 205 + 30 * kk, 270)], fill=AMBER + (255,), width=5)
            if kk >= 1: d.polygon([(x + 237, 270), (x + 222, 260), (x + 222, 280)], fill=AMBER + (255,))
    k = eob((t - 2.1) / 0.4)
    if k > 0:
        d.rounded_rectangle([90, 420, 870, 500], radius=10, fill=(30, 10, 14, 240), outline=GREEN + (255,), width=3); put(im, text_img("ALL YES? THE REVIEW COMPLETES AT ONCE.", F("bebas", 52), GREEN), W / 2, 460)
    k = eob((t - 2.8) / 0.4)
    if k > 0:
        d.rounded_rectangle([90, 530, 870, 610], radius=10, fill=(30, 10, 14, 240), outline=AMBER + (255,), width=3); put(im, text_img("LOCKED ONCE SUBMITTED. A CLEAN AUDIT TRAIL.", F("bebas", 52), AMBER), W / 2, 570)
    return im


def s_hard(t, T):
    im = bg(t); title(im, t, "THE HARD PART", 70, 84, AMBER); d = ImageDraw.Draw(im, "RGBA")
    L = [(80, 135 + i * 64) for i in range(4)]; Rr = [(660, 150 + i * 84) for i in range(3)]
    for i, (x, y) in enumerate(L):
        k = eo3((t - 0.3 - i * 0.12) / 0.3)
        if k > 0: d.rounded_rectangle([x, y, x + 220 * k, y + 52], radius=8, fill=(30, 10, 14, 245), outline=CREAM + (255,), width=2); put(im, text_img("DEPARTMENT %d" % (i + 1), F("bebas", 30), CREAM, alpha=k), x + 110, y + 26) if k > 0.9 else None
    for i, (x, y) in enumerate(Rr):
        k = eo3((t - 0.5 - i * 0.12) / 0.3)
        if k > 0: d.rounded_rectangle([x, y, x + 220 * k, y + 52], radius=8, fill=(30, 10, 14, 245), outline=AMBER + (255,), width=2); put(im, text_img("DBA %s" % "ABC"[i], F("bebas", 30), AMBER, alpha=k), x + 110, y + 26) if k > 0.9 else None
    for j, (a, b) in enumerate(((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 2), (3, 0))):
        k = clamp((t - 0.9 - j * 0.15) / 0.3)
        if k > 0: (x0, y0), (x1, y1) = (L[a][0] + 220, L[a][1] + 26), (Rr[b][0], Rr[b][1] + 26); d.line([(x0, y0), (lerp(x0, x1, k), lerp(y0, y1, k))], fill=(255, 120, 135, 230), width=3)
    put(im, text_img("MANY-TO-MANY", F("bebas", 54), CREAM, alpha=eo3((t - 2.2) / 0.3)), W / 2, 420) if t > 2.2 else None
    for i, txt in enumerate(("STORED AS A DELIMITED LIST OF DBA EMAILS", "ANY LISTED DBA CAN RESOLVE", "FILTERED BY STATUS FIRST, SO THE QUERY STAYS DELEGABLE")):
        k = eob((t - 2.9 - i * 0.7) / 0.35)
        if k > 0:
            d.rounded_rectangle([60, 470 + i * 62, 60 + 840 * min(k, 1), 470 + i * 62 + 52], radius=8, fill=(30, 10, 14, 240), outline=GREEN + (255,), width=3)
            if k > 0.9: d.text((84, 470 + i * 62 + 8), "\u2713 " if False else "OK", font=F("mono", 22), fill=GREEN); put(im, text_img(txt, F("bebas", 36), CREAM), 60 + 435, 470 + i * 62 + 26)
    return im

def s_auto(t, T):
    im = bg(t); title(im, t, "FIVE POWER AUTOMATE FLOWS", 70, 70); k = eo3((t - 0.2) / 0.4); s = SHOT["financial-reconciliation/power-automate-notifications.png"]
    vw, vh = 480, 400; u = eio(t / 4.0); w0 = 681 * vw / vh; x0 = lerp(100, 1238 - w0, u)
    cr = s.resize((vw, vh), Image.LANCZOS, box=(x0, 0, x0 + w0, 681))
    d = ImageDraw.Draw(im, "RGBA"); x = int(50 - (1 - k) * 600); d.rounded_rectangle([x - 8, 142, x + vw + 8, 142 + vh + 16], radius=10, fill=UHRED + (255,)); im.paste(cr, (x, 150))
    for i, nm in enumerate(("SUBMIT REVIEW", "DBA RESOLVE", "STATUS EMAILS", "WEEKLY REMINDERS", "MONTHLY DATA REFRESH")):
        kk = eob((t - 0.6 - i * 0.28) / 0.35)
        if kk > 0:
            w = 360 * min(kk, 1); y = 140 + i * 78; d.rounded_rectangle([570, y, 570 + w, y + 62], radius=10, fill=(30, 10, 14, 245), outline=AMBER + (255,), width=3)
            if kk > 0.9: put(im, text_img(nm, F("bebas", 38), CREAM), 570 + 180, y + 31)
    return im

def s_auto(t, T):
    im = bg(t); title(im, t, "FIVE POWER AUTOMATE FLOWS", 70, 70); k = eo3((t - 0.2) / 0.4); s = SHOT["financial-reconciliation/power-automate-notifications.png"]
    vw, vh = 480, 400; u = eio(t / 4.0); w0 = 681 * vw / vh; x0 = lerp(100, 1238 - w0, u)
    cr = s.resize((vw, vh), Image.LANCZOS, box=(x0, 0, x0 + w0, 681))
    d = ImageDraw.Draw(im, "RGBA"); x = int(50 - (1 - k) * 600); d.rounded_rectangle([x - 8, 142, x + vw + 8, 142 + vh + 16], radius=10, fill=UHRED + (255,)); im.paste(cr, (x, 150))
    for i, nm in enumerate(("SUBMIT REVIEW", "DBA RESOLVE", "STATUS EMAILS", "WEEKLY REMINDERS", "MONTHLY DATA REFRESH")):
        kk = eob((t - 0.6 - i * 0.28) / 0.35)
        if kk > 0:
            w = 360 * min(kk, 1); y = 140 + i * 78; d.rounded_rectangle([570, y, 570 + w, y + 62], radius=10, fill=(30, 10, 14, 245), outline=AMBER + (255,), width=3)
            if kk > 0.9: put(im, text_img(nm, F("bebas", 38), CREAM), 570 + 180, y + 31)
    return im

def s_impact(t, T):
    im = bg(t); d = ImageDraw.Draw(im, "RGBA")
    for r_ in range(3):
        rr = ((t * 260 + r_ * 150) % 450); d.ellipse([W / 2 - rr, 270 - rr, W / 2 + rr, 270 + rr], outline=UHRED + (int(160 * (1 - rr / 450)),), width=3)
    v = int(150 * eo3((t - 0.2) / 1.1)); put(im, text_img("%d+" % v, F("bebas", 360), AMBER, scale=1.0 + 0.08 * max(0, 1 - (t - 1.3) * 3)), W / 2, 260)
    put(im, text_img("PROFESSORS", F("bebas", 130), CREAM, alpha=eo3((t - 1.0) / 0.4)), W / 2, 470)
    put(im, text_img("USE SAKINA'S APP TODAY", F("mono", 28), GREEN, alpha=eo3((t - 1.7) / 0.4)), W / 2, 560)
    return im


SCENES = [("intro", 3.5, s_intro, "cut"), ("hook", 8.0, s_hook, "glitch"), ("policy", 11.0, s_policy, "whip"), ("stack", 7.5, s_stack, "zoom"), ("manager", 5.0, s_manager, "whip"),
          ("dba", 4.0, s_dba, "zoom"), ("flow", 5.0, s_flow, "whip"), ("hard", 6.5, s_hard, "glitch"), ("auto", 3.3, s_auto, "whip"), ("impact", 5.7, s_impact, "cut")]
assert abs(sum(s[1] for s in SCENES) - 59.5) < 1e-6
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
        for f in range(a, b): p.stdin.write(fade(render(f / FPS), f / FPS).tobytes())
        p.stdin.close(); p.wait(); print("part done", a, b); sys.exit()
    if mode == "sheet":
        ts = [float(x) for x in sys.argv[3].split(",")]; cols = 4; rows = (len(ts) + cols - 1) // cols
        sh = Image.new("RGB", (cols * 480, rows * 360))
        for i, T in enumerate(ts):
            fr = Image.fromarray(render(T)).resize((480, 360)); ImageDraw.Draw(fr).text((6, 6), "%.1fs" % T, fill=(255, 255, 0)); sh.paste(fr, ((i % cols) * 480, (i // cols) * 360))
        sh.save(sys.argv[2], quality=88)
    else:
        out = sys.argv[2]; N = int(59.5 * FPS)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-vf", "gblur=sigma=0.5:steps=1",
                              "-c:v", "libx264", "-crf", "24", "-preset", "veryfast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        for f in range(N): p.stdin.write(fade(render(f / FPS), f / FPS).tobytes())
        p.stdin.close(); p.wait(); print("video done")
