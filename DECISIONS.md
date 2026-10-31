# Decisions

Newest last. Each entry: decision — reason.

- **2026-10-31 · The live baked room is the approved baseline.** Matches Sakina's chosen warm, dark night
  reference; the golden-hour docs in `docs/` are superseded.
- **2026-10-31 · Three.js r160 (from r134).** r134 ignored `KHR_materials_emissive_strength`.
- **2026-10-31 · Baked lighting, rendered unlit.** V2's Cycles bake reproduces the reference look; real-time
  lights on the unbaked export were tested and came out flat and overexposed.
- **2026-10-31 · Camera far plane 7000 m.** 331 of 342 city meshes were beyond the old 120 m and invisible.
- **2026-10-31 · JS/CSS revalidate on every load; GLBs get a new filename per change.** A 24 h JS cache made
  deployed fixes invisible to returning visitors; GLBs stay immutable for speed.
- **2026-10-31 · Edits are scripts layered on the untouched v17 source.** Reproducible, reviewable, reversible.
- **2026-10-31 · CPU bakes at 192 spp.** Parity-tested against the shipped lightmaps (see ARCHITECTURE.md).
- **2026-10-31 · Candidates publish to `/preview/` before the main page.** Main page stays on the last
  verified version until Sakina approves.
- **2026-10-31 · Edit #1: tapes at VHS proportions (20 × 11.2 × 3 cm), slanted stacks, VCR 40 cm wide.**
  Sakina: tapes "too long", stack them "in a slant position", VCR under the monitor smaller. Thickness and VCR
  height kept so stack heights and the CRT position do not change.
- **2026-10-31 · Tape clicks will use per-tape boxes (`web/tapes.json`).** The old height formula opened the
  wrong project for 6 of 13 tapes on the live site (measured); the stacks are being rebuilt anyway.
