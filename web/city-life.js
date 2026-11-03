import * as THREE from "three";

// Moving details drawn over the Berlin rail-yard photo outside the window. Everything is an additive light in photo pixel
// coordinates (2576x1718 scaled to 1400x934): two trains on the tracks, cars on the lit road, walkers, and the blinking METRO signs.
const FRAG = /* glsl */ `
uniform float uTime;
varying vec2 vUv;
const vec2 SZ = vec2(1400.0, 934.0);

float box(vec2 q, vec2 h, float soft) {
  vec2 d = abs(q) - h;
  return 1.0 - smoothstep(-soft, soft, max(d.x, d.y));
}
float dotGlow(vec2 p, vec2 c, float r) {
  float d = length(p - c);
  return exp(-d * d / (r * r));
}
float streak(vec2 p, vec2 c, vec2 r) {
  vec2 d = (p - c) / r;
  return exp(-dot(d, d));
}
float h1(float n) { return fract(sin(n * 91.3458) * 47453.5453); }

// A train of lit windows along the line a -> b. head runs 0..1 along it; the cars shrink toward the vanishing end a.
vec3 train(vec2 p, vec2 a, vec2 b, float head, float cars, float k) {
  vec3 col = vec3(0.0);
  vec2 d = normalize(b - a), n = vec2(-d.y, d.x);
  for (int i = 0; i < 7; i++) {
    if (float(i) >= cars) break;
    float s = head - float(i) * 0.062;
    if (s < 0.0 || s > 1.04) continue;
    float sc = mix(0.16, 1.0, pow(clamp(s, 0.0, 1.0), 1.5));
    vec2 c = mix(a, b, s);
    vec2 q = p - c;
    vec2 l = vec2(dot(q, d), dot(q, n));
    vec2 half_ = vec2(26.0 * sc * k, 5.5 * sc * k);
    float body = box(l, half_ * 1.04, 1.6 * sc + 0.6);
    float cell = fract(l.x / (9.0 * sc * k) + float(i) * 0.37);
    float win = smoothstep(0.38, 0.5, cell) * (1.0 - smoothstep(0.88, 0.98, cell)) * box(l - vec2(0.0, -half_.y * 0.2), vec2(half_.x, half_.y * 0.45), 1.2 * sc + 0.5);
    float flick = 0.92 + 0.08 * sin(uTime * 23.0 + float(i) * 4.0);
    col += vec3(1.0, 0.84, 0.52) * win * 0.5 * flick;
    col += vec3(0.8, 0.62, 0.38) * body * 0.07;
    col += vec3(1.0, 0.75, 0.4) * streak(l, vec2(0.0, 0.0), vec2(half_.x * 1.5, half_.y * 3.0)) * 0.1 * sc;
  }
  float lead = clamp(head, 0.0, 1.0);
  col += vec3(1.0, 0.95, 0.8) * dotGlow(p, mix(a, b, head + 0.01), 4.0 + 12.0 * lead) * 0.28 * step(head, 1.0);
  return col;
}

void main() {
  float t = uTime;
  vec2 p = vUv * SZ;
  p += 1.3 * vec2(sin(t * 1.1 + p.y * 0.045) + 0.6 * sin(t * 2.3 + p.y * 0.11), 0.7 * cos(t * 0.9 + p.x * 0.05));
  vec3 col = vec3(0.0);

  // trains: right track toward the viewer, left tracks away from the viewer, each on a loop with a pause
  float c1 = mod(t, 15.0) / 15.0;
  col += train(p, vec2(803.0, 648.0), vec2(1215.0, 940.0), c1 * 1.5 - 0.12, 6.0, 1.0);
  float c2 = mod(t + 9.0, 19.0) / 19.0;
  col += train(p, vec2(548.0, 536.0), vec2(150.0, 930.0), 1.0 - (c2 * 1.5 - 0.12), 5.0, 0.8);
  float c3 = mod(t + 5.0, 27.0) / 27.0;
  col += train(p, vec2(566.0, 540.0), vec2(300.0, 936.0), c3 * 1.5 - 0.12, 4.0, 0.62);

  // cars on the road past the lamps: white headlights one way, red tail lights the other
  for (int i = 0; i < 16; i++) {
    float f = float(i);
    float dirn = mod(f, 2.0) < 1.0 ? 1.0 : -1.0;
    float u = fract(t * (0.018 + 0.006 * h1(f)) * dirn + h1(f + 3.0));
    float x = mix(842.0, 1395.0, u);
    float y = 546.0 + (x - 842.0) * 0.046 + (dirn > 0.0 ? 7.0 : 3.0) * (0.6 + 0.4 * u);
    float sc = 0.55 + 0.9 * u;
    vec3 lc = dirn > 0.0 ? vec3(1.0, 0.12, 0.08) : vec3(1.0, 0.93, 0.72);
    float fl = 0.85 + 0.15 * sin(t * 9.0 + f * 5.0);
    col += lc * (dotGlow(p, vec2(x - 2.4 * sc, y), 1.8 * sc) + dotGlow(p, vec2(x + 2.4 * sc, y), 1.8 * sc)) * 0.42 * fl;
    col += lc * dotGlow(p, vec2(x, y), 7.0 * sc) * 0.07;
    col += lc * streak(p, vec2(x, y + 7.0 * sc), vec2(3.2 * sc, 9.0 * sc)) * 0.1;
    if (dirn < 0.0) col += vec3(1.0, 0.9, 0.7) * streak(p, vec2(x - 16.0 * sc, y + 1.2 * sc), vec2(18.0 * sc, 2.4 * sc)) * 0.12;
  }

  // a bus now and then: a long body with a row of lit windows
  float bu = fract(t / 31.0 + 0.2);
  if (bu < 0.6) {
    float bx = mix(842.0, 1395.0, bu / 0.6), by = 546.0 + (bx - 842.0) * 0.046 + 5.0;
    float bs = 0.55 + 0.9 * (bu / 0.6);
    vec2 q = p - vec2(bx, by - 4.0 * bs);
    float body = box(q, vec2(24.0 * bs, 5.5 * bs), 1.0 * bs + 0.4);
    float wins = body * smoothstep(0.35, 0.5, fract(q.x / (6.0 * bs))) * (1.0 - smoothstep(0.85, 0.95, fract(q.x / (6.0 * bs)))) * box(q - vec2(0.0, -1.2 * bs), vec2(24.0 * bs, 2.2 * bs), 0.8 * bs);
    col += vec3(1.0, 0.86, 0.55) * wins * 0.45 + vec3(0.6, 0.5, 0.4) * body * 0.05;
    col += vec3(1.0, 0.12, 0.08) * dotGlow(p, vec2(bx - 25.0 * bs, by), 2.4 * bs) * 0.5;
  }

  // people on the pavement: small warm shapes that bob as they walk
  for (int i = 0; i < 9; i++) {
    float f = float(i) + 20.0;
    float dirn = mod(f, 2.0) < 1.0 ? 1.0 : -1.0;
    float u = fract(t * 0.0045 * dirn + h1(f));
    float x = mix(900.0, 1380.0, u);
    float y = 564.0 + (x - 900.0) * 0.05 + 1.1 * abs(sin(t * 5.0 + f));
    col += vec3(1.0, 0.7, 0.42) * (dotGlow(p, vec2(x, y), 2.2) * 0.26 + dotGlow(p, vec2(x, y - 3.2), 1.8) * 0.2);
    if (mod(f, 2.0) < 1.0) col += vec3(0.35, 0.42, 0.6) * dotGlow(p, vec2(x, y - 6.0), 3.4) * 0.16;
  }

  // METRO signs: on for most of a cycle, off briefly, with a soft glow
  float cyc = mod(t, 2.6);
  float on = smoothstep(0.0, 0.08, cyc) * (1.0 - smoothstep(1.75, 1.83, cyc)) + smoothstep(2.15, 2.2, cyc) * (1.0 - smoothstep(2.5, 2.55, cyc)) * 0.8;
  float sign_ = box(p - vec2(972.0, 516.0), vec2(37.0, 7.5), 3.0) + box(p - vec2(895.0, 474.0), vec2(23.0, 5.5), 2.5) * 0.9;
  float halo = dotGlow(p, vec2(972.0, 516.0), 34.0) * 0.3 + dotGlow(p, vec2(895.0, 474.0), 22.0) * 0.22;
  col += vec3(1.0, 0.9, 0.12) * (sign_ * 0.3 + halo * 1.3 + streak(p, vec2(972.0, 548.0), vec2(30.0, 22.0)) * 0.06) * on;

  // aircraft warning lights on the cranes
  float bl = step(0.5, fract(t * 0.55));
  col += vec3(1.0, 0.1, 0.06) * (dotGlow(p, vec2(483.0, 395.0), 3.4) + dotGlow(p, vec2(341.0, 330.0), 3.0)) * 0.5 * bl;
  col += vec3(1.0, 0.1, 0.06) * dotGlow(p, vec2(1077.0, 346.0), 3.4) * 0.5 * (1.0 - bl);

  gl_FragColor = vec4(col, 1.0);
}`;

export function createCityLife(photo, reduced) {
  const material = new THREE.ShaderMaterial({
    uniforms: { uTime: { value: 0 } },
    vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
    fragmentShader: FRAG,
    transparent: true, depthWrite: false, depthTest: true, side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2
  });
  const mesh = new THREE.Mesh(photo.geometry, material);
  mesh.name = "WindowView_Life";
  mesh.renderOrder = -0.5;
  mesh.frustumCulled = false;
  photo.parent.add(mesh);
  mesh.position.copy(photo.position); mesh.quaternion.copy(photo.quaternion); mesh.scale.copy(photo.scale);
  return { step: t => { material.uniforms.uTime.value = reduced ? 3.0 : t; } };
}
