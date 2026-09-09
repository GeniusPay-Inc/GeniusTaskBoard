/*
 * Geni — mascotte GeniusPay, portée du composant Blade/Alpine.js d'origine
 * vers du JS natif (le back-office et l'écran TV sont des pages statiques
 * FastAPI, sans Laravel ni Alpine). Le SVG est identique à celui fourni ;
 * seule la mécanique de montage/état a été réécrite.
 *
 * Usage :
 *   <div class="geni geni-md" id="mon-geni"></div>
 *   <script>
 *     const geni = Geni.mount(document.getElementById('mon-geni'), { state: 'idle' });
 *     geni.setState('success');
 *   </script>
 */
(function (global) {
  let counter = 0;

  function svgMarkup(uid) {
    return `<svg class="geni-svg" viewBox="0 0 360 400" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Geni, la mascotte GeniusPay">
  <defs>
    <linearGradient id="${uid}-bodyGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffffff"/>
      <stop offset="0.62" stop-color="#f3f8ff"/>
      <stop offset="1" stop-color="#e2ecff"/>
    </linearGradient>
    <linearGradient id="${uid}-tailGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#eef4ff"/>
      <stop offset="0.55" stop-color="#cfe0ff"/>
      <stop offset="1" stop-color="#7db4ff" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="${uid}-cardGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#2563eb"/>
      <stop offset="0.5" stop-color="#0ea5e9"/>
      <stop offset="1" stop-color="#14b8a6"/>
    </linearGradient>
    <linearGradient id="${uid}-coinGrad" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#3b82f6"/>
      <stop offset="1" stop-color="#2563eb"/>
    </linearGradient>
    <radialGradient id="${uid}-auraGrad" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#0ea5e9" stop-opacity="0.55"/>
      <stop offset="0.6" stop-color="#0ea5e9" stop-opacity="0.12"/>
      <stop offset="1" stop-color="#0ea5e9" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <g id="geni-aura">
    <circle id="aura-glow" cx="180" cy="196" r="150" fill="url(#${uid}-auraGrad)"/>
    <g id="aura-rings" class="ac-stroke" fill="none" stroke="#0ea5e9" stroke-opacity="0.35">
      <ellipse cx="180" cy="210" rx="138" ry="70" stroke-width="1.5"/>
      <ellipse cx="180" cy="210" rx="100" ry="50" stroke-width="1.5" stroke-opacity="0.22"/>
    </g>
    <g id="aura-dots" class="ac-fill" fill="#0ea5e9">
      <circle class="p" cx="58"  cy="150" r="3.5"/>
      <circle class="p" cx="312" cy="172" r="4.5"/>
      <circle class="p" cx="300" cy="92"  r="3"/>
      <circle class="p" cx="70"  cy="262" r="3"/>
      <circle class="p" cx="286" cy="276" r="3.5"/>
      <circle class="p" cx="44"  cy="206" r="2.5"/>
      <circle class="p" cx="330" cy="226" r="2.5"/>
    </g>
  </g>

  <g id="geni-tail">
    <path d="M120 196 C104 250, 120 300, 150 344 C160 356, 200 356, 210 344 C242 300, 256 250, 240 196 C214 168, 146 168, 120 196 Z"
      fill="url(#${uid}-tailGrad)"/>
  </g>

  <g id="geni-armL">
    <path d="M126 214 C96 214, 70 200, 58 178" fill="none" stroke="url(#${uid}-bodyGrad)" stroke-width="24" stroke-linecap="round"/>
    <circle id="handL" cx="52" cy="172" r="18" fill="#ffffff" stroke="#cfe0ff" stroke-width="2.5"/>
  </g>

  <g id="geni-armR">
    <path d="M236 214 C266 214, 286 208, 300 206" fill="none" stroke="url(#${uid}-bodyGrad)" stroke-width="24" stroke-linecap="round"/>
    <g id="geni-card" transform="rotate(-14 300 200)">
      <rect x="266" y="150" width="92" height="60" rx="12" fill="url(#${uid}-cardGrad)"/>
      <rect x="276" y="166" width="22" height="16" rx="4" fill="#ffffff" fill-opacity="0.85"/>
      <rect x="276" y="192" width="64" height="6" rx="3" fill="#ffffff" fill-opacity="0.5"/>
    </g>
    <circle id="handR" cx="300" cy="206" r="18" fill="#ffffff" stroke="#cfe0ff" stroke-width="2.5"/>
  </g>

  <g id="geni-head">
    <g id="geni-spark" class="ac-fill" fill="#0ea5e9">
      <path d="M180 12 L185 27 L200 32 L185 37 L180 52 L175 37 L160 32 L175 27 Z"/>
      <circle cx="206" cy="22" r="3"/>
      <circle cx="154" cy="26" r="2.4"/>
    </g>

    <ellipse id="head-shape" cx="180" cy="138" rx="86" ry="80" fill="url(#${uid}-bodyGrad)" stroke="#d3e2ff" stroke-width="2"/>

    <g id="cheeks" opacity="0.9">
      <ellipse cx="132" cy="160" rx="15" ry="9" fill="#5ec8d6" opacity="0.28"/>
      <ellipse cx="228" cy="160" rx="15" ry="9" fill="#5ec8d6" opacity="0.28"/>
    </g>

    <g id="eyes">
      <g id="eyeL">
        <ellipse id="eyeL-ball" cx="150" cy="132" rx="17" ry="21" fill="#0f1f3d"/>
        <circle class="glint" cx="144" cy="124" r="6" fill="#ffffff"/>
        <circle class="glint" cx="156" cy="138" r="2.6" fill="#7fd0ff"/>
        <path class="happy-eye" d="M134 138 Q150 120 166 138" fill="none" stroke="#0f1f3d" stroke-width="6" stroke-linecap="round"/>
        <rect id="lidL" x="131" y="104" width="38" height="52" rx="7" fill="url(#${uid}-bodyGrad)"/>
      </g>
      <g id="eyeR">
        <ellipse id="eyeR-ball" cx="210" cy="132" rx="17" ry="21" fill="#0f1f3d"/>
        <circle class="glint" cx="204" cy="124" r="6" fill="#ffffff"/>
        <circle class="glint" cx="216" cy="138" r="2.6" fill="#7fd0ff"/>
        <path class="happy-eye" d="M194 138 Q210 120 226 138" fill="none" stroke="#0f1f3d" stroke-width="6" stroke-linecap="round"/>
        <rect id="lidR" x="191" y="104" width="38" height="52" rx="7" fill="url(#${uid}-bodyGrad)"/>
      </g>
    </g>

    <g id="brows" stroke="#0f1f3d" stroke-width="5" stroke-linecap="round">
      <line id="browL" x1="134" y1="104" x2="166" y2="100"/>
      <line id="browR" x1="194" y1="100" x2="226" y2="104"/>
    </g>

    <g id="mouth">
      <path class="m m-smile"   d="M158 170 Q180 187 202 170" fill="none" stroke="#0f1f3d" stroke-width="6" stroke-linecap="round"/>
      <path class="m m-grin"    d="M150 166 Q180 204 210 166 Q180 184 150 166 Z" fill="#0f1f3d"/>
      <path class="m m-neutral" d="M166 176 H194" fill="none" stroke="#0f1f3d" stroke-width="6" stroke-linecap="round"/>
      <path class="m m-think"   d="M170 177 Q182 171 196 175" fill="none" stroke="#0f1f3d" stroke-width="6" stroke-linecap="round"/>
    </g>
  </g>

  <g id="geni-coin">
    <circle cx="286" cy="74" r="27" fill="url(#${uid}-coinGrad)"/>
    <circle cx="286" cy="74" r="27" fill="none" stroke="#ffffff" stroke-width="2" stroke-opacity="0.5"/>
    <path d="M276 62 h17 a4 4 0 0 1 4 4 v12 l-9 9 h-12 a4 4 0 0 1 -4 -4 v-17 a4 4 0 0 1 4 -4 Z" fill="#ffffff"/>
  </g>

  <g id="geni-loader">
    <circle cx="180" cy="138" r="58" fill="none" stroke="#0ea5e9" class="ac-stroke" stroke-width="6" stroke-linecap="round" stroke-dasharray="70 320"/>
  </g>
  <g id="geni-check">
    <circle cx="286" cy="74" r="20" fill="#10b981"/>
    <circle cx="286" cy="74" r="20" fill="none" stroke="#ffffff" stroke-width="2" stroke-opacity="0.6"/>
    <path d="M277 75 L283 82 L296 67" fill="none" stroke="#ffffff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
  <g id="geni-think" class="ac-fill" fill="#0ea5e9">
    <circle class="td td1" cx="250" cy="96" r="4"/>
    <circle class="td td2" cx="268" cy="80" r="5.5"/>
    <circle class="td td3" cx="290" cy="62" r="7"/>
  </g>
</svg>`;
  }

  function mount(container, opts) {
    opts = opts || {};
    const state = opts.state || "idle";
    const size = opts.size || "md";
    const uid = "geni" + counter++;

    container.classList.add("geni");
    if (size) container.classList.add("geni-" + size);
    container.innerHTML = svgMarkup(uid);
    const svg = container.querySelector("svg.geni-svg");
    svg.setAttribute("data-state", state);

    return {
      el: svg,
      setState(next) {
        svg.setAttribute("data-state", next);
      },
    };
  }

  global.Geni = { mount: mount };
})(window);
