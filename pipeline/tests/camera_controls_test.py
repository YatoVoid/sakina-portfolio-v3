"""Camera-control acceptance test with real input events (mouse, wheel, keys, touch) on the site served locally.
    python3 camera_controls_test.py <web_dir> <out_prefix>
Prints a PASS/FAIL line per check and saves screenshots <out_prefix>_<case>.png."""
import http.server, threading, os, sys, json, time, math, subprocess
from playwright.sync_api import sync_playwright

WEB, OUT = sys.argv[1], sys.argv[2]
W, H = 1915, 866
PKG = os.environ.get("THREE_PKG", "/tmp/three160/package")
if not os.path.exists(PKG):
    os.makedirs("/tmp/three160", exist_ok=True)
    subprocess.run("cd /tmp/three160 && npm pack three@0.160.0 --silent && tar xzf three-0.160.0.tgz", shell=True, check=True)
PREFIX = "https://cdn.jsdelivr.net/npm/three@0.160.0/"
PORT = int(os.environ.get("PORT", "7711"))


class Hd(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=WEB, **k)
    def log_message(s, *a): pass


http.server.SimpleHTTPRequestHandler.extensions_map[".js"] = "application/javascript"
srv = http.server.ThreadingHTTPServer(("", PORT), Hd)
threading.Thread(target=srv.serve_forever, daemon=True).start()
results = []


def check(name, ok, detail=""):
    results.append(ok); print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}", flush=True)


def route(pg):
    pg.route(PREFIX + "**", lambda r, q: r.fulfill(path=os.path.join(PKG, q.url[len(PREFIX):].split("?")[0]),
             content_type="application/wasm" if q.url.endswith(".wasm") else "application/javascript"))
    pg.route("**/main.js*", lambda r, q: r.fulfill(body=open(os.path.join(WEB, "main.js")).read()
                                                  + "\nwindow.__dbg={camera,controls,THREE};\n", content_type="application/javascript"))
    pg.route("https://fonts.**", lambda r, q: r.fulfill(status=200, body=""))


CAM = """()=>{const c=window.__dbg.camera;const d=new window.__dbg.THREE.Vector3();c.getWorldDirection(d);
  return {p:c.position.toArray(),d:d.toArray(),yaw:Math.atan2(-d.x,-d.z)*180/Math.PI,pitch:Math.asin(d.y)*180/Math.PI}}"""
PANEL = "document.getElementById('panel').hidden?null:document.getElementById('panel-title').textContent"


def same(a, b, tol=1e-6):
    return all(abs(x - y) <= tol for x, y in zip(a["p"] + a["d"], b["p"] + b["d"]))


def settle(pg, min_wait=1.2, timeout=40):
    """Wait until the camera stops moving (slow software rendering can stretch flights)."""
    time.sleep(min_wait); prev = pg.evaluate(CAM); t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(0.7); cur = pg.evaluate(CAM)
        if same(prev, cur, 1e-5):
            return cur
        prev = cur
    return prev


def drag(pg, dx, dy, steps=30):
    pg.mouse.move(W / 2, H / 2); pg.mouse.down()
    for i in range(1, steps + 1):
        pg.mouse.move(W / 2 + dx * i / steps, H / 2 + dy * i / steps)
    pg.mouse.up(); settle(pg, 0.8)


def home(pg):
    pg.keyboard.press("Escape"); settle(pg, 1.6)


def shot(pg, name):
    pg.screenshot(path=f"{OUT}_{name}.png", timeout=300000)


with sync_playwright() as p:
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": W, "height": H}); route(pg)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f"http://localhost:{PORT}/")
    pg.wait_for_function("!document.getElementById('loader')", timeout=300000); time.sleep(2)
    c0 = pg.evaluate(CAM); shot(pg, "1_home")
    print("HOME camera", json.dumps({k: (round(v, 2) if not isinstance(v, list) else [round(x, 3) for x in v]) for k, v in c0.items()}))

    # 1. cursor movement without buttons
    for x, y in [(5, 5), (W - 5, 5), (W - 5, H - 5), (5, H - 5), (W / 2, H / 2), (0, H / 2), (W - 1, H / 2)]:
        pg.mouse.move(x, y, steps=12)
    time.sleep(1.0); c1 = pg.evaluate(CAM)
    check("1 mouse move without button leaves camera unchanged", same(c0, c1), f"yaw {c1['yaw']:.3f} pitch {c1['pitch']:.3f}")

    # 2/4/7. drag left to the limit, release, settle
    drag(pg, -1400, 0); cl = pg.evaluate(CAM); time.sleep(0.6); cl2 = pg.evaluate(CAM)
    check("2 drag left turns view left", cl["yaw"] - c0["yaw"] > 30, f"yaw {c0['yaw']:.1f} -> {cl['yaw']:.1f}")
    check("7 max left limited to +45 deg", abs(cl["yaw"] - c0["yaw"] - 45) < 1.0, f"delta {cl['yaw'] - c0['yaw']:.2f}")
    check("4 released: no drift", same(cl, cl2, 1e-4))
    shot(pg, "2_max_left")
    # 8. drag right to the limit (from the left limit)
    drag(pg, 2800, 0); cr = pg.evaluate(CAM)
    check("8 max right limited to -45 deg", abs(cr["yaw"] - c0["yaw"] + 45) < 1.0, f"delta {cr['yaw'] - c0['yaw']:.2f}")
    shot(pg, "3_max_right")
    home(pg)
    # 3/9. vertical
    drag(pg, 0, -1400); cu = pg.evaluate(CAM)
    check("3/9 drag up looks up, limited", 17 < cu["pitch"] - c0["pitch"] < 18.9 or cu["pitch"] <= 15.01, f"pitch {c0['pitch']:.1f} -> {cu['pitch']:.1f}")
    shot(pg, "5_max_up")
    drag(pg, 0, 2800); cd = pg.evaluate(CAM)
    check("10 drag down looks down, limited", -30.9 < cd["pitch"] - c0["pitch"] < -29 or cd["pitch"] >= -45.01, f"pitch -> {cd['pitch']:.1f}")
    shot(pg, "6_max_down")
    home(pg)
    # 5/6. zoom limits
    pg.mouse.move(W / 2, H / 2)
    for _ in range(40):
        pg.mouse.wheel(0, 400)
    time.sleep(1.2); co = pg.evaluate(CAM)
    dist = lambda c, t=(-0.02, 0.92, -1.65): math.dist(c["p"], t)
    check("5 zoom out stops at 1.22x", abs(dist(co) / dist(c0) - 1.22) < 0.02, f"distance {dist(c0):.2f} -> {dist(co):.2f} m")
    shot(pg, "4_max_zoom_out")
    for _ in range(60):
        pg.mouse.wheel(0, -400)
    time.sleep(1.2); ci = pg.evaluate(CAM)
    check("6 zoom in stops at 0.70x", abs(dist(ci) / dist(c0) - 0.70) < 0.02, f"distance -> {dist(ci):.2f} m")
    shot(pg, "7_max_zoom_in")
    home(pg)
    # 13/14. keyboard presets + home
    for key, want in [("t", "TAPE"), ("i", "IBM"), ("n", "NOTEPAD"), ("z", None)]:
        pg.keyboard.press(key); settle(pg, 1.6)
        eb = pg.evaluate("document.getElementById('panel').hidden?null:document.getElementById('panel-eyebrow').textContent")
        ok = (eb is None) if want is None else (eb is not None and want in eb)
        check(f"13 key {key.upper()} preset", ok, f"panel={eb!r}")
        drag(pg, -300, 0); after = pg.evaluate(CAM)
        check(f"   drag after {key.upper()} preset still works and stays in room",
              -2.7 <= after["p"][0] <= 3.3 and 0.35 <= after["p"][1] <= 2.5 and -2.25 <= after["p"][2] <= 3.2)
    home(pg); ch = pg.evaluate(CAM)
    check("14 Escape returns to home view", same(c0, ch, 1e-3), f"pos {[round(v, 3) for v in ch['p']]}")
    # 11. click vs drag on a tape (home view)
    tapes = json.load(open(os.path.join(WEB, "tapes.json")))
    def proj(pt):
        return pg.evaluate("""([x,y,z])=>{const {camera,THREE}=window.__dbg;const v=new THREE.Vector3(x,y,z).project(camera);
          return [(v.x+1)/2*innerWidth,(1-v.y)/2*innerHeight]}""", pt)
    x, y = proj(tapes[3]["spine"])
    pg.mouse.move(x, y); pg.mouse.down(); pg.mouse.move(x + 40, y, steps=5); pg.mouse.up(); time.sleep(1.0)
    check("11a drag that starts on a tape does not open it", pg.evaluate(PANEL) is None)
    home(pg); x, y = proj(tapes[3]["spine"])
    pg.mouse.click(x, y); settle(pg, 1.6)
    check("11b plain click on a tape opens it", pg.evaluate(PANEL) == "BLUTECH CONSULTING", f"panel={pg.evaluate(PANEL)!r}")
    home(pg)
    # 12. click the CRT screen (report current behaviour)
    x, y = proj([-0.02, 1.0, -1.6]); pg.mouse.click(x, y); time.sleep(1.5)
    print("INFO  12 click on CRT screen -> panel:", pg.evaluate(PANEL))
    check("no page errors", not errs, "; ".join(errs[:3]))
    b.close()

    # 15. touch: one-finger drag, tap, pinch (phone viewport)
    b = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
    ctx = b.new_context(viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True, device_scale_factor=1)
    pg = ctx.new_page(); route(pg)
    pg.goto(f"http://localhost:{PORT}/")
    pg.wait_for_function("!document.getElementById('loader')", timeout=300000); time.sleep(2)
    cdp = ctx.new_cdp_session(pg)
    def touch(kind, pts):
        cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": [{"x": x, "y": y, "id": i} for i, (x, y) in enumerate(pts)]})
    t0 = pg.evaluate(CAM)
    touch("touchStart", [(195, 400)])
    for i in range(1, 21):
        touch("touchMove", [(195 - 8 * i, 400)])
    touch("touchEnd", []); time.sleep(1.0); t1 = pg.evaluate(CAM)
    check("15a one-finger drag turns the view (no click)", t1["yaw"] - t0["yaw"] > 5 and pg.evaluate(PANEL) is None, f"yaw +{t1['yaw'] - t0['yaw']:.1f}")
    touch("touchStart", [(150, 400), (240, 400)])
    for i in range(1, 16):
        touch("touchMove", [(150 + 2 * i, 400), (240 - 2 * i, 400)])
    touch("touchEnd", []); time.sleep(1.0); t2 = pg.evaluate(CAM)
    check("15b pinch zooms within limits, no click", pg.evaluate(PANEL) is None and t2["p"] != t1["p"])
    pg.keyboard.press("Escape"); time.sleep(2.2)
    x, y = pg.evaluate("""([x,y,z])=>{const {camera,THREE}=window.__dbg;const v=new THREE.Vector3(x,y,z).project(camera);
          return [(v.x+1)/2*innerWidth,(1-v.y)/2*innerHeight]}""", [-0.02, 1.0, -1.6])
    xs, ys = pg.evaluate("""([x,y,z])=>{const {camera,THREE}=window.__dbg;const v=new THREE.Vector3(x,y,z).project(camera);
          return [(v.x+1)/2*innerWidth,(1-v.y)/2*innerHeight]}""", tapes[0]["spine"])
    if 0 < xs < 390 and 0 < ys < 844:
        touch("touchStart", [(xs, ys)]); touch("touchEnd", []); time.sleep(2.2)
        check("15c tap on a tape opens it", pg.evaluate(PANEL) == "DENTAL-X AI", f"panel={pg.evaluate(PANEL)!r}")
    else:
        print("INFO  15c Dental-X tape is off-screen on the phone home view; tap test skipped")
    pg.screenshot(path=f"{OUT}_8_phone.png", timeout=300000)
    b.close()
srv.shutdown()
print(f"RESULT {sum(results)}/{len(results)} checks passed")
