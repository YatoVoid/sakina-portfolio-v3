// node cut_disc.mjs <in.glb> <out.glb> <node> <cx> <cz> <radius> <ymin> <ymax> : delete triangles of one group node whose 3 vertices lie in a small disc (WORLD three.js coords, node translation applied)
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { prune, draco } from '@gltf-transform/functions';
import draco3d from 'draco3dgltf';
const [inp, out, node, cx, cz, r, y0, y1] = process.argv.slice(2).map((v,i)=>i<3?v:+v);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'draco3d.decoder': await draco3d.createDecoderModule(), 'draco3d.encoder': await draco3d.createEncoderModule() });
const doc = await io.read(inp); let removed = 0;
for (const nd of doc.getRoot().listNodes().filter(n => n.getName() === node && n.getMesh())) { const T = nd.getTranslation(), Q = nd.getRotation(); const rot = (v) => { const [qx,qy,qz,qw]=Q; const tx=2*(qy*v[2]-qz*v[1]), ty=2*(qz*v[0]-qx*v[2]), tz=2*(qx*v[1]-qy*v[0]); return [v[0]+qw*tx+(qy*tz-qz*ty), v[1]+qw*ty+(qz*tx-qx*tz), v[2]+qw*tz+(qx*ty-qy*tx)]; }; for (const p of nd.getMesh().listPrimitives()) {
  const pos = p.getAttribute('POSITION'); const idx = p.getIndices(); if (!idx) continue;
  const w = (n) => { const m = n.getWorldMatrix?.(); return null; };
  const ia = idx.getArray(), keep = [];
  const inD = (i) => { const v = rot(pos.getElement(i, [])); const x=v[0]+T[0], y=v[1]+T[1], z=v[2]+T[2]; return Math.hypot(x-cx, z-cz) < r && y > y0 && y < y1; };
  for (let t = 0; t < ia.length; t += 3) {
    if (inD(ia[t]) && inD(ia[t+1]) && inD(ia[t+2])) { removed++; continue; }
    keep.push(ia[t], ia[t+1], ia[t+2]);
  }
  if (keep.length !== ia.length) idx.setArray(new (ia.constructor)(keep));
} }
console.log('triangles removed:', removed);
await doc.transform(prune(), draco({ quantizePosition: 16, quantizeTexcoord: 16, quantizeNormal: 10 }));
await io.write(out, doc);
