# Atlas — browser preview

A single self-contained HTML file that runs Atlas entirely in the browser, so
the prototype can be clicked without installing Python or deploying anything.

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
| `ui_1.js` | State, persistence, helpers, the sidebar |
| `ui_2.js` | Intake and the request pages |
| `ui_3.js` | Directory, profiles, agent log |
| `ui_4.js` | Charts (hand-built SVG) and the dashboard |
| `ui_5.js` | Event wiring, tooltips, the agent loop, boot |

`export_seed.py` imports the real `atlas.seed` module, so the preview's data is
generated from the Python seed rather than transcribed by hand.

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

## Known differences from the Python app

- **No shared state.** Every visitor has their own database in `localStorage`;
  the Python app has one SQLite file shared by everyone hitting the server.
- **The agent stops when the tab is closed.** It ticks every 2 seconds while the
  page is open. Simulated time is stored, so nothing is lost — but the agent
  will not act while you are away, and no chases accumulate in the background.
- **Reassignment is not exposed.** The engine implements it; the preview's
  request detail does not surface the control.
