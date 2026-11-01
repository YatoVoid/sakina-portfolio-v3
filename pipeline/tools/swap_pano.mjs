// node swap_pano.mjs <in.glb> <pano.jpg> <out.glb> : replace the texture used by WindowView_Pano
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import fs from 'fs';
const [inp, jpg, out] = process.argv.slice(2);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc = await io.read(inp);
for (const n of doc.getRoot().listNodes()) {
  if (n.getName().includes('Pano') && n.getMesh()) {
    for (const p of n.getMesh().listPrimitives()) {
      const tex = p.getMaterial().getBaseColorTexture() || p.getMaterial().getEmissiveTexture();
      tex.setImage(new Uint8Array(fs.readFileSync(jpg))).setMimeType('image/jpeg');
      console.log('swapped', n.getName(), tex.getName());
    }
  }
}
await io.write(out, doc);
