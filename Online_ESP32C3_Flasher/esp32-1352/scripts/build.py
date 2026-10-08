"""Build, package and checksum a complete classic ESP32 image; never flash."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, "-m", "platformio", "run", "-e", "esp32dev"],
               cwd=root, check=True)
subprocess.run([sys.executable, "-m", "platformio", "run", "-e", "esp32dev", "-t", "buildfs"],
               cwd=root, check=True)
build = root / ".pio/build/esp32dev"
out = root / "artifacts"
out.mkdir(exist_ok=True)
core = Path(os.environ.get("PLATFORMIO_CORE_DIR", str(Path.home() / ".platformio")))
boot_app = core / "packages/framework-arduinoespressif32/tools/partitions/boot_app0.bin"
for name in ("firmware.bin", "bootloader.bin", "partitions.bin", "littlefs.bin"):
    shutil.copy2(build / name, out / name)
shutil.copy2(boot_app, out / "boot_app0.bin")
shutil.copy2(root / "generated/asset-manifest.json", out / "asset-manifest.json")
subprocess.run([
    sys.executable, "-m", "esptool", "--chip", "esp32", "merge-bin",
    "--output", str(out / "esp32-1352-merged.bin"),
    "--flash-mode", "dio", "--flash-freq", "40m", "--flash-size", "4MB",
    "0x1000", str(out / "bootloader.bin"),
    "0x8000", str(out / "partitions.bin"),
    "0xe000", str(out / "boot_app0.bin"),
    "0x10000", str(out / "firmware.bin"),
    "0x210000", str(out / "littlefs.bin"),
], check=True)
files = sorted([*out.glob("*.bin"), out / "asset-manifest.json"])
(out / "SHA256SUMS").write_text("".join(
    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in files))
print(f"Packaged firmware and checksums in {out}; device flash was not written.")
