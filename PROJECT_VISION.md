# Project vision — approved direction

**An interactive, photorealistic vintage graduate-student study room at night.**
A warm, dark, cinematic desk scene: wooden desk under a window onto a rainy night city, a beige CRT computer on
a VCR, VHS tapes that hold the portfolio projects, a red desk lamp as the key light, a plant, a mug, papers,
a phone and a cassette recorder. Natural material colours, subtle screen glow, lived-in clutter.

Visual reference chosen by Sakina (2026-10-31): a Felix Rieseberg-style render — warm amber interior, desk
lamp pool, CRT with a blue screen, stacked labelled tapes, night city through a large window.

## Approved baseline

The live site (https://sakinav3.netlify.app/) as of commit `144419e` is the approved room. It is the Cycles-baked
room from the V2 pipeline. New work refines individual components from reference photos Sakina sends; it does
not redesign the room.

## Content mapping

- 13 VHS tapes = 13 projects (`web/content.js`, `projects[]`), two stacks right of the CRT.
- IBM PC / CRT = about and contact. Notepad = "Currently". Credits panel.
- Tape descriptions are still placeholders ("Add a two sentence description…").

## Quality bar

- Match the reference photo, not a generic model. Say what is inferred vs. certain.
- Never call something photorealistic just because it rendered.
- Keep the site fast: room GLB currently 7.6 MB (Draco), city 1.9 MB.
