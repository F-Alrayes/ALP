
  /* ============================ people & org tree ======================= */

  const NODE_W = 208, NODE_H = 66, H_GAP = 20, V_GAP = 62;

  const DEPT_HUE = {
    "Executive": "var(--dept-a)", "Finance": "var(--dept-b)",
    "Legal & Compliance": "var(--dept-c)", "IT": "var(--dept-d)",
    "Operations / HR": "var(--dept-e)", "Investments / Deal Team": "var(--dept-f)",
  };
  const deptColor = d => DEPT_HUE[d] || "var(--ink-3)";

  const isCollapsed = id => !!UI.tree.collapsed[id];

  function initials(name) {
    const parts = String(name || "").split(/\s+/).filter(Boolean);
    if (!parts.length) return "?";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  function findNode(roots, id) {
    for (const r of roots) {
      if (r.id === id) return r;
      const found = findNode(r.children, id);
      if (found) return found;
    }
    return null;
  }

  // Best-match first: a name that starts with the term beats one that merely
  // contains it, which beats a title or team hit.
  function searchMatches(term) {
    const t = String(term || "").trim().toLowerCase();
    if (!t) return [];
    const score = p => {
      const n = p.name.toLowerCase();
      if (n.startsWith(t)) return 4;
      if (n.split(" ").some(w => w.startsWith(t))) return 3;
      if (n.includes(t)) return 2;
      if (p.title.toLowerCase().includes(t)) return 1;
      return 0;
    };
    return S.people
      .map(p => ({ p, s: Math.max(score(p),
        E.departmentName(S, p).toLowerCase().includes(t) ? 1 : 0) }))
      .filter(x => x.s > 0)
      .sort((a, b) => b.s - a.s || a.p.name.localeCompare(b.p.name))
      .map(x => x.p);
  }

  // Tidy-tree layout: leaves take the next slot, parents centre over children.
  function layoutTree(roots) {
    const cursor = { x: 0 };
    const placed = [];
    const walk = (node, depth) => {
      const kids = isCollapsed(node.id) ? [] : node.children;
      let x;
      if (!kids.length) {
        x = cursor.x;
        cursor.x += NODE_W + H_GAP;
      } else {
        const childXs = kids.map(k => walk(k, depth + 1));
        x = (childXs[0] + childXs[childXs.length - 1]) / 2;
      }
      placed.push({ node, x, y: depth * (NODE_H + V_GAP), depth });
      return x;
    };
    roots.forEach(r => walk(r, 0));
    const width = Math.max(cursor.x, NODE_W + H_GAP);
    const depth = Math.max(...placed.map(p => p.y)) + NODE_H + 14;
    return { placed, width, height: depth };
  }

  function treeSVG() {
    const dept = UI.tree.dept;
    const forest = E.orgTree(S);
    // Focusing re-roots the chart on one person, which hides everyone above them.
    const focused = UI.tree.root ? findNode(forest, UI.tree.root) : null;
    const roots = focused ? [focused] : forest;
    const { placed, width, height } = layoutTree(roots);
    const byId = new Map(placed.map(p => [p.node.id, p]));
    const at = now();

    const edges = placed.filter(p => p.node.manager_id && byId.has(p.node.manager_id))
      .map(p => {
        const parent = byId.get(p.node.manager_id);
        const x1 = parent.x + NODE_W / 2, y1 = parent.y + NODE_H;
        const x2 = p.x + NODE_W / 2, y2 = p.y;
        const mid = y1 + V_GAP / 2;
        return `<path d="M${x1} ${y1} V${mid} H${x2} V${y2}" fill="none"
          stroke="var(--line)" stroke-width="1.5"/>`;
      }).join("");

    const nodes = placed.map(p => {
      const n = p.node;
      const pers = person(n.id);
      const ooo = pers && E.isOutOfOffice(pers, at);
      const hidden = n.children.length && isCollapsed(n.id);
      const dim = dept !== "All departments" && n.department !== dept;
      const selected = UI.tree.selected === n.id;
      const hue = deptColor(n.department);
      const toggle = n.children.length ? `
        <g class="tgl" data-act="treetoggle" data-id="${n.id}" tabindex="0"
           role="button" aria-label="${hidden ? "Expand" : "Collapse"} ${esc(n.name)}'s team">
          <circle cx="${NODE_W / 2}" cy="${NODE_H + 1}" r="10"
            fill="var(--surface)" stroke="var(--line)"/>
          <text x="${NODE_W / 2}" y="${NODE_H + 5}" text-anchor="middle"
            class="tglt">${hidden ? "+" + n.descendants : "–"}</text>
        </g>` : "";
      const title = n.title.length > 26 ? n.title.slice(0, 24) + "…" : n.title;
      return `<g class="onode${dim ? " dim" : ""}${selected ? " sel" : ""}"
          data-node="${n.id}" style="--d:${hue}" transform="translate(${p.x},${p.y})">
        <g data-act="treeselect" data-id="${n.id}" tabindex="0" role="button"
           aria-label="${esc(n.name)}, ${esc(n.title)}, ${esc(n.department)}">
          <rect class="obox" width="${NODE_W}" height="${NODE_H}" rx="11"/>
          <circle class="oav oavr" cx="30" cy="${NODE_H / 2}" r="15" stroke-width="1"/>
          <text class="oavt" x="30" y="${NODE_H / 2 + 4}" text-anchor="middle">${esc(initials(n.name))}</text>
          <text class="oname" x="55" y="${NODE_H / 2 - 4}">${esc(n.name)}</text>
          <text class="otitle" x="55" y="${NODE_H / 2 + 13}">${esc(title)}</text>
          ${ooo ? `<circle class="oaway" cx="${NODE_W - 15}" cy="17" r="5"/>` : ""}
        </g>${toggle}</g>`;
    }).join("");

    const t = UI.tree;
    return `<svg id="treesvg" viewBox="0 0 ${width} ${height + 24}"
      style="width:${Math.round(width * t.zoom)}px;height:${Math.round((height + 24) * t.zoom)}px"
      role="img" aria-label="Organisation chart of ${S.people.length} people">
      <g>${edges}${nodes}</g></svg>`;
  }

  // Deliberately short: a first-time viewer needs who they are, who they report
  // to, and what they own. Everything else is a click away in Ask Atlas.
  function treeDetail() {
    const id = UI.tree.selected;
    if (!id) return "";
    const p = person(id);
    if (!p) return "";
    const at = now();
    const mgr = p.manager_id ? person(p.manager_id) : null;
    const reports = S.people.filter(x => x.manager_id === id).length;
    const owns = (E.responsibilitiesOf(S, id).owner || []).map(x => x.name);

    return `<div class="side-head">
        <div><h3>${esc(p.name)}</h3><p class="sub">${esc(p.title)}</p></div>
        <button class="btn sm" data-act="treeclose" aria-label="Close">✕</button>
      </div>
      <div class="chips tight">${badge(E.departmentName(S, p), "role")}
        ${E.isOutOfOffice(p, at) ? badge("Away until " + E.fmtDate(p.ooo_until), "ooo") : ""}</div>
      <div class="kv"><span class="k">Reports to</span>${esc(mgr ? mgr.name : "Nobody — top of the firm")}</div>
      ${reports ? `<div class="kv"><span class="k">Team</span>${reports} direct report${
        reports === 1 ? "" : "s"}</div>` : ""}
      <div class="kv"><span class="k">Owns</span>${owns.length
        ? esc(owns.join(", ")) : `<span class="muted">nothing directly</span>`}</div>
      <div class="acts">
        <button class="btn primary sm" data-act="askperson" data-id="${p.id}">Ask them for something</button>
        ${UI.tree.root === p.id
          ? `<button class="btn sm" data-act="focusclear">Show whole firm</button>`
          : `<button class="btn sm" data-act="focusperson" data-id="${p.id}">Show just their team</button>`}
      </div>`;
  }

  function pagePeople() {
    const which = UI.tab.people || "org";
    const tabs = [["org", "Org chart"], ["teams", "Teams"]]
      .map(([k, t]) => `<button class="tab" role="tab" data-act="subtab" data-group="people"
        data-k="${k}" aria-selected="${which === k}">${esc(t)}</button>`).join("");
    const tabsBar = `<div class="tabs" role="tablist">${tabs}</div>`;
    if (which === "org") return tabsBar + orgPanel();
    const head = phead("People", "Teams", "") + tabsBar;
    return head + teamsPanel();
  }

  function orgPanel() {
    const t = UI.tree;
    const legend = Object.keys(DEPT_HUE).map(d =>
      `<span><i style="background:${deptColor(d)}"></i>${esc(d)}</span>`).join("");
    return `<div class="orgtools">
        <div class="findwrap">
          <label class="sr" for="ts">Find someone</label>
          <input id="ts" class="field" data-act="treequery" role="combobox" autocomplete="off"
            aria-expanded="false" aria-controls="suggestbox" aria-autocomplete="list"
            placeholder="Find someone by name…" value="${esc(t.query || "")}">
          <div class="suggest-list" id="suggestbox" role="listbox" aria-label="Matching people" hidden></div>
        </div>
        <select class="field slim" data-act="treedept" aria-label="Highlight a team">
          ${deptOptions(t.dept)}</select>
        <div class="zoomer" role="group" aria-label="Zoom">
          <button class="btn sm" data-act="zoom" data-d="-1" aria-label="Zoom out">−</button>
          <span class="mono zoomv">${Math.round(t.zoom * 100)}%</span>
          <button class="btn sm" data-act="zoom" data-d="1" aria-label="Zoom in">+</button>
          <button class="btn sm" data-act="zoomfit">Fit</button>
        </div>
        <button class="btn sm" data-act="expandall">Expand all</button>
        <button class="btn sm" data-act="collapseall">Collapse</button>
      </div>
      ${focusBar()}
      <div class="orgstage">
        <div class="orgscroll" id="orgscroll" data-act="orgpan">${treeSVG()}</div>
        <div class="hovercard" id="hovercard" hidden></div>
        ${UI.tree.selected ? `<aside class="orgpanel">${treeDetail()}</aside>` : ""}
        <div class="orglegend">${legend}<span><i class="ooo-dot"></i>Away</span></div>
      </div>`;
  }

  function focusBar() {
    const focused = UI.tree.root ? person(UI.tree.root) : null;
    const matches = searchMatches(UI.tree.search);
    const others = matches.filter(p => !focused || p.id !== focused.id).slice(0, 5);

    if (!focused) {
      if (!matches.length) return "";
      return `<div class="focusbar">
        <span class="fb-label">${matches.length} match${matches.length === 1 ? "" : "es"}</span>
        <div class="chips">${others.map(p => `<button class="chip sm" data-act="focusperson"
          data-id="${p.id}">${esc(p.name)}</button>`).join("")}</div></div>`;
    }

    const mgr = focused.manager_id ? person(focused.manager_id) : null;
    const above = E.pathToRoot(S, focused.id).length - 1;
    return `<div class="focusbar on">
      <span class="fb-label">Showing ${esc(focused.name)}${
        focused.manager_id ? ` and their team only` : ``}</span>
      ${mgr ? `<button class="btn sm" data-act="focusup" data-id="${mgr.id}">
        ↑ Up to ${esc(mgr.name)}</button>` : ""}
      ${above ? `<span class="muted">${above} level${above === 1 ? "" : "s"} hidden above</span>` : ""}
      <button class="btn sm" data-act="focusclear">Show whole firm</button>
      ${others.length ? `<span class="muted">Other matches:</span>
        <div class="chips">${others.map(p => `<button class="chip sm" data-act="focusperson"
          data-id="${p.id}">${esc(p.name)}</button>`).join("")}</div>` : ""}
    </div>`;
  }

  function teamsPanel() {
    const teams = E.teamSummary(S);
    const at = now();
    return `<div class="stack">${teams.map(t => {
      const members = S.people.filter(p => E.departmentName(S, p) === t.department)
        .sort((a, b) => a.name.localeCompare(b.name));
      const owned = S.responsibilities.filter(r => r.role === "owner" &&
        members.some(m => m.id === r.person_id)).length;
      const load = S.requests.filter(r => E.OPEN_STATUSES.includes(r.status) &&
        members.some(m => m.id === r.assignee_id)).length;
      return `<div class="card">
        <div class="card-t"><span class="swatch" style="background:${deptColor(t.department)}"></span>
          ${esc(t.department)}</div>
        <div class="card-m"><span>Led by ${esc(t.head || "—")}</span>
          <span>${t.size} people</span>
          ${badge(owned + " processes owned", "role")}
          ${badge(load + " open requests", load ? "gold" : "mute")}
          ${t.ooo ? badge(t.ooo + " away", "ooo") : ""}</div>
        <div class="chips tight">${members.map(m =>
          `<button class="chip sm" data-act="treeperson" data-id="${m.id}">${esc(m.name)}</button>`
        ).join("")}</div>
        ${coversLine(t.department)}
      </div>`;
    }).join("")}</div>`;
  }

  // What Atlas will route to this team from a plain-English question. Showing
  // it makes the routing inspectable — and makes clear it is editable data,
  // not something the chat invented.
  function coversLine(name) {
    const dept = S.departments.find(d => d.name === name);
    const words = String(dept && dept.topics || "").split(",")
      .map(w => w.trim()).filter(Boolean);
    if (!words.length) return "";
    return `<details class="why"><summary>Covers ${words.length} topics</summary>
      <p class="sub small">${esc(words.join(" · "))}</p></details>`;
  }

  function deptOptions(selected) {
    const names = ["All departments"].concat(S.departments.map(d => d.name).sort());
    return names.map(n => `<option${n === selected ? " selected" : ""}>${esc(n)}</option>`).join("");
  }

  function pageProcesses() {
    if (UI.process) return processProfile(UI.process);
    return phead("Catalogue", "What you can ask for",
      "Ask for any of these in plain English.") + processList();
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

  function processProfile(id) {
    const p = E.process_(S, id);
    if (!p) { UI.process = null; return pagePeople(); }
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
