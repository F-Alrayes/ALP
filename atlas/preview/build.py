"""Assemble the Atlas preview into one self-contained HTML file."""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "atlas-preview.html"

shell = (HERE / "shell.html").read_text()
engine = (HERE / "atlas_engine.js").read_text()
seed = json.loads((HERE / "seed.json").read_text())
ui = "".join((HERE / f"ui_{i}.js").read_text() for i in range(1, 6))

# </script> inside a string literal would close the block early.
seed_js = json.dumps(seed, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")

html = shell + "\n<script>\n" + \
    "const SEED = " + seed_js + ";\n" + \
    engine + "\n" + ui + "\n</script>\n"

OUT.write_text(html)
print(f"built {OUT}  {len(html):,} bytes")
for name, blob in (("shell", shell), ("seed", seed_js), ("engine", engine), ("ui", ui)):
    print(f"   {name:7} {len(blob):>9,}")
