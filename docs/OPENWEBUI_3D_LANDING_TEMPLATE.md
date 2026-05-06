# Open WebUI 3D Landing Template

## Goal

This template describes the cinematic GitHub Pages landing page for Open WebUI: an immersive nature-led hero, a scroll-driven camera journey, then a product-focused workspace story with model routing, RAG, agents, governance, deployment, and HA messaging.

The current implementation uses a scroll-driven procedural canvas world, CSS 3D parallax, and a `requestAnimationFrame` scroll engine. The canvas works like a lightweight image sequence: scroll maps to a frame/camera timeline, while the real HTML interface stays as an accessible overlay above the scene.

## File Structure

- `docs/index.html`: standalone HTML/CSS/JS with no build pipeline required for GitHub Pages.
- `docs/assets/logo.png`: local wordmark asset.
- `docs/assets/favicon.ico`: local favicon asset; the file contains PNG image data and is linked as an icon.
- External visual assets: Unsplash still imagery and a Pexels MP4 for fog/mountain atmosphere.
- External icon library: Lucide UMD CDN.
- Procedural canvas world: avoids shipping a large 100-300 frame image sequence while preserving a continuous timeline/camera feel.

## Scroll Concept

The landing is split into five phases:

1. Intro nature view: the first viewport is almost text-free, showing brand, mountains, forest, fog, and motion cues.
2. Depth entry: scroll moves the camera from close-up to farther away; the canvas world and CSS layers move together.
3. Product reveal: headline, CTA, proof row, and command deck appear after the visual introduction.
4. Product storytelling: the fixed canvas keeps moving across the whole page while each section adds its own parallax depth and product checkpoint.
5. Landing close: the CTA and footer reduce motion so the user can land cleanly.

## CSS Core

```css
.global-scene {
  position: fixed;
  inset: -12vh -8vw;
  perspective: 1600px;
  transform-style: preserve-3d;
}

.world-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.depth-stage {
  position: sticky;
  top: 0;
  height: 100vh;
  perspective: 1280px;
  transform-style: preserve-3d;
}

.scene-layer,
.depth-shape,
[data-story-surface],
[data-story-card] {
  will-change: transform, opacity, filter;
}
```

## JavaScript Core

```js
const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
let ticking = false;

function requestUpdate() {
  if (!ticking) {
    window.requestAnimationFrame(update);
    ticking = true;
  }
}

window.addEventListener('scroll', requestUpdate, { passive: true });
window.addEventListener('resize', requestUpdate);
```

## Canvas World Timeline

The canvas is a continuous full-page world inspired by scroll-driven image-sequence sites. Instead of loading hundreds of exported frames, the page draws a new procedural frame on each scroll update:

- sky gradient
- mountain ridges
- depth tunnel lines
- fog ellipses
- floating product UI panels
- vignette

Core mapping:

```js
const pageProgress = scrollY / (document.documentElement.scrollHeight - window.innerHeight);
const heroProgress = clamp((scrollY - journey.offsetTop) / (journey.offsetHeight - window.innerHeight));
const frame = Math.round(pageProgress * 220);
renderWorld(scrollY, pageProgress, heroProgress);
```

Reverse depth / zoom-out:

```js
const zoomOut = easeOutCubic(heroProgress / 0.52);
const cameraScale = 1.72 - zoomOut * 0.64;
```

At the top, the camera starts close to the world. As the user scrolls, the scale decreases, making the scene feel smaller, farther away, and more map-like.

## Hero Depth Mapping

The hero uses multiple layers:

- Poster/background mountain: starts large, then scales down while scrolling to create the zoom-out.
- Video fog/mountain: moderate opacity so the still image remains readable.
- Mountain ridge: slower vertical motion than the foreground.
- Valley/forest: faster vertical motion for stronger depth.
- Cloud/fog overlay: blur and screen blend for atmosphere.
- UI deck/text: delayed reveal after the intro, moving from rear depth into the interface plane.

Current visibility mapping:

```js
const contentIn = clamp((progress - 0.22) / 0.16);
const contentOut = clamp((0.84 - progress) / 0.18);
const contentVisibility = Math.min(contentIn, contentOut);
```

The headline is intentionally hidden at the very top. The user first moves through the visual scene, then the product message appears.

## Full-Page Parallax Sections

Every product section includes depth geometry:

```html
<div class="section-depth" aria-hidden="true">
  <span class="depth-shape one" data-section-depth="0.10"></span>
  <span class="depth-shape two" data-section-depth="0.22"></span>
  <span class="depth-shape three" data-section-depth="0.34"></span>
</div>
```

The lower page also uses surface/card transforms so the bottom sections do not feel flat:

```js
const centerOffset = (rect.top + rect.height / 2 - window.innerHeight / 2) / window.innerHeight;
const y = centerOffset * depth * -220;
const z = depth * 280;
layer.style.transform = `translate3d(0, ${y}px, ${z}px)`;
```

For product cards and section surfaces, keep movement subtle. The goal is a full-page camera feel, not a distracting floating dashboard.

## Theme Mode

The landing has three modes:

- `dark`: cinematic default.
- `light`: enterprise/daytime presentation.
- `system`: follows the OS color scheme.

The hero keeps a darker cinematic mood. Lower sections use CSS variables and translucent bands so the fixed canvas remains visible while text stays readable.

## UI/UX Rules

- The first viewport prioritizes visual immersion and avoids heavy text.
- Product messaging reveals only after the user has entered the scene.
- Use parallax for depth, not random floating motion.
- Keep the progress bar and navigation available so users understand page position.
- On mobile, simplify the command deck and keep horizontal overflow at zero.
- The video is an enhancement layer; the poster/fallback image must look complete without it.
- Lower-page cards and panels should have subtle parallax, stable dimensions, and no text overlap.

## Validation Checklist

- `docs/index.html` contains a single complete HTML document.
- `docs/assets/logo.png` and `docs/assets/favicon.ico` load locally.
- No tracked image/icon files use the `(1)` suffix.
- Top viewport has no visible hero headline copy.
- Canvas pixel sampling is nonblank at top and changes after scrolling.
- `#worldCanvas[data-frame]` increases with page scroll.
- Hero poster scale starts near `1.74` and shrinks during scroll.
- Lower product sections show visible parallax transforms, not only the hero.
- Desktop and mobile preview have no horizontal overflow.
- Browser console has no warnings/errors caused by the landing.
- `npm run build` passes when frontend/static changes are part of the branch.
