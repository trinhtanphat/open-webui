(function () {
  "use strict";
  if (window.__vnsoDepthPromptInstalled) return;
  window.__vnsoDepthPromptInstalled = true;

  var PROMPT = "A chaotic urban scene freezes instantly mid-motion, people, debris, and particles suspended in air, opening on a slow dolly through frozen elements, camera weaving between floating glass shards and halted explosions, then a glowing pulse begins forming at the center, time slowly cracking like glass, camera pushing closer as fractures spread across reality, ending with a sudden release where everything resumes at once in an explosive burst of motion and energy.";
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function injectCss() {
    if (document.getElementById("vnso-depth-prompt-css")) return;
    var style = document.createElement("style");
    style.id = "vnso-depth-prompt-css";
    style.textContent = [
      "html.vnso-depth-prompt-ready{overflow-x:hidden;}",
      "html.vnso-depth-prompt-ready body{overflow-x:hidden;background:transparent;}",
      ".vnso-depth-scene{position:fixed;inset:-10vh -8vw;z-index:0;pointer-events:none;overflow:hidden;background:radial-gradient(circle at 18% 18%,rgba(56,189,248,.20),transparent 30%),radial-gradient(circle at 82% 24%,rgba(34,197,94,.16),transparent 32%),linear-gradient(145deg,rgba(4,9,22,.92),rgba(8,24,44,.82) 52%,rgba(4,9,22,.94));}",
      ".vnso-depth-scene span{position:absolute;inset:0;will-change:transform;}",
      ".vnso-depth-scene .grid{opacity:.20;background-image:linear-gradient(90deg,rgba(125,211,252,.20) 1px,transparent 1px),linear-gradient(180deg,rgba(74,222,128,.16) 1px,transparent 1px);background-size:96px 96px;mask-image:radial-gradient(circle at 50% 34%,#000 0,transparent 72%);}",
      ".vnso-depth-scene .freeze{opacity:.26;background:radial-gradient(circle at var(--pulse-x,50%) var(--pulse-y,45%),rgba(255,255,255,.20),transparent 13%),radial-gradient(circle at 50% 45%,rgba(125,211,252,.14),transparent 34%);}",
      "html.vnso-depth-prompt-ready body>:not(.vnso-depth-scene):not(.vnso-freeze-prompt){position:relative;z-index:1;}",
      ".vnso-freeze-prompt{position:fixed;right:16px;bottom:16px;z-index:9998;width:min(420px,calc(100vw - 32px));border:1px solid rgba(125,211,252,.28);border-radius:8px;background:rgba(5,12,26,.82);color:#e5f7ff;box-shadow:0 20px 70px rgba(0,0,0,.32);backdrop-filter:blur(14px);font:500 13px/1.45 system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}",
      ".vnso-freeze-prompt details{padding:12px 14px;}",
      ".vnso-freeze-prompt summary{cursor:pointer;font-weight:800;color:#bae6fd;list-style:none;}",
      ".vnso-freeze-prompt summary::-webkit-details-marker{display:none;}",
      ".vnso-freeze-prompt p{margin:10px 0 0;color:#d6eef8;}",
      "@media(max-width:700px){.vnso-freeze-prompt{left:12px;right:12px;bottom:12px;width:auto;}.vnso-freeze-prompt p{max-height:28vh;overflow:auto;}}",
      "@media(prefers-reduced-motion:reduce){.vnso-depth-scene{display:none!important;}}"
    ].join("");
    document.head.appendChild(style);
  }

  function boot() {
    injectCss();
    document.documentElement.classList.add("vnso-depth-prompt-ready");
    var scene = document.getElementById("vnso-depth-scene");
    if (!scene) {
      scene = document.createElement("div");
      scene.id = "vnso-depth-scene";
      scene.className = "vnso-depth-scene";
      scene.setAttribute("aria-hidden", "true");
      scene.innerHTML = '<span class="grid" data-depth-layer="0.10"></span><span class="freeze" data-depth-layer="0.26"></span>';
      document.body.insertBefore(scene, document.body.firstChild);
    }
    if (!document.getElementById("vnso-freeze-prompt")) {
      var card = document.createElement("aside");
      card.id = "vnso-freeze-prompt";
      card.className = "vnso-freeze-prompt";
      card.innerHTML = '<details><summary>Pixverse Freeze Scene</summary><p>' + PROMPT + '</p></details>';
      document.body.appendChild(card);
    }
    if (reduceMotion) return;
    var layers = Array.prototype.slice.call(scene.querySelectorAll("[data-depth-layer]"));
    var ticking = false;
    var lastY = -1;
    function update() {
      ticking = false;
      var scrollY = window.scrollY || document.documentElement.scrollTop || 0;
      if (Math.abs(scrollY - lastY) < 1) return;
      lastY = scrollY;
      var vh = Math.max(1, window.innerHeight || document.documentElement.clientHeight || 800);
      var maxScroll = Math.max(1, document.documentElement.scrollHeight - vh);
      var progress = Math.max(0, Math.min(1, scrollY / maxScroll));
      scene.setAttribute("data-frame", String(Math.round(progress * 120)));
      scene.style.setProperty("--pulse-x", 45 + Math.sin(progress * Math.PI * 2) * 12 + "%");
      scene.style.setProperty("--pulse-y", 38 + Math.cos(progress * Math.PI * 2) * 8 + "%");
      layers.forEach(function (layer) {
        var depth = Number(layer.getAttribute("data-depth-layer")) || 0.1;
        layer.style.transform = "translate3d(" + (Math.sin(progress * Math.PI * 2 + depth) * depth * 22) + "px," + (scrollY * depth * -0.12) + "px,0) scale(" + (1 + depth * 0.2) + ")";
      });
    }
    function requestUpdate() {
      if (ticking) return;
      ticking = true;
      (window.requestAnimationFrame || function (fn) { window.setTimeout(fn, 16); })(update);
    }
    window.addEventListener("scroll", requestUpdate, { passive: true });
    window.addEventListener("resize", function () { lastY = -1; requestUpdate(); });
    requestUpdate();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot, { once: true });
  else boot();
})();
