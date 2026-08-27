
  /* ============================== requests ============================== */

  function requestRow(r, counterpartId, label) {
    const proc = r.process_id ? E.process_(S, r.process_id) : null;
    const cp = counterpartId ? person(counterpartId) : null;
    const unread = S.messages.filter(m => m.request_id === r.id && !m.read &&
      m.recipient_id === UI.actor).length;
    const chase = r.chase_count ? ` · ${r.chase_count} chase${r.chase_count === 1 ? "" : "s"}` : "";
    return `<div class="rowline">
      <div class="card ${r.status === "escalated" ? "alarm" : (r.status === "pending" ? "flag" : "")}">
        <div class="card-t">#${r.id} — ${esc(r.title)}</div>
        <div class="card-m">${statusBadge(r.status)}
          <span>${esc(proc ? proc.name : "Unmatched")}</span>
          <span>${esc(label)} ${esc(cp ? cp.name : "—")}</span>
          <span class="mono">raised ${esc(human(now() - r.created_at))} ago · quiet for ${
            esc(human(now() - r.last_action_at))}${esc(chase)}</span></div>
      </div>
      <button class="btn sm" data-act="open" data-id="${r.id}">Open${unread ? ` (${unread})` : ""}</button>
    </div>`;
  }

  function pageRequests() {
    if (UI.open) return requestDetail(UI.open);
    const me = actor();
    const open = S.requests.filter(r => r.assignee_id === UI.actor && E.OPEN_STATUSES.includes(r.status))
      .sort((a, b) => b.last_action_at - a.last_action_at);
    const mine = S.requests.filter(r => r.requester_id === UI.actor)
      .sort((a, b) => b.created_at - a.created_at);
    const done = S.requests.filter(r => r.assignee_id === UI.actor && r.status === "completed")
      .sort((a, b) => b.last_action_at - a.last_action_at);
    const which = UI.tab.requests || "inbox";
    const rows = which === "inbox" ? open : which === "mine" ? mine : done;
    const label = which === "mine" ? "with" : "from";
    const cp = r => which === "mine" ? r.assignee_id : r.requester_id;

    const tabs = [["inbox", `My inbox (${open.length})`], ["mine", `My requests (${mine.length})`],
                  ["done", "Completed by me"]].map(([k, t]) =>
      `<button class="tab" role="tab" data-act="subtab" data-group="requests" data-k="${k}"
        aria-selected="${which === k}">${esc(t)}</button>`).join("");

    const caption = "";

    return phead("Requests", `${me.name}'s desk`,
      `${open.length} with you · ${mine.length} raised by you`) +
      `<div class="tabs" role="tablist">${tabs}</div>` +
      (rows.length ? `<div class="stack">${rows.map(r => requestRow(r, cp(r), label)).join("")}</div>`
        : empty("Nothing here."));
  }

  function requestDetail(id) {
    const r = E.request(S, id);
    if (!r) { UI.open = null; return pageRequests(); }
    E.markRead(S, UI.actor, id);
    const proc = r.process_id ? E.process_(S, r.process_id) : null;
    const a = r.assignee_id ? person(r.assignee_id) : null;
    const req = person(r.requester_id);
    const orig = r.original_assignee_id ? person(r.original_assignee_id) : null;
    const msgs = S.messages.filter(m => m.request_id === id)
      .sort((x, y) => x.created_at - y.created_at || x.id - y.id);
    const isAssignee = r.assignee_id === UI.actor;
    const isOpen = E.OPEN_STATUSES.includes(r.status);

    const actions = !isOpen
      ? `<div class="note info">This request is closed.</div>`
      : isAssignee ? `
        <div style="display:flex;gap:9px;flex-wrap:wrap">
          <button class="btn" data-act="ack" data-id="${id}"${
            r.status === "pending" || r.status === "escalated" ? "" : " disabled"}>Acknowledge</button>
          <button class="btn" data-act="prog" data-id="${id}"${
            r.status === "in_progress" ? " disabled" : ""}>Mark in progress</button>
          <button class="btn primary" data-act="done" data-id="${id}">Complete</button>
        </div>
        <label class="lbl" style="margin-top:13px" for="note">Add a note (sent to the requester)</label>
        <div style="display:flex;gap:9px">
          <input id="note" class="field" data-act="note" value="${esc(UI.note || "")}">
          <button class="btn" data-act="sendnote" data-id="${id}">Send note</button>
        </div>`
      : `<p class="sub">Switch to <strong>${esc(a ? a.name : "the assignee")}</strong>
         to act on it.</p>`;

    return `<button class="btn sm" data-act="back">← Back to the list</button>
      <div class="card flag" style="margin-top:13px">
        <div class="card-t">#${r.id} — ${esc(r.title)}</div>
        <div class="card-m">${statusBadge(r.status)}<span>${esc(proc ? proc.name : "Unmatched")}</span>
          <span class="mono">raised ${esc(human(now() - r.created_at))} ago</span></div>
        <div class="card-b">${esc(r.body)}</div>
      </div>
      <div class="grid2" style="margin-top:20px">
        <div><h2>Timeline</h2><div style="margin-top:9px">${trail(timelineOf(id))}</div></div>
        <div>
          <h2>Detail</h2>
          <div style="margin-top:9px">
            <div class="kv"><span class="k">Requester</span>${esc(req ? req.name : "—")}</div>
            <div class="kv"><span class="k">Assignee</span>${esc(a ? a.name : "Unassigned")}</div>
            ${orig && a && orig.id !== a.id ? `<div class="kv"><span class="k">Originally</span>
              ${esc(orig.name)} ${badge("rerouted", "gold")}</div>` : ""}
            <div class="kv"><span class="k">Raised</span><span class="mono">${esc(fmtTime(r.created_at))}</span></div>
            <div class="kv"><span class="k">Acknowledged</span><span class="mono">${esc(fmtTime(r.acknowledged_at))}</span></div>
            <div class="kv"><span class="k">Completed</span><span class="mono">${esc(fmtTime(r.completed_at))}</span></div>
            <div class="kv"><span class="k">Chases sent</span><span class="mono">${r.chase_count}</span></div>
          </div>
          <h2 style="margin-top:20px">Messages</h2>
          <div class="stack" style="margin-top:9px">${msgs.map(m => `<div class="card">
            <div class="card-m">${badge(m.type.replace(/_/g, " "), "role")}
              <span>${esc(m.sender_id ? person(m.sender_id).name : "Atlas agent")} →
                ${esc(person(m.recipient_id) ? person(m.recipient_id).name : "—")}</span>
              <span class="mono">${esc(fmtTime(m.created_at))}</span></div>
            <div class="card-b">${esc(m.body)}</div></div>`).join("")}</div>
        </div>
      </div>
      <div class="sect"><h2>Actions</h2></div>${actions}`;
  }

  /* =============================== agent log ============================ */

  const LOG_FILTERS = {
    "Autonomous actions": ["chase","escalation","escalation_blocked","reroute_ooo","reroute_chase","ooo_no_cover"],
    "Chases": ["chase"],
    "Reroutes": ["reroute","reroute_ooo","reroute_chase"],
    "Escalations": ["escalation","escalation_blocked"],
    "Routing decisions": ["routing","dispatch","orphan"],
    "Everything": null,
  };

  function pageAgentLog() {
    const at = now();
    const counts = {
      chase: S.events.filter(e => e.type === "chase").length,
      reroute: S.events.filter(e => e.type === "reroute_ooo" || e.type === "reroute_chase").length,
      esc: S.events.filter(e => e.type === "escalation").length,
    };
    const types = LOG_FILTERS[UI.filter] || null;
    const rows = S.events.filter(e => !types || types.includes(e.type))
      .sort((a, b) => b.created_at - a.created_at || b.id - a.id).slice(0, 200);

    const cards = rows.map(e => {
      const r = e.request_id ? E.request(S, e.request_id) : null;
      const tone = e.type.indexOf("escalation") === 0 ? "escalated"
        : (AGENT_TYPES.has(e.type) ? "gold" : "mute");
      const label = EVENT_LABELS[e.type] ||
        e.type.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
      return `<div class="card${e.type.indexOf("escalation") === 0 ? " alarm" : ""}">
        <div class="card-m">${badge(label, tone)}
          <span class="mono">${esc(fmtTime(e.created_at))} · ${esc(human(at - e.created_at))} ago</span>
          <strong>${esc(e.actor)}</strong>
          <span>${esc(r ? "#" + r.id + " — " + r.title : "no request")}</span></div>
        <div class="card-b">${esc(e.detail)}</div></div>`;
    }).join("");

    const opts = Object.keys(LOG_FILTERS).map(k =>
      `<option${k === UI.filter ? " selected" : ""}>${esc(k)}</option>`).join("");

    return phead("Agent", "What the agent did", "Nobody triggered any of this.") +
      `<div class="tiles">
        ${tile("Chases sent", String(counts.chase), "after 48h")}
        ${tile("Reroutes", String(counts.reroute), "to a cover")}
        ${tile("Escalations", String(counts.esc), "to a manager", counts.esc ? "bad" : "")}
      </div>
      <div class="toolbar">
        <div class="grow"><label class="lbl" for="lf">Show</label>
          <select id="lf" class="field" data-act="logfilter">${opts}</select></div>
        <button class="btn" data-act="tick">Run the agent now</button>
      </div>
      <p class="muted" style="margin-bottom:9px">${rows.length} entries</p>` +
      (rows.length ? `<div class="stack">${cards}</div>`
        : empty("Nothing yet.", "Move the clock forward in Demo controls."));
  }
