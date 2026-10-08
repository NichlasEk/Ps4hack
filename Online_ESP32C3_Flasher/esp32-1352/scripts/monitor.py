"""Capture serial output to a local file; reset only when explicitly requested."""
import argparse
from datetime import datetime
from pathlib import Path
import sys
import time

import serial

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--port", default="/dev/ttyUSB0")
parser.add_argument("--duration", type=float, default=60)
parser.add_argument("--reset", action="store_true")
parser.add_argument("--log", type=Path)
args = parser.parse_args()
path = args.log or Path(__file__).resolve().parents[1] / "artifacts" / (
    datetime.now().strftime("serial-%Y%m%d-%H%M%S.log"))
path.parent.mkdir(parents=True, exist_ok=True)
port = serial.Serial(port=None, baudrate=115200, timeout=0.2, exclusive=True)
port.dtr = False
port.rts = False
port.port = args.port
port.open()
print(f"Logging {args.port} at 115200 baud to {path}", flush=True)
try:
    with path.open("xb") as log:
        if args.reset:
            port.rts = True
            time.sleep(0.15)
            port.rts = False
        deadline = time.monotonic() + args.duration
        while time.monotonic() < deadline:
            data = port.read(max(1, port.in_waiting))
            if data:
                log.write(data)
                log.flush()
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
except KeyboardInterrupt:
    pass
finally:
    port.close()
