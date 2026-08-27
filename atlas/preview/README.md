# Atlas — browser preview

A single self-contained HTML file that runs Atlas entirely in the browser, so
the prototype can be clicked without installing Python or deploying anything.

The browser build is **chat-first**: you ask Atlas for things in plain English
rather than filling in a form, and the rest of the platform (org chart,
requests, agent log, dashboard) hangs off that conversation. The Python app in
`atlas/` still has the original form-based intake and no org chart.

**This is a mirror, not the product.** `atlas/` (the Python app) is the source of
truth. This directory is a second implementation of the same logic in
JavaScript, kept honest by the parity suite below. If you change routing, the
agent rules, matching or analytics in the Python app, change them here too and
re-run the parity check — otherwise the two will drift apart.

## Open it

Just open `atlas-preview.html` in a browser. No server, no build, no network
(the only outbound request is Google Fonts, and the page falls back to system
fonts without it).

State lives in `localStorage`, so each visitor gets their own private copy —
advancing the clock or resetting the database affects nobody else. **Reset &
reseed** in the sidebar clears it.

## Rebuild it

```bash
cd atlas/preview
python3 export_seed.py     # re-dump the seeded database to seed.json
python3 build.py           # assemble atlas-preview.html
```

`build.py` concatenates, in order: `shell.html` (markup + CSS), `seed.json`
(inlined as `const SEED`), `atlas_engine.js` (the ported logic) and `ui_1.js`
through `ui_5.js` (the interface). Editing any of those and re-running
`build.py` is the whole loop.

| File | What it holds |
| --- | --- |
| `shell.html` | Page shell, design tokens, light and dark themes |
| `seed.json` | The seeded database, timestamps stored as hours relative to seed time |
| `atlas_engine.js` | Fuzzy matching, TF-IDF, routing, the agent rules, analytics |
| `ui_1.js` | State, persistence, helpers, the sidebar, navigation |
| `ui_2.js` | The chat surface — intents, bot replies, the draft flow |
| `ui_3.js` | People: interactive org chart, directory, teams, processes |
| `ui_4.js` | Requests and the agent log |
| `ui_5.js` | Charts (hand-built SVG) and the dashboard |
| `ui_6.js` | Guide and tour, event wiring, pan/zoom, the agent loop, boot |

`build.py` discovers `ui_*.js` in numeric order, so adding a part needs no edit
to the builder. It also fails the build if the assembled page contains more than
one `</script>` — a script that does not close its own braces truncates silently
in the browser rather than erroring.

`export_seed.py` imports the real `atlas.seed` module, so the preview's data is
generated from the Python seed rather than transcribed by hand.

## Browser test suite

`test_preview.py` drives the built page in a real browser and checks the
first-run guide, the chat flow, the org chart (full-bleed layout, suggestions,
focus, climbing back up, wheel zoom and its cursor anchoring, folding), the other
pages, persistence across a reload, and dark mode.

```bash
pip install playwright && playwright install chromium
python3 test_preview.py
```

## Parity suite

Proves the JavaScript behaves like the Python across matching, the full request
lifecycle, and analytics:

```bash
cd atlas/preview/parity
python3 ref_match.py     > ref_match.json      # Python reference output
python3 ref_agent.py     > ref_agent.json
python3 ref_analytics.py > ref_analytics.json
node check_parity.js                            # compare against the JS engine
```

What it currently confirms:

- **Matching** — identical top match and identical matched-keyword set across 24
  queries; confidences and all four signal values agree to the 4 decimal places
  the reference stores.
- **Agent lifecycle** — the data-room request driven through
  `+48h → +24h ×4`, then acknowledged and completed, produces the same status,
  assignee, chase count, agent-action count and event sequence at every step.
- **Analytics** — headline metrics, status counts, per-department turnaround,
  the orphan report, the single-point-of-failure report and the bottleneck table
  all match. Two fields (`avg_queue_hours`, `oldest_open_hours`,
  `oldest_wait_hours`) are compared to the nearest hour because they depend on
  the wall clock between the two runs.

## The chat

`classify()` in the engine routes a message to one of a handful of intents —
raise a request, who owns X, who is out of office, my inbox, my requests, who is
this person, help — falling back to treating anything else as a request. It is
keyword and fuzzy matching over the seeded data, not a language model: there is
no network call, and the same input always produces the same answer.

A request turns into a draft the user can edit before sending, with the process
match, the confidence, the matched keywords and the full resolution trace shown
inline so the routing is never a black box.

## The org chart

`orgTree()` builds a forest from `manager_id`; anyone whose manager is missing
becomes a root, so nobody is silently dropped. Layout is a tidy tree — leaves
take the next slot, parents centre over their children — drawn as inline SVG
with pan, zoom, per-node collapse, search-to-highlight and a detail panel.

It opens folded to the five department heads rather than dropping the viewer
into a 7,000-pixel canvas, and auto-fits to the container on first paint.

The chart is **full-bleed**: on the Org chart tab the page header is dropped and
the canvas fills the viewport, with the detail panel floating over the top-right
corner and the legend over the bottom-left.

**Zoom** is on the wheel, anchored at the cursor so whatever you point at stays
put. The chart owns the wheel — it is a canvas, not a scrolling document — and
the zoom is applied straight to the DOM rather than through a re-render, so the
scroll position survives. (The chart is a flex item; it needs `flex:none` or the
container shrinks it back and zoom silently does nothing.)

**Search is a combobox.** Typing filters a suggestion list and leaves the chart
alone; the chart only moves once you pick someone. Arrow keys move the
highlight, Enter takes the top match, Escape closes. Picking someone re-roots
the chart on them — everyone above is hidden — and centres them in the stage.

A bar above the chart then names who is showing, says how many levels are hidden
above, offers "↑ Up to <manager>" to climb back one level at a time, and "Show
whole firm" to reset.

**Nodes carry an avatar, a name and a title, and nothing else.** Everything else
lives on a **hover card**, which scales 1:1 with the zoom level so it is always
the same size relative to the cards it describes. It — team, away date, who they report to, team size, what
they own, open load — with two actions: ask that person for something, or focus
on their team. Hovering also lights the chain of command from that person up to
the CEO and mutes everyone off it.

**You can raise a request straight from the chart.** "Ask them for something"
opens the chat scoped to that person and offers the request types they own as
chips; picking one drafts it. If they own nothing, it says so and asks what you
need instead. If they are away, the routing still applies — the request goes to
their cover, and the trace says why.

The **detail panel is deliberately short** — name, title, team, away status, who
they report to, team size, and what they own. Anything deeper is a question for
Ask Atlas rather than a wall of fields on first glance.

### Navigation and chrome

There is no side panel. A single header bar carries the wordmark, three primary
tabs — Ask, People, Requests — a **More** menu, and the "you are" switcher.
Everything else (the request catalogue, dashboard, agent log, demo controls and
guide) lives behind More, so a first-time employee sees three choices rather
than a wall of controls.

The demo rig — simulated clock, out-of-office toggle, agent, reset — is its own
page under More rather than a permanent panel, so it stays out of the way while
you are trying the product. The identity switcher stays in the header because
you need it constantly to see both sides of a request.

Copy throughout is deliberately terse: page subtitles are one short line or
absent, chart descriptions are gone, and the match explanation sits behind a
"Why this match?" disclosure rather than a paragraph under every reply.

These follow established org-chart practice: an avatar as the hero element,
details on demand rather than crammed into every node, hover-highlighting the
reporting chain, and deferring rarely-used features to a secondary surface.

## Known differences from the Python app

- **Chat and the org chart are browser-only.** The Python app still has the
  form-based intake page and no org chart.
- **No shared state.** Every visitor has their own database in `localStorage`;
  the Python app has one SQLite file shared by everyone hitting the server.
- **The agent stops when the tab is closed.** It ticks every 2 seconds while the
  page is open. Simulated time is stored, so nothing is lost — but the agent
  will not act while you are away, and no chases accumulate in the background.
- **Reassignment is not exposed.** The engine implements it; the preview's
  request detail does not surface the control.
