
  /* ============================ event wiring ============================ */

  function val(sel) { const el = document.querySelector(sel); return el ? el.value : ""; }
  function captureDraft() {
    const t = document.querySelector('[data-act="title"]');
    const b = document.querySelector('[data-act="body"]');
    if (t) UI.title = t.value;
    if (b) UI.body = b.value;
  }
  function clearDraft() { UI.title = UI.body = null; }

  document.addEventListener("click", ev => {
    const el = ev.target.closest("[data-act]");
    if (!el) return;
    const act = el.dataset.act;
    const id = el.dataset.id ? Number(el.dataset.id) : null;

    switch (act) {
      case "page": UI.page = el.dataset.page; UI.open = UI.person = UI.process = null;
        return commit();
      case "subtab": UI.tab[el.dataset.group] = el.dataset.k;
        UI.person = UI.process = null; return commit();

      /* rail */
      case "adv": {
        E.advance(S, Number(el.dataset.h));
        const n = E.runUntilSettled(S);
        return commit(`Advanced ${el.dataset.h}h. The agent took ${n} action${n === 1 ? "" : "s"}.`);
      }
      case "advcustom": {
        const hrs = Math.max(1, Math.min(720, Number(UI.advH || 24)));
        E.advance(S, hrs);
        const n = E.runUntilSettled(S);
        return commit(`Advanced ${hrs}h. The agent took ${n} action${n === 1 ? "" : "s"}.`);
      }
      case "clockreset": E.resetClock(S); return commit("Simulated clock reset to real time.");
      case "ooo": {
        const target = person(UI.oooPerson) ||
          S.people.slice().sort((a, b) => a.name.localeCompare(b.name))[0];
        const isOoo = E.isOutOfOffice(target, now());
        const days = Math.max(1, Math.min(60, Number(UI.oooDays || 5)));
        E.setOoo(S, target.id, !isOoo, isOoo ? null : now() + days * 24 * HOUR);
        const n = E.runUntilSettled(S);
        return commit(`${target.name} is now ${isOoo ? "back in the office" : "out of office"}. ` +
          `The agent took ${n} action${n === 1 ? "" : "s"}.`);
      }
      case "tick": {
        const n = E.runUntilSettled(S);
        return commit(`Agent evaluated its rules and took ${n} action${n === 1 ? "" : "s"}.`);
      }
      case "reseed": reseed(); return commit("Database reset and reseeded.");

      /* intake */
      case "example": UI.query = EXAMPLES[Number(el.dataset.i)]; UI.override = null;
        clearDraft(); return commit();
      case "clear": UI.query = ""; UI.override = null; clearDraft(); return commit();
      case "send": {
        captureDraft();
        const query = (UI.query || "").trim();
        const matches = E.matchProcesses(S.processes, query, 3);
        const top = matches[0];
        const chosen = UI.override !== null && UI.override !== undefined ? UI.override
          : (top && top.confidence >= 25 ? top.process_id : S.processes[0].id);
        const proc = E.process_(S, chosen);
        const res = E.resolve(S, proc);
        const me = actor();
        const r = E.createRequest(S, {
          requester_id: UI.actor, process_id: chosen, assignee_id: res.assignee_id,
          title: UI.title !== null && UI.title !== undefined ? UI.title
                 : E.suggestTitle(query, proc ? proc.name : null),
          body: UI.body !== null && UI.body !== undefined ? UI.body
                : E.draftBody(me, proc, res, query),
          resolution: res,
        });
        UI.sent = r.id; clearDraft();
        return commit();
      }
      case "another": UI.sent = null; UI.query = ""; UI.override = null; clearDraft();
        return commit();
      case "follow": E.followExisting(S, id, UI.actor); UI.sent = id; clearDraft();
        return commit("Joined the existing request instead of raising a duplicate.");

      /* requests */
      case "open": UI.open = id; return commit();
      case "back": UI.open = null; return commit();
      case "ack": E.acknowledge(S, id, UI.actor); return commit("Acknowledged.");
      case "prog": E.startProgress(S, id, UI.actor); return commit("Moved to In progress.");
      case "done": E.complete(S, id, UI.actor, UI.note || ""); UI.note = "";
        return commit("Request completed.");
      case "sendnote": {
        const note = (UI.note || "").trim();
        if (!note) return;
        E.addNote(S, id, UI.actor, note); UI.note = "";
        return commit("Note sent.");
      }

      /* directory */
      case "person": UI.person = id; UI.process = null; return commit();
      case "process": UI.process = id; UI.person = null; return commit();
      case "backdir": UI.person = UI.process = null; return commit();
      default: return;
    }
  });

  document.addEventListener("change", ev => {
    const el = ev.target.closest("[data-act]");
    if (!el) return;
    switch (el.dataset.act) {
      case "actor": UI.actor = Number(el.value); UI.open = null; return commit();
      case "oooperson": UI.oooPerson = Number(el.value); return commit();
      case "override": UI.override = Number(el.value); clearDraft(); return commit();
      case "logfilter": UI.filter = el.value; return commit();
      case "dept": UI.dept = el.value; return commit();
      case "graphdept": UI.graphDept = el.value; return commit();
      default: return;
    }
  });

  // Text fields keep their value in UI state without a re-render per keystroke.
  document.addEventListener("input", ev => {
    const el = ev.target.closest("[data-act]");
    if (!el) return;
    switch (el.dataset.act) {
      case "query": UI.query = el.value; clearDraft(); break;
      case "title": UI.title = el.value; break;
      case "body": UI.body = el.value; break;
      case "note": UI.note = el.value; break;
      case "advh": UI.advH = el.value; break;
      case "oood": UI.oooDays = el.value; break;
      case "search": UI.search = el.value; break;
      default: return;
    }
    save();
  });

  // The intake query needs a render once the user pauses, so the trace updates.
  let queryTimer = null;
  document.addEventListener("input", ev => {
    const el = ev.target.closest('[data-act="query"], [data-act="search"]');
    if (!el) return;
    clearTimeout(queryTimer);
    const isSearch = el.dataset.act === "search";
    queryTimer = setTimeout(() => {
      const pos = el.selectionStart;
      render();
      const again = document.querySelector(`[data-act="${el.dataset.act}"]`);
      if (again) { again.focus(); try { again.setSelectionRange(pos, pos); } catch (e) {} }
    }, isSearch ? 220 : 420);
  });

  /* ------------------------------ tooltips ------------------------------ */

  const tipEl = () => document.getElementById("tip");
  function showTip(target, ev) {
    const el = tipEl();
    el.innerHTML = `<div class="tt">${esc(target.dataset.tip)}</div>
      <div>${esc(target.dataset.tipb || "")}</div>`;
    el.hidden = false;
    const r = el.getBoundingClientRect();
    const x = Math.min(window.innerWidth - r.width - 10, (ev.clientX || 0) + 14);
    const y = Math.max(8, (ev.clientY || 0) - r.height - 12);
    el.style.left = x + "px"; el.style.top = y + "px";
  }
  function bindCharts() {
    document.querySelectorAll("[data-tip]").forEach(node => {
      node.addEventListener("mousemove", ev => showTip(node, ev));
      node.addEventListener("mouseleave", () => { tipEl().hidden = true; });
      node.addEventListener("focus", ev => {
        const b = node.getBoundingClientRect();
        showTip(node, { clientX: b.left + b.width / 2, clientY: b.top + b.height });
      });
      node.addEventListener("blur", () => { tipEl().hidden = true; });
    });
  }

  /* -------------------------------- boot -------------------------------- */

  if (!load()) reseed();
  if (!E.person(S, UI.actor)) UI.actor = S.people[0].id;
  render();

  // The agent runs on its own, exactly as it does in the Python app.
  setInterval(() => {
    const before = S.events.length;
    E.tick(S);
    if (S.events.length !== before) { save(); render(); }
    else { save(); }
  }, 2000);
})();
