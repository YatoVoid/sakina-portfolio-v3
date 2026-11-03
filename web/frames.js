import * as THREE from "three";

// The Iqra University degree is cut out of the baked Room_Keepsakes mesh and hung on the right wall above the leather chair,
// while a new frame with the hackathon photo (the $500 Best Pitch cheque) hangs where the degree was, under the clocks. Right wall plane is x = 3.60, facing -x.
const WALL_X = 3.60;
const DEGREE = new THREE.Box3(new THREE.Vector3(-2.12, 1.25, -2.56), new THREE.Vector3(-1.50, 1.75, -2.40));
const DEGREE_SLOT = { z: -0.78, y: 1.52 };
const PHOTO = { w: 0.56, x: -1.81, y: 1.44, wallZ: -2.50, mat: 0.035, rim: 0.034, depth: 0.034, aspect: 1600 / 721 };

function cutDegree(source) {
  source.updateWorldMatrix(true, false);
  const e = source.matrixWorld.elements, g = source.geometry, pos = g.attributes.position, index = g.index.array;
  const p = new THREE.Vector3();
  const world = i => { const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i); return p.set(e[0] * x + e[4] * y + e[8] * z + e[12], e[1] * x + e[5] * y + e[9] * z + e[13], e[2] * x + e[6] * y + e[10] * z + e[14]); };
  const weld = new Map(), parent = [];
  const find = a => { while (parent[a] !== a) { parent[a] = parent[parent[a]]; a = parent[a]; } return a; };
  const wid = i => {
    const k = Math.round(pos.getX(i) * 1e5) + "," + Math.round(pos.getY(i) * 1e5) + "," + Math.round(pos.getZ(i) * 1e5);
    let w = weld.get(k); if (w === undefined) { w = parent.length; parent.push(w); weld.set(k, w); } return w;
  };
  for (let t = 0; t < index.length; t += 3) { const a = wid(index[t]), b = wid(index[t + 1]), c = wid(index[t + 2]); parent[find(a)] = find(b); parent[find(b)] = find(c); }
  const isl = new Map();
  for (let t = 0; t < index.length; t += 3) {
    const r = find(wid(index[t]));
    let o = isl.get(r); if (!o) { o = { tris: [], box: new THREE.Box3() }; isl.set(r, o); }
    o.tris.push(t);
    for (let k = 0; k < 3; k++) o.box.expandByPoint(world(index[t + k]));
  }
  const mine = [], sel = new Set(), box = new THREE.Box3();
  for (const o of isl.values()) {
    if (!DEGREE.containsBox(o.box)) continue;
    box.union(o.box);
    for (const t of o.tris) { mine.push(index[t], index[t + 1], index[t + 2]); sel.add(t); }
  }
  if (mine.length < 300) return null;
  const keep = [];
  for (let t = 0; t < index.length; t += 3) if (!sel.has(t)) keep.push(index[t], index[t + 1], index[t + 2]);
  g.setIndex(new THREE.BufferAttribute(new Uint32Array(keep), 1));
  return { mine, box };
}

export function createFrames({ meshes, scene }) {
  const out = {};
  const src = meshes.Room_Keepsakes;
  const cut = src && cutDegree(src);
  if (cut) {
    const c = cut.box.getCenter(new THREE.Vector3()), size = cut.box.getSize(new THREE.Vector3());
    const gi = new THREE.BufferGeometry();
    for (const n of Object.keys(src.geometry.attributes)) gi.setAttribute(n, src.geometry.attributes[n]);
    gi.setIndex(new THREE.BufferAttribute(new Uint32Array(cut.mine), 1));
    const mesh = new THREE.Mesh(gi, src.material);
    mesh.matrixAutoUpdate = false;
    mesh.matrix.copy(src.matrixWorld).premultiply(new THREE.Matrix4().makeTranslation(-c.x, -c.y, -c.z));
    mesh.frustumCulled = false; mesh.name = "DegreeFrame";
    const holder = new THREE.Group();
    holder.rotation.y = -Math.PI / 2;
    holder.position.set(WALL_X - size.z / 2 - 0.004, DEGREE_SLOT.y, DEGREE_SLOT.z);
    holder.add(mesh); scene.add(holder);
    out.degree = holder;
  }

  out.photo = hackathonFrame();
  scene.add(out.photo);
  return out;
}

// A wooden frame built from mitred strips shaded as if lit from above, a brass inner fillet, a cream mat, the photo and a glass sheen.
function hackathonFrame() {
  const P = PHOTO, ph = P.w / P.aspect, mat = P.mat, rim = P.rim;
  const iw = P.w + 2 * mat, ih = ph + 2 * mat;          // opening behind the frame lip
  const W = iw + 2 * rim, H = ih + 2 * rim, D = P.depth;
  const group = new THREE.Group();
  group.position.set(P.x, P.y, P.wallZ + 0.002);

  const tone = (hex, k) => new THREE.Color(hex).multiplyScalar(k);
  const SIDE = [1.35, 0.95, 0.62, 0.8];                  // top, right, bottom, left
  const positions = [], colors = [];
  const quad = (a, b, c, d, col) => { for (const v of [a, b, c, a, c, d]) { positions.push(v.x, v.y, v.z); colors.push(col.r, col.g, col.b); } };
  const V = (hw, hh, z, sx, sy) => new THREE.Vector3(sx * hw, sy * hh, z);
  const band = (hwO, hhO, zO, hwI, hhI, zI, hex, k = 1) => {
    const o = [V(hwO, hhO, zO, -1, 1), V(hwO, hhO, zO, 1, 1), V(hwO, hhO, zO, 1, -1), V(hwO, hhO, zO, -1, -1)];
    const n = [V(hwI, hhI, zI, -1, 1), V(hwI, hhI, zI, 1, 1), V(hwI, hhI, zI, 1, -1), V(hwI, hhI, zI, -1, -1)];
    for (let i = 0; i < 4; i++) { const j = (i + 1) % 4; quad(o[i], o[j], n[j], n[i], tone(hex, SIDE[i] * k)); }
  };
  const WOOD = 0x4b2d19, BRASS = 0x8a6a35;
  const hw = W / 2, hh = H / 2, f1 = rim * 0.30, f2 = rim * 0.82;
  band(hw, hh, 0, hw, hh, D, WOOD, 0.55);                                          // outer edge
  band(hw, hh, D, hw - f1, hh - f1, D, WOOD, 1.0);                                 // flat front
  band(hw - f1, hh - f1, D, hw - f2, hh - f2, D - 0.016, WOOD, 1.1);               // sloped moulding
  band(hw - f2, hh - f2, D - 0.016, iw / 2, ih / 2, D - 0.016, BRASS, 1.0);        // brass fillet
  band(iw / 2, ih / 2, D - 0.016, iw / 2 - 0.004, ih / 2 - 0.004, D - 0.03, WOOD, 0.35);  // inner wall of the opening
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  g.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
  group.add(new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.DoubleSide })));

  const matMesh = new THREE.Mesh(new THREE.PlaneGeometry(iw, ih), new THREE.MeshBasicMaterial({ color: 0x8a8272 }));
  matMesh.position.z = D - 0.030; group.add(matMesh);
  const bevel = new THREE.Mesh(new THREE.PlaneGeometry(P.w + 0.008, ph + 0.008), new THREE.MeshBasicMaterial({ color: 0x1a1612 }));
  bevel.position.z = D - 0.0295; group.add(bevel);
  const tex = new THREE.TextureLoader().load("cheque-photo.jpg");
  tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8;
  const pic = new THREE.Mesh(new THREE.PlaneGeometry(P.w, ph), new THREE.MeshBasicMaterial({ map: tex, color: 0x9a8670 }));
  pic.position.z = D - 0.029; group.add(pic);

  const gc = document.createElement("canvas"); gc.width = 256; gc.height = 128;
  const gx = gc.getContext("2d"), gr = gx.createLinearGradient(0, 0, 256, 128);
  gr.addColorStop(0, "rgba(255,255,255,0)"); gr.addColorStop(0.32, "rgba(255,240,220,0.0)"); gr.addColorStop(0.42, "rgba(255,240,220,0.5)");
  gr.addColorStop(0.5, "rgba(255,240,220,0.0)"); gr.addColorStop(0.58, "rgba(255,240,220,0.22)"); gr.addColorStop(0.64, "rgba(255,240,220,0)"); gr.addColorStop(1, "rgba(255,255,255,0)");
  gx.fillStyle = gr; gx.fillRect(0, 0, 256, 128);
  const glass = new THREE.Mesh(new THREE.PlaneGeometry(iw, ih), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(gc), transparent: true, opacity: 0.16, blending: THREE.AdditiveBlending, depthWrite: false }));
  glass.position.z = D - 0.012; glass.renderOrder = 2; group.add(glass);

  const sc = document.createElement("canvas"); sc.width = sc.height = 128;
  const sx = sc.getContext("2d"); sx.filter = "blur(9px)"; sx.fillStyle = "#000"; sx.fillRect(28, 28, 72, 72);
  const shadow = new THREE.Mesh(new THREE.PlaneGeometry(W + 0.10, H + 0.10), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(sc), transparent: true, opacity: 0.6, depthWrite: false }));
  shadow.position.set(0.012, -0.022, -0.001); shadow.renderOrder = 1; group.add(shadow);
  return group;
}
