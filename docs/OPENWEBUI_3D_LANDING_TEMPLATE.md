# Open WebUI 3D Landing Template

## Muc tieu

Template nay dung de tao landing GitHub Pages kieu cinematic cho Open WebUI: hero thien nhien co chieu sau, scroll di vao khung canh, sau do moi reveal noi dung san pham va UI workspace.

Huong chon trong landing hien tai la CSS 3D parallax + requestAnimationFrame scroll engine. Day la huong thuc dung nhat cho GitHub Pages: dep, nhe hon Three.js, de deploy tinh, va van tao duoc cam giac camera-depth.

## Cau truc file

- `docs/index.html`: standalone HTML/CSS/JS, khong can build pipeline.
- `docs/assets/logo.png`: logo wordmark.
- `docs/assets/favicon.ico`: favicon dang PNG data nhung dung duoc qua link icon.
- External visual assets: Unsplash images + Pexels MP4.
- External icon library: Lucide UMD CDN.

## Concept scroll

Landing duoc chia thanh cac phase:

1. Intro nature view: viewport dau tien gan nhu khong co chu, chi co logo va canh nui/rung/may.
2. Depth entry: khi scroll, camera di sau vao landscape, cac layer di chuyen khac toc do.
3. Product reveal: title, CTA, proof row va command deck bat dau xuat hien sau khoang 1 viewport.
4. Product storytelling: moi section co depth-shape rieng de tao cam giac full-page parallax.
5. Landing close: CTA va footer giam motion de user ha canh.

## CSS core

```css
.global-scene {
  position: fixed;
  inset: -12vh -8vw;
  perspective: 1600px;
  transform-style: preserve-3d;
}

.depth-stage {
  position: sticky;
  top: 0;
  height: 100vh;
  perspective: 1280px;
  transform-style: preserve-3d;
}

.scene-layer,
.depth-shape {
  will-change: transform, opacity, filter;
}
```

## JavaScript core

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

## Hero depth mapping

Hero nen dung nhieu layer:

- Poster/background mountain: di cham, scale lon dan.
- Video fog/mountain: opacity vua phai de khong de mat anh nen.
- Mountain ridge: translateY cham hon foreground.
- Valley/forest: translateY nhanh hon de tao depth.
- Cloud/fog overlay: blur + mix-blend-mode screen.
- UI deck/text: reveal tre sau intro, translateZ tu sau ra truoc.

Cong thuc dang dung:

```js
const contentIn = clamp((progress - 0.22) / 0.16);
const contentOut = clamp((0.84 - progress) / 0.18);
const contentVisibility = Math.min(contentIn, contentOut);
```

Nghia la chu khong hien ngay o top page. User scroll qua nature view truoc, sau do content moi vao.

## Full-page parallax sections

Moi section co block:

```html
<div class="section-depth" aria-hidden="true">
  <span class="depth-shape one" data-section-depth="0.10"></span>
  <span class="depth-shape two" data-section-depth="0.22"></span>
  <span class="depth-shape three" data-section-depth="0.34"></span>
</div>
```

Scroll engine tinh vi tri section theo viewport center:

```js
const rect = layer.closest('section').getBoundingClientRect();
const centerOffset = (rect.top + rect.height / 2 - window.innerHeight / 2) / window.innerHeight;
const y = centerOffset * depth * -220;
const z = depth * 280;
layer.style.transform = `translate3d(0, ${y}px, ${z}px)`;
```

## Theme mode

Landing co 3 mode:

- `dark`: cinematic default.
- `light`: phu hop enterprise/daytime.
- `system`: theo OS.

Hero van giu mood toi; cac section duoi dung CSS variables de sang/toi mem hon.

## Nguyen tac UI/UX

- Viewport dau tien uu tien visual, khong nhieu text.
- Text/product message reveal sau khi user da vao scene.
- Dung parallax cho depth, khong lam moi element bay lung tung.
- Luon co progress bar va nav de user khong bi lac.
- Mobile phai tat bot deck phuc tap, giu hero nhe va khong overflow ngang.
- Video chi la lop nang cap; poster/image fallback phai dep neu video khong load.

## Checklist truoc khi push

- `docs/index.html` chi co mot document HTML.
- Local assets `docs/assets/logo.png` va `docs/assets/favicon.ico` load OK.
- Khong con file image/icon co hau to `(1)`.
- Browser preview khong overflow ngang desktop/mobile.
- Scroll depth lam thay doi transform cua hero va section layers.
- Console khong co warning/error.
- `npm run build` pass neu thay doi lien quan static/frontend.
