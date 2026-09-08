"""Assemble the Atlas preview into one self-contained HTML file."""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "atlas-preview.html"

shell = (HERE / "shell.html").read_text()

# Inline the fonts so the page stays a single offline file — the same promise
# the Python app makes. Latin subsets only; ~130KB before base64.
FACES = [
    ("Fraunces", "normal", "100 900", "fraunces-latin-wght-normal.woff2"),
    ("Fraunces", "italic", "100 900", "fraunces-latin-wght-italic.woff2"),
    ("Instrument Sans", "normal", "400 700", "instrument-sans-latin-wght-normal.woff2"),
    ("Instrument Sans", "italic", "400 700", "instrument-sans-latin-wght-italic.woff2"),
    ("IBM Plex Mono", "normal", "400", "ibm-plex-mono-latin-400-normal.woff2"),
    ("IBM Plex Mono", "normal", "600", "ibm-plex-mono-latin-600-normal.woff2"),
]
import base64
rules = []
for family, style, weight, fname in FACES:
    blob = base64.b64encode((HERE / "fonts" / fname).read_bytes()).decode()
    rules.append(
        "@font-face{font-family:'" + family + "';font-style:" + style +
        ";font-weight:" + weight + ";font-display:swap;" +
        "src:url(data:font/woff2;base64," + blob + ") format('woff2');}"
    )
fonts_css = "\n".join(rules)
marker = "/*__FONTS__*/"
if marker not in shell:
    raise SystemExit("ERROR: shell.html is missing the " + marker + " marker")
shell = shell.replace(marker, fonts_css, 1)
engine = (HERE / "atlas_engine.js").read_text()
seed = json.loads((HERE / "seed.json").read_text())
# Discover the ui_*.js parts in numeric order, so adding one needs no edit here.
ui_parts = sorted(HERE.glob("ui_*.js"), key=lambda f: int(f.stem.split("_")[1]))
ui = "".join(f.read_text() for f in ui_parts)

# </script> inside a string literal would close the block early.
seed_js = json.dumps(seed, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")

html = shell + "\n<script>\n" + \
    "const SEED = " + seed_js + ";\n" + \
    engine + "\n" + ui + "\n</script>\n"

OUT.write_text(html)
print(f"built {OUT}  {len(html):,} bytes")
for name, blob in (("shell", shell), ("seed", seed_js), ("engine", engine), ("ui", ui)):
    print(f"   {name:7} {len(blob):>9,}")
print("   ui parts:", ", ".join(f.name for f in ui_parts))

# A script that does not close its own braces silently truncates in the browser.
if html.count("</script") != 1:
    raise SystemExit("ERROR: unbalanced </script> in the assembled page")
