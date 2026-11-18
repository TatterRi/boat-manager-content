"""Build preview.html: every type, outline and zones, with the app-drawn labels. Open in a browser."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
m = json.load(open(os.path.join(HERE, "boat-outlines.json")))
rows = []
for t in m["types"]:
    svg = open(os.path.join(HERE, t["zonesImage"])).read()
    out = open(os.path.join(HERE, t["outline"])).read()
    vb = svg.split('viewBox="')[1].split('"')[0].split()
    w, h = float(vb[2]), float(vb[3])
    labels = "".join(
        f'<text x="{z["label"][0]*w:.1f}" y="{z["label"][1]*h:.1f}">{z["name"]}</text>' for z in t["zones"])
    zsvg = svg.replace("</svg>", f'<g class="lbl">{labels}</g></svg>')
    rows.append(f'<section><h2>{t["name"]} <code>{t["id"]}</code></h2><p>{t["description"]}</p>'
                f'<div class="pair"><figure>{out}<figcaption>-outline.svg</figcaption></figure>'
                f'<figure>{zsvg}<figcaption>-zones.svg + app labels</figcaption></figure></div></section>')
html = f"""<!doctype html><meta charset="utf-8"><title>Boat outlines</title>
<style>body{{font:14px -apple-system,Helvetica,sans-serif;margin:24px 40px;background:#fff;color:#111}}
h2{{font-size:16px;margin:28px 0 2px}} p{{margin:0 0 8px;color:#555}} code{{font-size:12px;color:#777}}
.pair{{display:grid;grid-template-columns:1fr 1fr;gap:20px}} figure{{margin:0}}
svg{{width:100%;height:auto;overflow:visible}} figcaption{{font-size:11px;color:#888}}
.lbl text{{font-size:12px;text-anchor:middle;dominant-baseline:middle;fill:#0a58ca;stroke:none;paint-order:stroke}}
</style><h1>Boat Map — generic outlines</h1><p>{m["orientation"]}</p>{"".join(rows)}"""
open(os.path.join(HERE, "preview.html"), "w").write(html)
