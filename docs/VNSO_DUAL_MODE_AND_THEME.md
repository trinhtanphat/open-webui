# VNSO Dual-Mode Chat & Theme Implementation

This document keeps the project implementation aligned with [AI_CONTEXT.md](../AI_CONTEXT.md) and [THEME_CONTRACT.md](../THEME_CONTRACT.md).

## Product Direction

The long-term choice is a hybrid chat-native graph experience:

- Linear Chat remains the default reading and streaming experience.
- Mind Map View is embedded in the chat surface for branch navigation, pan, zoom, and active branch visualization.
- The implementation uses `@xyflow/svelte` and `dagre` rather than a hand-rolled graph engine because the product requires a real canvas, edges, zooming, panning, and custom nodes.
- The existing Overview feature remains a separate graph-oriented surface; Mind Map View is optimized for chat branch navigation.

## Files

| Area             | File                                                                                                                     | Responsibility                                                                     |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| Chat shell       | [../src/lib/components/chat/Chat.svelte](../src/lib/components/chat/Chat.svelte)                                         | Owns `viewMode` and `history.currentId`; conditionally renders Linear or Mind Map. |
| Header controls  | [../src/lib/components/chat/Navbar.svelte](../src/lib/components/chat/Navbar.svelte)                                     | Shows segmented Linear/Mind Map toggle and theme picker.                           |
| Mind Map wrapper | [../src/lib/components/chat/MindMapMessages.svelte](../src/lib/components/chat/MindMapMessages.svelte)                   | Wraps the canvas in `SvelteFlowProvider`.                                          |
| Mind Map canvas  | [../src/lib/components/chat/MindMapMessages/Canvas.svelte](../src/lib/components/chat/MindMapMessages/Canvas.svelte)     | Converts history to nodes/edges and runs Dagre layout.                             |
| Mind Map node    | [../src/lib/components/chat/MindMapMessages/ChatNode.svelte](../src/lib/components/chat/MindMapMessages/ChatNode.svelte) | Plain-text preview, avatar, active badge, active-branch styling.                   |
| Theme picker     | [../src/lib/components/common/ThemeModeToggle.svelte](../src/lib/components/common/ThemeModeToggle.svelte)               | Family picker for Anthropic, Vercel, GitHub, Linear, Stripe, Notion, etc.          |
| Theme bootstrap  | [../src/app.html](../src/app.html)                                                                                       | Pre-paint `proxmoxai_prefs` hydration and setter API.                              |
| Theme CSS        | [../static/static/custom.css](../static/static/custom.css)                                                               | Bridge Open WebUI surfaces to VNSO variables.                                      |

## Required Behavior

1. The user can toggle between Linear Chat and Mind Map View from the chat header.
2. Both views share the same `history` object.
3. Clicking a node in Mind Map View updates `history.currentId`.
4. Switching back to Linear Chat shows the selected branch.
5. Mind Map View supports pan, zoom, top-to-bottom layout, and left-to-right layout.
6. Custom nodes must render plain text previews only. Do not render arbitrary HTML in nodes.
7. Theme family + light/dark/system mode must update live through `proxmoxai_prefs` and `<html data-theme>`.

## Svelte Flow Rule

Any component using `useSvelteFlow()`, `useStore()`, or `useNodesInitialized()` must be rendered inside `<SvelteFlowProvider>`. The wrapper/canvas split is intentional:

```svelte
<SvelteFlowProvider>
	<Canvas bind:history {onNodeSelect} />
</SvelteFlowProvider>
```

Do not move Svelte Flow hooks back into the wrapper component unless the provider remains above them in the component tree.

## Theme Smoke Test

1. Open the chat header theme picker.
2. Select `Anthropic`, `Vercel`, `GitHub`, `Linear`, `Stripe`, and `Notion`.
3. Toggle `Light`, `Dark`, and `System`.
4. Confirm `localStorage.proxmoxai_prefs` updates.
5. Confirm `<html data-theme="...">` changes without reload.

## Build Notes

- `npm run build` is the production gate.
- `npm run check` can report existing upstream type debt; use file-level diagnostics for focused frontend changes.
- `npm run build` runs `pyodide:fetch`; revert generated `static/pyodide/pyodide-lock.json` churn unless Pyodide was intentionally updated.
