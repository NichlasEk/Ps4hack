# Classic ESP32 host for PS4 13.52

Local port for the connected ESP32-D0WD-V3 rev 3.1, with 4 MB flash and a
CP2102 USB UART at `/dev/ttyUSB0`.

The port serves unchanged `/1302-1352/` web assets extracted from this
repository's `goldhen24b1812` C3 image. The HTTP/DNS/AP firmware is compiled
for the classic Xtensa ESP32; no C3 executable code is reused.

## Current physical status

The current diagnostic build was flashed and hash verified on 2026-10-08.
It reached `ESP32 13.52 host ready` on three reset/start cycles, each observed
for 20 seconds without a panic or watchdog reboot. All 15 files were found
on LittleFS. The ready log reported 248284 bytes of free heap.

Earlier builds reset during Wi-Fi initialization. A minimal Wi-Fi-only
probe passed, while several full-host variants failed. The current build
retains linker wrappers that log entry/exit from four Wi-Fi initialization
functions. It started successfully after adding those wrappers; **the root
cause has not been established**. Logging changes timing and code layout,
so these three successful starts are not proof of a general fix or long-term
stability. Keep this diagnostic build and its logs for further testing.

`serial-user-test-1.log` additionally records Android station association,
DHCP assignment and HTTP requests for the captive-portal probe and landing
page. The user subsequently confirmed that Android rendered the unsupported
console/firmware message; the page checks for a PS4 user-agent, so this is
expected on Android. `serial-user-test-3.log` records those requests.
The user subsequently reported successful PS4 execution on 2026-10-08 after
initial trouble. No usable serial capture of that PS4 run is available;
the report does not establish the cause of the earlier failures. See
`artifacts/validation.txt` and the serial logs for the latest recorded results.

## Network

- SSID: `ESP32_Xploithost`
- Password: `password`
- Address: `http://192.168.1.1`
- Landing page: `/1302-1352/index.html`

Wildcard DNS and User's Guide/captive-portal redirects are enabled. The
server streams compressed assets from LittleFS and sends `Content-Encoding:
gzip` exactly once, including for binary patches and payloads. Query strings
such as `core.js?v=10` use the same route. Missing resources within the host
path return 404, rather than HTML that might be incorrectly cached.

## Build and package

From this directory:

```sh
/home/nichlas/Ps4hack/.venv/bin/python scripts/build.py
```

PlatformIO pins `espressif32@6.12.0` (Arduino ESP32 2.0.17), `esp32dev`, DIO
40 MHz flash, 160 MHz CPU, 4 MB flash, and the no-OTA partition layout. The
application partition is 2 MB; LittleFS occupies 0x1e0000 bytes at 0x210000.
The build extracts and checks the assets, builds both images and creates
`artifacts/esp32-1352-merged.bin` plus `SHA256SUMS`. Building does not flash.

The input C3 image is pinned to SHA-256
`5d78672507ea2dd006c0b44787c0d475561ba2b6d4107f18d040d018f7e37b42`, from upstream
commit `0b128df3e13fd463797a679bfbcfdaf8b87da7c8`. Audited gzip offsets, gzip
filenames and checksums guard extraction. `generated/asset-manifest.json`
records exact offsets, sizes and decompressed SHA-256 hashes. Assets unpacked
from the resulting LittleFS image were compared byte-for-byte with upstream.
Three patch hashes in upstream's appcache comments are stale; the actual
upstream patch bytes are preserved and their real hashes are recorded.

## Flash

Close any browser/serial monitor using the port. The complete merged image
is written at **0x0**, and includes both firmware and LittleFS:

```sh
/home/nichlas/Ps4hack/.venv/bin/esptool --chip esp32 --port /dev/ttyUSB0 --baud 115200 \
  write-flash 0x0 artifacts/esp32-1352-merged.bin
```

Component offsets are bootloader 0x1000, partitions 0x8000, boot_app0 0xe000,
application 0x10000, and LittleFS 0x210000. The tested final build was written
using those component offsets. Use 115200 baud: higher-speed reads stalled
on this connection. The user confirmed the device was empty and requested
skipping the full backup; partial reads are not a complete recovery image.

## Serial logging

```sh
/home/nichlas/Ps4hack/.venv/bin/python scripts/monitor.py --duration 60
```

This saves a timestamped raw log under `artifacts/` and displays it live.
Add `--reset` only when a deliberate reset/start capture is wanted. The port
is locked exclusively while monitoring. If a long-running shell predates
the user's membership in `uucp`, start a fresh login session or use `newgrp
uucp` to activate that group.

Relevant evidence:

- `boot-wifi-probe.log`: minimal Wi-Fi-only control passed.
- `boot-wifi-trace.log`, `boot-wifi-trace-2.log`, `boot-wifi-trace-3.log`:
  three successful starts of the full host with diagnostic wrappers.
- `flash-wifi-trace.log`: current application/bootloader writes verified.
- `flash-littlefs.log`: filesystem write verified.
- `serial-user-test-*.log`: subsequent wireless/request observations, if any.

Build artifacts, extracted assets, logs and partial backups are ignored by Git.
