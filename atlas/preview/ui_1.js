/* Atlas preview UI. All logic lives in the engine above; these files render it
   and wire the controls. State is per-viewer, in localStorage. */
(function () {
  "use strict";
  const E = globalThis;
  const HOUR = E.HOUR || 3600000;
  const STORE = "atlas.preview.v2";

  let S = null;                      // engine state
  let UI = {
    actor: null, page: "chat", tab: {}, open: null,
    chat: [], draft: null, msgSeq: 1,
    tree: { collapsed: {}, zoom: 1, x: 0, y: 0, selected: null, search: "", dept: "All departments" },
    person: null, process: null,
    filter: "Autonomous actions", search: "", dept: "All departments",
    guideSeen: false, guideStep: 0, flash: null,
  };

  /* ------------------------------- storage ------------------------------ */

  function save() {
    try { localStorage.setItem(STORE, JSON.stringify({ s: S, ui: UI })); }
    catch (err) { /* private mode, quota, blocked storage — run in memory */ }
  }
  function load() {
    try {
      const raw = localStorage.getItem(STORE);
      if (!raw) return false;
      const parsed = JSON.parse(raw);
      if (!parsed || !parsed.s || !parsed.s.people) return false;
      S = parsed.s;
      UI = Object.assign(UI, parsed.ui || {});
      UI.tree = Object.assign({ collapsed: {}, zoom: 1, x: 0, y: 0, selected: null,
                                search: "", dept: "All departments" }, UI.tree || {});
      return true;
    } catch (err) { return false; }
  }
  function reseed(keepGuide) {
    const seen = keepGuide ? UI.guideSeen : false;
    S = E.hydrate(SEED, Date.now());
    UI.actor = (S.people.find(p => p.name === "Noura Al-Sabah") || S.people[0]).id;
    UI.open = UI.person = UI.process = null;
    UI.chat = []; UI.draft = null; UI.msgSeq = 1;
    UI.tab = {}; UI.guideSeen = seen; UI.guideStep = 0;
    UI.tree = { collapsed: {}, zoom: 0.85, x: 0, y: 0, selected: null,
                search: "", dept: "All departments", center: true };
    collapseToTeams();
    E.runUntilSettled(S);
    greet();
    save();
  }

  /* ------------------------------- helpers ------------------------------ */

  const esc = s => String(s === null || s === undefined ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  const person = id => E.person(S, id);
  const actor = () => person(UI.actor) || S.people[0];
  const now = () => E.now(S);

  function fmtTime(ms) {
    if (ms === null || ms === undefined) return "—";
    const d = new Date(ms);
    const M = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    const p2 = n => String(n).padStart(2, "0");
    return `${p2(d.getDate())} ${M[d.getMonth()]} ${d.getFullYear()}, ${p2(d.getHours())}:${p2(d.getMinutes())}`;
  }
  function human(ms) {
    if (ms === null || ms === undefined) return "—";
    const sign = ms < 0 ? "-" : "";
    let s = Math.floor(Math.abs(ms) / 1000);
    const d = Math.floor(s / 86400); s -= d * 86400;
    const h = Math.floor(s / 3600); s -= h * 3600;
    const m = Math.floor(s / 60);
    if (d) return `${sign}${d}d ${h}h`;
    if (h) return `${sign}${h}h ${m}m`;
    return `${sign}${m}m`;
  }
  const badge = (t, k) => `<span class="b ${k || "mute"}">${esc(t)}</span>`;
  const statusBadge = s => `<span class="b ${s}">${esc(E.STATUS_LABELS[s] || s)}</span>`;
  const tile = (l, v, s, tone) => `<div class="tile ${tone || ""}"><div class="l">${esc(l)}</div>
    <div class="v">${esc(v)}</div><div class="s">${esc(s || "")}</div></div>`;
  const empty = (b, h2) => `<div class="empty"><div class="big">${esc(b)}</div>
    <div>${esc(h2 || "")}</div></div>`;
  const phead = (e, t, s) => `<div class="phead"><div class="eyebrow">${esc(e)}</div>
    <h1>${esc(t)}</h1><p>${esc(s || "")}</p></div>`;

  const EVENT_LABELS = {
    created:"Request raised", routing:"Routing", dispatch:"Dispatched", chase:"Chase sent",
    escalation:"Escalated", escalation_blocked:"Escalation blocked", reroute:"Reassigned",
    reroute_ooo:"Rerouted — out of office", reroute_chase:"Rerouted — no response",
    ooo_no_cover:"No cover available", acknowledged:"Acknowledged", status_update:"Status update",
    completed:"Completed", note:"Note", follow:"Follower joined", orphan:"No owner",
    ooo_change:"Out-of-office change", seed:"Database seeded",
  };
  const AGENT_TYPES = new Set(["chase","escalation","reroute_ooo","reroute_chase",
                               "ooo_no_cover","escalation_blocked"]);
  const ALERT_TYPES = new Set(["escalation","escalation_blocked","orphan"]);

  function trail(events) {
    if (!events.length) return empty("Nothing has happened yet.",
      "Events appear here as the request moves.");
    return `<div class="trail">` + events.map(e => {
      let cls = "node";
      if (ALERT_TYPES.has(e.type)) cls += " fail";
      else if (e.actor === E.AGENT_ACTOR || AGENT_TYPES.has(e.type)) cls += " agent";
      else cls += " ok";
      const label = EVENT_LABELS[e.type] ||
        e.type.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
      return `<div class="${cls}">
        <div class="w mono">${esc(fmtTime(e.created_at))} · <span class="who">${esc(e.actor)}</span></div>
        <div class="d"><span class="k">${esc(label)}</span> — ${esc(e.detail)}</div></div>`;
    }).join("") + `</div>`;
  }

  function timelineOf(id) {
    return S.events.filter(e => e.request_id === id)
      .sort((a, b) => a.created_at - b.created_at || a.id - b.id);
  }
  const unreadFor = id => S.messages.filter(m => m.recipient_id === id && !m.read).length;

  /* --------------------------------- rail ------------------------------- */

  function railHTML() {
    const at = now();
    const people = S.people.slice().sort((a, b) => a.name.localeCompare(b.name));
    const opt = p => `<option value="${p.id}"${p.id === UI.actor ? " selected" : ""}>` +
      `${esc(p.name)} — ${esc(p.title)}${E.isOutOfOffice(p, at) ? "  (OOO)" : ""}</option>`;
    const unread = unreadFor(UI.actor);
    const oooTarget = person(UI.oooPerson) || people[0];
    const oooOpt = p => `<option value="${p.id}"${p.id === oooTarget.id ? " selected" : ""}>` +
      `${esc(p.name)}${E.isOutOfOffice(p, at) ? "  (OOO)" : ""}</option>`;
    const isOoo = E.isOutOfOffice(oooTarget, at);

    return `
    <div class="brand"><span class="mark">A</span>
      <span><span class="name">ATLAS</span><br><span class="tag">Responsibility, routed</span></span></div>

    <div class="rail-sec">
      <span class="rail-label">You are</span>
      <select data-act="actor" aria-label="Acting as">${people.map(opt).join("")}</select>
      <span class="rail-note">${unread ? unread + " unread message" + (unread === 1 ? "" : "s") +
        " in your inbox." : "Inbox clear."}</span>
      <button data-act="guide">Open the guide</button>
    </div>

    <div class="rail-sec">
      <span class="rail-label">Demo controls</span>
      <span class="rail-note">None of this exists in a real deployment — it is how the
        prototype is driven.</span>
    </div>

    <div class="rail-sec">
      <span class="rail-label">Simulated clock</span>
      <span class="clock-read mono">${esc(fmtTime(at))}</span>
      <span class="clock-off mono">offset ${E.offsetHours(S) >= 0 ? "+" : ""}${E.offsetHours(S)}h from real time</span>
      <div class="btn-row">
        <button data-act="adv" data-h="1">+1h</button>
        <button data-act="adv" data-h="24">+24h</button>
        <button data-act="adv" data-h="48">+48h</button>
      </div>
      <label class="sr" for="advh">Advance by hours</label>
      <input id="advh" type="number" min="1" max="720" value="${UI.advH || 24}" data-act="advh">
      <button data-act="advcustom">Advance clock</button>
      <button data-act="clockreset">Reset clock to real time</button>
    </div>

    <div class="rail-sec">
      <span class="rail-label">Out of office</span>
      <select data-act="oooperson" aria-label="Person">${people.map(oooOpt).join("")}</select>
      <label class="sr" for="oood">Away for days</label>
      <input id="oood" type="number" min="1" max="60" value="${UI.oooDays || 5}" data-act="oood">
      <button data-act="ooo">${isOoo ? "Mark back in office" : "Mark out of office"}</button>
    </div>

    <div class="rail-sec">
      <span class="rail-label"><span class="agent-dot live"></span>Agent</span>
      <span class="rail-note">Evaluating its rules every 2s<br>
        last pass ${esc(S.lastTickAt ? fmtTime(S.lastTickAt) : "—")}</span>
      <button data-act="tick">Run agent now</button>
    </div>

    <div class="rail-sec">
      <span class="rail-label">Database</span>
      <button class="danger" data-act="reseed">Reset &amp; reseed</button>
    </div>`;
  }

  /* --------------------------------- shell ------------------------------ */

  // Everyday work stays on the bar; the pitch and admin surfaces sit behind
  // "More", so a first-time employee sees three choices, not six.
  const PRIMARY = [["chat", "Ask Atlas"], ["people", "People"], ["requests", "Requests"]];
  const MORE = [["processes", "What you can ask for"], ["dashboard", "Dashboard"],
                ["agentlog", "Agent log"], ["guide", "Guide"]];
  const LABELS = Object.fromEntries(PRIMARY.concat(MORE));

  function render() {
    const root = document.getElementById("root");
    const orgMode = UI.page === "people" && (UI.tab.people || "org") === "org";
    const inMore = MORE.some(([k]) => k === UI.page);

    const tabs = PRIMARY.map(([k, label]) => {
      const unread = k === "requests" ? unreadFor(UI.actor) : 0;
      return `<button class="tab" role="tab" data-act="page" data-page="${k}"
        aria-selected="${UI.page === k}">${esc(label)}${
          unread ? ` <span class="pip">${unread}</span>` : ""}</button>`;
    }).join("");

    const moreMenu = `<div class="morewrap">
      <button class="tab more${inMore ? " on" : ""}" data-act="moretoggle"
        aria-expanded="${!!UI.moreOpen}" aria-haspopup="menu">${
        esc(inMore ? LABELS[UI.page] : "More")} <span class="caret">▾</span></button>
      ${UI.moreOpen ? `<div class="moremenu" role="menu">${MORE.map(([k, label]) =>
        `<button role="menuitem" data-act="page" data-page="${k}"
          class="${UI.page === k ? "on" : ""}">${esc(label)}</button>`).join("")}</div>` : ""}
    </div>`;

    root.innerHTML = `<div class="app${UI.page === "chat" ? " chatmode" : ""}${
      orgMode ? " orgmode" : ""}">
      <aside class="rail">${railHTML()}</aside>
      <main class="canvas"><div class="wrap">
        <div class="tabs" role="tablist">${tabs}${moreMenu}</div>
        <div id="page">${pageHTML()}</div>
      </div></main></div>` +
      (UI.flash ? `<div class="flash">${esc(UI.flash)}</div>` : "") +
      (UI.guideOpen ? guideOverlay() : "");

    if (UI.flash) { const f = UI.flash; setTimeout(() => {
      if (UI.flash === f) { UI.flash = null; const el = document.querySelector(".flash");
        if (el) el.remove(); } }, 4200); }
    afterRender();
  }

  function pageHTML() {
    switch (UI.page) {
      case "people":    return pagePeople();
      case "processes": return pageProcesses();
      case "requests":  return pageRequests();
      case "agentlog":  return pageAgentLog();
      case "dashboard": return pageDashboard();
      case "guide":     return pageGuide();
      default:          return pageChat();
    }
  }

  function flash(msg) { UI.flash = msg; }
  function commit(msg) { if (msg) flash(msg); save(); render(); }
