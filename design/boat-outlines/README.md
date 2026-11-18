# Boat Map — generic outlines

Plan-view outlines for owners who have no manual page to upload as the base of
the Boat Map (where things are stowed or located). An owner with a manual page
— e.g. Otter's *Engine Room Layout* — uses that instead.

| Type | `id` | Typical boat | Zones |
| --- | --- | --- | --- |
| Sailboat, monohull | `sailboat-monohull` | Cruising sloop, 35–45 ft | 12 |
| Catamaran | `catamaran-sail` | Sailing cat, 38–45 ft | 14 |
| Powerboat, monohull | `powerboat-monohull` | Express cruiser, 30–40 ft | 10 |
| Trawler | `trawler` | Displacement trawler, 36–48 ft | 10 |
| Center console | `center-console` | Open fishing boat, 20–30 ft | 7 |

## Files

- `<id>-outline.svg` — hull, deck edge, fixed structure (cabin top, cockpit,
  mast, helm). **This is the asset the app ships.**
- `<id>-zones.svg` — the same plus dashed compartment divisions. For review and
  App Store screenshots, not for the app (see *Zones* below).
- `boat-outlines.json` — the manifest: per type, its images, aspect ratio and
  zones (`id`, `name`, `polygon`, `label` point, optional `beneath`).
- `generate.py` — writes all of the above. Edit geometry here, never the SVGs.
- `preview.py` → `preview.html` — every type side by side with zone labels.

```bash
python3 generate.py && python3 preview.py
```

## Conventions

- Plan view, **bow to the right, port at the top** — same as most builders'
  drawings, including Otter's.
- viewBox width 1000; height set by the type's beam/length ratio (`aspect`).
- One colour, strokes only, no masks, no text. Safe as a template image in the
  asset catalog (Preserve Vector Data); it takes the text colour in dark mode.
  The seal needed PNGs because of its mask; these have none.
- Coordinates in the manifest are **0..1 of the image** (x right, y down), so a
  pin keeps its place at any render size.

## Zones

Zones are the *typical* layout for the type. They will be wrong in detail for
most real boats — a 35 ft sloop may have no aft cabin; a 3-cabin cat has
different heads. Hence:

- The app draws zones from the manifest polygons (so it can highlight, hide or
  relabel them) rather than baking them into the image. At phone width the
  1.2-unit dashed line in `-zones.svg` renders at ~0.4 pt — too faint to ship.
- A plan view shows one level. Spaces below it are listed in `beneath`
  (e.g. trawler `saloon` → Engine room, Generator, Fuel tanks) so the pin
  picker can offer them without a second drawing.

## Storing a pin (per `design/design-principles.md`)

A pin stores the owner's words for the location, the (x, y) on the image, and
the outline `id` and zone `id` as opaque handles. The zone **name** is a label,
never the key: renaming "Lazarette" must not detach what is stowed there.

Open question for the feature spec: if an owner later swaps the generic outline
for an uploaded manual page, the (x, y) of existing pins no longer mean
anything. Either keep the zone handle and ask the owner to re-place pins, or
don't allow the swap without a re-placement step. Do not silently carry
coordinates across.
