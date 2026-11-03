import * as THREE from "three";
import {BOOT, BAR, commands} from "./ibm-content.js";

const W = 640, H = 480, PX = 40, PY = 30, LH = 28, SIZE = 30;
const GREEN = "#52ff86", DARK = "#021206";
const FONT = `${SIZE}px VT323, "DejaVu Sans Mono", monospace`;
const BAR_H = 32;
const CPS = 260;

export function makeIbmTerminal({scene, position, size, rotationY = Math.PI / 2, onOpenLink, onType}) {
  const cv = document.createElement("canvas");
  cv.width = W; cv.height = H;
  const g = cv.getContext("2d");
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;

  const u = {uMap: {value: tex}, uTime: {value: 0}};
  const mesh = new THREE.Mesh(
    new THREE.PlaneGeometry(size[0], size[1]),
    new THREE.ShaderMaterial({
      uniforms: u,
      vertexShader: "varying vec2 vUv;void main(){vUv=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}",
      fragmentShader: `uniform sampler2D uMap;uniform float uTime;varying vec2 vUv;
        void main(){
          vec2 c=vUv-0.5;
          vec2 uv=c+0.5;
          vec3 col=texture2D(uMap,uv).rgb;
          vec3 blur=texture2D(uMap,uv+vec2(0.0016,0.0)).rgb*0.5+texture2D(uMap,uv-vec2(0.0016,0.0)).rgb*0.5;
          col=mix(col,blur,0.35);
          float lines=0.80+0.20*sin(vUv.y*${H}.0*3.14159);
          float vig=1.0-0.5*smoothstep(0.35,1.1,dot(c,c)*1.9);
          float flick=0.97+0.03*sin(uTime*47.0);
          float edge=1.0;
          gl_FragColor=vec4(col*lines*vig*flick*1.35+vec3(0.0,0.012,0.004),edge);
        }`,
      transparent: true, depthWrite: false
    })
  );
  mesh.rotation.y = rotationY;
  mesh.position.set(...position);
  mesh.renderOrder = 2;
  mesh.name = "IbmScreen";
  scene.add(mesh);

  const maxW = W - PX * 2;
  const rowsVisible = Math.floor((H - PY * 2 - BAR_H - 16) / LH) - 1;
const PAGE = rowsVisible - 1;

  const wrap = (text) => {
    g.font = FONT;
    if (text === "") return [""];
    const lead = text.match(/^ */)[0];
    const words = text.trim().split(" ");
    const out = [];
    let line = lead;
    for (const w of words) {
      const test = line.trim() ? line + " " + w : line + w;
      if (g.measureText(test).width > maxW && line.trim()) { out.push(line); line = lead + w; } else line = test;
    }
    out.push(line);
    return out;
  };

  const st = {
    active: false, booted: false, out: [], pending: [], cur: "", curFull: null, input: "",
    pauseUntil: 0, last: 0, autoAt: 0, scrollBack: 0, bar: [], skip: false, waiting: false, count: 0, paged: false
  };

  const reset = (now) => {
    st.out = []; st.cur = ""; st.curFull = null; st.input = ""; st.scrollBack = 0; st.skip = false;
    st.pending = [];
    BOOT.forEach(l => wrap(l).forEach(x => st.pending.push(x)));
    st.pending.push("");
    st.pending.push("READY");
    st.booted = false; st.waiting = false; st.count = 0; st.paged = false;
    st.last = now; st.pauseUntil = now + 250;
    st.autoAt = 0;
  };

  const queueLines = (lines) => {
    st.paged = true; st.count = 0;
    lines.forEach(l => wrap(l).forEach(x => st.pending.push(x)));
    st.pending.push("");
    st.pending.push("READY");
  };

  const run = (name) => {
    const cmd = name.trim().toUpperCase();
    if (!cmd) { st.pending.push("READY"); return; }
    if (cmd === "CLEAR" || cmd === "CLS") { st.out = []; st.scrollBack = 0; st.pending.push("READY"); return; }
    const c = commands[cmd];
    if (!c) { queueLines(["Syntax error. Type HELP."]); return; }
    queueLines(c.lines);
    if (c.href) onOpenLink(c.href);
  };

  const submit = () => {
    const t = st.input;
    st.input = "";
    st.out.push(t);
    st.scrollBack = 0;
    run(t);
  };

  const step = (now) => {
    const dt = Math.min(100, now - st.last);
    st.last = now;
    if (now < st.pauseUntil || st.waiting) return;
    if (st.curFull === null && st.pending.length) { st.curFull = st.pending.shift(); st.cur = ""; }
    if (st.curFull !== null) {
      const n = st.skip ? st.curFull.length : Math.max(1, Math.round(dt * CPS / 1000));
      const before = st.cur.length;
      st.cur = st.curFull.slice(0, st.cur.length + n);
      if (st.cur.length > before) onType?.("out");
      if (st.cur.length >= st.curFull.length) {
        st.out.push(st.curFull); st.cur = ""; st.curFull = null;
        if (st.paged && ++st.count >= PAGE && st.pending.length > 2) { st.waiting = true; st.skip = false; }
        if (!st.skip) st.pauseUntil = now + (st.out[st.out.length - 1] === "" ? 160 : 45);
      }
    } else {
      st.skip = false;
      if (!st.booted) { st.booted = true; st.autoAt = st.active ? now + 1600 : 0; }
      else if (st.autoAt && now > st.autoAt && !st.input) { st.autoAt = 0; st.input = ""; st.out.push("ABOUT"); run("ABOUT"); }
    }
  };

  const draw = (now) => {
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.fillStyle = "#010a03";
    g.fillRect(0, 0, W, H);
    g.font = FONT;
    g.textBaseline = "alphabetic";
    const busy = st.pending.length > 0 || st.curFull !== null;
    const lines = [...st.out];
    if (st.curFull !== null) lines.push(st.cur);
    if (!busy) lines.push(st.input);
    const end = Math.max(rowsVisible, lines.length) - st.scrollBack;
    const slice = lines.slice(Math.max(0, end - rowsVisible), end);
    g.shadowColor = "rgba(82,255,134,.7)";
    g.shadowBlur = 7;
    g.fillStyle = GREEN;
    slice.forEach((t, i) => {
      const y = PY + 14 + LH * (i + 1);
      g.fillText(t, PX, y);
      const isLast = i === slice.length - 1 && end === lines.length;
      if (isLast && (busy || Math.floor(now / 450) % 2 === 0)) {
        const w = g.measureText(t).width;
        g.fillRect(PX + w + 3, y - 4, 14, 4);
      }
    });
    g.shadowBlur = 0;
    const hint = st.waiting && st.scrollBack === 0 ? "v PRESS DOWN TO SCROLL   ^ UP TO GO BACK" : st.scrollBack > 0 ? "v DOWN FOR LATER   ^ UP FOR EARLIER" : !busy && st.out.length > rowsVisible ? "^ PRESS UP TO SCROLL BACK" : "";
    if (hint && (st.scrollBack > 0 || Math.floor(now / 700) % 2 === 0 || !st.waiting)) {
      g.fillStyle = "#c9ffd8";
      g.font = `25px VT323, "DejaVu Sans Mono", monospace`;
      g.fillText(hint, PX, H - PY - BAR_H - 6);
      g.font = FONT;
    }
    st.bar = [];
    const by = H - PY - BAR_H + 6, bw = (W - PX * 2) / BAR.length;
    BAR.forEach((b, i) => {
      const x = PX + i * bw;
      g.fillStyle = GREEN;
      g.fillRect(x + 18, by, bw - 4 - 18, BAR_H - 6);
      g.font = `25px VT323, "DejaVu Sans Mono", monospace`;
      g.fillText(b.key, x + 4, by + BAR_H - 10);
      g.fillStyle = DARK;
      g.fillText(b.label, x + 22, by + BAR_H - 10);
      g.font = FONT;
      st.bar.push({x0: x, x1: x + bw, y0: by, y1: by + BAR_H, cmd: b.cmd});
    });
    tex.needsUpdate = true;
  };

  const choose = (cmd) => {
    st.skip = false;
    if (st.pending.length || st.curFull !== null) { st.pending = []; if (st.curFull !== null) st.out.push(st.curFull); st.cur = ""; st.curFull = null; }
    st.autoAt = 0;
    st.out.push(cmd);
    st.scrollBack = 0;
    run(cmd);
  };

  const onKey = (e) => {
    if (!st.active) return false;
    const k = e.key;
    if (k === "Escape") return false;
    const busy = st.pending.length > 0 || st.curFull !== null;
    st.autoAt = 0;
    if (k === "Enter" || k === " ") {
      if (busy) { st.skip = true; return true; }
      if (k === "Enter") { onType?.("enter"); submit(); return true; }
    }
    if (/^F[1-5]$/.test(k)) { onType?.("key"); choose(BAR[parseInt(k.slice(1), 10) - 1].cmd); return true; }
    if (k === "ArrowDown" || k === "PageDown") {
      if (st.scrollBack > 0) st.scrollBack = Math.max(0, st.scrollBack - (k === "PageDown" ? rowsVisible - 2 : 1));
      else if (st.waiting) { st.waiting = false; st.count = 0; st.pauseUntil = performance.now() + 150; }
      return true;
    }
    if (k === "ArrowUp") { st.scrollBack = Math.min(Math.max(0, st.out.length - rowsVisible), st.scrollBack + 1); return true; }
    if (k === "PageUp") { st.scrollBack = Math.min(Math.max(0, st.out.length - rowsVisible), st.scrollBack + rowsVisible - 2); return true; }
    if (busy) return k.length === 1 || k === "Backspace";
    if (k === "Backspace") { onType?.("key"); st.input = st.input.slice(0, -1); return true; }
    if (!st.input && /^[1-5]$/.test(k)) { onType?.("key"); choose(BAR[parseInt(k, 10) - 1].cmd); return true; }
    if (k.length === 1) { onType?.("key"); if (st.input.length < 40) st.input += k.toUpperCase(); st.scrollBack = 0; return true; }
    return false;
  };

  const clickAt = (uv) => {
    const x = uv.x * W, y = (1 - uv.y) * H;
    const b = st.bar.find(q => x >= q.x0 && x <= q.x1 && y >= q.y0 && y <= q.y1);
    if (b) choose(b.cmd);
  };

  reset(performance.now());

  return {
    mesh,
    get active() { return st.active; },
    setActive(v) {
      if (v === st.active) return;
      st.active = v;
      if (v) reset(performance.now());
    },
    onKey,
    clickAt,
    command(cmd) { if (st.active) choose(cmd); },
    step(now, reduced) {
      u.uTime.value = reduced ? 0 : now / 1000;
      step(now);
      draw(now);
    }
  };
}
