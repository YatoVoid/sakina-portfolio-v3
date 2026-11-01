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
- **2026-11-01 · Edit #2: the right-wall armchair is replaced by the oversized English-style club chair** (Sakina's
  Attic-Ease screenshot). Same footprint and wall position as the old chair (back on the right wall, centred at
  y = 1.40, facing the room); the old chair and its pillow are removed. Script: `pipeline/edits/e02_club_chair.py`.
  *Certain from the photo:* rolled arms with round scroll fronts, loose box seat cushion, pillowy loose back cushion,
  piped seams, antique-brass nailheads, crocodile-embossed honey-brown leather with light tan veins.
  *Inferred:* real size (~1.02 x 0.96 x 0.92 m), nailhead rows, hidden parts (base, feet, back shell).
  *Texture (revised 2026-11-01, Sakina: "exact same texture"):* the first version was procedural and read as a cracked
  mosaic, not the photo's grain. It is now built from the photo's own pixels: clean leather patches are de-lit and
  quilted (`pipeline/tools/leather_from_photo.py`) into two 1024 px sheets, ~1.4 m each, so nothing repeats on the chair —
  `crackle` (seat, arms, base, piping) and `croc` (back cushion, back shell) — box-projected in chair space, with a bump
  map from the same pixels. Sheets live in `assets/textures/leather/`. Limits: one low-res screenshot is the only source
  (~1.4 mm/px), so it is a faithful *match*, not a lossless copy; the croc sheet is more scrambled than the photo's tidy grid.
- **2026-11-01 · Open issue for Edit #2 (decide after the preview is approved): web detail of the leather.** The
  Right_Nook lightmap is one 2048 px atlas shared by ~330 objects (about 5 mm per pixel on the chair), so the 1-2 cm
  vein pattern would blur into plain brown on the site. Proposed fix: bake the chair as its own group and multiply a
  small tiling leather detail map onto its lightmap in `main.js`. Not started.
- **2026-11-01 · `build_scene.py --only eNN`** builds the V2 state plus one edit, so a pending edit (e.g. #1) does not
  leak into the preview of another.
