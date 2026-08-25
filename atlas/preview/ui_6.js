
  /* ================================ guide =============================== */

  // A real sequence, so numbering it is honest.
  const TOUR = [
    { t: "Ask for something in plain English",
      d: "Type what you need into the chat — “I need access to the data room for Project " +
         "Falcon”. Atlas works out which of the firm's 14 processes that is, and shows you " +
         "how confident it is and which words it matched on." },
    { t: "Watch it find the accountable person",
      d: "The org chart says who reports to whom. Atlas answers a harder question: who can " +
         "action this today. It checks the owner, notices they're out of office, and falls " +
         "through to their delegate — showing every step of the reasoning." },
    { t: "Let the agent chase it for you",
      d: "Once sent, nobody has to remember it. The agent chases after 48 hours, hands over " +
         "to a cover, then escalates to a manager. Use the clock buttons on the left to skip " +
         "forward and watch it happen in seconds instead of days." },
    { t: "Explore who does what",
      d: "The People tab has the whole firm as an interactive org chart — search anyone, fold " +
         "teams away, click a card to see what they own and who covers for them." },
  ];

  function guideOverlay() {
    const step = Math.max(0, Math.min(TOUR.length - 1, UI.guideStep));
    const s = TOUR[step];
    const dots = TOUR.map((_, i) => `<span class="dot${i === step ? " on" : ""}"></span>`).join("");
    const last = step === TOUR.length - 1;
    return `<div class="scrim" data-act="guideclose-bg">
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="gt">
        <div class="modal-head">
          <span class="eyebrow">Getting started · ${step + 1} of ${TOUR.length}</span>
          <button class="btn sm" data-act="guideclose" aria-label="Close the guide">✕</button>
        </div>
        <h2 id="gt">${esc(s.t)}</h2>
        <p>${esc(s.d)}</p>
        <div class="modal-foot">
          <div class="dots">${dots}</div>
          <div class="acts">
            ${step > 0 ? `<button class="btn" data-act="guideprev">Back</button>` : ""}
            ${last ? `<button class="btn primary" data-act="guidetry">Try the example</button>`
                   : `<button class="btn primary" data-act="guidenext">Next</button>`}
          </div>
        </div>
      </div></div>`;
  }

  function pageGuide() {
    const rows = TOUR.map((s, i) => `<div class="node ok">
      <div class="k">${i + 1}. ${esc(s.t)}</div><div class="d">${esc(s.d)}</div></div>`).join("");
    return phead("Guide", "How to drive Atlas",
      "Atlas turns a sentence into a routed, chased, escalated piece of work. Here is the " +
      "whole loop, and what every control on the left does.") +
      `<div class="grid2">
        <div>
          <h2>The loop</h2>
          <div class="trail" style="margin-top:11px">${rows}</div>
          <div class="acts" style="margin-top:13px">
            <button class="btn primary" data-act="guidetry">Run the example for me</button>
            <button class="btn" data-act="guide">Replay the tour</button>
          </div>
        </div>
        <div>
          <h2>The controls on the left</h2>
          <div style="margin-top:11px">
            <div class="kv"><span class="k">You are</span>Switches whose eyes you are seeing
              through. There is no login in a prototype — this replaces it, and lets you look at
              both sides of the same request.</div>
            <div class="kv"><span class="k">Simulated clock</span>Every timestamp in Atlas is read
              through one clock that you control. Advancing it makes the agent's 48-hour rules
              fire immediately, which is the only way to demo them.</div>
            <div class="kv"><span class="k">Out of office</span>Mark anyone away and the agent
              reroutes their live work to a delegate within a couple of seconds.</div>
            <div class="kv"><span class="k">Run agent now</span>Forces an evaluation instead of
              waiting for the next two-second tick.</div>
            <div class="kv"><span class="k">Reset &amp; reseed</span>Puts the firm back to its
              starting state. Yours only — nobody else sees your copy.</div>
          </div>

          <h2 style="margin-top:22px">What's real and what isn't</h2>
          <p class="sub" style="margin-top:9px">The routing, the agent, the matching and the
            analytics are real code. The firm is invented: 40 people, 5 departments and 14
            processes of seeded data. Nothing leaves your browser, and your changes are private
            to you.</p>

          <h2 style="margin-top:22px">Things worth trying</h2>
          <div class="chips tight" style="margin-top:9px">
            ${["I need access to the data room for Project Falcon",
               "Who owns invoice approval?",
               "Is anyone out of office?",
               "I need the quarterly NAV marks signed off",
               "Raise a purchase order for new laptops"].map(q =>
              `<button class="chip" data-act="say" data-text="${esc(q)}">${esc(q)}</button>`).join("")}
          </div>
          <p class="muted" style="margin-top:9px">The last two are deliberately awkward: one has
            no delegate behind an absent owner, the other is a process nobody owns.</p>
        </div>
      </div>`;
  }

  /* ============================ event wiring ============================ */

  function captureDraft() {
    const t = document.querySelector('[data-act="dtitle"]');
    const b = document.querySelector('[data-act="dbody"]');
    if (UI.draft && t) UI.draft.title = t.value;
    if (UI.draft && b) UI.draft.body = b.value;
  }

  function sendDraft() {
    captureDraft();
    if (!UI.draft) return;
    const { query, processId, title, body } = UI.draft;
    const proc = E.process_(S, processId);
    const res = E.resolve(S, proc);
    const r = E.createRequest(S, {
      requester_id: UI.actor, process_id: processId, assignee_id: res.assignee_id,
      title, body, resolution: res,
    });
    UI.draft = null;
    pushMsg("bot", "sent", { id: r.id });
  }

  function expandTo(personId) {
    for (const id of E.pathToRoot(S, personId)) delete UI.tree.collapsed[id];
    UI.tree.selected = personId;
  }

  function collapseToTeams() {
    UI.tree.collapsed = {};
    const roots = E.orgTree(S);
    const walk = (n, depth) => {
      if (depth >= 1 && n.children.length) UI.tree.collapsed[n.id] = true;
      n.children.forEach(c => walk(c, depth + 1));
    };
    roots.forEach(r => walk(r, 0));
  }

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
      case "reseed": reseed(true); return commit("Database reset and reseeded.");

      /* guide */
      case "guide": UI.guideOpen = true; UI.guideStep = 0; return commit();
      case "guidenext": UI.guideStep = Math.min(TOUR.length - 1, UI.guideStep + 1); return commit();
      case "guideprev": UI.guideStep = Math.max(0, UI.guideStep - 1); return commit();
      case "guideclose": case "guideclose-bg":
        if (act === "guideclose-bg" && ev.target !== el) return;
        UI.guideOpen = false; UI.guideSeen = true; return commit();
      case "guidetry":
        UI.guideOpen = false; UI.guideSeen = true; UI.page = "chat";
        submitChat("I need access to the data room for Project Falcon");
        return commit();

      /* chat */
      case "say": UI.page = "chat"; submitChat(el.dataset.text); return commit();
      case "chatsend": sendDraft(); return commit();
      case "chatcancel": UI.draft = null;
        pushMsg("bot", "text", { text: "Dropped it. Tell me what you need instead." });
        return commit();
      case "repick": {
        if (!UI.draft) return;
        pushMsg("bot", "pick", { query: UI.draft.query, options: [] });
        return commit();
      }
      case "switchproc": {
        if (!UI.draft) return;
        openDraft(UI.draft.query, id);
        return commit();
      }
      case "follow": {
        E.followExisting(S, id, UI.actor);
        UI.draft = null;
        pushMsg("bot", "text", { text: `Done — you're following #${id} instead of raising a duplicate.` });
        pushMsg("bot", "sent", { id });
        return commit();
      }

      /* requests */
      case "open": UI.page = "requests"; UI.open = id; return commit();
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

      /* people & tree */
      case "process": UI.page = "people"; UI.tab.people = "processes"; UI.process = id;
        return commit();
      case "backdir": UI.process = null; return commit();
      case "treetoggle":
        if (UI.tree.collapsed[id]) delete UI.tree.collapsed[id];
        else UI.tree.collapsed[id] = true;
        return commit();
      case "treeselect": UI.tree.selected = id; return commit();
      case "treeclose": UI.tree.selected = null; return commit();
      case "treeperson":
        UI.page = "people"; UI.tab.people = "org"; UI.process = null;
        expandTo(id); UI.tree.focus = id;
        return commit();
      case "zoom": {
        const d = Number(el.dataset.d);
        UI.tree.zoom = Math.max(0.4, Math.min(1.6,
          Math.round((UI.tree.zoom + d * 0.15) * 100) / 100));
        return commit();
      }
      case "zoomfit": {
        const box = document.getElementById("orgscroll");
        const svg = document.getElementById("treesvg");
        if (box && svg) {
          const natural = svg.viewBox.baseVal.width || 1;
          UI.tree.zoom = Math.max(0.4, Math.min(1.2,
            Math.round(((box.clientWidth - 24) / natural) * 100) / 100));
        }
        return commit();
      }
      case "expandall": UI.tree.collapsed = {}; UI.tree.center = true; return commit();
      case "collapseall": collapseToTeams(); UI.tree.center = true; return commit();
      default: return;
    }
  });

  document.addEventListener("change", ev => {
    const el = ev.target.closest("[data-act]");
    if (!el) return;
    switch (el.dataset.act) {
      case "actor": UI.actor = Number(el.value); UI.open = null; return commit();
      case "oooperson": UI.oooPerson = Number(el.value); return commit();
      case "logfilter": UI.filter = el.value; return commit();
      case "dept": UI.dept = el.value; return commit();
      case "treedept": UI.tree.dept = el.value; return commit();
      case "pickproc": {
        if (!el.value) return;
        const mid = Number(el.dataset.mid);
        const msg = UI.chat.find(m => m.id === mid);
        const query = (msg && msg.data.query) || "";
        openDraft(query, Number(el.value));
        return commit();
      }
      default: return;
    }
  });

  document.addEventListener("input", ev => {
    const el = ev.target.closest("[data-act]");
    if (!el) return;
    switch (el.dataset.act) {
      case "dtitle": if (UI.draft) UI.draft.title = el.value; break;
      case "dbody": if (UI.draft) UI.draft.body = el.value; break;
      case "note": UI.note = el.value; break;
      case "advh": UI.advH = el.value; break;
      case "oood": UI.oooDays = el.value; break;
      case "composer": autoGrow(el); return;
      case "search": UI.search = el.value; debounceRender(el, 220); break;
      case "treesearch": UI.tree.search = el.value; debounceRender(el, 240); break;
      default: return;
    }
    save();
  });

  let debTimer = null;
  function debounceRender(el, ms) {
    clearTimeout(debTimer);
    const act = el.dataset.act, pos = el.selectionStart;
    debTimer = setTimeout(() => {
      save(); render();
      const again = document.querySelector(`[data-act="${act}"]`);
      if (again) { again.focus(); try { again.setSelectionRange(pos, pos); } catch (e) {} }
    }, ms);
  }

  function autoGrow(el) {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }

  document.addEventListener("submit", ev => {
    const form = ev.target.closest('[data-act="chatform"]');
    if (!form) return;
    ev.preventDefault();
    const box = form.querySelector('[data-act="composer"]');
    const text = box ? box.value : "";
    if (!String(text).trim()) return;
    if (box) box.value = "";
    submitChat(text);
    commit();
  });

  // Enter sends, Shift+Enter makes a new line.
  document.addEventListener("keydown", ev => {
    const box = ev.target.closest('[data-act="composer"]');
    if (box && ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      const form = box.closest("form");
      if (form) form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event("submit"));
      return;
    }
    if (ev.key === "Escape" && UI.guideOpen) { UI.guideOpen = false; UI.guideSeen = true; commit(); }
    const node = ev.target.closest('[data-act="treeselect"], [data-act="treetoggle"]');
    if (node && (ev.key === "Enter" || ev.key === " ")) { ev.preventDefault(); node.click(); }
  });

  /* ------------------------------ pan & zoom ---------------------------- */

  function bindPan() {
    const box = document.getElementById("orgscroll");
    if (!box) return;
    let down = false, sx = 0, sy = 0, sl = 0, st2 = 0;
    box.addEventListener("pointerdown", ev => {
      if (ev.target.closest("[data-act]") !== box && ev.target.closest("g[data-act]")) return;
      down = true; sx = ev.clientX; sy = ev.clientY; sl = box.scrollLeft; st2 = box.scrollTop;
      box.classList.add("grabbing");
    });
    const stop = () => { down = false; box.classList.remove("grabbing"); };
    box.addEventListener("pointermove", ev => {
      if (!down) return;
      box.scrollLeft = sl - (ev.clientX - sx);
      box.scrollTop = st2 - (ev.clientY - sy);
    });
    box.addEventListener("pointerup", stop);
    box.addEventListener("pointerleave", stop);
  }

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

  function afterRender() {
    bindCharts();
    bindPan();
    if (UI.page === "chat") {
      const log = document.getElementById("chatlog");
      if (log) log.scrollTop = log.scrollHeight;
      const box = document.querySelector('[data-act="composer"]');
      if (box && !UI.guideOpen && !document.querySelector('[data-act="dbody"]:focus')) {
        box.focus(); autoGrow(box);
      }
    }
    if (UI.tree.center && UI.page === "people") {
      const box = document.getElementById("orgscroll");
      const svg = document.getElementById("treesvg");
      if (box && svg) {
        const natural = svg.viewBox.baseVal.width || 1;
        const fit = Math.max(0.4, Math.min(1, Math.round(((box.clientWidth - 30) / natural) * 100) / 100));
        UI.tree.center = false;
        if (Math.abs(fit - UI.tree.zoom) > 0.02) { UI.tree.zoom = fit; save(); render(); return; }
        box.scrollLeft = (box.scrollWidth - box.clientWidth) / 2;
        box.scrollTop = 0;
      }
    }
    if (UI.tree.focus) {
      const node = document.querySelector(`g[data-act="treeselect"][data-id="${UI.tree.focus}"]`);
      const box = document.getElementById("orgscroll");
      if (node && box) {
        const nb = node.getBoundingClientRect(), bb = box.getBoundingClientRect();
        box.scrollLeft += (nb.left - bb.left) - box.clientWidth / 2 + nb.width / 2;
        box.scrollTop += (nb.top - bb.top) - box.clientHeight / 2;
      }
      UI.tree.focus = null;
    }
  }

  /* -------------------------------- boot -------------------------------- */

  if (!load()) reseed(false);
  if (!E.person(S, UI.actor)) UI.actor = S.people[0].id;
  if (!UI.chat.length) greet();
  if (!UI.guideSeen) UI.guideOpen = true;
  render();

  setInterval(() => {
    const before = S.events.length;
    E.tick(S);
    if (S.events.length !== before) { save(); render(); } else { save(); }
  }, 2000);
})();
