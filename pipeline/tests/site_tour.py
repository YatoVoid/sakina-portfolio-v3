"""Drive the real site like a visitor and screenshot it: preset views by key (T tapes, I IBM PC, N notepad, Z desk) and orbit by mouse drag.
    python3 site_tour.py <abs_web_dir> <out_prefix> [WxH]
Serves web_dir locally, mirrors three@0.160.0 from npm (cloud sandbox has no CDN access)."""
import http.server, threading, os, sys, time, subprocess
from playwright.sync_api import sync_playwright

WEB, OUT = sys.argv[1], sys.argv[2]
W, H = (int(v) for v in (sys.argv[3] if len(sys.argv) > 3 else "1600x900").split("x"))
PKG = os.environ.get("THREE_PKG", "/tmp/three160/package")
if not os.path.exists(PKG):
    os.makedirs("/tmp/three160", exist_ok=True)
    subprocess.run("cd /tmp/three160 && npm pack three@0.160.0 --silent && tar xzf three-0.160.0.tgz", shell=True, check=True)
PREFIX = "https://cdn.jsdelivr.net/npm/three@0.160.0/"
PORT = int(os.environ.get("PORT", "7691"))


class Hd(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=WEB, **k)
    def log_message(s, *a): pass


http.server.SimpleHTTPRequestHandler.extensions_map[".js"] = "application/javascript"
srv = http.server.ThreadingHTTPServer(("", PORT), Hd)
threading.Thread(target=srv.serve_forever, daemon=True).start()
errs = []
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": W, "height": H})
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route(PREFIX + "**", lambda r, q: r.fulfill(path=os.path.join(PKG, q.url[len(PREFIX):].split("?")[0]),
             content_type="application/wasm" if q.url.endswith(".wasm") else "application/javascript"))
    pg.route("https://fonts.**", lambda r, q: r.fulfill(status=200, body=""))
    pg.goto(f"http://localhost:{PORT}/")
    pg.wait_for_function("!document.getElementById('loader')", timeout=300000)
    time.sleep(3)

    def shot(n):
        time.sleep(3.5)
        pg.screenshot(path=f"{OUT}_{n}.png", timeout=300000)
        print("SHOT", n, flush=True)

    def drag(dx, dy):
        pg.mouse.move(W / 2, H / 2); pg.mouse.down()
        for i in range(1, 21):
            pg.mouse.move(W / 2 + dx * i / 20, H / 2 + dy * i / 20); time.sleep(0.03)
        pg.mouse.up()

    shot("home")
    drag(-1400, 0); shot("orbit_a")
    drag(2800, 0); shot("orbit_b")
    pg.keyboard.press("Escape"); shot("home_again")
    for k, n in (("z", "desk"), ("i", "ibm"), ("n", "notepad"), ("t", "tapes")):
        pg.keyboard.press(k); shot(n)
    pg.keyboard.press("Escape"); time.sleep(2)
    wheel = [("out", 600), ("in", -900)]
    print("CONSOLE ERRORS:", errs[:5] or "none")
    b.close()
srv.shutdown()
