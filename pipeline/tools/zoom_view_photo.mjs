// Enlarge the Berlin photo patch in angle space about the photographer's horizon / vanishing point, so it covers more of the sky
// and (more importantly) more of the view below the horizon when the camera looks down.
//   node zoom_view_photo.mjs <in.glb> <out.glb> <zoom> [anchor_photo_px_x=1680] [drop_m=0]   (default anchor = the METRO sign, so it stays in the window)
// View space = origin at the hero eye (-0.02, 1.12, -0.25) three.js; z_view = -(Z+0.25); see components/window_view/view.py.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
const [inp, out, zs, ax, dr] = process.argv.slice(2); const DROP = dr ? +dr : 0;   // drop_m: lower the whole picture by this many metres on the 80 m cylinder (moves the rails up into the window)
const _unused = 0; const S = +zs; const ANCHOR_PX = ax ? +ax : 1680;
const C = [-0.02, 1.12, -0.25];
const TH0 = (-2.5 * Math.PI / 180) + Math.atan((ANCHOR_PX - 1288) / 3200);          // yaw of the anchor column (photo centre = -2.5 deg, f = 3200 px)
const H0 = 79.75 * Math.tan(4 * Math.PI / 180);                                 // horizon height above the eye on the 79.75 m cylinder
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc = await io.read(inp);
for (const n of doc.getRoot().listNodes()) {
  if (!n.getName().includes('Photo') || !n.getMesh()) continue;
  for (const p of n.getMesh().listPrimitives()) {
    const pos = p.getAttribute('POSITION');
    for (let i = 0; i < pos.getCount(); i++) {
      const v = pos.getElement(i, []);
      const xv = v[0] - C[0], zv = -(v[2] - C[2]), yv = v[1] - C[1];
      const r = Math.hypot(xv, zv), th = Math.atan2(xv, zv);
      const th2 = TH0 + S * (th - TH0), y2 = H0 + S * (yv - H0) - DROP;
      pos.setElement(i, [C[0] + r * Math.sin(th2), C[1] + y2, C[2] - r * Math.cos(th2)]);
    }
    console.log('zoomed', n.getName(), 'x', S);
  }
}
await io.write(out, doc);
