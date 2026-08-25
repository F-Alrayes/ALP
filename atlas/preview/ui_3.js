
  /* =============================== directory ============================ */

  function pageDirectory() {
    if (UI.person) return personProfile(UI.person);
    if (UI.process) return processProfile(UI.process);
    const which = UI.tab.directory || "people";
    const tabs = [["people", "People"], ["processes", "Processes"], ["graph", "Responsibility graph"]]
      .map(([k, t]) => `<button class="tab" role="tab" data-act="subtab" data-group="directory"
        data-k="${k}" aria-selected="${which === k}">${esc(t)}</button>`).join("");
    const head = phead("Directory & Graph", "Who is responsible for what",
      "The org chart says who reports to whom. This says who owns the work.") +
      `<div class="tabs" role="tablist">${tabs}</div>`;
    if (which === "processes") return head + processList();
    if (which === "graph") return head + graphPanel();
    return head + peopleList();
  }

  function deptOptions(selected) {
    const names = ["All departments"].concat(S.departments.map(d => d.name).sort());
    return names.map(n => `<option${n === selected ? " selected" : ""}>${esc(n)}</option>`).join("");
  }

  function peopleList() {
    const at = now();
    const term = (UI.search || "").trim().toLowerCase();
    const rows = S.people.slice().sort((a, b) => a.name.localeCompare(b.name)).filter(p => {
      const dept = E.departmentName(S, p);
      if (UI.dept !== "All departments" && dept !== UI.dept) return false;
      if (term && !(p.name.toLowerCase().includes(term) || p.title.toLowerCase().includes(term)))
        return false;
      return true;
    });
    const cards = rows.map(p => {
      const owned = S.responsibilities.filter(r => r.person_id === p.id &&
        (r.role === "owner" || r.role === "approver")).length;
      const load = S.requests.filter(r => r.assignee_id === p.id &&
        E.OPEN_STATUSES.includes(r.status)).length;
      const ooo = E.isOutOfOffice(p, at);
      return `<div class="rowline"><div class="card">
        <div class="card-t">${esc(p.name)}</div>
        <div class="card-m"><span>${esc(p.title)}</span><span>${esc(E.departmentName(S, p))}</span></div>
        <div class="card-m" style="margin-top:7px">${badge(owned + " owned/approved", "role")}
          ${badge(load + " open", load ? "gold" : "mute")}
          ${ooo ? badge("OOO until " + E.fmtDate(p.ooo_until), "ooo") : ""}</div>
      </div><button class="btn sm" data-act="person" data-id="${p.id}">View</button></div>`;
    }).join("");
    return `<div class="toolbar">
        <div class="grow"><label class="lbl" for="ps">Search people</label>
          <input id="ps" class="field" data-act="search" placeholder="name or title"
            value="${esc(UI.search || "")}"></div>
        <div class="grow"><label class="lbl" for="pd">Department</label>
          <select id="pd" class="field" data-act="dept">${deptOptions(UI.dept)}</select></div>
      </div>
      <p class="muted" style="margin-bottom:9px">${rows.length} people</p>` +
      (rows.length ? `<div class="stack">${cards}</div>` : empty("Nobody matches that search."));
  }

  function processList() {
    const at = now();
    const cards = S.processes.slice().sort((a, b) => a.name.localeCompare(b.name)).map(p => {
      const owners = E.holders(S, p.id, "owner");
      const dels = E.holders(S, p.id, "delegate");
      const open = S.requests.filter(r => r.process_id === p.id &&
        E.OPEN_STATUSES.includes(r.status)).length;
      const ownerBadge = owners.length
        ? badge("Owner: " + owners[0].name, E.isOutOfOffice(owners[0], at) ? "ooo" : "role")
        : badge("Orphan — no owner", "escalated");
      return `<div class="rowline"><div class="card${owners.length ? "" : " alarm"}">
        <div class="card-t">${esc(p.name)}</div>
        <div class="card-m"><span>${esc(p.category)}</span></div>
        <div class="card-m" style="margin-top:7px">${ownerBadge}
          ${dels.length ? badge("Delegate: " + dels[0].name, "mute") : ""}
          ${badge(open + " open", open ? "gold" : "mute")}</div>
      </div><button class="btn sm" data-act="process" data-id="${p.id}">View</button></div>`;
    }).join("");
    return `<div class="stack">${cards}</div>`;
  }

  function personProfile(id) {
    const p = person(id);
    if (!p) { UI.person = null; return pageDirectory(); }
    const at = now();
    const stats = E.personStats(S, id);
    const grouped = E.responsibilitiesOf(S, id);
    const mgr = p.manager_id ? person(p.manager_id) : null;
    const reports = S.people.filter(x => x.manager_id === id).sort((a, b) => a.name.localeCompare(b.name));
    const recent = S.requests.filter(r => r.assignee_id === id)
      .sort((a, b) => b.last_action_at - a.last_action_at).slice(0, 6);
    const ooo = E.isOutOfOffice(p, at);
    const roleRows = ["owner", "approver", "delegate", "backup"].map(role => {
      const list = grouped[role] || [];
      if (!list.length) return "";
      return `<div class="kv"><span class="k">${esc(role[0].toUpperCase() + role.slice(1))}</span>
        <span class="chips">${list.map(x => badge(x.name, "role")).join(" ")}</span></div>`;
    }).join("");

    return `<button class="btn sm" data-act="backdir">← Back to the directory</button>
      <div class="card flag" style="margin-top:13px">
        <div class="card-t">${esc(p.name)} ${ooo ? badge("Out of office until " +
          E.fmtDate(p.ooo_until), "ooo") : ""}</div>
        <div class="card-m"><span>${esc(p.title)}</span><span>${esc(E.departmentName(S, p))}</span>
          <span class="mono">${esc(p.email)}</span></div>
      </div>
      <div class="tiles" style="margin-top:16px">
        ${tile("Open load", String(stats.open_load), "requests with them now",
               stats.open_load >= 3 ? "warn" : "")}
        ${tile("Completed", String(stats.completed), "all time")}
        ${tile("Avg turnaround", stats.avg_turnaround_hours !== null ?
               Math.round(stats.avg_turnaround_hours) + "h" : "—", "raised to completed")}
        ${tile("Avg to acknowledge", stats.avg_ack_hours !== null ?
               Math.round(stats.avg_ack_hours) + "h" : "—", "first response")}
      </div>
      <div class="grid2">
        <div>
          <h2>Reporting line</h2>
          <div style="margin-top:9px">
            <div class="kv"><span class="k">Manager</span>${esc(mgr ? mgr.name : "—")}</div>
            <div class="kv"><span class="k">Direct reports</span>${
              esc(reports.length ? reports.map(r => r.name).join(", ") : "—")}</div>
          </div>
          <h2 style="margin-top:20px">Responsibilities</h2>
          <div style="margin-top:9px">${roleRows ||
            `<p class="muted">No edges in the responsibility graph.</p>`}</div>
        </div>
        <div><h2>Recent requests</h2><div class="stack" style="margin-top:9px">${
          recent.length ? recent.map(r => `<div class="card">
            <div class="card-t">#${r.id} — ${esc(r.title)}</div>
            <div class="card-m">${statusBadge(r.status)}
              <span>${esc(r.process_id ? E.process_(S, r.process_id).name : "Unmatched")}</span>
              <span class="mono">${esc(human(now() - r.created_at))} old</span></div></div>`).join("")
            : empty("No requests routed here yet.")}</div></div>
      </div>`;
  }

  function processProfile(id) {
    const p = E.process_(S, id);
    if (!p) { UI.process = null; return pageDirectory(); }
    const at = now();
    const stats = E.processStats(S, id);
    const orphan = !E.holders(S, id, "owner").length;
    const recent = S.requests.filter(r => r.process_id === id)
      .sort((a, b) => b.created_at - a.created_at).slice(0, 8);
    const roleRows = ["owner", "approver", "delegate", "backup"].map(role => {
      const list = E.holders(S, id, role);
      if (!list.length) return `<div class="kv"><span class="k">${esc(role[0].toUpperCase() +
        role.slice(1))}</span><span class="muted">not configured</span></div>`;
      return `<div class="kv"><span class="k">${esc(role[0].toUpperCase() + role.slice(1))}</span>
        <span class="chips">${list.map(x => badge(x.name + (E.isOutOfOffice(x, at) ? " · OOO" : ""),
          E.isOutOfOffice(x, at) ? "ooo" : "role")).join(" ")}</span></div>`;
    }).join("");

    return `<button class="btn sm" data-act="backdir">← Back to processes</button>
      <div class="card ${orphan ? "alarm" : "flag"}" style="margin-top:13px">
        <div class="card-t">${esc(p.name)} ${orphan ? badge("Orphan — no owner", "escalated") : ""}</div>
        <div class="card-m"><span>${esc(p.category)}</span></div>
        <div class="card-b">${esc(p.description)}</div>
      </div>
      <div class="tiles" style="margin-top:16px">
        ${tile("Requests", String(stats.total), "all time")}
        ${tile("Open now", String(stats.open), "in the queue", stats.open ? "warn" : "")}
        ${tile("Completed", String(stats.completed), "all time")}
        ${tile("Avg turnaround", stats.avg_turnaround_hours !== null ?
               Math.round(stats.avg_turnaround_hours) + "h" : "—", "raised to completed")}
      </div>
      <div class="grid2">
        <div><h2>Who is accountable</h2>
          ${orphan ? `<div class="note bad" style="margin:9px 0">Nobody owns this process.
            Requests matched to it are parked for the Atlas admin.</div>` : ""}
          <div style="margin-top:9px">${roleRows}</div>
          <h2 style="margin-top:20px">Matching keywords</h2>
          <div class="chips" style="margin-top:9px">${
            E.keywordList(p).map(k => badge(k, "mute")).join(" ") || `<span class="muted">none</span>`}</div>
        </div>
        <div><h2>Recent requests</h2><div class="stack" style="margin-top:9px">${
          recent.length ? recent.map(r => `<div class="card">
            <div class="card-t">#${r.id} — ${esc(r.title)}</div>
            <div class="card-m">${statusBadge(r.status)}
              <span>with ${esc(r.assignee_id ? person(r.assignee_id).name : "Unassigned")}</span>
              <span class="mono">${esc(human(now() - r.created_at))} old</span></div></div>`).join("")
            : empty("No requests have used this process yet.")}</div></div>
      </div>`;
  }

  function graphPanel() {
    const dept = UI.graphDept || "All departments";
    const g = E.responsibilityGraph(S, dept === "All departments" ? null : dept);
    return `<p class="sub">Gold nodes are processes, green nodes are people. Line colour is the
        role: owner, approver, delegate or backup. Hover a node for its name.</p>
      <div class="toolbar" style="margin-top:11px"><div class="grow">
        <label class="lbl" for="gd">Filter people by department</label>
        <select id="gd" class="field" data-act="graphdept">${deptOptions(dept)}</select></div></div>` +
      (g.edges.length ? `<div class="chart">${graphSVG(g)}</div>`
        : empty("No responsibility edges to draw for that filter."));
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

    return phead("Agent Log", "What the agent did, and why",
      "The agent evaluates its rules against simulated time every couple of seconds. " +
      "Nothing here was triggered by a human.") +
      `<div class="tiles">
        ${tile("Agent", "Running", "last pass " + (S.lastTickAt ? fmtTime(S.lastTickAt) : "—"), "good")}
        ${tile("Chases sent", String(counts.chase), "unacknowledged after 48h")}
        ${tile("Reroutes", String(counts.reroute), "cover picked up the work")}
        ${tile("Escalations", String(counts.esc), "handed to a manager", counts.esc ? "bad" : "")}
      </div>
      <div class="toolbar">
        <div class="grow"><label class="lbl" for="lf">Show</label>
          <select id="lf" class="field" data-act="logfilter">${opts}</select></div>
        <button class="btn" data-act="tick">Run the agent now</button>
      </div>
      <p class="muted" style="margin-bottom:9px">${rows.length} entries · simulated time
        <span class="mono">${esc(fmtTime(at))}</span></p>` +
      (rows.length ? `<div class="stack">${cards}</div>`
        : empty("The agent has not needed to act yet.",
                "Advance the simulated clock in the sidebar to make chases and escalations fire."));
  }
