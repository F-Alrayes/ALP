
  /* ================================ guide =============================== */

  // A real sequence, so numbering it is honest.
  const TOUR = [
    { t: "Ask in plain English",
      d: "\"Email whoever owns the data room and ask for access.\" No forms, no names." },
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
        // A worked example, not a live send: the trace and the editable draft
        // are the point, and nobody wants a tour button to fire a real request.
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
      case "sendcontact":
        sendToContact(el.dataset.q, id);
        return commit();
      case "chose":
        commitChoice(el.dataset.q, id);
        return commit();
      case "undo": {
        if (!E.withdrawRequest(S, id, UI.actor)) {
          pushMsg("bot", "text", { text:
            "Too late to pull that one back — it's already been picked up. Open it and add a note instead." });
          return commit();
        }
        const msg = UI.chat.find(m => m.id === Number(el.dataset.mid));
        if (msg) msg.data.withdrawn = true;
        if (UI.open === id) UI.open = null;
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
          UI.tree.zoom = fitZoom(box, svg);
          applyZoom();
          centreStage(box);
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

  // Fit against the stage's content box, and against both axes: fitting the
  // width alone leaves a chart that is still taller than the stage.
  function fitZoom(box, svg) {
    const vb = svg.viewBox.baseVal;
    const css = getComputedStyle(box);
    const padX = parseFloat(css.paddingLeft) + parseFloat(css.paddingRight);
    const padY = parseFloat(css.paddingTop) + parseFloat(css.paddingBottom);
    const w = (box.clientWidth - padX) / (vb.width || 1);
    const h = (box.clientHeight - padY) / (vb.height || 1);
    return clampZoom(Math.floor(Math.min(w, h, ZOOM_MAX) * 100) / 100);
  }

  // Whatever the stage cannot fit gets centred, not pinned to a corner.
  function centreStage(box) {
    box.scrollLeft = Math.max(0, (box.scrollWidth - box.clientWidth) / 2);
    box.scrollTop = Math.max(0, (box.scrollHeight - box.clientHeight) / 2);
  }

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
    // Velocity needs a short history, not the last event: the final move
    // before release is often a near-stationary settle.
    let hist = [];
    let glide = null;
    const stopGlide = () => { if (glide) { cancelAnimationFrame(glide); glide = null; } };

    box.addEventListener("pointerdown", ev => {
      stopGlide();                               // grabbing mid-glide takes over
      if (ev.target.closest("[data-act]") !== box && ev.target.closest("g[data-act]")) return;
      down = true; sx = ev.clientX; sy = ev.clientY; sl = box.scrollLeft; st2 = box.scrollTop;
      hist = [{ x: ev.clientX, y: ev.clientY, t: performance.now() }];
      // Capture keeps the drag alive outside the box — losing the chart the
      // moment the pointer crosses its edge reads as the app letting go.
      box.setPointerCapture(ev.pointerId);
      box.classList.add("grabbing");
    });

    box.addEventListener("pointermove", ev => {
      if (!down) return;
      box.scrollLeft = sl - (ev.clientX - sx);
      box.scrollTop = st2 - (ev.clientY - sy);
      const now = performance.now();
      hist.push({ x: ev.clientX, y: ev.clientY, t: now });
      while (hist.length > 2 && now - hist[0].t > 90) hist.shift();
    });

    const stop = () => {
      if (!down) return;
      down = false; box.classList.remove("grabbing");
      // Hand the release velocity to a decaying glide, so the seam between
      // dragging and coasting disappears. Exponential decay at ~0.998/ms is
      // the same feel as scroll deceleration.
      if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      const a = hist[0], b = hist[hist.length - 1];
      if (!a || !b || b.t - a.t < 10) return;
      let vx = -(b.x - a.x) / (b.t - a.t);       // px/ms, in scroll direction
      let vy = -(b.y - a.y) / (b.t - a.t);
      if (Math.hypot(vx, vy) < 0.08) return;     // a settle, not a flick
      let last = performance.now();
      const tick = () => {
        const now = performance.now(), dt = now - last; last = now;
        box.scrollLeft += vx * dt;
        box.scrollTop += vy * dt;
        const decay = Math.pow(0.998, dt);
        vx *= decay; vy *= decay;
        glide = Math.hypot(vx, vy) > 0.02 ? requestAnimationFrame(tick) : null;
      };
      glide = requestAnimationFrame(tick);
    };
    box.addEventListener("pointerup", stop);
    box.addEventListener("pointercancel", stop);

    box.addEventListener("wheel", ev => {
      stopGlide();
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
        <span class="hc-av" style="--d:${deptColor(E.departmentName(S, p))}">${
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

  /* --------------------- assignment notifications ---------------------- */
  // A toast the moment a request lands on the person you're acting as. It
  // lives in #notify, outside #root, so re-renders never kill an in-flight
  // gesture. All motion is one spring per card driven from the current
  // position and velocity, so a card can be grabbed mid-flight, thrown, or
  // released and it always continues from where it is.

  const CALM = matchMedia("(prefers-reduced-motion: reduce)");
  let notifSeen = null, notifActor = null;

  const assignedNow = () => new Set(S.requests
    .filter(r => E.OPEN_STATUSES.includes(r.status) && r.assignee_id === UI.actor)
    .map(r => r.id));

  function syncNotify() {
    const ids = assignedNow();
    if (notifActor !== UI.actor || notifSeen === null) {
      // Switching people (or booting) re-baselines silently: the toast is for
      // things that happen while you watch, not a recap of your inbox.
      notifActor = UI.actor;
      notifSeen = ids;
      return;
    }
    for (const id of ids) {
      if (notifSeen.has(id)) continue;
      const req = S.requests.find(r => r.id === id);
      if (req && req.requester_id !== UI.actor) showNotify(req);
    }
    notifSeen = ids;
  }

  function showNotify(req) {
    const host = document.getElementById("notify");
    if (!host) return;
    while (host.children.length >= 3) host.firstChild.remove();

    const from = person(req.requester_id);
    const card = document.createElement("div");
    card.className = "notif";
    card.setAttribute("role", "status");
    card.innerHTML = `
      <button class="n-x" aria-label="Dismiss">✕</button>
      <div class="n-eyebrow"><span class="dot"></span>New request for you</div>
      <div class="n-title">${esc(req.title)}</div>
      <div class="n-meta">#${req.id} · from ${esc(from ? from.name : "the agent")}${
        req.process_name ? ` · ${esc(req.process_name)}` : ""}</div>
      <div class="n-row">
        <button class="n-open" data-act="open" data-id="${req.id}">Open</button>
        <button class="n-later">Later</button>
      </div>`;
    host.appendChild(card);

    const width = card.getBoundingClientRect().width + 26;   // + the offscreen gap
    const m = { x: 0, v: 0, target: 0, raf: 0, gone: false };

    const apply = () => {
      card.style.transform = m.x ? `translateX(${m.x}px)` : "";
      card.style.opacity = m.gone ? String(Math.max(0, 1 - m.x / width)) : "";
    };

    // Critically damped spring (damping 1.0, response ~0.34s). No fixed
    // duration: retargeting mid-flight just changes `target` and the motion
    // stays continuous.
    function settleTo(target, gone) {
      cancelAnimationFrame(m.raf);
      m.target = target; m.gone = !!gone;
      let last = performance.now();
      const tickSpring = () => {
        m.raf = requestAnimationFrame(() => {
          const t = performance.now(), dt = Math.min(0.048, (t - last) / 1000);
          last = t;
          const w = 2 * Math.PI / 0.34;
          const acc = -w * w * (m.x - m.target) - 2 * w * m.v;
          m.v += acc * dt; m.x += m.v * dt;
          if (Math.abs(m.x - m.target) < 0.5 && Math.abs(m.v) < 25) {
            m.x = m.target; m.v = 0; apply();
            if (m.gone) card.remove();
          } else { apply(); tickSpring(); }
        });
      };
      tickSpring();
    }

    const dismiss = () => {
      if (m.gone) return;
      pause();
      if (CALM.matches) {
        card.style.transition = "opacity .18s ease";
        card.style.opacity = "0";
        m.gone = true;
        setTimeout(() => card.remove(), 200);
      } else {
        settleTo(width, true);
      }
    };

    // Auto-dismiss, but never under the pointer: hovering or holding the card
    // stops the clock; it resumes with whatever time was left.
    let timer = 0, left = 8000, mark = 0;
    const pause = () => {
      if (timer) { clearTimeout(timer); timer = 0; left -= performance.now() - mark; }
    };
    const resume = () => {
      if (!timer && !m.gone) {
        mark = performance.now();
        timer = setTimeout(dismiss, Math.max(1200, left));
      }
    };
    card.addEventListener("pointerenter", pause);
    card.addEventListener("pointerleave", resume);

    card.querySelector(".n-x").addEventListener("click", dismiss);
    card.querySelector(".n-later").addEventListener("click", dismiss);
    // "Open" also navigates via the global data-act dispatcher; the card only
    // needs to get out of the way.
    card.querySelector(".n-open").addEventListener("click", dismiss);

    // Direct manipulation: the card tracks the pointer 1:1 from wherever it
    // was grabbed — including mid-animation. Left of home it rubber-bands
    // (there is nothing over there); released, the projected resting point
    // decides between dismissal and spring-back, and the spring inherits the
    // finger's velocity so there is no seam.
    card.addEventListener("pointerdown", ev => {
      if (ev.target.closest("button")) return;
      card.setPointerCapture(ev.pointerId);
      cancelAnimationFrame(m.raf);
      pause();
      const grab = ev.clientX - m.x;
      let hist = [[performance.now(), m.x]];
      const move = e => {
        let x = e.clientX - grab;
        if (x < 0) x = (x * width * 0.55) / (width + 0.55 * Math.abs(x));
        m.x = x; apply();
        const t = performance.now();
        hist.push([t, x]);
        while (hist.length > 2 && hist[0][0] < t - 90) hist.shift();
      };
      const up = () => {
        card.removeEventListener("pointermove", move);
        const [t0, x0] = hist[0], [t1, x1] = hist[hist.length - 1];
        m.v = t1 > t0 ? (x1 - x0) / ((t1 - t0) / 1000) : 0;
        const projected = m.x + (m.v / 1000) * 0.998 / (1 - 0.998);
        if (projected > width * 0.5 && !CALM.matches) { m.gone = true; settleTo(width, true); }
        else { resume(); settleTo(0); }
      };
      card.addEventListener("pointermove", move);
      card.addEventListener("pointerup", up, { once: true });
      card.addEventListener("pointercancel", up, { once: true });
    });

    // Arrive from the right — the same edge a dismissal leaves by.
    if (CALM.matches) {
      card.style.opacity = "0";
      card.style.transition = "opacity .2s ease";
      requestAnimationFrame(() => { card.style.opacity = "1"; });
    } else {
      m.x = width; apply();
      settleTo(0);
    }
    resume();
  }

  // The chat log jumps to the newest message only when the conversation itself
  // grew (or on arrival) — never on the re-render that follows every unrelated
  // click. -1 means "not on the chat page".
  let chatLen = -1;

  function afterRender() {
    bindCharts();
    bindPan();
    bindHover();
    syncNotify();
    if (UI.page === "chat") {
      const log = document.getElementById("chatlog");
      if (log && chatLen !== UI.chat.length) log.scrollTop = log.scrollHeight;
      chatLen = UI.chat.length;
      const box = document.querySelector('[data-act="composer"]');
      if (box && !UI.guideOpen && !document.querySelector('[data-act="dbody"]:focus')) {
        box.focus({ preventScroll: true }); autoGrow(box);
      }
    } else {
      chatLen = -1;
    }
    if (UI.tree.center && UI.page === "people") {
      const box = document.getElementById("orgscroll");
      const svg = document.getElementById("treesvg");
      if (!box || !svg) {
        UI.tree.center = false;
      } else {
        const fit = fitZoom(box, svg);
        // Leave `center` set through the re-render. Clearing it here left the
        // chart correctly scaled and stuck against the left edge, because the
        // second pass never got to centre it.
        if (Math.abs(fit - UI.tree.zoom) > 0.02) { UI.tree.zoom = fit; save(); render(); return; }
        UI.tree.center = false;
        centreStage(box);
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

  // Scroll-edge: the topbar's divider only exists while content is under it.
  const edgeBar = () => {
    const bar = document.querySelector(".topbar");
    if (bar) bar.classList.toggle("edged", window.scrollY > 2);
  };
  window.addEventListener("scroll", edgeBar, { passive: true });

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
