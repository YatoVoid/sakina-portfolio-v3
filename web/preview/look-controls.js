// Look-around camera for the study room (replaces free OrbitControls).
// - Cursor movement alone never moves the camera.
// - Left-drag / one-finger drag turns the view (drag left = look left), within limits.
// - Wheel / pinch dollies along the view axis within a small range.
// - The camera is clamped inside the room; limits are relative to the current preset view.
// Limits were derived from the room layout (see DECISIONS.md, round 2 camera):
//   chair ~55 deg left and right nook 35-70 deg right of HOME, horizontal half-FOV ~37 deg at 2.2:1
//   -> yaw +-45 deg shows both without ever facing the entrance wall (45 + 37 < 90).
import * as THREE from "three";

const YAW_LIMIT = THREE.MathUtils.degToRad(45);
const PITCH_UP = THREE.MathUtils.degToRad(18), PITCH_DOWN = THREE.MathUtils.degToRad(16);   // down 30 showed the floor under the desk
const PITCH_ABS_MIN = THREE.MathUtils.degToRad(-45), PITCH_ABS_MAX = THREE.MathUtils.degToRad(15);
const DOLLY_MIN = 0.70, DOLLY_MAX = 1.22;          // x distance to the view target
const RAD_PER_PX = 0.0019;
const DRAG_THRESHOLD = 6;                          // px: below this a press is a click/tap
// Room interior (three.js coords: x right, y up, z toward the entrance), shrunk by a safety margin.
const ROOM = new THREE.Box3(new THREE.Vector3(-2.7, 0.35, -2.25), new THREE.Vector3(3.3, 2.5, 3.2));

export class LookControls {
  constructor(camera, dom) {
    this.camera = camera; this.dom = dom;
    this.enabled = true;
    this.target = new THREE.Vector3();
    this.clickBlocked = false;                     // true when the last press became a drag/pinch
    this._basePos = new THREE.Vector3(); this._baseYaw = 0; this._basePitch = 0; this._dist = 1;
    this._yaw = 0; this._pitch = 0; this._dolly = 1;          // current (smoothed)
    this._gYaw = 0; this._gPitch = 0; this._gDolly = 1;       // goals
    this._ptrs = new Map(); this._pinch0 = 0; this._dolly0 = 1; this._start = null;
    this._last = performance.now();
    dom.addEventListener("pointerdown", e => this._down(e));
    dom.addEventListener("pointermove", e => this._move(e));
    dom.addEventListener("pointerup", e => this._up(e));
    dom.addEventListener("pointercancel", e => this._up(e));
    dom.addEventListener("wheel", e => this._wheel(e), { passive: false });
  }

  // Adopt the camera's current position/target as the base view (after load or a preset flight).
  setFromCamera() {
    const d = this.target.clone().sub(this.camera.position);
    this._dist = d.length();
    this._basePos.copy(this.camera.position);
    this._baseYaw = Math.atan2(-d.x, -d.z);
    this._basePitch = Math.asin(THREE.MathUtils.clamp(d.y / this._dist, -1, 1));
    this._yaw = this._gYaw = 0; this._pitch = this._gPitch = 0; this._dolly = this._gDolly = 1;
  }

  update() {
    const now = performance.now(), dt = Math.min(0.1, (now - this._last) / 1000); this._last = now;
    if (!this.enabled) return;
    const k = 1 - Math.exp(-dt * 16);              // responsive, settles in ~0.25 s, no drift
    this._yaw += (this._gYaw - this._yaw) * k;
    this._pitch += (this._gPitch - this._pitch) * k;
    this._dolly += (this._gDolly - this._dolly) * k;
    const yaw = this._baseYaw + this._yaw;
    const pitch = THREE.MathUtils.clamp(this._basePitch + this._pitch, PITCH_ABS_MIN, PITCH_ABS_MAX);
    const dir = new THREE.Vector3(-Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), -Math.cos(yaw) * Math.cos(pitch));
    // Dolly along the base view axis (towards / away from what the preset looks at).
    const baseDir = new THREE.Vector3(-Math.sin(this._baseYaw) * Math.cos(this._basePitch), Math.sin(this._basePitch),
                                      -Math.cos(this._baseYaw) * Math.cos(this._basePitch));
    const pos = this._basePos.clone().addScaledVector(baseDir, this._dist * (1 - this._dolly));
    ROOM.clampPoint(pos, pos);
    this.camera.position.copy(pos);
    this.target.copy(pos).addScaledVector(dir, this._dist * this._dolly);
    this.camera.lookAt(this.target);
  }

  _down(e) {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    this._ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
    this.dom.setPointerCapture?.(e.pointerId);
    if (this._ptrs.size === 1) { this._start = { x: e.clientX, y: e.clientY }; this.clickBlocked = false; }
    if (this._ptrs.size === 2) { this._pinch0 = this._spread(); this._dolly0 = this._gDolly; this.clickBlocked = true; }
  }

  _move(e) {
    const p = this._ptrs.get(e.pointerId);
    if (!p || !this.enabled) return;               // no button held: cursor movement does nothing
    const dx = e.clientX - p.x, dy = e.clientY - p.y;
    p.x = e.clientX; p.y = e.clientY;
    if (this._ptrs.size >= 2) {
      const s = this._spread();
      if (this._pinch0 > 0) this._gDolly = THREE.MathUtils.clamp(this._dolly0 * this._pinch0 / s, DOLLY_MIN, DOLLY_MAX);
      return;
    }
    if (this._start && Math.hypot(e.clientX - this._start.x, e.clientY - this._start.y) > DRAG_THRESHOLD) this.clickBlocked = true;
    if (!this.clickBlocked) return;
    this._gYaw = THREE.MathUtils.clamp(this._gYaw - dx * RAD_PER_PX, -YAW_LIMIT, YAW_LIMIT);        // drag left -> look left
    this._gPitch = THREE.MathUtils.clamp(this._gPitch - dy * RAD_PER_PX, -PITCH_DOWN, PITCH_UP);    // drag up -> look up
  }

  _up(e) {
    this._ptrs.delete(e.pointerId);
    if (this._ptrs.size < 2) this._pinch0 = 0;
  }

  _wheel(e) {
    if (!this.enabled) return;
    e.preventDefault();
    this._gDolly = THREE.MathUtils.clamp(this._gDolly * Math.exp(e.deltaY * 0.0012), DOLLY_MIN, DOLLY_MAX);
  }

  _spread() {
    const [a, b] = [...this._ptrs.values()];
    return Math.hypot(a.x - b.x, a.y - b.y) || 1;
  }
}
