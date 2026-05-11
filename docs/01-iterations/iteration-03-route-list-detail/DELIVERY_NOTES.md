# Delivery Notes

Status: draft
Owner: project maintainer
Last reviewed: 2026-05-08
Source of truth: update after implementation.

## Delivered

```text
2026-05-11 UI polish:
- Route, plan, and candidate cards now prefer uploaded cover images before falling back to track SVG previews.
- Saved plan detail removes the fixed mock-like route SVG overlay and shows the cover image cleanly.
- Route list header no longer labels the page as "real data".
- AMap route coloring now uses relative elevation buckets, while the slope coloring helper is retained for later algorithm refinement.
```

## Tests Run

```text
npm run lint
npm run build
```

## Risks

```text
Map visual verification still depends on a valid VITE_AMAP_JS_KEY and browser-side data with elevation values.
```
