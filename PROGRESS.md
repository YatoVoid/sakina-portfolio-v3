# Progress

## Last verified working version

**`144419e`** — Cycles-baked room live at https://sakinav3.netlify.app/.
Verified 2026-10-31 on the published site (laptop built-in browser): loads with no errors; T / I / N / Esc open
the tape, IBM PC and notepad panels and return home; city visible through the window.
Known pre-existing bug: 6 of 13 tapes open the project of the tape above them (measured with
`pipeline/tests/tape_click_test.py`).

## Log

- 2026-10-31 — Fixed "FAILED TO LOAD SCENE" (mesh-name mismatch), Three.js r160, stale-JS caching,
  shipped V2's baked room (Draco 37.7 → 7.6 MB), city visible (far plane).
- 2026-10-31 — Project docs created; V2 bake pipeline copied into `pipeline/bake/` and parity-tested on CPU.
- 2026-10-31 — **Edit #1 in progress** (tapes shorter + slanted stacks, smaller VCR):
  edit script `pipeline/edits/e01_tapes_vcr.py`; Cycles before/after previews rendered for approval.
  Next after approval: re-bake Tapes, Monitor, Desk groups; per-tape click boxes; publish to `/preview/`.
- 2026-11-01 — **Edit #2 in progress** (club chair on the right wall): `pipeline/edits/e02_club_chair.py`;
  Cycles before/after previews rendered for approval (`chair` and `chair_wide` views in `render_preview.py`).
  Nothing re-baked, nothing published; live site unchanged (`144419e`).
  Next after approval: decide the leather-detail approach (see DECISIONS.md), re-bake Right_Nook only, publish to `/preview/`.
- 2026-11-01 — Edit #2 revised: leather rebuilt from the reference photo's pixels (crackle + croc sheets), arms rounder,
  back cushion and seat more pillowy. New Cycles previews rendered for approval; still nothing re-baked or published.
- 2026-11-01 — **Edit #3 in progress** (antique bookcase + nook re-arrangement, branch `edit3-bookcase`):
  `pipeline/edits/e03_antique_bookcase.py`; Cycles previews (`nook`, `bookcase` views) rendered for approval.
  Nothing re-baked or published; live site unchanged (`144419e`). Web caveat: the glass doors need a decision before the
  Right_Nook re-bake (transmissive glass does not bake; plan: bake with the doors transparent and add a faint reflective
  pane in Three.js).
- 2026-11-01 — Sakina approved the chair / bookcase / side table / lamp / carton positions (see DECISIONS.md). No bake, no GLB,
  no /preview/ publish, main unchanged. When merging `edit3-bookcase` (which contains e02 + e03), treat the merge as source
  only; the live site stays on `144419e` until a bake is separately requested.
- 2026-11-01 — Edit #4 (radiator under the desk) built and previewed (`under_desk`, `radiator_close` views). Not baked, not published.
- 2026-11-01 — Edit #5 (under-desk wires removed) built and previewed. Not baked, not published.
- 2026-10-31 — **Round 2** (branch `round2`): hero opening camera, orbit-around-the-CRT camera (drag only, limited
  zoom, kept inside the room), golden pothos, tape stacks closer, IBM PC/AT rebuilt in the corner, night sky.
  Published to `/preview/` (57bdb1d); live check of the orbit camera still pending (laptop browser needed).
- 2026-10-31 — **Round 3** (branch `round3`): edits e04–e07 (left wall 0.7 m in, wooden dresser, aged computer,
  realistic postcards + clock; CRT bezel/funnel/housing + VCR; right nook lounge chair, painted side table, linen
  floor lamp, wall picture; warm practical lighting with shadow-linked lamp leak). Cycles previews sent.
  Full re-bake at 64 spp + OIDN (albedo-guided) — parity test: brightness ratio 0.998 vs 192 spp.
