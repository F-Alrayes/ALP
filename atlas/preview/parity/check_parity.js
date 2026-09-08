/* Compare the browser preview's engine against the Python implementation.
 *
 *   cd atlas/preview/parity
 *   python3 ref_match.py > ref_match.json
 *   python3 ref_relay.py > ref_relay.json
 *   python3 ref_contact.py > ref_contact.json
 *   python3 ref_agent.py > ref_agent.json
 *   python3 ref_analytics.py > ref_analytics.json
 *   node check_parity.js
 *
 * Exits non-zero on any divergence. */
const path = require("path");
const E = require(path.join(__dirname, "..", "atlas_engine.js"));
const seed = require(path.join(__dirname, "..", "seed.json"));

let failures = 0;
const ok = (label, pass, extra) => {
  console.log((pass ? "  PASS  " : "  FAIL  ") + label + (extra ? "   " + extra : ""));
  if (!pass) failures++;
};

/* ------------------------------- matching ------------------------------- */
console.log("\n[matching]");
{
  const ref = require("./ref_match.json");
  let topBad = 0, kwBad = 0, drift = 0;
  for (const row of ref) {
    const js = E.matchProcesses(seed.processes, row.q, 3);
    const py = row.top;
    if (!js.length || js[0].process_name !== py[0].name) { topBad++; continue; }
    if (js[0].matched_keywords.join("|") !== py[0].kw.join("|")) kwBad++;
    drift = Math.max(drift, Math.abs(js[0].confidence - py[0].conf));
    for (const k of ["keywords", "name", "tfidf", "description"])
      drift = Math.max(drift, Math.abs(js[0].signals[k] - py[0].sig[k]));
  }
  ok(`top match identical across ${ref.length} queries`, topBad === 0, `${topBad} differed`);
  ok("matched keyword sets identical", kwBad === 0, `${kwBad} differed`);
  // The Python reference stores signals rounded to 4 decimals, so that rounding
  // is the floor of what this comparison can resolve.
  const TOL = 5e-4;
  ok(`confidence and signals agree within the reference's 4-decimal precision`,
     drift < TOL, `max drift ${drift.toExponential(2)} (tolerance ${TOL})`);
}

/* ---------------------------- reading requests --------------------------- */
console.log("\n[reading plain English]");
{
  // Both apps split "email whoever owns X and ask them to Y" into the subject
  // and the ask before matching. If they ever read a sentence differently, the
  // same words would route to different people in the two front ends.
  const ref = require("./ref_relay.json");
  let bad = 0, first = "";
  for (const row of ref) {
    const p = E.splitRelay(row.s);
    const joined = [p.subject, p.ask].filter(Boolean).join(" ").trim();
    const query = joined.length >= 3 ? joined : row.s.trim();
    if (p.subject !== row.subject || p.ask !== row.ask || query !== row.query) {
      bad++;
      if (!first) first = JSON.stringify(row.s);
    }
  }
  ok(`subject and ask identical across ${ref.length} sentences`, bad === 0,
     bad ? `${bad} differed, first ${first}` : "");
}

/* -------------------------- who do I contact? ---------------------------- */
console.log("\n[routing a problem to a team]");
{
  // Both apps answer "who do I contact to get my laptop fixed" from the same
  // team vocabulary. A drift here would send the same question to two
  // different people depending on which front end you happened to be in.
  const ref = require("./ref_contact.json");
  const st = E.hydrate(seed, Date.now());
  let bad = 0, first = "";
  for (const row of ref) {
    const js = JSON.stringify(E.matchDepartments(st, row.q, 3).map(c =>
      [c.department_name, c.confidence, c.matched_keywords, c.person_name, c.reason]));
    const py = JSON.stringify(row.top.map(c => [c.dept, c.conf, c.kw, c.who, c.reason]));
    if (js !== py) { bad++; if (!first) first = JSON.stringify(row.q); }
  }
  ok(`team, contact and confidence identical across ${ref.length} questions`, bad === 0,
     bad ? `${bad} differed, first ${first}` : "");
}

/* --------------------------- agent lifecycle ---------------------------- */
console.log("\n[agent lifecycle]");
{
  const ref = require("./ref_agent.json");
  const st = E.hydrate(seed, Date.now());
  const steps = [];
  const snap = (label, actions, rid) => {
    const r = rid ? E.request(st, rid) : null;
    steps.push({
      label, actions,
      status: r ? r.status : null,
      assignee: r && r.assignee_id ? E.person(st, r.assignee_id).name : null,
      chases: r ? r.chase_count : null,
      events: rid ? st.events.filter(e => e.request_id === rid)
        .sort((a, b) => a.created_at - b.created_at || a.id - b.id)
        .map(e => [e.type, e.actor]) : [],
      agent_events_total: st.events.filter(e => e.actor === "atlas-agent").length,
    });
  };

  snap("seed+settle", E.runUntilSettled(st), null);
  const Q = "I need access to the data room for Project Falcon";
  const m = E.matchProcesses(st.processes, Q, 3)[0];
  const proc = E.process_(st, m.process_id);
  const res = E.resolve(st, proc);
  const requester = st.people.find(p => p.name === "Noura Al-Sabah");
  const rid = E.createRequest(st, {
    requester_id: requester.id, process_id: proc.id, assignee_id: res.assignee_id,
    title: "Data room access for Project Falcon",
    body: E.draftBody(requester, proc, res, Q), resolution: res,
  }).id;
  snap("created", 0, rid);
  for (const h of [48, 24, 24, 24, 24]) { E.advance(st, h); snap("+" + h + "h", E.runUntilSettled(st), rid); }
  E.acknowledge(st, rid, E.request(st, rid).assignee_id); snap("acknowledge", 0, rid);
  E.complete(st, rid, E.request(st, rid).assignee_id, "Access granted."); snap("complete", 0, rid);

  for (let i = 0; i < ref.length; i++) {
    const a = ref[i], b = steps[i];
    ok(`${a.label}: ${a.actions} agent action(s), ${a.status || "—"}, ${a.assignee || "—"}`,
       JSON.stringify(a) === JSON.stringify(b));
  }
}

/* ------------------------------- analytics ------------------------------ */
console.log("\n[analytics]");
{
  const ref = require("./ref_analytics.json");
  const st = E.hydrate(seed, Date.now());
  E.runUntilSettled(st);
  const round = o => JSON.stringify(o, (k, v) =>
    // These two depend on the wall clock between the two runs.
    (k === "avg_queue_hours" || k === "oldest_open_hours" || k === "oldest_wait_hours")
      ? Math.round(v) : v);
  const js = {
    headline: (() => { const h = E.headline(st), o = {};
      for (const k in h) o[k] = typeof h[k] === "number" && !Number.isInteger(h[k])
        ? Math.round(h[k] * 1000) / 1000 : h[k];
      return o; })(),
    by_status: E.byStatus(st).map(r => ({ status: r.status, key: r.key, count: r.count })),
    turnaround: E.turnaroundByDepartment(st),
    orphans: E.orphanProcesses(st),
    spof: E.singlePointsOfFailure(st, 2).map(r => ({ person: r.person, owns: r.owns,
      approves: r.approves, uncovered: r.uncovered, open_load: r.open_load })),
    bottlenecks: E.bottlenecks(st).map(b => { const { avg_wait_hours, ...rest } = b; return rest; }),
  };
  for (const key of Object.keys(ref)) ok(key + " identical", round(ref[key]) === round(js[key]));
}

console.log(failures ? `\nFAILED — ${failures} check(s) diverged`
                     : "\nPASS — the preview engine matches the Python implementation");
process.exit(failures ? 1 : 0);
