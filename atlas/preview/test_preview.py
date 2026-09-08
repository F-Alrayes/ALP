#!/usr/bin/env python3
"""End-to-end regression suite for the Atlas browser preview.

    pip install playwright && playwright install chromium
    python3 test_preview.py [path/to/atlas-preview.html]

Drives the built page in a real browser and checks the behaviour that matters:
the first-run guide, the chat flow, the org chart (full-bleed layout, search
suggestions, focus, zoom, collapse), the other pages, persistence across a
reload, and dark mode. Exits non-zero on any failure.
"""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PAGE = Path(sys.argv[1] if len(sys.argv) > 1
            else Path(__file__).resolve().parent / "atlas-preview.html").resolve()
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

fails: list[str] = []


def check(label, cond, extra=""):
    print(("  PASS  " if cond else "  FAIL  ") + label + (f"   {extra}" if extra else ""))
    if not cond:
        fails.append(label)


def section(name):
    print(f"\n[{name}]")


def launch(pw, **kw):
    try:
        browser = pw.chromium.launch(executable_path=CHROME)
    except Exception:
        browser = pw.chromium.launch()
    return browser


def tab(p, name):
    p.get_by_role("tab", name=name, exact=False).first.click()
    p.wait_for_timeout(900)


def names(p):
    return p.evaluate("[...document.querySelectorAll('.onode .oname')].map(e=>e.textContent)")


def run(p):
    p.goto(PAGE.as_uri(), wait_until="load", timeout=45000)
    p.wait_for_timeout(1800)

    # ---------------------------------------------------------------- guide
    section("first-run guide")
    check("guide opens on a first visit", p.locator(".modal").count() == 1)
    check("it is step 1 of 4", "1 of 4" in p.inner_text(".modal").lower())
    for _ in range(3):
        p.get_by_role("button", name="Next").click()
        p.wait_for_timeout(320)
    check("it reaches the last step", "4 of 4" in p.inner_text(".modal").lower())
    p.get_by_role("button", name="Try the example").click()
    p.wait_for_timeout(1300)
    check("guide closes and runs the example", p.locator(".modal").count() == 0)

    # ----------------------------------------------------------------- chat
    section("chat")
    log = p.inner_text("#chatlog")
    check("echoes what was asked", "data room for Project Falcon" in log)
    check("matches the process", "Data Room Access" in log and "100%" in log)
    check("shows the routing trace", "Owner lookup" in log and "Layla Mansour" in log)
    check("detects out of office and delegates", "out of office" in log and "James Okonkwo" in log)
    check("offers an editable draft", p.locator('[data-act="dbody"]').count() == 1)
    p.locator('[data-act="chatsend"]').click()
    p.wait_for_timeout(1000)
    check("confirms it was sent", "Sent." in p.inner_text("#chatlog"))

    def ask(text):
        box = p.locator('[data-act="composer"]')
        box.click(); box.fill(text)
        p.keyboard.press("Enter"); p.wait_for_timeout(900)
        return p.inner_text("#chatlog")

    check("answers who owns a process", "Rania Khoury" in ask("Who owns invoice approval?"))
    check("answers who is away", "Layla Mansour" in ask("Is anyone out of office?"))
    check("answers about a person", "Financial Controller" in ask("Who is Huda Al-Najjar?"))
    check("answers for help", "find the right person and send it" in ask("help").lower())
    check("password requests route to IT access",
          "IT Access Provisioning" in ask("I am locked out of my account"))

    # --------------------------------------------------------- free text
    section("chat — plain English, no org chart")
    # A clean identity: the request above would otherwise be flagged as a
    # duplicate, which is right, but hides the send path being tested here.
    p.select_option('[data-act="actor"]', label="Marco Bianchi")
    p.wait_for_timeout(700)

    def reply(text):
        """The bot's answer to one message, not the whole scrollback."""
        box = p.locator('[data-act="composer"]')
        box.click(); box.fill(text)
        p.keyboard.press("Enter"); p.wait_for_timeout(900)
        return p.locator("#chatlog .msg.bot").last.inner_text()

    # The sentence a user actually typed, typos and all. Nobody is named, so
    # Atlas has to read it, look the owner up and send it on its own.
    log = reply("Can you send an email to whoever is reposible for Data and ask "
                "them to to give me access to it if possible")
    check("acts on it instead of answering a question", "Sent." in log, log[:160])
    check("resolves the owner from the subject alone", "Layla Mansour" in log, log[:160])
    check("fails over to the delegate", "James Okonkwo" in log, log[:160])
    check("offers an undo", p.locator('[data-act="undo"]').count() >= 1)
    p.locator('[data-act="undo"]').last.click(); p.wait_for_timeout(600)
    check("undo withdraws it",
          "Withdrawn" in p.locator("#chatlog .msg.bot").last.inner_text())

    log = reply("Ask whoever approves expenses to sign off my claim")
    check("reads an ask-first sentence", "Sent." in log or "Expense Reimbursement" in log,
          log[:160])

    # "access" genuinely means two different things here, so Atlas should ask
    # rather than pick one and send it.
    log = reply("ask whoever owns access and ask them to give me the documents")
    check("asks first when two readings are close",
          p.locator('[data-act="chose"]').count() >= 2, log[:200])
    check("offers both readings", "IT Access Provisioning" in log
          and "Data Room Access" in log, log[:200])
    check("names who each option would reach", "Bilal Rahman" in log, log[:200])

    log = reply("tell me about Layla Mansour")
    check("a question about a person is still a question", "Senior Associate" in log,
          log[:160])

    # ------------------------------------------------- who do I contact?
    section("chat — problems no request type covers")
    log = reply("who do i need to contact to get my laptop fixed")
    check("a broken laptop reaches IT", "IT" in log and "Vikram Chandra" in log, log[:160])
    check("shows the word it routed on", "laptop" in log, log[:160])
    check("offers to send it", p.locator('[data-act="sendcontact"]').count() == 1)
    p.locator('[data-act="sendcontact"]').last.click()
    p.wait_for_timeout(700)
    log = p.locator("#chatlog .msg.bot").last.inner_text()
    check("sends it to the team contact", "Sent." in log and "Vikram Chandra" in log, log[:160])
    check("is honest that no process covers it", "No request type covers this" in log,
          log[:200])
    # The recipient gets the need, not the routing question wrapped round it.
    check("titles it with what was actually asked for", "get my laptop fixed" in log
          and "who do i need to contact" not in log.lower(), log[:220])

    for question, team, who in [
        ("my chair is broken", "Operations / HR", "Claire Donovan"),
        ("who handles payroll", "Finance", "Karim El-Masri"),
        ("i think i got a phishing email", "IT", "Vikram Chandra"),
        ("who do i contact about a sanctions check", "Legal & Compliance", "Nadia Suleiman"),
    ]:
        log = reply(question)
        check(f"{question!r} reaches {who}", team in log and who in log, log[:140])

    log = reply("who owns invoice approval?")
    check("a real process still beats the team fallback", "Rania Khoury" in log, log[:140])

    reply("where is the coffee machine")
    tail = p.inner_text("#chatlog")[-700:]
    check("a genuine blank stays a blank", "couldn't match" in tail, tail[:160])

    p.select_option('[data-act="actor"]', label="Noura Al-Sabah")
    p.wait_for_timeout(700)

    # ------------------------------------------------------------ org chart
    section("org chart — layout")
    tab(p, "People")
    p.wait_for_timeout(600)
    m = p.evaluate("""() => { const e = document.querySelector('#orgscroll').getBoundingClientRect();
        return {w: e.width, h: e.height, vw: window.innerWidth, vh: window.innerHeight}; }""")
    check("spans the canvas width", m["w"] > (m["vw"] - 288) * 0.93, f"{m['w']:.0f}px")
    check("fills most of the height", m["h"] > m["vh"] * 0.7, f"{m['h']:.0f}px")
    check("opens folded to the teams", len(names(p)) == 6, f"{len(names(p))} cards")
    fit = p.evaluate("""() => {
        const box = document.getElementById('orgscroll');
        const svg = document.getElementById('treesvg');
        const r = svg.getBoundingClientRect(), b = box.getBoundingClientRect();
        return {left: r.left - b.left, right: b.right - r.right,
                top: r.top - b.top, bottom: b.bottom - r.bottom}; }""")
    # The chart is centred in the stage rather than pinned to a corner.
    check("centred horizontally", abs(fit["left"] - fit["right"]) < 4,
          f"{fit['left']:.0f} vs {fit['right']:.0f}")
    check("centred vertically", abs(fit["top"] - fit["bottom"]) < 4,
          f"{fit['top']:.0f} vs {fit['bottom']:.0f}")

    section("org chart — search suggestions")
    before = names(p)
    box = p.locator('[data-act="treequery"]')
    box.click(); box.type("Lay", delay=55); p.wait_for_timeout(500)
    check("a suggestion list opens", p.locator("#suggestbox .sug").count() >= 1)
    check("suggestions name the person and role",
          "Layla Mansour" in p.inner_text("#suggestbox")
          and "Senior Associate" in p.inner_text("#suggestbox"))
    check("the chart does not move while typing", before == names(p))
    p.locator("#suggestbox .sug").first.click(); p.wait_for_timeout(1100)
    check("picking focuses that person", "Layla Mansour" in names(p))
    check("everyone above is hidden", "Khalid Al-Rayes" not in names(p))
    check("the list closes", p.locator("#suggestbox .sug").count() == 0)
    check("the box keeps the chosen name",
          p.locator('[data-act="treequery"]').input_value() == "Layla Mansour")
    pos = p.evaluate("""() => { const s = document.querySelector('.onode.sel .obox').getBoundingClientRect();
        const st = document.querySelector('#orgscroll').getBoundingClientRect();
        return {dx: Math.abs((s.left+s.width/2)-(st.left+st.width/2)), w: st.width}; }""")
    check("the person lands mid-page", pos["dx"] < pos["w"] * 0.2, f"{pos['dx']:.0f}px off centre")

    section("org chart — keyboard")
    box = p.locator('[data-act="treequery"]')
    box.click(); box.fill(""); box.type("Hud", delay=55); p.wait_for_timeout(500)
    p.keyboard.press("ArrowDown"); p.wait_for_timeout(200)
    check("arrow keys move the highlight", p.locator("#suggestbox .sug.on").count() == 1)
    p.keyboard.press("Enter"); p.wait_for_timeout(1000)
    check("enter selects the highlighted person", "Huda Al-Najjar" in names(p))
    box = p.locator('[data-act="treequery"]')
    box.click(); box.type("z", delay=50); p.wait_for_timeout(400)
    p.keyboard.press("Escape"); p.wait_for_timeout(300)
    check("escape closes the list", p.locator("#suggestbox .sug").count() == 0)

    section("org chart — climbing back up")
    up = p.get_by_role("button", name="Up to", exact=False).first
    check("the up button names the manager", "Amira Haddadin" in up.inner_text(), up.inner_text())
    up.click(); p.wait_for_timeout(900)
    check("the manager appears", "Amira Haddadin" in names(p))
    for _ in range(4):
        btn = p.get_by_role("button", name="Up to", exact=False)
        if btn.count() == 0:
            break
        btn.first.click(); p.wait_for_timeout(700)
    check("climbing reaches the top", "Khalid Al-Rayes" in names(p))
    p.get_by_role("button", name="Show whole firm").first.click(); p.wait_for_timeout(900)
    check("reset clears the focus", p.locator(".focusbar.on").count() == 0)

    section("org chart — zoom and fold")
    p.get_by_role("button", name="Expand all").click(); p.wait_for_timeout(1000)
    check("expanding shows all 40", len(names(p)) == 40, f"{len(names(p))} cards")
    z0 = int(p.inner_text(".zoomv").rstrip("%"))
    stage = p.locator("#orgscroll").bounding_box()
    p.mouse.move(stage["x"] + stage["width"] / 2, stage["y"] + stage["height"] / 2)
    p.mouse.wheel(0, -300); p.wait_for_timeout(400)
    z1 = int(p.inner_text(".zoomv").rstrip("%"))
    check("scrolling up zooms in", z1 > z0, f"{z0}% -> {z1}%")
    p.mouse.wheel(0, 600); p.wait_for_timeout(400)
    check("scrolling down zooms out", int(p.inner_text(".zoomv").rstrip("%")) < z1)
    # With the chart larger than the stage there is scroll to preserve, so the
    # point under the cursor must stay put.
    p.mouse.wheel(0, -600); p.wait_for_timeout(400)
    overflows = p.evaluate("""() => { const b=document.getElementById('orgscroll');
        return b.scrollWidth > b.clientWidth + 20; }""")
    if overflows:
        b4 = p.evaluate("""() => { const n=document.querySelector('.onode .obox').getBoundingClientRect();
            return {x:n.left+n.width/2, y:n.top+n.height/2}; }""")
        p.mouse.move(b4["x"], b4["y"]); p.mouse.wheel(0, -240); p.wait_for_timeout(400)
        af = p.evaluate("""() => { const n=document.querySelector('.onode .obox').getBoundingClientRect();
            return {x:n.left+n.width/2, y:n.top+n.height/2}; }""")
        drift = max(abs(af["x"] - b4["x"]), abs(af["y"] - b4["y"]))
        check("zoom stays anchored at the cursor", drift < 30, f"{drift:.0f}px drift")
    else:
        check("zoom stays anchored at the cursor", True, "chart fits, nothing to anchor")
    p.get_by_role("button", name="Collapse", exact=False).first.click(); p.wait_for_timeout(900)
    check("collapse folds back to the teams", len(names(p)) <= 8, f"{len(names(p))} cards")

    section("org chart — detail panel")
    p.locator('g[data-act="treeselect"]').nth(1).click(); p.wait_for_timeout(700)
    panel = p.inner_text(".orgpanel")
    check("shows who they report to", "Reports to" in panel)
    check("shows what they own", "Owns" in panel)
    for gone in ["Avg turnaround", "Approver", "Delegate", "Backup", "Reporting line"]:
        check(f"no longer shows '{gone}'", gone not in panel)
    check("stays short", len([l for l in panel.split("\n") if l.strip()]) <= 12)

    # -------------------------------------------------- hover card & chain
    section("org chart — hover card")
    p.get_by_role("button", name="Expand all").click(); p.wait_for_timeout(1000)
    node = p.locator('g[data-act="treeselect"]').nth(6)
    node.hover(); p.wait_for_timeout(650)
    check("a hover card appears", p.locator("#hovercard").is_visible())
    hc = p.inner_text("#hovercard")
    check("hover card names who they report to", "Reports to" in hc)
    check("hover card shows what they own", "Owns" in hc)
    check("hover card offers a request action", "Ask them for something" in hc)
    check("hovering lights the chain of command", p.locator(".onode.chain").count() >= 2,
          f"{p.locator('.onode.chain').count()} in chain")
    check("everyone off the chain is muted", p.locator(".onode.faded").count() > 10)
    p.mouse.move(10, 10); p.wait_for_timeout(600)
    check("card hides on leaving", not p.locator("#hovercard").is_visible())
    check("highlight clears", p.locator(".onode.chain").count() == 0)

    # ------------------------------------------------- request from a person
    section("request straight from the chart")
    node = p.locator('g[data-act="treeselect"]').nth(6)
    node.hover(); p.wait_for_timeout(650)
    who = p.evaluate("""() => document.querySelector('#hovercard strong').textContent""")
    p.locator('#hovercard [data-act="askperson"]').click(); p.wait_for_timeout(1000)
    log = p.inner_text("#chatlog")
    check("jumps to the chat scoped to that person", who in log, who)
    chips = p.locator('[data-act="askproc"]')
    if chips.count():
        want = chips.first.inner_text().strip()
        chips.first.click(); p.wait_for_timeout(1000)
        check("picking a request type drafts it",
              p.locator('[data-act="dbody"]').count() == 1)
        check("the draft is for that request type", want in p.inner_text("#chatlog"), want)
        p.locator('[data-act="chatsend"]').click(); p.wait_for_timeout(900)
        check("it can be sent", "Sent." in p.inner_text("#chatlog"))
    else:
        check("explains when they own nothing", "doesn" in log.lower())

    # --------------------------------------------------- momentum pan
    section("org chart — a flick keeps coasting")
    tab(p, "People")
    p.wait_for_timeout(700)
    for _ in range(7):
        p.locator('[data-act="zoom"][data-d="1"]').click(); p.wait_for_timeout(100)
    start = p.evaluate("""() => {
      const b = document.getElementById('orgscroll').getBoundingClientRect();
      for (let y = b.top+30; y < b.bottom-40; y += 40)
        for (let x = b.left+260; x < b.right-260; x += 60) {
          const el = document.elementFromPoint(x, y);
          if (el && el.closest('#orgscroll') && !el.closest('g[data-act]')) return [x, y];
        }
      return [b.left+b.width/2, b.top+40];
    }""")
    before = p.evaluate("() => document.getElementById('orgscroll').scrollLeft")
    p.mouse.move(start[0]+180, start[1]); p.mouse.down()
    for i in range(6):
        p.mouse.move(start[0]+180-i*55, start[1], steps=1); p.wait_for_timeout(12)
    p.mouse.up()
    released = p.evaluate("() => document.getElementById('orgscroll').scrollLeft")
    p.wait_for_timeout(700)
    settled = p.evaluate("() => document.getElementById('orgscroll').scrollLeft")
    check("drag tracks the pointer", released > before, f"{before} -> {released}")
    check("release hands velocity to a glide", settled > released + 20,
          f"{released} -> {settled}")

    # ------------------------------------------------------------- chrome
    section("layout")
    check("the left panel is gone", p.locator(".rail").count() == 0)
    check("identity lives in the header", p.locator(".topbar .who select").count() == 1)
    check("no clock controls outside the demo page",
          p.locator('.topbar [data-act="adv"]').count() == 0)

    section("hover card matches the zoom")
    tab(p, "People"); p.wait_for_timeout(700)
    p.get_by_role("button", name="Expand all").click(); p.wait_for_timeout(900)
    def ratio():
        p.locator('g[data-act="treeselect"]').nth(5).hover(); p.wait_for_timeout(650)
        r = p.evaluate("""() => { const c=document.getElementById('hovercard').getBoundingClientRect();
            const n=document.querySelectorAll('.onode .obox')[5].getBoundingClientRect();
            return c.width / n.width; }""")
        p.mouse.move(4, 4); p.wait_for_timeout(350)
        return r
    r_start = ratio()
    for _ in range(4):
        p.get_by_role("button", name="Zoom out").click(); p.wait_for_timeout(110)
    r_out = ratio()
    for _ in range(9):
        p.get_by_role("button", name="Zoom in").click(); p.wait_for_timeout(110)
    r_in = ratio()
    check("card stays proportional to the nodes", max(r_start, r_out, r_in) -
          min(r_start, r_out, r_in) < 0.1,
          f"ratios {r_start:.2f} / {r_out:.2f} / {r_in:.2f}")

    # ---------------------------------------------------------- other pages
    section("other pages")
    tab(p, "People"); p.wait_for_timeout(500)
    p.get_by_role("tab", name="Teams", exact=False).first.click(); p.wait_for_timeout(800)
    t = p.inner_text("#page")
    check("teams lists every department", all(d in t for d in
          ["Investments / Deal Team", "Finance", "Legal & Compliance", "IT", "Operations / HR"]))
    section("navigation")
    n_primary = p.evaluate(
        "[...document.querySelectorAll('.tabs')][0].querySelectorAll('.tab:not(.more)').length")
    check("only three primary tabs", n_primary == 3, f"{n_primary} tabs")
    p.locator('[data-act="moretoggle"]').click(); p.wait_for_timeout(450)
    check("More opens a menu", p.locator(".moremenu button").count() == 5)
    for label, probe in [("What you can ask for", "What you can ask for"),
                         ("Dashboard", "Where work is stuck"),
                         ("Agent log", "What the agent did"),
                         ("Demo controls", "Demo controls"),
                         ("Guide", "How Atlas works")]:
        if p.locator(".moremenu").count() == 0:
            p.locator('[data-act="moretoggle"]').click(); p.wait_for_timeout(400)
        p.locator(".moremenu button", has_text=label).first.click(); p.wait_for_timeout(900)
        check(f"{label} renders", probe in p.inner_text("#page"))
    p.locator('[data-act="moretoggle"]').click(); p.wait_for_timeout(400)
    p.locator(".moremenu button", has_text="What you can ask for").first.click()
    p.wait_for_timeout(800)
    n_proc = p.locator("#page .rowline").count()
    check("catalogue is trimmed to 8", n_proc == 8, f"{n_proc} request types")
    p.locator('[data-act="moretoggle"]').click(); p.wait_for_timeout(400)
    p.locator(".moremenu button", has_text="Dashboard").first.click(); p.wait_for_timeout(900)
    check("dashboard charts draw", p.locator(".chart svg").count() >= 4)

    # ------------------------------------------- chat scroll is not animated
    section("chat scroll stays put")
    tab(p, "Ask"); p.wait_for_timeout(500)
    log = p.locator(".chatlog")
    check("no smooth-scroll on the chat log",
          log.evaluate("el => getComputedStyle(el).scrollBehavior") == "auto")
    log.evaluate("el => el.scrollTop = 0"); p.wait_for_timeout(150)
    p.locator('[data-act="moretoggle"]').click(); p.wait_for_timeout(500)
    kept = p.locator(".chatlog").evaluate("el => el.scrollTop")
    check("an unrelated click leaves the scroll position alone", kept < 10, f"scrollTop={kept}")
    p.locator('[data-act="moretoggle"]').click(); p.wait_for_timeout(300)

    # ------------------------------------------------------ assignment toast
    section("assignment toast")
    check("boot skeleton shipped and was replaced",
          p.evaluate("document.querySelector('.skel')") is None)
    p.locator('select[data-act="actor"]').select_option(label="Anna Sorenson")
    p.wait_for_timeout(400)
    p.locator('[data-act="moretoggle"]').click(); p.wait_for_timeout(400)
    p.locator(".moremenu button", has_text="Demo controls").first.click(); p.wait_for_timeout(700)
    got = False
    for _ in range(8):
        p.locator('[data-act="adv"][data-h="48"]').click(); p.wait_for_timeout(500)
        if p.locator("#notify .notif").count():
            got = True; break
    check("a request routed to you raises a toast", got)
    if got:
        body = p.locator("#notify .notif").first.inner_text().lower()
        check("the toast announces itself", "new request for you" in body)
        rid = re.search(r"#(\d+)", p.locator("#notify .notif").first.inner_text())
        check("the toast names the request", rid is not None)
        p.locator("#notify .notif .n-open").first.click(); p.wait_for_timeout(800)
        check("Open lands on the request",
              p.locator('.tab[data-page="requests"][aria-selected="true"]').count() == 1
              and (rid is None or f"#{rid.group(1)}" in p.inner_text("#page")))
        check("Open clears the toast", p.locator("#notify .notif").count() == 0)

    # --------------------------------------------------------- persistence
    section("persistence")
    p.reload(wait_until="load"); p.wait_for_timeout(1900)
    check("the guide does not reopen", p.locator(".modal").count() == 0)
    tab(p, "Ask")
    check("chat history survives a reload", "Data Room Access" in p.inner_text("#chatlog"))


with sync_playwright() as pw:
    browser = launch(pw)
    page = browser.new_page(viewport={"width": 1500, "height": 1000})
    page.on("pageerror", lambda e: fails.append(f"PAGEERROR: {e}"))
    run(page)

    section("dark mode")
    dark = browser.new_page(viewport={"width": 1500, "height": 1000}, color_scheme="dark")
    dark.on("pageerror", lambda e: fails.append(f"PAGEERROR (dark): {e}"))
    dark.goto(PAGE.as_uri(), wait_until="load", timeout=45000)
    dark.wait_for_timeout(1800)
    bg = dark.evaluate("getComputedStyle(document.body).backgroundColor")
    check("the page paints a dark ground", bg not in ("rgba(0, 0, 0, 0)", "rgb(251, 248, 240)"), bg)
    dark.get_by_role("button", name="Close the guide").click()
    dark.wait_for_timeout(400)
    dark.get_by_role("tab", name="People", exact=False).first.click()
    dark.wait_for_timeout(1200)
    card = dark.evaluate("getComputedStyle(document.querySelector('.onode .obox')).fill")
    check("org cards use the dark surface", card not in ("rgb(255, 255, 255)",), card)
    browser.close()

print("\n" + "=" * 60)
print("FAILED:" , fails if fails else "none — the preview behaves as specified")
sys.exit(1 if fails else 0)
