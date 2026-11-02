import * as THREE from "three";
import {MENU_TITLE, sections} from "./ibm-content.js";

const W = 640, H = 480, PX = 62, PY = 40, LH = 23, SIZE = 24;
const GREEN = "#52ff86", DIM = "#2fb85a", BRIGHT = "#c9ffd8";
const FONT = `${SIZE}px VT323, "DejaVu Sans Mono", monospace`;

export function makeIbmTerminal({scene, position, size, onOpenLink}) {
  const cv = document.createElement("canvas");
  cv.width = W; cv.height = H;
  const g = cv.getContext("2d");
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;

  const u = {uMap: {value: tex}, uTime: {value: 0}, uOn: {value: 1}};
  const mesh = new THREE.Mesh(
    new THREE.PlaneGeometry(size[0], size[1]),
    new THREE.ShaderMaterial({
      uniforms: u,
      vertexShader: "varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}",
      fragmentShader: `uniform sampler2D uMap;uniform float uTime;varying vec2 vUv;
        void main(){
          vec2 c=vUv-0.5;
          vec2 w=c*(1.0+0.035*dot(c,c)*4.0);
          vec2 uv=w+0.5;
          vec3 col=texture2D(uMap,uv).rgb;
          vec3 blur=texture2D(uMap,uv+vec2(0.0016,0.0)).rgb*0.5+texture2D(uMap,uv-vec2(0.0016,0.0)).rgb*0.5;
          col=mix(col,blur,0.35);
          float lines=0.80+0.20*sin(vUv.y*${H}.0*3.14159);
          float vig=1.0-smoothstep(0.18,0.62,dot(c,c)*1.9);
          float flick=0.97+0.03*sin(uTime*47.0);
          float edge=1.0-smoothstep(0.44,0.5,max(abs(c.x),abs(c.y)));
          gl_FragColor=vec4(col*lines*vig*flick*1.35+vec3(0.0,0.012,0.004),edge);
        }`,
      transparent: true, depthWrite: false
    })
  );
  mesh.rotation.y = Math.PI / 2;
  mesh.position.set(...position);
  mesh.renderOrder = 2;
  mesh.name = "IbmScreen";
  scene.add(mesh);

  const st = {active: false, path: [], scroll: 0, t0: performance.now(), hits: []};

  const node = () => {
    let n = {items: sections, root: true};
    for (const i of st.path) n = n.items[i];
    return n;
  };

  const wrap = (text, maxW) => {
    g.font = FONT;
    const words = text.split(" ");
    const out = [];
    let line = "";
    for (const w of words) {
      const test = line ? line + " " + w : w;
      if (g.measureText(test).width > maxW && line) { out.push(line); line = w; } else line = test;
    }
    out.push(line);
    return out;
  };

  const build = () => {
    const n = node();
    const rows = [];
    const maxW = W - PX * 2;
    const add = (text, color = GREEN, hit = null) => rows.push({text, color, hit});
    if (n.root) {
      add("C:\\SAKINA> MENU", DIM);
      add("");
      sections.forEach((s, i) => add(`[${i + 1}] ${s.key}`, GREEN, i));
      add("");
      add("PRESS A NUMBER OR CLICK A LINE", DIM);
    } else {
      add("C:\\SAKINA\\" + [sections[st.path[0]].key, ...(st.path.length > 1 ? [n.key] : [])].join("\\").replace(/ /g, "_").toUpperCase(), DIM);
      add("");
      if (n.when !== undefined || n.meta !== undefined) {
        wrap(n.key.toUpperCase(), maxW).forEach(l => add(l, BRIGHT));
        if (n.meta) wrap(n.meta, maxW).forEach(l => add(l, GREEN));
        if (n.when) wrap(n.when, maxW).forEach(l => add(l, DIM));
        add("");
      }
      if (n.intro) { wrap(n.intro, maxW).forEach(l => add(l, DIM)); add(""); }
      if (n.items) {
        n.items.forEach((it, i) => {
          const head = `[${i + 1}] ${it.key}`;
          wrap(head, maxW).forEach((l, k) => add(k ? "    " + l : l, GREEN, i));
          if (it.meta) wrap(it.meta, maxW - 40).forEach(l => add("    " + l, DIM, i));
        });
      }
      if (n.lines) {
        n.lines.forEach((l, i) => {
          if (!l) { add(""); return; }
          const head = !n.meta && !n.when && l === l.toUpperCase() && l.length < 60 && /[A-Z]/.test(l);
          const bullet = n.when !== undefined && n.items === undefined ? "> " : "";
          wrap(bullet + l, maxW).forEach((x, k) => add(k && bullet ? "  " + x : x, head ? BRIGHT : GREEN));
        });
      }
    }
    return rows;
  };

  let rows = build();
  const visible = () => Math.floor((H - PY * 2 - LH * 2) / LH);

  const draw = (now) => {
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.fillStyle = "#010a03";
    g.fillRect(0, 0, W, H);
    g.font = FONT;
    g.textBaseline = "alphabetic";
    g.shadowColor = "rgba(82,255,134,.75)";
    g.shadowBlur = 7;
    g.fillStyle = BRIGHT;
    g.fillText(MENU_TITLE + "  ·  SAKINA-DOS 3.0", PX, PY + 10);
    g.shadowBlur = 0;
    g.fillStyle = DIM;
    g.fillRect(PX, PY + 18, W - PX * 2, 2);
    const vis = visible();
    let budget = Math.floor((now - st.t0) * 0.9);
    st.hits = [];
    const first = rows.slice(st.scroll, st.scroll + vis);
    first.forEach((r, i) => {
      const y = PY + 24 + LH * (i + 1) + 6;
      const take = Math.max(0, Math.min(r.text.length, budget));
      budget -= r.text.length;
      const txt = r.text.slice(0, take);
      g.shadowBlur = 7;
      g.fillStyle = r.color;
      g.fillText(txt, PX, y);
      g.shadowBlur = 0;
      if (r.hit !== null && r.hit !== undefined) st.hits.push({y0: y - LH + 4, y1: y + 4, index: r.hit});
    });
    const shownAll = budget >= 0;
    if (shownAll && Math.floor(now / 500) % 2 === 0) {
      const y = PY + 24 + LH * (first.length + 1) + 6;
      g.fillStyle = GREEN;
      g.fillRect(PX, y - 17, 11, 19);
    }
    g.shadowBlur = 0;
    g.fillStyle = DIM;
    g.fillRect(PX, H - PY - 14, W - PX * 2, 2);
    g.fillStyle = DIM;
    const more = rows.length > vis;
    const hint = (st.path.length ? "ESC BACK  " : "ESC EXIT  ") + (more ? "UP/DOWN SCROLL  " : "") + (node().items || node().root ? "1-" + (node().items || sections).length + " SELECT" : "");
    g.fillText(hint, PX, H - PY + 6);
    if (more && st.scroll + vis < rows.length) g.fillText("v", W - PX - 10, H - PY + 6);
    tex.needsUpdate = true;
  };

  const goTo = (path) => {
    st.path = path;
    st.scroll = 0;
    st.t0 = performance.now();
    rows = build();
  };

  const select = (i) => {
    const n = node();
    const list = n.items;
    if (!list || !list[i]) return;
    const it = list[i];
    if (it.href) { onOpenLink(it.href); return; }
    goTo([...st.path, i]);
  };

  const back = () => {
    if (!st.path.length) return false;
    goTo(st.path.slice(0, -1));
    return true;
  };

  const scrollBy = (d) => {
    const max = Math.max(0, rows.length - visible());
    st.scroll = Math.min(max, Math.max(0, st.scroll + d));
    st.t0 = performance.now() - 5000;
  };

  const onKey = (e) => {
    if (!st.active) return false;
    const k = e.key;
    if (k >= "1" && k <= "9") { select(parseInt(k, 10) - 1); return true; }
    if (k === "ArrowDown") { scrollBy(1); return true; }
    if (k === "ArrowUp") { scrollBy(-1); return true; }
    if (k === "PageDown") { scrollBy(visible() - 1); return true; }
    if (k === "PageUp") { scrollBy(-(visible() - 1)); return true; }
    if (k === "Backspace") return back();
    if (k === "Escape") return back();
    return false;
  };

  const clickAt = (uv) => {
    const y = (1 - uv.y) * H;
    const h = st.hits.find(x => y >= x.y0 && y <= x.y1);
    if (h) select(h.index);
    else if (st.path.length && y > H - PY - 24) back();
  };

  return {
    mesh,
    get active() { return st.active; },
    get depth() { return st.path.length; },
    setActive(v) {
      if (v === st.active) return;
      st.active = v;
      if (v) { goTo([]); }
    },
    onKey,
    clickAt,
    step(now, reduced) {
      u.uTime.value = reduced ? 0 : now / 1000;
      draw(reduced ? st.t0 + 1e6 : now);
    },
    raycastTarget: mesh
  };
}
