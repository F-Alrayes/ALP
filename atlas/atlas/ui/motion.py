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
