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
- **2026-11-01 · Edit #3: the wall-mounted half shelf on the back wall is replaced by the tall antique glazed bookcase**
  (Sakina's "Antiques Boutique" photo). Script `pipeline/edits/e03_antique_bookcase.py` (needs e02). Floor-standing,
  touches the floor, back on the back-wall baseboard, 1.50 m wide at the cornice x 2.16 m tall x 0.56 m deep, x 1.60-3.10.
  *Certain from the photo:* two glazed doors, fluted corner columns with gilt capital/collar/reeds, stepped cornice,
  gilt garland frieze (6 swags), corner rosettes, finials, thick centre stile with keyhole + hanging tag, 4 shelves + tall
  bottom compartment of leather books (red/orange/green/navy/tan, gold bands), plinth base with a gilt scroll panel.
  *Inferred:* real size, wood tone, shelf heights, individual books, side/back. Wood and books are procedural (not photo-sampled).
  Old half shelf (242 objects: Shelf_*, ShelfBook_*, ShelfStack_*) removed.
- **2026-11-01 · Nook re-arranged around the bookcase (Edit #3).** Side table (+ its books) slid 0.52 m into the back-right
  corner; club chair turned 18 deg toward the desk (front rotated toward the back wall, i.e. image-left in the wide view),
  rear corner on the right wall, kept in front of the bookcase base; floor lamp (+ its light L3) placed 4 cm in front of the
  chair's front plane, offset 25 cm toward the table side so the seat stays free; the floor carton moved out of the
  bookcase footprint to the floor in front of it.
  *Interpretation to confirm with Sakina:* "left" is read as seen from the room (table on the chair's image-left, chair turned
  toward image-left); "lamp in front of the chair, 4 cm" is read as base edge 4 cm from the chair's front plane.
- **2026-11-01 · Edit #3 follow-up: chair, side table and lamp slid 0.50 m along the right wall away from the bookcase**
  (Sakina: "more to the right, away from the book shelf"). Chair centre now y ~0.76, table y 1.61-1.95; table still on the
  chair's image-left; the carton moved 15 cm further left to stay clear of the lamp base. Parameter `ALONG_WALL` in e03.
- **2026-11-01 · APPROVED by Sakina: the layout of Edit #2 + Edit #3 (positions only).** Approved as previewed (commit `2c60956`):
  antique bookcase on the back wall x 1.60-3.10; club chair turned 18 deg toward the desk, centre y ~0.76, back corner on the
  right wall; side table on the chair's image-left at x 3.20-3.54, y 1.61-1.95; floor lamp 4 cm in front of the chair on its
  room-front side; carton at x 0.92-1.95, y 0.25-1.08. **This approval covers positions only. It is NOT approval to re-bake,
  build a new room GLB, publish to /preview/ or change the main page.** Sakina said explicitly: "Don't bake."
- **2026-11-01 · Edit #4: cast-iron column radiator under the centre desk** (Sakina's Rieseberg-style reference). Script
  `pipeline/edits/e04_radiator.py` (independent of e02/e03; parts go to the Desk collection = Desk bake group).
  1.10 m x 0.53 m x 0.12 m, 24 rounded sections in two rows, top cap, bottom rail, 4 feet, two cream pipes from the right end
  into the floor with floor rings, brass valve + bleed screw; dark warm-bronze satin paint. Back against the back wall
  (y 2.48), centred in the open wall gap between the curtains (x -0.66 .. 0.48). *Certain:* sections, caps, pipes at the
  right end. *Inferred:* size, pitch, paint colour. Not visible from the site's HOME camera (the desk top hides it); it shows
  from low orbit angles. The desk's existing hanging cables fall in front of it (pre-existing, unchanged).
  Preview only: no bake, no GLB, no publish (Sakina: "Don't bake").
- **2026-11-01 · Edit #5: wires removed from underneath the desk only** (Sakina: "remove the wires, they are overlapping, from
  underneath the desk only"). `pipeline/edits/e05_remove_under_desk_wires.py` cuts the four hanging cables (Cable_Left,
  Cable_Power, Wire_CRT_Power, Wire_VCR_Power) at desk-top height (world z 0.70); the parts on the desk / behind the equipment,
  all other cables, the phone cord and the wall sockets are untouched. They live in the Monitor and Keepsakes bake groups, so a
  later bake must include those groups. Preview only; no bake, no publish.
- **2026-10-31 · Round 3: left wall moved from x −3.00 to −2.30.** Sakina wants a moderate gap between the left
  furniture and the desk (was ~1.3 m, now ~0.55 m). Back-wall degrees/flags slide right to fit; camera room
  bounds follow.
- **2026-10-31 · Desk-lamp "leak" light with shadow linking.** A spot at the bulb that the lamp's own shade does not
  block, so the plant/computer cast soft shaped shadows on the walls (Felix refs). Bulb radius 2.5 cm.
- **2026-10-31 · CRT glass effects are real-time (web), not baked.** Scanlines/vignette/reflection depend on view
  angle and would alias or smear in a lightmap; the baked screen stays clean and calmer (no neon blue).
- **2026-10-31 · Lightmaps: 64 spp + Intel OIDN guided by a baked albedo pass** (Cycles does not denoise bakes).
  Same brightness as 192 spp (ratio 0.998, Lamp group test), ~3× faster, so a full re-bake fits in one evening.
