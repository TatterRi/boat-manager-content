# USCG seal, one colour

`uscg-seal-mono.svg` is the source of the app's `United_States_Coast_Guard`
image asset (Boat-Manager, `Assets.xcassets/United_States_Coast_Guard.imageset`).

It is the colour Mark of the U.S. Coast Guard from Wikimedia Commons (a U.S.
government work, public domain), made one colour: its white layer becomes an
SVG mask cut out of the blue layer under it, and the lettering, shield and
inner ring above it are drawn in black.

The app uses PNGs, not this SVG, because iOS renders SVG masks unreliably. The
asset is a template image (`template-rendering-intent: template`), so the seal
takes the text colour: black in light mode, white in dark.

## Regenerate the PNGs

```bash
mkdir -p out && swift export-png.swift uscg-seal-mono.svg out
```

That writes `United_States_Coast_Guard.png`, `@2x` and `@3x` at 64pt high.
Copy them into the imageset; keep the asset name, which help.json uses.
