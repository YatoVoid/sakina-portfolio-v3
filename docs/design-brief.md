> **Superseded (2026-10-31):** this describes an earlier concept/setup. The approved room is the live baked night scene — start from `CLAUDE.md`, `PROJECT_VISION.md` and `ARCHITECTURE.md`. Kept for history.

# V3 Design Brief — Vintage Study Room

## Aesthetic

**"Warm golden-hour Mac desk meets 90s poster-wall bedroom"**

Two reference images establish the tone:
- `ref-warm-mac-desk.jpg` — early Macintosh on wooden filing-cabinet desk, large window with amber sunset flooding the room, Persian rug, framed photos, flowers, lived-in clutter
- `ref-90s-pc-room.jpg` — tower PC + CRT, walls fully papered in game/software posters, brass desk lamp, CD tower, cables and discs on floor

---

## Lighting

| Light | Type | Color | Notes |
|-------|------|-------|-------|
| Window (dominant) | PointLight / RectAreaLight | `#ffd090` warm amber | Right wall, large pane; golden-hour angle (low, raking) |
| Desk lamp | PointLight | `#ffc840` | On desk, near monitor; warm fill; flickers slightly |
| Monitor glow | PointLight | `#1a4060` blue-teal | Subtle cool fill bounced off desk surface |
| TV/VCR | PointLight | `#004488` | Blue cathode glow, very dim |
| Moon (ambient) | AmbientLight | `#1a1a2e` deep blue | Background shadow fill, very low intensity |

Golden ratio: **70% warm amber window : 20% lamp : 10% cool monitor**

---

## Color palette

| Token | Hex | Used for |
|-------|-----|---------|
| `--room-wall` | `#14100a` | Dark warm brown-black walls |
| `--room-floor` | `#1c1108` | Dark oak floor planks |
| `--desk-wood` | `#2d1a09` | Desk surface, chair, shelves |
| `--desk-dark` | `#1a0e06` | Underside, legs |
| `--cream-mac` | `#e8d8b0` | Monitor/Mac body, beige tech |
| `--brass` | `#8a6a20` | Lamp arm, drawer pulls |
| `--rug-base` | `#3a1a0a` | Persian rug primary |
| `--rug-pattern` | `#7a3010` | Rug geometric pattern |
| `--poster-bg` | `#0a0a0a` | Back of wall behind posters |
| `--paper` | `#d4c89a` | Stacked papers, notebooks |

---

## Room layout (top-down, 7m × 8m × 3.4m)

```
┌──────────────────────────────┐
│  BOOKSHELF     POSTER WALL   │ ← back wall
│                              │
│  TV + VCR    VHS RACK        │
│                              │
│         DESK (centre-right)  │ ← filing cabinet desk
│         CHAIR                │
│                              │
│  WINDOW (right wall)         │ ← dominant light source
│  RUG (floor centre)          │
└──────────────────────────────┘
```

Camera HOME position: slightly elevated, looking across desk toward window — golden light catches monitor and papers.

---

## Objects and detail level

### Priority 1 — blocking geometry (load first)
- Room shell (walls, floor, ceiling, window opening)
- Desk with filing cabinet drawers
- CRT monitor (cream/beige) on desk
- Chair (wooden, upholstered pink/red seat — from ref)
- Desk lamp (brass)

### Priority 2 — mid detail
- TV + VCR unit (left wall, on shelf)
- VHS tape rack (7 tapes)
- Bookshelf (right of door)
- Rug (Persian pattern, procedural)

### Priority 3 — surface clutter
- Stacked papers + notebooks on desk
- Coffee mug
- Keyboard (cream/beige)
- Framed photo(s)
- Scattered CDs / floppy disks (floor)

### Priority 4 — wall dressing
- Posters on back wall:
  - Sakina's university diploma / certificate
  - CodeRED "Best Pitch" award
  - Hackathon team photo (placeholder texture)
  - A few retro game/OS posters for texture (Diablo, generic)
- Sticky notes on monitor bezel

---

## Tone guidelines

- **Not a museum** — it should look used. Papers not perfectly stacked. One drawer slightly open.
- **Warm, not orange** — golden-hour amber, not neon or candy.
- **Dark background** — walls nearly black, so the window and lamp punch hard.
- **Poster wall density** — 70% wall coverage, varied sizes, slight tilt on some.
- **Scale reference** — desk height ≈ 0.76m, monitor centre ≈ 1.1m from floor, chair seat ≈ 0.45m.

---

## What NOT to do

- No IKEA-clean geometry — add edge wear, slight non-uniform scale to books
- No bright white surfaces — everything has a warm/dark tint
- No floating objects — every prop sits on a surface
- No neon/cyberpunk — this is amber warmth, not blue LEDs
