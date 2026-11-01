"""Screenshot the real site (served locally) from candidate cameras.
    python3 camera_shots.py <web_dir> <out_prefix> '<json list of {name,pos,target,fov}>' [WxH]
pos/target are three.js coords (Y up). Uses the site's own renderer, GLBs and lightmaps."""
import http.server, threading, os, sys, json, time, subprocess
from playwright.sync_api import sync_playwright

WEB, OUT, CANDS = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
W, H = (int(v) for v in (sys.argv[4] if len(sys.argv) > 4 else "1915x866").split("x"))
PKG = os.environ.get("THREE_PKG", "/tmp/three160/package")
if not os.path.exists(PKG):
    os.makedirs("/tmp/three160", exist_ok=True)
    subprocess.run("cd /tmp/three160 && npm pack three@0.160.0 --silent && tar xzf three-0.160.0.tgz", shell=True, check=True)
PREFIX = "https://cdn.jsdelivr.net/npm/three@0.160.0/"
PORT = int(os.environ.get("PORT", "7681"))


class Hd(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=WEB, **k)
    def log_message(s, *a): pass


http.server.SimpleHTTPRequestHandler.extensions_map[".js"] = "application/javascript"
srv = http.server.ThreadingHTTPServer(("", PORT), Hd)
threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": W, "height": H})
    pg.route(PREFIX + "**", lambda r, q: r.fulfill(path=os.path.join(PKG, q.url[len(PREFIX):].split("?")[0]),
             content_type="application/wasm" if q.url.endswith(".wasm") else "application/javascript"))
    pg.route("**/main.js*", lambda r, q: r.fulfill(body=open(os.path.join(WEB, "main.js")).read() + "\nwindow.__dbg={camera,controls,scene,THREE};\n",
                                                  content_type="application/javascript"))
    pg.route("https://fonts.**", lambda r, q: r.fulfill(status=200, body=""))
    pg.goto(f"http://localhost:{PORT}/")
    pg.wait_for_function("!document.getElementById('loader')", timeout=300000)
    time.sleep(2)
    for c in CANDS:
        pg.evaluate("""(c)=>{const {camera,controls}=window.__dbg; if(c.pos){camera.position.set(...c.pos);controls.target.set(...c.target);
            camera.fov=c.fov;camera.updateProjectionMatrix();controls.update();} if(c.js){(new Function('d',c.js))(window.__dbg);}}""", c)
        time.sleep(1.5)
        pg.screenshot(path=f"{OUT}_{c['name']}.png", timeout=300000)
        print("SHOT", c["name"], flush=True)
    b.close()
srv.shutdown()
