"""Extract the original CSSFontFace/Lapse bundle from the pinned C3 image.

Offsets were matched byte-for-byte against XiaoESP32C3-CSSFontFace-Xploithost
commit 82a700f9c916ee281d771743d09e1aa56822e6b1 headers for scripts and patches.
The remaining page, cache, UI and payload members come from the pinned image.
"""
import hashlib
import json
from pathlib import Path
import sys
import zlib

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'esp32-1352/scripts'))
from extract_assets import IMAGE, IMAGE_SHA256

MEMBERS = {
    'index.html': 0x11e9cc,
    'cache.manifest': 0x11f288,
    'includes/script.js': 0x10cce8,
    'includes/style.css': 0x10ca8c,
    'src/payload.bin': 0x120,
    'src/lapse.js': 0x10aa1c,
    'src/loader.js': 0x10a720,
    'src/main.js': 0x10a2ec,
    'src/misc.js': 0x10982c,
    'src/netctrl.js': 0x1084a4,
    'src/worker.js': 0x1081dc,
    'src/workers.js': 0x107ecc,
    'src/ps4/constants.js': 0x106f68,
    'src/ps4/kernel.js': 0x106050,
    'src/ps4/userland.js': 0x103e74,
}
PATCHES = {
    600: 0x103d8c, 620: 0x103ca4, 650: 0x103ba0, 670: 0x103a98,
    700: 0x10393c, 750: 0x103788, 800: 0x1035e0, 850: 0x103438,
    900: 0x103294, 903: 0x1030ec, 950: 0x102f40, 1000: 0x102d94,
    1050: 0x102bd0, 1100: 0x102a00, 1102: 0x10283c,
}
MEMBERS.update({f'src/ps4/patches/{fw}.bin': offset for fw, offset in PATCHES.items()})


def extract():
    image = IMAGE.read_bytes()
    if hashlib.sha256(image).hexdigest() != IMAGE_SHA256:
        raise ValueError('Upstream image hash mismatch')
    records = []
    raw_files = {}
    for path, offset in MEMBERS.items():
        decoder = zlib.decompressobj(31)
        raw = decoder.decompress(image[offset:])
        if not decoder.eof:
            raise ValueError(f'Truncated gzip: {path}')
        packed = image[offset:len(image) - len(decoder.unused_data)]
        dest = ROOT / 'generated-960' / (path + '.gz')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(packed)
        raw_files[path] = raw
        records.append(dict(route='/960/' + path, offset=offset, bytes=len(raw),
                            compressed_bytes=len(packed), sha256=hashlib.sha256(raw).hexdigest()))
    cache = raw_files['cache.manifest'].decode().split('CACHE:\n', 1)[1].split('NETWORK:', 1)[0]
    references = {line.strip() for line in cache.splitlines() if line.strip()}
    if references != set(MEMBERS) - {'cache.manifest'}:
        raise ValueError('Cache manifest and extracted routes disagree')
    # In this original bundle 9.60 inherits the 9.50 kernel patch constants.
    if b'KPATCH: "950.bin"' not in raw_files['src/ps4/constants.js']:
        raise ValueError('Expected 9.50/9.60 patch mapping')
    (ROOT / 'generated-960/asset-manifest.json').write_text(json.dumps(
        dict(source_sha256=IMAGE_SHA256, assets=records), indent=2) + '\n')
    print(f'Extracted and verified {len(records)} assets for the 9.60 host')


if __name__ == '__main__':
    extract()
