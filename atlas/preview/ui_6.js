
  /* ================================ guide =============================== */

  // A real sequence, so numbering it is honest.
  const TOUR = [
    { t: "Ask in plain English",
      d: "Type what you need. Atlas works out which request type it is." },
    { t: "It finds who can actually act",
      d: "Owner away? It falls through to their delegate, and shows you why." },
    { t: "The agent chases for you",
      d: "Unanswered after 48h it chases, then hands over, then escalates." },
    { t: "Browse the whole firm",
      d: "People has every employee as an org chart you can search and request from." },
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
    const rows = TOUR.map((step, i) => `<div class="node ok">
      <div class="k">${i + 1}. ${esc(step.t)}</div><div class="d">${esc(step.d)}</div></div>`).join("");
    return phead("Guide", "How Atlas works", "") +
      `<div class="grid2">
        <div>
          <h2>The loop</h2>
          <div class="trail" style="margin-top:11px">${rows}</div>
          <div class="acts" style="margin-top:13px">
            <button class="btn primary" data-act="guidetry">Run the example</button>
            <button class="btn" data-act="guide">Replay the tour</button>
          </div>
        </div>
        <div>
          <h2>Try these</h2>
          <div class="chips tight" style="margin-top:11px">
            ${["I need access to the data room for Project Falcon",
               "Who owns invoice approval?",
               "Is anyone out of office?",
               "I need the quarterly NAV marks signed off"].map(q =>
              `<button class="chip" data-act="say" data-text="${esc(q)}">${esc(q)}</button>`).join("")}
          </div>
          <p class="muted" style="margin-top:11px">The last one has no delegate behind an
            absent owner.</p>

          <h2 style="margin-top:22px">What's real</h2>
          <p class="sub small" style="margin-top:9px">The routing, agent, matching and analytics
            are real code. The firm is invented. Nothing leaves your browser.</p>
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

  // Re-root the chart on someone and open on them at a readable size.
  function focusOn(personId) {
    UI.page = "people"; UI.tab.people = "org"; UI.process = null;
    UI.tree.root = personId;
    UI.tree.selected = personId;
    delete UI.tree.collapsed[personId];      // show their team, not a "+n" stub
    UI.tree.zoom = 1;
    UI.tree.center = false;
    UI.tree.focus = personId;
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
        UI.moreOpen = false; return commit();
      case "moretoggle": UI.moreOpen = !UI.moreOpen; return commit();
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
      case "askperson": {
        UI.page = "chat"; UI.draft = null; hideHover();
        const who = person(id);
        if (who) pushMsg("user", "text", { text: `I need something from ${who.name}.` });
        botAskWho(id);
        return commit();
      }
      case "askproc": {
        const proc = E.process_(S, id);
        if (!proc) return;
        pushMsg("user", "text", { text: proc.name });
        openDraft(`I need ${proc.name.toLowerCase()}`, proc.id);
        return commit();
      }
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
        const box = document.getElementById("orgscroll");
        if (!box) return;
        const step = Number(el.dataset.d) > 0 ? 1.15 : 1 / 1.15;
        zoomAt(UI.tree.zoom * step, box.clientWidth / 2, box.clientHeight / 2);
        return;
      }
      case "zoomfit": {
        const box = document.getElementById("orgscroll");
        const svg = document.getElementById("treesvg");
        if (box && svg) {
          const natural = svg.viewBox.baseVal.width || 1;
          UI.tree.zoom = clampZoom(Math.round(((box.clientWidth - 30) / natural) * 100) / 100);
          applyZoom();
          box.scrollLeft = (box.scrollWidth - box.clientWidth) / 2;
          box.scrollTop = 0;
          saveSoon();
        }
        return;
      }
      case "pickperson": {
        const picked = person(id);
        if (picked) UI.tree.query = picked.name;
        closeSuggest(); focusOn(id); return commit();
      }
      case "focusperson": focusOn(id); return commit();
      case "focusup": focusOn(id); return commit();
      case "focusclear":
        UI.tree.root = null; UI.tree.query = ""; UI.tree.selected = null;
        UI.tree.center = true; UI.tree.zoom = 0.85;
        return commit();
      case "expandall": UI.tree.collapsed = {}; UI.tree.center = true; return commit();
      case "collapseall": collapseToTeams(); UI.tree.center = true; return commit();
      default: return;
    }
  });

  // Clicking anywhere off the menu closes it.
  document.addEventListener("click", ev => {
    if (!UI.moreOpen) return;
    if (ev.target.closest(".morewrap")) return;
    UI.moreOpen = false;
    const menu = document.querySelector(".moremenu");
    if (menu) menu.remove();
    const btn = document.querySelector('[data-act="moretoggle"]');
    if (btn) btn.setAttribute("aria-expanded", "false");
    save();
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
      case "treequery": UI.tree.query = el.value; sugIndex = -1; renderSuggest(); return;
      default: return;
    }
    save();
  });

  let sugIndex = -1;

  function currentSuggestions() {
    const input = document.querySelector('[data-act="treequery"]');
    const q = input ? input.value.trim() : "";
    return q ? searchMatches(q).slice(0, 6) : [];
  }

  function renderSuggest() {
    const box = document.getElementById("suggestbox");
    const input = document.querySelector('[data-act="treequery"]');
    if (!box || !input) return;
    const matches = currentSuggestions();
    if (!matches.length) {
      box.hidden = true; box.innerHTML = "";
      input.setAttribute("aria-expanded", "false");
      return;
    }
    box.hidden = false;
    input.setAttribute("aria-expanded", "true");
    box.innerHTML = matches.map((p, i) => `
      <button class="sug${i === sugIndex ? " on" : ""}" role="option"
        aria-selected="${i === sugIndex}" data-act="pickperson" data-id="${p.id}">
        <span class="sug-n">${esc(p.name)}</span>
        <span class="sug-t">${esc(p.title)} · ${esc(E.departmentName(S, p))}</span>
      </button>`).join("");
  }

  function closeSuggest() {
    const box = document.getElementById("suggestbox");
    const input = document.querySelector('[data-act="treequery"]');
    sugIndex = -1;
    if (box) { box.hidden = true; box.innerHTML = ""; }
    if (input) input.setAttribute("aria-expanded", "false");
  }

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

  document.addEventListener("keydown", ev => {
    const combo = ev.target.closest('[data-act="treequery"]');
    if (!combo) return;
    const matches = currentSuggestions();
    if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
      if (!matches.length) return;
      ev.preventDefault();
      const step = ev.key === "ArrowDown" ? 1 : -1;
      sugIndex = sugIndex < 0
        ? (step > 0 ? 0 : matches.length - 1)
        : (sugIndex + step + matches.length) % matches.length;
      renderSuggest();
      return;
    }
    if (ev.key === "Enter") {
      ev.preventDefault();
      const pick = matches[sugIndex >= 0 ? sugIndex : 0];
      if (pick) { UI.tree.query = pick.name; focusOn(pick.id); closeSuggest(); commit(); }
      return;
    }
    if (ev.key === "Escape") { ev.preventDefault(); closeSuggest(); }
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

  const ZOOM_MIN = 0.3, ZOOM_MAX = 2;
  const clampZoom = z => Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, z));

  function applyZoom() {
    const svg = document.getElementById("treesvg");
    if (!svg || !svg.viewBox.baseVal) return;
    svg.style.width = Math.round(svg.viewBox.baseVal.width * UI.tree.zoom) + "px";
    svg.style.height = Math.round(svg.viewBox.baseVal.height * UI.tree.zoom) + "px";
    const label = document.querySelector(".zoomv");
    if (label) label.textContent = Math.round(UI.tree.zoom * 100) + "%";
  }

  // Zoom about a point so whatever is under the cursor stays under it.
  function zoomAt(next, px, py) {
    const box = document.getElementById("orgscroll");
    if (!box) return;
    const old = UI.tree.zoom;
    next = clampZoom(next);
    if (Math.abs(next - old) < 0.001) return;
    const cx = (box.scrollLeft + px) / old, cy = (box.scrollTop + py) / old;
    UI.tree.zoom = next;
    applyZoom();
    box.scrollLeft = cx * next - px;
    box.scrollTop = cy * next - py;
    saveSoon();
  }

  let saveTimer = null;
  function saveSoon() { clearTimeout(saveTimer); saveTimer = setTimeout(save, 400); }

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

    box.addEventListener("wheel", ev => {
      // The chart owns the wheel: this is a canvas, not a scrolling document.
      ev.preventDefault();
      const rect = box.getBoundingClientRect();
      const step = ev.deltaY < 0 ? 1.12 : 1 / 1.12;
      zoomAt(UI.tree.zoom * step, ev.clientX - rect.left, ev.clientY - rect.top);
    }, { passive: false });
  }

  /* ---------------------------- org hover card --------------------------- */
  /* Details on demand rather than crammed into every node, plus the pattern of
     lighting up the chain of command from the hovered person to the top. */

  let hoverTimer = null, hideTimer = null, hoveredId = null;

  function chainHighlight(personId) {
    const stage = document.getElementById("orgscroll");
    if (!stage) return;
    const chain = new Set(personId ? E.pathToRoot(S, personId) : []);
    stage.querySelectorAll(".onode").forEach(node => {
      const id = Number(node.dataset.node);
      node.classList.toggle("chain", chain.has(id));
      node.classList.toggle("faded", chain.size > 0 && !chain.has(id));
    });
  }

  function hoverCardHTML(p) {
    const at = now();
    const mgr = p.manager_id ? person(p.manager_id) : null;
    const reports = S.people.filter(x => x.manager_id === p.id).length;
    const owns = (E.responsibilitiesOf(S, p.id).owner || []).map(x => x.name);
    const load = S.requests.filter(r => r.assignee_id === p.id &&
      E.OPEN_STATUSES.includes(r.status)).length;
    const away = E.isOutOfOffice(p, at);
    return `<div class="hc-head">
        <span class="hc-av" style="background:${deptColor(E.departmentName(S, p))}">${
          esc(initials(p.name))}</span>
        <span><strong>${esc(p.name)}</strong><br><span class="sub">${esc(p.title)}</span></span>
      </div>
      <div class="chips tight">${badge(E.departmentName(S, p), "role")}
        ${away ? badge("Away until " + E.fmtDate(p.ooo_until), "ooo") : ""}
        ${load ? badge(load + " open", "gold") : ""}</div>
      <div class="kv"><span class="k">Reports to</span>${esc(mgr ? mgr.name : "Nobody")}</div>
      ${reports ? `<div class="kv"><span class="k">Team</span>${reports} direct report${
        reports === 1 ? "" : "s"}</div>` : ""}
      <div class="kv"><span class="k">Owns</span>${owns.length
        ? esc(owns.join(", ")) : `<span class="muted">nothing directly</span>`}</div>
      <div class="acts">
        <button class="btn primary sm" data-act="askperson" data-id="${p.id}">Ask them for something</button>
        <button class="btn sm" data-act="focusperson" data-id="${p.id}">Their team</button>
      </div>`;
  }

  function showHover(nodeEl, personId) {
    const card = document.getElementById("hovercard");
    const stage = document.querySelector(".orgstage");
    const p = person(personId);
    if (!card || !stage || !p) return;
    card.innerHTML = hoverCardHTML(p);
    card.hidden = false;
    // Scale 1:1 with the chart, so the card is always the same size relative to
    // the cards it describes rather than dwarfing them when zoomed out.
    const z = UI.tree.zoom;
    card.style.transform = `scale(${z})`;
    const nb = nodeEl.getBoundingClientRect(), sb = stage.getBoundingClientRect();
    const cb = card.getBoundingClientRect();
    // Prefer below-right of the node, flip when that would leave the stage.
    let left = nb.left - sb.left + nb.width / 2 - cb.width / 2;
    let top = nb.bottom - sb.top + 10 * z;
    left = Math.max(8, Math.min(left, sb.width - cb.width - 8));
    if (top + cb.height > sb.height - 8) top = nb.top - sb.top - cb.height - 10;
    card.style.left = Math.round(left) + "px";
    card.style.top = Math.round(Math.max(8, top)) + "px";
  }

  function hideHover() {
    const card = document.getElementById("hovercard");
    if (card) { card.hidden = true; card.innerHTML = ""; }
    hoveredId = null;
    chainHighlight(null);
  }

  function bindHover() {
    const stage = document.getElementById("orgscroll");
    const card = document.getElementById("hovercard");
    if (!stage || !card) return;

    stage.querySelectorAll('g[data-act="treeselect"]').forEach(node => {
      const id = Number(node.dataset.id);
      const enter = () => {
        clearTimeout(hideTimer); clearTimeout(hoverTimer);
        if (hoveredId === id) return;
        hoverTimer = setTimeout(() => {
          hoveredId = id;
          chainHighlight(id);
          showHover(node, id);
        }, 220);
      };
      const leave = () => {
        clearTimeout(hoverTimer);
        hideTimer = setTimeout(hideHover, 220);
      };
      node.addEventListener("mouseenter", enter);
      node.addEventListener("mouseleave", leave);
      node.addEventListener("focus", () => { hoveredId = id; chainHighlight(id); showHover(node, id); });
      node.addEventListener("blur", leave);
    });

    // Moving into the card keeps it open so its buttons are clickable.
    card.addEventListener("mouseenter", () => clearTimeout(hideTimer));
    card.addEventListener("mouseleave", () => { hideTimer = setTimeout(hideHover, 180); });
    stage.addEventListener("scroll", hideHover, { passive: true });
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
    bindHover();
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
