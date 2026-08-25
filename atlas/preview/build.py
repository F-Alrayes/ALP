"""Assemble the Atlas preview into one self-contained HTML file."""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "atlas-preview.html"

shell = (HERE / "shell.html").read_text()
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
