# Deploying Atlas

Atlas is a single Streamlit process with a SQLite file next to it. It has no
external dependencies, so it will run anywhere that can run Python or a
container. It seeds itself on first launch, which means an ephemeral filesystem
is fine — there is nothing to provision.

Pick one of the three options below. The first is the fastest.

---

## Option A — Streamlit Community Cloud (free, ~2 minutes)

The quickest way to get a shareable URL. Free, and it redeploys on every push.

1. Go to <https://share.streamlit.io> and sign in with the GitHub account that
   owns `F-Alrayes/ALP`.
2. Authorise Streamlit to read the repository when prompted.
3. **Create app** → **Deploy a public app from GitHub**, then fill in:

   | Field | Value |
   | --- | --- |
   | Repository | `F-Alrayes/ALP` |
   | Branch | `claude/new-platform-setup-dkls05` |
   | Main file path | `atlas/app.py` |

4. Under **Advanced settings**, set the Python version to **3.11** (3.12 also
   works; 3.10 is the minimum).
5. **Deploy**.

You will get a URL like `https://<something>.streamlit.app`.

Two things worth knowing:

- **Dependencies.** Streamlit Cloud looks for a requirements file next to the
  entrypoint, so it picks up `atlas/requirements.txt` on its own. If the build
  log complains that `streamlit`, `plotly` or another package is missing, that
  is the fix — point it at `atlas/requirements.txt`, or copy that file to the
  repository root and redeploy.
- **The theme.** Streamlit resolves `.streamlit/config.toml` relative to the
  entrypoint, so `atlas/.streamlit/config.toml` is picked up automatically. No
  extra configuration needed.

---

## Option B — Any container host (Render, Railway, Fly.io, Cloud Run)

`atlas/Dockerfile` builds a self-contained image. It binds `$PORT` when the host
injects one and falls back to 8501.

```bash
cd atlas
docker build -t atlas .
docker run --rm -p 8501:8501 atlas       # then open http://localhost:8501
```

**Render** has a blueprint committed at the repository root. Go to
render.com → **New** → **Blueprint**, point it at this repository, and it reads
`render.yaml` (Docker runtime, `rootDir: atlas`, health check on
`/_stcore/health`). Note that Render's free tier sleeps after inactivity and
takes ~30s to wake.

**Railway / Fly.io / Cloud Run** all detect the Dockerfile directly; set the
build context or root directory to `atlas/`.

---

## Option C — Run it on your own machine

The lowest-friction way to try it, and the only one where nothing is public:

```bash
git clone https://github.com/F-Alrayes/ALP.git
cd ALP/atlas
git checkout claude/new-platform-setup-dkls05
pip install -r requirements.txt
python run.py
```

It opens at <http://localhost:8501>. Requires Python 3.10+.

To let colleagues on the same network reach it:

```bash
python run.py --address 0.0.0.0
```

---

## Things to know about a shared deployment

Atlas was built as a prototype to be driven by one person, so a shared URL has
a few sharp edges. None of them are bugs, but they will surprise you if two
people open the link at once.

- **No authentication.** The sidebar "acting as" switcher replaces login by
  design. Anyone with the URL can act as anyone. Do not put real data in it.
- **State is shared, not per-visitor.** One database backs the whole
  deployment. If a colleague advances the simulated clock or marks someone out
  of office, you will see it too. That is realistic for an internal tool, but it
  means two people demoing at the same time will step on each other.
- **Reset & reseed is global.** The sidebar button wipes every request for
  everyone, not just the person who clicked it.
- **Data does not survive a restart.** The database lives on the host's
  ephemeral disk, so a redeploy or an idle-sleep resets it to the seeded state.
  For a demo this is a feature — every session starts clean. If you want
  requests to persist, mount a volume at `atlas/data/`.
- **Free tiers sleep.** Both Streamlit Cloud and Render's free plan idle out
  after a period of inactivity and take a few seconds to wake. The background
  agent stops while the process is asleep, then resumes on the next request —
  simulated time is stored in the database, so nothing is lost.

## Verifying a deployment

Once it is up, `python verify.py` runs the full acceptance checklist against a
local copy, and the three-minute script in [README.md](README.md#the-three-minute-demo)
is the fastest way to confirm the deployed instance behaves correctly.
