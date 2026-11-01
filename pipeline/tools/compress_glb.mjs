// Compress one full export with the same Draco settings splice_room.mjs uses.
//   node pipeline/tools/compress_glb.mjs <in.glb> <out.glb>
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { prune, unpartition, draco } from '@gltf-transform/functions';
import draco3d from 'draco3dgltf';

const [inp, out] = process.argv.slice(2);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'draco3d.decoder': await draco3d.createDecoderModule(),
  'draco3d.encoder': await draco3d.createEncoderModule(),
});
const doc = await io.read(inp);
await doc.transform(prune(), unpartition(), draco({ quantizePosition: 16, quantizeTexcoord: 16, quantizeNormal: 10 }));
await io.write(out, doc);
const scene = doc.getRoot().listScenes()[0];
console.log('written', out, 'top-level nodes:', scene.listChildren().map(n => n.getName()).sort().join(' '));
