import * as THREE from "three";

const W = 1240, H = 860;
const INK = "#1d2748", RED = "#b3302a";
const STEP = 56, FIRST = 176;

function rng(seed) {
  let s = seed;
  return () => (s = s * 16807 % 2147483647) / 2147483647;
}

function fit(g, text, font, size, maxW) {
  let s = size;
  for (; s > 24; s -= 2) {
    g.font = font.replace("{s}", s);
    if (g.measureText(text).width <= maxW) break;
  }
  return s;
}

function paper(g, w, h, seed) {
  const r = rng(seed);
  const bg = g.createLinearGradient(0, 0, w, h);
  bg.addColorStop(0, "#f1e8cf");
  bg.addColorStop(1, "#e8dcba");
  g.fillStyle = bg;
  g.fillRect(0, 0, w, h);
  for (let i = 0; i < 2600; i++) {
    g.fillStyle = `rgba(110,90,50,${0.02 + r() * 0.04})`;
    g.fillRect(r() * w, r() * h, 1 + r() * 2, 1 + r() * 2);
  }
}

function rules(g, w, h, first, step) {
  g.strokeStyle = "rgba(70,100,150,.34)";
  g.lineWidth = 2;
  const ys = [];
  for (let y = first; y < h - 20; y += step) {
    ys.push(y);
    g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke();
  }
  g.strokeStyle = "rgba(190,60,50,.5)";
  g.lineWidth = 3;
  g.beginPath(); g.moveTo(104, 34); g.lineTo(104, h); g.stroke();
  return ys;
}

export const PAD_ROWS = [];
export const PAD_W = W, PAD_H = H;
function drawPad(g, pad) {
  const r = rng(11);
  PAD_ROWS.length = 0;
  let rowNo = 0;
  paper(g, W, H, 3);
  g.fillStyle = "#cfc6a6";
  g.fillRect(0, 0, W, 30);
  g.fillStyle = "rgba(0,0,0,.14)";
  g.fillRect(0, 30, W, 3);
  const ys = rules(g, W, H, FIRST, STEP);

  g.fillStyle = INK;
  g.font = "600 128px Caveat, cursive";
  g.save();
  g.translate(136, 134);
  g.rotate(-0.01);
  g.fillText(pad.title, 0, 0);
  const tw = g.measureText(pad.title).width;
  g.strokeStyle = INK;
  g.lineWidth = 4;
  g.beginPath();
  g.moveTo(0, 20);
  g.bezierCurveTo(tw * 0.3, 14, tw * 0.7, 28, tw + 24, 16);
  g.stroke();
  g.restore();

  let rule = 1;
  pad.sections.forEach((sec, si) => {
    g.save();
    g.translate(136, ys[rule] - 8);
    g.rotate(-0.008);
    g.fillStyle = RED;
    g.font = "600 70px Caveat, cursive";
    g.fillText(sec.head, 0, 0);
    const w = g.measureText(sec.head).width;
    g.strokeStyle = RED;
    g.lineWidth = 3;
    g.beginPath();
    g.moveTo(0, 12);
    g.bezierCurveTo(w * 0.4, 8, w * 0.7, 16, w + 10, 9);
    g.stroke();
    g.restore();

    const cols = si === 0 ? 2 : 1;
    const per = Math.ceil(sec.items.length / cols);
    sec.items.forEach((text, i) => {
      const col = Math.floor(i / per), row = i % per;
      const x = 150 + col * 560;
      const y = ys[rule + 1 + row] - 8 + (r() - 0.5) * 3;
      g.save();
      g.translate(x, y);
      g.rotate((r() - 0.5) * 0.018);
      g.fillStyle = INK;
      g.font = "600 50px Caveat, cursive";
      g.fillText("\u2013", 0, 0);
      g.fillText(text, 34, 0);
      PAD_ROWS.push({ i: rowNo++, x0: x - 10, x1: x + 34 + g.measureText(text).width + 10, y0: y - 50, y1: y + 16 });
      g.restore();
    });
    rule += 1 + per + 1;
  });
}

function make(width, height, drawFn) {
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const g = canvas.getContext("2d");
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 8;
  const paint = () => { drawFn(g); tex.needsUpdate = true; };
  paint();
  if (document.fonts?.load) document.fonts.load("600 44px Caveat").then(paint).catch(() => {});
  return tex;
}

function drawWood(g, w, h) {
  const r = rng(21);
  const base = g.createLinearGradient(0, 0, w, 0);
  base.addColorStop(0, "rgb(132,98,76)");
  base.addColorStop(0.55, "rgb(122,88,64)");
  base.addColorStop(1, "rgb(108,76,52)");
  g.fillStyle = base;
  g.fillRect(0, 0, w, h);
  for (let i = 0; i < 46; i++) {
    const y = r() * h, bh = 14 + r() * 90;
    g.fillStyle = r() < 0.5 ? `rgba(80,32,14,${0.04 + r() * 0.05})` : `rgba(255,205,160,${0.03 + r() * 0.05})`;
    g.fillRect(0, y, w, bh);
  }
  for (let i = 0; i < 2600; i++) {
    const y = r() * h, len = 240 + r() * 1100, x = r() * (w - len), bend = (r() - 0.5) * 7;
    g.strokeStyle = r() < 0.55 ? `rgba(70,28,12,${0.10 + r() * 0.12})` : `rgba(255,196,150,${0.06 + r() * 0.08})`;
    g.lineWidth = 0.8 + r() * 1.8;
    g.beginPath();
    g.moveTo(x, y);
    g.quadraticCurveTo(x + len / 2, y + bend, x + len, y + bend * 0.4);
    g.stroke();
  }
  const sh = g.createLinearGradient(0, 0, 0, h);
  sh.addColorStop(0, "rgba(10,4,2,.55)");
  sh.addColorStop(0.35, "rgba(10,4,2,0)");
  sh.addColorStop(0.75, "rgba(10,4,2,0)");
  sh.addColorStop(1, "rgba(10,4,2,.45)");
  g.fillStyle = sh;
  g.fillRect(0, 0, w, h);
  g.globalCompositeOperation = "destination-in";
  const m = 36;
  const fx = g.createLinearGradient(0, 0, w, 0);
  fx.addColorStop(0, "rgba(0,0,0,0)"); fx.addColorStop(m / w, "#000"); fx.addColorStop(1 - m / w, "#000"); fx.addColorStop(1, "rgba(0,0,0,0)");
  g.fillStyle = fx; g.fillRect(0, 0, w, h);
  const fy = g.createLinearGradient(0, 0, 0, h);
  fy.addColorStop(0, "rgba(0,0,0,0)"); fy.addColorStop(m / h, "#000"); fy.addColorStop(1 - m / h, "#000"); fy.addColorStop(1, "rgba(0,0,0,0)");
  g.fillStyle = fy; g.fillRect(0, 0, w, h);
  g.globalCompositeOperation = "source-over";
}

export const makePadTexture = pad => make(W, H, g => drawPad(g, pad));
export const makeWoodTexture = () => make(2048, 1456, g => drawWood(g, 2048, 1456));

// The sheet baked into the room is 0.31 x 0.215 m, centred at UNDER, turned about 2.5 degrees. A patch of desk wood covers it once the note is lifted.
export const UNDER = { x: 0.431, y: 0.7262, z: -1.87, w: 0.31, h: 0.215, rotY: -0.044 };
// The note is landscape. Its near edge rests on the desk where the sheet is and its far edge leans on the tapes.
export const PAD = { x: 0.431, z: -1.87, w: 0.31, h: 0.215, rotY: -0.044 };
