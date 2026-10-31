"""Click every tape spine in the running site and check the project panel that opens.
Usage: python3 tape_click_test.py <web_dir> <tapes.json> [screenshot_prefix]
Serves web_dir locally, mirrors three@0.160.0 from the npm package (cloud sandbox has no CDN access)."""
import http.server, threading, os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright

WEB, TAPES = sys.argv[1], json.load(open(sys.argv[2]))
SHOT = sys.argv[3] if len(sys.argv) > 3 else None
PKG = os.environ.get("THREE_PKG", "/tmp/three160/package")
if not os.path.exists(PKG):
    os.makedirs("/tmp/three160", exist_ok=True)
    subprocess.run("cd /tmp/three160 && npm pack three@0.160.0 --silent && tar xzf three-0.160.0.tgz", shell=True, check=True)
PREFIX = "https://cdn.jsdelivr.net/npm/three@0.160.0/"
PORT = int(os.environ.get("PORT", "7671"))


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=WEB, **k)
    def log_message(s, *a): pass


http.server.SimpleHTTPRequestHandler.extensions_map[".js"] = "application/javascript"
srv = http.server.ThreadingHTTPServer(("", PORT), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
titles = json.loads(subprocess.run(["node", "-e", f"import('{WEB}/content.js').then(m=>console.log(JSON.stringify(m.projects.map(p=>p.title))))"],
                                   capture_output=True, text=True).stdout)
errs, fails = [], 0
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1280, "height": 720})

    def cdn(route, req):
        f = os.path.join(PKG, req.url[len(PREFIX):].split("?")[0])
        if os.path.exists(f):
            route.fulfill(path=f, content_type="application/wasm" if f.endswith(".wasm") else "application/javascript")
        else:
            route.fulfill(status=404, body="missing")

    def expose(route, req):  # test-only: expose camera so 3D points can be projected to screen pixels
        body = open(os.path.join(WEB, "main.js")).read()
        body += "\nwindow.__dbg={camera,THREE};\n"
        route.fulfill(body=body, content_type="application/javascript")
    pg.route(PREFIX + "**", cdn)
    pg.route("**/main.js*", expose)
    pg.route("https://fonts.**", lambda r, q: r.fulfill(status=200, body=""))
    pg.on("console", lambda m: errs.append(f"{m.type}: {m.text}") if m.type == "error" else None)
    pg.on("pageerror", lambda e: errs.append("PAGEERROR: " + str(e)))
    pg.goto(f"http://localhost:{PORT}/")
    pg.wait_for_function("!document.getElementById('loader') || document.getElementById('loader-text').textContent.includes('FAILED')", timeout=240000)
    time.sleep(2)
    state = pg.evaluate("document.getElementById('loader')?document.getElementById('loader-text').textContent:'loaded'")
    print("LOAD:", state)
    pg.keyboard.press("t"); time.sleep(2.5)
    if SHOT:
        pg.screenshot(path=SHOT + "_tapes_view.png", timeout=300000)
    for t in TAPES:
        xy = pg.evaluate("""([x,y,z])=>{const {camera,THREE}=window.__dbg;const v=new THREE.Vector3(x,y,z).project(camera);
            const r=document.getElementById('scene').getBoundingClientRect();return [r.left+(v.x+1)/2*r.width, r.top+(1-v.y)/2*r.height]}""", t["spine"])
        pg.mouse.move(xy[0], xy[1]); pg.mouse.down(); pg.mouse.up(); time.sleep(0.6)
        got = pg.evaluate("document.getElementById('panel').hidden?null:document.getElementById('panel-title').textContent")
        want = titles[t["idx"]]
        ok = got == want
        fails += not ok
        print(f"{'OK  ' if ok else 'FAIL'} tape {t['idx']:2} {t['object']:17} screen=({xy[0]:.0f},{xy[1]:.0f}) expected={want!r} got={got!r}")
    print("CONSOLE ERRORS:", [e for e in errs if "TUNNEL" not in e] or "none")
    print(f"RESULT: {13 - fails}/13 tapes open the right project")
    b.close()
srv.shutdown()
sys.exit(1 if fails else 0)
