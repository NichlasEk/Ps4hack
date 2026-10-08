"""Check offline cache completeness and JS imports before compiling."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

root = Path(__file__).resolve().parents[1] / "generated"
records = json.loads((root / "asset-manifest.json").read_text())["assets"]
count = 0
for line in (root / "cache.appcache").read_text().splitlines():
    if (not line or line == "CACHE MANIFEST" or line.startswith("#")
            or line.endswith(":") or line == "*"):
        continue
    for url in line.split(" #")[0].split():
        if not (root / urlsplit(url).path).is_file():
            raise ValueError(f"Missing appcache resource: {url}")
        count += 1
for file in root.glob("*.js"):
    for ref in re.findall(r'''(?:from\s*|import\s*|new Worker\(\s*)["']([^"']+)["']''',
                          file.read_text()):
        if not (root / urlsplit(ref).path).is_file():
            raise ValueError(f"Missing JS dependency: {file.name}: {ref}")
offsets = (root / "ps4_offsets.js").read_text()
if 'PS4["13.52"]' not in offsets:
    raise ValueError("Missing 13.52 offsets")
for record in records:
    path = root / record["route"].removeprefix("/1302-1352/")
    if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
        raise ValueError(f"Modified asset: {path}")
print(f"PASS: {len(records)} asset hashes, {count} appcache references, "
      "module/worker imports, 13.52 offsets present")
