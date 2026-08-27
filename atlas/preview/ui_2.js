
  /* ================================= chat =============================== */

  const SUGGESTIONS = [
    "Email whoever owns the data room and ask them for access",
    "Ask whoever approves expenses to sign off my claim",
    "Who owns invoice approval?",
    "What's in my inbox?",
  ];

  function pushMsg(role, kind, data) {
    UI.chat.push({ id: UI.msgSeq++, role, kind, data: data || {}, at: now() });
    if (UI.chat.length > 200) UI.chat.splice(0, UI.chat.length - 200);
  }

  function greet() {
    UI.chat = [];
    pushMsg("bot", "text", { text:
      "Say it how you'd say it out loud. I'll work out who's accountable and send it." });
    pushMsg("bot", "suggest", { items: SUGGESTIONS.slice(0, 3) });
  }

  /* ---------------------------- bot responses --------------------------- */

  // Free text, one entry point. Everything below decides what to do with it;
  // nothing here needs the user to have found anybody in the org chart first.
  function botRequest(u) {
    const query = (u && u.query) || (typeof u === "string" ? u : u.text);
    const matches = E.matchProcesses(S.processes, query, 3);
    const top = matches[0];
    if (!top || top.confidence < 25) {
      pushMsg("bot", "text", { text:
        "I couldn't match that. Pick the closest one, or rephrase it." });
      pushMsg("bot", "pick", { query, options: matches.map(m => m.process_id) });
      return;
    }
    openDraft(query, top.process_id, matches);
  }

  /* -- relays ------------------------------------------------------------
     "Send an email to whoever is responsible for Data and ask them for
     access." Nobody is named, no question is asked, and the user should not
     have to go and look anyone up. Read the sentence, resolve the owner
     through the responsibility graph, and send it. */

  function botRelay(u) {
    const named = u.personId ? person(u.personId) : null;
    const query = u.query || u.text;
    let matches = E.matchProcesses(S.processes, query, 3);

    // A name in the message outranks a keyword hit: prefer what that person is
    // actually on the hook for.
    if (named) {
      const theirs = new Set(E.processesFor(S, named.id).map(x => x.process.id));
      const mine = matches.filter(m => theirs.has(m.process_id) && m.confidence >= 25);
      if (mine.length) matches = mine.concat(matches.filter(m => !mine.includes(m)));
    }

    const top = matches[0];
    if (!top || top.confidence < 25) {
      // Understood the instruction, not the subject.
      if (named) { pushMsg("bot", "askwho", { id: named.id }); return; }
      pushMsg("bot", "text", { text:
        "I can tell you want something raised — I just can't tell what. Pick one:" });
      pushMsg("bot", "pick", { query, options: [] });
      return;
    }

    // Two plausible readings, or one weak one: ask before sending anything.
    const second = matches[1];
    const tooClose = second && second.confidence >= 25 && top.confidence - second.confidence < 20;
    if (tooClose || top.confidence < 55) {
      pushMsg("bot", "choose", { query, text: u.text, subject: u.subject || "",
        ids: matches.filter(m => m.confidence >= 15).slice(0, 3).map(m => m.process_id) });
      return;
    }

    const proc = E.process_(S, top.process_id);
    const res = E.resolve(S, proc);
    const title = E.suggestTitle(u.ask || u.subject || u.text, proc.name);
    const dupes = E.findSimilarOpen(S, { process_id: proc.id, requester_id: UI.actor, title });

    // Anything Atlas can't route cleanly, or that looks like a repeat, goes
    // back to the user before it is sent.
    if (res.needs_admin || res.assignee_id === null || dupes.length) {
      openDraft(u.text, proc.id, matches, title);
      return;
    }

    sendRelay(u, proc, res, title);
  }

  function sendRelay(u, proc, res, title) {
    const me = actor();
    const r = E.createRequest(S, {
      requester_id: UI.actor, process_id: proc.id, assignee_id: res.assignee_id,
      title, body: E.draftBody(me, proc, res, u.text), resolution: res,
    });
    UI.draft = null;
    pushMsg("bot", "sent", { id: r.id, subject: u.subject || "", auto: true });
  }

  // The user picked between two readings. Carry on as if the sentence had been
  // unambiguous — they have already seen who each option would reach.
  function commitChoice(text, processId) {
    const u = E.understand(S, text);
    const proc = E.process_(S, processId);
    if (!proc) return;
    const res = E.resolve(S, proc);
    const title = E.suggestTitle(u.ask || u.subject || text, proc.name);
    const dupes = E.findSimilarOpen(S, { process_id: proc.id, requester_id: UI.actor, title });
    if (res.needs_admin || res.assignee_id === null || dupes.length) {
      openDraft(text, proc.id, null, title);
      return;
    }
    sendRelay(u, proc, res, title);
  }

  function openDraft(query, processId, matches, title) {
    const proc = E.process_(S, processId);
    const res = E.resolve(S, proc);
    const me = actor();
    UI.draft = {
      query, processId,
      title: title || E.suggestTitle(query, proc ? proc.name : null),
      body: E.draftBody(me, proc, res, query),
    };
    pushMsg("bot", "match", {
      query, processId,
      matchIds: (matches || E.matchProcesses(S.processes, query, 3)).map(m => m.process_id),
    });
  }

  function botWhoOwns(text) {
    const proc = E.findProcess(S, text);
    if (!proc) {
      pushMsg("bot", "text", { text:
        "Which one? Try invoice approval, data room access, travel approval." });
      return;
    }
    pushMsg("bot", "owners", { processId: proc.id });
  }

  function botOoo() {
    const at = now();
    const away = S.people.filter(p => E.isOutOfOffice(p, at))
      .sort((a, b) => a.name.localeCompare(b.name));
    if (!away.length) {
      pushMsg("bot", "text", { text: "Nobody is marked out of office right now." });
      return;
    }
    pushMsg("bot", "ooo", { ids: away.map(p => p.id) });
  }

  function botInbox() {
    const rows = S.requests.filter(r => r.assignee_id === UI.actor &&
      E.OPEN_STATUSES.includes(r.status)).sort((a, b) => b.last_action_at - a.last_action_at);
    pushMsg("bot", "reqlist", { ids: rows.map(r => r.id), mine: false,
      empty: "Nothing is sitting with you right now." });
  }

  function botMyRequests() {
    const rows = S.requests.filter(r => r.requester_id === UI.actor)
      .sort((a, b) => b.created_at - a.created_at);
    pushMsg("bot", "reqlist", { ids: rows.map(r => r.id), mine: true,
      empty: "You haven't raised anything yet. Tell me what you need and I'll route it." });
  }

  function botAbout(u) {
    const p = u.personId ? person(u.personId) : E.findPerson(S, u.text);
    if (!p) {
      pushMsg("bot", "text", { text:
        "I couldn't find them. Try their full name, or browse People." });
      return;
    }
    pushMsg("bot", "person", { id: p.id });
  }

  // Reached from the org chart: scope the conversation to one person.
  function botAskWho(personId) {
    pushMsg("bot", "askwho", { id: personId });
  }

  function botHelp() {
    pushMsg("bot", "text", { text:
      "Write it the way you'd say it. \"Email whoever owns the data room and ask " +
      "for access\" is enough — I'll find them and send it.\n\n" +
      "Once sent, I chase after 48h, hand over to a cover, then escalate." });
    pushMsg("bot", "suggest", { items: SUGGESTIONS });
  }

  function submitChat(text) {
    text = String(text || "").trim();
    if (!text) return;
    pushMsg("user", "text", { text });
    UI.draft = null;
    const u = E.understand(S, text);
    switch (u.intent) {
      case "help":        botHelp(); break;
      case "who_ooo":     botOoo(); break;
      case "who_owns":    botWhoOwns(text); break;
      case "my_inbox":    botInbox(); break;
      case "my_requests": botMyRequests(); break;
      case "about":       botAbout(u); break;
      default:            u.relay ? botRelay(u) : botRequest(u);
    }
  }

  /* ------------------------------ rendering ----------------------------- */

  function bubbleUser(m) {
    return `<div class="msg user"><div class="bub">${esc(m.data.text)}</div></div>`;
  }

  function botWrap(inner, extraClass) {
    return `<div class="msg bot ${extraClass || ""}">
      <div class="ava" aria-hidden="true">A</div><div class="bub">${inner}</div></div>`;
  }

  function renderMatch(m) {
    const { query, processId, matchIds } = m.data;
    const proc = E.process_(S, processId);
    const all = E.matchProcesses(S.processes, query, 3);
    const top = all.find(x => x.process_id === processId) || all[0];
    const res = E.resolve(S, proc);
    const isCurrent = UI.draft && UI.draft.processId === processId && UI.draft.query === query;
    const dupes = isCurrent ? E.findSimilarOpen(S, { process_id: processId,
      requester_id: UI.actor, title: UI.draft.title }) : [];

    const kw = top && top.matched_keywords.length
      ? top.matched_keywords.slice(0, 5).map(k => badge(k, "role")).join(" ") : "";

    // Only offer runners-up that actually scored; a 0% suggestion is noise.
    const alts = (matchIds || []).filter(id => id !== processId)
      .map(id => all.find(x => x.process_id === id))
      .filter(x => x && x.confidence >= 15).slice(0, 2);
    const alternatives = alts.map(x => `<button class="chip sm" data-act="switchproc"
        data-id="${x.process_id}" data-mid="${m.id}">${esc(x.process_name)}
        <span class="muted">${x.confidence.toFixed(0)}%</span></button>`).join("") +
      `<button class="chip sm" data-act="repick">Pick another process</button>`;

    const steps = `<div class="trail tight">` + res.steps.map(s =>
      `<div class="node ${s.outcome}"><div class="k">${esc(s.label)}</div>
       <div class="d">${esc(s.detail)}</div></div>`).join("") + `</div>`;

    const dupeBlock = dupes.length ? `<div class="note warn tight">
        <strong>Possible duplicate.</strong> ${esc(dupes[0].reason)}
        <div style="margin-top:7px;display:flex;gap:7px;flex-wrap:wrap">
          <button class="btn sm" data-act="follow" data-id="${dupes[0].request.id}">
            Follow #${dupes[0].request.id} instead</button></div></div>` : "";

    const draftBlock = isCurrent ? `
      <div class="draft">
        <label class="lbl" for="dt">Title</label>
        <input id="dt" class="field" data-act="dtitle" value="${esc(UI.draft.title)}">
        <label class="lbl" for="db" style="margin-top:9px">Message to ${esc(res.assignee_name || "the admin")}</label>
        <textarea id="db" class="field" data-act="dbody" rows="7">${esc(UI.draft.body)}</textarea>
        <div class="acts">
          <button class="btn primary" data-act="chatsend">Send it</button>
          <button class="btn" data-act="chatcancel">Cancel</button>
          <span class="muted" style="align-self:center">Not right?</span>${alternatives}
        </div>
      </div>` : `<p class="muted">This draft has been dealt with.</p>`;

    return botWrap(`
      <p>That looks like <strong>${esc(proc.name)}</strong>${top ?
        ` — ${badge(top.confidence.toFixed(0) + "% · " + top.confidence_label,
          top.confidence >= 70 ? "gold" : "mute")}` : ""}</p>
      ${kw ? `<div class="chips tight">${kw}</div>` : ""}
      ${top ? `<details class="why"><summary>Why this match?</summary>
        <p class="sub small">${esc(E.why(top))}</p></details>` : ""}
      <div class="who-now"><span class="lbl">Who it goes to</span>${steps}
        <div class="note ${res.needs_admin ? "bad" : "info"} tight">${esc(E.resolutionSummary(res))}</div>
      </div>
      ${dupeBlock}
      ${draftBlock}`);
  }

  function renderSent(m) {
    if (m.data.withdrawn) return botWrap(`<p>Withdrawn — nothing was sent.</p>`);
    const r = E.request(S, m.data.id);
    if (!r) return botWrap(`<p>That request no longer exists.</p>`);
    const a = r.assignee_id ? person(r.assignee_id) : null;
    const proc = r.process_id ? E.process_(S, r.process_id) : null;
    const res = proc ? E.resolve(S, proc) : null;
    const owner = res && res.owner_id ? person(res.owner_id) : null;

    // Show the lookup, not just the outcome: finding the right person is the
    // work the user skipped by asking Atlas instead of guessing an address.
    let trail = "";
    if (m.data.auto && owner) {
      const lead = m.data.subject
        ? `Whoever owns <strong>${esc(m.data.subject)}</strong> is <strong>${esc(owner.name)}</strong>`
        : `<strong>${esc(owner.name)}</strong> owns that`;
      trail = `<p class="sub small">${lead}${
        res.rerouted && a && a.id !== owner.id
          ? ` — away until ${esc(E.fmtDate(owner.ooo_until))}, so it went to ${esc(a.name)}, their ${esc(res.assignee_role)}.`
          : `.`}</p>`;
    }

    const undo = E.canWithdraw(S, r.id, UI.actor)
      ? `<button class="btn sm" data-act="undo" data-id="${r.id}" data-mid="${m.id}">Undo</button>` : "";

    return botWrap(`
      <p>Sent. <strong>#${r.id}</strong> is with <strong>${esc(a ? a.name : "the Atlas admin")}</strong>.</p>
      ${trail}
      <div class="card flag tight">
        <div class="card-t">#${r.id} — ${esc(r.title)}</div>
        <div class="card-m">${statusBadge(r.status)}<span>${esc(proc ? proc.name : "Unmatched")}</span>
          <span class="mono">raised ${esc(human(now() - r.created_at))} ago</span></div>
      </div>
      <p class="sub small">I'll chase it if it isn't picked up in 48h.</p>
      <div class="acts">
        <button class="btn sm" data-act="open" data-id="${r.id}">Timeline</button>
        <button class="btn sm" data-act="adv" data-h="48">Skip 48h</button>
        ${undo}
      </div>`);
  }

  // Two readings of the same sentence. Name the person each would reach, so
  // the choice is about who gets it rather than what it is filed under.
  function renderChoose(m) {
    const rows = m.data.ids.map(id => E.process_(S, id)).filter(Boolean);
    return botWrap(`
      <p>${m.data.subject
        ? `More than one thing covers <strong>${esc(m.data.subject)}</strong>.`
        : `That could be a couple of things.`} Which do you mean?</p>
      <div class="stack tight">${rows.map(p => {
        const res = E.resolve(S, p);
        return `<button class="pickrow" data-act="chose" data-id="${p.id}"
          data-q="${esc(m.data.text || m.data.query)}">
          <span class="pickrow-t">${esc(p.name)}</span>
          <span class="pickrow-s">${esc(res.assignee_name || "no owner set")}</span></button>`;
      }).join("")}</div>`);
  }

  function renderOwners(m) {
    const proc = E.process_(S, m.data.processId);
    const at = now();
    const res = E.resolve(S, proc);
    const roleRow = role => {
      const list = E.holders(S, proc.id, role);
      if (!list.length) return `<div class="kv"><span class="k">${esc(role[0].toUpperCase() +
        role.slice(1))}</span><span class="muted">not configured</span></div>`;
      return `<div class="kv"><span class="k">${esc(role[0].toUpperCase() + role.slice(1))}</span>
        <span class="chips">${list.map(p => badge(p.name +
          (E.isOutOfOffice(p, at) ? " · away" : ""),
          E.isOutOfOffice(p, at) ? "ooo" : "role")).join(" ")}</span></div>`;
    };
    return botWrap(`
      <p><strong>${esc(proc.name)}</strong> — ${esc(proc.category)}</p>
      ${["owner", "approver", "delegate", "backup"].map(roleRow).join("")}
      <div class="note ${res.needs_admin ? "bad" : "info"} tight">
        ${esc(res.needs_admin ? res.steps[res.steps.length - 1].detail
          : "Right now it would go to " + res.assignee_name + ".")}</div>
      <div class="acts"><button class="btn sm" data-act="process" data-id="${proc.id}">
        Open the process</button></div>`);
  }

  function renderOoo(m) {
    const rows = m.data.ids.map(id => person(id)).filter(Boolean);
    return botWrap(`<p>${rows.length} ${rows.length === 1 ? "person is" : "people are"} out of office:</p>
      <div class="stack tight">${rows.map(p => {
        const covers = S.responsibilities.filter(r => r.person_id === p.id && r.role === "owner")
          .map(r => E.process_(S, r.process_id).name);
        return `<div class="card">
          <div class="card-t">${esc(p.name)} ${badge("back " + E.fmtDate(p.ooo_until), "ooo")}</div>
          <div class="card-m"><span>${esc(p.title)}</span>
            ${covers.length ? `<span>owns ${esc(covers.join(", "))}</span>` : ""}</div>
        </div>`;
      }).join("")}</div>
      `);
  }

  function renderReqList(m) {
    const rows = m.data.ids.map(id => E.request(S, id)).filter(Boolean);
    if (!rows.length) return botWrap(`<p>${esc(m.data.empty)}</p>`);
    return botWrap(`<p>${rows.length} request${rows.length === 1 ? "" : "s"}:</p>
      <div class="stack tight">${rows.slice(0, 8).map(r => {
        const other = m.data.mine ? r.assignee_id : r.requester_id;
        const op = other ? person(other) : null;
        return `<div class="rowline"><div class="card">
          <div class="card-t">#${r.id} — ${esc(r.title)}</div>
          <div class="card-m">${statusBadge(r.status)}
            <span>${m.data.mine ? "with" : "from"} ${esc(op ? op.name : "—")}</span>
            <span class="mono">${esc(human(now() - r.created_at))} old</span></div>
        </div><button class="btn sm" data-act="open" data-id="${r.id}">Open</button></div>`;
      }).join("")}</div>`);
  }

  function renderPersonMsg(m) {
    const p = person(m.data.id);
    if (!p) return botWrap(`<p>That person is no longer in the directory.</p>`);
    const at = now();
    const stats = E.personStats(S, p.id);
    const grouped = E.responsibilitiesOf(S, p.id);
    const mgr = p.manager_id ? person(p.manager_id) : null;
    const owns = (grouped.owner || []).map(x => x.name);
    return botWrap(`
      <p><strong>${esc(p.name)}</strong> — ${esc(p.title)}, ${esc(E.departmentName(S, p))}
        ${E.isOutOfOffice(p, at) ? badge("out of office", "ooo") : ""}</p>
      <div class="kv"><span class="k">Reports to</span>${esc(mgr ? mgr.name : "—")}</div>
      <div class="kv"><span class="k">Owns</span>${owns.length ?
        `<span class="chips">${owns.map(n => badge(n, "role")).join(" ")}</span>` :
        `<span class="muted">nothing directly</span>`}</div>
      <div class="kv"><span class="k">Open load</span>${stats.open_load} request(s)</div>
      <div class="acts"><button class="btn sm" data-act="treeperson" data-id="${p.id}">
        Show in the org chart</button></div>`);
  }

  function renderAskWho(m) {
    const p = person(m.data.id);
    if (!p) return botWrap(`<p>That person is no longer in the directory.</p>`);
    const owns = E.responsibilitiesOf(S, p.id).owner || [];
    const at = now();
    const away = E.isOutOfOffice(p, at);

    if (!owns.length) {
      return botWrap(`
        <p><strong>${esc(p.name)}</strong> doesn't own anything you can request directly.</p>
        <p class="sub small">Tell me what you need instead.</p>
        <div class="chips tight">${SUGGESTIONS.slice(0, 2).map(q =>
          `<button class="chip sm" data-act="say" data-text="${esc(q)}">${esc(q)}</button>`).join("")}</div>`);
    }

    return botWrap(`
      <p>What do you need from <strong>${esc(p.name)}</strong>?</p>
      ${away ? `<p class="sub small">Away until ${E.fmtDate(p.ooo_until)} — this may go
        to their cover.</p>` : ""}
      <div class="chips tight">${owns.map(proc =>
        `<button class="chip" data-act="askproc" data-id="${proc.id}"
          data-who="${p.id}">${esc(proc.name)}</button>`).join("")}</div>`);
  }

  function renderPick(m) {
    const opts = S.processes.slice().sort((a, b) => a.name.localeCompare(b.name));
    return botWrap(`<div class="picker">
      <label class="lbl" for="pk">Route it as</label>
      <select id="pk" class="field" data-act="pickproc" data-mid="${m.id}">
        <option value="">Choose a process…</option>
        ${opts.map(p => `<option value="${p.id}">${esc(p.name)} — ${esc(p.category)}</option>`).join("")}
      </select></div>`);
  }

  function renderMsg(m) {
    if (m.role === "user") return bubbleUser(m);
    switch (m.kind) {
      case "match":   return renderMatch(m);
      case "sent":    return renderSent(m);
      case "owners":  return renderOwners(m);
      case "ooo":     return renderOoo(m);
      case "reqlist": return renderReqList(m);
      case "person":  return renderPersonMsg(m);
      case "pick":    return renderPick(m);
      case "choose":  return renderChoose(m);
      case "askwho":  return renderAskWho(m);
      case "suggest":
        return `<div class="chips suggest">${m.data.items.map(s =>
          `<button class="chip" data-act="say" data-text="${esc(s)}">${esc(s)}</button>`).join("")}</div>`;
      default:
        return botWrap(m.data.text.split("\n").map(line =>
          line.trim() ? `<p>${esc(line)}</p>` : "").join(""));
    }
  }

  function pageChat() {
    return `<div class="chatpage">
      <div class="chatlog" id="chatlog">
        ${UI.chat.map(renderMsg).join("")}
      </div>
      <form class="composer" data-act="chatform">
        <label class="sr" for="composer">Message Atlas</label>
        <textarea id="composer" rows="1" placeholder="Tell Atlas what you need…"
          data-act="composer"></textarea>
        <button class="btn primary" type="submit" data-act="chatsubmit">Send</button>
      </form>
    </div>`;
  }
