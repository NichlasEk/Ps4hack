# Ps4hack

Classic ESP32 (ESP32-D0WD-V3, 4 MB) conversion of a PS4 13.52 web host,
plus a Python LAN host with persistent telemetry.

- [ESP32 build and flashing](Online_ESP32C3_Flasher/esp32-1352/README.md)
- [LAN host and User's Guide setup](Online_ESP32C3_Flasher/lan-host/README.md)

## Prepare a fresh checkout

```sh
python3 -m venv .venv
.venv/bin/pip install platformio==6.2.0 esptool==5.5.0 pyserial==3.5
.venv/bin/python Online_ESP32C3_Flasher/esp32-1352/scripts/fetch_upstream.py
.venv/bin/python Online_ESP32C3_Flasher/esp32-1352/scripts/extract_assets.py
.venv/bin/python Online_ESP32C3_Flasher/esp32-1352/scripts/check_assets.py
```

The upstream input is downloaded from
[may0need5/Online_ESP32C3_Flasher](https://github.com/may0need5/Online_ESP32C3_Flasher)
at commit `0b128df3e13fd463797a679bfbcfdaf8b87da7c8` and hash checked.
Upstream binaries, extracted payloads, build outputs and device logs are not
committed. Upstream assets retain their original ownership and terms.

The supplied systemd examples target `/home/nichlas/Ps4hack` and
`192.168.32.88`; adapt those paths, account and address for another machine.

The owner reported successful PS4 execution using the ESP32 on 2026-10-08.
LAN host HTTP and asset tests pass; physical PS4 LAN execution still needs
confirmation. Earlier ESP32 Wi-Fi initialization failures remain unexplained;
the working diagnostic wrappers are retained.
