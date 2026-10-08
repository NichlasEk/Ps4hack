"""Fetch the exact upstream input; do not redistribute extracted payloads."""
import hashlib
from urllib.request import urlopen
from extract_assets import IMAGE, IMAGE_SHA256

URL = ("https://raw.githubusercontent.com/may0need5/Online_ESP32C3_Flasher/"
       "0b128df3e13fd463797a679bfbcfdaf8b87da7c8/"
       "goldhen24b1812/bins/ESP32C3_XploitHost_600-1352.ino.bin")


def main():
    if IMAGE.exists():
        data = IMAGE.read_bytes()
    else:
        with urlopen(URL, timeout=60) as response:
            data = response.read()
    if hashlib.sha256(data).hexdigest() != IMAGE_SHA256:
        raise SystemExit("Upstream image hash mismatch; refusing to use it")
    IMAGE.parent.mkdir(parents=True, exist_ok=True)
    if not IMAGE.exists():
        IMAGE.write_bytes(data)
    print("Verified pinned upstream input:", IMAGE)


if __name__ == "__main__":
    main()
