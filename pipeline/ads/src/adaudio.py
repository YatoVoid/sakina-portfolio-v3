"""Soft 1980s low-signal ad bed + narration. usage: adaudio.py cfg.json out.wav [novo]"""
import numpy as np, sys, wave, json
from scipy.signal import lfilter, butter
cfg = json.load(open(sys.argv[1])); OUT = sys.argv[2]; NOVO = len(sys.argv) > 3
SR = 44100; DUR = cfg["dur"]; N = int(SR * DUR); rng = np.random.default_rng(cfg.get("seed", 5)); SH = cfg.get("shift", 0)
tt = lambda d: np.arange(int(d * SR)) / SR
def lp(x, fc, o=2): b, a = butter(o, fc / (SR / 2), "low"); return lfilter(b, a, x)
def hp(x, fc, o=2): b, a = butter(o, fc / (SR / 2), "high"); return lfilter(b, a, x)
def bp(x, lo, hi, o=2): b, a = butter(o, [lo / (SR / 2), hi / (SR / 2)], "band"); return lfilter(b, a, x)
noise = lambda d: rng.standard_normal(int(d * SR)); NOTE = lambda n: 440 * 2 ** ((n + SH - 69) / 12)
def env(d, a, r): t = tt(d); return np.minimum(1, t / max(a, 1e-4)) * np.clip((d - t) / max(r, 1e-4), 0, 1)
M = np.zeros((2, N))
def add(buf, sig, t0, g=1.0, pan=0.0):
    i = int(t0 * SR); j = min(N, i + len(sig))
    if i >= N or j <= i: return
    s = sig[:j - i] * g; buf[0, i:j] += s * (1 - max(0, pan)); buf[1, i:j] += s * (1 + min(0, pan))
def epiano(f, d=0.9): t = tt(d); m = np.sin(2 * np.pi * f * t) * 0.9 * np.exp(-t * 7); return (np.sin(2 * np.pi * f * t + m) * np.exp(-t * 3.0) + 0.15 * np.sin(4 * np.pi * f * t) * np.exp(-t * 6)) * env(d, 0.004, 0.2)
def pad(fr, d): t = tt(d); x = sum(np.sin(2 * np.pi * f * t) + 0.6 * np.sin(2 * np.pi * f * 1.004 * t) + 0.25 * np.sin(4 * np.pi * f * t) for f in fr) / len(fr); return lp(x, 1400) * env(d, 1.2, 1.5)
def sub(f, d): t = tt(d); return np.sin(2 * np.pi * f * t) * env(d, 0.02, 0.35)
def bell(f, d=1.6): t = tt(d); m = np.sin(2 * np.pi * f * 3.5 * t) * 1.4 * np.exp(-t * 4); return np.sin(2 * np.pi * f * t + m) * np.exp(-t * 2.4)
def brush(): d = 0.12; t = tt(d); return hp(noise(d), 5000) * np.exp(-t * 35)
def zig(d, lo, hi, rate): t = tt(d); tri = 2 * np.abs(2 * ((t * rate) % 1) - 1) - 1; f = lo + (hi - lo) * (tri * 0.5 + 0.5); return (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.5 + bp(noise(d), 300, 4000) * 0.5) * np.sin(np.pi * np.clip(tt(d) / d, 0, 1))
BPM = cfg.get("bpm", 76); B = 60 / BPM; prog = [(38, [62, 66, 69, 73]), (35, [59, 62, 66, 69]), (43, [55, 59, 62, 66]), (45, [57, 61, 64, 68])]
if cfg.get("minor"): prog = [(38, [62, 65, 69, 72]), (34, [58, 62, 65, 69]), (31, [55, 58, 62, 65]), (33, [57, 60, 64, 67])]
t0 = 1.8; bar = 0
while t0 < DUR - 2.0:
    root, ch = prog[bar % 4]; lvl = 0.55 if t0 < 5 else 1.0
    add(M, pad([NOTE(n) for n in ch], B * 4.2) * 0.10 * lvl, t0); add(M, sub(NOTE(root), B * 1.8) * 0.18 * lvl, t0); add(M, sub(NOTE(root + 7), B * 1.2) * 0.12 * lvl, t0 + 2 * B)
    for k in range(8): add(M, epiano(NOTE(ch[[0, 2, 1, 3, 2, 1, 3, 2][k]])) * 0.05 * lvl, t0 + k * B / 2, 1.0, -0.3 if k % 2 else 0.3)
    for k in range(4): add(M, brush() * 0.035 * lvl, t0 + k * B + B / 2)
    t0 += 4 * B; bar += 1
d_ = tt(1.2); add(M, bp(noise(1.2), 400, 2600) * np.sin(np.pi * d_ / 1.2) * 0.05, 0.0)
d_ = tt(1.0); add(M, (np.sin(2 * np.pi * 55 * d_) + 0.5 * np.sin(2 * np.pi * 110 * d_)) * np.exp(-d_ * 4) * 0.22, 0.1)
add(M, bell(NOTE(86), 1.8) * 0.05, 1.5, 1.0, 0.2); add(M, bell(NOTE(81), 1.8) * 0.04, 1.7, 1.0, -0.2)
for s in cfg["cuts"]: add(M, zig(0.28, 500, 2400, 15) * env(0.28, 0.01, 0.06) * 0.05, s - 0.2)
V = np.zeros((2, N))
if not NOVO:
    for f, ts in cfg["plan"]:
        w = wave.open(f); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float) / 32768
        nz = np.where(abs(x) > 0.012)[0]; x = x[nz[0]:nz[-1] + int(0.1 * 22050)]
        x = np.interp(np.arange(0, len(x) - 1, 22050 / SR), np.arange(len(x)), x); x = bp(x, 260, 3400, 2); x = np.tanh(x * 2.2) / np.tanh(2.2)
        e = np.zeros(len(x) + int(0.12 * SR)); e[:len(x)] += x; e[int(0.09 * SR):int(0.09 * SR) + len(x)] += x * 0.16
        e = e / np.max(np.abs(e)) * 0.34; ev = env(len(e) / SR, 0.03, 0.08); ev = np.pad(ev, (0, max(0, len(e) - len(ev))))[:len(e)]; e = e * ev; add(V, e, ts)
    duck = lp(np.abs(V[0]), 5, 1); duck = 1 - 0.5 * np.clip(duck * 14, 0, 1); M *= duck[None, :]
x = M + V
x = np.stack([bp(x[0], 150, 5000, 2), bp(x[1], 150, 5000, 2)]); n_ = np.arange(N) / SR
wow = np.cumsum(1 + 0.0025 * np.sin(2 * np.pi * 0.5 * n_) + 0.001 * np.sin(2 * np.pi * 5.1 * n_)); wow = wow / wow[-1] * (N - 1)
x = np.stack([np.interp(wow, np.arange(N), x[0]), np.interp(wow, np.arange(N), x[1])])
g = np.ones(N); zz = np.zeros(N)
for td, dd in cfg["dips"]:
    i = int(td * SR); j = i + int(dd * SR); g[i:j] = 0.35 + 0.15 * np.sin(np.linspace(0, 25, j - i)); z = zig(dd, 400, 2200, 17) * 0.025; zz[i:i + len(z)] += z
hiss = hp(noise(DUR), 3000) * 0.010 * (1 + 0.3 * np.sin(2 * np.pi * 0.2 * n_)); hum = np.sin(2 * np.pi * 60 * n_) * 0.005 + np.sin(2 * np.pi * 120 * n_) * 0.002
crack = np.zeros(N)
for p_ in rng.integers(0, N, int(DUR * 5)): crack[p_:p_ + 3] += rng.uniform(-1, 1) * 0.12
x = x * g + (hiss + hum + zz + crack)[None, :]
fade = np.ones(N); fade[:int(0.15 * SR)] = np.linspace(0, 1, int(0.15 * SR)); k0 = N - int(1.9 * SR); u_ = np.linspace(1, 0, N - k0); fade[k0:] = u_ * u_ * (3 - 2 * u_)
x = x * fade; x = x / np.max(np.abs(x)) * 0.42
with wave.open(OUT, "wb") as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x.T * 32767).astype(np.int16).tobytes())
print(OUT, "ok")
