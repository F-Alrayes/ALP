#!/usr/bin/env python3
"""End-to-end regression suite for the Atlas browser preview.

    pip install playwright && playwright install chromium
    python3 test_preview.py [path/to/atlas-preview.html]

Drives the built page in a real browser and checks the behaviour that matters:
the first-run guide, the chat flow, the org chart (full-bleed layout, search
suggestions, focus, zoom, collapse), the other pages, persistence across a
reload, and dark mode. Exits non-zero on any failure.
"""
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
    p.get_by_role("button", name="Send it").click()
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
    check("answers for help", "raise a request" in ask("help").lower())
    check("password requests route to IT access",
          "IT Access Provisioning" in ask("I am locked out of my account"))

    # ------------------------------------------------------------ org chart
    section("org chart — layout")
    tab(p, "People")
    p.wait_for_timeout(600)
    m = p.evaluate("""() => { const e = document.querySelector('#orgscroll').getBoundingClientRect();
        return {w: e.width, h: e.height, vw: window.innerWidth, vh: window.innerHeight}; }""")
    check("spans the canvas width", m["w"] > (m["vw"] - 288) * 0.93, f"{m['w']:.0f}px")
    check("fills most of the height", m["h"] > m["vh"] * 0.7, f"{m['h']:.0f}px")
    check("opens folded to the teams", len(names(p)) == 6, f"{len(names(p))} cards")

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

    # ---------------------------------------------------------- other pages
    section("other pages")
    tab(p, "Teams")
    t = p.inner_text("#page")
    check("teams lists every department", all(d in t for d in
          ["Investments / Deal Team", "Finance", "Legal & Compliance", "IT", "Operations / HR"]))
    tab(p, "Processes")
    check("catalogue is trimmed to 8", p.locator("#page .rowline").count() == 8,
          f"{p.locator('#page .rowline').count()}")
    for name, probe in [("Requests", "desk"), ("Agent Log", "What the agent did"),
                        ("Dashboard", "Where work is actually stuck"), ("Guide", "How to drive Atlas")]:
        tab(p, name)
        check(f"{name} renders", probe in p.inner_text("#page"))
    tab(p, "Dashboard")
    p.wait_for_timeout(700)
    check("dashboard charts draw", p.locator(".chart svg").count() >= 4)

    # --------------------------------------------------------- persistence
    section("persistence")
    p.reload(wait_until="load"); p.wait_for_timeout(1900)
    check("the guide does not reopen", p.locator(".modal").count() == 0)
    tab(p, "Ask Atlas")
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
