# VNSO Cloud — Shared Theme Contract

Canonical design-system contract for VNSO Cloud frontends, copied from `/root/THEME_CONTRACT.md` and adapted for this Open WebUI fork.

Reference source:

- ProxmoxAI bootstrap: `/root/temp-prj/ProxmoxAI/frontend/src/main.js`
- ProxmoxAI premium CSS: `/root/temp-prj/ProxmoxAI/frontend/src/themes-premium.css`

Open WebUI integration:

- [src/app.html](src/app.html) — pre-paint bootstrap; exposes `window.__setTheme`, `window.__setColorScheme`, `window.__setLocale`.
- [src/lib/components/common/ThemeModeToggle.svelte](src/lib/components/common/ThemeModeToggle.svelte) — theme family picker and light/dark/system controls.
- [static/static/custom.css](static/static/custom.css) — Open WebUI bridge CSS, served at `/static/custom.css`.
- [static/static/proxmoxai-themes.css](static/static/proxmoxai-themes.css) — copied ProxmoxAI theme CSS, served at `/static/proxmoxai-themes.css`.

The nested `static/static/*` path is intentional. In this SvelteKit app, files under repository `static/` are served from `/`, so repository `static/static/custom.css` becomes browser path `/static/custom.css`.

## 1. Storage Contract

| Key                                 | Value type                             | Owner  | Notes                                                                                        |
| ----------------------------------- | -------------------------------------- | ------ | -------------------------------------------------------------------------------------------- |
| `proxmoxai_prefs`                   | JSON                                   | shared | Single source of truth. Consumers read and merge the same shape.                             |
| `proxmoxai_prefs.theme`             | string                                 | shared | Family id such as `midnight`, `anthropic`, `v0`, `github-dim`, `linear`, `stripe`, `notion`. |
| `proxmoxai_prefs.color_scheme`      | `'light' \| 'dark' \| 'system'`        | shared | Independent axis from `theme` family.                                                        |
| `proxmoxai_prefs.locale`            | `'vi' \| 'en'`                         | shared | UI language preference.                                                                      |
| `proxmoxai_prefs.density`           | `'compact' \| 'comfortable' \| 'cozy'` | shared | Layout density.                                                                              |
| `proxmoxai_prefs.reduced_motion`    | boolean                                | shared | Motion reduction flag.                                                                       |
| `proxmoxai_prefs.sidebar_collapsed` | boolean                                | shared | Shared sidebar preference.                                                                   |

Rule: never invent a new top-level key. Extend `DEFAULT_PREFS` in ProxmoxAI first, then mirror the field in every consumer.

## 2. DOM Contract

```html
<html data-theme="anthropic" data-density="comfortable" lang="vi"></html>
```

- `data-theme` is the resolved id, including light variants such as `anthropic-light`, `vercel-light`, or `github-light`.
- `data-density` is `compact`, `comfortable`, or `cozy`.
- `data-motion="reduced"` is present only when reduced motion is enabled.
- `class="light-mode"` is toggled on `<html>` for legacy light theme CSS.
- `class="light"` / `class="dark"` are still maintained for Open WebUI Tailwind dark-mode compatibility.

Every theme block must define:

```css
--bg;
--bg-secondary;
--bg-tertiary;
--card-bg;
--sidebar-bg;
--text;
--text-muted;
--primary;
--primary-dim;
--primary-glow;
--accent;
--success;
--warning;
--danger;
--border;
--border-glow;
--radius;
```

Recommended premium variables:

```css
--bg-card;
--bg-card-hov;
--bg-elev;
--bg-input;
--shadow-card;
--code-bg;
--text-dim;
```

## 3. Theme Catalog

Dark families:

`midnight`, `cursor`, `anthropic`, `v0`, `perplexity`, `synthwave`, `aurora`, `nebula`, `nord`, `solarized`, `contrast`, `dracula`, `tokyo-night`, `github-dim`, `monokai`, `gruvbox`, `catppuccin`, `rosepine`, `oceanic`, `terminal`, `discord`, `linear`, `figma`, `raycast`, `supabase`, `railway`.

Light families:

`light`, `sakura`, `sepia`, `paper`, `arctic`, `pastel-dream`, `porcelain`, `platinum`, `spring`, `summer`, `minimal-light`, `stripe`, `notion`.

Light variants of dark families:

- `anthropic` -> `anthropic-light`
- `v0` -> `vercel-light`
- `github-dim` -> `github-light`

Sentinel:

- `system` resolves to `light` if the OS prefers light, otherwise `midnight`.

## 4. JS Bootstrap Contract

Every frontend must run a pre-paint snippet before CSS paint to avoid theme flash. Open WebUI's implementation lives in [src/app.html](src/app.html).

Required public functions:

```js
window.__setTheme(id); // family id, e.g. 'anthropic' or 'v0'
window.__setColorScheme(scheme); // 'light' | 'dark' | 'system'
window.__setLocale(locale); // 'vi' | 'en'
```

The bootstrap must:

- Load `proxmoxai_prefs` and merge with `DEFAULT_PREFS`.
- Resolve light variants from family + color scheme.
- Set `data-theme`, `data-density`, `data-motion`, `lang`, `light-mode`, `light`, and `dark` before paint.
- Keep legacy `localStorage.theme` compatible for Open WebUI code that still reads it.

## 5. Theme Picker UI Contract

Open WebUI's picker implementation is [src/lib/components/common/ThemeModeToggle.svelte](src/lib/components/common/ThemeModeToggle.svelte).

Required behavior:

- A compact trigger with a swatch showing the selected family.
- Family options for at least `midnight`, `anthropic`, `v0`/Vercel, `github-dim`, `linear`, `stripe`, `notion`, `figma`, `raycast`, `supabase`, `railway`, `rosepine`, `nord`, `tokyo-night`, `dracula`, `terminal`.
- Mode controls for `light`, `dark`, and `system`.
- On family selection, write `proxmoxai_prefs.theme` and call `window.__setTheme` when available.
- On mode selection, write `proxmoxai_prefs.color_scheme`, update the Svelte `theme` store, maintain legacy `localStorage.theme`, and call `window.__setColorScheme` when available.

## 6. Open WebUI CSS Bridge

[static/static/custom.css](static/static/custom.css) bridges Open WebUI classes to VNSO variables. It must:

- Import `/static/proxmoxai-themes.css`.
- Preserve Open WebUI's native `.dark` / `.light` compatibility.
- Map main surfaces, sidebar, cards, inputs, buttons, borders, code blocks, and selection styles to `--bg`, `--text`, `--primary`, `--border`, and related variables.
- Avoid introducing product-specific hardcoded palettes outside theme definitions.

## 7. Contributing A New Theme

1. Add the CSS block in ProxmoxAI `frontend/src/themes-premium.css` and define all required variables.
2. Register metadata in ProxmoxAI `frontend/src/main.js`.
3. Add the family to [src/lib/components/common/ThemeModeToggle.svelte](src/lib/components/common/ThemeModeToggle.svelte).
4. If it is a light variant of a dark family, add it to `LIGHT_VARIANTS` in both [src/app.html](src/app.html) and the picker component.
5. Copy updated CSS into [static/static/proxmoxai-themes.css](static/static/proxmoxai-themes.css).
6. Smoke test contrast in light/dark mode and verify `<html data-theme="...">` updates live.

## 8. Cross-App Sync

Browser `localStorage` is not shared across subdomains. For cross-subdomain sync, use the VNSO auth preferences API:

```text
GET https://proxmox.vnso.vn/api/v1/auth/preferences
PUT https://proxmox.vnso.vn/api/v1/auth/preferences
```

Fallback when offline or unauthenticated: keep using local `proxmoxai_prefs` with the same JSON shape.
