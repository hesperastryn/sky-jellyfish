# Worklog

## 2026-11-16 22:32 CST — setup
- Read starter main.ts and LICENSE from the kit; repo is empty, starting fresh.
- Plan: procedural "Sky Jellyfish" with Python + PIL at 2048x2048, downscale to 1024x1024.
  Deep indigo night, colossal glowing jellyfish ascending diagonally (tentacles streaming
  down-left), tiny rooftop figures on a city skyline for scale, no text anywhere.

## 2026-11-16 22:38 CST — iteration 1 render
- PNG, 626,611 bytes, 1024x1024. Clean and readable at small size, moon and skyline work.
- Problems seen on viewing: bell is a flat perfect half-disc (umbrella/mushroom), inner
  filaments converge to one apex like umbrella spokes, white core is a geometric semicircle,
  a specular blob floats above the bell like a stray cloud, tentacles are thin straight
  diagonal lines (rain-like, too faint), sky is washed-out light blue-grey at the top,
  rooftop figures are tiny and read as chimneys.

## 2026-11-16 22:40 CST — iteration 2 changes
- Darker, deeper indigo sky gradient for contrast.
- Bell: narrower and taller, tilted (right side higher — ascending), inner layers offset
  so the core is an off-centre glow blob instead of a concentric semicircle.
- Filaments: originate low inside the bell and curve outward, thinner and fainter.
- Removed the floating specular blob; highlight now clipped inside the bell mask.
- Tentacles: thicker, brighter, stronger S-curve sway, wider length spread.
- Rooftop figures enlarged (~110px at 2048) and spaced out.

## 2026-11-16 22:47 CST — iteration 2 render
- PNG, 629,704 bytes, 1024x1024. Bell rounder, sky deeper, figures now clearly human.
- Problems: core blob too big/bright — a blown-out white lamp washing out the bell centre,
  filaments fan visibly from one point under it, one far-left cyan tentacle looks detached
  from the bell, bell centre is featureless white.

## 2026-11-16 22:49 CST — iteration 3 changes
- Core: smaller, cyan-tinted, lower alpha, positioned lower-centre.
- Filaments redesigned: 11 independent strands starting along an inner arc, gentle bow.
- Edge tentacles: less drift so they stay attached to the bell visually.

## 2026-11-16 22:52 CST — iteration 3 render, accepted as final
- PNG, 606,461 bytes (under the 1,048,576 limit, so no JPEG fallback needed), 1024x1024.
- Core is now a soft cyan glow, filaments read as subtle strands, tentacle sweep gives
  clear upward momentum, figures are legible silhouettes. Checked a 300px downscale:
  jellyfish, moon, skyline and rooftop figures all read instantly.
- Packaging: main.ts mirrors the starter (copies ./entry.png to MAKEFUN_OUTPUT_DIR),
  LICENSE copied from the kit starter, README.md written in the required shape.
- Verified: `mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts` produced
  out/entry.png byte-identical to entry.png (same size and sha256 prefix 84ecc836e74a5a43);
  the test `out/` directory was removed afterwards. No git commit/push (coordinator's job).
