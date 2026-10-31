/**
 * V3 Study Room — main.js
 * Three.js r134 (UMD global: THREE)
 * No bundler. Vanilla ES2020.
 *
 * Architecture:
 *  - MinimalOrbit: mouse + touch orbit, dampingFactor = 0.13 (V3 fix)
 *  - flyTo(): cubic ease in-out tween between camera views
 *  - Parallax: update target on mousemove event only; lerp in frame loop (V3 fix)
 *  - Raycaster: hover tooltip + click/tap to fly / open panel
 *  - Panel: slide-in details from content.js
 *  - GLTFLoader: loads production .glb assets (from /assets/models/)
 *  - Loader: 4-priority progressive asset queue
 */

// ── Views ──────────────────────────────────────────────────────────────────
const VIEWS = {
  HOME:    { pos: [0,   1.4,  3.8],  tgt: [0,    0.9, -1.0] },
  DESK:    { pos: [-0.2,1.3,  1.2],  tgt: [-0.1, 0.75,-2.2] },
  MONITOR: { pos: [0,   1.15, 0.6],  tgt: [0,    1.0, -2.5] },
  TV:      { pos: [2.0, 1.1,  0.8],  tgt: [2.1,  0.75,-2.2] },
  VHS:     { pos: [1.4, 0.9,  0.4],  tgt: [1.8,  0.55,-2.2] },
};

// ── MinimalOrbit ──────────────────────────────────────────────────────────
class MinimalOrbit {
  constructor(camera, dom) {
    this.camera = camera;
    this.dom    = dom;
    this.target = new THREE.Vector3(0, 0.9, -1);
    /** V3 fix: higher damping than V2's 0.07 */
    this.damping  = 0.13;
    this.minDist  = 0.6;
    this.maxDist  = 7.5;
    this.minPolar = 0.12;
    this.maxPolar = Math.PI * 0.55;
    this.enabled  = true;
    this._sph      = new THREE.Spherical();
    this._sphDelta = new THREE.Spherical(0, 0, 0);
    this._ptrs     = [];
    this._prevDist = 0;
    this._sync();
    this._bind();
  }
  _sync() {
    const off = this.camera.position.clone().sub(this.target);
    this._sph.setFromVector3(off);
  }
  _clamp() {
    this._sph.radius = Math.max(this.minDist, Math.min(this.maxDist, this._sph.radius));
    this._sph.phi    = Math.max(this.minPolar, Math.min(this.maxPolar, this._sph.phi));
  }
  _bind() {
    this.dom.addEventListener('mousedown', e => {
      if (!this.enabled) return;
      let lx = e.clientX, ly = e.clientY;
      const onM = ev => {
        this._sphDelta.theta -= (ev.clientX - lx) * 0.004;
        this._sphDelta.phi   -= (ev.clientY - ly) * 0.004;
        lx = ev.clientX; ly = ev.clientY;
      };
      const onU = () => { window.removeEventListener('mousemove', onM); window.removeEventListener('mouseup', onU); };
      window.addEventListener('mousemove', onM);
      window.addEventListener('mouseup', onU);
    });
    this.dom.addEventListener('wheel', e => {
      e.preventDefault();
      this._sph.radius *= 1 + e.deltaY * 0.001;
      this._clamp();
    }, { passive: false });
    this.dom.addEventListener('touchstart', e => {
      e.preventDefault();
      this._ptrs = [...e.touches];
      if (e.touches.length === 2) this._prevDist = this._pDist(e);
    }, { passive: false });
    this.dom.addEventListener('touchmove', e => {
      e.preventDefault();
      if (!this.enabled) return;
      if (e.touches.length === 1 && this._ptrs.length >= 1) {
        this._sphDelta.theta -= (e.touches[0].clientX - this._ptrs[0].clientX) * 0.005;
        this._sphDelta.phi   -= (e.touches[0].clientY - this._ptrs[0].clientY) * 0.005;
      } else if (e.touches.length === 2) {
        const d = this._pDist(e);
        this._sph.radius *= this._prevDist / d;
        this._clamp();
        this._prevDist = d;
      }
      this._ptrs = [...e.touches];
    }, { passive: false });
    this.dom.addEventListener('contextmenu', e => e.preventDefault());
  }
  _pDist(e) {
    const dx = e.touches[0].clientX - e.touches[1].clientX;
    const dy = e.touches[0].clientY - e.touches[1].clientY;
    return Math.sqrt(dx * dx + dy * dy);
  }
  update() {
    this._sph.theta += this._sphDelta.theta * this.damping;
    this._sph.phi   += this._sphDelta.phi   * this.damping;
    this._sphDelta.theta *= (1 - this.damping);
    this._sphDelta.phi   *= (1 - this.damping);
    this._clamp();
    const off = new THREE.Vector3().setFromSpherical(this._sph);
    this.camera.position.copy(this.target).add(off);
    this.camera.lookAt(this.target);
  }
}

// ── App ───────────────────────────────────────────────────────────────────
(function V3App() {
  // Renderer
  const canvas = document.getElementById('three-canvas');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.setSize(innerWidth, innerHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.1;
  renderer.setClearColor(0x07050a);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene  = new THREE.Scene();
  scene.fog    = new THREE.FogExp2(0x07050a, 0.10);
  const camera = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.05, 30);
  camera.position.set(...VIEWS.HOME.pos);

  const controls = new MinimalOrbit(camera, canvas);
  controls.target.set(...VIEWS.HOME.tgt);
  controls._sync();

  // Resize
  window.addEventListener('resize', () => {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
  });

  // ── Fly-to tween ────────────────────────────────────────────────────────
  let _tween = null;
  let currentView = 'HOME';

  function flyTo(name) {
    if (!VIEWS[name]) return;
    currentView = name;
    document.getElementById('view-label').textContent = name;
    const { pos, tgt } = VIEWS[name];
    const startPos = camera.position.clone();
    const startTgt = controls.target.clone();
    const endPos   = new THREE.Vector3(...pos);
    const endTgt   = new THREE.Vector3(...tgt);
    const dur = 1350;
    const t0  = performance.now();
    controls.enabled = false;
    _tween = (now) => {
      const raw = Math.min((now - t0) / dur, 1);
      const e   = raw < 0.5 ? 4 * raw * raw * raw : 1 - Math.pow(-2 * raw + 2, 3) / 2;
      camera.position.lerpVectors(startPos, endPos, e);
      controls.target.lerpVectors(startTgt, endTgt, e);
      controls._sync();
      if (raw >= 1) { _tween = null; controls.enabled = true; }
    };
  }

  // ── Parallax (V3 fix) ────────────────────────────────────────────────────
  const parallaxTgt = { x: 0, y: 0 };
  const parallaxCur = { x: 0, y: 0 };
  /** V3 fix: only update target on mousemove, never in frame loop */
  canvas.addEventListener('mousemove', ev => {
    parallaxTgt.x = (ev.clientX / innerWidth)  * 2 - 1;
    parallaxTgt.y = (ev.clientY / innerHeight)  * 2 - 1;
  });

  // ── Raycaster ────────────────────────────────────────────────────────────
  const raycaster = new THREE.Raycaster();
  const pointer   = new THREE.Vector2();
  const tip       = document.getElementById('tip');
  let   hoveredName = null;

  function setPointer(clientX, clientY) {
    pointer.x =  (clientX / innerWidth)  * 2 - 1;
    pointer.y = -(clientY / innerHeight) * 2 + 1;
  }
  canvas.addEventListener('mousemove', ev => setPointer(ev.clientX, ev.clientY));
  canvas.addEventListener('click', ev => {
    setPointer(ev.clientX, ev.clientY);
    handlePick();
  });
  canvas.addEventListener('touchend', ev => {
    if (ev.changedTouches.length !== 1) return;
    const t = ev.changedTouches[0];
    setPointer(t.clientX, t.clientY);
    handlePick();
  });

  function handlePick() {
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(scene.children, true);
    for (const h of hits) {
      const obj  = h.object;
      const meta = obj.userData;
      if (meta.view)    { flyTo(meta.view); break; }
      if (meta.project) { openPanel(meta.project); break; }
    }
  }

  // ── Keyboard ─────────────────────────────────────────────────────────────
  document.addEventListener('keydown', e => {
    const k = e.key.toUpperCase();
    if (k === 'H' || k === 'ESCAPE') flyTo('HOME');
    if (k === 'D') flyTo('DESK');
    if (k === 'M') flyTo('MONITOR');
    if (k === 'T') flyTo('TV');
    if (k === 'V') flyTo('VHS');
  });

  // ── Nav buttons ───────────────────────────────────────────────────────────
  document.querySelectorAll('#hotspot-nav button').forEach(btn => {
    btn.addEventListener('click', () => flyTo(btn.dataset.view));
  });

  // ── Panel ─────────────────────────────────────────────────────────────────
  function openPanel(projectId) {
    const p = CONTENT.projects.find(x => x.id === projectId);
    if (!p) return;
    const el = document.getElementById('panel-content');
    el.innerHTML = `
      <h2>${p.category}</h2>
      <h3>${p.title}</h3>
      <p>${p.description}</p>
      <div class="tags">${(p.tech || []).map(t => `<span class="tag">${t}</span>`).join('')}</div>
      <div class="links">
        ${p.github ? `<a href="${p.github}" target="_blank" rel="noopener">GitHub →</a>` : ''}
        ${p.demo   ? `<a href="${p.demo}"   target="_blank" rel="noopener">Live Demo →</a>` : ''}
      </div>
    `;
    const panel = document.getElementById('panel');
    panel.hidden = false;
    requestAnimationFrame(() => panel.classList.add('open'));
  }
  document.getElementById('panel-close').addEventListener('click', () => {
    const panel = document.getElementById('panel');
    panel.classList.remove('open');
    setTimeout(() => { panel.hidden = true; }, 360);
  });

  // ── Lighting ──────────────────────────────────────────────────────────────
  scene.add(new THREE.AmbientLight(0x100c18, 0.9));
  const lampLight = new THREE.PointLight(0xffc050, 3.5, 3.2, 1.5);
  lampLight.position.set(0.72, 1.18, -2.79);
  lampLight.castShadow = true;
  scene.add(lampLight);
  const moonLight = new THREE.PointLight(0x5070a0, 1.8, 7, 1.2);
  moonLight.position.set(-1.2, 2.1, -4.8);
  scene.add(moonLight);
  const tvLight = new THREE.PointLight(0x0044cc, 0.9, 1.8, 1.5);
  tvLight.position.set(2.1, 0.9, -2.6);
  scene.add(tvLight);

  // ── Placeholder geometry (replaced by GLB assets in production) ───────────
  buildPlaceholderRoom(scene);

  // ── Progressive GLB loader ────────────────────────────────────────────────
  // Uncomment when .glb assets are ready in /assets/models/
  // loadAssets(scene);

  // ── Loader UI ─────────────────────────────────────────────────────────────
  const loaderEl  = document.getElementById('loader');
  const loaderBar = document.getElementById('loader-bar');
  const loaderSts = document.getElementById('loader-status');
  let   _loadT    = 0;
  const _loadInt  = setInterval(() => {
    _loadT = Math.min(_loadT + 15, 92);
    loaderBar.style.width = _loadT + '%';
    if (_loadT > 30) loaderSts.textContent = 'Building scene…';
    if (_loadT > 60) loaderSts.textContent = 'Almost ready…';
  }, 60);

  // ── Frame loop ─────────────────────────────────────────────────────────────
  let _started = false;
  function frame(now) {
    requestAnimationFrame(frame);

    if (!_started) {
      _started = true;
      clearInterval(_loadInt);
      loaderBar.style.width = '100%';
      loaderSts.textContent = 'Ready';
      setTimeout(() => { loaderEl.style.opacity = '0'; setTimeout(() => { loaderEl.hidden = true; }, 600); }, 250);
    }

    // Fly tween
    if (_tween) _tween(now);

    // Orbit
    controls.update();

    // V3 parallax fix: lerp in frame loop, only at HOME, not during tween
    if (currentView === 'HOME' && !_tween) {
      parallaxCur.x += (parallaxTgt.x - parallaxCur.x) * 0.05;
      parallaxCur.y += (parallaxTgt.y - parallaxCur.y) * 0.05;
      camera.setViewOffset(
        innerWidth, innerHeight,
        parallaxCur.x * innerWidth  * 0.006,
        parallaxCur.y * innerHeight * 0.006,
        innerWidth, innerHeight
      );
    } else {
      camera.clearViewOffset();
    }

    // Hover detect
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(scene.children, true);
    let hitName = null;
    for (const h of hits) {
      const d = h.object.userData;
      if (d.view || d.project) { hitName = d.view || d.project; break; }
      if (d.label) { hitName = d.label; break; }
    }
    if (hitName !== hoveredName) {
      hoveredName = hitName;
      if (hitName) {
        tip.textContent = hits[0]?.object.userData.tip || hitName;
        tip.classList.add('show');
        canvas.style.cursor = 'pointer';
      } else {
        tip.classList.remove('show');
        canvas.style.cursor = 'default';
      }
    }

    // Lamp flicker
    lampLight.intensity = 3.5 + Math.sin(now * 0.0031) * 0.1 + Math.sin(now * 0.0073) * 0.06;

    renderer.render(scene, camera);
  }
  requestAnimationFrame(frame);

})(); // end V3App

// ── Placeholder room geometry ──────────────────────────────────────────────
// These boxes are replaced by loaded .glb files in production.
// Keep them here so the scene is never empty.
function buildPlaceholderRoom(scene) {
  const box = (mat, w, h, d, x, y, z, meta = {}) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
    m.position.set(x, y, z);
    Object.assign(m.userData, meta);
    scene.add(m);
    return m;
  };
  const M = (c, r = 0.8, me = 0, mei = 0) => {
    const mat = new THREE.MeshStandardMaterial({ color: c, roughness: r });
    if (me) { mat.emissive = new THREE.Color(me); mat.emissiveIntensity = mei; }
    return mat;
  };

  // Room shell
  box(M(0x1c1108,0.9), 7,0.06,8,  0,-0.03,-1.5);
  box(M(0x0f0d14,0.98),4,0.02,3, -0.3,0.02,-2.5);
  box(M(0x14100a,0.95),7,3.4,0.12,0,1.67,-5.0);
  box(M(0x14100a,0.95),0.12,3.4,8,-3.5,1.67,-1.5);
  box(M(0x14100a,0.95),0.12,3.4,8, 3.5,1.67,-1.5);
  box(M(0x10080a,0.95),7,0.12,8,  0,3.4,-1.5);
  // Window
  box(M(0x304060,0.05,0x8ab8e8,0.6),1.6,1.1,0.06,-1.2,2.1,-4.94);
  // Desk
  const desk = box(M(0x2d1a09,0.75),2.4,0.06,0.9,-0.2,0.78,-2.7,{view:'DESK',tip:'→ DESK AREA'});
  box(M(0x2d1a09,0.8),2.4,0.05,0.9,-0.2,0.25,-2.7);
  // Monitor
  box(M(0x0d0d0d,0.6),0.85,0.52,0.07,0,1.16,-2.82,{view:'MONITOR',tip:'→ COMPUTER'});
  box(M(0x001520,0.2,0x1a4060,0.8),0.76,0.44,0.01,0,1.16,-2.79,{view:'MONITOR',tip:'→ COMPUTER'});
  // TV
  const tv = box(M(0x111111,0.5),0.72,0.5,0.25,2.1,0.9,-2.82,{view:'TV',tip:'→ TV / VCR'});
  box(M(0x050810,0.1,0x004488,0.5),0.62,0.41,0.01,2.1,0.9,-2.7,{view:'TV',tip:'→ TV / VCR'});
  box(M(0x2d1a09,0.8),0.7,0.65,0.4,2.1,0.325,-2.8,{view:'TV',tip:'→ TV / VCR'});
  // VHS rack
  box(M(0x1a1a1a,0.3),0.25,0.65,0.12,1.5,0.63,-2.82,{view:'VHS',tip:'→ VHS TAPES'});
  const tapeCols = [0x0a1020,0x200808,0x0a1a08,0x0a1020,0x200808,0x0a1a08,0x100a20];
  const tapeLabels = ['DENTAL-X','HOUSING AI','FLOOD CAST','POWERGUARD','WARMTHREAD','SUMUS','RESUME'];
  tapeCols.forEach((c,i) => {
    box(M(c,0.8),0.028,0.19,0.1,1.38+i*0.034,0.63,-2.82,{
      view:'VHS', label:`tape_${i}`,
      tip:`→ ${tapeLabels[i]}`
    });
  });
  // Bookshelf
  [-3.0,-2.0].forEach(x => box(M(0x2d1a09,0.9),0.08,1.8,0.32,x,0.9,-3.4));
  [0,0.65,1.3,1.8].forEach(y => box(M(0x2d1a09,0.9),1.06,0.04,0.32,-2.5,y,-3.4));
  // Lamp (emissive)
  box(M(0xffc840,0.3,0xffc840,3.0),0.08,0.02,0.08,0.72,1.19,-2.79);
  // Chair
  box(M(0x0e0b07,0.95),0.55,0.04,0.5,-0.1,0.48,-1.8);
  box(M(0x0e0b07,0.95),0.52,0.55,0.05,-0.1,0.79,-2.05);
}

// ── Progressive GLB asset loader ──────────────────────────────────────────
// Called once bpy-generated .glb files are placed in /assets/models/
function loadAssets(scene) {
  if (!THREE.GLTFLoader) {
    console.warn('[V3] THREE.GLTFLoader not available. Skipping GLB load.');
    return;
  }
  const loader = new THREE.GLTFLoader();

  /**
   * Priority tiers (see architecture doc §4):
   *  1 → blocking (floor, walls, desk) — wait before first render
   *  2 → important (monitor, TV, VHS) — load immediately after P1
   *  3 → background (books, chair, accessories) — load after 2s
   *  4 → lazy (fine detail, decorative) — load on idle / intersection
   */
  const ASSETS = [
    { file: 'room-shell.glb',   priority: 1, position: [0,0,0] },
    { file: 'desk.glb',         priority: 1, position: [0,0,0] },
    { file: 'monitor.glb',      priority: 2, position: [0,0,0] },
    { file: 'tv-vcr.glb',       priority: 2, position: [0,0,0] },
    { file: 'vhs-rack.glb',     priority: 2, position: [0,0,0], userData: { view:'VHS', tip:'→ VHS TAPES' } },
    { file: 'chair.glb',        priority: 3, position: [0,0,0] },
    { file: 'bookshelf.glb',    priority: 3, position: [0,0,0] },
    { file: 'lamp.glb',         priority: 3, position: [0,0,0] },
    { file: 'props.glb',        priority: 4, position: [0,0,0] },
  ];

  const base = './assets/models/';
  const loadGLB = (asset) => {
    loader.load(
      base + asset.file,
      (gltf) => {
        const root = gltf.scene;
        if (asset.position) root.position.set(...asset.position);
        if (asset.userData) Object.assign(root.userData, asset.userData);
        scene.add(root);
      },
      undefined,
      (err) => console.warn(`[V3] Failed to load ${asset.file}:`, err)
    );
  };

  const p1 = ASSETS.filter(a => a.priority === 1);
  const p2 = ASSETS.filter(a => a.priority === 2);
  const p3 = ASSETS.filter(a => a.priority === 3);
  const p4 = ASSETS.filter(a => a.priority === 4);

  p1.forEach(loadGLB);
  p2.forEach(loadGLB);
  setTimeout(() => p3.forEach(loadGLB), 2000);
  setTimeout(() => p4.forEach(loadGLB), 5000);
}
