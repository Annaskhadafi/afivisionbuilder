import sys
import os
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("engine"))

import server

templates = server._templates()
print(f"Total templates: {len(templates)}")
for i, t in enumerate(templates):
    wf = t.get("workflow", {})
    input_node = next((n for n in wf.get("nodes", []) if n.get("type") in ("input", "ip_camera")), None)
    cfg = input_node.get("config", {}) if input_node else {}
    stype = cfg.get("sourceType", "none")
    yt = cfg.get("youtubeUrl") or cfg.get("streamUrl", "")
    tid = t.get("id")
    name = t.get("name")
    print(f"{i+1:2d}. {tid:<32} | {stype:<8} | {yt:<40} | {name}")
