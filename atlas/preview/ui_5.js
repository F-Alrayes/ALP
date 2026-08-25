
  /* ================================ charts ============================== */
  /* Hand-built inline SVG: thin marks, rounded data-ends on the baseline,
     recessive grid, selective direct labels, hover tooltip on every mark. */

  const CH = { w: 560, rowH: 30, gap: 9, pad: { l: 124, r: 54, t: 8, b: 26 } };

  // Department names are long; the axis has a fixed gutter, so trim to fit.
  const SHORT = { "Investments / Deal Team": "Investments", "Legal & Compliance": "Legal & Comp.",
                  "Operations / HR": "Operations" };
  const shortLabel = s => SHORT[s] || s;
  const tipAttr = (title, body) =>
    `data-tip="${esc(title)}" data-tipb="${esc(body)}" tabindex="0"`;

  function barTrack(x, y, w, h) {
    return `<rect x="${x}" y="${y}" width="${Math.max(w, 0)}" height="${h}" rx="4" ry="4"
      class="bar" />`;
  }

  // Horizontal category bars, one series. Identity comes from the axis label,
  // so colour is not carrying meaning; escalated is tinted as a status.
  function hbar(rows, opts) {
    opts = opts || {};
    const max = Math.max(1, ...rows.map(r => r.value));
    const h = CH.pad.t + rows.length * (CH.rowH + CH.gap) + CH.pad.b;
    const plotW = CH.w - CH.pad.l - CH.pad.r;
    const ticks = niceTicks(max, 4);
    const grid = ticks.map(t => {
      const x = CH.pad.l + (t / max) * plotW;
      return `<line class="gl" x1="${x}" y1="${CH.pad.t}" x2="${x}" y2="${h - CH.pad.b}"/>
        <text class="axl" x="${x}" y="${h - CH.pad.b + 15}" text-anchor="middle">${t}</text>`;
    }).join("");
    const bars = rows.map((r, i) => {
      const y = CH.pad.t + i * (CH.rowH + CH.gap);
      const w = (r.value / max) * plotW;
      const fill = r.color || "var(--s1)";
      return `<g ${tipAttr(r.label, r.tip || (r.value + " requests"))}>
        <text class="cat" x="${CH.pad.l - 10}" y="${y + CH.rowH / 2 + 4}" text-anchor="end">${esc(shortLabel(r.label))}</text>
        <g fill="${fill}">${barTrack(CH.pad.l, y, w, CH.rowH)}</g>
        <text class="vl" x="${CH.pad.l + w + 7}" y="${y + CH.rowH / 2 + 4}">${r.value}</text>
      </g>`;
    }).join("");
    return `<svg viewBox="0 0 ${CH.w} ${h}" role="img" aria-label="${esc(opts.aria || "bar chart")}">
      ${grid}${bars}</svg>`;
  }

  // Two series, grouped. Legend + direct labels; validated colour pair.
  function groupedBar(rows, opts) {
    const pad = { l: 124, r: 66, t: 8, b: 26 };
    const barH = 13, inner = 5, groupH = barH * 2 + inner, gap = 14;
    const max = Math.max(1, ...rows.map(r => Math.max(r.a, r.b)));
    const h = pad.t + rows.length * (groupH + gap) + pad.b;
    const plotW = CH.w - pad.l - pad.r;
    const ticks = niceTicks(max, 4);
    const grid = ticks.map(t => {
      const x = pad.l + (t / max) * plotW;
      return `<line class="gl" x1="${x}" y1="${pad.t}" x2="${x}" y2="${h - pad.b}"/>
        <text class="axl" x="${x}" y="${h - pad.b + 15}" text-anchor="middle">${t}</text>`;
    }).join("");
    const bars = rows.map((r, i) => {
      const y = pad.t + i * (groupH + gap);
      const wa = (r.a / max) * plotW, wb = (r.b / max) * plotW;
      return `<g>
        <text class="cat" x="${pad.l - 10}" y="${y + groupH / 2 + 4}" text-anchor="end">${esc(shortLabel(r.label))}</text>
        <g fill="var(--s2)" ${tipAttr(r.label, opts.aLabel + ": " + r.a + "h")}>
          ${barTrack(pad.l, y, wa, barH)}</g>
        <text class="vl" x="${pad.l + wa + 6}" y="${y + barH - 2}">${r.a}h</text>
        <g fill="var(--s1)" ${tipAttr(r.label, opts.bLabel + ": " + r.b + "h")}>
          ${barTrack(pad.l, y + barH + inner, wb, barH)}</g>
        <text class="vl" x="${pad.l + wb + 6}" y="${y + barH + inner + barH - 2}">${r.b}h</text>
      </g>`;
    }).join("");
    return `<svg viewBox="0 0 ${CH.w} ${h}" role="img" aria-label="${esc(opts.aria || "grouped bar chart")}">
      ${grid}${bars}</svg>`;
  }

  function histogram(values, opts) {
    const pad = { l: 40, r: 14, t: 10, b: 34 };
    const w = CH.w, h = 210;
    if (!values.length) return "";
    const max = Math.max(...values), bins = 10;
    const size = Math.max(1, Math.ceil(max / bins));
    const counts = new Array(bins).fill(0);
    for (const v of values) counts[Math.min(bins - 1, Math.floor(v / size))]++;
    const top = Math.max(1, ...counts);
    const plotW = w - pad.l - pad.r, plotH = h - pad.t - pad.b;
    const bw = plotW / bins;
    const ticks = niceTicks(top, 3);
    const grid = ticks.map(t => {
      const y = pad.t + plotH - (t / top) * plotH;
      return `<line class="gl" x1="${pad.l}" y1="${y}" x2="${w - pad.r}" y2="${y}"/>
        <text class="axl" x="${pad.l - 7}" y="${y + 4}" text-anchor="end">${t}</text>`;
    }).join("");
    const bars = counts.map((c, i) => {
      const bh = (c / top) * plotH;
      const x = pad.l + i * bw + 2, y = pad.t + plotH - bh;
      const lo = i * size, hi = (i + 1) * size;
      return `<g fill="var(--s1)" ${tipAttr(`${lo}–${hi}h old`,
        `${c} open request${c === 1 ? "" : "s"}`)}>
        ${barTrack(x, y, Math.max(bw - 4, 1), Math.max(bh, c ? 3 : 0))}</g>`;
    }).join("");
    const labels = [0, Math.floor(bins / 2), bins].map(i => {
      const x = pad.l + i * bw;
      return `<text class="axl" x="${x}" y="${h - 12}" text-anchor="middle">${i * size}h</text>`;
    }).join("");
    return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(opts.aria || "histogram")}">
      ${grid}${bars}${labels}</svg>`;
  }

  function niceTicks(max, count) {
    const raw = max / count;
    const mag = Math.pow(10, Math.floor(Math.log10(Math.max(raw, 1))));
    const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= raw) || mag * 10;
    const out = [];
    for (let v = 0; v <= max + 1e-9; v += step) out.push(Math.round(v * 10) / 10);
    if (out[out.length - 1] < max) out.push(Math.round((out[out.length - 1] + step) * 10) / 10);
    return out;
  }

  // Backup is distinguished by a dash pattern, not by a paler colour: a fourth
  // hue would not clear the CVD gate, and a near-surface grey is invisible.
  /* =============================== dashboard ============================ */

  function pageDashboard() {
    const at = now();
    const h = E.headline(S);
    const status = E.byStatus(S);
    const depts = E.openByDepartment(S);
    const turn = E.turnaroundByDepartment(S);
    const orphans = E.orphanProcesses(S);
    const spofs = E.singlePointsOfFailure(S, 2);
    const necks = E.bottlenecks(S);
    const ages = E.queueAges(S);

    const statusRows = status.map(r => ({
      label: r.status, value: r.count,
      color: r.key === "escalated" ? "var(--critical)" : "var(--s1)",
      tip: r.count + " request" + (r.count === 1 ? "" : "s"),
    }));
    const deptRows = depts.map(d => ({
      label: d.department, value: d.count,
      tip: d.count + " open" + (d.escalated ? ` · ${d.escalated} escalated` : ""),
    }));
    const turnRows = turn.map(t => ({ label: t.department, a: t.avg_ack_hours, b: t.avg_complete_hours }));

    const charts = `<div class="charts">
      <div class="chart"><h3>Requests by status</h3>
        <div class="csub">Every request ever raised. Escalated is marked in the critical colour
          and named on the axis.</div>
        ${hbar(statusRows, { aria: "Requests by status" })}</div>
      <div class="chart"><h3>Open requests by department</h3>
        <div class="csub">Where the open queue sits right now.</div>
        ${deptRows.length ? hbar(deptRows, { aria: "Open requests by department" })
          : empty("Nothing open right now.")}</div>
      <div class="chart"><h3>Turnaround by department</h3>
        <div class="legend"><span><i style="background:var(--s2)"></i>Time to acknowledge</span>
          <span><i style="background:var(--s1)"></i>Time to complete</span></div>
        ${turnRows.length ? groupedBar(turnRows, { aLabel: "Time to acknowledge",
          bLabel: "Time to complete", aria: "Turnaround by department" })
          : empty("No completed requests yet.")}</div>
      <div class="chart"><h3>How long open items have been waiting</h3>
        <div class="csub">Age of every open request, in simulated hours.</div>
        ${ages.length ? histogram(ages.map(a => a.age_hours), { aria: "Queue age distribution" })
          : empty("Nothing is waiting.")}</div>
    </div>`;

    const neckTable = necks.length ? `<div class="tblwrap"><table>
      <thead><tr><th>Person</th><th>Title</th><th>Department</th><th class="n">Open</th>
        <th class="n">Avg wait</th><th class="n">Oldest</th><th>Status</th></tr></thead>
      <tbody>${necks.map(b => `<tr><td><strong>${esc(b.person)}</strong></td><td>${esc(b.title)}</td>
        <td>${esc(b.department)}</td><td class="n">${b.open}</td>
        <td class="n">${b.avg_wait_hours}h</td><td class="n">${b.oldest_wait_hours}h</td>
        <td>${b.is_ooo ? badge("Out of office", "ooo") : `<span class="muted">In office</span>`}</td>
        </tr>`).join("")}</tbody></table></div>` : empty("No queues are backing up.");

    const orphanCards = orphans.length ? orphans.map(o => `<div class="card alarm">
        <div class="card-t">${esc(o.process)} ${badge("No owner", "escalated")}</div>
        <div class="card-m"><span>${esc(o.category)}</span>
          <span>${o.open_requests} open request(s)</span>
          <span>other roles configured: ${esc(o.other_roles)}</span></div></div>`).join("")
      : `<div class="note info">Every process has an owner.</div>`;

    const spofCards = spofs.length ? spofs.map(r => {
      const detail = r.uncovered.length ? "Uncovered: " + r.uncovered.join(", ")
        : r.owns ? "Every process they own has a delegate or backup."
        : `Approves on ${r.approves} process(es) but owns none outright.`;
      return `<div class="card${r.uncovered.length ? " alarm" : ""}">
        <div class="card-t">${esc(r.person)}</div>
        <div class="card-m"><span>${esc(r.title)}</span><span>${esc(r.department)}</span></div>
        <div class="card-m" style="margin-top:7px">${badge(r.owns + " owned", "role")}
          ${badge(r.approves + " approved", "role")}
          ${badge(r.open_load + " open", r.open_load ? "gold" : "mute")}
          ${r.is_ooo ? badge("Out of office", "ooo") : ""}
          ${r.uncovered.length ? badge(r.uncovered.length + " uncovered", "escalated") : ""}</div>
        <div class="card-b">${esc(detail)}</div></div>`;
    }).join("") : `<div class="note info">No individual carries enough uncovered processes
      to be a concern.</div>`;

    return phead("Dashboard", "Where work is actually stuck",
      "Queue times, bottlenecks, orphaned processes and single points of failure — computed live " +
      "against simulated time.") +
      `<p class="muted" style="margin-bottom:11px">Simulated time
        <span class="mono">${esc(fmtTime(at))}</span></p>
      <div class="tiles">
        ${tile("Open requests", String(h.open_requests), "of " + h.total_requests + " raised")}
        ${tile("Avg time to acknowledge", h.avg_ack_hours.toFixed(1) + "h", "first response")}
        ${tile("Avg time to complete", h.avg_cycle_hours.toFixed(1) + "h", "raised to closed")}
        ${tile("Escalation rate", Math.round(h.escalation_rate) + "%",
               h.escalated_requests + " escalated", h.escalation_rate >= 20 ? "bad" : "")}
        ${tile("Oldest open item", Math.round(h.oldest_open_hours) + "h", "still waiting",
               h.oldest_open_hours >= 48 ? "warn" : "")}
      </div>
      <div class="sect"><h2>Queue</h2></div>${charts}
      <div class="sect"><h2>Bottlenecks</h2><p>Who the open queue is piling up behind.</p></div>
      ${neckTable}
      <div class="sect"><h2>Orphaned processes</h2>
        <p>Requests matched to these have no owner to route to — they park for the admin.</p></div>
      <div class="stack">${orphanCards}</div>
      <div class="sect"><h2>Single points of failure</h2>
        <p>People carrying several processes. “Uncovered” means the process has no available
          delegate or backup behind them.</p></div>
      <div class="stack">${spofCards}</div>`;
  }
