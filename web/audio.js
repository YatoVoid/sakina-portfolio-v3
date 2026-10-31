/**
 * V3 audio.js — Ambient study-room soundscape.
 * Sounds play only after the first user interaction (browser autoplay policy).
 * All audio is generated procedurally via Web Audio API (no external files needed).
 */

const AUDIO = (() => {
  let _ctx = null;
  let _started = false;
  let _ambientNode = null;

  // Initialise AudioContext on first interaction
  function _init() {
    if (_ctx) return;
    _ctx = new (window.AudioContext || window.webkitAudioContext)();
  }

  // Low-volume brown-noise generator (study-room ambience)
  function _startAmbient() {
    if (_ambientNode || !_ctx) return;
    const bufferSize = 2 * _ctx.sampleRate;
    const buffer = _ctx.createBuffer(1, bufferSize, _ctx.sampleRate);
    const data = buffer.getChannelData(0);
    let lastOut = 0;
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      data[i] = (lastOut + 0.02 * white) / 1.02;
      lastOut = data[i];
      data[i] *= 3.5; // amplify
    }
    const source = _ctx.createBufferSource();
    source.buffer = buffer;
    source.loop = true;
    const gain = _ctx.createGain();
    gain.gain.value = 0.018; // barely audible
    source.connect(gain).connect(_ctx.destination);
    source.start();
    _ambientNode = { source, gain };
  }

  // Soft click — played when flying to a hotspot
  function playClick() {
    _init();
    if (!_ctx) return;
    const osc = _ctx.createOscillator();
    const env = _ctx.createGain();
    osc.type = 'sine';
    osc.frequency.value = 880;
    env.gain.setValueAtTime(0, _ctx.currentTime);
    env.gain.linearRampToValueAtTime(0.06, _ctx.currentTime + 0.005);
    env.gain.exponentialRampToValueAtTime(0.0001, _ctx.currentTime + 0.18);
    osc.connect(env).connect(_ctx.destination);
    osc.start(_ctx.currentTime);
    osc.stop(_ctx.currentTime + 0.2);
  }

  // VHS rewind tone — played when hovering a tape
  function playTapeHover() {
    _init();
    if (!_ctx) return;
    const osc = _ctx.createOscillator();
    const env = _ctx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(220, _ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(110, _ctx.currentTime + 0.08);
    env.gain.setValueAtTime(0.04, _ctx.currentTime);
    env.gain.exponentialRampToValueAtTime(0.0001, _ctx.currentTime + 0.1);
    osc.connect(env).connect(_ctx.destination);
    osc.start(_ctx.currentTime);
    osc.stop(_ctx.currentTime + 0.12);
  }

  // Start ambient on first interaction
  document.addEventListener('pointerdown', () => {
    if (_started) return;
    _started = true;
    _init();
    if (_ctx.state === 'suspended') _ctx.resume();
    _startAmbient();
  }, { once: false });

  return { playClick, playTapeHover };
})();
