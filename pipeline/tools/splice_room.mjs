// Replace re-baked groups in the room GLB, keep every other group as it is, re-compress with Draco.
//   node pipeline/tools/splice_room.mjs <base.glb> <out.glb> <group.glb> [group.glb ...]
// Each group.glb comes from pipeline/bake_group.py and holds one root node "Room_<Group>" with its baked lightmap.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { mergeDocuments, prune, unpartition, draco } from '@gltf-transform/functions';
import draco3d from 'draco3dgltf';

const [base, out, ...parts] = process.argv.slice(2);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
  'draco3d.decoder': await draco3d.createDecoderModule(),
  'draco3d.encoder': await draco3d.createEncoderModule(),
});
const doc = await io.read(base);
const scene = doc.getRoot().getDefaultScene() || doc.getRoot().listScenes()[0];
const before = scene.listChildren().map(n => n.getName());

for (const p of parts) {
  const part = await io.read(p);
  const names = part.getRoot().listScenes().flatMap(s => s.listChildren()).map(n => n.getName()).filter(n => n.startsWith('Room_'));
  if (!names.length) throw new Error(`${p}: no Room_* node`);
  for (const n of scene.listChildren()) if (names.includes(n.getName())) n.dispose();   // drop old group
  const map = mergeDocuments(doc, part);
  for (const s of part.getRoot().listScenes()) {
    const merged = map.get(s);
    for (const child of merged.listChildren()) if (names.includes(child.getName())) scene.addChild(child);
    merged.dispose();
  }
  console.log('spliced', names.join(','), 'from', p);
}
for (const s of doc.getRoot().listScenes()) if (s !== scene) s.dispose();
await doc.transform(prune(), unpartition(),
  draco({ quantizePosition: 16, quantizeTexcoord: 16, quantizeNormal: 10 }));
await io.write(out, doc);
const after = scene.listChildren().map(n => n.getName());
console.log('groups before:', before.sort().join(' '));
console.log('groups after: ', after.sort().join(' '));
