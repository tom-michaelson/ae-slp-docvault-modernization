# `source/ui` — Angular modernization target

Angular 19 (standalone components) skeleton with a layout that mirrors the hosted
eShopOnWeb shell. Pages are intentionally empty — the `awa-develop` workflow
fills them in using the specs under
[`docs/entry-points/ui-features/`](../../../docs/entry-points/).

## Layout

```
ui/
├── angular.json
├── package.json
├── tsconfig.json, tsconfig.app.json, tsconfig.spec.json
├── public/                     (static assets, served at /)
└── src/
    ├── index.html, main.ts, styles.scss
    └── app/
        ├── app.component.ts    (header + hero + <router-outlet> + footer)
        ├── app.config.ts       (Router + zone change detection)
        ├── app.routes.ts       ('' → Home, '/basket' → Basket, ** → '')
        ├── layout/
        │   ├── header.component.ts       (logo, login, basket badge)
        │   ├── hero-banner.component.ts  (gradient + "ALL T-SHIRTS ON SALE" headline)
        │   └── footer.component.ts       (dark bar w/ copyright)
        └── pages/
            ├── home/home.component.ts    (placeholder)
            └── basket/basket.component.ts (placeholder)
```

## Running locally

Angular CLI isn't bundled; first run needs dependencies installed.

```bash
cd target_repo/source/ui
npm install
npm start            # dev server on http://localhost:4200
npm run build        # production bundle → dist/modernization-ui
npm test             # Karma + Jasmine
```

## Theme

Brand tokens live in `src/styles.scss` as CSS custom properties so components
share a single source:

| Token | Purpose |
| --- | --- |
| `--eshop-teal` | Logo bracket + `OnWeb` accent |
| `--eshop-green` | Primary CTA (add to basket, submit filter) + basket badge |
| `--eshop-footer` | Footer background |
| `--eshop-text` | Default body text |

Header badge count is an `input()` on `HeaderComponent` — wire it up to the
basket service when that endpoint is generated.
