
  /* ================================ intake ============================== */

  const EXAMPLES = [
    "I need access to the data room for Project Falcon",
    "Invoice 88596 from Halcyon needs approving before Friday's payment run",
    "I am locked out of my account and cannot log in",
    "We need to renew the Bloomberg contract before it expires",
  ];

  function pageIntake() {
    if (UI.sent) return intakeSent(UI.sent);
    const head = phead("Intake", "What do you need?",
      "Describe it in your own words. Atlas identifies the process, finds who is accountable " +
      "right now, and drafts the request for you.");

    const chips = `<div class="chips">` + EXAMPLES.map((x, i) =>
      `<button class="chip" data-act="example" data-i="${i}" title="${esc(x)}">${
        esc(x.length <= 40 ? x : x.slice(0, 37).replace(/\s+\S*$/, "") + "…")}</button>`).join("") +
      `</div>`;

    const box = `<label class="sr" for="q">Your request</label>
      <textarea id="q" class="field" data-act="query" rows="3"
        placeholder="e.g. I need access to the data room for Project Falcon">${esc(UI.query)}</textarea>`;

    const query = (UI.query || "").trim();
    if (!query) return head + box + chips +
      `<div style="margin-top:20px">${empty("Nothing to route yet.",
        "Type a request above, or pick one of the examples to see the resolution trace.")}</div>`;

    const matches = E.matchProcesses(S.processes, query, 3);
    const top = matches[0];
    const chosenId = UI.override !== null && UI.override !== undefined
      ? UI.override : (top && top.confidence >= 25 ? top.process_id : S.processes[0].id);
    const proc = E.process_(S, chosenId);
    const res = E.resolve(S, proc);
    const me = actor();
    const title = UI.title !== undefined && UI.title !== null
      ? UI.title : E.suggestTitle(query, proc ? proc.name : null);
    const body = UI.body !== undefined && UI.body !== null
      ? UI.body : E.draftBody(me, proc, res, query);
    const dupes = E.findSimilarOpen(S, { process_id: chosenId, requester_id: UI.actor, title });

    const weak = !top || top.confidence < 25;
    const kw = top && top.matched_keywords.length
      ? top.matched_keywords.slice(0, 6).map(k => badge(k, "role")).join(" ")
      : `<span class="muted">no direct keyword hits</span>`;

    const matchCard = top ? `<div class="card flag">
        <div class="card-t">${esc(top.process_name)}
          ${badge(top.confidence.toFixed(0) + "% · " + top.confidence_label,
                  top.confidence >= 70 ? "gold" : "mute")}</div>
        <div class="card-m">${esc(top.category)}</div>
        <div class="card-b">${esc(E.why(top))}</div>
        <div style="margin-top:9px" class="chips">${kw}</div>
      </div>
      <details class="card" style="margin-top:9px"><summary style="cursor:pointer;font-size:.88rem">
        Why this matched — signal breakdown</summary>
        <div style="margin-top:9px">${matches.map(m => `<div class="kv">
          <span class="k">${esc(m.process_name)}</span>
          <span class="mono">${m.confidence.toFixed(0)}% · ` +
          ["keywords","name","tfidf","description"].map(k =>
            `${k}: ${Math.round(m.signals[k] * 100)}%`).join(" · ") +
          `</span></div>`).join("")}</div></details>` : "";

    const options = S.processes.slice().sort((a, b) => a.name.localeCompare(b.name)).map(p =>
      `<option value="${p.id}"${p.id === chosenId ? " selected" : ""}>${esc(p.name)} — ${esc(p.category)}</option>`
    ).join("");

    const steps = `<div class="trail">` + res.steps.map(s =>
      `<div class="node ${s.outcome}"><div class="k">${esc(s.label)}</div>
       <div class="d">${esc(s.detail)}</div></div>`).join("") + `</div>`;

    const dupBlock = dupes.length ? `<div class="sect"><h2>Possible duplicate</h2></div>
      <div class="note warn">An open request on this process already looks like yours. Follow it
        instead of adding another item to the same queue.</div>
      <div class="stack" style="margin-top:9px">` + dupes.map(d => `
        <div class="rowline"><div class="card">
          <div class="card-t">#${d.request.id} — ${esc(d.request.title)}</div>
          <div class="card-m">${statusBadge(d.request.status)}
            <span>with ${esc(d.request.assignee_id ? person(d.request.assignee_id).name : "Unassigned")}</span>
            <span class="mono">${d.similarity.toFixed(0)}% similar</span></div>
          <div class="card-b">${esc(d.reason)}</div></div>
        <button class="btn sm" data-act="follow" data-id="${d.request.id}">Follow</button></div>`
      ).join("") + `</div>` : "";

    return head + box + chips +
      `<div class="sect"><h2>Process match</h2></div>` +
      (weak ? `<div class="note warn" style="margin-bottom:9px">No process matched with usable
        confidence. Pick one manually, or send it anyway and Atlas will park it for the admin.</div>` : "") +
      matchCard +
      `<div style="margin-top:12px"><label class="lbl" for="routeas">Route as</label>
        <select id="routeas" class="field" data-act="override">${options}</select></div>` +
      `<div class="sect"><h2>Resolution trace</h2></div>` + steps +
      `<div class="note ${res.needs_admin ? "bad" : "info"}">${esc(E.resolutionSummary(res))}</div>` +
      dupBlock +
      `<div class="sect"><h2>Drafted request</h2></div>
       <label class="lbl" for="rt">Title</label>
       <input id="rt" class="field" data-act="title" value="${esc(title)}">
       <label class="lbl" for="rb" style="margin-top:11px">Message</label>
       <textarea id="rb" class="field" data-act="body" rows="9">${esc(body)}</textarea>
       <div style="margin-top:13px" class="stack">
         <div class="kv"><span class="k">Will be sent to</span><strong>${
           esc(res.assignee_name || "the Atlas admin (no owner resolved)")}</strong></div>
         <div class="kv"><span class="k">Raised by</span>${esc(me.name)}</div>
         <div class="kv"><span class="k">Simulated time</span><span class="mono">${esc(fmtTime(now()))}</span></div>
       </div>
       <div style="margin-top:15px;display:flex;gap:9px">
         <button class="btn primary" data-act="send">Send request</button>
         <button class="btn" data-act="clear">Clear</button>
       </div>`;
  }

  function intakeSent(id) {
    const r = E.request(S, id);
    if (!r) { UI.sent = null; return pageIntake(); }
    const proc = r.process_id ? E.process_(S, r.process_id) : null;
    const a = r.assignee_id ? person(r.assignee_id) : null;
    return phead("Intake", "Request dispatched", "") +
      `<div class="note info">Request #${r.id} dispatched.</div>
       <div class="card flag" style="margin-top:11px">
         <div class="card-t">#${r.id} — ${esc(r.title)}</div>
         <div class="card-m">${statusBadge(r.status)}<span>${esc(proc ? proc.name : "Unmatched")}</span>
           <span>assigned to ${esc(a ? a.name : "the Atlas admin")}</span></div>
       </div>
       <div class="sect"><h2>Timeline</h2></div>${trail(timelineOf(id))}
       <div style="margin-top:15px"><button class="btn primary" data-act="another">Raise another request</button></div>`;
  }

  /* =============================== requests ============================= */

  function requestRow(r, counterpartId, label, prefix) {
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

    const caption = which === "inbox" ? "Work Atlas has routed to you, newest activity first."
      : which === "mine" ? "Everything you have raised, including what the agent has done with it."
      : "Requests you have closed.";

    return phead("Requests", `${me.name}'s desk`,
      `${open.length} open with you · ${mine.length} raised by you · ${unreadFor(UI.actor)} unread`) +
      `<div class="tabs" role="tablist">${tabs}</div>
       <p class="sub" style="margin-bottom:11px">${esc(caption)}</p>` +
      (rows.length ? `<div class="stack">${rows.map(r =>
        requestRow(r, cp(r), label, which)).join("")}</div>`
        : empty("Nothing here.", "Requests will appear as they are raised or routed to you."));
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
      : `<p class="sub">You are watching this request. Switch to
         <strong>${esc(a ? a.name : "the assignee")}</strong> in the sidebar to act on it.</p>`;

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
