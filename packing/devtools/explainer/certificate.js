(() => {
  /* Certificate {{ID}} */
  const ATOM_Q = [__SQUARES_ATOMS__];
  const ATOMS = ATOM_Q.map(([xn, xd, yn, yd, w]) => [xn / xd, yn / yd, w]);
  const SCALE = __SQUARES_SCALE__,
    L = __SQUARES_L__,
    B = __SQUARES_B__,
    HALF = B / 2;
  const LIMIT_N = __SQUARES_LIMIT_NUM__,
    LIMIT_D = __SQUARES_LIMIT_DEN__,
    LIMIT = LIMIT_N / LIMIT_D,
    STEPS = __SQUARES_STEPS__;

  const gcd = (a, b) => (b ? gcd(b, a % b) : a);
  const reduce = (n, d) => {
    const g = gcd(n, d) || 1;
    return [n / g, d / g];
  };
  const fracTex = (n, d) => (d === 1 ? String(n) : `${n}/${d}`);

  /* Angles are the one thing on this page that cannot be printed exactly. A net
   angle is 2*arctan of a rational, so its degree measure is irrational, and so
   is any angle the reader drags to; the digits a readout shows are a rounding
   of it and say so. Zero is the one angle that prints exactly, which is why
   the mark is conditional rather than blanket: at k = 0 the readout states the
   angle as an equality, and means it.

   `nearly` marks a value standing on its own — grouped, so KaTeX sets the sign
   as an ordinary symbol rather than spacing it as a relation — and `degRel`
   marks one introduced by a relation, by replacing the relation. */
  const deg = (a, places) => ((a * 180) / Math.PI).toFixed(places);
  const nearly = (text) => `{\\approx}\\,${text}`;
  const degTex = (a, places, exact = a === 0) => (exact ? deg(a, places) : nearly(deg(a, places)));
  const degRel = (a, places, exact = a === 0) => `${exact ? "=" : "\\approx"} ${deg(a, places)}`;
  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  /* The shared renderer gates every call, including the ResizeObserver's initial
   redraw and input received while fonts are loading. It selects the context's face
   and metrics together before revealing the result. */
  const tex = squaresMath.render;
  /* A readout that is replaced rather than slid fades in (see `.swap`); one
   that already shows the text is left alone, so leaving and re-entering a
   figure does not blink it. */
  const swap = (el) => {
    el.classList.remove("swap");
    void el.offsetWidth;
    el.classList.add("swap");
  };
  const setText = (el, text) => {
    if (el.textContent !== text) {
      el.textContent = text;
      swap(el);
    }
  };

  function rot(t) {
    const d = 1 + t * t;
    return [(1 - t * t) / d, (2 * t) / d];
  }
  function netT(k) {
    return (LIMIT * k) / STEPS;
  }

  /* The direction the figure is computing at. The slider sets a net direction,
   exactly, from its half-tangent; the handle sets any angle at all. Everything
   downstream reads cs and sn only, so a direction off the net costs nothing. */
  let sorted = [],
    cs = 1,
    sn = 0,
    angle = 0,
    onNet = true;
  function resort() {
    sorted = ATOMS.map((a) => [cs * a[0] + sn * a[1], -sn * a[0] + cs * a[1], a[2]]).sort(
      (p, q) => p[0] - q[0],
    );
  }
  function setDir(k) {
    heat = null;
    curK = k;
    onNet = true;
    [cs, sn] = rot(netT(k));
    angle = Math.atan2(sn, cs);
    resort();
  }
  function setAngle(a) {
    const TAU = 2 * Math.PI;
    heat = null;
    angle = ((a % TAU) + TAU) % TAU;
    onNet = false;
    cs = Math.cos(angle);
    sn = Math.sin(angle);
    resort();
  }
  function lowerBound(u) {
    let lo = 0,
      hi = sorted.length;
    while (lo < hi) {
      const m = (lo + hi) >> 1;
      if (sorted[m][0] < u) {
        lo = m + 1;
      } else {
        hi = m;
      }
    }
    return lo;
  }

  /* Counting and highlighting use identical edge comparisons. Floating-point
   subtraction can disagree with an equivalent absolute-difference test. */
  function covered(u, v, cu, cv) {
    return u >= cu - HALF && u <= cu + HALF && v >= cv - HALF && v <= cv + HALF;
  }
  function massAt(x, y) {
    const u = cs * x + sn * y,
      v = -sn * x + cs * y;
    let i = lowerBound(u - HALF),
      tot = 0;
    for (; i < sorted.length && sorted[i][0] <= u + HALF; i++) {
      if (covered(sorted[i][0], sorted[i][1], u, v)) {
        tot += sorted[i][2];
      }
    }
    return tot;
  }
  function inset() {
    return (B * (Math.abs(cs) + Math.abs(sn))) / 2;
  }
  function admissible(x, y) {
    const h = inset();
    return x >= h - 1e-12 && x <= L - h + 1e-12 && y >= h - 1e-12 && y <= L - h + 1e-12;
  }

  /* The canvas keeps pan-y. A native overlay owns rotation, touch capture and
   keyboard input, and supplies the same endpoint the canvas uses for its stem. */
  function rotationHandle(canvas, { id, label, point, angleAt, getAngle, rotate, finish, redraw }) {
    const stage = canvas.parentElement,
      button = document.createElement("button");
    button.type = "button";
    button.id = id;
    button.className = "rotation-handle";
    button.setAttribute("aria-label", label);
    button.setAttribute("aria-keyshortcuts", "ArrowLeft ArrowRight ArrowUp ArrowDown");
    button.title =
      "Drag to rotate. Tap or press Enter for 5°. Arrow keys adjust by 1°; Shift by 10°.";
    /* An inline icon rather than the `↺` character. No face this page ships carries
     U+21BA, so as text it is drawn from whatever family the reader's machine has --
     a different mark for every reader, and a finding in
     `inspect_explainer_typography --check-supporting`, which holds every run inside
     the document to a shipped face. Drawn on `currentColor` in the stroke language
     kpress's own control icons use, so the handle needs no face at all. */
    button.innerHTML =
      '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"' +
      ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"' +
      ' stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/>' +
      '<path d="M3 3v5h5"/></svg>';
    stage.append(button);

    function update() {
      const box = canvas.getBoundingClientRect(),
        frame = stage.getBoundingClientRect();
      const [x, y] = point();
      button.hidden = !box.width || !box.height;
      if (button.hidden) {
        return [x, y];
      }
      /* A square may be moved to the container edge. Keep the whole target in
       view, and return its clamped position so the connector still meets it. */
      const px = Math.max(22, Math.min(box.width - 22, (x * box.width) / canvas.width));
      const py = Math.max(22, Math.min(box.height - 22, (y * box.height) / canvas.height));
      button.style.left = `${box.left - frame.left + px}px`;
      button.style.top = `${box.top - frame.top + py}px`;
      return [(px * canvas.width) / box.width, (py * canvas.height) / box.height];
    }

    let pointer = null,
      startX = 0,
      startY = 0,
      offset = 0,
      dragged = false,
      suppressClick = false;
    button.addEventListener("pointerdown", (e) => {
      if (pointer !== null || !e.isPrimary || e.button !== 0) {
        return;
      }
      pointer = e.pointerId;
      startX = e.clientX;
      startY = e.clientY;
      /* Grabbing the edge of the enlarged or clamped target must not jump the
       square to the pointer's initial angle. */
      offset = getAngle() - angleAt(e);
      dragged = false;
      suppressClick = false;
      button.dataset.dragging = "";
      button.setPointerCapture(pointer);
    });
    button.addEventListener("pointermove", (e) => {
      if (e.pointerId !== pointer) {
        return;
      }
      if (!dragged && Math.hypot(e.clientX - startX, e.clientY - startY) < 3) {
        return;
      }
      dragged = true;
      suppressClick = true;
      rotate(angleAt(e) + offset);
    });
    function end(e) {
      if (e.pointerId !== pointer) {
        return;
      }
      pointer = null;
      delete button.dataset.dragging;
      if (button.hasPointerCapture(e.pointerId)) {
        button.releasePointerCapture(e.pointerId);
      }
      if (dragged && finish) {
        finish();
      }
      if (e.type === "pointercancel") {
        suppressClick = false;
      }
    }
    button.addEventListener("pointerup", end);
    button.addEventListener("pointercancel", end);
    button.addEventListener("lostpointercapture", end);
    button.addEventListener("click", (e) => {
      if (suppressClick && e.detail > 0) {
        suppressClick = false;
        return;
      }
      rotate(getAngle() + (5 * Math.PI) / 180);
      if (finish) {
        finish();
      }
    });
    button.addEventListener("keydown", (e) => {
      const direction = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1 }[e.key];
      if (!direction) {
        return;
      }
      e.preventDefault();
      rotate(getAngle() + (direction * (e.shiftKey ? 10 : 1) * Math.PI) / 180);
      if (finish) {
        finish();
      }
    });
    const observer = new ResizeObserver(redraw);
    observer.observe(canvas);
    observer.observe(stage);
    return { update };
  }

  /* ---------- Figure 4: the atoms ---------- */
  const fc = /** @type {HTMLCanvasElement} */ (document.getElementById("field-{{SLUG}}")),
    fg = fc.getContext("2d");
  const FS = fc.width,
    FM = FS * 0.055,
    FPX = FS - 2 * FM,
    FSC = FPX / L;
  const MAXW = Math.max(...ATOMS.map((a) => a[2]));
  const fieldTip = document.getElementById("field-tip-{{SLUG}}");
  let hovered = -1;

  function drawField() {
    fg.clearRect(0, 0, FS, FS);
    fg.fillStyle = css("--kpress-doc-bg");
    fg.fillRect(0, 0, FS, FS);
    fg.strokeStyle = css("--kpress-doc-border");
    fg.lineWidth = 1;
    fg.setLineDash([4, 6]);
    for (let i = 1; i <= 3; i++) {
      const p = FM + (FPX * i) / L;
      fg.beginPath();
      fg.moveTo(p, FM);
      fg.lineTo(p, FM + FPX);
      fg.moveTo(FM, p);
      fg.lineTo(FM + FPX, p);
      fg.stroke();
    }
    fg.setLineDash([]);
    fg.strokeStyle = css("--kpress-doc-border-hairline");
    fg.lineWidth = 2;
    fg.strokeRect(FM, FM, FPX, FPX);
    ATOMS.forEach(([x, y, w], i) => {
      const share = Math.sqrt(w / MAXW);
      const r = share * FSC * 0.115 + FSC * 0.008;
      const on = i === hovered;
      fg.fillStyle = on ? css("--cert-probe") : css("--kpress-doc-accent");
      fg.globalAlpha = on ? 1 : 0.35 + 0.55 * share;
      fg.beginPath();
      fg.arc(FM + x * FSC, FM + (L - y) * FSC, on ? r + FSC * 0.012 : r, 0, 6.2832);
      fg.fill();
    });
    fg.globalAlpha = 1;
  }

  /* The atom under the pointer, or -1. Ties go to the heavier one, since a small
   atom drawn on top of a large one is the harder of the two to aim at. */
  function atomAt(cx, cy) {
    let best = -1,
      bestScore = Infinity;
    for (let i = 0; i < ATOMS.length; i++) {
      const [x, y, w] = ATOMS[i];
      const dx = FM + x * FSC - cx,
        dy = FM + (L - y) * FSC - cy;
      const d = Math.hypot(dx, dy);
      const r = Math.sqrt(w / MAXW) * FSC * 0.115 + FSC * 0.008;
      const reach = Math.max(r, FSC * 0.035);
      if (d <= reach && d - r < bestScore) {
        best = i;
        bestScore = d - r;
      }
    }
    return best;
  }

  function showAtomTip(i) {
    const [xn, xd, yn, yd, w] = ATOM_Q[i];
    const [wn, wd] = reduce(w, SCALE);
    fieldTip.innerHTML = '<span class="tip-xy"></span><span class="tip-w"></span>';
    void tex(fieldTip.querySelector(".tip-xy"), `(${fracTex(xn, xd)},\\; ${fracTex(yn, yd)})`);
    void tex(fieldTip.querySelector(".tip-w"), `w = ${fracTex(wn, wd)}`);
    swap(fieldTip);
  }
  const ATOM_PROMPT = "Hover or tap an atom for its position and weight.";

  /* One selection path for every pointer. A mouse selects by moving over an atom; a
   touch has nothing to hover with, so it selects on the way down and keeps what it
   picked, because lifting a finger destroys the pointer and fires `pointerleave`
   at once. Clearing on leave is therefore for the mouse alone. */
  const pickAtom = (e) => {
    const box = fc.getBoundingClientRect();
    const cx = ((e.clientX - box.left) / box.width) * FS,
      cy = ((e.clientY - box.top) / box.height) * FS;
    const i = atomAt(cx, cy);
    fc.style.cursor = i < 0 ? "default" : "crosshair";
    if (i === hovered) {
      return;
    }
    hovered = i;
    drawField();
    if (i < 0) {
      setText(fieldTip, ATOM_PROMPT);
    } else {
      showAtomTip(i);
    }
  };
  fc.addEventListener("pointermove", pickAtom);
  fc.addEventListener("pointerdown", pickAtom);
  fc.addEventListener("pointerleave", (e) => {
    if (e.pointerType && e.pointerType !== "mouse") {
      return;
    }
    if (hovered !== -1) {
      hovered = -1;
      drawField();
    }
    setText(fieldTip, ATOM_PROMPT);
  });

  /* ---------- Figure 5: covered mass ---------- */
  const pv = /** @type {HTMLCanvasElement} */ (document.getElementById("prove-{{SLUG}}")),
    pg = pv.getContext("2d");
  const PS = pv.width,
    PM = PS * 0.06,
    PPX = PS - 2 * PM,
    PSC = PPX / L;
  const RES = 230,
    TIGHT = __SQUARES_TIGHT__;
  let probe = [L * 0.22, L * 0.64],
    curK = Math.round(STEPS / 3),
    showHeat = true,
    heat = null;
  let heatQueued = false;
  /* Handle geometry in container units, so it scales with the drawing. */
  const HGAP = 0.3;
  let mode = "none";

  function buildHeat() {
    const img = pg.createImageData(RES, RES),
      d = img.data;
    const parse = (v) => {
      const m = document.createElement("canvas").getContext("2d");
      m.fillStyle = v;
      m.fillRect(0, 0, 1, 1);
      return Array.from(m.getImageData(0, 0, 1, 1).data).slice(0, 3);
    };
    const cLo = parse(css("--cert-below")),
      cTight = parse(css("--cert-near")),
      cA = parse(css("--cert-accent-wash")),
      cB = parse(css("--kpress-doc-accent")),
      cOut = parse(css("--kpress-doc-border"));
    const h = inset();
    const vals = new Float32Array(RES * RES);
    let hi = 1;
    for (let j = 0; j < RES; j++) {
      const y = (L * (RES - 1 - j)) / (RES - 1);
      for (let i = 0; i < RES; i++) {
        const x = (L * i) / (RES - 1),
          m = massAt(x, y) / SCALE;
        vals[j * RES + i] = m;
        if (x >= h && x <= L - h && y >= h && y <= L - h && m > hi) {
          hi = m;
        }
      }
    }
    const span = Math.max(hi - TIGHT, 0.25);
    for (let j = 0; j < RES; j++) {
      const y = (L * (RES - 1 - j)) / (RES - 1);
      for (let i = 0; i < RES; i++) {
        const x = (L * i) / (RES - 1),
          o = 4 * (j * RES + i),
          m = vals[j * RES + i];
        let col, a;
        if (!(x >= h && x <= L - h && y >= h && y <= L - h)) {
          col = cOut;
          a = 45;
        } else if (m < 1) {
          col = cLo;
          a = 235;
        } else if (m < TIGHT) {
          col = cTight;
          a = 155;
        } else {
          const t = Math.sqrt(Math.min(1, (m - TIGHT) / span));
          col = [
            cA[0] + (cB[0] - cA[0]) * t,
            cA[1] + (cB[1] - cA[1]) * t,
            cA[2] + (cB[2] - cA[2]) * t,
          ];
          a = 70 + 165 * t;
        }
        d[o] = col[0];
        d[o + 1] = col[1];
        d[o + 2] = col[2];
        d[o + 3] = a;
      }
    }
    const off = document.createElement("canvas");
    off.width = off.height = RES;
    off.getContext("2d").putImageData(img, 0, 0);
    heat = off;
  }

  function drawProver() {
    pg.clearRect(0, 0, PS, PS);
    pg.fillStyle = css("--kpress-doc-bg");
    pg.fillRect(0, 0, PS, PS);
    const X = (x) => PM + x * PSC,
      Y = (y) => PM + (L - y) * PSC;
    if (showHeat && heat) {
      pg.drawImage(heat, PM, PM, PPX, PPX);
    }
    pg.strokeStyle = css("--kpress-doc-border-hairline");
    pg.lineWidth = 2;
    pg.strokeRect(PM, PM, PPX, PPX);
    const h = inset();
    pg.strokeStyle = css("--kpress-doc-muted");
    pg.lineWidth = 1.5;
    pg.setLineDash([7, 6]);
    pg.strokeRect(X(h), Y(L - h), (L - 2 * h) * PSC, (L - 2 * h) * PSC);
    pg.setLineDash([]);
    const maxw = Math.max(...ATOMS.map((a) => a[2]));
    const pu = cs * probe[0] + sn * probe[1],
      pvv = -sn * probe[0] + cs * probe[1];
    for (const [x, y, w] of ATOMS) {
      const u = cs * x + sn * y,
        v = -sn * x + cs * y;
      const hit = covered(u, v, pu, pvv);
      pg.fillStyle = hit ? css("--cert-probe") : css("--kpress-doc-accent");
      pg.globalAlpha = hit ? 1 : 0.42;
      const r = Math.sqrt(w / maxw) * PSC * 0.1 + PSC * 0.007;
      pg.beginPath();
      pg.arc(X(x), Y(y), r, 0, 6.2832);
      pg.fill();
    }
    pg.globalAlpha = 1;
    pg.save();
    pg.translate(X(probe[0]), Y(probe[1]));
    pg.rotate(-Math.atan2(sn, cs));
    pg.strokeStyle = css("--kpress-doc-bg");
    pg.lineWidth = 7;
    pg.strokeRect(-HALF * PSC, -HALF * PSC, B * PSC, B * PSC);
    pg.strokeStyle = css("--cert-probe");
    pg.lineWidth = 4;
    pg.strokeRect(-HALF * PSC, -HALF * PSC, B * PSC, B * PSC);
    pg.restore();

    const [hx, hy] = proverHandle.update();
    if (!window.matchMedia("print").matches) {
      const ex = probe[0] - sn * HALF,
        ey = probe[1] + cs * HALF;
      pg.strokeStyle = css("--cert-probe");
      pg.lineWidth = 2.5;
      pg.beginPath();
      pg.moveTo(X(ex), Y(ey));
      pg.lineTo(hx, hy);
      pg.stroke();
    }
  }

  /* The rotation handle sits off the square's own top edge, so it turns with it. */
  function handlePoint() {
    return [probe[0] - sn * (HALF + HGAP), probe[1] + cs * (HALF + HGAP)];
  }

  /* Any direction reduces onto the net's arc [0, pi/4] by the container's own
   symmetry, which is the reduction Condition 1 pays for. This names the net
   direction nearest to that reduced angle; the readout reports it and the
   slider follows it, while the square itself stays exactly where it was put. */
  function nearestNet(phi) {
    let a = ((phi % (Math.PI / 2)) + Math.PI / 2) % (Math.PI / 2);
    if (a > Math.PI / 4) {
      a = Math.PI / 2 - a;
    }
    let best = 0,
      bestGap = Infinity;
    for (let k = 0; k <= STEPS; k++) {
      const gap = Math.abs(2 * Math.atan(netT(k)) - a);
      if (gap < bestGap) {
        bestGap = gap;
        best = k;
      }
    }
    return best;
  }

  function updateReadout() {
    const m = massAt(probe[0], probe[1]);
    /* Always over SCALE, never reduced: the denominator is the unit the whole
     certificate is counted in, and a reduced one would change under the reader
     as they drag, which is the opposite of what the readout is for. The six
     places are exact rather than rounded, because SCALE divides a million; the
     renderer refuses a certificate for which it does not. */
    void tex(document.getElementById("mv-{{SLUG}}"), `\\dfrac{${m}}{${SCALE}}`);
    /* The comparison sits on the equality line; the pill speaks only when there
     is more to say than the comparison. */
    const covers = m >= SCALE,
      md = document.getElementById("md-{{SLUG}}");
    void tex(md, `= ${(m / SCALE).toFixed(6)} ${covers ? "\\ge" : "\\lt"} 1`);
    md.style.color = covers ? css("--kpress-doc-accent") : css("--cert-below");
    const vd = document.getElementById("vd-{{SLUG}}");
    let cls = "verdict out",
      text = "";
    if (!admissible(probe[0], probe[1])) {
      text = "Outside the domain";
    } else if (covers && onNet) {
      text = "";
    } else if (covers) {
      text = "Off the net";
    } else if (onNet) {
      cls = "verdict no";
      text = "Below 1 in this preview";
    } else {
      text = "Off the net: no condition tested";
    }
    const shown = vd.hidden ? "" : vd.textContent;
    vd.hidden = !text;
    if (text && (shown !== text || vd.className !== cls)) {
      vd.className = cls;
      vd.textContent = text;
      swap(vd);
    }
  }
  function updateK() {
    const el = document.getElementById("kval-{{SLUG}}");
    /* The half-tangent t is the exact rational the net is built from; the degree
     measure beside it is not, so only the second one carries a mark. */
    const [n, d] = reduce(LIMIT_N * curK, LIMIT_D * STEPS);
    const parts = onNet
      ? [
          `k = ${curK}`,
          `t = ${curK === 0 ? "0" : `\\dfrac{${n}}{${d}}`}`,
          `\\theta ${degRel(angle, 4)}^{\\circ}`,
        ]
      : [
          `\\theta ${degRel(angle, 4)}^{\\circ}`,
          `\\text{nearest net } k = ${curK}`,
          `\\theta_k ${degRel(2 * Math.atan(netT(curK)), 4)}^{\\circ}`,
        ];
    /* Attached before it is typeset, not after. `tex` asks the cascade which face the
     words around the expression are in, and a detached span has no cascade: `closest`
     finds no ancestor and `getComputedStyle` answers with nothing, so these three
     readouts came out of the serif composite inside a sans panel. Reuse prepared
     children on startup, retaining their measured boxes while fonts decode. */
    let spans = [...el.children];
    if (
      spans.length !== parts.length ||
      spans.some((span) => !span.classList.contains("math-item"))
    ) {
      spans = parts.map(() => {
        const span = document.createElement("span");
        span.className = "math-item";
        return span;
      });
      el.replaceChildren(...spans);
    }
    parts.forEach((part, index) => {
      void tex(spans[index], part);
    });
    document
      .getElementById("kslider-{{SLUG}}")
      .setAttribute(
        "aria-valuetext",
        onNet
          ? `Direction ${curK} of ${STEPS}; angle ${deg(angle, 4)} degrees`
          : `Nearest net direction ${curK}; square is off the net at ${deg(angle, 4)} degrees`,
      );
  }
  function setProverStatus(text = "") {
    const el = document.getElementById("status-{{SLUG}}");
    el.hidden = !text;
    setText(el, text);
  }
  function refresh(rebuild) {
    if (onNet) {
      setDir(curK);
    } else {
      setAngle(angle);
    }
    const h = inset();
    probe[0] = Math.min(L - h, Math.max(h, probe[0]));
    probe[1] = Math.min(L - h, Math.max(h, probe[1]));
    if (rebuild && showHeat) {
      buildHeat();
    }
    drawProver();
    updateReadout();
    updateK();
  }

  /* The initial readouts must get a paint before the 53,000-cell preview occupies
   the main thread. The hidden certificate does no heat-map work until selected. */
  function scheduleHeat() {
    const visible = () => !(/** @type {HTMLElement} */ (pv.closest(".cert-figure")).hidden);
    if (heatQueued || heat || !showHeat || !visible()) {
      return;
    }
    heatQueued = true;
    void squaresMath.settled().then(() =>
      requestAnimationFrame(() =>
        setTimeout(() => {
          heatQueued = false;
          if (!heat && showHeat && visible()) {
            buildHeat();
            drawProver();
          }
        }, 0),
      ),
    );
  }

  function toWorld(e) {
    const box = pv.getBoundingClientRect();
    return [
      (((e.clientX - box.left) / box.width) * PS - PM) / PSC,
      L - (((e.clientY - box.top) / box.height) * PS - PM) / PSC,
    ];
  }
  function place(x, y) {
    setProverStatus();
    probe = [Math.min(L, Math.max(0, x)), Math.min(L, Math.max(0, y))];
    drawProver();
    updateReadout();
  }
  function rotateProbe(a) {
    setProverStatus();
    setAngle(a);
    curK = nearestNet(angle);
    /** @type {HTMLInputElement} */ (document.getElementById("kslider-{{SLUG}}")).value =
      String(curK);
    drawProver();
    updateReadout();
    updateK();
  }

  /* Inside the square a drag holds it where it was grabbed; elsewhere a press
   puts the center under the pointer. */
  let grabOffset = [0, 0];
  function insideProbe(x, y) {
    const u = cs * x + sn * y,
      v = -sn * x + cs * y;
    const pu = cs * probe[0] + sn * probe[1],
      pvv = -sn * probe[0] + cs * probe[1];
    return Math.abs(u - pu) <= HALF && Math.abs(v - pvv) <= HALF;
  }
  pv.addEventListener("pointerdown", (e) => {
    if (!e.isPrimary || e.button !== 0) {
      return;
    }
    const [x, y] = toWorld(e);
    mode = "move";
    grabOffset = insideProbe(x, y) ? [probe[0] - x, probe[1] - y] : [0, 0];
    pv.setPointerCapture(e.pointerId);
    place(x + grabOffset[0], y + grabOffset[1]);
  });
  pv.addEventListener("pointermove", (e) => {
    const [x, y] = toWorld(e);
    if (mode === "move") {
      place(x + grabOffset[0], y + grabOffset[1]);
      return;
    }
    pv.style.cursor = insideProbe(x, y) ? "grab" : "crosshair";
  });
  pv.addEventListener("pointerup", () => {
    mode = "none";
  });
  pv.addEventListener("pointercancel", () => {
    mode = "none";
  });
  const proverHandle = rotationHandle(pv, {
    id: "prove-rotate-{{SLUG}}",
    label: "Rotate the covered square",
    point: () => {
      const [x, y] = handlePoint();
      return [PM + x * PSC, PM + (L - y) * PSC];
    },
    angleAt: (e) => {
      const [x, y] = toWorld(e);
      return Math.atan2(-(x - probe[0]), y - probe[1]);
    },
    getAngle: () => angle,
    rotate: rotateProbe,
    redraw: drawProver,
    /* The 53,000-cell field is rebuilt on release, after a tap or a key step. */
    finish: () => {
      if (showHeat) {
        buildHeat();
      }
      drawProver();
    },
  });

  document.getElementById("kslider-{{SLUG}}").addEventListener("input", (e) => {
    setProverStatus();
    setDir(+(/** @type {HTMLInputElement} */ (e.target).value));
    refresh(true);
  });
  document.getElementById("btn-tight-{{SLUG}}").addEventListener("click", () => {
    setDir(0);
    /** @type {HTMLInputElement} */ (document.getElementById("kslider-{{SLUG}}")).value = "0";
    probe = [__SQUARES_WITNESS_X__, __SQUARES_WITNESS_Y__];
    refresh(true);
    setProverStatus(
      "Showing the minimum over all {{N_DIRECTIONS}} net directions: k = 0, covered mass {{LEAST_DEC}}.",
    );
  });
  document.getElementById("btn-scan-{{SLUG}}").addEventListener("click", () => {
    const h = inset();
    let best = Infinity,
      bx = 0,
      by = 0,
      N = 300;
    for (let j = 0; j <= N; j++) {
      const y = h + ((L - 2 * h) * j) / N;
      for (let i = 0; i <= N; i++) {
        const x = h + ((L - 2 * h) * i) / N;
        const m = massAt(x, y);
        if (m < best) {
          best = m;
          bx = x;
          by = y;
        }
      }
    }
    probe = [bx, by];
    drawProver();
    updateReadout();
    /* Exact, like the readout above it: an integer count of 1/SCALE units. */
    const lowest = (best / SCALE).toFixed(6);
    setProverStatus(
      "Sampled " +
        ((N + 1) ** 2).toLocaleString("en-US") +
        " allowed centers " +
        (onNet ? `at direction k = ${curK}` : `at ≈${deg(angle, 4)}°, off the net`) +
        ": lowest sampled mass " +
        lowest +
        ". The square now marks one of those sampled minima.",
    );
  });
  document.getElementById("btn-heat-{{SLUG}}").addEventListener("change", (e) => {
    showHeat = /** @type {HTMLInputElement} */ (e.currentTarget).checked;
    if (showHeat && !heat) {
      buildHeat();
    }
    drawProver();
  });

  /* ---------- Figure 6: the shrink ---------- */
  let KNET = 3;
  const sk = /** @type {HTMLCanvasElement} */ (document.getElementById("shrink-{{SLUG}}")),
    skg = sk.getContext("2d");
  const SKS = sk.width,
    SKC = SKS / 2,
    SKSIDE = SKS * 0.62,
    SKGAP = SKS * 0.055;
  sk.style.cursor = "default";

  const phiInput = () => /** @type {HTMLInputElement} */ (document.getElementById("phi-{{SLUG}}"));
  /* The unit square's angle. The slider covers the net's arc; the handle turns
   through the whole circle, and the slider then shows the arc angle the
   container's symmetry reduces the square to. */
  let phiVal = ((+phiInput().value / 10) * Math.PI) / 180;
  /* The slider moves in tenths of a degree, so an angle it sets is an exact
   number of degrees and the readout prints it as one; the handle turns to
   wherever the pointer is, and from then on the degree readouts are marked. */
  let phiExact = true;
  const phiNow = () => phiVal;
  const arcOf = (phi) => {
    const psi = phi % (Math.PI / 2);
    return psi > Math.PI / 4 ? Math.PI / 2 - psi : psi;
  };
  /* The handle rides the square's own top edge, so it turns with it. */
  function phiHandlePoint(phi) {
    const r = SKSIDE / 2 + SKGAP;
    return [SKC - r * Math.sin(phi), SKC - r * Math.cos(phi)];
  }
  function skToCanvas(e) {
    const box = sk.getBoundingClientRect();
    return [((e.clientX - box.left) / box.width) * SKS, ((e.clientY - box.top) / box.height) * SKS];
  }
  function setPhiAngle(a) {
    const TAU = 2 * Math.PI;
    phiVal = ((a % TAU) + TAU) % TAU;
    phiExact = false;
    phiInput().value = String(Math.round(((arcOf(phiVal) * 180) / Math.PI) * 10));
    shrinkDraw();
  }
  const shrinkHandle = rotationHandle(sk, {
    id: "shrink-rotate-{{SLUG}}",
    label: "Rotate the unit square",
    point: () => phiHandlePoint(phiNow()),
    angleAt: (e) => {
      const [x, y] = skToCanvas(e);
      return Math.atan2(SKC - x, SKC - y);
    },
    getAngle: phiNow,
    rotate: setPhiAngle,
    finish: null,
    redraw: shrinkDraw,
  });
  function shrinkDraw() {
    const _c = sk,
      g = skg,
      S = SKS;
    const phi = phiNow(),
      psi = phi % (Math.PI / 2),
      mirrored = psi > Math.PI / 4;
    const arc = arcOf(phi);
    let bestK = 0,
      bestD = Infinity;
    for (let k = 0; k <= KNET; k++) {
      const th = 2 * Math.atan((LIMIT * k) / KNET);
      if (Math.abs(th - arc) < bestD) {
        bestD = Math.abs(th - arc);
        bestK = k;
      }
    }
    const theta = 2 * Math.atan((LIMIT * bestK) / KNET),
      d = Math.abs(theta - arc);
    /* The net direction drawn inside the square is theta's image under the same
     symmetry that took phi to the arc, so the two squares stay together. */
    const thetaDrawn = phi - psi + (mirrored ? Math.PI / 2 - theta : theta);
    let D = 0;
    for (let k = 0; k < KNET; k++) {
      const a = (LIMIT * k) / KNET,
        b2 = (LIMIT * (k + 1)) / KNET;
      D = Math.max(D, (b2 - a) / (1 + a * b2));
    }
    const Bk = Math.floor(1e7 / (1 + D) - 1) / 1e7;
    const prod = Bk * (Math.cos(d) + Math.sin(d));

    g.clearRect(0, 0, S, S);
    g.fillStyle = css("--kpress-doc-bg");
    g.fillRect(0, 0, S, S);
    const sc = S * 0.62;
    g.save();
    g.translate(S / 2, S / 2);
    g.save();
    g.rotate(-phi);
    g.strokeStyle = css("--kpress-doc-border-hairline");
    g.lineWidth = 3;
    g.strokeRect(-sc / 2, -sc / 2, sc, sc);
    g.restore();
    g.save();
    g.rotate(-thetaDrawn);
    g.fillStyle = css("--cert-probe-wash");
    g.globalAlpha = 0.8;
    g.fillRect((-Bk * sc) / 2, (-Bk * sc) / 2, Bk * sc, Bk * sc);
    g.globalAlpha = 1;
    g.strokeStyle = css("--cert-probe");
    g.lineWidth = 3;
    g.strokeRect((-Bk * sc) / 2, (-Bk * sc) / 2, Bk * sc, Bk * sc);
    g.restore();
    g.restore();

    const [hx, hy] = shrinkHandle.update();
    if (!window.matchMedia("print").matches) {
      const ex = SKC - (SKSIDE / 2) * Math.sin(phi),
        ey = SKC - (SKSIDE / 2) * Math.cos(phi);
      g.strokeStyle = css("--kpress-doc-border-hairline");
      g.lineWidth = 2;
      g.beginPath();
      g.moveTo(ex, ey);
      g.lineTo(hx, hy);
      g.stroke();
    }

    /* What each of these six can and cannot claim: phi is exact while the slider
     owns it; theta is a net angle, exact only at zero; d is their difference,
     exact only when both are; D is a rational whose decimal does not
     terminate; Bk is a whole multiple of 1e-7 by construction, so seven places
     print it in full; and the product is irrational whatever the other two are. */
    const thetaExact = theta === 0,
      dExact = phiExact && thetaExact;
    void tex(
      document.getElementById("s-phi-{{SLUG}}"),
      `${degTex(phi, 3, phiExact)}^{\\circ}` +
        (Math.abs(arc - phi) > 1e-9 ? ` \\equiv ${degTex(arc, 3, phiExact)}^{\\circ}` : ""),
    );
    void tex(
      document.getElementById("s-theta-{{SLUG}}"),
      `${degTex(theta, 3, thetaExact)}^{\\circ}`,
    );
    void tex(document.getElementById("s-d-{{SLUG}}"), `${degTex(d, 4, dExact)}^{\\circ}`);
    void tex(document.getElementById("s-D-{{SLUG}}"), nearly(D.toFixed(7)));
    void tex(document.getElementById("s-B-{{SLUG}}"), Bk.toFixed(7));
    const pe = document.getElementById("s-prod-{{SLUG}}");
    void tex(pe, `\\approx ${prod.toFixed(6)} ${prod < 1 ? "\\lt" : "\\ge"} 1`);
    pe.style.color = prod < 1 ? "" : css("--kpress-doc-danger");
  }
  document.getElementById("phi-{{SLUG}}").addEventListener("input", (e) => {
    phiVal = ((+(/** @type {HTMLInputElement} */ (e.target).value) / 10) * Math.PI) / 180;
    phiExact = true;
    shrinkDraw();
  });
  const knets = document.querySelectorAll('.cert-figure[data-cert="{{SLUG}}"] .knet');
  knets.forEach((b) => {
    b.addEventListener("click", () => {
      knets.forEach((o) => {
        o.setAttribute("aria-pressed", "false");
      });
      b.setAttribute("aria-pressed", "true");
      KNET = +(/** @type {HTMLElement} */ (b).dataset.k);
      shrinkDraw();
    });
  });

  /* ---------- boot ---------- */
  function boot() {
    drawField();
    /** @type {HTMLInputElement} */ (document.getElementById("kslider-{{SLUG}}")).value =
      String(curK);
    refresh(false);
    shrinkDraw();
    if (window.matchMedia("print").matches) {
      if (showHeat && !heat && pv.getClientRects().length) {
        buildHeat();
      }
      drawProver();
    } else {
      scheduleHeat();
    }
  }
  /* Each render validates its actual faces; a prepared formula retains its measured
   box while it hydrates. No unrelated font or heat map delays the first readout. */
  boot();
  document.addEventListener("squares:certificatechange", scheduleHeat);
  const repaint = () => {
    heat = null;
    boot();
  };
  if (window.matchMedia) {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    if (mq.addEventListener) {
      mq.addEventListener("change", repaint);
    }
    /* A canvas is a bitmap, so print CSS cannot recolour one: a reader printing in
     dark mode would get three near-black squares on white paper. Redrawing once
     print media is active picks up the light tokens kpress forces for print. The
     media listener covers a headless render, `beforeprint` the print dialog, and
     `afterprint` puts the screen colours back. */
    const pm = window.matchMedia("print");
    if (pm.addEventListener) {
      pm.addEventListener("change", repaint);
    }
  }
  window.addEventListener("beforeprint", repaint);
  window.addEventListener("afterprint", repaint);
})();
