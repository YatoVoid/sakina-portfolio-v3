"""Screenshot the live baked room with the current outside city (before) and the new window view (after).

    python3 components/window_view/preview/room_preview.py [out_dir]

Serves the repo root locally; three@0.160.0 is mirrored from the npm package (no CDN in the cloud sandbox).
Views: the live site's home camera, the round-3 opening camera, two orbit extremes, a raised orbit view, and a
phone-portrait opening shot. Writes <out_dir>/<view>_<before|after>.jpg and side-by-side pairs.
"""
import http.server, threading, os, sys, math, subprocess, time
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
PKG = os.environ.get("THREE_PKG", "/tmp/three160/package")
if not os.path.exists(PKG):
    os.makedirs("/tmp/three160", exist_ok=True)
    subprocess.run("cd /tmp/three160 && npm pack three@0.160.0 --silent && tar xzf three-0.160.0.tgz", shell=True, check=True)
PREFIX = "https://cdn.jsdelivr.net/npm/three@0.160.0/"
PORT = int(os.environ.get("PORT", "7681"))

T = (-0.02, 0.92, -1.65)                       # round-3 orbit target (CRT)
def orbit(az_deg, height=0.20, dist=1.4):
    a = math.radians(az_deg)
    return (T[0] + dist * math.sin(a), T[1] + height, T[2] + dist * math.cos(a))

VIEWS = {   # name: (viewport, camera position, target)  — three.js coordinates
    "opening":       ((1280, 720), (-0.02, 1.12, -0.25), T),
    "live-home":     ((1280, 720), (0.12, 0.86, -0.30), (0.10, 0.98, -1.80)),
    "orbit-right55": ((1280, 720), orbit(55), T),
    "orbit-left50":  ((1280, 720), orbit(-50), T),
    "orbit-raised":  ((1280, 720), orbit(15, height=0.95), T),
    "phone":         ((430, 932), (-0.02, 1.12, -0.25), T),
}


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(s, *a): pass


def main():
    os.makedirs(OUT, exist_ok=True)
    http.server.SimpleHTTPRequestHandler.extensions_map[".js"] = "application/javascript"
    srv = http.server.ThreadingHTTPServer(("", PORT), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    errs = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        for mode in ("before", "after"):
            pg = b.new_page(viewport={"width": 1280, "height": 720})

            def cdn(route, req):
                f = os.path.join(PKG, req.url[len(PREFIX):].split("?")[0])
                if os.path.exists(f):
                    route.fulfill(path=f, content_type="application/wasm" if f.endswith(".wasm") else "application/javascript")
                else:
                    route.fulfill(status=404, body="missing")
            pg.route(PREFIX + "**", cdn)
            pg.on("console", lambda m: errs.append(f"{mode} {m.type}: {m.text}") if m.type == "error" else None)
            pg.on("pageerror", lambda e: errs.append(f"{mode} PAGEERROR: {e}"))
            pg.goto(f"http://localhost:{PORT}/components/window_view/preview/index.html?mode={mode}")
            pg.wait_for_function("window.ready === true", timeout=300000)
            for name, (vp, pos, tgt) in VIEWS.items():
                pg.set_viewport_size({"width": vp[0], "height": vp[1]})
                pg.evaluate("([p,t]) => window.shot(p,t)", [list(pos), list(tgt)])
                time.sleep(0.5)
                path = os.path.join(OUT, f"{name}_{mode}.png")
                pg.screenshot(path=path, timeout=300000)
                print("SHOT", path, flush=True)
            pg.close()
        b.close()
    srv.shutdown()
    for name in VIEWS:   # side-by-side pairs (before | after) as phone-friendly JPEGs
        a, c = Image.open(os.path.join(OUT, f"{name}_before.png")), Image.open(os.path.join(OUT, f"{name}_after.png"))
        horiz = a.width > a.height
        s = Image.new("RGB", (a.width, a.height * 2 + 8) if horiz else (a.width * 2 + 8, a.height), (20, 20, 20))
        s.paste(a, (0, 0)); s.paste(c, (0, a.height + 8) if horiz else (a.width + 8, 0))
        s.save(os.path.join(OUT, f"{name}_compare.jpg"), quality=88)
        c.convert("RGB").save(os.path.join(OUT, f"{name}_after.jpg"), quality=90)
    print("CONSOLE ERRORS:", errs or "none")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
