// Non-uniform zoom of the Berlin photo patch: nearly the original scale where the FRONT view looks (METRO + the left rail tracks
// visible from the home camera), growing smoothly towards the photo's edges so every sideways swing / tilt the orbit allows still sees
// real photo (same coverage as a 3.2x uniform zoom: yaw -89..+52 deg, 34 deg below eye level). No invented pixels, only a smooth stretch.
//   node warp_view_photo.mjs <in.glb> <out.glb>
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
const [inp, out] = process.argv.slice(2);
const C = [-0.02, 1.12, -0.25], R = 79.75, DEG = Math.PI / 180;
const ANCHOR_PX = 1700;
const TH0 = -2.5 + Math.atan((ANCHOR_PX - 1288) / 3200) / DEG;        // anchor yaw (deg)
const MPD = R * Math.tan(DEG);                                        // metres per degree on the cylinder, near the horizon
const H0 = R * Math.tan(4 * DEG);                                     // horizon height above the eye (m)
// photo extents (deg from the anchor / metres)
const LEFT = -2.5 - Math.atan(1288 / 3200) / DEG - TH0, RIGHT = -2.5 + Math.atan(1288 / 3200) / DEG - TH0;
const DOWN_M = -12.92 - H0;      // photo bottom relative to horizon (m, negative)
// target display extents
const T_LEFT = +(process.env.TL||-89) - TH0, T_RIGHT = +(process.env.TR||52) - TH0;                         // deg from the anchor
const T_DOWN = (R * Math.tan(-(+(process.env.TD||34)) * DEG)) - H0;                        // m below the horizon
// slope profile: sCore inside [lo, hi], smoothly rising to sOut outside (ramp wide)
function make(lo, hi, ramp, sCore, sOut) {
  const smooth = t => t * t * (3 - 2 * t);
  const slope = x => { const d = x < lo ? lo - x : x > hi ? x - hi : 0; return sCore + (sOut - sCore) * smooth(Math.min(1, d / ramp)); };
  return x => { const n = 4000, dx = x / n; let a = 0; for (let i = 0; i < n; i++) a += slope((i + 0.5) * dx) * dx; return a; };
}
function solve(limit, target, mk) {                                   // find sOut so that map(limit) == target
  let a = 1, b = 30;
  for (let i = 0; i < 60; i++) { const m = (a + b) / 2; (mk(m)(limit) < target ? a = m : b = m); }
  return (a + b) / 2;
}
const sCore = +(process.env.SCORE||1.35);
const mkL = s => make(-14, 3, 3, sCore, s), mkR = s => make(-14, 3, 3, sCore, s);
const sL = solve(Math.abs(LEFT), Math.abs(T_LEFT), s => { const f = make(-3, 14, 3, sCore, s); return f; });   // mirrored for the left side
const sR = solve(RIGHT, T_RIGHT, s => make(-14, 3, 3, sCore, s));
const mUnitDown = 1 / MPD;
const sD = solve(Math.abs(DOWN_M) / MPD, Math.abs(T_DOWN) / MPD, s => make(-99, 7, 3, sCore, s));      // depression in degrees
const fL = make(-3, 14, 3, sCore, sL), fR = make(-14, 3, 3, sCore, sR), fD = make(-99, 7, 3, sCore, sD);
const fU = make(-99, 10, 3, sCore, 2.5);
console.log('slopes: left', sL.toFixed(2), 'right', sR.toFixed(2), 'down', sD.toFixed(2));
function warpYaw(a) { return a >= 0 ? fR(a) : -fL(-a); }              // a = photo yaw offset from anchor (deg)
function warpH(h) { const dm = (H0 - h) / MPD; return H0 - (dm >= 0 ? fD(dm) : -fU(-dm)) * MPD; }   // h = height above eye (m)
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc = await io.read(inp);
for (const n of doc.getRoot().listNodes()) {
  if (!n.getName().includes('Photo') || !n.getMesh()) continue;
  for (const p of n.getMesh().listPrimitives()) {
    const pos = p.getAttribute('POSITION');
    for (let i = 0; i < pos.getCount(); i++) {
      const v = pos.getElement(i, []);
      const xv = v[0] - C[0], zv = -(v[2] - C[2]), yv = v[1] - C[1];
      const r = Math.hypot(xv, zv), th = Math.atan2(xv, zv) / DEG;
      const th2 = (TH0 + warpYaw(th - TH0)) * DEG, y2 = warpH(yv);
      pos.setElement(i, [C[0] + r * Math.sin(th2), C[1] + y2, C[2] - r * Math.cos(th2)]);
    }
    console.log('warped', n.getName());
  }
}
await io.write(out, doc);
