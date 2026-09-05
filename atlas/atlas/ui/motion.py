"""Frame-level motion Streamlit's CSS can't express, via a zero-height component.

The one effect here: dashboard stat values count from their previous value to
the new one. Per the fluid-interface rules, the animation starts from the
current on-screen value (the last run's number, remembered on the parent
window) — never a replay from zero on an unrelated rerun — and steps down to
nothing under prefers-reduced-motion.
"""

from __future__ import annotations

import streamlit.components.v1 as components

_COUNT_UP = """<script>
(() => {
  const win = window.parent;
  const doc = win.document;
  const reduce = win.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const prev = win.__atlasStatPrev || (win.__atlasStatPrev = {});

  doc.querySelectorAll(".stat").forEach((tile) => {
    const label = (tile.querySelector(".label") || {}).textContent || "";
    const el = tile.querySelector(".value");
    if (!el || !label) return;
    const raw = el.textContent.trim();
    const m = raw.match(/^(-?\\d+(?:\\.\\d+)?)(.*)$/);
    if (!m) return;                       // non-numeric tiles stay untouched
    const target = parseFloat(m[1]);
    const suffix = m[2];
    const decimals = (m[1].split(".")[1] || "").length;

    const had = label in prev;
    const from = had ? prev[label] : 0;
    prev[label] = target;
    if (reduce || from === target) return;

    const t0 = win.performance.now();
    const dur = 650;
    const ease = (t) => 1 - Math.pow(1 - t, 3);   // strong ease-out: fast, then settles
    const step = () => {
      const k = Math.min(1, (win.performance.now() - t0) / dur);
      el.textContent = (from + (target - from) * ease(k)).toFixed(decimals) + suffix;
      if (k < 1) win.requestAnimationFrame(step);
    };
    win.requestAnimationFrame(step);
  });
})();
</script>"""


def count_up_stats() -> None:
    """Animate every .stat value on the page from its previous value."""
    components.html(_COUNT_UP, height=0)


_GLIDE = """<script>
(() => {
  const win = window.parent;
  const doc = win.document;
  const glide = () => {
    const reduce = win.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const behavior = reduce ? "auto" : "smooth";
    const main = doc.querySelector("section.stMain");
    if (main && main.scrollTop > 0) main.scrollTo({top: 0, behavior});
    if (win.scrollY > 0) win.scrollTo({top: 0, behavior});
  };
  // The rerun swaps the page content and the browser snaps to the top, so a
  // post-render scroll has nothing to animate. Glide on pointerdown instead:
  // the old page visibly scrolls up while the switch is in flight. The
  // listener must live in the PARENT realm — this iframe is torn down on
  // every rerun and handlers owned by a dead realm go silent — so it is
  // injected as a parent-owned <script> once.
  if (!win.__atlasNavGlide) {
    win.__atlasNavGlide = true;
    const tag = doc.createElement("script");
    tag.textContent = "(function(){" +
      "document.addEventListener('pointerdown', function(e){" +
        "var t = e.target;" +
        "var btn = t && t.closest && t.closest('.st-key-topbar .stButton button');" +
        "if (!btn) return;" +
        "var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;" +
        "var behavior = reduce ? 'auto' : 'smooth';" +
        "var m = document.querySelector('section.stMain');" +
        "if (m && m.scrollTop > 0) m.scrollTo({top: 0, behavior: behavior});" +
        "if (window.scrollY > 0) window.scrollTo({top: 0, behavior: behavior});" +
      "}, {capture: true, passive: true});" +
    "})();";
    doc.body.appendChild(tag);
  }
  // Fallback: if the switch still lands mid-page (kept widgets), finish it.
  const key = %KEY%;
  if (win.__atlasPage !== undefined && win.__atlasPage !== key) glide();
  win.__atlasPage = key;
})();
</script>"""


def page_glide(page: str) -> None:
    """On a nav change, glide the viewport back to the top of the new page."""
    import json

    components.html(_GLIDE.replace("%KEY%", json.dumps(page)), height=0)
