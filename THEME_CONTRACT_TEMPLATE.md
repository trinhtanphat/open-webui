# VNSO Cloud — Shared Theme Contract

Canonical design-system contract for **all VNSO Cloud frontends** (ProxmoxAI, ems, cloud-platform, hrm-platform, Cerberus dashboard, cloudstack UI, etc.).

The reference implementation lives at [ProxmoxAI/frontend/src/main.js](ProxmoxAI/frontend/src/main.js) (search `PREFS_KEY`) and [ProxmoxAI/frontend/src/themes-premium.css](ProxmoxAI/frontend/src/themes-premium.css). Every other frontend MUST mirror the same contract so a user's theme choice carries cross-app via shared `localStorage`.

---

## 1. Storage contract

| Key | Value type | Owner | Notes |
| --- | --- | --- | --- |
| `proxmoxai_prefs` | JSON | shared | Single source of truth, written by ProxmoxAI; **all sibling apps read & merge same shape** |
| `proxmoxai_prefs.theme` | string | shared | Family id (e.g. `anthropic`, `v0`, `github-dim`, `linear`, `stripe`, `notion`, `vercel-light` …) |
| `proxmoxai_prefs.color_scheme` | `'light' \| 'dark' \| 'system'` | shared | Independent axis from `theme` family |
| `proxmoxai_prefs.locale` | `'vi' \| 'en'` | shared | |
| `proxmoxai_prefs.density` | `'compact' \| 'comfortable' \| 'cozy'` | shared | |
| `proxmoxai_prefs.reduced_motion` | boolean | shared | |
| `proxmoxai_prefs.sidebar_collapsed` | boolean | shared | |

**Rule:** never invent a new top-level key. Extending the schema requires adding the field to `DEFAULT_PREFS` in ProxmoxAI first and then to every consumer.

---

## 2. DOM contract

```html
<html data-theme="anthropic" data-density="comfortable" lang="vi">
```

- `data-theme` is the **resolved** id (family OR variant for light mode, e.g. `anthropic-light`).
- `data-density` ∈ `compact | comfortable | cozy`.
- `data-motion="reduced"` when user opts into reduced motion.
- `class="light-mode"` toggled on `<html>` for legacy CSS rules (light variants only).

CSS contract — every theme block MUST set these CSS variables on `html[data-theme="<id>"]`:

```
--bg            --bg-secondary  --bg-tertiary
--card-bg       --sidebar-bg
--text          --text-muted
--primary       --primary-dim   --primary-glow
--accent
--success       --warning       --danger
--border        --border-glow
--radius
```

Optional but recommended for premium themes: `--bg-card`, `--bg-card-hov`, `--bg-elev`, `--bg-input`, `--shadow-card`, `--code-bg`, `--text-dim`.

---

## 3. Theme catalog (canonical IDs)

### Dark families
`midnight` (default) · `cursor` · `anthropic` · `v0` (Vercel) · `perplexity` · `synthwave` · `aurora` · `nebula` · `nord` · `solarized` · `contrast` · `dracula` · `tokyo-night` · `github-dim` · `monokai` · `gruvbox` · `catppuccin` · `rosepine` · `oceanic` · `terminal` · `discord` · `linear` · `figma` · `raycast` · `supabase` · `railway`

### Light families
`light` · `sakura` · `sepia` · `paper` · `arctic` · `pastel-dream` · `porcelain` · `platinum` · `spring` · `summer` · `minimal-light` · `stripe` · `notion`

### Light variants of a dark family (auto-routed via `color_scheme: 'light'`)
- `anthropic` → `anthropic-light`
- `v0` → `vercel-light`
- `github-dim` → `github-light`

### Sentinel
- `system` — resolves to `light` if OS prefers light, else `midnight`.

---

## 4. JS bootstrap contract

Every frontend MUST run an inline pre-paint snippet in `<head>` before any CSS paint to avoid theme flash:

```html
<script>
(function () {
  try {
    var raw = localStorage.getItem('proxmoxai_prefs');
    var p = raw ? JSON.parse(raw) : {};
    var theme = p.theme || 'midnight';
    var scheme = p.color_scheme || 'system';
    var LIGHT_VARIANTS = { anthropic:'anthropic-light', v0:'vercel-light', 'github-dim':'github-light' };
    if (theme === 'system') {
      theme = (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) ? 'light' : 'midnight';
    }
    if (scheme === 'light' && LIGHT_VARIANTS[theme]) theme = LIGHT_VARIANTS[theme];
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-density', p.density || 'comfortable');
    if (p.reduced_motion) document.documentElement.setAttribute('data-motion', 'reduced');
    document.documentElement.lang = p.locale || 'vi';
  } catch (_) {}
})();
</script>
```

---

## 5. Theme-picker UI contract

A standard dropdown component lives at `theme-kit/theme-picker.html` (snippet) with:

- Trigger button: `id="theme-picker-btn"` carrying `[data-theme-picker-btn]`, contains `.theme-swatch` + `.theme-picker-label`.
- Menu: `id="theme-picker-menu"` with `<li role="option" data-theme="<id>">…</li>` rows.
- Mode toggle (light / dark / system): three buttons with `data-mode` attribute inside `.auth-mode-toggle`.

The shared bootstrap also exposes:

```js
window.__setTheme(id)      // family or variant
window.__setColorScheme(s) // 'light' | 'dark' | 'system'
window.__setLocale(loc)    // 'vi' | 'en'
```

---

## 6. Contributing a new theme

1. Add a CSS block in [ProxmoxAI/frontend/src/themes-premium.css](ProxmoxAI/frontend/src/themes-premium.css) targeting `html[data-theme="<id>"]` and define every required variable.
2. Register `THEME_META[<id>]` in [ProxmoxAI/frontend/src/main.js](ProxmoxAI/frontend/src/main.js).
3. Add an `<li role="option" data-theme="<id>">` to the picker menu in `index.html`.
4. If it's a light variant of a dark family, add to `LIGHT_VARIANTS` map.
5. Smoke test against WCAG AA contrast for body + muted text.

---

## 7. Cross-app sync

- All apps share the **same eTLD+1** under `vnso.vn`. `localStorage` is **NOT** shared across subdomains by browsers.
- For cross-subdomain sync we MUST use the auth API at `https://proxmox.vnso.vn/api/v1/auth/preferences` (GET to hydrate, PUT to persist). After login, every consumer hydrates `_prefs` from the user object's `preferences` field.
- Fallback when offline / unauthenticated: each app uses its own `localStorage` key but follows the same JSON shape.

---

## 8. Drop-in kit

For new frontends without a theme system yet, drop in:
- [theme-kit/theme.css](theme-kit/theme.css) — every required theme block (built from ProxmoxAI source)
- [theme-kit/theme.js](theme-kit/theme.js) — bootstrap + setter API
- [theme-kit/theme-picker.html](theme-kit/theme-picker.html) — UI snippet

These three files are the **only** integration surface a sibling frontend needs.
