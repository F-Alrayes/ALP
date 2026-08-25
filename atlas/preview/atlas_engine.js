/* Atlas engine — a faithful port of the Python prototype's logic.
   Pure functions plus a small mutable store; no DOM access, so it can be
   unit-tested in Node against the Python implementation. */
(function (root) {
  "use strict";

  /* ---------------- rapidfuzz-compatible string similarity ---------------- */

  // Longest common subsequence length — the basis of the Indel distance that
  // rapidfuzz's ratio() normalises.
  function lcsLength(a, b) {
    const n = a.length, m = b.length;
    if (!n || !m) return 0;
    let prev = new Int32Array(m + 1), cur = new Int32Array(m + 1);
    for (let i = 1; i <= n; i++) {
      const ai = a.charCodeAt(i - 1);
      for (let j = 1; j <= m; j++) {
        cur[j] = ai === b.charCodeAt(j - 1)
          ? prev[j - 1] + 1
          : (cur[j - 1] > prev[j] ? cur[j - 1] : prev[j]);
      }
      const t = prev; prev = cur; cur = t; cur.fill(0);
    }
    return prev[m];
  }

  // fuzz.ratio: 100 * 2*LCS / (len1 + len2)
  function ratio(a, b) {
    if (!a.length && !b.length) return 100;
    if (!a.length || !b.length) return 0;
    return (200 * lcsLength(a, b)) / (a.length + b.length);
  }

  // fuzz.partial_ratio: best ratio of the shorter string against any window of
  // the longer one.
  function partialRatio(a, b) {
    let shorter = a, longer = b;
    if (a.length > b.length) { shorter = b; longer = a; }
    const sl = shorter.length, ll = longer.length;
    if (!sl || !ll) return 0;
    if (sl === ll) return ratio(shorter, longer);
    let best = 0;
    for (let start = 0; start + sl <= ll; start++) {
      const r = ratio(shorter, longer.substr(start, sl));
      if (r > best) best = r;
      if (best === 100) break;
    }
    // Ragged ends: also try windows that overhang either edge.
    for (let len = 1; len < sl; len++) {
      best = Math.max(best, ratio(shorter, longer.substr(0, len)),
                            ratio(shorter, longer.substr(ll - len, len)));
    }
    return best;
  }

  function splitTokens(s) { return s.split(/\s+/).filter(Boolean); }

  // fuzz.token_set_ratio
  function tokenSetRatio(a, b) {
    const t1 = Array.from(new Set(splitTokens(a))).sort();
    const t2 = Array.from(new Set(splitTokens(b))).sort();
    const set2 = new Set(t2), set1 = new Set(t1);
    const inter = t1.filter(t => set2.has(t));
    const d1 = t1.filter(t => !set2.has(t));
    const d2 = t2.filter(t => !set1.has(t));
    const si = inter.join(" ");
    const s1 = (si + " " + d1.join(" ")).trim();
    const s2 = (si + " " + d2.join(" ")).trim();
    if (!si) return ratio(s1, s2);
    return Math.max(ratio(si, s1), ratio(si, s2), ratio(s1, s2));
  }

  /* ------------------------------ matching ------------------------------- */

  const STOPWORDS = new Set(("a an and are as at be can could do does for from get getting give has " +
    "have help how i if in is it just like me my need needs of on or our please so someone that the " +
    "their there this to up want was we what when which who will with would you your").split(" "));

  const TOKEN_RE = /[a-z0-9]+/g;

  function tokenize(text) {
    const out = [];
    const matches = String(text || "").toLowerCase().match(TOKEN_RE) || [];
    for (const t of matches) if (!STOPWORDS.has(t) && t.length > 1) out.push(t);
    return out;
  }

  const WEIGHTS = { keywords: 0.45, name: 0.20, tfidf: 0.25, description: 0.10 };

  function tf(tokens) {
    const counts = new Map();
    for (const t of tokens) counts.set(t, (counts.get(t) || 0) + 1);
    const total = tokens.length || 1;
    const out = new Map();
    for (const [k, v] of counts) out.set(k, v / total);
    return out;
  }

  function cosine(a, b) {
    if (!a.size || !b.size) return 0;
    let dot = 0, na = 0, nb = 0;
    for (const [k, v] of a) { na += v * v; const w = b.get(k); if (w !== undefined) dot += v * w; }
    for (const v of b.values()) nb += v * v;
    if (!na || !nb) return 0;
    return dot / (Math.sqrt(na) * Math.sqrt(nb));
  }

  function wordMatches(word, queryTokens) {
    for (const token of queryTokens) {
      if (token === word) return true;
      if (ratio(word, token) >= 88) return true;
      const shorter = word.length <= token.length ? word : token;
      const longer = word.length <= token.length ? token : word;
      if (shorter.length >= 4 && longer.startsWith(shorter)) return true;
    }
    return false;
  }

  function keywordHits(query, queryTokens, keywords) {
    const lowered = query.toLowerCase();
    const hits = [], seen = new Set();
    for (const keyword of keywords) {
      const kw = keyword.trim().toLowerCase();
      if (!kw) continue;
      let hit = false;
      if (lowered.includes(kw)) {
        hit = true;
      } else {
        const words = (kw.match(TOKEN_RE) || []).filter(w => w.length > 1);
        if (!words.length) continue;
        if (words.length > 1) {
          if (partialRatio(kw, lowered) >= 92) hit = true;
          else {
            let covered = 0;
            for (const w of words) if (wordMatches(w, queryTokens)) covered++;
            if (covered / words.length >= 0.75) hit = true;
          }
        } else if (wordMatches(words[0], queryTokens)) {
          hit = true;
        }
      }
      if (hit && !seen.has(kw)) { seen.add(kw); hits.push(keyword); }
    }
    return hits;
  }

  function keywordList(process) {
    return (process.keywords || "").split(",").map(k => k.trim().toLowerCase()).filter(Boolean);
  }

  function corpusFor(p) {
    return [p.name, p.category || "", p.keywords || "", p.description || ""].join(" ");
  }

  function confidenceLabel(c) {
    if (c >= 70) return "High confidence";
    if (c >= 45) return "Likely";
    if (c >= 25) return "Weak";
    return "No usable match";
  }

  function matchProcesses(processes, query, limit) {
    limit = limit || 3;
    query = String(query || "").trim();
    const ordered = processes.slice().sort((a, b) => a.name.localeCompare(b.name));
    if (!query || !ordered.length) return [];

    const queryTokens = tokenize(query);
    const queryTf = tf(queryTokens);

    const docTokens = new Map();
    for (const p of ordered) docTokens.set(p.id, tokenize(corpusFor(p)));
    const docCount = ordered.length;
    const df = new Map();
    for (const tokens of docTokens.values())
      for (const t of new Set(tokens)) df.set(t, (df.get(t) || 0) + 1);
    const idf = new Map();
    for (const [t, n] of df) idf.set(t, Math.log((1 + docCount) / (1 + n)) + 1);

    const queryVec = new Map();
    for (const [t, v] of queryTf) queryVec.set(t, v * (idf.get(t) === undefined ? 1 : idf.get(t)));

    const lowerQuery = query.toLowerCase();
    const matches = ordered.map(process => {
      const hits = keywordHits(query, queryTokens, keywordList(process));
      const keywordScore = hits.length ? Math.min(1, hits.length / 3) : 0;
      const nameScore = tokenSetRatio(lowerQuery, process.name.toLowerCase()) / 100;
      const descScore = tokenSetRatio(lowerQuery, (process.description || "").toLowerCase()) / 100;

      const docTf = tf(docTokens.get(process.id));
      const docVec = new Map();
      for (const [t, v] of docTf) docVec.set(t, v * (idf.get(t) === undefined ? 1 : idf.get(t)));
      const tfidfScore = cosine(queryVec, docVec);

      const signals = { keywords: keywordScore, name: nameScore, tfidf: tfidfScore, description: descScore };
      let raw = 0;
      for (const k of Object.keys(WEIGHTS)) raw += WEIGHTS[k] * signals[k];
      const confidence = Math.max(0, Math.min(100, ((raw - 0.12) / 0.72) * 100));

      return {
        process_id: process.id, process_name: process.name,
        category: process.category || "General",
        confidence: Math.round(confidence * 10) / 10,
        matched_keywords: hits, signals,
        confidence_label: confidenceLabel(confidence),
      };
    });

    matches.sort((a, b) =>
      b.confidence - a.confidence || b.matched_keywords.length - a.matched_keywords.length);
    return matches.slice(0, limit);
  }

  function why(match) {
    const bits = [];
    if (match.matched_keywords.length) {
      const shown = match.matched_keywords.slice(0, 4).map(k => `'${k}'`).join(", ");
      bits.push(`matched ${match.matched_keywords.length} keyword(s): ${shown}`);
    }
    if (match.signals.name >= 0.5) bits.push(`process name similarity ${Math.round(match.signals.name * 100)}%`);
    if (match.signals.tfidf >= 0.15) bits.push(`term-overlap score ${Math.round(match.signals.tfidf * 100)}%`);
    if (match.signals.description >= 0.5) bits.push(`description similarity ${Math.round(match.signals.description * 100)}%`);
    if (!bits.length) return "Nothing in the request text lined up with a known process.";
    const joined = bits.join("; ");
    return joined.charAt(0).toUpperCase() + joined.slice(1) + ".";
  }

  root.AtlasFuzz = { ratio, partialRatio, tokenSetRatio, tokenize };
  root.AtlasMatch = { matchProcesses, why, keywordList, confidenceLabel };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { ...root.AtlasFuzz, ...root.AtlasMatch };
  }
})(typeof globalThis !== "undefined" ? globalThis : this);

/* ==================== state, clock, routing, agent, analytics ============= */
(function (root) {
  "use strict";
  const HOUR = 3600000;
  const OPEN_STATUSES = ["pending", "acknowledged", "in_progress", "escalated"];
  const STATUS_LABELS = {
    pending: "Pending", acknowledged: "Acknowledged", in_progress: "In progress",
    completed: "Completed", escalated: "Escalated",
  };
  const AGENT_ACTOR = "atlas-agent";

  /* ------------------------------- state -------------------------------- */

  function hydrate(seed, baseMs) {
    const abs = h => (h === null || h === undefined) ? null : Math.round(baseMs + h * HOUR);
    const st = {
      base: baseMs,
      clockOffsetMs: 0,
      departments: seed.departments.map(d => ({ ...d })),
      people: seed.people.map(p => ({ ...p, ooo_until: abs(p.ooo_until) })),
      processes: seed.processes.map(p => ({ ...p })),
      responsibilities: seed.responsibilities.map(r => ({ ...r })),
      requests: seed.requests.map(r => ({
        ...r,
        created_at: abs(r.created_at), updated_at: abs(r.updated_at),
        last_action_at: abs(r.last_action_at), acknowledged_at: abs(r.acknowledged_at),
        completed_at: abs(r.completed_at),
      })),
      messages: seed.messages.map(m => ({ ...m, created_at: abs(m.created_at) })),
      events: seed.events.map(e => ({ ...e, created_at: abs(e.created_at) })),
      settings: { ...seed.settings },
    };
    st.nextId = {
      request: Math.max(0, ...st.requests.map(r => r.id)) + 1,
      message: Math.max(0, ...st.messages.map(m => m.id)) + 1,
      event: Math.max(0, ...st.events.map(e => e.id)) + 1,
    };
    return st;
  }

  const byId = (list, id) => list.find(x => x.id === id) || null;
  const person = (st, id) => byId(st.people, id);
  const process_ = (st, id) => byId(st.processes, id);
  const request = (st, id) => byId(st.requests, id);
  const department = (st, id) => byId(st.departments, id);

  /* ------------------------------- clock -------------------------------- */

  function now(st) { return Date.now() + st.clockOffsetMs; }
  function advance(st, hours) { st.clockOffsetMs += hours * HOUR; return now(st); }
  function resetClock(st) { st.clockOffsetMs = 0; return now(st); }
  function offsetHours(st) { return Math.round((st.clockOffsetMs / HOUR) * 100) / 100; }

  /* ------------------------------ routing ------------------------------- */

  function isOutOfOffice(p, at) {
    if (!p || !p.is_ooo) return false;
    if (p.ooo_until === null || p.ooo_until === undefined) return true;
    return p.ooo_until >= at;
  }

  function holders(st, processId, role) {
    return st.responsibilities
      .filter(r => r.process_id === processId && r.role === role)
      .map(r => person(st, r.person_id))
      .filter(Boolean);
  }

  function firstHolder(st, processId, role) {
    const list = holders(st, processId, role);
    return list.length ? list[0] : null;
  }

  function fmtDate(ms) {
    if (ms === null || ms === undefined) return "—";
    const d = new Date(ms);
    const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    return `${String(d.getDate()).padStart(2,"0")} ${months[d.getMonth()]} ${d.getFullYear()}`;
  }

  function resolve(st, proc, at) {
    if (at === undefined) at = now(st);
    if (!proc) {
      return {
        process_id: null, process_name: "Unmatched request", assignee_id: null,
        assignee_name: null, assignee_role: null, owner_id: null, owner_name: null,
        rerouted: false, needs_admin: true,
        steps: [{ label: "Process match", outcome: "fail",
          detail: "The request text did not match a known process, so no owner could be looked up." }],
      };
    }
    const res = {
      process_id: proc.id, process_name: proc.name, assignee_id: null, assignee_name: null,
      assignee_role: null, owner_id: null, owner_name: null, rerouted: false,
      needs_admin: false, steps: [],
    };
    res.steps.push({ label: "Process match", outcome: "ok",
      detail: `Resolved to '${proc.name}' (${proc.category}).` });

    const owner = firstHolder(st, proc.id, "owner");
    if (!owner) {
      res.needs_admin = true;
      res.steps.push({ label: "Owner lookup", outcome: "fail",
        detail: `'${proc.name}' is an orphan process — no owner edge exists in the responsibility ` +
                `graph. Flagged for the Atlas admin to assign an owner.` });
      return res;
    }
    res.owner_id = owner.id; res.owner_name = owner.name;
    res.steps.push({ label: "Owner lookup", outcome: "ok",
      detail: `${owner.name} (${owner.title}) owns this process.`,
      person_id: owner.id, person_name: owner.name });

    if (!isOutOfOffice(owner, at)) {
      res.steps.push({ label: "Availability check", outcome: "ok",
        detail: `${owner.name} is available.`, person_id: owner.id, person_name: owner.name });
      res.assignee_id = owner.id; res.assignee_name = owner.name; res.assignee_role = "owner";
      return res;
    }

    res.rerouted = true;
    res.steps.push({ label: "Availability check", outcome: "warn",
      detail: `${owner.name} is out of office until ${fmtDate(owner.ooo_until)}. ` +
              `Applying out-of-office failover.`,
      person_id: owner.id, person_name: owner.name });

    for (const role of ["delegate", "backup"]) {
      const cap = role.charAt(0).toUpperCase() + role.slice(1);
      const candidate = firstHolder(st, proc.id, role);
      if (!candidate) {
        res.steps.push({ label: `${cap} lookup`, outcome: "warn",
          detail: `No ${role} is configured for '${proc.name}'.` });
        continue;
      }
      if (isOutOfOffice(candidate, at)) {
        res.steps.push({ label: `${cap} lookup`, outcome: "warn",
          detail: `${candidate.name} is the configured ${role} but is also out of office ` +
                  `until ${fmtDate(candidate.ooo_until)}.`,
          person_id: candidate.id, person_name: candidate.name });
        continue;
      }
      res.steps.push({ label: `${cap} lookup`, outcome: "ok",
        detail: `${candidate.name} (${candidate.title}) is the configured ${role} and is available.`,
        person_id: candidate.id, person_name: candidate.name });
      res.assignee_id = candidate.id; res.assignee_name = candidate.name; res.assignee_role = role;
      return res;
    }

    const manager = owner.manager_id ? person(st, owner.manager_id) : null;
    if (manager && !isOutOfOffice(manager, at)) {
      res.steps.push({ label: "Manager fallback", outcome: "warn",
        detail: `No available delegate or backup. Routing to ${owner.name}'s manager, ` +
                `${manager.name} (${manager.title}). This process is a single point of failure.`,
        person_id: manager.id, person_name: manager.name });
      res.assignee_id = manager.id; res.assignee_name = manager.name; res.assignee_role = "manager";
      return res;
    }

    res.needs_admin = true;
    res.steps.push({ label: "Escalation", outcome: "fail",
      detail: `Owner, delegate, backup and manager are all unavailable for '${proc.name}'. ` +
              `Flagged for the Atlas admin.` });
    return res;
  }

  function resolutionSummary(res) {
    if (res.needs_admin) return `No owner configured for '${res.process_name}' — flagged for the Atlas admin.`;
    if (res.rerouted) return `${res.owner_name} is out of office; routed to ${res.assignee_name} as ${res.assignee_role}.`;
    return `Routed to ${res.assignee_name}, the accountable owner of '${res.process_name}'.`;
  }

  function coverFor(st, processId, personId, at) {
    for (const role of ["delegate", "backup"]) {
      for (const candidate of holders(st, processId, role)) {
        if (candidate.id === personId) continue;
        if (!isOutOfOffice(candidate, at)) return candidate;
      }
    }
    return null;
  }

  root.AtlasCore = {
    HOUR, OPEN_STATUSES, STATUS_LABELS, AGENT_ACTOR,
    hydrate, person, process_, request, department, byId,
    now, advance, resetClock, offsetHours,
    isOutOfOffice, holders, firstHolder, resolve, resolutionSummary, coverFor, fmtDate,
  };
  if (typeof module !== "undefined" && module.exports) Object.assign(module.exports, root.AtlasCore);
})(typeof globalThis !== "undefined" ? globalThis : this);

/* ======================= services, agent rules, analytics ================= */
(function (root) {
  "use strict";
  const C = root.AtlasCore;
  const { HOUR, OPEN_STATUSES, AGENT_ACTOR } = C;

  const hoursSince = (at, ref) => (at - ref) / HOUR;

  function logEvent(st, requestId, type, detail, at, actor) {
    const ev = { id: st.nextId.event++, request_id: requestId, type, detail,
                 actor: actor || "system", created_at: at };
    st.events.push(ev);
    return ev;
  }

  function sendMessage(st, o) {
    const msg = { id: st.nextId.message++, request_id: o.request_id, sender_id: o.sender_id,
                  recipient_id: o.recipient_id, type: o.type, body: o.body,
                  created_at: o.at, read: false };
    st.messages.push(msg);
    return msg;
  }

  function touch(req, at) { req.updated_at = at; req.last_action_at = at; }

  /* ------------------------------ drafting ------------------------------ */

  function draftBody(requester, proc, res, query) {
    const target = res.assignee_name || "the Atlas admin";
    const processName = proc ? proc.name : "an unmatched request";
    const lines = [
      `Hi ${res.assignee_name ? target.split(" ")[0] : "there"},`, "",
      `${requester.name} (${requester.title}) has raised a request under ${processName}:`, "",
      `    ${String(query).trim()}`, "",
    ];
    if (res.rerouted && res.owner_name) {
      lines.push(`You are receiving this because ${res.owner_name} is out of office and you are ` +
                 `the configured ${res.assignee_role} for this process.`);
      lines.push("");
    }
    lines.push("Atlas will chase this automatically if it is not acknowledged.");
    return lines.join("\n");
  }

  function suggestTitle(query, processName) {
    const text = String(query || "").split(/\s+/).filter(Boolean).join(" ");
    if (!text) return processName || "New request";
    if (text.length <= 70) return text.replace(/[.!?]+$/, "");
    return text.slice(0, 67).replace(/\s+\S*$/, "") + "...";
  }

  function findSimilarOpen(st, o) {
    if (o.process_id === null || o.process_id === undefined) return [];
    const threshold = 62;
    const rows = st.requests
      .filter(r => r.process_id === o.process_id && OPEN_STATUSES.includes(r.status))
      .sort((a, b) => b.created_at - a.created_at);
    const out = [];
    for (const row of rows) {
      let similarity = root.AtlasFuzz.tokenSetRatio(
        String(o.title || "").toLowerCase(), String(row.title || "").toLowerCase());
      let reason;
      if (row.requester_id === o.requester_id) {
        reason = "You already have an open request on this process.";
        similarity = Math.max(similarity, threshold);
      } else if (similarity >= threshold) {
        reason = "An open request with very similar wording is already in flight.";
      } else continue;
      out.push({ request: row, similarity: Math.round(similarity * 10) / 10, reason });
    }
    out.sort((a, b) => b.similarity - a.similarity);
    return out.slice(0, 3);
  }

  /* ------------------------------ lifecycle ----------------------------- */

  function createRequest(st, o) {
    const at = C.now(st);
    const requester = C.person(st, o.requester_id);
    const req = {
      id: st.nextId.request++, requester_id: o.requester_id, process_id: o.process_id,
      assignee_id: o.assignee_id, original_assignee_id: o.assignee_id,
      title: (o.title || "").trim() || "New request", body: o.body, status: "pending",
      created_at: at, updated_at: at, last_action_at: at, chase_count: 0,
      acknowledged_at: null, completed_at: null,
    };
    st.requests.push(req);

    const processName = o.resolution ? o.resolution.process_name : "an unmatched request";
    logEvent(st, req.id, "created",
      `${requester.name} raised a request under '${processName}'.`, at, requester.name);

    if (o.resolution) {
      for (const step of o.resolution.steps)
        logEvent(st, req.id, "routing", `${step.label}: ${step.detail}`, at, "router");
    }

    if (o.assignee_id === null || o.assignee_id === undefined) {
      logEvent(st, req.id, "orphan",
        "No accountable person could be resolved. Request is parked for the Atlas admin.", at);
    } else {
      const assignee = C.person(st, o.assignee_id);
      logEvent(st, req.id, "dispatch", `Dispatched to ${assignee.name} (${assignee.title}).`, at);
      sendMessage(st, { request_id: req.id, sender_id: o.requester_id,
        recipient_id: o.assignee_id, type: "dispatch", body: o.body, at });
    }
    return req;
  }

  function notifyRequester(st, req, body, at) {
    sendMessage(st, { request_id: req.id, sender_id: req.assignee_id,
      recipient_id: req.requester_id, type: "status_update", body, at });
  }

  function acknowledge(st, requestId, actorId) {
    const at = C.now(st), req = C.request(st, requestId), actor = C.person(st, actorId);
    if (req.status === "completed") return req;
    if (req.acknowledged_at === null) req.acknowledged_at = at;
    req.status = "acknowledged"; touch(req, at);
    logEvent(st, req.id, "acknowledged", `${actor.name} acknowledged the request.`, at, actor.name);
    notifyRequester(st, req, `${actor.name} has acknowledged '${req.title}'.`, at);
    return req;
  }

  function startProgress(st, requestId, actorId) {
    const at = C.now(st), req = C.request(st, requestId), actor = C.person(st, actorId);
    if (req.status === "completed") return req;
    if (req.acknowledged_at === null) req.acknowledged_at = at;
    req.status = "in_progress"; touch(req, at);
    logEvent(st, req.id, "status_update",
      `${actor.name} moved the request to In progress.`, at, actor.name);
    notifyRequester(st, req, `${actor.name} is working on '${req.title}'.`, at);
    return req;
  }

  function complete(st, requestId, actorId, note) {
    const at = C.now(st), req = C.request(st, requestId), actor = C.person(st, actorId);
    if (req.status === "completed") return req;
    if (req.acknowledged_at === null) req.acknowledged_at = at;
    req.status = "completed"; req.completed_at = at; touch(req, at);
    let detail = `${actor.name} completed the request.`;
    if (note && note.trim()) detail += ` Note: ${note.trim()}`;
    logEvent(st, req.id, "completed", detail, at, actor.name);
    let body = `'${req.title}' has been completed by ${actor.name}.`;
    if (note && note.trim()) body += `\n\n${note.trim()}`;
    notifyRequester(st, req, body, at);
    return req;
  }

  function addNote(st, requestId, actorId, note) {
    const at = C.now(st), req = C.request(st, requestId), actor = C.person(st, actorId);
    logEvent(st, req.id, "note", `${actor.name}: ${note.trim()}`, at, actor.name);
    const recipientId = actorId === req.assignee_id ? req.requester_id : req.assignee_id;
    if (recipientId) sendMessage(st, { request_id: req.id, sender_id: actorId,
      recipient_id: recipientId, type: "status_update", body: note.trim(), at });
    touch(req, at);
    return req;
  }

  function followExisting(st, requestId, followerId) {
    const at = C.now(st), req = C.request(st, requestId), follower = C.person(st, followerId);
    logEvent(st, req.id, "follow",
      `${follower.name} joined this request instead of raising a duplicate.`, at, follower.name);
    if (req.assignee_id) sendMessage(st, { request_id: req.id, sender_id: followerId,
      recipient_id: req.assignee_id, type: "status_update",
      body: `${follower.name} is also waiting on this request.`, at });
    touch(req, at);
    return req;
  }

  function reassign(st, requestId, actorId, newAssigneeId, reason) {
    const at = C.now(st), req = C.request(st, requestId), actor = C.person(st, actorId);
    const newAssignee = C.person(st, newAssigneeId);
    const previous = req.assignee_id ? C.person(st, req.assignee_id) : null;
    req.assignee_id = newAssigneeId;
    if (req.status === "escalated") req.status = "pending";
    touch(req, at);
    let detail = `${actor.name} reassigned the request ` +
      `${previous ? "from " + previous.name + " " : ""}to ${newAssignee.name}.`;
    if (reason && reason.trim()) detail += ` Reason: ${reason.trim()}`;
    logEvent(st, req.id, "reroute", detail, at, actor.name);
    sendMessage(st, { request_id: req.id, sender_id: actorId, recipient_id: newAssigneeId,
      type: "reroute",
      body: `'${req.title}' has been reassigned to you by ${actor.name}. ${(reason||"").trim()}`.trim(), at });
    return req;
  }

  function markRead(st, personId, requestId) {
    let n = 0;
    for (const m of st.messages) {
      if (m.recipient_id !== personId || m.read) continue;
      if (requestId !== undefined && requestId !== null && m.request_id !== requestId) continue;
      m.read = true; n++;
    }
    return n;
  }

  function setOoo(st, personId, isOoo, untilMs) {
    const p = C.person(st, personId);
    if (!p) return;
    const at = C.now(st);
    p.is_ooo = isOoo;
    p.ooo_until = isOoo ? untilMs : null;
    logEvent(st, null, "ooo_change",
      `${p.name} marked ${isOoo ? "out of office" : "back in the office"}` +
      (isOoo && untilMs ? ` until ${C.fmtDate(untilMs)}.` : "."), at, "demo");
  }

  /* -------------------------------- agent ------------------------------- */

  function hasEvent(st, requestId, type) {
    return st.events.some(e => e.request_id === requestId && e.type === type);
  }

  function ruleOooReroute(st, req, at) {
    const assignee = req.assignee_id ? C.person(st, req.assignee_id) : null;
    if (!assignee || !C.isOutOfOffice(assignee, at)) return 0;
    if (req.process_id === null || req.process_id === undefined) return 0;

    const cover = C.coverFor(st, req.process_id, assignee.id, at);
    const proc = C.process_(st, req.process_id);
    if (!cover) {
      if (!hasEvent(st, req.id, "ooo_no_cover")) {
        logEvent(st, req.id, "ooo_no_cover",
          `${assignee.name} is out of office until ${C.fmtDate(assignee.ooo_until)} ` +
          `and no available delegate or backup is configured for ` +
          `'${proc ? proc.name : "this process"}'. ` +
          `The request stays with them and will be chased.`, at, AGENT_ACTOR);
        return 1;
      }
      return 0;
    }
    const note = `${assignee.name} was marked out of office until ` +
      `${C.fmtDate(assignee.ooo_until)}. Rerouted to ${cover.name} (${cover.title}).`;
    req.assignee_id = cover.id;
    touch(req, at);
    logEvent(st, req.id, "reroute_ooo", note, at, AGENT_ACTOR);
    sendMessage(st, { request_id: req.id, sender_id: null, recipient_id: cover.id, type: "reroute",
      body: `You are now covering '${req.title}'.\n\n${note}\n\n` +
            `Atlas rerouted this automatically because you are the configured cover.`, at });
    sendMessage(st, { request_id: req.id, sender_id: null, recipient_id: req.requester_id,
      type: "status_update", body: `'${req.title}' was rerouted: ${note}`, at });
    return 1;
  }

  function ruleChase(st, req, at, chaseAfter, interval, maxChases) {
    if (req.status !== "pending" || req.assignee_id === null) return 0;
    if (req.chase_count >= maxChases) return 0;
    const threshold = req.chase_count === 0 ? chaseAfter : interval;
    const elapsed = hoursSince(at, req.last_action_at);
    if (elapsed < threshold) return 0;

    const assignee = C.person(st, req.assignee_id);
    req.chase_count += 1;
    touch(req, at);
    const final = req.chase_count >= maxChases;
    const detail = `No acknowledgement after ${Math.floor(elapsed)}h — chase ` +
      `${req.chase_count} of ${maxChases} sent to ${assignee.name}.` +
      (final ? " This is the final reminder before escalation." : "");
    logEvent(st, req.id, "chase", detail, at, AGENT_ACTOR);
    sendMessage(st, { request_id: req.id, sender_id: null, recipient_id: assignee.id, type: "chase",
      body: `Reminder ${req.chase_count} of ${maxChases}: '${req.title}' is still awaiting ` +
            `your acknowledgement. It was raised ` +
            `${Math.floor(hoursSince(at, req.created_at))}h ago.` +
            (final ? " If it is not picked up it will be escalated." : ""), at });
    return 1;
  }

  function ruleHandoverOrEscalate(st, req, at, interval, maxChases) {
    if (req.status !== "pending" || req.assignee_id === null) return 0;
    if (req.chase_count < maxChases) return 0;
    if (hoursSince(at, req.last_action_at) < interval) return 0;

    const assignee = C.person(st, req.assignee_id);
    const proc = req.process_id ? C.process_(st, req.process_id) : null;
    const procName = proc ? proc.name : "this process";
    const alreadyRerouted = hasEvent(st, req.id, "reroute_chase");
    const cover = (req.process_id && !alreadyRerouted)
      ? C.coverFor(st, req.process_id, assignee.id, at) : null;

    if (cover) {
      const detail = `${maxChases} chases went unanswered by ${assignee.name}. Handed over to ` +
        `${cover.name} (${cover.title}), the configured cover for '${procName}'. ` +
        `One further chase will be sent before escalation.`;
      req.assignee_id = cover.id;
      req.chase_count = Math.max(0, maxChases - 1);
      touch(req, at);
      logEvent(st, req.id, "reroute_chase", detail, at, AGENT_ACTOR);
      sendMessage(st, { request_id: req.id, sender_id: null, recipient_id: cover.id,
        type: "reroute", body: `'${req.title}' has been handed over to you.\n\n${detail}`, at });
      sendMessage(st, { request_id: req.id, sender_id: null, recipient_id: req.requester_id,
        type: "status_update", body: `'${req.title}' was rerouted: ${detail}`, at });
      return 1;
    }

    const manager = assignee.manager_id ? C.person(st, assignee.manager_id) : null;
    if (!manager) {
      if (!hasEvent(st, req.id, "escalation_blocked")) {
        logEvent(st, req.id, "escalation_blocked",
          `${assignee.name} has no manager on record and no cover is configured, so this ` +
          `request cannot be escalated automatically. Flagged for the Atlas admin.`, at, AGENT_ACTOR);
        return 1;
      }
      return 0;
    }

    const reason = !alreadyRerouted ? "no cover is configured" : "the cover did not respond either";
    const detail = `${maxChases} chases went unanswered and ${reason} for '${procName}'. ` +
      `Escalated to ${manager.name} (${manager.title}).`;
    req.status = "escalated";
    req.assignee_id = manager.id;
    touch(req, at);
    logEvent(st, req.id, "escalation", detail, at, AGENT_ACTOR);
    sendMessage(st, { request_id: req.id, sender_id: null, recipient_id: manager.id,
      type: "escalation",
      body: `Escalation: '${req.title}'.\n\n${detail}\n\nIt is now assigned to you.`, at });
    sendMessage(st, { request_id: req.id, sender_id: null, recipient_id: req.requester_id,
      type: "escalation",
      body: `Your request '${req.title}' has been escalated to ${manager.name}. ${detail}`, at });
    return 1;
  }

  function tick(st) {
    const at = C.now(st);
    const chaseAfter = st.settings.chase_after_hours;
    const interval = st.settings.chase_interval_hours;
    const maxChases = st.settings.max_chases;
    let actions = 0;
    const open = st.requests
      .filter(r => OPEN_STATUSES.includes(r.status))
      .sort((a, b) => a.id - b.id);
    for (const req of open) {
      if (req.status === "escalated") continue;
      actions += ruleOooReroute(st, req, at);
      actions += ruleChase(st, req, at, chaseAfter, interval, maxChases);
      actions += ruleHandoverOrEscalate(st, req, at, interval, maxChases);
    }
    st.lastTickAt = at;
    st.lastTickActions = actions;
    return actions;
  }

  function runUntilSettled(st, maxPasses) {
    let total = 0;
    for (let i = 0; i < (maxPasses || 6); i++) {
      const fired = tick(st);
      total += fired;
      if (!fired) break;
    }
    return total;
  }

  root.AtlasServices = {
    logEvent, sendMessage, draftBody, suggestTitle, findSimilarOpen, createRequest,
    acknowledge, startProgress, complete, addNote, followExisting, reassign, markRead, setOoo,
    tick, runUntilSettled, hoursSince,
  };
  if (typeof module !== "undefined" && module.exports) Object.assign(module.exports, root.AtlasServices);
})(typeof globalThis !== "undefined" ? globalThis : this);

/* ================================ analytics ============================== */
(function (root) {
  "use strict";
  const C = root.AtlasCore;
  const { HOUR, OPEN_STATUSES, STATUS_LABELS } = C;

  const isOpen = r => OPEN_STATUSES.includes(r.status);
  const hrs = (a, b) => (a - b) / HOUR;

  function departmentName(st, p) {
    if (!p) return "Unassigned";
    if (p.department_id === null || p.department_id === undefined) return "Executive";
    const d = C.department(st, p.department_id);
    return d ? d.name : "Unassigned";
  }

  function headline(st) {
    const at = C.now(st);
    const reqs = st.requests;
    const open = reqs.filter(isOpen);
    const escalatedIds = new Set(st.events.filter(e => e.type === "escalation" && e.request_id)
                                          .map(e => e.request_id));
    const ack = reqs.filter(r => r.acknowledged_at).map(r => hrs(r.acknowledged_at, r.created_at));
    const cycle = reqs.filter(r => r.completed_at).map(r => hrs(r.completed_at, r.created_at));
    const waiting = open.map(r => hrs(at, r.created_at));
    const mean = a => a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0;
    return {
      total_requests: reqs.length,
      open_requests: open.length,
      completed_requests: reqs.filter(r => r.status === "completed").length,
      escalated_requests: escalatedIds.size,
      escalation_rate: reqs.length ? (escalatedIds.size / reqs.length) * 100 : 0,
      avg_ack_hours: mean(ack), avg_cycle_hours: mean(cycle), avg_queue_hours: mean(waiting),
      oldest_open_hours: waiting.length ? Math.max(...waiting) : 0,
    };
  }

  function byStatus(st) {
    const order = ["pending", "acknowledged", "in_progress", "escalated", "completed"];
    const counts = {};
    for (const r of st.requests) counts[r.status] = (counts[r.status] || 0) + 1;
    return order.map(s => ({ key: s, status: STATUS_LABELS[s], count: counts[s] || 0 }));
  }

  function openByDepartment(st) {
    const counts = new Map();
    for (const r of st.requests.filter(isOpen)) {
      const dept = departmentName(st, r.assignee_id ? C.person(st, r.assignee_id) : null);
      const row = counts.get(dept) || { department: dept, count: 0, escalated: 0 };
      row.count++;
      if (r.status === "escalated") row.escalated++;
      counts.set(dept, row);
    }
    return Array.from(counts.values()).sort((a, b) => b.count - a.count || a.department.localeCompare(b.department));
  }

  function turnaroundByDepartment(st) {
    const ack = new Map(), cycle = new Map();
    const push = (m, k, v) => { if (!m.has(k)) m.set(k, []); m.get(k).push(v); };
    for (const r of st.requests) {
      const dept = departmentName(st, r.assignee_id ? C.person(st, r.assignee_id) : null);
      if (r.acknowledged_at) push(ack, dept, hrs(r.acknowledged_at, r.created_at));
      if (r.completed_at) push(cycle, dept, hrs(r.completed_at, r.created_at));
    }
    const depts = Array.from(new Set([...ack.keys(), ...cycle.keys()])).sort();
    const mean = a => (a && a.length) ? a.reduce((x, y) => x + y, 0) / a.length : 0;
    return depts.map(d => ({
      department: d,
      avg_ack_hours: Math.round(mean(ack.get(d)) * 10) / 10,
      avg_complete_hours: Math.round(mean(cycle.get(d)) * 10) / 10,
      sample: Math.max((ack.get(d) || []).length, (cycle.get(d) || []).length),
    }));
  }

  function orphanProcesses(st) {
    const owned = new Set(st.responsibilities.filter(r => r.role === "owner").map(r => r.process_id));
    return st.processes.slice().sort((a, b) => a.name.localeCompare(b.name))
      .filter(p => !owned.has(p.id))
      .map(p => ({
        process: p.name, category: p.category,
        open_requests: st.requests.filter(r => r.process_id === p.id && isOpen(r)).length,
        other_roles: Array.from(new Set(st.responsibilities.filter(r => r.process_id === p.id)
          .map(r => r.role))).sort().join(", ") || "none",
      }));
  }

  function singlePointsOfFailure(st, threshold) {
    threshold = threshold === undefined ? 2 : threshold;
    const at = C.now(st);
    const byPerson = new Map();
    for (const row of st.responsibilities) {
      if (!byPerson.has(row.person_id)) byPerson.set(row.person_id, {});
      const roles = byPerson.get(row.person_id);
      (roles[row.role] = roles[row.role] || []).push(C.process_(st, row.process_id));
    }
    const rows = [];
    for (const [personId, roles] of byPerson) {
      const p = C.person(st, personId);
      if (!p) continue;
      const owns = roles.owner || [], approves = roles.approver || [];
      if (owns.length + approves.length < threshold) continue;
      const uncovered = [];
      for (const proc of owns) {
        const covers = st.responsibilities.filter(r => r.process_id === proc.id &&
          (r.role === "delegate" || r.role === "backup") && r.person_id !== personId)
          .map(r => C.person(st, r.person_id));
        if (!covers.some(c => c && !C.isOutOfOffice(c, at))) uncovered.push(proc.name);
      }
      rows.push({
        person: p.name, title: p.title, department: departmentName(st, p),
        owns: owns.length, approves: approves.length, uncovered: uncovered.sort(),
        open_load: st.requests.filter(r => r.assignee_id === personId && isOpen(r)).length,
        is_ooo: C.isOutOfOffice(p, at),
      });
    }
    rows.sort((a, b) => b.uncovered.length - a.uncovered.length ||
      (b.owns + b.approves) - (a.owns + a.approves) || b.open_load - a.open_load);
    return rows;
  }

  function bottlenecks(st, limit) {
    const at = C.now(st);
    const rows = new Map();
    for (const r of st.requests.filter(isOpen)) {
      if (!r.assignee_id) continue;
      if (!rows.has(r.assignee_id)) rows.set(r.assignee_id, { open: 0, waits: [] });
      const e = rows.get(r.assignee_id);
      e.open++; e.waits.push(hrs(at, r.created_at));
    }
    const out = [];
    for (const [pid, e] of rows) {
      const p = C.person(st, pid);
      if (!p) continue;
      out.push({
        person: p.name, title: p.title, department: departmentName(st, p), open: e.open,
        avg_wait_hours: Math.round((e.waits.reduce((x, y) => x + y, 0) / e.waits.length) * 10) / 10,
        oldest_wait_hours: Math.round(Math.max(...e.waits) * 10) / 10,
        is_ooo: C.isOutOfOffice(p, at),
      });
    }
    out.sort((a, b) => b.open - a.open || b.oldest_wait_hours - a.oldest_wait_hours);
    return out.slice(0, limit || 8);
  }

  function queueAges(st) {
    const at = C.now(st);
    return st.requests.filter(isOpen).map(r => {
      const a = r.assignee_id ? C.person(st, r.assignee_id) : null;
      return {
        id: r.id, title: r.title, status: STATUS_LABELS[r.status],
        department: departmentName(st, a), assignee: a ? a.name : "Unassigned",
        age_hours: Math.round(hrs(at, r.created_at) * 10) / 10, chases: r.chase_count,
      };
    }).sort((a, b) => b.age_hours - a.age_hours);
  }

  function processStats(st, processId) {
    const reqs = st.requests.filter(r => r.process_id === processId);
    const done = reqs.filter(r => r.completed_at);
    const t = done.map(r => hrs(r.completed_at, r.created_at));
    return {
      total: reqs.length, open: reqs.filter(isOpen).length, completed: done.length,
      avg_turnaround_hours: t.length ? Math.round((t.reduce((x, y) => x + y, 0) / t.length) * 10) / 10 : null,
    };
  }

  function personStats(st, personId) {
    const handled = st.requests.filter(r => r.assignee_id === personId);
    const done = handled.filter(r => r.completed_at);
    const t = done.map(r => hrs(r.completed_at, r.created_at));
    const a = handled.filter(r => r.acknowledged_at).map(r => hrs(r.acknowledged_at, r.created_at));
    const mean = arr => arr.length ? Math.round((arr.reduce((x, y) => x + y, 0) / arr.length) * 10) / 10 : null;
    return {
      open_load: handled.filter(isOpen).length, completed: done.length,
      avg_turnaround_hours: mean(t), avg_ack_hours: mean(a),
    };
  }

  function responsibilitiesOf(st, personId) {
    const grouped = { owner: [], approver: [], delegate: [], backup: [] };
    for (const row of st.responsibilities.filter(r => r.person_id === personId)) {
      const p = C.process_(st, row.process_id);
      if (p) (grouped[row.role] = grouped[row.role] || []).push(p);
    }
    for (const k of Object.keys(grouped)) grouped[k].sort((a, b) => a.name.localeCompare(b.name));
    return grouped;
  }

  function responsibilityGraph(st, dept) {
    const nodes = [], edges = [];
    for (const p of st.processes.slice().sort((a, b) => a.name.localeCompare(b.name)))
      nodes.push({ id: "p" + p.id, label: p.name, kind: "process", group: p.category });
    const peopleIds = Array.from(new Set(st.responsibilities.map(r => r.person_id))).sort((a, b) => a - b);
    for (const pid of peopleIds) {
      const p = C.person(st, pid);
      if (!p) continue;
      const d = departmentName(st, p);
      if (dept && d !== dept) continue;
      nodes.push({ id: "h" + p.id, label: p.name, kind: "person", group: d });
    }
    const ids = new Set(nodes.map(n => n.id));
    for (const row of st.responsibilities) {
      const s = "h" + row.person_id, t = "p" + row.process_id;
      if (ids.has(s) && ids.has(t)) edges.push({ source: s, target: t, role: row.role });
    }
    return { nodes, edges };
  }

  root.AtlasAnalytics = {
    headline, byStatus, openByDepartment, turnaroundByDepartment, orphanProcesses,
    singlePointsOfFailure, bottlenecks, queueAges, processStats, personStats,
    responsibilitiesOf, responsibilityGraph, departmentName, isOpen,
  };
  if (typeof module !== "undefined" && module.exports) Object.assign(module.exports, root.AtlasAnalytics);
})(typeof globalThis !== "undefined" ? globalThis : this);

/* Flatten the namespaces onto the global object so browser code sees exactly
   the same flat surface that `require()` gives the Node tests. */
(function (root) {
  Object.assign(root, root.AtlasFuzz, root.AtlasMatch, root.AtlasCore,
                root.AtlasServices, root.AtlasAnalytics);
})(typeof globalThis !== "undefined" ? globalThis : this);
