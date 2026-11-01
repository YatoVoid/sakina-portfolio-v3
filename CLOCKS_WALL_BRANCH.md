# Branch `integration/clocks-wall-colour` (2026-11-01)

Built on `main` (57bdb1d). Contains ONLY:
- `pipeline/edits/e06_wall_clocks.py` — Karachi + Houston bronze wall clocks with white name strips; replaces the Pakistan/USA flags and the old small left-wall clock. Verbatim from `origin/edit6-clocks-desk` (tip cefc009).
- `pipeline/edits/e02_club_chair.py` — NOT applied; e06 imports its helper functions (`_n`, `bevelled_box`, `poly_tube`). Verbatim from the same branch.
- `pipeline/edits/e13_wall_colour.py` — reference-photo wall colour, albedo scale 0.60 (same file as on `integration/v3-master`).
- `pipeline/build_scene.py` — `EDITS = ["e01_tapes_vcr", "e06_wall_clocks", "e13_wall_colour"]`.

Deliberately NOT included (all on `edit6-clocks-desk`): `e07_desk_shorten` (conflicts with the approved new desk), `e08_degree_center`
(removes the University of Houston degree, keeps Iqra only), club chair, bookcase, radiator, under-desk wire removal.

Previews (unbaked, 28 spp): `previews/clocks_wall/compare_clocks_wall.jpg`, `wall_value_test.jpg` (wall value 1.0/0.6/0.4).
Not baked, not published, not on `main`. Fonts for the clock lettering are loaded from Linux paths when the edit runs
(`/usr/share/fonts/...`); rebuild on another OS needs those paths adjusted. A baked .blend does not need them.
