# Homepage Landing V3 Prototype

## Purpose

This is a standalone static homepage prototype for future `pristolov.ru` review.

Public brand spelling: `приСтолов`.

Pre-game freeze is active. This is not runtime implementation.

## Selected hero image

V3 uses the selected generated hero image:

```text
docs/prototypes/homepage_landing_v3/assets/hero_council_room.png
```

The HTML references it with a local relative path:

```text
./assets/hero_council_room.png
```

## Why V3 exists

V1 was too generic and premium-brochure-like.

V2 became more game-like, but still leaned toward a dashboard/interface prototype.

V3 is image-first:

- cinematic council-room background;
- dark overlay;
- clear headline;
- obvious player entry;
- fewer cards;
- stronger first impression.

## How to open

Open:

```text
homepage_landing_v3.html
```

by double-clicking it in a browser.

## Technical boundaries

The prototype is standalone:

- no external CSS;
- no external JavaScript;
- no external fonts;
- no external web images;
- no real routes;
- no production URLs;
- buttons use placeholder anchors only.

This is not connected to FastAPI runtime.

This is not a template.

This must not be deployed as-is.

## Next step after approval

After freeze is lifted:

1. Audit the current root route and template.
2. Confirm actual CTA target routes.
3. Decide whether V3 visual direction should become the production homepage.
4. Create a narrow runtime implementation task.

Do not implement runtime homepage changes from this prototype without separate approval.
