import * as THREE from "three";

const YAW = 1.2896;

const rounded = (size, r, fill, glow) => {
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const g = c.getContext("2d");
  const grad = g.createLinearGradient(0, 0, 0, size);
  grad.addColorStop(0, glow);
  grad.addColorStop(1, fill);
  g.fillStyle = "#3a0907";
  g.beginPath(); g.roundRect(0, 0, size, size, r + 4); g.fill();
  g.fillStyle = grad;
  g.beginPath(); g.roundRect(size * 0.08, size * 0.08, size * 0.84, size * 0.84, r); g.fill();
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
};

const disc = (color, r, pos, ry) => {
  const m = new THREE.Mesh(
    new THREE.CircleGeometry(r, 20),
    new THREE.MeshBasicMaterial({color, toneMapped: false})
  );
  m.position.set(...pos);
  m.rotation.y = ry;
  m.renderOrder = 3;
  return m;
};

export function addIbmLights(scene) {
  const button = new THREE.Mesh(
    new THREE.PlaneGeometry(0.0185, 0.0185),
    new THREE.MeshBasicMaterial({map: rounded(128, 22, "#c4160e", "#ff4a36")})
  );
  button.position.set(-2.6788, 0.7465, -1.3258);
  button.rotation.y = YAW;
  button.renderOrder = 3;
  scene.add(button);

  const monLed = disc(0x3dff72, 0.0034, [-2.6892, 0.7465, -1.3046], YAW);
  scene.add(monLed);

  const dots = [-1.02, -1.032, -1.044].map(z => disc(0x3dff72, 0.0023, [-2.6724, 0.649, z], Math.PI / 2));
  dots.forEach(d => scene.add(d));

  const dim = new THREE.Color(0x0b3a1a);
  const lit = new THREE.Color(0x4dff7e);

  let on = true;

  return {
    setOn(v) { on = v; },
    step(now) {
      const t = now / 1000;
      const a = Math.sin(t * 5.2) > 0.1;
      const b = Math.sin(t * 3.1 + 1.7) > 0.2;
      dots[0].material.color.copy(a ? lit : dim);
      dots[1].material.color.copy(b ? lit : dim);
      dots[2].material.color.copy(lit);
      monLed.material.color.copy(!on ? new THREE.Color(0x050805) : Math.floor(t * 1.6) % 2 === 0 ? lit : dim.clone().lerp(lit, 0.35));
    }
  };
}
