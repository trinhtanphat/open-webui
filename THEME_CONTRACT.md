# VNSO Cloud — Shared Theme Contract

Canonical design-system contract for VNSO Cloud frontends, copied from `/root/THEME_CONTRACT.md` for this Open WebUI fork.

The reference implementation lives in `/root/temp-prj/ProxmoxAI/frontend/src/main.js` and `/root/temp-prj/ProxmoxAI/frontend/src/themes-premium.css`. Open WebUI consumes the contract through [src/app.html](src/app.html), [static/static/custom.css](static/static/custom.css), and [static/static/proxmoxai-themes.css](static/static/proxmoxai-themes.css).

## 1. Storage Contract

| Key                                 | Value type | Owner         | Notes                                                                                           |
| ----------------------------------- | ---------- | ------------- | ----------------------------------------------------------------------------------------------- | ---------------------- | ------------------------------------ |
| `proxmoxai_prefs`                   | JSON       | shared        | Single source of truth, written by ProxmoxAI; sibling apps read and merge the same shape        |
| `proxmoxai_prefs.theme`             | string     | shared        | Family id such as `anthropic`, `v0`, `github-dim`, `linear`, `stripe`, `notion`, `vercel-light` |
| `proxmoxai_prefs.color_scheme`      | `'light'   | 'dark'        | 'system'`                                                                                       | shared                 | Independent axis from `theme` family |
| `proxmoxai_prefs.locale`            | `'vi'      | 'en'`         | shared                                                                                          | UI language preference |
| `proxmoxai_prefs.density`           | `'compact' | 'comfortable' | 'cozy'`                                                                                         | shared                 | Layout density                       |
| `proxmoxai_prefs.reduced_motion`    | boolean    | shared        | Motion reduction flag                                                                           |
| `proxmoxai_prefs.sidebar_collapsed` | boolean    | shared        | Shared sidebar preference                                                                       |

Rule: never invent a new top-level key. Extend `DEFAULT_PREFS` in ProxmoxAI first, then mirror the field in every consumer.

## 2. DOM Contract

```html
<html data-theme="anthropic" data-density="comfortable" lang="vi"></html>
```

- `data-theme` is the resolved id, including light variants such as `anthropic-light`.
- `data-density` is `compact`, `comfortable`, or `cozy`.
- `data-motion="reduced"` is present only when the user opts into reduced motion.
- `class="light-mode"` is toggled on `<html>` for legacy CSS rules on light variants.

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

Every frontend must run a pre-paint snippet before CSS paint to avoid theme flash. Open WebUI's implementation lives in [src/app.html](src/app.html) and exposes:

```js
window.__setTheme(id);
window.__setColorScheme(scheme);
window.__setLocale(locale);
```

## 5. Theme Picker UI Contract

A standard picker has:

- Trigger button: `id="theme-picker-btn"`, `[data-theme-picker-btn]`, `.theme-swatch`, `.theme-picker-label`.
- Menu: `id="theme-picker-menu"` with `<li role="option" data-theme="<id>">` rows.
- Mode toggle buttons with `data-mode="light|dark|system"`.

Open WebUI currently consumes the theme but does not add the full picker in this change.

## 6. Contributing A New Theme

1. Add a CSS block in ProxmoxAI `frontend/src/themes-premium.css`.
2. Register `THEME_META[<id>]` in ProxmoxAI `frontend/src/main.js`.
3. Add the picker row in the ProxmoxAI picker UI.
4. Add light variant routing if needed.
5. Smoke test WCAG AA contrast for body and muted text.
6. Copy the updated CSS into [static/static/proxmoxai-themes.css](static/static/proxmoxai-themes.css) for this Open WebUI fork.

## 7. Cross-App Sync

Browser `localStorage` is not shared across subdomains. For cross-subdomain sync, use the VNSO auth preferences API:

```text
GET https://proxmox.vnso.vn/api/v1/auth/preferences
PUT https://proxmox.vnso.vn/api/v1/auth/preferences
```

Fallback when offline or unauthenticated: keep using local `proxmoxai_prefs` with the same JSON shape.
